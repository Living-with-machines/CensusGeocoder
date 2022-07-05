import dask.dataframe as dd
import pandas as pd
import geopandas as gpd
import json
import pygeos as pg
import pathlib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

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


#gpd.options.use_pygeos = True

def process_rsd_boundary_data(path_to_rsd_boundary_data,field_dict):
	"""
	Reads combined Parish / Registration Sub District (RSD) boundary data

	Parameters
	----------
	path_to_rsd_boundary_data : str, path object
		Either the absolute or relative path to the combined Parish/RSD boundary file.
	conparid: str
		Column label for consistent parish ID, either 'conpar51-9' or 'conpar01-1'
	cen: str
		Column label for RSD id, takes format 'CEN_' followed by year, e.g. 'CEN_1901'.
	new_id: pandas.series.name
		Column label for new_id that combines conparid and cen; default 'new_id'

	Returns
	--------
	geopandas.GeoDataFrame
		A geopandas geodataframe containing the Parish/RSD Boundary data with a new id column created from the conparid and cen id variables.
	"""
	if path_to_rsd_boundary_data != None:
		print('Reading Registration Sub District (RSD) boundary data')

		tmp_file = gpd.read_file(path_to_rsd_boundary_data,rows=1)
		list_of_all_cols = tmp_file.columns.values.tolist()
		cols_to_keep = [field_dict['cen'],'geometry']
		unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

		par_rsd_boundary = gpd.read_file(path_to_rsd_boundary_data,ignore_fields=unwanted_cols,crs='EPSG:27700')



		par_rsd_boundary = par_rsd_boundary.dissolve(by=field_dict['cen']).reset_index()

	else:
		par_rsd_boundary = None

	return par_rsd_boundary

def read_gis_to_icem(gis_to_icem_path,field_dict):
	list_of_cols = ['UKDS_ID',field_dict['conparid']]
	gis_to_icem = pd.read_excel(gis_to_icem_path,sheet_name='link',usecols=list_of_cols,na_values=".")
	return gis_to_icem

def process_parish_boundary_data(parish_shapefile,gis_to_icem,field_dict):
	print('Reading Parish Boundary Data')
	tmp_file = gpd.read_file(parish_shapefile,rows=1)
	list_of_all_cols = tmp_file.columns.values.tolist()
	cols_to_keep = ['ID','geometry']
	unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

	par_boundary = gpd.read_file(parish_shapefile,ignore_fields=unwanted_cols,crs='EPSG:27700')
	# Buffer to ensure valid geometries
	par_boundary['geometry'] = par_boundary['geometry'].buffer(0)
	# Set precision of coordinates so overlay operations between parish boundary and rsd boundary work properly
	par_boundary['geometry'] = pg.set_precision(par_boundary['geometry'].values.data,0)

	par_boundary_conparid = pd.merge(left=par_boundary,right=gis_to_icem,left_on='ID',right_on='UKDS_ID',how='left')
	par_boundary_conparid = par_boundary_conparid.dissolve(by=field_dict['conparid']).reset_index()
	par_boundary_conparid = par_boundary_conparid[[field_dict['conparid'],'geometry']]

	return par_boundary_conparid

def join_parish_rsd_boundary(par_boundary,rsd_boundary,field_dict):
	
	print('Joining Parish Boundary and RSD Boundary')
	#print(par_boundary['geometry'].is_valid.all())
	#print(rsd_boundary['geometry'].is_valid.all())
	par_rsd_boundary = gpd.overlay(par_boundary,rsd_boundary,how='intersection',keep_geom_type=True)

	par_rsd_boundary = par_rsd_boundary.dropna(subset=[field_dict['conparid'],field_dict['cen']]).copy()
	par_rsd_boundary['new_id'] = par_rsd_boundary[field_dict['conparid']].astype(str) + '_' + par_rsd_boundary[field_dict['cen']].astype(str)
	par_rsd_boundary = par_rsd_boundary.dissolve(by='new_id').reset_index()
	# print(par_rsd_boundary.info()) to delete
	return par_rsd_boundary

