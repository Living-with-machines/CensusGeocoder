import os
import pandas as pd
import geopandas as gpd
import json
import pygeos as pg
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

#gpd.options.use_pygeos = True

def process_rsd_boundary_data(path_to_rsd_boundary_data,cen):
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
	print('Reading Registration Sub District (RSD) boundary data')

	tmp_file = gpd.read_file(path_to_rsd_boundary_data,rows=1)
	list_of_all_cols = tmp_file.columns.values.tolist()
	cols_to_keep = [cen,'geometry']
	unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

	par_rsd_boundary = gpd.read_file(path_to_rsd_boundary_data,ignore_fields=unwanted_cols,crs='EPSG:27700')



	par_rsd_boundary = par_rsd_boundary.dissolve(by=cen).reset_index()



	return par_rsd_boundary

def read_gis_to_icem(gis_to_icem_path,conparid_alt):
	list_of_cols = ['UKDS_ID',conparid_alt]
	gis_to_icem = pd.read_excel(gis_to_icem_path,sheet_name='link',usecols=list_of_cols,na_values=".")
	return gis_to_icem

def process_parish_boundary_data(parish_shapefile,gis_to_icem,conparid_alt):
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
	par_boundary_conparid = par_boundary_conparid.dissolve(by=conparid_alt).reset_index()
	par_boundary_conparid = par_boundary_conparid[[conparid_alt,'geometry']]

	return par_boundary_conparid

def join_parish_rsd_boundary(par_boundary,rsd_boundary,conparid_alt,cen):
	
	print('Joining Parish Boundary and RSD Boundary')
	#print(par_boundary['geometry'].is_valid.all())
	#print(rsd_boundary['geometry'].is_valid.all())
	par_rsd_boundary = gpd.overlay(par_boundary,rsd_boundary,how='intersection',keep_geom_type=True)

	par_rsd_boundary = par_rsd_boundary.dropna(subset=[conparid_alt,cen]).copy()
	par_rsd_boundary['new_id'] = par_rsd_boundary[conparid_alt].astype(str) + '_' + par_rsd_boundary[cen].astype(str)
	par_rsd_boundary = par_rsd_boundary.dissolve(by='new_id').reset_index()
	print(par_rsd_boundary.info())
	return par_rsd_boundary


def read_raw_os_data(os_open_roads_filelist,rows_to_use):

	"""
	Reads OS OpenRoad line data and concatenates into a single GeoPandas Dataframe. Drops na values.

	Parameters
	----------
	os_open_roads_filelist : list of paths
		List of the file paths for each OS Open Road shapefile.
	
	Returns
	-------
	geopandas.GeoDataFrame
		A geopandas geodataframe containing the OS Open Road data.
	"""

	# Read in OS Roads vector data (reads multiple .shp files into one gdf)
	print('Reading OS Road vector data')
	count = 0
	for road_shp in os_open_roads_filelist:
		count = count + 1
		tmp_file = gpd.read_file(road_shp,rows=1)
		list_of_all_cols = tmp_file.columns.values.tolist()
		cols_to_keep = ['name1','geometry','nameTOID']
		unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]
		if count == 1:
			break
	
	os_open_road_data = gpd.GeoDataFrame(pd.concat([gpd.read_file(road_shp,ignore_fields=unwanted_cols,crs='EPSG:27700',rows=rows_to_use) for road_shp in os_open_roads_filelist]))
	print(os_open_road_data)
	os_open_road_data = os_open_road_data.dropna(subset=['name1','nameTOID']).copy()
	os_open_road_data = os_open_road_data.dropna(subset=['geometry']).copy()
	#os_open_road_data = os_open_road_data.set_crs('epsg:27700')
	print(os_open_road_data)
	return os_open_road_data


