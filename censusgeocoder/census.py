import json

import dask.dataframe as dd
import numpy as np
import pandas as pd
import utils

class Census:
    """Census Class
    vars:
    year
    country
    address_field
    read_params
    output_params


    methods:
    read_census
    clean address data
    process
    write output


    """
    def __init__(self, year, country, fields, census_file, read_params, standardisation_file, write_params, ):
        self.year = year
        self.country = country
        self.fields = fields
        self.census_file = census_file
        self.read_params = read_params
        self.standardisation_file = standardisation_file
        self.write_params = write_params


        self.data = self.read_census(self.census_file, **self.read_params)
        self.data = utils.clean_address_data(self.data, 
                                        self.fields["address"], 
                                        self.standardisation_file, )
        # self.data = self.clean_address_data(self.data, self.fields["Address"], self.standardisation_file, )

    def read_census(self, census_file, **read_params):
        """Reads census file returns a dask dataframe

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

        print("Reading census")

        census_data = dd.read_csv(census_file,  **read_params,)

        return census_data

    pass


    # def clean_address_data(self, census_data, address_field, standardisation_file):
    #     """Clean address data using regex replacement patterns set in json file

    #     Parameters
    #     ----------
    #     census_data: dask.DataFrame
    #         Dask DataFrame holding census data.

    #     address_field: str
    #         Column name of address field in census_data.

    #     standardisation_file: str
    #         Path to standardisation json file containing regex replacement patterns.
        
    #     Returns
    #     --------
    #     census_data: dask.DataFrame
    #     """
    #     if standardisation_file is not None:
    #         with open(standardisation_file) as f:
    #             street_standardisation = json.load(f)
    #         census_data[address_field] = census_data[address_field].replace(
    #             street_standardisation, regex=True
    #         )
    #         census_data = census_data.fillna(value=np.nan)
    #         census_data[address_field] = census_data[address_field].str.strip()
    #         census_data = census_data.dropna(subset=address_field).copy()

    #     return census_data


# def process_ew_census(
#     census_cleaned, rsd_dictionary, census_params, rsd_dictionary_config,
# ):
#     """Process England and Wales census data.

#     Merges census data with rsd dictonary. Creates new unique id from address,
#     conparid, and rsd id fields.

    
#     Parameters
#     ----------
#     census_cleaned: dask.DataFrame
#         Dask dataframe holding census data for census year.

#     rsd_dictionary: pandas.DataFrame
#         Pandas DataFrame containing rsd_dictionary lookup table for census year.

#     census_params: Dataclass
#         Dataclass containing parameters for census year.

#     rsd_dictionary_config:
#         Dataclass containing parameters for rsd dictionary.

#     Returns
#     --------
#     census_dd: dask.DataFrame
#         Dask DataFrame containing census data with new attributes.

#     census_blocking_cols: list
#         List of census columns for geo-blocking when running string comparisons.

#     partition_list: list
#         List of partition values from census data.
#     """


#     census_cleaned = census_cleaned.dropna(subset=census_params.census_fields["conparid"]).copy()
#     census_cleaned = census_cleaned.astype({census_params.census_fields["conparid"]:"int32"})

#     census_dd = dd.merge(
#         left=census_cleaned,
#         right=rsd_dictionary,
#         left_on=census_params.census_fields["parid"],
#         right_on=rsd_dictionary_config.cen_parid_field,
#         how="left",
#     )
    
#     census_dd[census_params.census_output_params.new_uid] = (
#         census_dd[census_params.census_fields["address"]].astype(str)
#         + "_"
#         + census_dd[census_params.census_fields["conparid"]].astype(str)
#         + "_"
#         + census_dd[rsd_dictionary_config.rsd_id_field].astype(str)
#     )

#     census_dd = census_dd.dropna()
#     print("Merged with RSD dictionary")

#     census_blocking_cols = [
#         census_params.census_fields["conparid"],
#         rsd_dictionary_config.rsd_id_field,
#     ]

#     partition_list = sorted(
#         census_dd[census_params.census_output_params.partition_on].unique()
#     )

#     return census_dd, census_blocking_cols, partition_list


# def output_census(census_dd, outputdir, output_params):
#     """Write census data to parquet files

#     Parameters
#     ----------
#     census_dd: dask.DataFrame
#         Dask dataframe holding census data for census year.

#     outputdir: str
#         Path to output directory.