def process_raw_geo_data(geom_name,rows_to_use,boundary_data,field_dict,geom_attributes,census_year,output_dir):

	print(f'Reading {geom_name} geometry data')

	cols_to_keep = []
	for k,v in geom_attributes.items():
		if 'field' in k:
			if isinstance(v, list):
				cols_to_keep.extend(v)
			else:
				cols_to_keep.append(v)

	print(cols_to_keep)

	filelist = set_geom_files(geom_attributes)

	new_uid = str(geom_name) + '_' + str(census_year)

	if geom_attributes['file_type'] == 'shp':

		tmp_file = gpd.read_file(filelist[0],rows=1)
		list_of_all_cols = tmp_file.columns.values.tolist()

		unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

		streets_gdf = gpd.GeoDataFrame(pd.concat([gpd.read_file(road_shp,ignore_fields=unwanted_cols,crs=geom_attributes['projection'],rows=rows_to_use) for road_shp in filelist]),crs=geom_attributes['projection'])
		# print(streets_gdf)
		streets_gdf = streets_gdf.dissolve(by='nameTOID',as_index=False)
		# print(streets_gdf)

	elif geom_attributes['file_type'] == 'csv':

		streets_df = pd.concat([pd.read_csv(csv_file,sep=',',encoding=geom_attributes['encoding'],usecols=cols_to_keep,nrows=rows_to_use) for csv_file in filelist])

		if geom_attributes['geometry_format'] == 'coords':

			streets_gdf = gpd.GeoDataFrame(streets_df, geometry=gpd.points_from_xy(streets_df[geom_attributes['geometry_field'][0]], streets_df[geom_attributes['geometry_field'][1]]),crs=geom_attributes['projection']).drop(columns=geom_attributes['geometry_field'])

			# print(streets_gdf.info())

		elif geom_attributes['geometry_format'] == 'wkt':

			streets_gdf = gpd.GeoDataFrame(streets_df, geometry=gpd.GeoSeries.from_wkt(streets_df['wkt']),crs=geom_attributes['projection'])
		# print(streets_gdf)

	streets_gdf = streets_gdf.dropna().copy() #need to check the effect this is having by not using subset any more.
	# print(streets_gdf)

	if geom_attributes['geom_type'] == 'line':
		streets_gdf_processed = process_linstring(streets_gdf,boundary_data,geom_attributes,field_dict,new_uid)

	elif geom_attributes['geom_type'] == 'point':
		streets_gdf_processed = process_point(streets_gdf,boundary_data,geom_attributes,field_dict,new_uid)
		# print(streets_gdf_processed.info())

	streets_gdf_processed = parse_address(streets_gdf_processed,geom_attributes)


	print(streets_gdf_processed.info())

	streets_gdf_processed.to_csv(output_dir+f'/{geom_name}_{census_year}.tsv',sep="\t")

	streets_gdf_lnk = streets_gdf_processed[[geom_attributes['address_field'],field_dict['conparid'],field_dict['cen']]]

	print(streets_gdf_lnk.info())

	return streets_gdf_lnk,new_uid

def drop_outside_country(streets_gdf,field_dict):
	subset_fields = []

	if field_dict['country'] == 'SCOT':
		subset_fields.append(field_dict['scot_parish'])
	elif field_dict['country'] == 'EW':
		subset_fields.append(field_dict['conparid'])
		subset_fields.append(field_dict['cen'])

	tmp = streets_gdf.dropna(subset=subset_fields).copy() # Drop roads outside country (i.e. with no associated parish info from the union)
	return tmp

def process_linstring(line_string_gdf,boundary_data,geom_attributes,field_dict,new_uid):
	tmp = line_string_gdf.dissolve(by=geom_attributes['uid_field'],as_index=False)
	print(tmp)
	tmp2 = gpd.overlay(tmp,boundary_data,how="identity",keep_geom_type=True)

	tmp2 = drop_outside_country(tmp2, field_dict)

	tmp2[new_uid] = tmp2[geom_attributes['uid_field']].astype(str)+'_'+tmp2['new_id'].astype(str)

	tmp3 =tmp2.dissolve(by=new_uid)
	print(tmp3)
	tmp4 =  tmp3.drop_duplicates(subset=[geom_attributes['address_field'],'new_id'],keep=False).copy()
	return tmp4

