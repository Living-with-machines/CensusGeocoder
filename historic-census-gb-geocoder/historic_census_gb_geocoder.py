# Main script that combines other scripts
import setupgeocoder
from datetime import datetime
import json

with open('./inputs/historic-census-gb-geocoder-params.json') as f:
	geocode_parameters = json.load(f)

input_data_path = geocode_parameters["input_data_path"]
output_data_path = geocode_parameters["output_data_path"]

for key, value in geocode_parameters["geocoding"].items():
	if value['type'] == 'no':
		continue
	else:

		start = datetime.now()

		country = key.split('_')[0]
		census_year = int(key.split('_')[1])
		parse_option = value['type']

		census_geocoder = setupgeocoder.CensusGB_geocoder(census_year,country,parse_option,input_data_path,output_data_path)
		print(vars(census_geocoder))

		os_roads, gb1900, census_unique_addresses, census_counties, census_processed = census_geocoder.preprocessing(value['use_existing_files'])
		full_output = census_geocoder.geocoding(census_unique_addresses,gb1900,os_roads,census_counties)
		final_output = census_geocoder.link_geocode_to_icem(census_processed,full_output)

		# Retain for testing purposes for now
		# print(dsh_output['sh_id'].is_unique)

		end_time = datetime.now() - start
		print('Time to run: ',end_time.total_seconds()/60)


