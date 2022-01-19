import pandas as pd
import os
import numpy as np
import preprocess
import recordcomparison

class CensusGB_geocoder:
	"""
	Class to geo-code census data

	Attributes
	----------
	#### GENERAL
	census_year : int
		The census year to be geo-coded, specified in `data/historic-census-gb-geocoder-params.json`
	country_input: str
		The country to be geo-coded, specified in `data/historic-census-gb-geocoder-params.json`
	type: str
		The type of geo-coding to be run, sepcified in `data/historic-census-gb-geocoder-params.json`

	os_open_roads_filelist: list
		List of file paths for OS Open Road data.
	gb1900_file: str
		Path to GB1900 dataset.
	census_file: str
		Path to the census file to be geocoded.
	parish_shapefile_path: str
		Path to the Parish Boundary Shapefile for either England and Wales or Scotland.

	row_limit: int
		The number of rows of the OS Open Road and census file to read. If `type` parameter is 'full', then `row_limit` is None, which results in the full files being read. If `type` parameter is 'testing', then `row_limit` is 15,000. By limiting the number of rows of data read from the OS Open Road dataset and the census file, the script will run much quicker for testing purposes.

	output_dir: str
		The path to the folder in the `data/ouput` directory where all outputs from the geo-coding script are stored. E.g. `data/output/1901/scot`.

	field_dict: dict
		Dictionary containing the column or field names for the various datasets used as part of the geo-coding script. Contains the following keys: "country", "cen", "conparid", "conparid_alt", "os_road_id", "scot_parish", "parid_for_rsd_dict". The values for each key are set in the below E&W and Scotland specific variables.

	os_road_id: str
		Name of the unique id field for roads in the OS Open Roads after segmenting roads by RSD/Parish boundaries for specified census year. Created using 'road_id_' + final two digits of census year, e.g. 'road_id_01'. # In future I want to add the country into this name, e.g. 'EW' or 'Scot', and expand the last two digits of the census year so that the name includes the full census year.

	#### ENGLAND & WALES SPECIFIC
	conparid: str
		The 'ConParID' column name, either 'conparid_51-91' for 1851 to 1891 or 'conparid_01-11' for 1901 to 1911.
	cen: str
		The cen field found in the RSD Dictionary lookup files and RSD Boundary Shapefiles. Created using 'cen' + `census_year` attribute, e.g. 'CEN_1901'. Used to dissolve the RSD Shapefile to create the correct RSD boundaries for specified census year and to link these to RSD Dictionary lookup.
	rsd_shapefile_path: str
		Path to the England and Wales RSD Boundary Shapefile.
	rsd_dictionary_path: str
		Path to the England and Wales RSD Dictionary lookup file for the specified census year.
	ukds_gis_to_icem_path: str
		Path to lookup table that links England and Wales Parish Boundary Shapefile to the Consistent Parish Geographies (`ConParID` field) in I-CeM
	parid_for_rsd_dict: str
		Name of the `Par_ID` column in the England and Wales RSD Dictionary lookup file. For 1851,1861,1891,1901, and 1911 the column is labelled 'ParID'. The 1881 RSD Dictionary lookup file has two columns 'OLD_ParID' and 'NEW_ParID', we use 'NEW_ParID'.

	#### SCOTLAND SPECIFIC

	scot_parish_lkup_file: str
		Path to the lookup table that links the Scotland Parish boundary shapefile to the 'ParID' field in I-CeM.

	Methods
	----------
	set_conparid()
		Sets the label to be used for the 'ConParID' field.
	set_cen()
		Sets the label for the 'CEN_****' field for the specified census year in RSD Dictionary lookup files and RSD Boundary Shapefiles, e.g. 'CEN_1901'.
	set_os_road_id()
		Sets the unique id field for roads in OS Open Roads datasets after segmenting by boundary data, e.g. 'road_id_01'.
	set_rsd_shapefile()
		Sets the filepath to the England and Wales Registration Sub-District (RSD) Boundary shapefile.
	set_rsd_dictionary()
		Sets filepath to the England and Wales Registration Sub-District (RSD) dictionary lookup file.
	set_parish_shapefile()
		Sets the filepath to the Parish Boundary shapefile for England and Wales or Scotland.
	set_os_open_roads_filelist()
		Sets the list of shapefiles to be used from the OS Open Roads dataset.
	set_gb1900_file()
		Sets the GB1900 file.
	set_ukds_gis_to_icem_file()
		Sets the UKDS_GIS_to_icem file.
	set_census_file()
		Sets the census file to be geo-coded.
	set_par_id()
		Sets the ParID column label for the England and Wales Registration Sub-District (RSD) dictionary lookup file.
	set_row_limit()
		Sets the number of rows to read from OS Open Roads, GB1900, and Census file.
	set_output_dir()
		Sets the output directory to which all outputs are written. Creates directory if none exists.
	create_field_dict()
		Creates a dictionary that holds various column or field names from various input datasets.
	preprocessing()
		Pre-processes input files, returning OS Open Road data, GB1900, Census, and a list of census counties. Writes OS Open Road and GB1900 datasets segmented by historic parish/RSD boundaries.
	geocoding()
		Loops over each county in the census, geo-coding the census data for that county using OS Open Road Data and GB1900. Writes output files containing....
	summary_stats()
		Produces summary statistics, detailing the contents of the geo-coded outputs.

	"""

	def __init__(self,census_year,country_input,type):

		"""
		Parameters
		----------
		census_year : int
			The census year to be geo-coded, e.g. 1851, 1861, 1871, 1881, 1891, 1901, or 1911. Warning, no census data for England and Wales for 1871, and no Scottish census data for 1911.
		country_input: str
			Name of the census country to be geo-coded, either 'EW' for England and Wales, or 'scot' for Scotland
		type: str
			Specify type of geo-coding, use 'full' to geo-code entire year and country specified, or 'testing' to geo-code sample for testing/debugging purposes.
		"""

		"""
		GEO-CODING PARAMETERS PASSED FROM `data/historic-census-gb-geocoder-params.json`
		"""
		self.census_year = census_year
		self.country = country_input
		self.type = type

		"""
		GENERAL VARIABLES
		"""
		self.os_open_roads_filelist = self.set_os_open_roads_filelist()
		self.gb1900_file = self.set_gb1900_file()
		self.census_file = self.set_census_file()
		self.row_limit = self.set_row_limit()
		self.output_dir = self.set_output_dir()
		self.field_dict = self.create_field_dict()

		"""
		ENGLAND & WALES SPECIFIC VARIABLES
		"""
		self.rsd_shapefile_path = self.set_rsd_shapefile()
		self.rsd_dictionary_path = self.set_rsd_dictionary()
		self.parish_shapefile_path = self.set_parish_shapefile()
		self.ukds_gis_to_icem_path = self.set_ukds_gis_to_icem_file()

		"""
		SCOTLAND SPECIFIC VARIABLES
		"""
		self.scot_parish_lkup_file = self.set_scot_parish_lookup_file()

	def set_rsd_shapefile(self):
		"""
		Set path to Registration Sub-District (RSD) boundary shapefile. There is one shapefile for 1851-1911, the boundaries for a specific census year are created by dissolving the shapefile on a specified field. The pre-processing and dissolving are done by `process_rsd_boundary_data` in `preprocess.py`.

		Returns
		----------
		
		rsd_shapefile_path: str
			Path to RSD boundary shapefile

		"""
		if self.country == 'EW':
			rsd_shapefile_folder = 'data/input/rsd_boundary_data/'
			for root, directories, files in os.walk(rsd_shapefile_folder):
				for file in files:
					if file == 'RSD_1851_1911_JR.shp':
						rsd_shapefile_path = os.path.join(root,file)
		else:
			rsd_shapefile_path = None
		return rsd_shapefile_path

	def set_rsd_dictionary(self):
		"""
		Set path to Registration Sub-District (RSD) dictionary lookup for census year specified when initiating CensusGB_geocoder class, e.g. `CensusGB_geocoder(1881,'EW','testing')`

		Returns
		----------
		
		rsd_dictionary_path: str
			Path to RSD dictionary lookup file

		"""
		if self.country == 'EW':
			rsd_dictionary_folder = 'data/input/parish_dicts_encoding/'
			for root, directories, files in os.walk(rsd_dictionary_folder):
				for file in files:
					if str(self.census_year) in file and 'DICTIONARY_CODED' in file:
						rsd_dictionary_path = os.path.join(root,file)
		else:
			rsd_dictionary_path = None
		return rsd_dictionary_path

	def set_parish_shapefile(self):
		"""
		Set path to Parish boundary shapefile for census year specified when initiating CensusGB_geocoder class, e.g. `CensusGB_geocoder(1881,'EW','testing')`

		Returns
		----------
		
		parish_shapefile_path: str
			Path to Parish shapefile

		"""
		if self.country == 'EW':
			parish_shapefile_path = 'data/input/1851EngWalesParishandPlace/1851EngWalesParishandPlace.shp'
		else:
			if self.census_year <= 1891:
				parish_shapefile_path = 'data/input/scot_parish_boundary/CivilParish_pre1891/CivilParish_pre1891.shp'
			else:
				parish_shapefile_path = 'data/input/scot_parish_boundary/CivilParish1930/CivilParish1930.shp'

		return parish_shapefile_path

	def set_os_open_roads_filelist(self):
		"""
		Set path to Ordnance Survey Open Roads (OS Open Roads) dataset. For more documentation on OS Open Roads, see https://www.ordnancesurvey.co.uk/business-government/tools-support/open-map-roads-support. This function reads only the files with line vector data, labelled as `RoadLink.shp` and prefaced with the National Grid reference that they cover. The OS Open Roads dataset also includes nodes, which are ignored here.

		Returns
		----------
		
		os_open_roads_path_list: list containing str
			List containing the paths to OS Open Road line shapefiles.

		"""
		os_open_roads_filelist = []
		os_open_roads_folder = 'data/input/oproad_essh_gb-2/data'
		for root, directories, files in os.walk(os_open_roads_folder):
			for file in files:
				if 'RoadLink.shp' in file:
					os_open_roads_filelist.append(os.path.join(root,file))
		return os_open_roads_filelist

	def set_row_limit(self):
		"""
		Checks the `type` value specified when calling `CensusGB_geocoder`

		Returns
		----------
		
		rows: int or None
			Either None, in which case when passed to pandas `read_csv` or equivalent the argument is ignored, or an integer specifying the number of rows to read.

		"""
		if self.type == 'testing':
			rows = 15000
		elif self.type == 'full':
			rows = None
		return rows

	def set_conparid(self):
		"""
		TO COMPLETE

		Returns
		----------
		
		conparid: str
			TO COMPLETE
		conparid_alt: str
			TO COMPLETE

		"""
		if self.country == 'EW':
			if self.census_year in [1851,1861,1881,1891]:
				conparid = 'conparid_51-91'
			elif self.census_year in [1901,1911]:
				conparid = 'conparid_01-11'
		else:
			conparid = None
		return conparid

	def set_cen(self):
		"""
		Set the cen field for the specified census year. The cen field is found in the RSD Dictionary lookup files and RSD Boundary Shapefiles. Created using 'cen' + `census_year` attribute, e.g. 'CEN_1901'. `cen` is ued to dissolve the RSD Shapefile to create the correct RSD boundaries for specified census year and to link these to RSD Dictionary lookup.

		Returns
		----------
		
		cen: str
			Name of CEN column for specified census year, e.g. 'CEN_1901'.

		"""
		if self.country == 'EW':
			# cen = 'CEN_{}'.format(self.census_year)
			cen = f'CEN_{self.census_year}'
		else:
			cen = None
		return cen

	def set_os_road_id(self):
		"""
		Set the label of the unique id field for roads in the OS Open Roads dataset after processing and segmentation by RSD/parish boundary data for specified census year.
		
		Returns
		----------
		os_road_id: str
			Name of the unique id field for roads in the OS Open Roads after segmenting roads by RSD/Parish boundaries for specified census year. Created using 'road_id_' + final two digits of census year, e.g. 'road_id_01'. # In future I want to add the country into this name, e.g. 'EW' or 'Scot', and expand the last two digits of the census year so that the name includes the full census year.
		"""

		os_road_id = 'road_id_' + str(self.census_year)[-2:]
		return os_road_id

	def set_parid_for_rsd_dict(self):
		"""
		Set the label of the `Par_ID` column in the RSD Dictionary lookup file for the specified census year.
		
		Returns
		----------
		par_id: str
			Name of the `Par_ID` column in the RSD Dictionary lookup file. For 1851,1861,1891,1901, and 1911 the column is labelled 'ParID'. The 1881 RSD Dictionary lookup file has two columns 'OLD_ParID' and 'NEW_ParID', we use 'NEW_ParID'.
		"""
		if self.country == 'EW':
			if self.census_year in [1851,1861,1891,1901,1911]:
				parid_for_rsd_dict = 'ParID'
			elif self.census_year in [1881]:
				parid_for_rsd_dict = 'NEW_ParID'
		else:
			parid_for_rsd_dict = None
		return parid_for_rsd_dict
	
	def set_gb1900_file(self):
		"""
		Set the path to the GB1900 dataset.

		Returns
		----------
		gb1900_data: str
			Path to GB1900 dataset.
		"""
		gb1900_data = 'data/input/gb1900_gazetteer_complete_july_2018.csv'
		return gb1900_data

	def set_ukds_gis_to_icem_file(self):
		"""
		Set the path to 'UKDS_GIS_to_icem.xlsx' file, available from https://www.essex.ac.uk/research-projects/integrated-census-microdata. Lookup table that links Parish Boundary Shapefile to the Consistent Parish Geographies (`ConParID` field) in I-CeM

		Returns
		----------
		ukds_gis_to_icem_path: str
			Path to lookup table file.
		"""
		if self.country == 'EW':
			ukds_gis_to_icem_path = 'data/input/UKDS_GIS_to_icem.xlsx'
		else:
			ukds_gis_to_icem_path = None
		return ukds_gis_to_icem_path

	def set_scot_parish_lookup_file(self):
		"""
		# ADD

		Returns
		----------
		ukds_gis_to_icem_path: str #Change
			Path to lookup table file.#Change
		"""
		if self.country == 'scot':
			scot_parish_lkup_path = 'data/input/scot_parish_boundary/scotboundarylinking.xlsx'
		else:
			scot_parish_lkup_path = None
		return scot_parish_lkup_path



	def set_census_file(self):
		"""
		Set the path to the census file to be geocoded.

		Returns
		----------
		census_file: str
			Path to census file.
		"""
		census_folder = 'data/input/census_anonymisation_egress/'
		for root, directories, files in os.walk(census_folder):
			for file in files:
				if str(self.census_year) in file and self.country in file:
					census_file = os.path.join(root,file)
		return census_file

	def set_output_dir(self):
		# output_dir = 'data/output/{0}/{1}'.format(str(self.census_year),self.country)
		output_dir = f'data/output/{str(self.census_year)}/{self.country}'
		if os.path.exists(output_dir):
			# print('Output directory "{}" already exists'.format(output_dir)
			print(f'Output directory "{output_dir}" already exists')
		else:
			# print('Created output directory "{}"'.format(output_dir))
			print(f'Created output directory "{output_dir}"')
			os.makedirs(output_dir)
		return output_dir

	def create_field_dict(self):
		field_dict = {}
		field_dict['country'] = self.country
		field_dict['cen'] = self.set_cen()
		field_dict['conparid'] = self.set_conparid()
		field_dict['os_road_id'] = self.set_os_road_id()
		field_dict['scot_parish'] = 'ParID_link'
		field_dict['parid_for_rsd_dict'] = self.set_parid_for_rsd_dict()
		return field_dict



	def preprocessing(self):



		"""
		Pre-processes input files, returning OS Open Road data, GB1900, Census, and a list of census counties. Writes output of processed OS Open Road data segmented by RSD/Parish Boundary data.

		Returns
		---------
		
		segmented_os_roads_prepped: `geopandas.GeoDataFrame`
			GeoDataFrame of OS Open Roads data with additional attributes and new geometries based on RSD/Parish Boundaries attributes, which is ready to link to the census file. 
			The GeoDataFrame contains the following fields:

			`road_id_$` - unique id of road constructed from `nameTOID` + '_' + `new_id`.

			`name1` - name of road.

			`nameTOID`- unique id of road from base OS Open Roads Dataset.

			`new_id` - id created from `conparid_$` + '_' + `CEN_$`

			`conparid_$` - The ConParID that this road is within.

			`CEN_$` - The id of the RSD Unit that this road is within.

			`geometry` - Linestring or Multi Linestring geometry of a road.

		gb1900_processed: `geopandas.GeoDataFrame`
			GeoDataFrame of GB1900 data with additional attributes and new geometries based on RSD/Parish Boundaries attributes, which is ready to link to the census file. 
			The GeoDataFrame contains the following fields:

			`pid_id` - unique id of GB1900 label.

			`final_text` - transcribed map text label (e.g. the name of a street)

			`osgb_east`- Easting

			`osgb_north`- Northing

			`new_id` - id created from `conparid_$` + '_' + `CEN_$`

			`conparid_$` - The ConParID that this label is within.

			`CEN_$` - The id of the RSD Unit that this label is within.

			`geometry` - Point geometry of map text label.

		icem_processed: `pandas.DataFrame`
			DataFrame of census data with additional attributes from the RSD Dictionary lookup table, giving the RSD unit for each person.

			The DataFrame contains the following fields:

			`unique_add_id` - Unique id for an address comprised of `add_anon` + '_' + `ConParID` + '_' + `cen_$`.

			`ConParID` - The ConParID value from I-CeM

			`cen_$` - The id of the RSD Unit that this address lies within.

			`add_anon` - The street address, stripped of numerical digits to comply with egress from Turing DataSafeHaven.

			`RegCnty` - Census Registration County

			`sh_id_list` - List of the `safehaven_ids` that are associated with this unique address.

		census_counties: list
			Unique, sorted list of the names of Census Registration Counties in census file.

		"""
		if self.country == 'EW':
			processed = preprocess.process_rsd_boundary_data(self.rsd_shapefile_path,self.field_dict)
			ukds_link = preprocess.read_gis_to_icem(self.ukds_gis_to_icem_path,self.field_dict)
			parish = preprocess.process_parish_boundary_data(self.parish_shapefile_path,ukds_link,self.field_dict)
			parish_data_processed = preprocess.join_parish_rsd_boundary(parish,processed,self.field_dict)
			rsd_dictionary_processed = preprocess.read_rsd_dictionary(self.rsd_dictionary_path,self.field_dict)
		elif self.country == 'scot':
			scot_parish_link = preprocess.scot_parish_lookup(self.scot_parish_lkup_file,self.census_year)
			parish_data_processed = preprocess.process_scot_parish_boundary_data(self.parish_shapefile_path,scot_parish_link,self.census_year)
			rsd_dictionary_processed = None

		os_open_roads = preprocess.read_raw_os_data(self.os_open_roads_filelist,self.row_limit)

		segmented_os_roads = preprocess.segment_os_roads(os_open_roads,parish_data_processed,self.field_dict)
		segmented_os_roads_prepped = preprocess.icem_linking_prep(segmented_os_roads,self.field_dict)
		gb1900_processed = preprocess.process_gb1900(self.gb1900_file,parish_data_processed,self.field_dict,self.row_limit)


		# segmented_os_roads = preprocess.segment_os_roads(os_open_roads,parish_data_processed,self.cen,self.conparid_alt)
		# segmented_os_roads_prepped = preprocess.icem_linking_prep(segmented_os_roads,self.os_road_id,self.cen,self.conparid_alt)
		# gb1900_processed = preprocess.process_gb1900(self.gb1900_file,rsd_parish,self.conparid_alt,self.cen,self.row_limit)

		#segmented_os_roads_prepped.to_file('data/{0}/{1}_os_roads.shp'.format(self.census_year,self.census_year)) # Possibly remove
		# segmented_os_roads_prepped.to_csv(self.output_dir + '/{}_os_roads.tsv'.format(self.census_year),sep="\t")
		segmented_os_roads_prepped.to_csv(self.output_dir + f'/{self.census_year}_os_roads.tsv',sep="\t")
		#gb1900_processed.to_file('data/{0}/{1}_gb1900.shp'.format(self.census_year,self.census_year)) #Possibly remove
		gb1900_processed.to_csv(self.output_dir + '/{}_gb1900.tsv'.format(self.census_year),sep="\t")
		gb1900_processed.to_csv(self.output_dir + f'/{self.census_year}_gb1900.tsv',sep="\t")

		
		icem_processed, census_counties = preprocess.process_census(self.census_file,rsd_dictionary_processed,self.row_limit,self.field_dict)

		return segmented_os_roads_prepped,gb1900_processed, icem_processed, census_counties

	def geocoding(self,census,gb1900,segmented_os_roads,census_counties):
		"""
		Links census addresses to the geometry data for streets in OS Open Roads and GB1900.Takes outputs from `preprocessing` method, iterates over counties in census computing the similarity between census addresses and addresses in OS Open Roads and GB1900, outputs matches, duplicate matches for subsequent adjudication, and non-matches.

		Parameters
		---------
		census: `pandas.DataFrame`
			DataFrame containing pre-processed census data returned from the `preprocessing` method.
		gb1900: `geopandas.GeoDataFrame`
			GeoDataFrame containing pre-processed GB1900 data returned from the `preprocessing` method.
		segmented_os_roads: `geopandas.GeoDataFrame`
			GeoDataFrame containing pre-processed OS Open Roads data returned from the `preprocessing` method.
		census_counties: list
			List of Census Registration Counties returned from the `preprocessing` function.

		Returns
		---------

		"""
		dsh_output_list = []
		os_duplicate_list = []
		gb1900_duplicate_list = []

		census_output = census[['sh_id_list']].explode('sh_id_list',ignore_index=True)
		census_output = census_output.rename({'sh_id_list':'sh_id'},axis=1)
		print(census_output)

		for county in census_counties:
			print(county)
			census_subset = census[census['RegCnty'] == county].copy()
			census_subset = preprocess.compute_tfidf(census_subset).copy()
			gb1900_candidate_links = recordcomparison.gb1900_candidate_links(census_subset,gb1900,self.field_dict)
			gb1900_linked, gb1900_duplicates = recordcomparison.gb1900_compare(census_subset,gb1900,gb1900_candidate_links)
			os_candidate_links = recordcomparison.os_candidate_links(census_subset,segmented_os_roads,self.field_dict)
			os_linked, os_duplicates = recordcomparison.os_compare(census_subset,segmented_os_roads,os_candidate_links,self.field_dict)
			
			if os_linked.empty or gb1900_linked.empty: # Refine so that the script can run on one of these if the other is empty
				# print('No data in OS Open Roads or GB1900 for {}, skipping.'.format(county))
				print(f'No data in OS Open Roads or GB1900 for {county}, skipping.')
			else:
				cols_to_use = gb1900_linked.columns.difference(os_linked.columns) #can remove - see description below for why
				cols_to_use = cols_to_use.append(pd.Index(['unique_add_id','sh_id_list'])) #can remove - see description below for why

				# full_county_output = pd.merge(left=gb1900_linked[cols_to_use],right=os_linked,on='unique_add_id',how='outer',suffixes=['_gb1900','_os']) can remove - see description below for why
				full_county_output = pd.merge(left=gb1900_linked,right=os_linked,on='unique_add_id',how='outer',suffixes=['_gb1900','_os']) #it's important to have two fields one for gb1900 and one for os, so that we have the results for both. The previous approach kept only the details for OS links.

				full_county_output['sh_id_list'] = full_county_output['sh_id_list_gb1900'].fillna(full_county_output['sh_id_list_os'])
				full_county_output = full_county_output.drop(columns=['sh_id_list_gb1900','sh_id_list_os']) # Drop columns no longer needed as data contained in 'sh_id_list' column.
				full_county_output = full_county_output.explode('sh_id_list',ignore_index=True) # Explode the list of sh_ids
				full_county_output = full_county_output.rename({'sh_id_list':'sh_id'},axis=1) # Rename the sh_id_list column, which is no longer a list, to just 'sh_id'
				dsh_county_output = full_county_output[['sh_id','pin_id',self.field_dict['os_road_id']]] # Restrict version for linking to I-CeM in DSH to essential columns only
				
				# Write full county output to file
				full_county_output.to_csv(self.output_dir + '/{1}_{2}_full_county_output.tsv'.format(self.census_year,self.census_year,county),sep="\t",index=False)

				dsh_output_list.append(dsh_county_output) # Append DSH output for this county to a list of dfs

				os_duplicate_list.append(os_duplicates) # Append duplicate matches to OS Open Roads for this county to a list of dfs

				gb1900_duplicate_list.append(gb1900_duplicates) # Append duplicate matches to GB1900 for this county to a list of dfs

		print('Creating DSH outputs')
		if dsh_output_list == []:
			print('No DSH outputs to create')
			dsh_all_output = None
		else:
			dsh_all_output = pd.concat(dsh_output_list)
			
			print('Creating OS Duplicate matches outputs')
			os_duplicates_all = pd.concat(os_duplicate_list)
			os_duplicates_all = os_duplicates_all.explode('sh_id_list',ignore_index=True) # Explode the list of sh_ids
			os_duplicates_all = os_duplicates_all.rename({'sh_id_list':'sh_id'},axis=1)
			os_duplicates_all.to_csv(self.output_dir + '/os_duplicates.tsv',sep="\t",index=False)

			print('Creating GB1900 Duplicate matches outputs')
			gb1900_duplicates_all = pd.concat(gb1900_duplicate_list)
			gb1900_duplicates_all = gb1900_duplicates_all.explode('sh_id_list',ignore_index=True) # Explode the list of sh_ids
			gb1900_duplicates_all = gb1900_duplicates_all.rename({'sh_id_list':'sh_id'},axis=1)
			gb1900_duplicates_all.to_csv(self.output_dir + '/gb1900_duplicates.tsv',sep="\t",index=False)

			gb1900_linked_people = dsh_all_output['pin_id'].notna() # Mask people linked to GB1900
			os_linked_people = dsh_all_output[self.field_dict['os_road_id']].notna() # Mask people linked to OS Open Roads

			census2 = census_output.assign(gb1900_linked=census_output['sh_id'].isin(dsh_all_output[gb1900_linked_people]['sh_id']),
											os_linked=census_output['sh_id'].isin(dsh_all_output[os_linked_people]['sh_id']),
											gb1900_dup=census_output['sh_id'].isin(gb1900_duplicates_all['sh_id']),
											os_dup=census_output['sh_id'].isin(os_duplicates_all['sh_id']))


			census2['no_possible_match'] = np.where((census2['gb1900_linked'] == False) & (census2['os_linked'] == False) & (census2['gb1900_dup'] == False) & (census2['os_dup'] == False),True,False)

			dsh_all_output_final = pd.merge(left=dsh_all_output,right=census2,on='sh_id',how='left')
			# dsh_all_output_final.to_csv(self.output_dir + '/{}_dsh_output_combined.tsv'.format(self.census_year),sep="\t",index=False)
			dsh_all_output_final.to_csv(self.output_dir + f'/{self.census_year}_dsh_output_combined.tsv',sep="\t",index=False)

			all_inds_num = len(census_output)
			gb1900_linked_num = len(census2[census2['gb1900_linked'] == True])
			os_linked_num = len(census2[census2['os_linked'] == True])
			gb1900_dup_num = len(census2[census2['gb1900_dup'] == True])
			os_dup_num = len(census2[census2['os_dup'] == True])
			no_possible_match_num = len(census2[census2['no_possible_match'] == True])


			summary_dict = {'census_year':[self.census_year],
							'all_inds_num':[all_inds_num],
							'gb1900_linked_num':[gb1900_linked_num],
							'os_linked_num':[os_linked_num],
							'gb1900_dup_num':[gb1900_dup_num],
							'os_dup_num':[os_dup_num],
							'no_possible_match_num':[no_possible_match_num]}

			summary_df = pd.DataFrame(summary_dict)

			# summary_df.to_csv(self.output_dir + '/{}_summary_stat.tsv'.format(self.census_year),sep="\t",index=False)
			summary_df.to_csv(self.output_dir + f'/{self.census_year}_summary_stat.tsv',sep="\t",index=False)


			# print('GB1900 linked: ',(len(census2[census2['gb1900_linked'] == True]) / all_inds) * 100)
			# print('OS Open Roads linked: ',(len(census2[census2['os_linked'] == True]) / all_inds) * 100)
			# print('GB1900 Duplicate Matches: ',(len(census2[census2['gb1900_dup'] == True]) / all_inds) * 100)
			# print('OS Duplicate Matches: ',(len(census2[census2['os_dup'] == True]) / all_inds) * 100)
			# print('No Possible Matches: ',(len(census2[census2['no_possible_match'] == True]) / all_inds) * 100)

		return dsh_all_output










	def aggregate_stats(self,gb1900_all,os_all):
		# Output a full
		# Calculate length of shid_list; then groupby pin_id or road_id and sum the shid_list count field to get the number of people linked to that point or road.
		# 
		gb1900_all['length'] = gb1900_all['sh_id_list'].str.len()
		#gb1900_census_roads_output_counts = gb1900_all.groupby(['pin_id','unique_add_id']).size().reset_index(name='count') # count number of individuals linked to each gb1900 point

		#census_roads_output_counts = census_roads_output_final.groupby([index_name,'unique_add_id']).size().reset_index(name='count') # count number of indivdiuals linked to each os road

		return gb1900_all

	# Add function for output stats collection


"""
# Save output of segmentation (because it takes so long ideally the segmentation won't need to be re-run each time if we make other edits to this script)

print('writing segmented road shapefile')
segmented_os_roads.to_file('data/outputs/os_vector_data_processed_new/segmented_os_roads.shp')

# Writing aggregated outputs as shapefile and geoJSON
print('writing aggregated shapefiles')
segmented_os_roads_to_icem_aggregated.to_file('data/outputs/os_vector_data_processed_new/segmented_os_roads_to_icem_1901-1911.shp')


"""

