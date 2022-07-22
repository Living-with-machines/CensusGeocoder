import json

import dask.dataframe as dd
import numpy as np
import pandas as pd


def read_census(census_file, census_cols, csv_params):
    """Reads census file returns a dask dataframe

    Parameters
    ----------
    census_file: str
        Path to census data.

    census_cols: list
        List of columns to read from census file.

    csv_params: Dataclass
        A Dataclass containing read_csv parameters.

    Returns
    --------
    census_dd: dask.DataFrame
    """

    print("Reading census")

    census_dd = dd.read_csv(
        census_file,
        sep=csv_params.sep,
        encoding=csv_params.encoding,
        na_values=csv_params.na_values,
        usecols=census_cols,
        quoting=csv_params.quoting,
        blocksize=csv_params.blocksize,
        assume_missing=True,
    )

    return census_dd


def clean_census_address_data(census_dd, address_field, standardisation_file):
    """Clean address data using regex replacement patterns set in json file

    Parameters
    ----------
    census_dd: dask.DataFrame
        Dask DataFrame holding census data.

    address_field: str
        Column name of address field in census_dd.

    standardisation_file: str
        Path to standardisation json file containing regex replacement patterns.
    
    Returns
    --------
    census_dd: dask.DataFrame
    """

    with open(standardisation_file) as f:
        street_standardisation = json.load(f)
    census_dd[address_field] = census_dd[address_field].replace(
        street_standardisation, regex=True
    )
    census_dd = census_dd.fillna(value=np.nan)
    census_dd[address_field] = census_dd[address_field].str.strip()
    census_dd = census_dd.dropna(subset=[address_field]).copy()

    return census_dd


def process_ew_census(
    census_cleaned, rsd_dictionary, census_params, rsd_dictionary_config,
):
    """Process England and Wales census data.

    Merges census data with rsd dictonary. Creates new unique id from address,
    conparid, and rsd id fields.

    
    Parameters
    ----------
    census_cleaned: dask.DataFrame
        Dask dataframe holding census data for census year.

    rsd_dictionary: pandas.DataFrame
        Pandas DataFrame containing rsd_dictionary lookup table for census year.

    census_params: Dataclass
        Dataclass containing parameters for census year.

    rsd_dictionary_config:
        Dataclass containing parameters for rsd dictionary.

    Returns
    --------
    census_dd: dask.DataFrame
        Dask DataFrame containing census data with new attributes.

    census_blocking_cols: list
        List of census columns for geo-blocking when running string comparisons.

    census_counties: list
        List of counties in census data.
    """
    census_dd = dd.merge(
        left=census_cleaned,
        right=rsd_dictionary,
        left_on=census_params.census_fields.parid,
        right_on=rsd_dictionary_config.cen_parid_field,
        how="left",
    )
    census_dd[rsd_dictionary_config.rsd_id_field] = pd.to_numeric(
        census_dd[rsd_dictionary_config.rsd_id_field], errors="coerce"
    )

    census_dd[census_params.census_output_params.new_uid] = (
        census_dd[census_params.census_fields.address].astype(str)
        + "_"
        + census_dd[census_params.census_fields.conparid].astype(str)
        + "_"
        + census_dd[rsd_dictionary_config.rsd_id_field].astype(str)
    )
    print("Merged with RSD dictionary")

    census_blocking_cols = [
        census_params.census_fields.conparid,
        rsd_dictionary_config.rsd_id_field,
    ]

    census_counties = sorted(census_dd.RegCnty.unique())

    return census_dd, census_blocking_cols, census_counties


def output_census(census_dd, outputdir, output_params):
    """Write census data to parquet files

    Parameters
    ----------
    census_dd: dask.DataFrame
        Dask dataframe holding census data for census year.

    outputdir: str
        Path to output directory.

    output_params: Dataclass
        Dataclass containing parameters for outputting census data.
    """
    census_dd.to_parquet(
        outputdir, partition_on=output_params.partition_on, engine="pyarrow"
    )
    print(f"Created census parquet files, partitioned on {output_params.partition_on}")


def create_partition_subset(partition, censusdir, census_params):
    """Read a subset of census data based on given partition. Then keeps only
    unique addresses within a parish/parish & rsd by dropping duplicates of the
    new unique id field.  

    Parameters
    ----------
    partition: str
        Partition value, e.g. a county like 'Essex'.

    censusdir: str
        Path to directory containing census data.
        
    census_params: Dataclass
        Dataclass containing parameters for census year.

    Returns
    -------
    census_subset: pandas.DataFrame
        Pandas DataFrame containing census data subset on specified partition
        and only one entry for each unique address.
    """

    census_subset = pd.read_parquet(
        censusdir,
        filters=[
            [(census_params.census_output_params.partition_on, "=", f"{partition}")]
        ],
    )

    census_subset = (
        census_subset.drop_duplicates(
            subset=[census_params.census_output_params.new_uid]
        )
        .copy()
        .drop(columns=census_params.census_fields.uid)
    )
    census_subset = census_subset.set_index(census_params.census_output_params.new_uid)

    return census_subset