def process_point(point_gdf,boundary_data,geom_attributes,field_dict,new_uid):
	tmp= gpd.sjoin(left_df=point_gdf, right_df=boundary_data, predicate='intersects',how='inner').drop(columns=["index_right"])

	tmp = drop_outside_country(tmp, field_dict)

	tmp[new_uid] = tmp[geom_attributes['uid_field']].astype(str)+'_'+tmp['new_id'].astype(str)
	tmp2 = tmp.drop_duplicates(subset=[new_uid],keep=False)
	tmp3 = tmp2.set_index(new_uid)
	return tmp3

def parse_address(streets_gdf,geom_attributes):

	streets_gdf[geom_attributes['address_field']] = streets_gdf[geom_attributes['address_field']].str.upper()

	if geom_attributes['query_criteria'] != "":
		streets_gdf = streets_gdf.query(geom_attributes['query_criteria']).copy()

	if geom_attributes['standardisation_file'] != "":
		with open(geom_attributes['standardisation_file']) as f:
			street_standardisation = json.load(f)

		streets_gdf[geom_attributes['address_field']] = streets_gdf[geom_attributes['address_field']].replace(street_standardisation,regex=True)

	streets_gdf[geom_attributes['address_field']] = streets_gdf[geom_attributes['address_field']].str.strip()
	return streets_gdf



def icem_linking_prep(segmented_roads,field_dict,name1='name1',nameTOID='nameTOID',new_id='new_id'):
	# TO DO add in output for roads that get dropped due to duplication
	"""
	Prepare the segmented OS Open Road Data for linking to I-CeM. Conducts the following steps:
	1. Converts road names to uppercase, to match uppercase of ICeM addresses.
	2. Creates new ids for each road segment per parish boundary or for England and Wales per Parish/RSD boundary
	3. Dissolves on this new id so that roads with multiple segments in the same Parish/RSD are one geography

	Parameters
	----------
	segmented_roads: geopandas.GeoDataFrame
		GeoDataframe of OS Open Road Data segmented by Parish/RSD Boundaries.
	census_year integer
		Year of census; used for generating the new unique id for each road within a Parish/RSD
	nameTOID: pandas.series.name; default 'nameTOID'
		Column label of 'nameTOID' column from OS Open Roads Dataset
	new_id: pandas.series.name; default 'new_id'
		Column label of 'new_id' column from ?? overlay of OS Open Roads and Parish/RSD Boundary;

	Returns
	-------
	geopandas.GeoDataFrame
		A geopandas geodataframe containing the OS Open Road data ready for linking to I-CeM.
	"""




	# Create new road_id for each road segment per ConParID (one set of ids for 1851-1891; another for 1901-1911)
	segmented_roads[field_dict['os_road_id']] = segmented_roads[nameTOID].astype(str)+'_'+segmented_roads[new_id].astype(str)

	# Dissolve multiple segments of roads with the same road_id (e.g. where there are two line segments of the same road in a parish)
	print('Dissolving on road_ids')
	segmented_os_roads_to_icem_aggregated = segmented_roads.dissolve(by=field_dict['os_road_id'])
	
	# Ensure ids match the datatype int64 otherwise error produced when linking to ConParID in I-CeM
	# Drop duplicate roads (roads with same name and same ConParID e.g. two roads with the same name in the same parish with currently no way to distinguish them)
	#print('before de-duplicating: ',len(os_vector_data_01_11))
	segmented_os_roads_to_icem_aggregated_deduplicated =  segmented_os_roads_to_icem_aggregated.drop_duplicates(subset=['name1','new_id'],keep=False).copy()
	#print('after de-duplicating: ',len(os_vector_data_01_11_deduplicated))
	#os_vector_data_01_11_duplicates = pd.concat([os_vector_data_01_11,os_vector_data_01_11_deduplicated]).drop_duplicates(keep=False)
	#os_vector_data_01_11_duplicates = os_vector_data_01_11_duplicates.reset_index(drop=True)
	#os_vector_data_01_11_duplicates.to_csv('data/outputs_new/os_vector_data_01_11_duplicates.txt','\t')
	print(segmented_os_roads_to_icem_aggregated_deduplicated.info())
	if field_dict['country'] == 'SCOT':
		segmented_os_roads_to_icem_aggregated_deduplicated[field_dict['scot_parish']] = pd.to_numeric(segmented_os_roads_to_icem_aggregated_deduplicated[field_dict['scot_parish']], errors='coerce')
	elif field_dict['country'] == 'EW':
		segmented_os_roads_to_icem_aggregated_deduplicated[field_dict['cen']] = pd.to_numeric(segmented_os_roads_to_icem_aggregated_deduplicated[field_dict['cen']], errors='coerce')
		segmented_os_roads_to_icem_aggregated_deduplicated[field_dict['conparid']] = pd.to_numeric(segmented_os_roads_to_icem_aggregated_deduplicated[field_dict['conparid']], errors='coerce')

	#segmented_os_roads_to_icem_aggregated_deduplicated = segmented_os_roads_to_icem_aggregated_deduplicated[['geometry','name1',conparid,cen,'new_id']]
	print(segmented_os_roads_to_icem_aggregated_deduplicated) #remove once testing finished
	return segmented_os_roads_to_icem_aggregated_deduplicated