def segment_os_roads(os_open_roads,par_rsd_boundary,cen,conparid_alt):
	"""
		Segments OS Open Road Data by Parish/RSD Boundary by performing a union (geopandas overlay, how = "union") between the two datasets. The result provides road segments within each Parish/RSD Boundary, e.g. if a road runs through two Parish/RSD boundaries it will be split at the boundary and assigned the relevant ids for each segment in each Parish/RSD boundary. This allows for more accurate geo-coding of addresses because individuals can be linked to the street segment that lays within their Parish/RSD.

		Parameters
		----------
		os_open_roads: geopandas.GeoDataFrame
			GeoDataframe of OS Open Road Data.
		par_rsd_boundary: geopandas.GeoDataFrame
			GeoDataframe of combined Parish and RSD boundary data.

		Returns
		-------
		geopandas.GeoDataFrame
			A geopandas geodataframe containing the OS Open Road data with attributes from the Parish/RSD boundary dataset.
		"""
	print('Segmenting OS Open Roads with Parish/RSD Boundary data')
	os_open_roads = os_open_roads.set_crs('epsg:27700')
	# if os.path.exists('data/1881/1881_os_roads.tsv'): # Needs editing now that the .shp doesn't exist
	# 	print('Reading not conducting Segmentation')
	# 	segmented_roads_df = pd.read_csv('data/1881/1881_os_roads.tsv',sep="\t")
	# 	segmented_roads_df['geometry'] = gpd.GeoSeries.from_wkt(segmented_roads_df['geometry'])
	# 	segmented_roads = gpd.GeoDataFrame(segmented_roads_df,geometry='geometry',crs='EPSG:27700')
		#segmented_roads = segmented_roads.rename({'conparid_5':'conparid_51-91'},axis=1)
	# else:
	segmented_roads = gpd.overlay(os_open_roads,par_rsd_boundary,how="union",keep_geom_type=True)
	segmented_roads = segmented_roads.dropna(subset=[conparid_alt,cen]).copy()
	return segmented_roads


def icem_linking_prep(segmented_roads,os_road_id,cen,conparid,name1='name1',nameTOID='nameTOID',new_id='new_id'):
	# TO DO add in output for roads that get dropped due to duplication
	"""
	Prepare the segmented OS Open Road Data for linking to I-CeM. Conducts the following steps:
	1. Converts road names to uppercase, to match uppercase of ICeM addresses.
	2. Creates new ids for each road segment per Parish/RSD
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

	segmented_roads = segmented_roads.dropna(subset=['name1']).copy()
	segmented_roads[name1] = segmented_roads[name1].str.upper() # uppercase to match I-CeM addresses

	# Create new road_id for each road segment per ConParID (one set of ids for 1851-1891; another for 1901-1911)
	segmented_roads[os_road_id] = segmented_roads[nameTOID].astype(str)+'_'+segmented_roads[new_id].astype(str)

	# Dissolve multiple segments of roads with the same road_id (e.g. where there are two line segments of the same road in a parish)
	print('Dissolving on road_ids')
	segmented_os_roads_to_icem_aggregated = segmented_roads.dissolve(by=os_road_id)
	
	# Ensure ids match the datatype int64 otherwise error produced when linking to ConParID in I-CeM
	# Drop duplicate roads (roads with same name and same ConParID e.g. two roads with the same name in the same parish with currently no way to distinguish them)
	#print('before de-duplicating: ',len(os_vector_data_01_11))
	segmented_os_roads_to_icem_aggregated_deduplicated =  segmented_os_roads_to_icem_aggregated.drop_duplicates(subset=['name1','new_id'],keep=False).copy()
	#print('after de-duplicating: ',len(os_vector_data_01_11_deduplicated))
	#os_vector_data_01_11_duplicates = pd.concat([os_vector_data_01_11,os_vector_data_01_11_deduplicated]).drop_duplicates(keep=False)
	#os_vector_data_01_11_duplicates = os_vector_data_01_11_duplicates.reset_index(drop=True)
	#os_vector_data_01_11_duplicates.to_csv('data/outputs_new/os_vector_data_01_11_duplicates.txt','\t')

	segmented_os_roads_to_icem_aggregated_deduplicated[cen] = pd.to_numeric(segmented_os_roads_to_icem_aggregated_deduplicated[cen], errors='coerce')
	segmented_os_roads_to_icem_aggregated_deduplicated[conparid] = pd.to_numeric(segmented_os_roads_to_icem_aggregated_deduplicated[conparid], errors='coerce')

	#segmented_os_roads_to_icem_aggregated_deduplicated = segmented_os_roads_to_icem_aggregated_deduplicated[['geometry','name1',conparid,cen,'new_id']]

	return segmented_os_roads_to_icem_aggregated_deduplicated


def process_gb1900(gb1900_file,rsd_boundary,conparid,cen,rows_to_use):
	# todo read gb1900, union of gb1900 and parish/rsd boundary data; drop null values
	"""
	Read gb1900 dataset. Subset 

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
	with open('data/input/street_standardisation.json') as f:
		street_standardisation = json.load(f)

	gb1900['final_text'] = gb1900['final_text'].replace(street_standardisation,regex=True)

	# Convert gb1900 to a geodataframe; uses osgb_east and osgb_north rather than lat long and EPSG: 4326 to conform to the same CRS as the England and Wales parish polygon dataset (see below)
	gb1900_gdf = gpd.GeoDataFrame(
		gb1900, geometry=gpd.points_from_xy(gb1900['osgb_east'], gb1900['osgb_north']),crs='EPSG:27700')
	#print(gb1900_gdf)
	# Spatial join between England and Wales parish polygons and gb1900
	gb1900_to_icem = gpd.sjoin(left_df=gb1900_gdf, right_df=rsd_boundary, op='intersects',how='inner')
	#print(gb1900_to_icem)
	gb1900_to_icem = gb1900_to_icem.dropna(subset=[conparid,cen]).copy()

	# Drop duplicates as 'pin_id' should be unique and needs to be unique for use as index
	gb1900_filtered = gb1900_to_icem.drop_duplicates(subset=['pin_id'],keep=False)
	gb1900_filtered = gb1900_filtered.set_index('pin_id')
	return gb1900_filtered

