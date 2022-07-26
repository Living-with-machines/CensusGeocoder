import geopandas as gpd
import pandas as pd


def process_scot_boundary(boundary_config):
    """
    Reads combined Scotland parish boundary data.

    Parameters
    ----------
    boundary_config: Dataclass
        Dataclass containing parameters for reading Parish GIS Boundary data
        for census year.

    Returns
    --------
    parish_boundary: geopandas.GeoDataFrame
        A geopandas geodataframe containing the parish Boundary data for census year.

    geom_blocking_cols: list
        List of columns for geo-blocking when running string comparisons.
    """
    tmp_file = gpd.read_file(boundary_config.filepath, rows=1)
    list_of_all_cols = tmp_file.columns.values.tolist()
    cols_to_keep = [boundary_config.uid, tmp_file.geometry.name]
    unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

    parish_boundary = gpd.read_file(
        boundary_config.filepath,
        ignore_fields=unwanted_cols,
        crs=boundary_config.projection,
    )

    parish_boundary[boundary_config.uid] = parish_boundary[
        boundary_config.uid
    ].str.upper()

    parish_boundary["tmp_id"] = parish_boundary[boundary_config.uid]

    geom_blocking_cols = []
    geom_blocking_cols.append(boundary_config.uid)

    return parish_boundary, geom_blocking_cols


def process_scot_lkup(boundary_lkup_config, boundary_config):
    """
    Reads lookup table linking Scottish parish boundary data to
    I-CeM.

    Parameters
    ----------
    boundary_lkup_config : Dataclass
        Dataclass containing parameters for reading lookup table.
    boundary_config : Dataclass
        Dataclass containing parameters for reading GIS boundary data.

    Returns
    --------
    boundary_lkup: pandas.DataFrame
        A Pandas DataFrame containing the lookup table.
    """
    list_of_cols = [boundary_lkup_config.parid_field, boundary_config.uid]
    boundary_lkup = pd.read_excel(
        boundary_lkup_config.filepath,
        sheet_name=boundary_lkup_config.sheet,
        usecols=list_of_cols,
    )
    return boundary_lkup


# def merge_lkup(parish_boundary, boundary_lkup, boundary_config, boundary_lkup_config):
#     processed_parish_boundary = pd.merge(
#         left=parish_boundary,
#         right=boundary_lkup,
#         left_on=boundary_config.uid,
#         right_on=boundary_lkup_config.uid,
#         how="inner",
#     )
#     return processed_parish_boundary

