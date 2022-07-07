import geopandas as gpd
import pandas as pd
import json
import pathlib


def set_geom_files(geom_config):
    """Create list of file(s) containing target geometry data

    Returns
    ----------
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
    """"""
    print("*" * 100)
    print(f"Reading {geom_name} geometry data")
    cols_to_keep = geom_config.data_fields.list_cols()

    filelist = set_geom_files(geom_config)

    new_uid = str(geom_name) + "_" + str(census_params.year)

    if geom_config.file_type == "shp":
        target_gdf = read_shp(filelist, cols_to_keep, geom_config)
        # print(target_gdf)

    elif geom_config.file_type == "csv":
        target_df = read_csv(geom_config, cols_to_keep, filelist)
        if geom_config.geometry_format == "coords":
            target_gdf = process_coords(target_df, geom_config)
        elif geom_config.geometry_format == "wkt":
            target_gdf = process_wkt(target_df, geom_config)

    target_gdf = (
        target_gdf.dropna().copy()
    )  # need to check the effect this is having by not using subset any more.
    # print(target_gdf)

    if geom_config.geom_type == "line":
        target_gdf_processed = process_linstring(
            target_gdf, boundary_data, geom_config, new_uid
        )

    elif geom_config.geom_type == "point":
        target_gdf_processed = process_point(
            target_gdf, boundary_data, geom_config, new_uid
        )
        # print(target_gdf_processed.info())

    target_gdf_processed = parse_address(target_gdf_processed, geom_config)

    print(target_gdf_processed.info())

    target_gdf_processed.to_csv(
        f"{output_dir}/{geom_name}_{census_params.year}.tsv", sep="\t"
    )
    target_gdf_processed_small = target_gdf_processed.drop(
        columns=[target_gdf_processed.geometry.name]
    )
    print(target_gdf_processed_small.info())

    return target_gdf_processed_small, new_uid


def drop_outside_country(target_gdf, new_id):
    """Drop roads outside country (i.e. with
    no associated parish info from the union"""

    tmp = target_gdf.dropna(subset=new_id).copy()
    return tmp


def process_linstring(line_string_gdf, boundary_data, geom_config, new_uid):
    tmp = line_string_gdf.dissolve(by=geom_config.data_fields.uid_field, as_index=False)
    print(tmp)
    tmp2 = gpd.overlay(tmp, boundary_data, how="identity", keep_geom_type=True)
    print(tmp2.info())
    tmp2 = drop_outside_country(tmp2, "new_id")

    tmp2[new_uid] = (
        tmp2[geom_config.data_fields.uid_field].astype(str)
        + "_"
        + tmp2["new_id"].astype(str)
    )

    tmp3 = tmp2.dissolve(by=new_uid)
    print(tmp3)
    tmp4 = tmp3.drop_duplicates(
        subset=[geom_config.data_fields.address_field, "new_id"], keep=False
    ).copy()
    return tmp4


def process_point(point_gdf, boundary_data, geom_config, new_uid):
    tmp = gpd.sjoin(
        left_df=point_gdf, right_df=boundary_data, predicate="intersects", how="inner"
    ).drop(columns=["index_right"])

    tmp = drop_outside_country(tmp, "new_id")

    tmp[new_uid] = (
        tmp[geom_config.data_fields.uid_field].astype(str)
        + "_"
        + tmp["new_id"].astype(str)
    )
    tmp2 = tmp.drop_duplicates(subset=[new_uid], keep=False)
    tmp3 = tmp2.set_index(new_uid)
    return tmp3


def parse_address(target_gdf, geom_config):

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
                    rows=1000,
                )
                for target_shp in filelist
            ]
        ),
        crs=geom_config.projection,
    )
    return target_gdf


def read_csv(geom_config, cols_to_keep, filelist):
    target_df = pd.concat(
        [
            pd.read_csv(
                csv_file,
                sep=geom_config.sep,
                encoding=geom_config.encoding,
                usecols=cols_to_keep,
                nrows=1000,
            )
            for csv_file in filelist
        ]
    )
    return target_df


def process_coords(target_df, geom_config):
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
    target_gdf = gpd.GeoDataFrame(
        target_df,
        geometry=gpd.GeoSeries.from_wkt(target_df["wkt"]),
        crs=geom_config.projection,
    )
    return target_gdf