def process_gb1900(gb1900_file,boundary_data,field_dict,rows_to_use):
	"""
	Read gb1900 dataset. Subset by labels longer than 5 characters to filter out entries that probably aren't roads to speed up later record comparison.

	Parameters
	----------
	gb1900_file: path to gb1900 file
		Path to gb1900 file.

	Returns
	-------
	geopandas.GeoDataFrame
		A geopandas geodataframe containing the gb1900 data.
	"""

	# Read gb1900
	print('Reading gb1900 data')

	gb1900_variables = ['pin_id','final_text','osgb_east','osgb_north']
	gb1900 = pd.read_csv(gb1900_file,sep=',',encoding='utf-16',usecols=gb1900_variables,nrows=rows_to_use)

	gb1900 = gb1900[gb1900['final_text'].str.len()>5]

	# Convert gb1900 final_text field to uppercase (to match uppercase of I-CeM data)
	gb1900['final_text'] = gb1900['final_text'].str.upper()

	# Strip any leading or trailing spaces in the final_text field
	gb1900['final_text'] = gb1900['final_text'].str.strip()

	# Read in regex replacement dictionary to standardise street names e.g. 'HIGH ST.' TO 'HIGH STREET'
	with open('./inputs/street_standardisation.json') as f:
		street_standardisation = json.load(f)

	gb1900['final_text'] = gb1900['final_text'].replace(street_standardisation,regex=True)

	# Convert gb1900 to a geodataframe; uses osgb_east and osgb_north rather than lat long and EPSG: 4326 to conform to the same CRS as the England and Wales parish polygon dataset (see below)
	gb1900_gdf = gpd.GeoDataFrame(
		gb1900, geometry=gpd.points_from_xy(gb1900['osgb_east'], gb1900['osgb_north']),crs='EPSG:27700')
	#print(gb1900_gdf)
	# Spatial join between England and Wales parish polygons and gb1900
	gb1900_to_icem = gpd.sjoin(left_df=gb1900_gdf, right_df=boundary_data, op='intersects',how='inner')

	subset_fields = []

	if field_dict['country'] == 'SCOT':
		subset_fields.append(field_dict['scot_parish'])
	elif field_dict['country'] == 'EW':
		subset_fields.append(field_dict['conparid'])
		subset_fields.append(field_dict['cen'])

	print(gb1900_to_icem)
	gb1900_to_icem = gb1900_to_icem.dropna(subset=subset_fields).copy()

	# Drop duplicates as 'pin_id' should be unique and needs to be unique for use as index
	gb1900_filtered = gb1900_to_icem.drop_duplicates(subset=['pin_id'],keep=False)
	gb1900_filtered = gb1900_filtered.set_index('pin_id')
	print(gb1900_filtered)
	return gb1900_filtered

