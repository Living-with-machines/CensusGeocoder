import pathlib

import numpy as np
import pandas as pd

from rapidfuzz import fuzz
from recordlinkage.base import BaseCompareFeature
from recordlinkage.utils import fillna as _fillna

import geopandas as gpd
import json

from inspect import signature

from scipy import spatial

from unidecode import unidecode


def clean_address_data(
    df: pd.DataFrame,
    field_to_clean: str,
    standardisation_file: str,
    min_length: int,
    suffix: str,
    convert_non_ascii: bool = False,
) -> tuple[pd.DataFrame, str]:
    """Cleans `field_to_clean` returns `pd.DataFrame` with added `pd.Series` containing cleaned data, and name of cleaned field.
    Applies regex pattern replacements from file
    Strips leading and trailing spaces
    Converts to uppercase

    Parameters
    ----------

    df: `pd.DataFrame`
        `pd.DataFrame` of data including a field to be cleaned

    field_to_clean: str
        Name of `pd.Series` in `df` that will be cleaned

    min_length: int
        Minimum number of characters that `field_to_clean` must contain otherwise class as NaN

    suffix: str
        Suffix to add to `field_to_clean` to distinguish cleaned field from original field in dataframe.

    convert_non_ascii: bool
        Whether to convert non ascii characters in `field_to_clean` or not. See Documentation re. non ascii characters in GB1900.


    Returns
    -------

    df: `pd.DataFrame`
        `pd.DataFrame` containing original data with added `pd.Series` containing cleaned data

    field_to_clean_new: str
        Name of `pd.Series` in `df` that contains cleaned data.

    """

    field_to_clean_new = f"{field_to_clean}{suffix}"

    df[field_to_clean_new] = df[field_to_clean]

    if convert_non_ascii is True:
        df[field_to_clean_new] = df[field_to_clean_new].apply(
            lambda a: a if pd.isna(a) else unidecode(a)
        )

    df[field_to_clean_new] = df[field_to_clean_new].str.upper()

    if standardisation_file is not None:
        with open(standardisation_file) as f:
            street_standardisation = json.load(f)

        for patt, repla in street_standardisation.items():
            df[field_to_clean_new] = df[field_to_clean_new].replace(
                patt, repla, regex=True
            )

        df = df.fillna(value=np.nan)
    df[field_to_clean_new] = df[field_to_clean_new].str.strip()

    if min_length is not None:

        df[field_to_clean_new] = np.where(
            df[field_to_clean_new].str.len() >= min_length,
            df[field_to_clean_new],
            np.nan,
        )

    return (df, field_to_clean_new)


def process_coords(
    target_df: pd.DataFrame,
    long_field: str,
    lat_field: str,
    projection: str,
):
    """Processes coordindates in a `pd.DataFrame` reading them into a geometry field in a `gpd.GeoDatFrame`.
    Returns a gpd.GeoDataFrame with geometry data and specified crs.

    Parameters
    ----------

    target_df:  `pd.DataFrame`
        `pd.DataFrame` containing coordinates but not read into geometry field of a `gpd.GeoDataFrame`.

    long_field: str
        Name of `pd.Series` containing longitude values.

    lat_field: str
        Name of `pd.Series` containing latitude values.

    projection: str
        Intended CRS projection.

    Returns
    -------
    target_gdf:  `gpd.GeoDataFrame`
        `gpd.GeoDataFrame` containing original data (minus the original lat and long fields) with geometry column in WKT.

    """
    target_gdf = gpd.GeoDataFrame(
        target_df,
        geometry=gpd.points_from_xy(
            target_df[long_field],
            target_df[lat_field],
        ),
        crs=projection,
    ).drop(
        columns=[
            long_field,
            lat_field,
        ]
    )
    return target_gdf


class rapidfuzzy_wratio_comparer(BaseCompareFeature):
    """Provides funtionality for recordlinkage BaseCompareFeature to use
    algorithm from rapidfuzz rather than fuzzywuzzy.
    """

    def __init__(
        self,
        left_on,
        right_on,
        method="rapidfuzzy_wratio",
        threshold=None,
        missing_value=0.0,
        label=None,
    ):
        super(rapidfuzzy_wratio_comparer, self).__init__(left_on, right_on, label=label)

        self.method = method
        self.threshold = threshold
        self.missing_value = missing_value

    def _compute_vectorized(self, s_left, s_right):

        if self.method == "rapidfuzzy_wratio":
            str_sim_alg = rapidfuzzy_wratio
        elif self.method == "rapidfuzzy_partial_ratio":
            str_sim_alg = rapidfuzzy_partialratio
        elif self.method == "rapidfuzzy_partial_ratio_alignment":
            str_sim_alg = rapidfuzzy_partialratioalignment
        elif self.method == "rapidfuzzy_get_src_start_pos":
            str_sim_alg = rapidfuzzy_get_src_start_pos
        else:
            raise ValueError("The algorithm '{}' is not known.".format(self.method))

        c = str_sim_alg(s_left, s_right)

        if self.threshold is not None:
            c = c.where((c < self.threshold) | (pd.isnull(c)), other=1.0)
            c = c.where((c >= self.threshold) | (pd.isnull(c)), other=0.0)

        c = _fillna(c, self.missing_value)

        return c


