# Main script that combines other scripts
import setupgeocoder

# from datetime import datetime
import yaml
import config


def get_year_country(census):
    census_country = census.split("_")[0]
    census_year = int(census.split("_")[1])
    return census_year, census_country


with open("inputs/input_config.yaml", "r") as f:
    geocode_config = yaml.load(f, Loader=yaml.FullLoader)

# print(geocode_config)

config.validate_configs(geocode_config)

gen = config.General(**geocode_config["general"])


for x, y in geocode_config["census_config"].items():
    census_configuration = config.Censusconfiguration(**y)
    ew_configuration = config.EW_configuration(
        census_configuration.year, **geocode_config["ew_config"]
    )

    if census_configuration.runtype is True:
        print("#" * 88)
        print(census_configuration.year, census_configuration.country)
        print("#" * 88)
        if census_configuration.country == "EW":
            census_geocoder = setupgeocoder.EW_geocoder(
                census_configuration, gen, ew_configuration,
            )
        (
            rsd_dictionary_processed,
            processed_parish_boundary_data,
            geom_blocking_cols,
        ) = census_geocoder.create_ew_parishboundaryprocessed()
        (census_blocking_cols, census_counties,) = census_geocoder.process_ew_census(
            rsd_dictionary_processed
        )
        for geom, geom_config in geocode_config["target_geoms"].items():
            print("#" * 88)
            print(geom)
            geom_configuration = config.Target_geom(**geom_config)
            print(geom_configuration)

            census_geocoder.geocoding_new(
                processed_parish_boundary_data,
                census_blocking_cols,
                geom_blocking_cols,
                census_counties,
                geom,
                geom_configuration,
            )

# for census, census_params in geocode_config["census_config"].items():

#     census_year, census_country = get_year_country(census)

#     start = datetime.now()
#     if census_params["runtype"] == "no":
#         continue
#     else:
#         if census_country == "EW":
#             census_geocoder = setupgeocoder.EW_geocoder(
#                 census_country,
#                 census_year,
#                 census_params,
#                 geocode_config["target_geoms"],
#                 geocode_config["general"],
#                 geocode_config["ew_config"],
#             )
#             (
#                 rsd_dictionary_processed,
#                 processed_parish_boundary_data,
#                 geom_blocking_cols,
#             ) = census_geocoder.create_ew_parishboundaryprocessed()
#             (
#                 census_blocking_cols,
#                 census_counties,
#             ) = census_geocoder.process_ew_census(rsd_dictionary_processed)
#         elif census_country == "SCOT":
#             SCOT_config = namedtuple("SCOT_config", [*geocode_config["scot_config"]])
#             scot_config = SCOT_config(**geocode_config["scot_config"])

#             census_geocoder = setupgeocoder.SCOT_geocoder(
#                 census_country,
#                 census_year,
#                 census_params,
#                 geocode_config["target_geoms"],
#                 geocode_config["general"],
#                 geocode_config["scot_config"],
#             )
#             processed_parish_boundary_data = (
#                 census_geocoder.create_scot_parishboundaryprocessed()
#             )
#             census_geocoder.process_scot_census()

#         census_geocoder.geocoding_new(
#             processed_parish_boundary_data,
#             census_blocking_cols,
#             geom_blocking_cols,
#             census_counties,
#         )

#         end_time = datetime.now() - start
#         print("Time to run: ", end_time.total_seconds() / 60)
