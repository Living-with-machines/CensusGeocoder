import pandas as pd

import census
import eval
import ew_geom_preprocess
import recordcomparison

# import scot_geom_preprocess
import target_geom_preprocess
import utils


class CensusGB_geocoder:
    """Base Class to geo-code census data

    Methods
    ----------
    link_geocode_to_icem()
        Links geocoded census output (unique census addresses with corresponding
        linked street geometry) to individuals in the census; creates dataframe
        containing all unique individual census ids and the id of the street
        geometry that person has been linked to.

    geocode()
        Links census addresses to target geometries using geo-blocking and
        fuzzy string matching.

    """

    def link_geocode_to_icem(
        self,
        linked,
        partition,
        new_uid,
        geom_name,
        census_params,
        censusdir,
        output_dir,
    ):
        """Creates lookup for each partition containing unique id from census
        and unique id from target geometry data.

        Parameters
        ----------
        linked: pandas.DataFrame
            A pandas dataframe of high-quality matches between target geometry data
            and census.

        partition: str
            Partition value, e.g. a county like 'Essex'.
        
        new_uid: str
            Name of unique identifier column created from target geometry name
            and census year.

        geom_name: str
            Name of the target geometry data.
            
        census_params: Dataclass
            Dataclass containing parameters for census year.

        censusdir: str
            Path to directory containing census data.

        output_dir: str
            Path to write output file.
        """
        if not linked.empty:
            census = pd.read_parquet(
                censusdir,
                filters=[
                    [(census_params.census_output_params.partition_on, "=", partition)]
                ],
                columns=[
                    census_params.census_output_params.new_uid,
                    census_params.census_fields.uid,
                ],
            )

            cen_geom_lkp = pd.merge(
                left=census,
                right=linked,
                on=census_params.census_output_params.new_uid,
                how="inner",
            )
            cen_geom_lkp = cen_geom_lkp[[census_params.census_fields.uid, new_uid]]

        else:
            cen_geom_lkp = pd.DataFrame()

        cen_geom_lkp.to_csv(
            utils.make_path(output_dir)
            / f"{census_params.year}_{geom_name}_{partition}_lkup"
            f"{census_params.census_output_params.filetype}",
            sep=census_params.census_output_params.sep,
            index=census_params.census_output_params.index,
        )
        return cen_geom_lkp

    def geocode(
        self,
        historic_boundaries,
        census_blocking_cols,
        geom_blocking_cols,
        partition_list,
        geom_name,
        geom_config,
        censusdir,
        census_params,
        output_dir,
    ):
        """Reads and processes target geometry data. Iterates over census
        partitions, performing fuzzy string matching between addresses in
        census and  target geometry data. Writes the results for each partition
        to files - one file for linked addresses (one match only), one file for
        duplicate linked addresses (more than 1 equally good match).

        Parameters
        ---------
        historic_boundaries: geopandas.GeoDataFrame
            A geopandas geodataframe containing processed historic boundary data.

        census_blocking_cols: list
            List of census columns for geo-blocking when running string comparisons.

        geom_blocking_cols: list
            List of columns for geo-blocking when running string comparisons.

        partition_list: list
            List of partition values from census data.

        geom_name: str
            Name of the target geometry data.

        geom_config: Dataclass
            Dataclass containing parameters for target geometry data.

        censusdir: str
            Path to directory containing census data.

        census_params: Dataclass
            Dataclass containing parameters for census year.

        output_dir: str
            Path to write output file.
        """

        processed_geom_data, new_uid = target_geom_preprocess.process_raw_geo_data(
            geom_name, historic_boundaries, geom_config, census_params, output_dir,
        )

        (
            inds_list,
            adds_list,
            adds_list_dup,
            inds_list_all,
            adds_list_all,
            eval_df,
        ) = eval.setup_eval(
            census_params.census_output_params.partition_on, partition_list
        )

        for count, partition in enumerate(partition_list):
            print("#" * 30)
            print(partition)
            print("#" * 30)
            census_subset, inds_in_part, adds_in_part = census.create_partition_subset(
                partition, censusdir, census_params
            )

            inds_list_all.append(inds_in_part)
            adds_list_all.append(adds_in_part)

            if not census_subset.empty:
                census_subset_tfidf = utils.compute_tfidf(
                    census_subset, census_params.census_fields
                )

                candidate_links = recordcomparison.create_candidate_links(
                    census_subset,
                    processed_geom_data,
                    census_blocking_cols,
                    geom_blocking_cols,
                )
                # print(census_subset_tfidf)
                target_results = recordcomparison.compare(
                    census_subset_tfidf,
                    processed_geom_data,
                    candidate_links,
                    geom_config,
                    census_params,
                )
                linked, linked_duplicates = recordcomparison.process_results(
                    target_results,
                    census_subset_tfidf,
                    processed_geom_data,
                    census_params,
                    geom_config,
                    new_uid,
                )
            else:
                continue

            linked.to_csv(
                utils.make_path(output_dir, "linked")
                / f"{census_params.year}_{geom_name}_{partition}{census_params.census_output_params.filetype}",
                sep=census_params.census_output_params.sep,
                index=census_params.census_output_params.index,
            )

            linked_duplicates.to_csv(
                utils.make_path(output_dir, "linked_duplicates")
                / f"{census_params.year}_{geom_name}_{partition}"
                f"{census_params.census_output_params.filetype}",
                sep=census_params.census_output_params.sep,
                index=census_params.census_output_params.index,
            )

            adds_list = eval.append_list(
                linked, census_params.census_output_params.new_uid, adds_list,
            )

            adds_list_dup = eval.append_list(
                linked_duplicates,
                census_params.census_output_params.new_uid,
                adds_list_dup,
            )

            cen_geom_lkp = self.link_geocode_to_icem(
                linked,
                partition,
                new_uid,
                geom_name,
                census_params,
                censusdir,
                output_dir,
            )

            inds_list = eval.append_list(
                cen_geom_lkp, census_params.census_fields.uid, inds_list,
            )

        eval.eval_df_add(
            eval_df,
            inds_list,
            adds_list,
            adds_list_dup,
            inds_list_all,
            adds_list_all,
            output_dir,
            geom_name,
        )
        print(f"Geocoding to {geom_name} complete")

        # if linked.empty and linked_duplicates.empty:
        #     inds_list.append(0)
        #     adds_list.append(0)
        #     adds_list_dup.append(0)
        # elif linked.empty and not linked_duplicates.empty:


