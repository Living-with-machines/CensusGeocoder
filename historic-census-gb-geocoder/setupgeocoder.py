import pandas as pd
import ew_geom_preprocess

# import scot_geom_preprocess
import target_geom_preprocess
import census
import utils
import recordcomparison


class CensusGB_geocoder:
    """Base Class to geo-code census data

    Methods
    ----------

    preprocessing()
        Pre-processes input files, returning OS Open Road data, GB1900,
        Census, and a list of census counties. Writes OS Open Road and
        GB1900 datasets segmented by historic parish/RSD boundaries.

    geocode()
        Links census addresses to target geometries using geo-blocking and
        fuzzy string matching.

    link_geocode_to_icem()
        Links geocoded census output (unique census addresses with corresponding
        linked street geometry) to individuals in the census; creates dataframe
        containing all unique individual census ids and the id of the street
        geometry that person has been linked to.

    """

    def link_geocode_to_icem(
        self,
        linked,
        partition,
        new_uid,
        geom_name,
        census_fields,
        census_output_params,
        tmpcensusdir,
        output_dir,
        census_year,
    ):

        census = pd.read_parquet(
            tmpcensusdir,
            filters=[[(census_output_params.partition_on, "=", f"{partition}")]],
            columns=[census_output_params.new_uid, census_fields.uid],
        )

        new_trial = pd.merge(
            left=census, right=linked, on=census_output_params.new_uid, how="inner"
        )
        new_trial = new_trial[[census_fields.uid, new_uid]]
        new_trial.to_csv(
            utils.make_path(output_dir)
            / f"{census_year}_{geom_name}_{partition}_lkup.tsv",
            sep="\t",
            index=False,
        )
        pass

    def geocode(
        self,
        parish_data_processed,
        census_blocking_cols,
        geom_blocking_cols,
        partition_list,
        geom,
        geom_config,
        tmpcensusdir,
        census_params,
        output_dir,
    ):
        """
        Needs editing Links census addresses to the geometry data for
        streets in OS Open Roads and GB1900. Takes outputs from
        `preprocessing` method, iterates over counties in census
        computing the similarity between census addresses and addresses
        in OS Open Roads and GB1900.

        Writes the results for each county, the whole country, as well
        as duplicate matches.

        Parameters
        ---------
        census: `pandas.DataFrame`
            DataFrame containing pre-processed census data returned from
            the `preprocessing` method.
        gb1900: `geopandas.GeoDataFrame`
            GeoDataFrame containing pre-processed GB1900 data returned
            from the `preprocessing` method.
        segmented_os_roads: `geopandas.GeoDataFrame`
            GeoDataFrame containing pre-processed OS Open Roads data
            returned from the `preprocessing` method.
        census_counties: list
            List of Census Registration Counties returned from the
            `preprocessing` function.

        Returns
        ---------
        Currently doesn't pass anything on to another function.

        """

        processed_geom_data, new_uid = target_geom_preprocess.process_raw_geo_data(
            geom, parish_data_processed, geom_config, census_params, output_dir,
        )

        for partition in partition_list:
            print("#" * 30)
            print(partition)
            print("#" * 30)
            census_subset = census.create_partition_subset(
                partition, tmpcensusdir, census_params.census_output_params
            )
            if census_subset.empty:
                continue
            else:
                census_subset_tfidf = utils.compute_tfidf(
                    census_subset, census_params.census_fields
                )

                candidate_links = recordcomparison.create_candidate_links(
                    census_subset,
                    processed_geom_data,
                    census_blocking_cols,
                    geom_blocking_cols,
                )
                print(census_subset_tfidf)
                linked, duplicates = recordcomparison.compare(
                    census_subset_tfidf,
                    processed_geom_data,
                    candidate_links,
                    new_uid,
                    geom_config,
                    census_params.census_fields,
                )
                # print(linked.info())
                if linked.empty:
                    continue
                else:
                    linked.to_csv(
                        utils.make_path(output_dir, "linked")
                        / f"{census_params.year}_{geom}_{partition}{census_params.census_output_params.filetype}",
                        sep=census_params.census_output_params.sep,
                        index=census_params.census_output_params.index,
                    )
                    duplicates.to_csv(
                        utils.make_path(output_dir, "duplicate")
                        / f"{census_params.year}_{geom}_{partition}{census_params.census_output_params.filetype}",
                        sep=census_params.census_output_params.sep,
                        index=census_params.census_output_params.index,
                    )
                    self.link_geocode_to_icem(
                        linked,
                        partition,
                        new_uid,
                        geom,
                        census_params.census_fields,
                        census_params.census_output_params,
                        tmpcensusdir,
                        output_dir,
                        census_params.year,
                    )  # need to add in census output params here
        pass


