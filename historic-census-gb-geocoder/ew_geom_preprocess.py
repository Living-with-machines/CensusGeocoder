import pandas as pd
import geopandas as gpd
import pygeos as pg


# gpd.options.use_pygeos = True


def process_rsd_boundary_data(rsd_id_field, rsd_gis_config):
    """
    Reads combined Parish / Registration Sub District (RSD) boundary data

    Parameters
    ----------
    path_to_rsd_boundary_data : str, path object
        Either the absolute or relative path to the combined Parish/RSD boundary file.
    conparid: str
        Column label for consistent parish ID, either 'conpar51-9' or 'conpar01-1'
    cen: str
        Column label for RSD id, takes format 'CEN_' followed by year, e.g. 'CEN_1901'.
    new_id: pandas.series.name
        Column label for new_id that combines conparid and cen; default 'new_id'

    Returns
    --------
    geopandas.GeoDataFrame
        A geopandas geodataframe containing the Parish/RSD Boundary data with a new id
        column created from the conparid and cen id variables.
    """

    print("Reading Registration Sub District (RSD) boundary data")

    tmp_file = gpd.read_file(rsd_gis_config.filepath, rows=1)
    list_of_all_cols = tmp_file.columns.values.tolist()
    cols_to_keep = [rsd_id_field, "geometry"]
    unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

    par_rsd_boundary = gpd.read_file(
        rsd_gis_config.filepath,
        ignore_fields=unwanted_cols,
        crs=rsd_gis_config.projection,
    )

    par_rsd_boundary = par_rsd_boundary.dissolve(by=rsd_id_field).reset_index()

    return par_rsd_boundary


def read_gis_to_icem(parish_icem_lkup_config, conparid):
    list_of_cols = [parish_icem_lkup_config.ukds_id_field, conparid]
    gis_to_icem = pd.read_excel(
        parish_icem_lkup_config.filepath,
        sheet_name=parish_icem_lkup_config.sheet,
        usecols=list_of_cols,
        na_values=parish_icem_lkup_config.na_values,
    )
    return gis_to_icem


def process_parish_boundary_data(
    parish_gis_config, ukds_lkuptbl, conparid, parish_icem_lkup_idfield,
):
    print("Reading Parish Boundary Data")
    tmp_file = gpd.read_file(parish_gis_config.filepath, rows=1)
    list_of_all_cols = tmp_file.columns.values.tolist()
    cols_to_keep = [parish_gis_config.id_field, "geometry"]
    unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

    par_boundary = gpd.read_file(
        parish_gis_config.filepath,
        ignore_fields=unwanted_cols,
        crs=parish_gis_config.projection,
    )
    # Buffer to ensure valid geometries
    par_boundary["geometry"] = par_boundary["geometry"].buffer(0)
    # Set precision of coordinates so overlay operations
    # between parish boundary and rsd boundary work properly
    par_boundary["geometry"] = pg.set_precision(par_boundary["geometry"].values.data, 0)

    par_boundary_conparid = pd.merge(
        left=par_boundary,
        right=ukds_lkuptbl,
        left_on=parish_gis_config.id_field,
        right_on=parish_icem_lkup_idfield,
        how="left",
    )
    par_boundary_conparid = par_boundary_conparid.dissolve(by=conparid).reset_index()
    par_boundary_conparid = par_boundary_conparid[[conparid, "geometry"]]

    return par_boundary_conparid


def join_parish_rsd_boundary(par_boundary, rsd_boundary, conparid, rsd_id_field):

    print("Joining Parish Boundary and RSD Boundary")
    # print(par_boundary['geometry'].is_valid.all())

    par_rsd_boundary = gpd.overlay(
        par_boundary, rsd_boundary, how="intersection", keep_geom_type=True
    )

    par_rsd_boundary = par_rsd_boundary.dropna(subset=[conparid, rsd_id_field]).copy()
    par_rsd_boundary["new_id"] = (
        par_rsd_boundary[conparid].astype(str)
        + "_"
        + par_rsd_boundary[rsd_id_field].astype(str)
    )
    par_rsd_boundary = par_rsd_boundary.dissolve(by="new_id").reset_index()

    geom_blocking_cols = [conparid, rsd_id_field]
    return par_rsd_boundary, geom_blocking_cols


def read_rsd_dictionary(rsd_dictionary_config):
    """
    Read the RSD Dictionary lookup file for the appropriate census year.

    Parameters
    ----------
    rsd_dictionary: str
        Path to rsd dictionary file.
    field_dict: dictionary
        Dictionary with field values.

    Returns
    -------
    pandas.DataFrame
        A pandas dataframe containing the RSD Dictionary lookup table.
    """

    rsd_variables = [
        rsd_dictionary_config.cen_parid_field,
        rsd_dictionary_config.rsd_id_field,
    ]

    rsd_dict = pd.read_csv(
        rsd_dictionary_config.filepath,
        sep="\t",
        quoting=3,
        usecols=rsd_variables,
        encoding=rsd_dictionary_config.encoding,
    )

    return rsd_dict
