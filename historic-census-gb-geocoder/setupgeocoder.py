import pandas as pd
import pathlib
import geopandas as gpd

import census
import eval
import ew_geom_preprocess
import recordcomparison

import scot_geom_preprocess
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
        linked_duplicates,  # remove if not used
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

        linked_duplicates: pandas.DataFrame
            A pandas dataframe of multiple equal high-quality matches between target 
            geometry data and census.

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

            # linked_all = pd.concat([linked, linked_duplicates])

            cen_geom_lkp = pd.merge(
                left=census,
                right=linked,
                on=census_params.census_output_params.new_uid,
                how="inner",
            )
            cen_geom_lkp = cen_geom_lkp[
                [
                    census_params.census_fields.uid,
                    census_params.census_output_params.new_uid,
                    new_uid,
                ]
            ]

        else:
            cen_geom_lkp = pd.DataFrame()

        cen_geom_lkp.to_csv(
            utils.make_path(output_dir, "lookup")
            / f"{census_params.country}_{census_params.year}_{geom_name}"
            f"_{partition}_lkup{census_params.census_output_params.filetype}",
            **census_params.census_output_params.to_csv_kwargs,
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

        geom_path = pathlib.Path(f"data/output_geom_test/{census_params.year}/{census_params.country}/{geom_name}/{geom_name}_{census_params.country}_{census_params.year}.geojson")

        if geom_path.exists():
            new_uid =  (str(geom_name)
            + "_"
            + str(census_params.country)
            + "_"
            + str(census_params.year)
            )
            # print(new_uid)
            
            processed_geom_data = gpd.read_file(geom_path)
            # print(processed_geom_data)
            processed_geom_data = processed_geom_data.drop(columns="geometry").set_index(new_uid)
            # print(processed_geom_data.info())



        else:

            processed_geom_data, new_uid = target_geom_preprocess.process_raw_geo_data(
                geom_name, historic_boundaries, geom_config, census_params, output_dir, geom_blocking_cols,
            )

        # (
        #     inds_list,
        #     adds_list,
        #     adds_list_dup,
        #     inds_list_all,
        #     adds_list_all,
        #     eval_df,
        # ) = eval.setup_eval(
        #     census_params.census_output_params.partition_on, partition_list
        # )

        for partition in partition_list:
            print(partition)
            (
                census_subset,
                inds_in_part,
                adds_in_part,
            ) = census.create_partition_subset(partition, censusdir, census_params)
            # print(census_subset)
            # inds_list_all.append(inds_in_part)
            # adds_list_all.append(adds_in_part)
            # print(census_subset)
            # print(census_subset.info())
            # print(processed_geom_data)
            # print(processed_geom_data.info())
            if not census_subset.empty:
                # census_subset = census_subset[[census_params.census_fields["address"]]]
                # census_subset_tfidf = utils.compute_tfidf(
                #     census_subset, census_params.census_fields["address"]
                # )
                # print(census_subset)
                # print(census_subset_tfidf)
                # print(processed_geom_data)
                # print(geom_blocking_cols)
                # print(census_blocking_cols)

                candidate_links = recordcomparison.create_candidate_links(
                    census_subset,
                    processed_geom_data,
                    census_blocking_cols,
                    geom_blocking_cols,
                )
                # print(census_subset_tfidf)
                target_results = recordcomparison.compare(
                    census_subset[[census_params.census_fields["address"]]],#_tfidf
                    processed_geom_data,
                    candidate_links,
                    geom_config,
                    census_params,
                )
                linked, linked_duplicates = recordcomparison.process_results(
                    target_results,
                    census_subset,#_tfidf
                    processed_geom_data,
                    census_params,
                    geom_config,
                    new_uid,
                    partition,
                )
                if not linked.empty and not linked_duplicates.empty:


                    linked_output = linked.drop(
                        columns=[
                            census_params.census_fields["address"],
                            geom_config.data_fields.address_field,
                        ]
                    )

                    linked_duplicates_output = linked_duplicates.drop(
                        columns=[
                            census_params.census_fields["address"],
                            geom_config.data_fields.address_field,
                        ]
                    )

                    linked_output.to_csv(
                        utils.set_filepath(
                            output_dir,
                            "linked",
                            # census_params.country,
                            # str(census_params.year),
                            # geom_name,
                        )
                        / f"{partition}_link{census_params.census_output_params.filetype}",
                        **census_params.census_output_params.to_csv_kwargs,
                    )

                    linked_duplicates_output.to_csv(
                        utils.set_filepath(
                            output_dir,
                            "linked_duplicates",
                            # census_params.country,
                            # str(census_params.year),
                            # geom_name,
                        )
                        / f"{partition}_linkdup{census_params.census_output_params.filetype}",
                        **census_params.census_output_params.to_csv_kwargs,
                    )
                else:
                    continue

            else:
                continue

            # adds_list = eval.append_list(
            #     linked, census_params.census_output_params.new_uid, adds_list,
            # )

            # adds_list_dup = eval.append_list(
            #     linked_duplicates,
            #     census_params.census_output_params.new_uid,
            #     adds_list_dup,
            # )

            # cen_geom_lkp = self.link_geocode_to_icem(
            #     linked,
            #     linked_duplicates,
            #     partition,
            #     new_uid,
            #     geom_name,
            #     census_params,
            #     censusdir,
            #     output_dir,
            # )

        #     inds_list = eval.append_list(
        #         cen_geom_lkp, census_params.census_fields.uid, inds_list,
        #     )



        # eval.eval_df_add(
        #     eval_df,
        #     inds_list,
        #     adds_list,
        #     adds_list_dup,
        #     inds_list_all,
        #     adds_list_all,
        #     output_dir,
        #     geom_name,
        #     census_params,
        # )
        print(
            f"Geocoding {census_params.country} {census_params.year} to {geom_name} complete"
        )

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
            Creates new boundary dataset by combining RSD and Parish boundaries.

        process_ew_census()
            Process England and Wales census data ready for geocoding.

    """

    def create_ew_parishboundaryprocessed(
        self,
        rsd_dictionary_config,
        rsd_gis_config,
        parish_icem_lkup_config,
        parish_gis_config,
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

        ukds_link = ew_geom_preprocess.read_gis_to_icem(parish_icem_lkup_config,)

        parish = ew_geom_preprocess.process_parish_boundary_data(
            parish_gis_config, ukds_link, parish_icem_lkup_config
        )

        (
            parish_data_processed,
            geom_blocking_cols,
        ) = ew_geom_preprocess.join_parish_rsd_boundary(
            parish,
            processed,
            parish_icem_lkup_config.conparid,
            rsd_dictionary_config.rsd_id_field,
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
            list(census_params.census_fields.values()),
            # usecols = list(census_params.census_fields.values()),
            **census_params.csv_params,
        )

        census_cleaned = census.clean_census_address_data(
            census_data,
            census_params.census_fields["address"],
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
    """Subclass of CensusGB_geocoder containing methods for processing
    Scottish data.

    Methods
    -------
        create_scot_parishboundaryprocessed()
            Creates processed Scottish boundary dataset and lookup table.

        process_scot_census()
            Process Scottish census data ready for geocoding.

    """

    def create_scot_parishboundaryprocessed(
        self, boundary_lkup_config, boundary_config
    ):
        """Reads and processes Scottish boundary GIS datasets and lookup tables.
        Returns parish boundary data in geopandas geodataframe, a boundary
        lookup table linking the boundary dataset to I-CeM, and a list of columns
        for blocking stage of record comparison. 

        Parameters
        ---------
        boundary_lkup_config: Dataclass
            Dataclass containing parameters for reading parish boundary lookup table.

        boundary_config: Dataclass
            Dataclass containing parameters for reading parish boundary GIS files.

        Returns
        -------
        parish_boundary: geopandas.GeoDataFrame
            A geopandas geodataframe containing parish boundary data for census year.

        boundary_lkup: pandas.DataFrame
            A pandas dataframe containing the parish lookup table for census year.

        geom_blocking_cols: list
            List of columns for geo-blocking when running string comparisons.
        """
        boundary_lkup = scot_geom_preprocess.process_scot_lkup(
            boundary_lkup_config, boundary_config
        )

        (
            parish_boundary,
            geom_blocking_cols,
        ) = scot_geom_preprocess.process_scot_boundary(boundary_config)

        processed_parish_boundary = scot_geom_preprocess.merge_lkup(
            parish_boundary, boundary_lkup, boundary_config, boundary_lkup_config
        )

        dissolved = scot_geom_preprocess.dissolve_scot_boundary(
            processed_parish_boundary,
            boundary_lkup_config.parid_field,
            boundary_lkup_config,
        )
        # print(parish_boundary)
        # print(boundary_lkup)
        # print(processed_parish_boundary)
        print(dissolved.head(10))

        # dissolved.to_file("dissolved_test.geojson", crs="EPSG:27700", driver="GeoJSON")

        return (
            dissolved,
            boundary_lkup[["ParID", "merged_id"]],
            geom_blocking_cols,
        )  # replace dissolved with processed_parish_boundary but original was parish_boundary

    def process_scot_census(
        self, tmpcensusdir, boundary_lkup, census_params, boundary_lkup_config
    ):
        """Reads and processes Scottish census data.

        Parameters
        ---------
        
        tmpcensusdir: str
            Path to temporary parquet census directory.

        boundary_lkup: pandas.DataFrame
            Pandas dataframe containing lookup table linking ParID in I-Cem
            to Scottish parish boundary GIS datasets.

        census_params: Dataclass
            Dataclass containing parameters for census year.

        boundary_lkup_config: Dataclass
            Dataclass containing parameters for reading parish boundary lookup table.

        Returns
        -------
        census_blocking_cols: list
            List of census columns for geo-blocking when running string comparisons.

        partition_list: list
            List of partition values from census data.
        """

        census_data = census.read_census(
            census_params.census_file,
            list(census_params.census_fields.values()),
            **census_params.csv_params,
        )

        census_cleaned = census.clean_census_address_data(
            census_data,
            census_params.census_fields["address"],
            census_params.census_standardisation_file,
        )

        (
            census_linked,
            census_blocking_cols,
            partition_list,
        ) = census.process_scot_census(
            census_cleaned, boundary_lkup, boundary_lkup_config, census_params,
        )

        census.output_census(
            census_linked, tmpcensusdir, census_params.census_output_params
        )

        return census_blocking_cols, partition_list