class EW_geocoder(CensusGB_geocoder):
    """Subclass of CensusGB_geocoder containing methods for processing
    England and Wales data.

    Methods
    -------
        create_ew_parishboundaryprocessed()
            Creates new boundary dataset by combinging RSD and Parish boundaries.

        process_ew_census()
            Process England and Wales census data ready for geocoding.

    """

    def create_ew_parishboundaryprocessed(
        self,
        rsd_dictionary_config,
        rsd_gis_config,
        parish_icem_lkup_config,
        parish_gis_config,
        conparid,
    ):
        """Reads and processes parish and rsd boundary datasets and associated
        lookup tables. Returns processed rsd lookup dictionary, boundary data,
        and list of columns for blocking stage of record comparison. 

        Parameters
        ---------
        rsd_dictionary_config: Dataclass
            Dataclass containing parameters for reading rsd dictionary.

        rsd_gis_config: Dataclass
            Dataclass containing parameters for reading RSD GIS Boundary data
            for census year.
        
        parish_icem_lkup_config : Dataclass
            Dataclass containing parameters for reading lookup table.

        parish_gis_config : Dataclass
            Dataclass containing parameters for reading Parish GIS Boundary data.

        conparid: str
            Name of consistent parish identifier for census year

        Returns
        -------
        rsd_dictionary_processed: pandas.DataFrame
            A pandas dataframe containing the RSD Dictionary lookup table for census year.

        parish_data_processed: geopandas.GeoDataFrame
            A geopandas geodataframe containing parish/rsd boundary data for census year.

        geom_blocking_cols: list
            List of columns for geo-blocking when running string comparisons.
        """
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
        """Reads and processes England and Wales census data.

        Parameters
        ---------
        rsd_dictionary_processed: pandas.DataFrame
            A pandas dataframe containing the RSD Dictionary lookup table for census year.
        
        tmpcensusdir: str
            Path to temporary parquet census directory.
            
        rsd_dictionary_config: Dataclass
            Dataclass containing parameters for reading rsd dictionary.

        census_params: Dataclass
            Dataclass containing parameters for census year.

        Returns
        -------
        census_blocking_cols: list
            List of census columns for geo-blocking when running string comparisons.

        partition_list: list
            List of partition values from census data.
        """

        census_data = census.read_census(
            census_params.census_file,
            census_params.census_fields.list_cols(),
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
            census_params,
            rsd_dictionary_config,
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
