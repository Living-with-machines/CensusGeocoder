import geopandas as gpd
import pandas as pd
import json
import pathlib


def set_geom_files(geom_config):
    """Accepts a directory or single filepath and creates a list of file(s)
    containing target geometry data.

    Parameters
    -------

    geom_config: Dataclass
        Dataclass containing parameters for target geometry data.

    Returns
    -------
    geom_files: list
        List containing file(s) of target geometry data.
    """

    geom_files = []
    p = pathlib.Path(geom_config.path_to_geom)
    if p.is_file():
        geom_files.append(str(p))
    else:
        for file_p in p.iterdir():
            if geom_config.filename_disamb in str(file_p):
                geom_files.append(str(file_p))

    return geom_files


def process_raw_geo_data(
    geom_name, boundary_data, geom_config, census_params, output_dir
):
    """Process target geometry data. Save processed geometry data to
    file. Returns dataframe with geometry data removed (to reduce size)
    and since geometry data is not needed for linking to census data. Also
    returns the new unique identifier for geometry data.

    Parameters
    -------

    geom_name: str
        Name of the target geometry data.
    boundary_data: geopandas.GeoDataFrame
        Historic boundary data used to assign target geometries to historic
        boundary units.
    geom_config: Dataclass
        Dataclass containing parameters for target geometry data.
    census_params: Dataclass
        Dataclass containing parameters for census year.
    output_dir: str
        Path to write processed geometry data.

    Returns
    -------
    target_df_processed_small: pandas.DataFrame
        Pandas dataframe containing target address data and assigned
        historic boundary ids.
    new_uid: str
        Name of unique identifier column created from target geometry name
        and census year.
    """
    print("*" * 100)
    print(f"Reading {geom_name} geometry data")
    cols_to_keep = geom_config.data_fields.list_cols()

    filelist = set_geom_files(geom_config)

    new_uid = str(geom_name) + "_" + str(census_params.year)

    if geom_config.file_type == "shp":
        target_gdf = read_shp(filelist, cols_to_keep, geom_config)

    elif geom_config.file_type == "csv":
        target_df = read_csv(filelist, cols_to_keep, geom_config)
        if geom_config.geometry_format == "coords":
            target_gdf = process_coords(target_df, geom_config)
        elif geom_config.geometry_format == "wkt":
            target_gdf = process_wkt(target_df, geom_config)

    target_gdf = (
        target_gdf.dropna().copy()
    )  # need to check the effect this is having by not using subset any more.

    if geom_config.geom_type == "line":
        target_gdf_processed = process_linstring(
            target_gdf, boundary_data, geom_config, new_uid
        )

    elif geom_config.geom_type == "point":
        target_gdf_processed = process_point(
            target_gdf, boundary_data, geom_config, new_uid
        )

    target_gdf_processed = parse_address(target_gdf_processed, geom_config)

    if target_gdf_processed.crs != geom_config.output_params.crs:
        target_gdf_processed = target_gdf_processed.to_crs(
            geom_config.output_params.crs
        )

    target_gdf_processed.to_file(
        f"{output_dir}/{geom_name}_{census_params.year}{geom_config.output_params.file_type}",
        driver=geom_config.output_params.driver,
        crs=geom_config.output_params.crs,
    )
    target_df_processed_small = pd.DataFrame(
        target_gdf_processed.drop(columns=[target_gdf_processed.geometry.name])
    )

    return target_df_processed_small, new_uid


def drop_outside_country(target_gdf, tmp_id):
    """Drop target geometries with no associated historic boundary data
    after join.

    Parameters
    ----------

    target_gdf: geopandas.GeoDataFrame
        Geopandas geodataframe containing target geometry data with associated historic
        boundary info.
    tmp_id: str
        Name of temporary id column.

    Returns
    -------
    target_gdf:  geopandas.GeoDataFrame
        Geopandas geodataframe containing subset of target geometry data only
        with associated historic boundary info.
    """

    target_gdf = target_gdf.dropna(subset=tmp_id).copy()

    return target_gdf