#     output_params: Dataclass
#         Dataclass containing parameters for outputting census data.
#     """
#     census_dd.to_parquet(
#         outputdir, partition_on=output_params.partition_on, engine="pyarrow"
#     )
#     print(f"Created census parquet files, partitioned on {output_params.partition_on}")


# def read_partition(partition, censusdir, census_params, cols_to_read=None):
#     census_subset = pd.read_parquet(
#         censusdir,
#         filters=[[(census_params.census_output_params.partition_on, "=", partition)]],
#         columns=cols_to_read,
#     )
#     return census_subset


# def write_partition(partition, partition_name, census_params, output_dir):
#     partition.to_csv(
#         output_dir / f"{census_params.country}_{census_params.year}"
#         f"_{partition_name}_lkup{census_params.census_output_params.filetype}",
#         **census_params.census_output_params.to_csv_kwargs,
#     )
#     pass


# def create_partition_subset(partition, censusdir, census_params):
#     """Read a subset of census data based on given partition. Then keeps only
#     unique addresses within a parish/parish & rsd by dropping duplicates of the
#     new unique id field.  

#     Parameters
#     ----------
#     partition: str
#         Partition value, e.g. a county like 'Essex'.

#     censusdir: str
#         Path to directory containing census data.
        
#     census_params: Dataclass
#         Dataclass containing parameters for census year.

#     Returns
#     -------
#     census_subset: pandas.DataFrame
#         Pandas DataFrame containing census data subset on specified partition
#         and only one entry for each unique address.

#     # census_subset_all: pandas.DataFrame
#     #     Pandas DataFrame containing census data subset on specified partition
#     #     with all unique person ids and address ids.

#     inds_in_part: int
#         The number of individuals in this partition.

#     adds_in_part: int
#         The number of unique addresses in this partition.
#     """
#     census_subset = read_partition(partition, censusdir, census_params)
#     inds_in_part = len(census_subset)

#     census_subset = (
#         census_subset.drop_duplicates(
#             subset=[census_params.census_output_params.new_uid]
#         )
#         .copy()
#         .drop(columns=census_params.census_fields["uid"])
#     )

#     adds_in_part = len(census_subset)
#     census_subset = census_subset.set_index(census_params.census_output_params.new_uid)

#     return census_subset, inds_in_part, adds_in_part


# def process_scot_census(
#     census_cleaned, boundary_lkup, boundary_lkup_config, census_params,
# ):
#     """Process Scotland census data. Merges census data with lookup table
#     which adds an id to link the census data to GIS parish boundary files.
    
#     Parameters
#     ----------
#     census_cleaned: dask.DataFrame
#         Dask dataframe holding census data for census year.

#     boundary_lkup: pandas.DataFrame
#         Pandas DataFrame containing parish lookup table for census year.

#     boundary_lkup_config:
#         Dataclass containing parameters for boundary lookup table.

#     census_params: Dataclass
#         Dataclass containing parameters for census year.

#     Returns
#     --------
#     census_dd: dask.DataFrame
#         Dask DataFrame containing census data with new attributes.

#     census_blocking_cols: list
#         List of census columns for geo-blocking when running string comparisons.

#     partition_list: list
#         List of partition values from census data.
#     """

#     # print(census_cleaned[census_cleaned["RecID"] == 763827].compute().head())

#     census_dd = dd.merge(
#         left=census_cleaned,
#         right=boundary_lkup,
#         left_on=census_params.census_fields["parid"],
#         right_on=boundary_lkup_config.parid_field,
#         how="left",
#     )
#     # print(census_dd[census_dd["RecID"] == 763827].compute().head(10))
#     census_dd[boundary_lkup_config.parid_field] = pd.to_numeric(
#         census_dd[boundary_lkup_config.parid_field], errors="coerce"
#     )

#     census_dd[census_params.census_output_params.new_uid] = (
#         census_dd[census_params.census_fields["address"]].astype(str)
#         + "_"
#         # + census_dd[boundary_lkup_config.uid].astype(str)
#         + census_dd["merged_id"].astype(str)
#     )
#     # print("Merged with RSD dictionary")

#     census_dd = census_dd.dropna()

#     census_blocking_cols = [
#         # boundary_lkup_config.uid,
#         "merged_id",
#     ]

#     partition_list = sorted(
#         census_dd[census_params.census_output_params.partition_on].unique()
#     )
#     # print(census_dd)
#     return census_dd, census_blocking_cols, partition_list
