# Main script that combines other scripts
import setupgeocoder
from datetime import datetime
import json

with open('../inputs/historic-census-gb-geocoder-params.json') as f:
	geocode_parameters = json.load(f)

input_data_path = geocode_parameters["input_data_path"]
output_data_path = geocode_parameters["output_data_path"]

for key, value in geocode_parameters["geocoding"].items():
	if value['type'] == 'no':
		continue
	else:
		try:
			start = datetime.now()

			country = key.split('_')[0]
			census_year = int(key.split('_')[1])
			parse_option = value['type']

			census_geocoder = setupgeocoder.CensusGB_geocoder(census_year,country,parse_option,input_data_path,output_data_path)
			print(vars(census_geocoder))

			os_roads, gb1900, icem, census_counties = census_geocoder.preprocessing(value['use_existing_files'])
			dsh_output = census_geocoder.geocoding(icem,gb1900,os_roads,census_counties)

			# Retain for testing purposes for now
			# print(dsh_output['sh_id'].is_unique)

			end_time = datetime.now() - start
			print('Time to run: ',end_time.total_seconds()/60)

		except:
			print('An error occurred')