def read_rsd_dictionary(rsd_dictionary,field_dict):
	"""
	Read the RSD Dictionary lookup file for the appropriate census year.

	Parameters
	----------
	rsd_dictionary: str
		Path to rsd dictionary file.
	
	field_dict: dictionary
		Dictionary with field values.

	Returns
	-------
	pandas.DataFrame
		A pandas dataframe containing the RSD Dictionary lookup table.
	"""

	rsd_variables = [field_dict['parid_for_rsd_dict'],field_dict['cen']]

	rsd_dict = pd.read_csv(rsd_dictionary,sep="\t",quoting=3,usecols=rsd_variables,encoding='utf-8')
	return rsd_dict


def process_census(census_file,rsd_dictionary,rows_to_use,field_dict,census_year,country):

	"""
	Read the census file and prepare it for subsquent geo-coding steps.

	Parameters
	----------
	census_file: str
		Path to census file.

	rows_to_use: int or None
		The rows to read from the dataset as specified by the type of geo-coding, either 'full' or 'testing' in parameters json.
	
	field_dict: dictionary
		Dictionary with field values.

	Returns
	-------
	pandas.DataFrame
		A pandas dataframe containing the processed census data for each individual.

	pandas.DataFrame
		A pandas dataframe containing unique addresses and counties.

	list
		A sorted list of census counties.
	"""

	census_variables = ['safehaven_id','address_anonymised','ConParID','ParID','RegCnty']
	print('Reading census')

	census_dd = dd.read_csv(census_file,sep="\t",encoding="latin-1",na_values=".",usecols=census_variables,quoting=3,blocksize=25e6,assume_missing=True)
	# census_dd.to_parquet(f'./data/input/census_parquet/{census_year}/{country}/', partition_on=['RegCnty'], engine="pyarrow")
	


	# census = pd.read_csv(census_file,sep="\t",quoting=3,encoding = "latin-1",na_values=".",usecols=census_variables,nrows=rows_to_use)
	print('Successfully read census')

	census_dd['ConParID'] = pd.to_numeric(census_dd['ConParID'], errors='coerce')

	census_dd = census_dd.rename(columns = {'address_anonymised':'add_anon','safehaven_id':'sh_id'}) # This isn't necessary now as output is tsv not .shp so field names don't have to be under 10 characters long.

	# Make limited regex replacements to standardise street names
	with open('./inputs/icem_street_standardisation.json') as f:
		street_standardisation = json.load(f)
	census_dd['add_anon'] = census_dd['add_anon'].replace(street_standardisation,regex=True)
	census_dd['add_anon'] = census_dd['add_anon'].replace('^\\s*$',np.nan,regex=True)
	census_dd['add_anon'] = census_dd['add_anon'].str.strip()
	census_dd = census_dd.dropna(subset=['add_anon']).copy()

	if field_dict['country'] == 'EW':
		census_dd = dd.merge(left=census_dd,right=rsd_dictionary,left_on='ParID',right_on=field_dict['parid_for_rsd_dict'],how='left')
		census_dd[field_dict['cen']] = pd.to_numeric(census_dd[field_dict['cen']], errors='coerce')
		# Create an id for each unique 'address' + ConParID + CEN_1901 combination
		census_dd['unique_add_id'] = census_dd['add_anon'].astype(str)+'_'+census_dd['ConParID'].astype(str) + '_' + census_dd[field_dict['cen']].astype(str)
		print('Merged with RSD dictionary')
	elif field_dict['country'] == 'SCOT':
		census_dd['unique_add_id'] = census_dd['add_anon'].astype(str)+'_'+census_dd['ParID'].astype(str)

	census_dd.to_parquet(f'./data/input/census_parquet/{census_year}/{country}/', partition_on=['RegCnty'], engine="pyarrow")


	# trial = pd.read_parquet(f'./data/input/census_parquet/{census_year}/{country}/',filters=[[('RegCnty','=','Anglesey')]])
	# print(trial)
	# census_counties = census['RegCnty'].unique()
	# census_counties = sorted(census_counties)

	return 

