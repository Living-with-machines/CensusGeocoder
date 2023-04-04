import pathlib

import numpy as np
import pandas as pd

from rapidfuzz import fuzz
from recordlinkage.base import BaseCompareFeature
from recordlinkage.utils import fillna as _fillna
from sklearn.feature_extraction.text import TfidfVectorizer


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

