import pandas as pd
import ew_geom_preprocess
import scot_geom_preprocess
import target_geom_preprocess
import census
import utils
import recordcomparison
import pathlib


class CensusGB_geocoder:
    """Base Class to geo-code census data

    Attributes
    ----------
    #### GENERAL
    census_year : int
        The census year to be geo-coded, specified in
        `data/historic-census-gb-geocoder-config.json`
    census_country: str
        The country to be geo-coded, specified in
        `data/historic-census-gb-geocoder-config.json`
    runtype: str
        The parse_option of geo-coding to be run, specified in
        `data/historic-census-gb-geocoder-params.json`
    input_data_path: str
        The path to to where the datasets needed to run the code are stored,
        specified in `data/historic-census-gb-geocoder-config.json`
    output_data_path: str
        The path to the outputs directory, where all outputs from the
        geo-coding script are stored. E.g. `data/output/1901/SCOT`.
    census_file: str
        Path to the census file to be geocoded, specified in
        `data/historic-census-gb-geocoder-config.json`.
    row_limit: int
        The number of rows of the OS Open Road and census file to read.
        If `parse_option` parameter is 'full', then `row_limit` is None,
        which results in the full files being read. If `parse_option`
        parameter is 'testing', then `row_limit` is 15,000. By limiting
        the number of rows of data read from the OS Open Road dataset
        and the census file, the script will run much quicker for
        testing purposes.
    target_geoms: dict
        Dictionary containing information about the target geometry
        to be linked to the census.

    Methods
    ----------

    set_row_limit()
        Sets the number of rows to read from OS Open Roads, GB1900,
        and Census file.
    set_output_dir()
        Sets the output directory to which all outputs are written.
        Creates directory if none exists.


    preprocessing()
        Pre-processes input files, returning OS Open Road data, GB1900,
        Census, and a list of census counties. Writes OS Open Road and
        GB1900 datasets segmented by historic parish/RSD boundaries.
    geocoding()
        Loops over each county in the census, geo-coding the census data
        for that county using OS Open Road Data and GB1900. Writes output
        files containing....
    summary_stats()
        Produces summary statistics, detailing the contents of the,
        geo-coded outputs.

    """

    def __init__(self, census_params, path_to_data):

        """Parameters
        ----------
        census_year : int
            The census year to be geo-coded, e.g. 1851, 1861, 1871,
            1881, 1891, 1901, or 1911. Warning, no census data for
            England and Wales for 1871, and no Scottish census data
            for 1911. Specified in parameters json.
        runtype: str
            Specify type of geo-coding, use 'full' to geo-code entire
            year and country specified, or 'testing' to geo-code sample
            for testing/debugging purposes. Specified in parameters json.
        input_data_path: str
            Specify the path to the `data/` folder, where the datasets
            needed to perform the geocoding are stored.
        output_data_path: str
            Specify the path to the outputs folder, where the outputs
            are stored.
        """

        self.census_country = census_params.country
        self.census_year = census_params.year
        # self.row_limit = self.set_row_limit(census_params.runtype)
        self.census_file = census_params.census_file
        self.outputdir = self.set_output_dir(
            path_to_data.output_data_path, self.census_country, self.census_year
        )
        # self.target_geoms = target_geoms
        self.census_fields = census_params.census_fields
        self.census_csv_params = census_params.csv_params
        self.census_standardisation_file = census_params.census_standardisation_file
        self.census_output_params = census_params.census_output_params

    # def set_row_limit(self, runtype):
    #     """
    #     Checks the `parse_option` value specified in parameters json.

    #     Returns
    #     ----------

    #     rows: int or None
    #         Either None, in which case when passed to pandas `read_csv`
    #         or equivalent the argument is ignored, or an integer
    #         specifying the number of rows to read.

    #     """
    #     rows = None
    #     if runtype == False:
    #         rows = 1000
    #     return rows

    def set_output_dir(self, outputdirparent, census_country, census_year):
        """
        Set the output directory in the format e.g.
        `data/output/1901/EW/full`. Checks if output directory exists,
        if it doesn't it creates a directory.

        Returns
        ----------
        output_dir: str
            Path to output directory.
        """

        output_dir = outputdirparent + f"/{str(census_year)}/{census_country}"
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
        return output_dir

    def link_geocode_to_icem(
        self, linked, partition, new_uid, geom_name, census_fields, census_output_params
    ):

        census = pd.read_parquet(
            self.outputdir,
            filters=[[(census_output_params.partition_on, "=", f"{partition}")]],
            columns=["unique_add_id", census_fields.uid],
        )
        print(census.info())
        print(linked.info())
        new_trial = pd.merge(left=census, right=linked, on="unique_add_id", how="inner")
        new_trial = new_trial[[census_fields.uid, new_uid]]
        new_trial.to_csv(
            f"data/output/testingoutput/{partition}_{geom_name}_linked_output.tsv",
            sep="\t",
            index=False,
        )
        pass

    def geocoding_new(
        self,
        parish_data_processed,
        census_blocking_cols,
        geom_blocking_cols,
        partition_list,
        geom,
        geom_config,
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
            geom, parish_data_processed, geom_config, self.census_year, self.outputdir,
        )

        for partition in partition_list:
            print("#" * 30)
            print(partition)
            print("#" * 30)
            census_subset = census.create_county_subset(
                partition, self.outputdir, self.census_fields
            )
            if census_subset.empty:
                continue
            else:
                census_subset_tfidf = utils.compute_tfidf(
                    census_subset, self.census_fields
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
                    self.census_fields,
                )
                # print(linked.info())
                if linked.empty:
                    continue
                else:
                    linked.to_csv(
                        f"data/output/testingoutput/{self.census_year}_{partition}_linked.tsv",
                        sep="\t",
                        index=False,
                    )
                    duplicates.to_csv(
                        f"data/output/testingoutput/{self.census_year}_{partition}_duplicates.tsv",
                        sep="\t",
                        index=False,
                    )
                    self.link_geocode_to_icem(
                        linked,
                        partition,
                        new_uid,
                        geom,
                        self.census_fields,
                        self.census_output_params,
                    )  # need to add in census output params here
        pass


