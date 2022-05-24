import pandas as pd
import os
import numpy as np
import preprocess
import recordcomparison
import geopandas as gpd
import pathlib

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
	parse_option: str
		The parse_option of geo-coding to be run, specified in `data/historic-census-gb-geocoder-params.json`
	input_data_path: str
		The path to the `data/` folder, where the datasets needed to run the code are stored
	output_data_path: str
		The path to the outputs directory, where all outputs from the geo-coding script are stored. E.g. `data/output/1901/SCOT`.

	os_open_roads_filelist: list
		List of file paths for OS Open Road data.
	gb1900_file: str
		Path to GB1900 dataset.
	census_file: str
		Path to the census file to be geocoded.
	parish_shapefile_path: str
		Path to the Parish Boundary Shapefile for either England and Wales or Scotland.

	row_limit: int
		The number of rows of the OS Open Road and census file to read. If `parse_option` parameter is 'full', then `row_limit` is None, which results in the full files being read. If `parse_option` parameter is 'testing', then `row_limit` is 15,000. By limiting the number of rows of data read from the OS Open Road dataset and the census file, the script will run much quicker for testing purposes.

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

	def __init__(self,census_year,country_input,parse_option,input_data_path,output_data_path,reuse_data):

		"""
		Parameters
		----------
		census_year : int
			The census year to be geo-coded, e.g. 1851, 1861, 1871, 1881, 1891, 1901, or 1911. Warning, no census data for England and Wales for 1871, and no Scottish census data for 1911. Specified in parameters json.
		country_input: str
			Name of the census country to be geo-coded, either 'EW' for England and Wales, or 'SCOT' for Scotland. Specified in parameters json.
		parse_option: str
			Specify type of geo-coding, use 'full' to geo-code entire year and country specified, or 'testing' to geo-code sample for testing/debugging purposes. Specified in parameters json.
		input_data_path: str
			Specify the path to the `data/` folder, where the datasets needed to perform the geocoding are stored.
		output_data_path: str
			Specify the path to the outputs folder, where the outputs are stored.
		reuse_data: str
			If value is 'yes' and the source data has already been preprocessed, reuse preprocessed data. If value is 'no', preprocess data.
		"""

		"""
		GEO-CODING PARAMETERS PASSED FROM `data/historic-census-gb-geocoder-params.json`
		"""
		self.census_year = census_year
		self.country = country_input
		self.parse_option = parse_option
		self.input_data_path = input_data_path
		self.output_data_path = output_data_path
		self.reuse_data = reuse_data

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
		# rsd_shapefile_path = None
		# if self.reuse_data == 'yes':
		# 	return rsd_shapefile_path

		if self.country == 'EW':
			rsd_shapefile_folder = self.input_data_path + 'data/input/rsd_boundary_data/'
			for root, directories, files in os.walk(rsd_shapefile_folder):
				for file in files:
					if file == 'RSD_1851_1911_JR.shp':
						rsd_shapefile_path = os.path.join(root,file)
		return rsd_shapefile_path

	def set_rsd_dictionary(self):
		"""
		Set path to Registration Sub-District (RSD) dictionary lookup for census year specified when initiating CensusGB_geocoder class, e.g. `CensusGB_geocoder(1881,'EW','testing')`

		Returns
		----------
		
		rsd_dictionary_path: str
			Path to RSD dictionary lookup file

		"""
		# rsd_dictionary_path = None
		# if self.reuse_data == 'yes':
		# 	return rsd_dictionary_path

		if self.country == 'EW':
			rsd_dictionary_folder = self.input_data_path + 'data/input/parish_dicts_encoding/'
			for root, directories, files in os.walk(rsd_dictionary_folder):
				for file in files:
					if str(self.census_year) in file and 'DICTIONARY_CODED' in file:
						rsd_dictionary_path = os.path.join(root,file)
		return rsd_dictionary_path

	def set_parish_shapefile(self):
		"""
		Set path to the appropriate Parish boundary shapefile for the census year and country specified in parameters json.

		Returns
		----------
		
		parish_shapefile_path: str
			Path to Parish shapefile

		"""
		# parish_shapefile_path = None
		# if self.reuse_data == 'yes':
		# 	return parish_shapefile_path

		if self.country == 'EW':
			parish_shapefile_path = self.input_data_path + 'data/input/1851EngWalesParishandPlace/1851EngWalesParishandPlace.shp'
		else:
			if self.census_year <= 1891:
				parish_shapefile_path = self.input_data_path + 'data/input/scot_parish_boundary/CivilParish_pre1891/CivilParish_pre1891.shp'
			else:
				parish_shapefile_path = self.input_data_path + 'data/input/scot_parish_boundary/CivilParish1930/CivilParish1930.shp'

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
		# if self.reuse_data == 'yes':
		# 	return os_open_roads_filelist

		os_open_roads_folder = self.input_data_path + 'data/input/oproad_essh_gb-2/data'
		for root, directories, files in os.walk(os_open_roads_folder):
			for file in files:
				if 'RoadLink.shp' in file:
					os_open_roads_filelist.append(os.path.join(root,file))
		return os_open_roads_filelist

	def set_row_limit(self):
		"""
		Checks the `parse_option` value pecified in parameters json.

		Returns
		----------
		
		rows: int or None
			Either None, in which case when passed to pandas `read_csv` or equivalent the argument is ignored, or an integer specifying the number of rows to read.

		"""
		rows = None
		if self.parse_option == 'testing':
			rows = 15000
		return rows

	def set_conparid(self):
		"""
		Set the consistent parish id field for the appropriate census year and country. No consistent parish id used for Scotland. There are two consistent parish ids for England and Wales, one that covers 1851 to 1891, and a second that covers 1901 to 1911.

		Returns
		----------
		
		conparid: str
			Appropriate census year / country ConParID field name for I-CeM.

		"""
		conparid = None
		if self.country == 'EW':
			if self.census_year in [1851,1861,1881,1891]:
				conparid = 'conparid_51-91'
			elif self.census_year in [1901,1911]:
				conparid = 'conparid_01-11'
		return conparid

	def set_cen(self):
		"""
		Set the cen field for the specified census year. The cen field is found in the RSD Dictionary lookup files and RSD Boundary Shapefiles. Created using 'cen' + `census_year` attribute, e.g. 'CEN_1901'. `cen` is used to dissolve the RSD Shapefile to create the correct RSD boundaries for specified census year and to link these to RSD Dictionary lookup. England and Wales only.

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
		Set the label of the unique id field for roads in the OS Open Roads dataset after processing and segmentation by RSD/parish boundary data for specified census year and country.
		
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
		parid_for_rsd_dict = None
		if self.country == 'EW':
			if self.census_year in [1851,1861,1891,1901,1911]:
				parid_for_rsd_dict = 'ParID'
			elif self.census_year in [1881]:
				parid_for_rsd_dict = 'NEW_ParID'
		return parid_for_rsd_dict
	
	def set_gb1900_file(self):
		"""
		Set the path to the GB1900 dataset.

		Returns
		----------
		gb1900_data: str
			Path to GB1900 dataset.
		"""
		# gb1900_data = None
		# if self.reuse_data == 'yes':
		# 	return gb1900_data

		gb1900_data = self.input_data_path + 'data/input/gb1900_gazetteer_complete_july_2018.csv'
		return gb1900_data

	def set_ukds_gis_to_icem_file(self):
		"""
		Set the path to 'UKDS_GIS_to_icem.xlsx' file, available from https://www.essex.ac.uk/research-projects/integrated-census-microdata. Lookup table that links Parish Boundary Shapefile to the Consistent Parish Geographies (`ConParID` field) in I-CeM. England and Wales only.

		Returns
		----------
		ukds_gis_to_icem_path: str
			Path to lookup table file.
		"""
		# ukds_gis_to_icem_path = None
		# if self.reuse_data == 'yes':
		# 	return ukds_gis_to_icem_path
		
		if self.country == 'EW':
			ukds_gis_to_icem_path = self.input_data_path + 'data/input/UKDS_GIS_to_icem.xlsx'
			
		return ukds_gis_to_icem_path

	def set_scot_parish_lookup_file(self):
		"""
		Set path to the lookup table for Scottish boundary data. Currently only 1901 is available. Scotland only.

		Returns
		----------
		scot_parish_lkup_path: str
			Path to lookup table file.
		"""
		# scot_parish_lkup_path = None
		# if self.reuse_data == 'yes':
		# 	return scot_parish_lkup_path

		if self.country == 'SCOT':
			scot_parish_lkup_path = self.input_data_path + 'data/input/scot_parish_boundary/scotboundarylinking.xlsx'
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
		# census_file = None
		# if self.reuse_data == 'yes':
		# 	return census_file

		census_folder = self.input_data_path + 'data/input/census_anonymisation_egress/'
		for root, directories, files in os.walk(census_folder):
			for file in files:
				if str(self.census_year) in file and self.country in file:
					census_file = os.path.join(root,file)
		return census_file

	def set_output_dir(self):
		"""
		Set the output directory in the format e.g. `data/output/1901/EW/full`. Checks if output directory exists, if it doesn't it creates a directory. 

		Returns
		----------
		output_dir: str
			Path to output directory.
		"""

		output_dir = self.output_data_path + f'data/output/{str(self.census_year)}/{self.country}/{self.parse_option}'
		pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
		return output_dir

	def create_field_dict(self):
		"""
		Create a dictionary of values and field column names for use in various stages of the geo-coding process to allow code to select the correct column names and parameters depending on the year or country specified.

		Returns
		----------
		field_dict: dictionary
			Dictionary containing values and field names.
		"""
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
		Checks for existing pre-processed files, if these exist, it reads the files and moves to the geo-coding phase. If pre-processed files don't exist, it pre-processes input files, returning OS Open Road data, GB1900, a processed version of the census, a census subset only including unique addresses, and a list of census counties. It writes full versions of processed OS Open Road Data, GB1900, and processed census data, as well as a subset of the census data only including unique addresses and a list of census counties.

		Writes to output files
		---------
		
		segmented_os_roads_prepped: `geopandas.GeoDataFrame`
			GeoDataFrame of OS Open Roads data with additional attributes and new geometries based on RSD/Parish Boundaries attributes, which is ready to link to the census file. 
			The GeoDataFrame contains the following fields:

			`road_id_{}` - unique id of road constructed from `nameTOID` + '_' + `new_id`. {} populated with last two digits of census year e.g. 'road_id_61' for 1861. To be improved e.g. add full census year and country.

			`name1` - name of road from base OS Open Roads Dataset.

			`nameTOID`- unique id of road from base OS Open Roads Dataset.
			
			`new_id` - id created from either, England and Wales: `conparid_$` + '_' + `CEN_$`; Scotland: `ParID`.

			`geometry` - Linestring or Multi Linestring geometry of a road.

			`conparid_$` - The ConParID that this road is within. ***England and Wales ONLY***

			`CEN_$` - The id of the RSD Unit that this road is within. ***England and Wales ONLY***

			`ParID_link` - The ParID that this road is within. ***Scotland ONLY***


		gb1900_processed: `geopandas.GeoDataFrame`
			GeoDataFrame of GB1900 data with additional attributes and new geometries based on RSD/Parish Boundaries attributes, which is ready to link to the census file. 
			The GeoDataFrame contains the following fields:

			`pid_id` - unique id of GB1900 label.

			`final_text` - transcribed map text label (e.g. the name of a street)

			`osgb_east`- Easting

			`osgb_north`- Northing
			
			`geometry` - Point geometry of map text label.

			`new_id` - id created from either, England and Wales: `conparid_$` + '_' + `CEN_$`; Scotland: `ParID`.

			`conparid_$` - The ConParID that this label is within. ***England and Wales ONLY***

			`CEN_$` - The id of the RSD Unit that this label is within. ***England and Wales ONLY***

			`ParID_link` - The ParID that this road is within. ***Scotland ONLY***

		census_counties: list
			Unique, sorted list of the names of Census Registration Counties in census file.

		census_processed: `pandas.DataFrame`
			DataFrame of census data with additional attributes from the RSD Dictionary lookup table, giving the RSD unit for each person.

			The DataFrame contains the following fields:

			`unique_add_id` - Unique id for an address comprised of `add_anon` + '_' + `ConParID` + '_' + `cen_$`.

			`add_anon` - The street address, stripped of numerical digits to comply with egress from Turing DataSafeHaven.

			`RegCnty` - Census Registration County

			`sh_id_list` - List of the `safehaven_ids` that are associated with this unique address.

			`ConParID` - The ConParID value from I-CeM ***England and Wales ONLY***

			`cen_$` - The id of the RSD Unit that this address lies within. ***England and Wales ONLY***

			`ParID` - The ParID value from I-CeM ***Scotland ONLY***

		census_unique_addresses: `pandas.DataFrame`
			DataFrame of unique addresses from census with additional attributes to perform geo-blocking in geocoding function.

			The DataFrame contains the following fields:

			`unique_add_id` - Unique id for an address comprised of `add_anon` + '_' + `ConParID` + '_' + `cen_$`.

			`add_anon` - The street address, stripped of numerical digits to comply with egress from Turing DataSafeHaven.

			`RegCnty` - Census Registration County

			`ConParID` - The ConParID value from I-CeM ***England and Wales ONLY***

			`cen_$` - The id of the RSD Unit that this address lies within. ***England and Wales ONLY***

			`ParID` - The ParID value from I-CeM

		Returns
		--------
				segmented_os_roads_prepped: `geopandas.GeoDataFrame`
			GeoDataFrame of OS Open Roads
			The GeoDataFrame contains the following fields:

			`road_id_{}` - unique id of road constructed from `nameTOID` + '_' + `new_id`. {} populated with last two digits of census year e.g. 'road_id_61' for 1861. To be improved e.g. add full census year and country.

			`name1` - name of road from base OS Open Roads Dataset.
			
			`new_id` - id created from either, England and Wales: `conparid_$` + '_' + `CEN_$`; Scotland: `ParID`.

			`conparid_$` - The ConParID that this road is within. ***England and Wales ONLY***

			`CEN_$` - The id of the RSD Unit that this road is within. ***England and Wales ONLY***

			`ParID_link` - The ParID that this road is within. ***Scotland ONLY***


		gb1900_processed: `geopandas.GeoDataFrame`
			GeoDataFrame of GB1900 data with additional attributes and new geometries based on RSD/Parish Boundaries attributes, which is ready to link to the census file. 
			The GeoDataFrame contains the following fields:

			`pid_id` - unique id of GB1900 label.

			`final_text` - transcribed map text label (e.g. the name of a street)

			`new_id` - id created from either, England and Wales: `conparid_$` + '_' + `CEN_$`; Scotland: `ParID`.

			`conparid_$` - The ConParID that this label is within. ***England and Wales ONLY***

			`CEN_$` - The id of the RSD Unit that this label is within. ***England and Wales ONLY***

			`ParID_link` - The ParID that this road is within. ***Scotland ONLY***

		census_counties: list
			Unique, sorted list of the names of Census Registration Counties in census file.

		census_processed: `pandas.DataFrame`
			DataFrame of census data with additional attributes from the RSD Dictionary lookup table, giving the RSD unit for each person.

			The DataFrame contains the following fields:

			`unique_add_id` - Unique id for an address comprised of `add_anon` + '_' + `ConParID` + '_' + `cen_$`.

			`add_anon` - The street address, stripped of numerical digits to comply with egress from Turing DataSafeHaven.

			`RegCnty` - Census Registration County

			`sh_id` - Safehaven_id for individual.

			`ConParID` - The ConParID value from I-CeM ***England and Wales ONLY***

			`cen_$` - The id of the RSD Unit that this address lies within. ***England and Wales ONLY***

			`ParID` - The ParID value from I-CeM ***Scotland ONLY***

		census_unique_addresses: `pandas.DataFrame`
			DataFrame of unique addresses from census with additional attributes to perform geo-blocking in geocoding function.

			The DataFrame contains the following fields:

			`unique_add_id` - Unique id for an address comprised of `add_anon` + '_' + `ConParID` + '_' + `cen_$`.

			`add_anon` - The street address, stripped of numerical digits to comply with egress from Turing DataSafeHaven.

			`RegCnty` - Census Registration County

			`ConParID` - The ConParID value from I-CeM ***England and Wales ONLY***

			`cen_$` - The id of the RSD Unit that this address lies within. ***England and Wales ONLY***

			`ParID` - The ParID value from I-CeM

		"""

		segmented_os_roads_prepped = None
		gb1900_processed = None
		census_processed = None
		census_unique_addresses = None
		census_counties = None

		os_roads_processed_outputfile = self.output_dir + f'/os_roads_{self.census_year}_{self.country}_{self.parse_option}.tsv'
		gb1900_processed_outputfile = self.output_dir + f'/gb1900_{self.census_year}_{self.country}_{self.parse_option}.tsv'
		census_processed_outputfile = self.output_dir + f'/census_processed_{self.census_year}_{self.country}_{self.parse_option}.tsv'
		census_unique_addresses_outputfile = self.output_dir + f'/census_unique_addresses_{self.census_year}_{self.country}_{self.parse_option}.tsv'
		census_counties_outputfile = self.output_dir + f'/census_counties_{self.census_year}_{self.country}_{self.parse_option}.txt'

		os_roads_processed_outputfile_exists = os.path.exists(os_roads_processed_outputfile)
		gb1900_processed_outputfile_exists = os.path.exists(gb1900_processed_outputfile)
		census_processed_outputfile_exists = os.path.exists(census_processed_outputfile)
		census_unique_addresses_outputfile_exists = os.path.exists(census_unique_addresses_outputfile)
		census_counties_outputfile_exists = os.path.exists(census_counties_outputfile)

		# Process parish data
		parish_data_processed = None
		if not os_roads_processed_outputfile_exists or not gb1900_processed_outputfile_exists:
			print("Process parish data")
			if self.country == 'EW':
				processed = preprocess.process_rsd_boundary_data(self.rsd_shapefile_path,self.field_dict)
				ukds_link = preprocess.read_gis_to_icem(self.ukds_gis_to_icem_path,self.field_dict)
				parish = preprocess.process_parish_boundary_data(self.parish_shapefile_path,ukds_link,self.field_dict)
				parish_data_processed = preprocess.join_parish_rsd_boundary(parish,processed,self.field_dict)
			elif self.country == 'SCOT':
				scot_parish_link = preprocess.scot_parish_lookup(self.scot_parish_lkup_file,self.census_year)
				parish_data_processed = preprocess.process_scot_parish_boundary_data(self.parish_shapefile_path,scot_parish_link,self.census_year)

		# Read or process OS Roads

		if self.country == 'EW':
			os_road_cols = [self.field_dict['os_road_id'],self.field_dict['conparid'],self.field_dict['cen'],'name1']
		else:
			os_road_cols = [self.field_dict['os_road_id'],self.field_dict['scot_parish'],'name1']


		# 			blocking_fields_l.append('ParID')
		# 	blocking_fields_r.append(field_dict['scot_parish'])
		# elif field_dict['country'] == 'EW':
		# 	blocking_fields_l.append('ConParID')
		# 	blocking_fields_l.append(field_dict['cen'])

		if os_roads_processed_outputfile_exists and self.reuse_data == 'yes':
			print('Pre-processed OS roads files already exist, reading pre-processed files')
			segmented_os_roads_prepped = pd.read_csv(os_roads_processed_outputfile,sep="\t",index_col=self.field_dict['os_road_id'],usecols=os_road_cols)
			# print(segmented_os_roads_prepped)
			# segmented_os_roads_prepped = gpd.GeoDataFrame(segmented_os_roads_prepped, geometry=gpd.GeoSeries.from_wkt(segmented_os_roads_prepped['geometry']),crs='EPSG:27700')
		else:
			os_open_roads = preprocess.read_raw_os_data(self.os_open_roads_filelist,self.row_limit)
			segmented_os_roads = preprocess.segment_os_roads(os_open_roads,parish_data_processed,self.field_dict)
			segmented_os_roads_prepped = preprocess.icem_linking_prep(segmented_os_roads,self.field_dict)
			# Output processed file
			segmented_os_roads_prepped.to_csv(os_roads_processed_outputfile,sep="\t") # OS Roads
			segmented_os_roads_prepped = segmented_os_roads_prepped[os_road_cols[1:]]

		# Read or process GB1900:
		if self.country == 'EW':
			gb1900_cols = ['pin_id',self.field_dict['conparid'],self.field_dict['cen'],'final_text']
		else:
			gb1900_cols = ['pin_id',self.field_dict['scot_parish'],'final_text']

		if gb1900_processed_outputfile_exists and self.reuse_data == 'yes':
			print('Pre-processed GB1900 files already exist, reading pre-processed files')
			gb1900_processed = pd.read_csv(gb1900_processed_outputfile,sep="\t",index_col='pin_id',usecols=gb1900_cols)
			# gb1900_processed = gpd.GeoDataFrame(gb1900_processed, geometry=gpd.GeoSeries.from_wkt(gb1900_processed['geometry']),crs='EPSG:27700')
			# print(gb1900_processed)
		else:
			gb1900_processed = preprocess.process_gb1900(self.gb1900_file,parish_data_processed,self.field_dict,self.row_limit)
			# Output processed file
			gb1900_processed.to_csv(gb1900_processed_outputfile,sep="\t")
			# print(gb1900_processed)
			gb1900_processed = gb1900_processed[gb1900_cols[1:]]

		# Read or process ICEM and census counties:	
		if census_processed_outputfile_exists and census_unique_addresses_outputfile_exists and census_counties_outputfile_exists and self.reuse_data == 'yes':
			print('Pre-processed ICEM files already exist, reading pre-processed files')
			# census_processed = pd.read_csv(census_processed_outputfile,sep="\t")

			census_unique_addresses = pd.read_csv(census_unique_addresses_outputfile,sep="\t",index_col='unique_add_id')

			print('Pre-processed census county list file already exists, reading pre-processed file')
			census_counties = []
			with open(census_counties_outputfile,'r') as f:
				for line in f:
					census_counties.append(str(line).strip('\n'))
				print(census_counties)
			
			census_processed = pd.read_csv(census_processed_outputfile,sep="\t")
		else:
			# Process RSD dictionary
			rsd_dictionary_processed = None
			if self.country == 'EW':
				rsd_dictionary_processed = preprocess.read_rsd_dictionary(self.rsd_dictionary_path,self.field_dict)
			census_processed, census_unique_addresses, census_counties = preprocess.process_census(self.census_file,rsd_dictionary_processed,self.row_limit,self.field_dict)
			census_processed.to_csv(census_processed_outputfile,sep="\t",index=False)
			census_unique_addresses.to_csv(census_unique_addresses_outputfile,sep="\t") # Census Processed
			with open (census_counties_outputfile,'w') as f:
				for county in census_counties:
					f.write(str(county) +"\n")


		return segmented_os_roads_prepped,gb1900_processed, census_unique_addresses, census_counties, census_processed

	def geocoding(self,census,gb1900,segmented_os_roads,census_counties):
		"""
		Links census addresses to the geometry data for streets in OS Open Roads and GB1900.Takes outputs from `preprocessing` method, iterates over counties in census computing the similarity between census addresses and addresses in OS Open Roads and GB1900.
		
		Writes the results for each county, the whole country, as well as duplicate matches.

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
		Currently doesn't pass anything on to another function.

		"""
		full_output_list = []

		for county in census_counties:
			print(county)
			census_subset = census[census['RegCnty'] == county].copy()

			census_subset = preprocess.compute_tfidf(census_subset).copy()

			print(self.field_dict)
			gb1900_candidate_links = recordcomparison.gb1900_candidate_links(census_subset,gb1900,self.field_dict)
			gb1900_linked, gb1900_duplicates = recordcomparison.gb1900_compare(census_subset,gb1900,gb1900_candidate_links)
			os_candidate_links = recordcomparison.os_candidate_links(census_subset,segmented_os_roads,self.field_dict)
			os_linked, os_duplicates = recordcomparison.os_compare(census_subset,segmented_os_roads,os_candidate_links,self.field_dict)

			if os_linked.empty or gb1900_linked.empty: # Refine so that the script can run on one of these if the other is empty
				# print('No data in OS Open Roads or GB1900 for {}, skipping.'.format(county))
				print(f'No data in OS Open Roads or GB1900 for {county}, skipping.')
			else:
				full_county_output = pd.merge(left=gb1900_linked,right=os_linked,on='unique_add_id',how='outer',suffixes=['_gb1900','_os'])
				full_county_duplicate_output = pd.merge(left=gb1900_duplicates,right=os_duplicates,on='unique_add_id',how='outer',suffixes=['_gb1900','_os'])
				# print(full_county_duplicate_output)
				# Write full county output to file
				full_county_output.to_csv(self.output_dir + '/{1}_{2}_full_county_output.tsv'.format(self.census_year,self.census_year,county),sep="\t",index=False)

				full_county_duplicate_output.to_csv(self.output_dir + '/{1}_{2}_full_county_duplicate_output.tsv'.format(self.census_year,self.census_year,county),sep="\t",index=False)
				full_output_list.append(full_county_output) # Append DSH output for this county to a list of dfs


		print('Creating DSH outputs')
		if full_output_list == []:
			print('No DSH outputs to create')
			full_all_output = None
		else:
			full_all_output = pd.concat(full_output_list)
			full_all_output.to_csv(self.output_dir + '/{0}_full_output.tsv'.format(self.census_year),sep="\t",index=False)


		return full_all_output

	def link_geocode_to_icem(self,census_processed,geocoded_addressses):
		# census_processed = pd.read_csv('/Users/jrhodes/historic-census-gb-geocoder/data/testing_outputs/data/output/1851/EW/testing/census_processed_1851_EW_testing.tsv',sep="\t")
		outputting = pd.merge(left=census_processed,right=geocoded_addressses,on='unique_add_id',how='left')
		print(outputting)
		outputting.to_csv(self.output_dir + '/outputting_trial.txt',sep="\t")
		pass


