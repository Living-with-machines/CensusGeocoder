import geopandas as gpd
import pandas as pd
import pygeos as pg


def process_rsd_boundary_data(rsd_id_field, rsd_gis_config):
    """
    Reads combined Registration Sub District (RSD) boundary data. Generates
    correct boundaries for census year by dissolving on specified rsd_id_field.

    Parameters
    ----------
    rsd_id_field : str
        Name of rsd id field for census year, e.g. 'CEN_1851'.
    rsd_gis_config: Dataclass
        Dataclass containing parameters for reading RSD GIS Boundary data
        for census year.

    Returns
    --------
    rsd_boundary: geopandas.GeoDataFrame
        A geopandas geodataframe containing the RSD Boundary data for census year.
    """

    # Read one line of the shapefile to create list of 'unwanted columns'
    tmp_file = gpd.read_file(rsd_gis_config.filepath, rows=1)
    list_of_all_cols = tmp_file.columns.values.tolist()
    cols_to_keep = [rsd_id_field, tmp_file.geometry.name]
    unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

    rsd_boundary = gpd.read_file(
        rsd_gis_config.filepath,
        ignore_fields=unwanted_cols,
        crs=rsd_gis_config.projection,
    )

    rsd_boundary = rsd_boundary.dissolve(by=rsd_id_field).reset_index()

    print("Processed Registration Sub District (RSD) boundary data")

    return rsd_boundary


def read_gis_to_icem(parish_icem_lkup_config, conparid):
    """
    Reads lookup table linking England and Wales parish boundary data to
    I-CeM.

    Parameters
    ----------
    parish_icem_lkup_config : Dataclass
        Dataclass containing parameters for reading lookup table.
    conparid: str
        Consistent parish identifier for census year, e.g. 'conparid_51-91' for 1851
        to 1891.

    Returns
    --------
    gis_to_icem: pandas.DataFrame
        A Pandas DataFrame containing the lookup table.
    """
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
    """
    Reads England and Wales parish boundary data. Merges parish boundary
    data with lookup table to assign each boundary a 'parid'. Then dissolves
    boundaries on the consistent parish identifier for census year. Returns
    a geopandas.GeoDataFrame containing parish boundary data for census year
    linkable to I-CeM.

    Parameters
    ----------
    parish_gis_config : Dataclass
        Dataclass containing parameters for reading Parish GIS Boundary data.
    ukds_lkuptbl: pandas.DataFrame
        Pandas DataFrame containing lookup table
    conparid: str
        Name of consistent parish identifier for census year
    parish_icem_lkup_idfield: str
        Unique id field that links lookup table to parish boundary data.


    Returns
    --------
    par_boundary_conparid: geopandas.GeoDataFrame
        A geopandas geodataframe containing parish boundary data for census year
        dissolved using consistent parish id.
        
    """

    print("Reading Parish Boundary Data")
    tmp_file = gpd.read_file(parish_gis_config.filepath, rows=1)
    list_of_all_cols = tmp_file.columns.values.tolist()
    cols_to_keep = [parish_gis_config.id_field, tmp_file.geometry.name]
    unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

    par_boundary = gpd.read_file(
        parish_gis_config.filepath,
        ignore_fields=unwanted_cols,
        crs=parish_gis_config.projection,
    )
    # Buffer to ensure valid geometries
    par_boundary.geometry = par_boundary.geometry.buffer(0)
    # Set precision of coordinates so overlay operations
    # between parish boundary and rsd boundary work properly
    par_boundary.geometry = pg.set_precision(par_boundary.geometry.values.data, 0)

    par_boundary_conparid = pd.merge(
        left=par_boundary,
        right=ukds_lkuptbl,
        left_on=parish_gis_config.id_field,
        right_on=parish_icem_lkup_idfield,
        how="left",
    )
    par_boundary_conparid = par_boundary_conparid.dissolve(by=conparid).reset_index()
    par_boundary_conparid = par_boundary_conparid[
        [conparid, par_boundary_conparid.geometry.name]
    ]

    return par_boundary_conparid


def join_parish_rsd_boundary(par_boundary, rsd_boundary, conparid, rsd_id_field):
    """
    Merges parish boundary data with rsd boundary data to create new geometries -
    some rsds are larger than consistent parish boundaries and vice versa. When rsd
    is larger than a consistent parish boundary, the rsd will be split into smaller
    units according to the consistent parish boundaries. Ditto for consistent parish
    boundaries that are larger than rsds.

    Dissolves on a temporary unique id produced by combining consistent parish
    identifier and rsd id.

    Parameters
    ----------
    par_boundary : geopandas.GeoDataFrame
        A geopandas geodataframe containing parish boundary data for census year.
    rsd_boundary : geopandas.GeoDataFrame
        A geopandas geodataframe containing rsd boundary data for census year.
    conparid: str
        Name of consistent parish identifier for census year
    rsd_id_field : str
        Name of rsd id field for census year, e.g. 'CEN_1851'.


    Returns
    --------
    par_rsd_boundary: geopandas.GeoDataFrame
        A geopandas geodataframe containing parish/rsd boundary data for census year.
    geom_blocking_cols: list
        List of columns for geo-blocking when running string comparisons.
        
    """

    print("Joining Parish Boundary and RSD Boundary")
    # print(par_boundary['geometry'].is_valid.all())

    par_rsd_boundary = gpd.overlay(
        par_boundary, rsd_boundary, how="intersection", keep_geom_type=True
    )

    par_rsd_boundary = par_rsd_boundary.dropna(subset=[conparid, rsd_id_field]).copy()
    par_rsd_boundary["tmp_id"] = (
        par_rsd_boundary[conparid].astype(str)
        + "_"
        + par_rsd_boundary[rsd_id_field].astype(str)
    )
    par_rsd_boundary = par_rsd_boundary.dissolve(by="tmp_id").reset_index()

    geom_blocking_cols = [conparid, rsd_id_field]
    return par_rsd_boundary, geom_blocking_cols


def read_rsd_dictionary(rsd_dictionary_config):
    """
    Read the RSD Dictionary lookup file for census year.

    Parameters
    ----------
    rsd_dictionary_config: Dataclass
        Dataclass containing parameters for reading rsd dictionary.

    Returns
    -------
    pandas.DataFrame
        A pandas dataframe containing the RSD Dictionary lookup table for census year.
    """

    rsd_variables = [
        rsd_dictionary_config.cen_parid_field,
        rsd_dictionary_config.rsd_id_field,
    ]

    rsd_dict = pd.read_csv(
        rsd_dictionary_config.filepath,
        sep=rsd_dictionary_config.sep,
        quoting=rsd_dictionary_config.quoting,
        usecols=rsd_variables,
        encoding=rsd_dictionary_config.encoding,
    )

    return rsd_dict