def read_rsd_dictionary(rsd_dictionary,par_id,cen):
	rsd_variables = [par_id,cen]

	rsd_dict = pd.read_csv(rsd_dictionary,sep="\t",quoting=3,usecols=rsd_variables,encoding='utf-8')
	return rsd_dict


def process_census(census_file,rsd_dictionary,par_id,cen,rows_to_use):
	census_variables = ['safehaven_id','address_anonymised','ConParID','ParID','RegCnty']
	census_dtypes = {'ConParID':'int32','ParID':'int32'}
	print('Reading census')
	census = pd.read_csv(census_file,sep="\t",quoting=3,encoding = "latin-1",na_values=".",usecols=census_variables,dtype=census_dtypes,nrows=rows_to_use)
	print('Successfully read census')
	census = pd.merge(left=census,right=rsd_dictionary,left_on='ParID',right_on=par_id,how='left')
	print('Merged with RSD dictionary')

	census['ConParID'] = pd.to_numeric(census['ConParID'], errors='coerce')
	census[cen] = pd.to_numeric(census[cen], errors='coerce')

	#TODO
	# Rename fields so they are <10 chars ready for output to shapefile
	census = census.rename({'address_anonymised':'add_anon','safehaven_id':'sh_id'},axis=1)
	# Make limited regex replacements to standardise street names

	with open('data/input/icem_street_standardisation.json') as f:
		street_standardisation = json.load(f)
	census['add_anon'] = census['add_anon'].replace(street_standardisation,regex=True)
	census['add_anon'] = census['add_anon'].replace('^\\s*$',np.nan,regex=True)
	census['add_anon'] = census['add_anon'].str.strip()
	census = census.dropna(subset=['add_anon']).copy()
	# Create an id for each unique 'address' + ConParID + CEN_1901 combination
	census['unique_add_id'] = census['add_anon'].astype(str)+'_'+census['ConParID'].astype(str) + '_' + census[cen].astype(str)

	# Create new dataframe containing unique addresses with a column containing a list of sh_ids that relate to this address
	
	census_unique = census.groupby(['unique_add_id','ConParID',cen,'add_anon','RegCnty'])['sh_id'].apply(list).reset_index(name='sh_id_list')
	census_unique = census_unique.set_index('unique_add_id')

	census_counties = census['RegCnty'].unique()
	census_counties = sorted(census_counties)


	return census_unique, census_counties

def compute_tfidf(census):
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