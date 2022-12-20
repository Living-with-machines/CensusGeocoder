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
    geom_blocking_cols.append("merged_id")

    return parish_boundary, geom_blocking_cols


def process_scot_lkup(
    boundary_lkup_config, boundary_config
):  ##### MAKE SURE THAT THE BOUNDARIES ARE DISSOLVED ON THE PARID TO ACCOUNT FOR MULTIPLE PARISHES BEING LINKED TO ONE PARID - BUT SOMETIMES THERE IS ONE PARISH SPLIT ACROSS MULTIPLE PARIDS - BASICALLY THESE CAN BE MANY-TO-MANY RELATIONSHIPS
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
    list_of_cols = [
        boundary_lkup_config.parid_field,
        boundary_lkup_config.link_id,
        boundary_config.uid,
    ]
    boundary_lkup = pd.read_excel(
        boundary_lkup_config.filepath,
        sheet_name=boundary_lkup_config.sheet,
        usecols=list_of_cols,
    )

    boundary_lkup = boundary_lkup.drop_duplicates(
        subset=[boundary_lkup_config.parid_field, boundary_lkup_config.link_id]
    ).copy()

    return boundary_lkup


def merge_lkup(parish_boundary, boundary_lkup, boundary_config, boundary_lkup_config):
    processed_parish_boundary = pd.merge(
        left=parish_boundary,
        right=boundary_lkup,
        left_on=boundary_config.uid,
        right_on=boundary_lkup_config.uid,
        how="inner",
        # validate="one_to_one",
    )
    return processed_parish_boundary


def dissolve_scot_boundary(
    processed_parish_boundary, dissolve_field, boundary_lkup_config,
):

    dissolved_scot_boundary = processed_parish_boundary.dissolve(
        by="merged_id", aggfunc={boundary_lkup_config.uid: "_".join},
    )

    # dissolved_scot_boundary_2 = processed_parish_boundary.dissolve(
    #     by="name", aggfunc={boundary_lkup_config.parid_field: "_".join}
    # )
    dissolved_scot_boundary = dissolved_scot_boundary.reset_index()
    dissolved_scot_boundary = dissolved_scot_boundary.rename(
        columns={boundary_lkup_config.uid: "new_name"}
    )
    dissolved_scot_boundary["tmp_id"] = dissolved_scot_boundary["merged_id"]
    # print(dissolved_scot_boundary)
    # dissolved_scot_boundary_2 = dissolved_scot_boundary_2.rename(
    #     columns={boundary_lkup_config.parid_field: "new_parid"}
    # ).reset_index()

    return dissolved_scot_boundary
