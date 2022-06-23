import geopandas as gpd
import pandas as pd
import json
import pathlib

def set_geom_files(geom_attributes):

	geom_files = []
	p = pathlib.Path(geom_attributes['data_path'])
	if p.is_file():
		geom_files.append(str(p))
	else:
		for file_p in p.iterdir():
			if geom_attributes['file_name'] in str(file_p):
				geom_files.append(str(file_p))

	return geom_files


def process_raw_geo_data(geom_name,rows_to_use,boundary_data,geom_attributes,census_year,outputdir):

	print(f'Reading {geom_name} geometry data')
	print(geom_attributes)
	cols_to_keep = [*geom_attributes['data_fields'].values()]

	# for k,v in geom_attributes.items():
	# 	if 'field' in k:
	# 		if isinstance(v, list):
	# 			cols_to_keep.extend(v)
	# 		else:
	# 			cols_to_keep.append(v)

	print(cols_to_keep)

	filelist = set_geom_files(geom_attributes)

	new_uid = str(geom_name) + '_' + str(census_year)

	if geom_attributes['file_type'] == 'shp':

		tmp_file = gpd.read_file(filelist[0],rows=1)
		list_of_all_cols = tmp_file.columns.values.tolist()

		unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

		streets_gdf = gpd.GeoDataFrame(pd.concat([gpd.read_file(road_shp,ignore_fields=unwanted_cols,crs=geom_attributes['projection'],rows=rows_to_use) for road_shp in filelist]),crs=geom_attributes['projection'])
		# print(streets_gdf)
		streets_gdf = streets_gdf.dissolve(by=geom_attributes['data_fields']['uid_field'],as_index=False)
		# print(streets_gdf)

	elif geom_attributes['file_type'] == 'csv':

		streets_df = pd.concat([pd.read_csv(csv_file,sep=',',encoding=geom_attributes['encoding'],usecols=cols_to_keep,nrows=rows_to_use) for csv_file in filelist])

		if geom_attributes['geometry_format'] == 'coords':

			streets_gdf = gpd.GeoDataFrame(streets_df, geometry=gpd.points_from_xy(streets_df[geom_attributes['data_fields']['long_field']], streets_df[geom_attributes['data_fields']['lat_field']]),crs=geom_attributes['projection']).drop(columns=[geom_attributes['data_fields']['long_field'],geom_attributes['data_fields']['long_field']])

			# print(streets_gdf.info())

		elif geom_attributes['geometry_format'] == 'wkt':

			streets_gdf = gpd.GeoDataFrame(streets_df, geometry=gpd.GeoSeries.from_wkt(streets_df['wkt']),crs=geom_attributes['projection'])
		# print(streets_gdf)

	streets_gdf = streets_gdf.dropna().copy() #need to check the effect this is having by not using subset any more.
	# print(streets_gdf)

	# print(streets_gdf.info())

	if geom_attributes['geom_type'] == 'line':
		streets_gdf_processed = process_linstring(streets_gdf,boundary_data,geom_attributes,new_uid)

	elif geom_attributes['geom_type'] == 'point':
		streets_gdf_processed = process_point(streets_gdf,boundary_data,geom_attributes,new_uid)
		# print(streets_gdf_processed.info())

	streets_gdf_processed = parse_address(streets_gdf_processed,geom_attributes)

	print(streets_gdf_processed.info())

	geom_outputdir = 'data/output/testing/'
	pathlib.Path(geom_outputdir).mkdir(parents=True, exist_ok=True)

	streets_gdf_processed.to_csv(geom_outputdir+f'{geom_name}_{census_year}.tsv',sep="\t")
	streets_gdf_processed_small = streets_gdf_processed.drop(columns=['geometry'])
	print(streets_gdf_processed_small.info())
	# streets_gdf_lnk = streets_gdf_processed[[geom_attributes['address_field'],field_dict['conparid'],field_dict['cen']]]

	# print(streets_gdf_lnk.info())


	return streets_gdf_processed_small,new_uid

def drop_outside_country(streets_gdf,new_id):
	# subset_fields = []

	# if field_dict['country'] == 'SCOT':
	# 	subset_fields.append(field_dict['scot_parish'])
	# elif field_dict['country'] == 'EW':
	# 	subset_fields.append(field_dict['conparid'])
	# 	subset_fields.append(field_dict['cen'])

	tmp = streets_gdf.dropna(subset=new_id).copy() # Drop roads outside country (i.e. with no associated parish info from the union)
	return tmp

def process_linstring(line_string_gdf,boundary_data,geom_attributes,new_uid):
	tmp = line_string_gdf.dissolve(by=geom_attributes['data_fields']['uid_field'],as_index=False)
	print(tmp)
	tmp2 = gpd.overlay(tmp,boundary_data,how="identity",keep_geom_type=True)
	print(tmp2.info())
	tmp2 = drop_outside_country(tmp2, 'new_id')

	tmp2[new_uid] = tmp2[geom_attributes['data_fields']['uid_field']].astype(str)+'_'+tmp2['new_id'].astype(str)

	tmp3 =tmp2.dissolve(by=new_uid)
	print(tmp3)
	tmp4 =  tmp3.drop_duplicates(subset=[geom_attributes['data_fields']['address_field'],'new_id'],keep=False).copy()
	return tmp4

def process_point(point_gdf,boundary_data,geom_attributes,new_uid):
	tmp= gpd.sjoin(left_df=point_gdf, right_df=boundary_data, predicate='intersects',how='inner').drop(columns=["index_right"])
	
	tmp = drop_outside_country(tmp, 'new_id')

	tmp[new_uid] = tmp[geom_attributes['data_fields']['uid_field']].astype(str)+'_'+tmp['new_id'].astype(str)
	tmp2 = tmp.drop_duplicates(subset=[new_uid],keep=False)
	tmp3 = tmp2.set_index(new_uid)
	return tmp3

def parse_address(streets_gdf,geom_attributes):

	streets_gdf[geom_attributes['data_fields']['address_field']] = streets_gdf[geom_attributes['data_fields']['address_field']].str.upper()

	if geom_attributes['query_criteria'] != "":
		streets_gdf = streets_gdf.query(geom_attributes['query_criteria']).copy()

	if geom_attributes['standardisation_file'] != "":
		with open(geom_attributes['standardisation_file']) as f:
			street_standardisation = json.load(f)

		streets_gdf[geom_attributes['data_fields']['address_field']] = streets_gdf[geom_attributes['data_fields']['address_field']].replace(street_standardisation,regex=True)

	streets_gdf[geom_attributes['data_fields']['address_field']] = streets_gdf[geom_attributes['data_fields']['address_field']].str.strip()
	return streets_gdf