def process_linstring(line_string_gdf, boundary_data, geom_config, new_uid):
    """Overlays historic boundary data with target geometry linestrings to create
    new linestrings. For example, if a linestring crosses more than one boundary,
    the linestring is split into two. Returns a geopandas GeoDataFrame of these
    new geometries.

    Parameters
    ----------

    ling_string_gdf: geopandas.GeoDataFrame
        Geopandas geodataframe containing target geometry data in a linestring format.
    boundary_data: geopandas.GeoDataFrame
        Historic boundary data used to assign target geometries to historic
        boundary units.
    geom_config: Dataclass
        Dataclass containing parameters for target geometry data.
    new_uid: str
        Name of unique identifier column created in `process_raw_geo_data` function.
    

    Returns
    -------
    tmp4:  geopandas.GeoDataFrame
        Geopandas geodataframe containing processed linestring geometries.
    """
    tmp = line_string_gdf.dissolve(by=geom_config.data_fields.uid_field, as_index=False)
    print(tmp)
    tmp2 = gpd.overlay(tmp, boundary_data, how="identity", keep_geom_type=True)
    print(tmp2.info())
    tmp2 = drop_outside_country(tmp2, "tmp_id")

    tmp2[new_uid] = (
        tmp2[geom_config.data_fields.uid_field].astype(str)
        + "_"
        + tmp2["tmp_id"].astype(str)
    )

    tmp3 = tmp2.dissolve(by=new_uid)
    print(tmp3)
    tmp4 = tmp3.drop_duplicates(
        subset=[geom_config.data_fields.address_field, "tmp_id"], keep=False
    ).copy()
    return tmp4


def process_point(point_gdf, boundary_data, geom_config, new_uid):
    """Conducts spatial join between historic boundary data and
    target geometry points to assign each point to historic boundary.
    Returns a geopandas GeoDataFrame of these points with associated historic
    boundary info.

    Parameters
    ----------

    point_gdf: geopandas.GeoDataFrame
        Geopandas geodataframe containing target point geometry data.
    boundary_data: geopandas.GeoDataFrame
        Historic boundary data used to assign target geometries to historic
        boundary units.
    geom_config: Dataclass
        Dataclass containing parameters for target geometry data.
    new_uid: str
        Name of unique identifier column created in `process_raw_geo_data` function.
    

    Returns
    -------
    tmp3:  geopandas.GeoDataFrame
        Geopandas geodataframe containing processed point geometries.
    """
    tmp = gpd.sjoin(
        left_df=point_gdf, right_df=boundary_data, predicate="intersects", how="inner"
    ).drop(columns=["index_right"])

    tmp = drop_outside_country(tmp, "tmp_id")

    tmp[new_uid] = (
        tmp[geom_config.data_fields.uid_field].astype(str)
        + "_"
        + tmp["tmp_id"].astype(str)
    )
    tmp2 = tmp.drop_duplicates(subset=[new_uid], keep=False)
    tmp3 = tmp2.set_index(new_uid)
    return tmp3


def parse_address(target_gdf, geom_config):
    """Process address data in target geometry in preparation
    for comparison with I-CeM data. Converts addresses to uppercase.
    If a standardisation file has been specified, then regex replacements
    are made using that file.

    Parameters
    ----------

    target_gdf: geopandas.GeoDataFrame
        Geopandas geodataframe containing target geometry data.
    geom_config: Dataclass
        Dataclass containing parameters for target geometry data.

    Returns
    -------
    target_gdf:  geopandas.GeoDataFrame
        Geopandas geodataframe containing target geometry data with processed
        addresses.
    """
    target_gdf[geom_config.data_fields.address_field] = target_gdf[
        geom_config.data_fields.address_field
    ].str.upper()

    if geom_config.query_criteria != "":
        target_gdf = target_gdf.query(geom_config.query_criteria).copy()

    if geom_config.standardisation_file != "":
        with open(geom_config.standardisation_file) as f:
            street_standardisation = json.load(f)

        target_gdf[geom_config.data_fields.address_field] = target_gdf[
            geom_config.data_fields.address_field
        ].replace(street_standardisation, regex=True)

    target_gdf[geom_config.data_fields.address_field] = target_gdf[
        geom_config.data_fields.address_field
    ].str.strip()
    return target_gdf


