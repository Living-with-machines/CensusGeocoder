# Main script that combines other scripts
import setupgeocoder
from datetime import datetime

year_list = [1891,1901,1911]

start = datetime.now()

for year in year_list:
	# Initiate census geocoder
	census_geocoder = setupgeocoder.CensusGB_geocoder(year,'EW','full')
	print(vars(census_geocoder))

	os_roads, gb1900, icem, census_counties = census_geocoder.preprocessing()
	dsh_output = census_geocoder.geocoding(icem,gb1900,os_roads,census_counties)

	print(dsh_output['sh_id'].is_unique)

	end_time = datetime.now() - start
	print('Time to run: ',end_time.total_seconds()/60)