def rapidfuzzy_wratio(s1, s2):
    """Apply rapidfuzz wratio to compare two pandas series"""

    conc = pd.Series(list(zip(s1, s2)))

    def fuzzy_apply(x):

        try:
            # divide by 100 to make comparable with levenshtein etc
            return (fuzz.WRatio(x[0], x[1])) / 100
        except Exception as err:
            if pd.isnull(x[0]) or pd.isnull(x[1]):
                return np.nan
            else:
                raise err

    return conc.apply(fuzzy_apply)


def rapidfuzzy_partialratio(s1, s2):
    """Apply rapidfuzz partial_ratio to compare two pandas series"""

    conc = pd.Series(list(zip(s1, s2)))

    def fuzzy_apply(x):

        try:
            # divide by 100 to make comparable with levenshtein etc
            return (fuzz.partial_ratio(x[0], x[1])) / 100
        except Exception as err:
            if pd.isnull(x[0]) or pd.isnull(x[1]):
                return np.nan
            else:
                raise err

    return conc.apply(fuzzy_apply)


def rapidfuzzy_partialratioalignment(s1, s2):
    """Apply rapidfuzz partial_ratio_alignment to compare two pandas series"""

    conc = pd.Series(list(zip(s1, s2)))

    def fuzzy_apply(x):

        try:
            calc = fuzz.partial_ratio_alignment(x[0], x[1])
            alignment_dist = calc.dest_end - calc.dest_start
            # divide by 100 to make comparable with levenshtein etc
            return alignment_dist
        except Exception as err:
            if pd.isnull(x[0]) or pd.isnull(x[1]):
                return np.nan
            else:
                raise err

    return conc.apply(fuzzy_apply)


def rapidfuzzy_get_src_start_pos(s1, s2):
    """Apply rapidfuzz partial_ratio_alignment to compare two pandas series"""

    conc = pd.Series(list(zip(s1, s2)))

    def fuzzy_apply(x):

        try:
            calc = fuzz.partial_ratio_alignment(x[0], x[1])
            return calc.src_start
        except Exception as err:
            if pd.isnull(x[0]) or pd.isnull(x[1]):
                return np.nan
            else:
                raise err

    return conc.apply(fuzzy_apply)


def calc_dist(coords: gpd.GeoSeries):
    """Calculate distance between coordinates. Returns distance.

    Parameters
    ----------

    coords: `gpd.GeoSeries`
        `gpd.GeoSeries` containing geometry data

    Returns
    -------

    mean_dist: int
        Mean distance between 2 or more points in `coords`.

    """

    np.seterr(all="ignore")
    mean_dist = spatial.distance.pdist(np.array(list(zip(coords.x, coords.y)))).mean()

    return mean_dist


def flatten(arg: str | int | list):
    """Flatten list-like objects; if not list just yield `arg`."""
    if not isinstance(arg, list):
        yield arg
    else:
        for sub in arg:
            yield from flatten(sub)


def validate_pandas_read_csv_kwargs(file_path, csv_params):
    """Validate keyword arguments for `pd.read_csv()`

    Parameters
    ----------

    file_path: str
        Path to csv-like file.

    csv_params: dict
        Dictionary of keyword arguments to pass to `pd.read_csv()`.

    """

    sig = signature(pd.read_csv)
    sig.bind(file_path, **csv_params)


def validate_pandas_excel_kwargs(file_path, excel_params):
    """Validate keyword arguments for `pd.read_excel()`

    Parameters
    ----------

    file_path: str
        Path to csv-like file.

    excel_params: dict
        Dictionary of keyword arguments to pass to `pd.read_excel()`.

    """

    sig = signature(pd.read_excel)
    sig.bind(file_path, **excel_params)


def validate_pandas_to_csv_kwargs(file_path, csv_params):
    """Validate keyword arguments for pandas `to_csv()`

    Parameters
    ----------

    file_path: str
        Path to csv-like file.

    csv_params: dict
        Dictionary of keyword arguments to pass to pandas `to_csv()`.

    """

    df = pd.DataFrame()
    sig = signature(df.to_csv)
    sig.bind(file_path, **csv_params)


def validate_geopandas_read_file_kwargs(file_path, params):
    """Validate keyword arguments for `gpd.read_file()`

    Parameters
    ----------

    file_path: str
        Path to geometry file, e.g. ShapeFile

    params: dict
        Dictionary of keyword arguments to pass to `gpd.read_file()`.

    """

    sig = signature(gpd.read_file)
    sig.bind(file_path, **params)