def read_shp(filelist, cols_to_keep, geom_config):
    """Reads target geometry from a single shapefile or multiple
    shapefiles. Returns target geometry in geopandas GeoDataFrame.

    Parameters
    ----------

    filelist: list
        List of filepaths.
    cols_to_keep: list
        Columns from target geometry data to read.
    geom_config: Dataclass
        Dataclass containing parameters for target geometry data.

    Returns
    -------
    target_gdf:  geopandas.GeoDataFrame
        Geopandas geodataframe containing target geometry data.
    """
    tmp_file = gpd.read_file(filelist[0], rows=1)
    list_of_all_cols = tmp_file.columns.values.tolist()

    unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

    target_gdf = gpd.GeoDataFrame(
        pd.concat(
            [
                gpd.read_file(
                    target_shp,
                    ignore_fields=unwanted_cols,
                    crs=geom_config.projection,
                    rows=1000,  # create sample data and remove.
                )
                for target_shp in filelist
            ]
        ),
        crs=geom_config.projection,
    )
    return target_gdf


def read_csv(filelist, cols_to_keep, geom_config):
    """Reads target geometry from a single delimited file or multiple
    delimited files. Returns target geometry data in pandas DataFrame.

    Parameters
    ----------

    filelist: list
        List of filepaths.
    cols_to_keep: list
        Columns from target geometry data to read.
    geom_config: Dataclass
        Dataclass containing parameters for target geometry data.

    Returns
    -------
    target_df:  pandas.DataFrame
        Pandas dataframe containing target geometry data.
    """
    target_df = pd.concat(
        [
            pd.read_csv(
                csv_file,
                sep=geom_config.sep,
                encoding=geom_config.encoding,
                usecols=cols_to_keep,
                nrows=1000,  # create sample data and remove.
            )
            for csv_file in filelist
        ]
    )
    return target_df


def process_coords(target_df, geom_config):
    """Processes coordindates in a pandas dataframe. Returns
    a geopandas GeoDataFrame with geometry data and specified crs.

    Parameters
    ----------

    target_df:  pandas.DataFrame
        Pandas dataframe containing target geometry data.
    geom_config: Dataclass
        Dataclass containing parameters for target geometry data.

    Returns
    -------
    target_gdf:  geopandas.GeoDataFrame
        Geopandas geodataframe containing target geometry data.
    """
    target_gdf = gpd.GeoDataFrame(
        target_df,
        geometry=gpd.points_from_xy(
            target_df[geom_config.data_fields.long_field],
            target_df[geom_config.data_fields.lat_field],
        ),
        crs=geom_config.projection,
    ).drop(
        columns=[geom_config.data_fields.long_field, geom_config.data_fields.lat_field,]
    )
    return target_gdf


def process_wkt(target_df, geom_config):
    """Processes wkt strings in a pandas dataframe. Returns
    a geopandas GeoDataFrame with geometry data and specified crs.

    Parameters
    ----------

    target_df:  pandas.DataFrame
        Pandas dataframe containing target geometry data.
    geom_config: Dataclass
        Dataclass containing parameters for target geometry data.

    Returns
    -------
    target_gdf:  geopandas.GeoDataFrame
        Geopandas geodataframe containing target geometry data.
    """
    target_gdf = gpd.GeoDataFrame(
        target_df,
        geometry=gpd.GeoSeries.from_wkt(
            target_df[geom_config.data_fields.geometry_field]
        ),
        crs=geom_config.projection,
    )
    return target_gdf