class EW_geocoder(CensusGB_geocoder):
    """
        create_ew_parishboundaryprocessed()
            Creates new boundary dataset from union of RSD and Parish boundaries.

        process_ew_census()
            Process census data ready for linking.

    """

    def create_ew_parishboundaryprocessed(
        self,
        rsd_dictionary_config,
        rsd_gis_config,
        parish_icem_lkup_config,
        parish_gis_config,
        conparid,
    ):
        rsd_dictionary_processed = ew_geom_preprocess.read_rsd_dictionary(
            rsd_dictionary_config,
        )

        processed = ew_geom_preprocess.process_rsd_boundary_data(
            rsd_dictionary_config.rsd_id_field, rsd_gis_config
        )

        ukds_link = ew_geom_preprocess.read_gis_to_icem(
            parish_icem_lkup_config, conparid
        )

        parish = ew_geom_preprocess.process_parish_boundary_data(
            parish_gis_config,
            ukds_link,
            conparid,
            parish_icem_lkup_config.ukds_id_field,
        )

        (
            parish_data_processed,
            geom_blocking_cols,
        ) = ew_geom_preprocess.join_parish_rsd_boundary(
            parish, processed, conparid, rsd_dictionary_config.rsd_id_field
        )

        return rsd_dictionary_processed, parish_data_processed, geom_blocking_cols

    def process_ew_census(
        self,
        rsd_dictionary_processed,
        tmpcensusdir,
        rsd_dictionary_config,
        census_params,
    ):

        census_data = census.read_census(
            census_params.census_file,
            census_params.census_fields,
            census_params.csv_params,
        )

        census_cleaned = census.clean_census_address_data(
            census_data,
            census_params.census_fields.address,
            census_params.census_standardisation_file,
        )

        census_linked, census_blocking_cols, partition_list = census.process_ew_census(
            census_cleaned,
            rsd_dictionary_processed,
            census_params.census_fields.parid,
            rsd_dictionary_config.cen_parid_field,
            rsd_dictionary_config.rsd_id_field,
            census_params.census_fields,
        )

        census.output_census(
            census_linked, tmpcensusdir, census_params.census_output_params
        )

        return census_blocking_cols, partition_list


class SCOT_geocoder(CensusGB_geocoder):
    # def __init__(
    #     self,
    #     census_country,
    #     census_year,
    #     census_params,
    #     target_geoms,
    #     path_to_data,
    #     scot_config,
    # ):
    #     super().__init__(
    #         census_country, census_year, census_params, target_geoms, path_to_data
    # )

    # 		#### SCOTLAND SPECIFIC
    def create_scot_parishboundaryprocessed(self):

        pass

        # def process_scot_census(self):

        #     self.process_census(self.census_file, self.census_fields)

        #     self.output_census()
        #     pass
        # scot_parish_lkup_file: str
        # 	Path to the lookup table that links the Scotland Parish
        # boundary shapefile to the 'ParID' field in I-CeM.
        # print(scot_config)
        """
        SCOTLAND SPECIFIC VARIABLES
        """
        # self.scot_parish_lkup_file = self.set_scot_parish_lookup_file()

    # scot_parish_link = preprocess.scot_parish_lookup
    # (self.scot_parish_lkup_file,self.census_year)
    # parish_data_processed = preprocess.process_scot_parish_boundary_data
    # (self.parish_shapefile_path,scot_parish_link,self.census_year)
