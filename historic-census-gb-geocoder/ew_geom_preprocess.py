import pandas as pd
import geopandas as gpd
import pygeos as pg


#gpd.options.use_pygeos = True

def process_rsd_boundary_data(path_to_rsd_boundary_data,rsd_id_field,rsd_gis_projection):
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
	cols_to_keep = [rsd_id_field,'geometry']
	unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

	par_rsd_boundary = gpd.read_file(path_to_rsd_boundary_data,ignore_fields=unwanted_cols,crs=rsd_gis_projection)

	par_rsd_boundary = par_rsd_boundary.dissolve(by=rsd_id_field).reset_index()

	return par_rsd_boundary

def read_gis_to_icem(path_to_data,conparid,sheet,ukdsid_field,na_values):
	list_of_cols = [ukdsid_field,conparid]
	gis_to_icem = pd.read_excel(path_to_data,sheet_name=sheet,usecols=list_of_cols,na_values=na_values)
	return gis_to_icem

def process_parish_boundary_data(path_to_parish_gis,parish_gis_projection,parish_gis_id_field,ukds_lkuptbl,conparid,parish_icem_lkup_idfield):
	print('Reading Parish Boundary Data')
	tmp_file = gpd.read_file(path_to_parish_gis,rows=1)
	list_of_all_cols = tmp_file.columns.values.tolist()
	cols_to_keep = [parish_gis_id_field,'geometry']
	unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

	par_boundary = gpd.read_file(path_to_parish_gis,ignore_fields=unwanted_cols,crs=parish_gis_projection)
	# Buffer to ensure valid geometries
	par_boundary['geometry'] = par_boundary['geometry'].buffer(0)
	# Set precision of coordinates so overlay operations between parish boundary and rsd boundary work properly
	par_boundary['geometry'] = pg.set_precision(par_boundary['geometry'].values.data,0)

	par_boundary_conparid = pd.merge(left=par_boundary,right=ukds_lkuptbl,left_on=parish_gis_id_field,right_on=parish_icem_lkup_idfield,how='left')
	par_boundary_conparid = par_boundary_conparid.dissolve(by=conparid).reset_index()
	par_boundary_conparid = par_boundary_conparid[[conparid,'geometry']]

	return par_boundary_conparid

def join_parish_rsd_boundary(par_boundary,rsd_boundary,conparid,rsd_id_field):
	
	print('Joining Parish Boundary and RSD Boundary')
	#print(par_boundary['geometry'].is_valid.all())
	#print(rsd_boundary['geometry'].is_valid.all())
	par_rsd_boundary = gpd.overlay(par_boundary,rsd_boundary,how='intersection',keep_geom_type=True)

	par_rsd_boundary = par_rsd_boundary.dropna(subset=[conparid,rsd_id_field]).copy()
	par_rsd_boundary['new_id'] = par_rsd_boundary[conparid].astype(str) + '_' + par_rsd_boundary[rsd_id_field].astype(str)
	par_rsd_boundary = par_rsd_boundary.dissolve(by='new_id').reset_index()
	# print(par_rsd_boundary.info()) to delete
	geom_blocking_cols = [conparid,rsd_id_field]
	return par_rsd_boundary,geom_blocking_cols





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




def read_rsd_dictionary(path_to_file,cen_parid_field,rsd_id_field,file_encoding):
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

	rsd_variables = [cen_parid_field,rsd_id_field]

	rsd_dict = pd.read_csv(path_to_file,sep="\t",quoting=3,usecols=rsd_variables,encoding=file_encoding)

	return rsd_dict


 

