from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import utils
import geocode
from geometry2 import TargetGeometry


@dataclass
class Census_vars:
    """A class to store variables for census geocoding.

    Attributes
    ----------

    country: str
        Country of census

    year: int
        Census year

    uid_field: str
        Column name of pandas.Series containing unique census person id.

    field_to_geocode: str
        Column name of pandas.Series containing field to geocode, e.g. Address field.

    boundaries_field: list
        # List of column names of boundary fields, e.g. 'ConParID' etc.

    census_file: str
        Path to census file.

    read_csv_params: dict
        Dictionary of parameters for reading csv files passed to pandas.read_csv().

    unique_field_to_geocode_name: str
        Column name for uid created in Census._create_uid_of_geocode_field().

    write_processed_csv_params: dict
        Dictionary of parameters for writing csv files pass to pandas.to_csv().

    write_processed_csv_params_slim: dict
        Dictionary of parameters for writing csv files pass to pandas.to_csv().

    comparers: dict
        Dictionary of comparison methods to pass to Geocode().

    comparison_method: str | None = None
        Type of comparison method, e.g. '1911_bespoke'.

    sim_comp_thresh: int | float
        Threshold for determining if string comparisons are sufficiently similar to be considered a match.

    align_thresh: int | float | None = None
        Threshold for alignment score, a match must be based on an alignment higher than align_thresh to be considered a match.

    final_score_field: str = "fs"
        Column name of field storing the final matching score.

    output_path: str = "../data/output_art_revs2"
        Directory path to write outputs to.

    output_filetype: str = ".tsv"
        Type of file (and file extension) of output files.

    process: bool = True
        Process census or read-in pre-processed census data. If False, processing steps are skipped and the code
        will compute comparisons between existing census and target geometry data.

    convert_non_ascii: bool = False
        Determine whether non ascii characters should be converted or not when processing addresses.

    field_to_clean: str = None
        Column name of field that will be cleaned and standardised using below variables.

    standardisation_file: str = None
        Path to standardisation file.
    min_len: int = None
        Minimum length of field_to_geocode entries. Entries/addresses below min_len are discarded.

    cleaned_field_suffix: str = None
        Suffix to add to column name of field_to_geocode, e.g. 'address_alt'.

    subset_field: str = None
        Column name of subset field (over which the code will iterate and output
        for each subset group the processed census and results).

    census_read_library: str = field(init=False)
        Read library for census data set by utils.get_readlibrary().

    subsetlist: list = field(init=False)
        Unique list of subset values in subset_field, for iterating over when processing and outputting geo-coded results.
    """

    country: str
    year: int
    uid_field: str
    field_to_geocode: str
    boundaries_field: list

    census_file: str
    read_csv_params: dict

    unique_field_to_geocode_name: str

    write_processed_csv_params: dict

    write_processed_csv_params_slim: dict

    output_path: str
    output_filetype: str

    comparers: dict
    comparison_method: str | None = None
    sim_comp_thresh: int | float = 0
    align_thresh: int | float | None = None
    final_score_field: str = "fs"

    process: bool = True
    lkups: dict = None

    convert_non_ascii: bool = False
    field_to_clean: str = None
    standardisation_file: str = None
    min_len: int = None
    cleaned_field_suffix: str = None

    subset_field: str = None

    census_read_library: str = field(init=False)

    subsetlist: list = field(init=False)

    def __post_init__(self):
        self.census_read_library = utils.get_readlibrary(
            self.census_file, self.read_csv_params
        )
        # utils.validate_pandas_read_csv_kwargs(
        #     self.census_file,
        #     self.read_csv_params,
        # ) already done in get_readlibrary


