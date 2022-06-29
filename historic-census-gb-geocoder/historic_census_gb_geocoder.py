# Main script that combines other scripts
import setupgeocoder
from datetime import datetime
import json

with open("./inputs/historic-census-gb-geocoder-config.json") as f:
    geocode_config = json.load(f)

# Call a json checker function here

for census_country, census_year in geocode_config["census_config"].items():
    for year, year_config in census_year.items():
        census_year = int(year)
        start = datetime.now()
        if year_config["runtype"] != "no":
            if census_country == "EW":
                census_geocoder = setupgeocoder.EW_geocoder(
                    census_country,
                    census_year,
                    year_config,
                    geocode_config["target_geoms"],
                    geocode_config["path_to_data"],
                    geocode_config["ew_config"],
                )
                (
                    rsd_dictionary_processed,
                    processed_parish_boundary_data,
                    geom_blocking_cols,
                ) = census_geocoder.create_ew_parishboundaryprocessed()
                (
                    census_blocking_cols,
                    census_counties,
                ) = census_geocoder.process_ew_census(rsd_dictionary_processed)
            elif census_country == "SCOT":
                census_geocoder = setupgeocoder.SCOT_geocoder(
                    census_country,
                    year,
                    year_config,
                    geocode_config["target_geoms"],
                    geocode_config["path_to_data"],
                    geocode_config["scot_config"],
                )
                processed_parish_boundary_data = (
                    census_geocoder.create_scot_parishboundaryprocessed()
                )
                census_geocoder.process_scot_census()

            census_geocoder.geocoding_new(
                processed_parish_boundary_data,
                census_blocking_cols,
                geom_blocking_cols,
                census_counties,
            )

            end_time = datetime.now() - start
            print("Time to run: ", end_time.total_seconds() / 60)
