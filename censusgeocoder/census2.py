import json
from dataclasses import dataclass, field, fields

import dask.dataframe as dd
import numpy as np
import pandas as pd
import utils
import pathlib
import geocode
from geometry2 import TargetGeometry
import pathlib


@dataclass
class Census_vars:
    """
    A class to store variables for census geocoding.

    Attributes
    ----------

    country: str
        Country of census

    year: int
        Census year

    uid_field: str
        Column name of pandas.Series containing unique census person id.
    """

    country: str
    year: int
    uid_field: str
    field_to_geocode: str
    boundaries_field: list

    census_file: str
    read_csv_params: dict

    unique_field_to_geocode_name: str

    # output_file_slim: str

    write_processed_csv_params: dict

    write_processed_csv_params_slim: dict

    # read_processed_csv_params: dict

    comparers: dict
    comparison_method: str | None = None
    sim_comp_thresh: int | float | None = None
    align_thresh: int | float | None = None
    final_score_field: str = "fs"

    output_path: str = "../data/output_art_revs2"
    output_filetype: str = ".tsv"

    process: bool = True
    lkup_file: str = None
    lkup_uid_field: str = None
    lkup_census_field: str = None
    lkup_params: dict = None

    convert_non_ascii: bool = False
    field_to_clean: str = None
    standardisation_file: str = None
    min_len: int = None
    cleaned_field_suffix: str = None

    subset_field: str = None

    census_read_library: str = field(init=False)
    # census_processed_read_library: str = field(init=False) #this one is the problem
    census_lkup_read_library: str = field(init=False)
    subsetlist: list = field(init=False)

    # field_to_clean_new: str = field(init=False)

    def __post_init__(self):
        self.census_read_library = utils.get_readlibrary(
            self.census_file, self.read_csv_params
        )
        utils.validate_pandas_read_csv_kwargs(
            self.census_file,
            self.read_csv_params,
        )

        if self.process != False:
            # self.census_processed_read_library = utils.get_readlibrary(self.output_file_slim, self.read_processed_csv_params, )
            # utils.validate_pandas_read_csv_kwargs(self.census_file, self.read_processed_csv_params,)

            if self.lkup_file != None:
                self.census_lkup_read_library = utils.get_readlibrary(
                    self.lkup_file,
                    self.lkup_params,
                )

            else:
                self.census_lkup_read_library = None

        # utils.validate_pandas_to_csv_kwargs(self.output_file, self.write_processed_csv_params)
        # utils.validate_pandas_to_csv_kwargs(self.output_file_slim, self.write_processed_csv_params_slim)


class Census:
    def __init__(
        self,
        vars,
    ):
        if type(vars) == Census_vars:

            self.vars = vars
        else:
            raise TypeError("Must be a Census_vars class")

        self.read_census()
        self._gensubsetlist()  # may need to deal with

        if self.vars.process != False:

            self.process_census()
            self.add_lkup()
            self.create_uid_of_geocode_field()

    def process_census(
        self,
    ):

        if self.vars.field_to_clean != None:
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
            "standardised",
            self.vars.write_processed_csv_params,
        )

    def read_census(
        self,
    ):
        """Reads census file returns a pandas dataframe

        Parameters
        ----------
        census_file: str
            Path to census data.

        read_params: dict
            A dictionary containing Dask/Pandas parameters for reading census csv file.

        Returns
        --------
        census_data: dask.DataFrame
        """

        print(f"Reading census {self.vars.country} {self.vars.year}")

        self.data = self.vars.census_read_library(
            self.vars.census_file,
            **self.vars.read_csv_params,
        )

    def _gensubsetlist(
        self,
    ):
        if self.vars.subset_field != None:
            self.vars.subsetlist = self.data[self.vars.subset_field].unique()
        else:
            self.vars.subsetlist == None

    def _write_census_data(
        self,
        status,
        params,
    ):

        if type(self.vars.subsetlist) == np.ndarray:
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

    def add_lkup(
        self,
    ):
        if self.vars.lkup_file != None:
            lkup_data = self.vars.census_lkup_read_library(
                self.vars.lkup_file,
                **self.vars.lkup_params,
            )

            print(len(self.data))

            self.data = pd.merge(
                left=self.data,
                right=lkup_data,
                left_on=self.vars.lkup_census_field,
                right_on=self.vars.lkup_uid_field,
                how="left",
            )

            print(len(self.data))

    def create_uid_of_geocode_field(
        self,
    ):
        """Groups field to geocode by boundary fields to create unique groups of addresses in each boundary. Assigns uid to each address"""
        groupby_cols = []
        groupby_cols.extend(
            [x for x in utils.flatten(self.vars.boundaries_field)]
        )  # this may not be correct as the boundaries field should include ConParID and CEN_1851
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
            "address_uid",
            self.vars.write_processed_csv_params,
        )

    def create_censusforlinking(
        self,
    ):
        self.data = self.data.drop_duplicates(
            subset=[self.vars.unique_field_to_geocode_name],
        )

        # col_list = []
        # col_list.extend([self.vars.unique_field_to_geocode_name,
        #                        self.vars.field_to_geocode,
        #                        self.vars.subset_field, ])
        # col_list.extend([item for item in list(utils.flatten(self.vars.boundaries_field))])

        # self.data = self.data[]
        self._write_census_data(
            "slim",
            self.vars.write_processed_csv_params_slim,
        )

    def geocode(
        self,
        target_geometry,
    ):
        """Geocodes census data"""

        assert type(target_geometry) == TargetGeometry

        if type(self.vars.subsetlist) != np.ndarray:

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

            for x, y in geocoded.rslts_dict.items():

                filename = f"{self.vars.country}_{self.vars.year}_{target_geometry.vars.geom_name}_{x}{self.vars.output_filetype}"

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
                    y,
                    output_path_components,
                    self.vars.write_processed_csv_params,
                )

        else:

            for cen in self.vars.subsetlist:
                census_data = self.data[self.data[self.vars.subset_field] == cen]
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

                for x, y in geocoded.rslts_dict.items():

                    filename = f"{self.vars.country}_{self.vars.year}_{target_geometry.vars.geom_name}_{cen}_{x}{self.vars.output_filetype}"

                    output_path_components = [
                        str(x)
                        for x in [
                            self.vars.output_path,
                            self.vars.country,
                            self.vars.year,
                            cen,
                            filename,
                        ]
                    ]

                    utils.write_df_to_file(
                        y,
                        output_path_components,
                        self.vars.write_processed_csv_params,
                    )
