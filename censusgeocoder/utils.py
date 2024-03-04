import pathlib

import numpy as np
import pandas as pd

from rapidfuzz import fuzz
from recordlinkage.base import BaseCompareFeature
from recordlinkage.utils import fillna as _fillna
from sklearn.feature_extraction.text import TfidfVectorizer

import geopandas as gpd
import json

from inspect import signature

from scipy import spatial

from unidecode import unidecode

def get_file_or_filelist(file_path, 
                         file_type: str = None):
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
            if file_type == file_p.suffix:
                file_list.append(str(file_p))
    print(file_list)
    return file_list


def read_shp_geom(file_path, **params):
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

    # tmp_file = gpd.read_file(filelist[0], rows=1)
    # list_of_all_cols = tmp_file.columns.values.tolist()

    # unwanted_cols = [col for col in list_of_all_cols if col not in cols_to_keep]

    gdf_list = []

    for file_ in filelist:
        if pathlib.Path(file_).suffix == ".shp":

            gpd.read_file(file_, 
                          **params, )


    
    target_gdf = pd.concat(gdf_list)
    

    return target_gdf


def read_csv_geom(file_path, **read_params, ):
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
                **read_params,
            )
            for csv_file in filelist
        ]
    )
    return target_df


def clean_address_data(df: pd.DataFrame, 
                       field_to_clean,
                       standardisation_file,
                       min_length,
                       suffix,
                       convert_non_ascii: bool = False,
                       ):
    """Generic clean address data
    Applies regex pattern replacements from file
    Strips leading and trailing spaces
    Converts to uppercase
    Drops NaN
    """
    
    field_to_clean_new = f"{field_to_clean}{suffix}"
    # print(df.info())
    # df = df.fillna(value=np.nan)
    # print(df.info())
    df[field_to_clean_new] = df[field_to_clean]

    if convert_non_ascii == True:
        df[field_to_clean_new] = df[field_to_clean_new].apply(lambda a: a if pd.isna(a) else unidecode(a))

    df[field_to_clean_new] = df[field_to_clean_new].str.upper()
    
    if standardisation_file != None:
        with open(standardisation_file) as f:
            street_standardisation = json.load(f)


        for patt, repla in street_standardisation.items():
            df[field_to_clean_new] = df[field_to_clean_new].replace(patt, 
                                                                                    repla, 
                                                                                    regex=True)


        df = df.fillna(value=np.nan)
    df[field_to_clean_new] = df[field_to_clean_new].str.strip()

    if min_length != None:

        df[field_to_clean_new] = np.where(df[field_to_clean_new].str.len() >= min_length,
                                            df[field_to_clean_new],
                                            np.nan
                                            )


    return df, field_to_clean_new


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


# def add_lkup(data, lkup_file, fields, lkup_params, base_link, lkup_link,):

#     # if base_uid == None:
#     #     base_uid = data.fields["uid"]

#     file_type = get_file_ext(lkup_file, )

#     if file_type in [".xlsx", ".xls", ]:


#         lkup = pd.read_excel(
#             lkup_file, usecols = fieldtolist(fields), **lkup_params, 
#                                     )
        
#     elif file_type in [".tsv", ".csv", ".txt", ]:

#         lkup = pd.read_csv(lkup_file, usecols = fieldtolist(fields), **lkup_params, )

#     else:
#         raise ValueError("Not a valid lkup format.")
    
#     data.data = pd.merge(left = data.data, right = lkup, left_on = base_link, right_on = lkup_link, how = "left", )

#     data.data = data.data.dropna(subset=fieldtolist(fields)) #check

#     return data.data


def add_lkup(data, lkup_file, read_library, read_params, left_on, right_on, how = "left", ):
    lkup_data = read_library(lkup_file, **read_params, )
    print(lkup_data.info())
    new_data = pd.merge(left = data, right = lkup_data, left_on = left_on, right_on = right_on, how = how, )
    return new_data

def fieldtolist(fields,
                ):
    
    field_list = []

    for k, v in fields.items():
        field_list.append(v)

    return field_list


def fieldtolist_comp(fields, subset, ):
    output_list = []
    for k, v in fields.items():
        for k1, v1 in v.items():
            if k1 == subset:
                col_val = v1
                output_list.append(col_val)
            else:
                "Do nothing"
    return output_list



def create_write_params(write_params, write_fields, ):
    if write_fields != None and write_params != None:
        write_params = write_params
        columns = []
        for k, v in write_fields.items():
            for k1, v1 in v.items():
                if k1 == "val":
                    col_val = v1
                    columns.append(col_val)
                # elif k1 == "dtype":
                #     dtype_dict[col_val] = v1
                # else:
                #     "Do nothing"
        write_params["columns"] = columns

    return write_params



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



def rapidfuzzy_get_src_start_pos(s1, s2):
    """Apply rapidfuzz partial_ratio_alignment to compare two pandas series"""

    conc = pd.Series(list(zip(s1, s2)))

    # from rapidfuzz import fuzz

    def fuzzy_apply(x):

        try:
            calc = fuzz.partial_ratio_alignment(x[0], x[1])
            return (calc.src_start)
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

def calc_dist(coords):
    np.seterr(all="ignore")
    mean_dist = spatial.distance.pdist(np.array(list(zip(coords.x, coords.y)))).mean()
    return mean_dist



def flatten(arg):
    if not isinstance(arg, list): # if not list
        yield arg
    else:
        for sub in arg:
            yield from flatten(sub)



def validate_pandas_read_csv_kwargs(file_path, csv_params):
    from pandas import read_csv
    sig = signature(read_csv)
    sig.bind(file_path, **csv_params)


def validate_pandas_excel_kwargs(file_path, excel_params):
    from pandas import read_excel
    sig = signature(read_excel)
    sig.bind(file_path, **excel_params)


def validate_pandas_to_csv_kwargs(file_path, csv_params):
    from pandas import DataFrame
    df = DataFrame()
    sig = signature(df.to_csv)
    sig.bind(file_path, **csv_params)


def validate_geopandas_read_file_kwargs(file_path, params):
    from geopandas import read_file
    sig = signature(read_file)
    sig.bind(file_path, **params)

def get_readlibrary(file_path, 
                    read_params, ):
    """docstring"""

    # file_list = get_file_or_filelist(file_path, 
    #                                  file_type, )

    ext = pathlib.Path(file_path).suffix

    if ext in [".txt", ".tsv", ".csv", ]:
        validate_pandas_read_csv_kwargs(file_path, read_params)
        # if geom != True:
        #     read_library = pd.read_csv
        # else:
        read_library = pd.read_csv

    elif ext in [".xlsx", ]:
        validate_pandas_excel_kwargs(file_path, read_params)
        read_library = pd.read_excel

    elif ext in [".geojson", ".shp", ]:
        # validate_geopandas_read_file_kwargs(file_path, read_params)
        read_library =  gpd.read_file

    return read_library


def validate_paths(filepath):
    """Checks the filepaths are valid. If not, returns an error"""

    new_path = pathlib.Path(filepath)
    if not new_path.exists():
        new_path.mkdir(parents=True)
        # msg = f"'{new_path}' is not a valid file path."
        # raise ValueError(msg)
    return new_path

def write_df_to_file(output_df, output_path_components, pandas_write_params):

    output_file_path = pathlib.Path(*output_path_components)

    if not output_file_path.parent.exists():
        output_file_path.parent.mkdir(parents=True)


    output_df.to_csv(output_file_path, **pandas_write_params)