def get_readlibrary(
    file_path,
    read_params,
) -> pd.read_csv | pd.read_excel | gpd.read_file:
    """Get the correct library to read a file

    Parameters
    ----------

    file_path: str
        Path of file to read

    read_params: dict
        Dictionary of keyword arguments to pass to read library

    Returns
    -------

    read_library: `pd.read_csv` | `pd.read_excel` | `gpd.read_file`
        Appropriate read library to read file at `file_path`

    """

    ext = pathlib.Path(file_path).suffix

    if ext in [
        ".txt",
        ".tsv",
        ".csv",
    ]:
        validate_pandas_read_csv_kwargs(file_path, read_params)

        read_library = pd.read_csv

    elif ext in [
        ".xlsx",
    ]:
        validate_pandas_excel_kwargs(file_path, read_params)
        read_library = pd.read_excel

    elif ext in [
        ".geojson",
        ".shp",
    ]:

        read_library = gpd.read_file

    return read_library


def read_file(
    file_path,
    read_params,
) -> pd.DataFrame | gpd.GeoDataFrame:
    """Reads file at `file_path`, returns data in `pd.DataFrame` or `gpd.DataFrame`

    Parameters
    ----------

    file_path: str
        Path to file to read

    read_params: dict
        Dictionary of keyword arguments for reading file.


    Returns
    -------

    data: `pd.DataFrame` | `gpd.GeoDataFrame`
        `pd.DataFrame` or `gpd.GeoDataFrame` containing data read from `file_path`.

    """

    read_library = get_readlibrary(
        file_path,
        read_params,
    )

    data = read_library(file_path, **read_params)

    return data


def validate_paths(filepath):
    """Checks the filepaths are valid. If not, returns an error"""

    new_path = pathlib.Path(filepath)
    if not new_path.exists():
        new_path.mkdir(parents=True)
        # msg = f"'{new_path}' is not a valid file path."
        # raise ValueError(msg)
    return new_path


def write_df_to_file(
    output_df: pd.DataFrame,
    output_path_components: list,
    pandas_write_params: dict,
):
    """Writes dataframe (e.g. `pd.DataFrame` or `gpd.GeoDataFrame`) to file.

    Parameters
    ----------

    output_df: `pd.DataFrame` or `gpd.GeoDataFrame`
        dataframe containing data to write to file.

    output_path_components: list
        List of path components

    pandas_write_params: dict
        Dictionary of keyword arguments passed to `pd.to_csv`.

    """

    output_file_path = pathlib.Path(*output_path_components)

    if not output_file_path.parent.exists():
        output_file_path.parent.mkdir(parents=True)

    output_df.to_csv(output_file_path, **pandas_write_params)


def add_lkup(
    data: pd.DataFrame | gpd.GeoDataFrame,
    lkup_file: str,
    lkup_params: dict,
    left_on: str,
    right_on: str,
    how: str = "left",
    lkup_val: str = "integer",
    fields_to_drop: str | list = None,
) -> pd.DataFrame | gpd.GeoDataFrame:
    """Adds lookup values from one dataframe to another dataframe. Returns original dataframe with lookup values added.

    Parameters
    ----------

    data: `pd.DataFrame` | `gpd.GeoDataFrame`
        `pd.DataFrame` or `gpd.GeoDataFrame` containing data to add lookup to.

    lkup_file: str
        File path of lookup data

    lkup_params: dict
        Dictonary of keyword arguments for reading `lkup_file`.

    left_on: str
        Name of `pd.Series` in `data` to join on.

    right_on: str
        Name of `pd.Series` in `lkup_data` to join on.

    how: str, optional
        How to perform join between `data` and lookup data.

    fields_to_drop: str | list | None, optional
        Specify name of field(s) to drop from dataframe after joining lookup data to `data`.

    Returns
    -------

    new_data: `pd.DataFrame` | `gpd.GeoDataFrame`
        `pd.DataFrame` or `gpd.GeoDataFrame` containing original `data` with added lookup values.

    """
    read_library = get_readlibrary(
        lkup_file,
        lkup_params,
    )

    lkup_data = read_library(lkup_file, **lkup_params)

    new_data = pd.merge(
        left=data,
        right=lkup_data,
        left_on=left_on,
        right_on=right_on,
        how=how,
    )

    lkup_cols_added = [col for col in lkup_data.columns if col != right_on]

    new_data = new_data.dropna(subset=lkup_cols_added)

    if lkup_val in ["integer", "float"]:
        for col in lkup_cols_added:
            new_data[col] = pd.to_numeric(new_data[col], downcast=lkup_val)

    if fields_to_drop is not None:
        new_data = new_data.drop(columns=fields_to_drop)

    return new_data
