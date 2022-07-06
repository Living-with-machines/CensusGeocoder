import pandas as pd
import json
import dask.dataframe as dd
import numpy as np


def read_census(census_file, census_cols, csv_params):
    cols_to_use = census_cols.list_cols()

    print("Reading census")

    census_dd = dd.read_csv(
        census_file,
        sep=csv_params.sep,
        encoding=csv_params.encoding,
        na_values=csv_params.na_values,
        usecols=cols_to_use,
        quoting=csv_params.quoting,
        blocksize=csv_params.blocksize,
        assume_missing=True,
    )

    return census_dd


def clean_census_address_data(census_dd, address_field, standarisation_file):

    with open(standarisation_file) as f:
        street_standardisation = json.load(f)
    census_dd[address_field] = census_dd[address_field].replace(
        street_standardisation, regex=True
    )
    census_dd = census_dd.fillna(value=np.nan)
    census_dd[address_field] = census_dd[address_field].str.strip()
    census_dd = census_dd.dropna(subset=[address_field]).copy()

    return census_dd


def process_ew_census(
    census_dd, rsd_dictionary, parid_field, parid_rsd_field, rsd_id_field, census_fields
):
    census_dd = dd.merge(
        left=census_dd,
        right=rsd_dictionary,
        left_on=parid_field,
        right_on=parid_rsd_field,
        how="left",
    )
    census_dd[rsd_id_field] = pd.to_numeric(census_dd[rsd_id_field], errors="coerce")
    # Create an id for each unique 'address' + ConParID + CEN_1901 combination
    census_dd["unique_add_id"] = (
        census_dd[census_fields.address].astype(str)
        + "_"
        + census_dd[census_fields.conparid].astype(str)
        + "_"
        + census_dd[rsd_id_field].astype(str)
    )
    print("Merged with RSD dictionary")
    print(census_dd)

    census_blocking_cols = [census_fields.conparid, rsd_id_field]

    census_counties = sorted(census_dd.RegCnty.unique())

    return census_dd, census_blocking_cols, census_counties


def output_census(census_dd, outputdir, output_params):
    census_dd.to_parquet(
        f"{outputdir}", partition_on=output_params.partition_on, engine="pyarrow"
    )
    pass


def create_partition_subset(
    partition, tmpcensusdir, census_output_params
):  # Need to use county field from census fields
    # outputdir = outputdir +'/'
    census_subset = pd.read_parquet(
        tmpcensusdir,
        filters=[[(census_output_params.partition_on, "=", f"{partition}")]],
    )
    print(tmpcensusdir)
    # print(census_subset)
    # # Drop duplicate addresses, drop sh_id column
    census_subset = census_subset.drop_duplicates(
        subset=[census_output_params.new_uid]
    ).copy()  # This could be changed so that when the census data is
    # written to parquet only unique addresses are written - this
    # would remove the need to write all the data to parquet, read in and then subset.
    # # Set the 'unique_add_id' field as the index
    census_subset = census_subset.set_index(census_output_params.new_uid)

    return census_subset