def scot_parish_lookup(scot_parish_lkup_path,census_year):
	"""
	Read Lookup Spreadsheet for Scotland Parish Boundaries that links Scotland Parish GIS to I-CeM ParID.

	Parameters
	----------
	scot_parish_lkup_path: path
		Path to scotland parish lookup file.

	Returns
	-------
	pandas.DataFrame
		A pandas dataframe containing the Scotland parish boundary lookup table.
	"""
	list_of_cols = ['name','ParID_link']
	sheet = str(census_year)
	scot_parish_lookup = pd.read_excel(scot_parish_lkup_path,sheet_name=sheet,usecols=list_of_cols,na_values=".")
	return scot_parish_lookup

def process_scot_parish_boundary_data(parish_shapefile,scot_parish_lkup,census_year):

	"""
	Link Scotland Parish Boundary dataset to I-CeM ParID by linking the boundary dataset to the parish lookup table.

	Parameters
	----------
	parish_shapefile: geopandas.GeoDataFrame
		A geopandas dataframe containing the information and geometries of Scotland parish boundaries.

	scot_parish_lkup: pandas.Dataframe
		A pandas dataframe containing data that links the parishes in the parish boundary dataset with the `ParID` column in I-CeM.

	census_year: int
		The census year.

	Returns
	-------
	geopandas.GeoDataFrame
		A geopandas dataframe containing the Scotland parish boundary geometries with associated `ParID` values for linking to I-CeM.
	"""

	print('Reading Parish Boundary Data')
	tmp_file = gpd.read_file(parish_shapefile,rows=1)
	list_of_all_cols = tmp_file.columns.values.tolist()
	print(list_of_all_cols) #edit from here
	if census_year <= 1891:
		cols_to_keep = ['ID','geometry'] #edit
		parish_field = '' #edit
	else:
		cols_to_keep = ['name','geometry']
		parish_field = 'name'

	unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

	par_boundary = gpd.read_file(parish_shapefile,ignore_fields=unwanted_cols,crs='EPSG:27700')
	par_boundary['name'] = par_boundary['name'].str.upper() # convert to uppercase to match scot parish lookup table

	
	par_boundary_parid = pd.merge(left=par_boundary,right=scot_parish_lkup,left_on=parish_field,right_on='name',how='left')
	par_boundary_parid = par_boundary_parid.dissolve(by='ParID_link').reset_index()
	par_boundary_parid['new_id'] = par_boundary_parid['ParID_link']
	par_boundary_parid = par_boundary_parid[['ParID_link','new_id','geometry']]
	print(par_boundary_parid) #remove once edits are done
	return par_boundary_parid

def compute_tfidf(census):
	"""
	Compute TF-IDF scores to assess how common road names are. These scores are used to weight the string comparisons so that common road names have to reach a higher matching threshold to be classed as a match.

	Parameters
	----------
	census: pandas.dataframe
		A pandas dataframe containing census data.

	Returns
	-------
	pandas.DataFrame
		A pandas dataframe containing census data with two additional columns with tf-idf weighting data.
	"""
	try:
		tfidf_vectorizer = TfidfVectorizer(norm='l2',use_idf=True,lowercase=False) # default is norm l2
		tfidf_sparse = tfidf_vectorizer.fit_transform(census['add_anon'])
		tfidf_array = tfidf_sparse.toarray()
		tfidf_array_sums = np.sum(tfidf_array,axis=1).tolist()
		census['tfidf'] = tfidf_array_sums
		census['weighting'] = census['tfidf'] / census['add_anon'].str.len()
	except ValueError:
			print('Likely error with tf-idf not having any strings to compare')
	return census