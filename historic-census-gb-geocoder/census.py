import pathlib
import pandas as pd
import json
import dask.dataframe as dd
import numpy as np


def process_census(
    census_file, rsd_dictionary, rows_to_use, field_dict, census_year, country
):

    """
    Read the census file and prepare it for subsquent geo-coding steps.

    Parameters
    ----------
    census_file: str
        Path to census file.

    rows_to_use: int or None
        The rows to read from the dataset as specified by the type of geo-coding, either 'full' or 'testing' in parameters json.

    field_dict: dictionary
        Dictionary with field values.

    Returns
    -------
    pandas.DataFrame
        A pandas dataframe containing the processed census data for each individual.

    pandas.DataFrame
        A pandas dataframe containing unique addresses and counties.

    list
        A sorted list of census counties.
    """

    census_variables = [
        "safehaven_id",
        "address_anonymised",
        "ConParID",
        "ParID",
        "RegCnty",
    ]
    print("Reading census")

    census_dd = dd.read_csv(
        census_file,
        sep="\t",
        encoding="latin-1",
        na_values=".",
        usecols=census_variables,
        quoting=3,
        blocksize=25e6,
        assume_missing=True,
    )
    # census_dd.to_parquet(f'./data/input/census_parquet/{census_year}/{country}/', partition_on=['RegCnty'], engine="pyarrow")

    # census = pd.read_csv(census_file,sep="\t",quoting=3,encoding = "latin-1",na_values=".",usecols=census_variables,nrows=rows_to_use)
    print("Successfully read census")

    census_dd["ConParID"] = pd.to_numeric(census_dd["ConParID"], errors="coerce")

    census_dd = census_dd.rename(
        columns={"address_anonymised": "add_anon", "safehaven_id": "sh_id"}
    )  # This isn't necessary now as output is tsv not .shp so field names don't have to be under 10 characters long.

    # Make limited regex replacements to standardise street names
    with open("./inputs/icem_street_standardisation.json") as f:
        street_standardisation = json.load(f)
    census_dd["add_anon"] = census_dd["add_anon"].replace(
        street_standardisation, regex=True
    )
    census_dd["add_anon"] = census_dd["add_anon"].replace("^\\s*$", np.nan, regex=True)
    census_dd["add_anon"] = census_dd["add_anon"].str.strip()
    census_dd = census_dd.dropna(subset=["add_anon"]).copy()

    if field_dict["country"] == "EW":
        census_dd = dd.merge(
            left=census_dd,
            right=rsd_dictionary,
            left_on="ParID",
            right_on=field_dict["parid_for_rsd_dict"],
            how="left",
        )
        census_dd[field_dict["cen"]] = pd.to_numeric(
            census_dd[field_dict["cen"]], errors="coerce"
        )
        # Create an id for each unique 'address' + ConParID + CEN_1901 combination
        census_dd["unique_add_id"] = (
            census_dd["add_anon"].astype(str)
            + "_"
            + census_dd["ConParID"].astype(str)
            + "_"
            + census_dd[field_dict["cen"]].astype(str)
        )
        print("Merged with RSD dictionary")
    elif field_dict["country"] == "SCOT":
        census_dd["unique_add_id"] = (
            census_dd["add_anon"].astype(str) + "_" + census_dd["ParID"].astype(str)
        )

    census_dd.to_parquet(
        f"./data/input/census_parquet/{census_year}/{country}/",
        partition_on=["RegCnty"],
        engine="pyarrow",
    )

    # trial = pd.read_parquet(f'./data/input/census_parquet/{census_year}/{country}/',filters=[[('RegCnty','=','Anglesey')]])
    # print(trial)
    # census_counties = census['RegCnty'].unique()
    # census_counties = sorted(census_counties)

    return


def read_census(census_file, census_cols, csv_params):
    cols_to_use = [*census_cols.values()]
    # census_variables = ['safehaven_id','address_anonymised','ConParID','ParID','RegCnty']
    print("Reading census")

    census_dd = dd.read_csv(
        census_file,
        sep=csv_params["sep"],
        encoding=csv_params["encoding"],
        na_values=csv_params["na_values"],
        usecols=cols_to_use,
        quoting=csv_params["quoting"],
        blocksize=csv_params["blocksize"],
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
        census_dd[census_fields["address"]].astype(str)
        + "_"
        + census_dd[census_fields["consistentparid"]].astype(str)
        + "_"
        + census_dd[rsd_id_field].astype(str)
    )
    print("Merged with RSD dictionary")
    print(census_dd)

    census_blocking_cols = [census_fields["consistentparid"], rsd_id_field]

    census_counties = sorted(census_dd["RegCnty"].unique())

    return census_dd, census_blocking_cols, census_counties


def output_census(census_dd, outputdir, output_params):
    census_dd.to_parquet(
        f"{outputdir}", partition_on=output_params["partition_on"], engine="pyarrow"
    )
    pass


def get_census_countylist(outputdir):
    census_counties = []
    for p in pathlib.Path(outputdir).iterdir():
        census_counties.append(p.stem.split("=")[1])
    census_counties = sorted(census_counties)
    full_output_list = []
    pass


def create_county_subset(
    county, outputdir, census_fields
):  # Need to use county field from census fields
    # outputdir = outputdir +'/'
    census_subset = pd.read_parquet(
        outputdir, filters=[[("RegCnty", "=", f"{county}")]]
    )
    print(outputdir)
    # print(census_subset)
    # # Drop duplicate addresses, drop sh_id column
    census_subset = census_subset.drop_duplicates(
        subset=["unique_add_id"]
    ).copy()  # This could be changed so that when the census data is written to parquet only unique addresses are written - this would remove the need to write all the data to parquet, read in and then subset.
    # # Set the 'unique_add_id' field as the index
    census_subset = census_subset.set_index("unique_add_id")

    return census_subset
