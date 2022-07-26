# Main script that combines other scripts
import tempfile

# from datetime import datetime
import yaml

import config
import setupgeocoder

with open("inputs/input_config.yaml", "r") as f:
    geocode_config = yaml.load(f, Loader=yaml.FullLoader)

config.validate_configs(geocode_config)

gen = config.General(**geocode_config["general"])


for x, y in geocode_config["census_config"].items():
    with tempfile.TemporaryDirectory(dir=gen.output_data_path) as tmpcensusdir:
        census_configuration = config.Censusconfiguration(**y)

        if census_configuration.runtype is True:
            print("#" * 88)
            print(census_configuration.year, census_configuration.country)
            print("#" * 88)

            if census_configuration.country == "EW":
                ew_configuration = config.EW_configuration(
                    census_configuration.year, **geocode_config["ew_config"]
                )
                conparid = config.create_conparid(
                    ew_configuration.parish_icem_lkup_config, census_configuration.year
                )
                census_geocoder = setupgeocoder.EW_geocoder()
                (
                    rsd_dictionary_processed,
                    processed_parish_boundary_data,
                    geom_blocking_cols,
                ) = census_geocoder.create_ew_parishboundaryprocessed(
                    ew_configuration.rsd_dictionary_config,
                    ew_configuration.rsd_gis_config,
                    ew_configuration.parish_icem_lkup_config,
                    ew_configuration.parish_gis_config,
                    conparid,
                )

                (
                    census_blocking_cols,
                    partition_list,
                ) = census_geocoder.process_ew_census(
                    rsd_dictionary_processed,
                    tmpcensusdir,
                    ew_configuration.rsd_dictionary_config,
                    census_configuration,
                )

            elif census_configuration.country == "SCOT":
                scot_configuration = config.SCOT_configuration(
                    census_configuration.year, **geocode_config["scot_config"]
                )
                census_geocoder = setupgeocoder.SCOT_geocoder()
                (
                    processed_parish_boundary_data,
                    boundary_lkup,
                    geom_blocking_cols,
                ) = census_geocoder.create_scot_parishboundaryprocessed(
                    scot_configuration.boundary_lkup_config,
                    scot_configuration.boundary_config,
                )

                (
                    census_blocking_cols,
                    partition_list,
                ) = census_geocoder.process_scot_census(
                    tmpcensusdir,
                    boundary_lkup,
                    census_configuration,
                    scot_configuration.boundary_lkup_config,
                )
            for geom, geom_config in geocode_config["target_geoms"].items():
                output_dir = config.create_outputdirs(
                    gen.output_data_path,
                    census_configuration.year,
                    census_configuration.country,
                    geom,
                )

                print("#" * 88)
                print(geom)
                geom_configuration = config.Target_geom(**geom_config)

                census_geocoder.geocode(
                    processed_parish_boundary_data,
                    census_blocking_cols,
                    geom_blocking_cols,
                    partition_list,
                    geom,
                    geom_configuration,
                    tmpcensusdir,
                    census_configuration,
                    output_dir,
                )


#         end_time = datetime.now() - start
#         print("Time to run: ", end_time.total_seconds() / 60)
