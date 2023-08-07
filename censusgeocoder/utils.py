import pathlib

import numpy as np
import pandas as pd

from rapidfuzz import fuzz
from recordlinkage.base import BaseCompareFeature
from recordlinkage.utils import fillna as _fillna
from sklearn.feature_extraction.text import TfidfVectorizer

import geopandas as gpd
import json

def get_file_or_filelist(file_path):
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

    file_list = []
    p = pathlib.Path(file_path)
    if p.is_file():
        file_list.append(str(p))
    else:
        for file_p in p.iterdir():
            # if geom_config.filename_disamb in str(file_p):
            file_list.append(str(file_p))

    return file_list


def read_shp_geom(file_path, cols_to_keep, geom_config):
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

    filelist = get_file_or_filelist(file_path, )

    tmp_file = gpd.read_file(filelist[0], rows=1)
    list_of_all_cols = tmp_file.columns.values.tolist()

    unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

    target_gdf = gpd.GeoDataFrame(
        pd.concat(
            [
                gpd.read_file(
                    target_shp, ignore_fields=unwanted_cols, crs=geom_config["projection"],
                )
                for target_shp in filelist
            ]
        ),
        crs=geom_config["projection"],
    )
    return target_gdf


def read_csv_geom(file_path, cols_to_keep, geom_config):
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

    filelist = get_file_or_filelist(file_path, )

    target_df = pd.concat(
        [
            pd.read_csv(
                csv_file,
                sep=geom_config["sep"],
                encoding=geom_config["encoding"],
                usecols=cols_to_keep,
            )
            for csv_file in filelist
        ]
    )
    return target_df


def clean_address_data(df, field_to_clean, standardisation_file):
    """Generic clean address data
    Applies regex pattern replacements from file
    Strips leading and trailing spaces
    Converts to uppercase
    Drops NaN
    """


        # if geom_config.query_criteria != "":
        # target_gdf = target_gdf.query(
        #     geom_config.query_criteria, engine="python"
        # ).copy()
    if standardisation_file is not None:
        with open(standardisation_file) as f:
            street_standardisation = json.load(f)
        df[field_to_clean] = df[field_to_clean].replace(
            street_standardisation, regex=True
        )
        df = df.fillna(value=np.nan)
        df[field_to_clean] = df[field_to_clean].str.strip()
        df[field_to_clean] = df[field_to_clean].str.upper()
        df = df.dropna(subset=field_to_clean).copy()

    return df


def process_coords(target_df, long_field, lat_field, projection, ):
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
            target_df[long_field],
            target_df[lat_field],
        ),
        crs=projection,
    ).drop(
        columns=[long_field, lat_field,]
    )
    return target_gdf


# def process_wkt(target_df, projection, ):
#     """Processes wkt strings in a pandas dataframe. Returns
#     a geopandas GeoDataFrame with geometry data and specified crs.

#     Parameters
#     ----------

#     target_df:  pandas.DataFrame
#         Pandas dataframe containing target geometry data.
        
#     geom_config: Dataclass
#         Dataclass containing parameters for target geometry data.

#     Returns
#     -------
#     target_gdf:  geopandas.GeoDataFrame
#         Geopandas geodataframe containing target geometry data.
#     """
#     target_gdf = gpd.GeoDataFrame(
#         target_df,
#         geometry=gpd.GeoSeries.from_wkt(
#             target_df[geom_config.data_fields.geometry_field]
#         ),
#         crs=projection,
#     )
#     return target_gdf




def get_file_ext(file_path, ):
    file_ext = pathlib.Path(file_path).suffix
    return file_ext


def add_lkup(data, lkup_file, fields, lkup_params, ):

    file_type = get_file_ext(lkup_file, )

    if file_type in [".xlsx", ".xls", ]:


        lkup = pd.read_excel(
            lkup_file, usecols = fieldtolist(fields), **lkup_params, 
                                    )
        
    elif file_type in [".tsv", ".csv", ".txt", ]:

        lkup = pd.read_csv(lkup_file, usecols = fieldtolist(fields), **lkup_params, )

    else:
        raise ValueError("Not a valid lkup format.")
    
    data.data = pd.merge(left = data.data, right = lkup, left_on = data.fields["uid"], right_on = fields["geom_uid"], how = "left", )

    return data.data