class Census:
    """A class for processing census data.

    Attributes
    ----------

    vars: `Census_vars`
        `Census_vars` class containing variables of census used throughout geocoding process.
        See `Census_vars` for more information.

    data: pd.DataFrame
        pd.DataFrame containing census data to be geo-coded.


    Methods
    -------
    `_addcensusvars()`
        Checks vars is type Census_vars, if not raise TypeError.

    `_read_census()`
        Reads census file to pd.DataFrame, assigns to data attribute.

    `_gensubsetlist()`
        Creates list of subset values if `vars.subset_field` is not `None`.

    `_process_census()`
        Bundles pre-processing steps into one method, includes `_cleanaddressfield()`, `_add_lkup()`,
        `_create_uid_of_geocode_field()`, `_create_censusforlinking()`.

    `_cleanaddressfield()`
        Cleans and standardises addresses if `field_to_clean` specified, re-assigns `field_to_geocode`
        to cleaned address field`, and writes original and cleaned addresses to file(s) for inspection.

    `_add_lkup()`
        Add lookup values to census data by iterating over dictionary of lkup parameters in `lkups`.

    `_create_uid_of_geocode_field()`
        Creates uid of each `field_to_geocode` within each geo-blocking unit, assigns uid to census data.
        Writes census data to file with newly added address uids.

    `_create_censusforlinking()`
        Reduces size of census data passed to `geocode()` to speed up geocoding by keeping only 1 entry for each address uid. Writes slimmed census data to file.

    `_write_census_data()`
        Write census data to file(s), outputting each subset (if specified) to a separate file.

    """

    def __init__(
        self,
        vars,
    ):

        self._addcensusvars(vars)
        self._read_census()
        self._gensubsetlist()  # may need to deal with

        if self.vars.process != False:

            self._process_census()

    def _addcensusvars(self, vars):
        """Checks vars is type Census_vars and assigns to self.vars. If not raise TypeError.

        Parameters
        ----------

        vars: `Census_vars`
            A `Census_vars` instance containing census variables.

        """
        if type(vars) is Census_vars:

            self.vars = vars

        else:
            raise TypeError(
                f"vars is {vars.__class__.__name__} must be {Census_vars.__name__}"
            )

    def _read_census(
        self,
    ):
        """Reads census file to `pd.DataFrame`, assigns to data attribute.

        Notes
        ----------

        `census_read_library` is the relevant pandas read library for the file type (.txt, .xlsx etc), set by `utils.get_readlibrary` in `Census.vars`.

        """

        print(f"Reading census {self.vars.country} {self.vars.year}")

        self.data = self.vars.census_read_library(
            self.vars.census_file,
            **self.vars.read_csv_params,
        )

    def _gensubsetlist(
        self,
    ):
        """Creates list of subset values if `vars.subset_field` is not `None`.

        Notes
        ----------

        If a subset_field is specified (recommended to avoid geocoding all census data at once), a subsetlist is created which is
        iterated over when a) writing the processed census files in `_write_census_data` b) when geocoding and writing geocoding outputs in `geocode`.

        """
        if self.vars.subset_field is not None:
            self.vars.subsetlist = self.data[self.vars.subset_field].unique()
        else:
            self.vars.subsetlist is None

    def _process_census(
        self,
    ):
        """Bundles pre-processing steps into one method, includes `_cleanaddressfield()`, `_add_lkup()`, `_create_uid_of_geocode_field()`, `_create_censusforlinking()`.
        Only adds lkup if `vars.lkups` is not `None`.

        """

        self._cleanaddressfield()

        if self.vars.lkups is not None:
            self._add_lkup()

        self._create_uid_of_geocode_field()
        self._create_censusforlinking()

    def _cleanaddressfield(
        self,
    ):
        """If `field_to_clean` is specified:
        1) Cleans and standardises specified `field_to_clean`
        2) Changes `field_to_geocode` to the cleaned field so that the geocoding process uses the cleaned addresses
        3) Writes cleaned data to file(s) using `_write_census_data()` so that original and cleaned/standardised fields can be compared.

        """

        if self.vars.field_to_clean is not None:
            self.data, field_to_clean_new = utils.clean_address_data(
                self.data,
                self.vars.field_to_clean,
                self.vars.standardisation_file,
                self.vars.min_len,
                self.vars.cleaned_field_suffix,
                self.vars.convert_non_ascii,
            )

            self.vars.field_to_geocode = field_to_clean_new

            self._write_census_data(
                "cleaned",  # specifies part of output name to identify this file
                self.vars.write_processed_csv_params,
            )

    def _add_lkup(
        self,
    ):
        """Add lookup values to census data by iterating over dictionary of lkup parameters in `lkups`."""

        for lkup, lkup_settings in self.vars.lkups.items():
            print(f"Adding {lkup}")

            self.data = utils.add_lkup(
                self.data,
                lkup_settings["lkup_file"],
                lkup_settings["lkup_params"],
                left_on=lkup_settings["lkup_census_field"],
                right_on=lkup_settings["lkup_uid_field"],
            )

    def _create_uid_of_geocode_field(
        self,
    ):
        """Creates uid of each `field_to_geocode` within each geo-blocking unit, assigns uid to census data. Writes census data to file with newly added address uids.

        Notes
        ----------

        `unique_field_to_geocode_name` is used throughout CensusGeocoder pipeline to keep track of addresses and link geocoded outputs
        back to individuals at those addresses. Used as `census_indexfield` attribute in `Geocode()`.

        """
        groupby_cols = []
        groupby_cols.extend([x for x in utils.flatten(self.vars.boundaries_field)])
        groupby_cols.append(self.vars.field_to_geocode)

        self.data[self.vars.unique_field_to_geocode_name] = self.data.groupby(
            groupby_cols, dropna=False
        ).ngroup()

        self.data = self.data.dropna(
            subset=self.vars.unique_field_to_geocode_name
        ).copy()

        self.data[self.vars.unique_field_to_geocode_name] = pd.to_numeric(
            self.data[self.vars.unique_field_to_geocode_name], downcast="integer"
        )

        self._write_census_data(
            "address_uid",  # specifies part of output name to identify this file
            self.vars.write_processed_csv_params,
        )

    def _create_censusforlinking(
        self,
    ):
        """Reduces size of census data passed to `geocode()` to speed up geocoding by keeping only 1 entry for each address uid. Writes slimmed census data to file.

        Notes
        ----------

        Individuals can be linked back to their geocoded output using the address uid and the RecID output in `_create_uid_of_geocode_field()`.

        """
        self.data = self.data.drop_duplicates(
            subset=[self.vars.unique_field_to_geocode_name],
        )

        self._write_census_data(
            "census_for_linking",  # specifies part of output name to identify this file
            self.vars.write_processed_csv_params_slim,
        )

    def _write_census_data(
        self,
        status,
        params,
    ):
        """Write census data to file(s), outputting each subset (if specified) to a separate file.

        Parameters
        ----------

        status: str
            Name specifying type of output file.

        params: dict
            Dictionary of parameters to be passed to `pd.to_csv` in `utils.write_df_to_file`.

        """

        if (
            type(self.vars.subsetlist) is np.ndarray
        ):  # checks for ndarray because subsetlist created used pd.unique which returns ndarray

            for sub in self.vars.subsetlist:
                filename = f"{self.vars.country}_{self.vars.year}_{status}_{sub}{self.vars.output_filetype}"
                output_path_components = [
                    str(x)
                    for x in [
                        self.vars.output_path,
                        self.vars.country,
                        self.vars.year,
                        sub,
                        filename,
                    ]
                ]

                output_df = self.data[self.data[self.vars.subset_field] == sub]
                utils.write_df_to_file(output_df, output_path_components, params)

        else:

            filename = f"{self.vars.country}_{self.vars.year}_{status}{self.vars.output_filetype}"
            output_path_components = [
                str(x)
                for x in [
                    self.vars.output_path,
                    self.vars.country,
                    self.vars.year,
                    filename,
                ]
            ]

            utils.write_df_to_file(output_df, output_path_components, params)

    def geocode(
        self,
        target_geometry,
    ):
        """Geocodes `field_to_geocode` using `geometry.GeoCode()`. Writes 3 types of output files (see `geometry.GeoCode.process_results()`).
        If subset list specified, iterates over subsets, geo-coding each subset and writing output files to their own directory.

        Parameters
        ----------

        target_geometry: `geometry.TargetGeometry`
            Instance of `geometry.TargetGeometry`

        """

        if type(target_geometry) is not TargetGeometry:
            raise TypeError(
                f"vars is {target_geometry.__class__.__name__} must be {TargetGeometry.__name__}"
            )

        if type(self.vars.subsetlist) is not np.ndarray:

            geocoded = geocode.GeoCode(
                census_data=self.data,
                census_geocode_field=self.vars.field_to_geocode,
                census_indexfield=self.vars.unique_field_to_geocode_name,
                target_geometry_data=target_geometry.data,
                target_geometry_geocode_field=target_geometry.vars.blockcols,
                target_geometry_indexfield=target_geometry.vars.item_per_unit_uid,
                census_block=self.vars.boundaries_field,
                target_geom_block=target_geometry.vars.blockcols,
                comparers=self.vars.comparers,
                sim_thresh=self.vars.sim_comp_thresh,
                align_thresh=self.vars.align_thresh,
                final_score_field=self.vars.final_score_field,
                comparison_method=self.vars.comparison_method,
            )

            for outputfiletype, outputdata in geocoded.rslts_dict.items():

                filename = f"{self.vars.country}_{self.vars.year}_{target_geometry.vars.geom_name}_{outputfiletype}{self.vars.output_filetype}"

                output_path_components = [
                    str(x)
                    for x in [
                        self.vars.output_path,
                        self.vars.country,
                        self.vars.year,
                        filename,
                    ]
                ]

                utils.write_df_to_file(
                    outputdata,
                    output_path_components,
                    self.vars.write_processed_csv_params,
                )

        else:

            for subset in self.vars.subsetlist:
                census_data = self.data[self.data[self.vars.subset_field] == subset]
                geocoded = geocode.GeoCode(
                    census_data=census_data,
                    census_geocode_field=self.vars.field_to_geocode,
                    census_indexfield=self.vars.unique_field_to_geocode_name,
                    target_geometry_data=target_geometry.data,
                    target_geometry_geocode_field=target_geometry.vars.gis_geocode_field,
                    target_geometry_indexfield=target_geometry.vars.item_per_unit_uid,
                    census_block=self.vars.boundaries_field,
                    target_geom_block=target_geometry.vars.blockcols,
                    comparers=self.vars.comparers,
                    sim_thresh=self.vars.sim_comp_thresh,
                    align_thresh=self.vars.align_thresh,
                    final_score_field=self.vars.final_score_field,
                    comparison_method=self.vars.comparison_method,
                )

                for outputfiletype, outputdata in geocoded.rslts_dict.items():

                    filename = f"{self.vars.country}_{self.vars.year}_{target_geometry.vars.geom_name}_{subset}_{outputfiletype}{self.vars.output_filetype}"

                    output_path_components = [
                        str(x)
                        for x in [
                            self.vars.output_path,
                            self.vars.country,
                            self.vars.year,
                            subset,
                            filename,
                        ]
                    ]

                    utils.write_df_to_file(
                        outputdata,
                        output_path_components,
                        self.vars.write_processed_csv_params,
                    )