class EW_geocoder(CensusGB_geocoder):
    """
        set_rsd_dictionary() Sets filepath to the England and Wales
        Registration Sub-District (RSD) dictionary lookup file.
    #### ENGLAND & WALES SPECIFIC conparid: str
        The 'ConParID' column name, either 'conparid_51-91' for 1851 to
        1891 or 'conparid_01-11' for 1901 to 1911.
    cen: str
        The cen field found in the RSD Dictionary lookup files and RSD
        Boundary Shapefiles. Created using 'cen' + `census_year`
        attribute, e.g. 'CEN_1901'. Used to dissolve the RSD Shapefile
        to create the correct RSD boundaries for specified census year
        and to link these to RSD Dictionary lookup.
    rsd_shapefile_path: str
        Path to the England and Wales RSD Boundary Shapefile.
    rsd_dictionary_path: str
        Path to the England and Wales RSD Dictionary lookup file for the
        specified census year.
    ukds_gis_to_icem_path: str
        Path to lookup table that links England and Wales Parish
        Boundary Shapefile to the Consistent Parish Geographies
        (`ConParID` field) in I-CeM
    parid_for_rsd_dict: str
        Name of the `Par_ID` column in the England and Wales RSD
        Dictionary lookup file. For 1851,1861,1891,1901, and 1911 the
        column is labelled 'ParID'. The 1881 RSD Dictionary lookup file
        has two columns 'OLD_ParID' and 'NEW_ParID', we use 'NEW_ParID'.
    """

    def __init__(
        self, census_params, path_to_data, ew_config,
    ):
        super().__init__(census_params, path_to_data)

        # self.conparid = census_params['conparid']

        self.rsd_dictionary_config = ew_config.rsd_dictionary_config

        self.rsd_gis_config = ew_config.rsd_gis_config

        self.parish_icem_lkup_config = ew_config.parish_icem_lkup_config

        self.conparid = self.create_conparid(
            self.parish_icem_lkup_config, self.census_year
        )

        self.parish_gis_config = ew_config.parish_gis_config

    def create_conparid(self, parish_icem_lkup_config, census_year):
        if census_year < 1901:
            conparid = parish_icem_lkup_config.conparid51_91_field
        else:
            conparid = parish_icem_lkup_config.conparid01_11_field
        return conparid

    def create_ew_parishboundaryprocessed(self):
        rsd_dictionary_processed = ew_geom_preprocess.read_rsd_dictionary(
            self.rsd_dictionary_config,
        )

        processed = ew_geom_preprocess.process_rsd_boundary_data(
            self.rsd_dictionary_config.rsd_id_field, self.rsd_gis_config
        )

        ukds_link = ew_geom_preprocess.read_gis_to_icem(
            self.parish_icem_lkup_config, self.conparid
        )

        parish = ew_geom_preprocess.process_parish_boundary_data(
            self.parish_gis_config,
            ukds_link,
            self.conparid,
            self.parish_icem_lkup_config.ukds_id_field,
        )

        (
            parish_data_processed,
            geom_blocking_cols,
        ) = ew_geom_preprocess.join_parish_rsd_boundary(
            parish, processed, self.conparid, self.rsd_dictionary_config.rsd_id_field
        )
        # print(parish_data_processed)
        return rsd_dictionary_processed, parish_data_processed, geom_blocking_cols

    def process_ew_census(self, rsd_dictionary_processed, tmpcensusdir):

        census_data = census.read_census(
            self.census_file, self.census_fields, self.census_csv_params
        )
        # print(census_data)
        census_cleaned = census.clean_census_address_data(
            census_data, self.census_fields.address, self.census_standardisation_file
        )
        # print(census_cleaned)
        census_linked, census_blocking_cols, census_counties = census.process_ew_census(
            census_cleaned,
            rsd_dictionary_processed,
            self.census_fields.parid,
            self.rsd_dictionary_config.cen_parid_field,
            self.rsd_dictionary_config.rsd_id_field,
            self.census_fields,
        )

        census.output_census(census_linked, tmpcensusdir, self.census_output_params)

        return census_blocking_cols, census_counties


class SCOT_geocoder(CensusGB_geocoder):
    def __init__(
        self,
        census_country,
        census_year,
        census_params,
        target_geoms,
        path_to_data,
        scot_config,
    ):
        super().__init__(
            census_country, census_year, census_params, target_geoms, path_to_data
        )

    # 		#### SCOTLAND SPECIFIC
    def create_scot_parishboundaryprocessed(self):

        pass

    def process_scot_census(self):

        self.process_census(self.census_file, self.census_fields)
        # scot unique here
        self.output_census()
        pass
        # scot_parish_lkup_file: str
        # 	Path to the lookup table that links the Scotland Parish boundary shapefile to the 'ParID' field in I-CeM.
        # print(scot_config)
        """
        SCOTLAND SPECIFIC VARIABLES
        """
        # self.scot_parish_lkup_file = self.set_scot_parish_lookup_file()

    # scot_parish_link = preprocess.scot_parish_lookup(self.scot_parish_lkup_file,self.census_year)
    # parish_data_processed = preprocess.process_scot_parish_boundary_data(self.parish_shapefile_path,scot_parish_link,self.census_year)