def fieldtolist(fields,
                ):
    
    field_list = []

    for k, v in fields.items():
        field_list.append(v)

    return field_list





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

    # from rapidfuzz import fuzz

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

    # from rapidfuzz import fuzz

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

    # from rapidfuzz import fuzz

    def fuzzy_apply(x):

        try:
            calc = fuzz.partial_ratio_alignment(x[0], x[1])
            alignment_dist = calc.dest_end - calc.dest_start
            # divide by 100 to make comparable with levenshtein etc
            return (alignment_dist)
        except Exception as err:
            if pd.isnull(x[0]) or pd.isnull(x[1]):
                return np.nan
            else:
                raise err

    return conc.apply(fuzzy_apply)


def compute_tfidf(census, col_to_compute):
    """Compute TF-IDF scores for a column in the census. These scores are used to
    weight the string comparisons so that common adddresses have to reach a higher
    matching threshold to be classed as a true match.

    Parameters
    ----------
    census: pandas.DataFrame
        A pandas dataframe containing census data.

    census_fields: Dataclass
        Dataclass containing census columns.

    Returns
    -------
    pandas.DataFrame
        A pandas dataframe containing census data with two additional columns with
        tf-idf and tf-idf weighting.
    """
    try:
        tfidf_vectorizer = TfidfVectorizer(
            norm="l2", use_idf=True, lowercase=False, dtype=np.float32
        )  # default is norm l2
        tfidf_sparse = tfidf_vectorizer.fit_transform(census[col_to_compute])
        # tfidf_array = tfidf_sparse.toarray()
        # tfidf_array_sums = np.sum(tfidf_array, axis=1).tolist()
        np.seterr(invalid="ignore")
        tfidf_mean = np.sum(tfidf_sparse, axis=1) / np.sum(tfidf_sparse != 0, axis=1)
        census["tfidf"] = tfidf_mean
        # census["tfidf_w"] = census["tfidf"] / census[census_fields.address].str.len()
    except ValueError:
        print("Likely error with tf-idf not having any strings to compare")
    return census[[col_to_compute, "tfidf"]]


# def set_path(*dirs):
#     """Takes input strings; creates a path if path doesn't exist;
#     returns a path"""

#     new_path = pathlib.Path(*dirs)
#     pathlib.Path(new_path).mkdir(parents=True, exist_ok=True)

#     return new_path


# def set_filename(output_dir, file_extension, *fname_components):
#     fname_components_list = [
#         str(fname_components) for fname_components in fname_components
#     ]
#     filename = (
#         str(output_dir) / "_".join(fname_components_list)
#         + str(".")
#         + str(file_extension)
#     )
#     return filename


# new_path = pathlib.Path("data", "output", "1911")
# pathlib.Path(new_path).mkdir(parents=True, exist_ok=True)


def set_filepath(*filepath_components):
    filepath = pathlib.Path().joinpath(*filepath_components)
    pathlib.Path(filepath).mkdir(parents=True, exist_ok=True)

    return filepath


# output_loc = set_filepath("data/output", "1911", "EW", "1911_EW_boundary.geojson",)

# print(output_loc)

# .mkdir(
#     parents=True, exist_ok=True
# )
# print(testing)

# output_dir = set_path("data", "output", "1911", "EW")

# print(output_dir)
# trial = set_filename(output_dir, "geojson", "1911", "EW", "boundary")
# print(trial)


def set_gis_file_extension(driver):
    # driver = params.driver
    if driver == "GeoJSON":
        file_extension = ".geojson"
    else:
        pass
    return file_extension


def write_gis_file(gdf, filepath, **params):
    print(params)
    # print(params[""])
    # print(**params)
    # file_extension = set_gis_file_extension(params["driver"])
    gdf.to_file(filepath, **params)

