# Main script that combines other scripts
import setupgeocoder
from datetime import datetime
import json

with open('data/historic-census-gb-geocoder-params.json') as f:
	geocode_parameters = json.load(f)

for key, value in geocode_parameters.items():
	if value == 'no':
		continue
	else:

		start = datetime.now()

		country = key.split('_')[0]
		census_year = int(key.split('_')[1])
		type = value

		census_geocoder = setupgeocoder.CensusGB_geocoder(census_year,country,type)
		print(vars(census_geocoder))

		os_roads, gb1900, icem, census_counties = census_geocoder.preprocessing()
		dsh_output = census_geocoder.geocoding(icem,gb1900,os_roads,census_counties)

		# Retain for testing purposes for now
		# print(dsh_output['sh_id'].is_unique)

		end_time = datetime.now() - start
		print('Time to run: ',end_time.total_seconds()/60)
