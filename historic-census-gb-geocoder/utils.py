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


def compute_tfidf(census, census_fields):
    """Compute TF-IDF scores for census addresses. These scores are used to
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
        tfidf_sparse = tfidf_vectorizer.fit_transform(census[census_fields.address])
        # tfidf_array = tfidf_sparse.toarray()
        # tfidf_array_sums = np.sum(tfidf_array, axis=1).tolist()
        np.seterr(invalid="ignore")
        tfidf_mean = np.sum(tfidf_sparse, axis=1) / np.sum(tfidf_sparse != 0, axis=1)
        census["tfidf"] = tfidf_mean
        # census["tfidf_w"] = census["tfidf"] / census[census_fields.address].str.len()
    except ValueError:
        print("Likely error with tf-idf not having any strings to compare")
    return census[[census_fields.address, "tfidf"]]


def make_path(*dirs):
    """Takes input strings; creates a path if path doesn't exist;
    returns a path"""

    new_path = pathlib.Path(*dirs)
    pathlib.Path(new_path).mkdir(parents=True, exist_ok=True)

    return new_path
