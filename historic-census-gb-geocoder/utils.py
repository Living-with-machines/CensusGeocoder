import pandas as pd
from recordlinkage.base import BaseCompareFeature
import numpy as np
from recordlinkage.utils import fillna as _fillna


class rapidfuzzy_wratio_comparer(BaseCompareFeature):

    """Compute the (fuzzy partial_ratio) similarity between strings values.
    Parameters
    ----------
    left_on : str or int
        The name or position of the column in the left DataFrame.
    right_on : str or int
        The name or position of the column in the right DataFrame.
    method : str, default 'levenshtein'
        An approximate string comparison method. Options are ['jaro',
        'jarowinkler', 'levenshtein', 'damerau_levenshtein', 'qgram',
        'cosine', 'smith_waterman', 'lcs']. Default: 'levenshtein'
    threshold : float, tuple of floats
        A threshold value. All approximate string comparisons higher or
        equal than this threshold are 1. Otherwise 0.
    missing_value : numpy.dtype
        The value for a comparison with a missing value. Default 0.
    """

    name = "string"
    description = "Compare string attributes of record pairs."

    def __init__(self,
                 left_on,
                 right_on,
                 method='rapidfuzzy_wratio',
                 threshold=None,
                 missing_value=0.0,
                 label=None):
        super(rapidfuzzy_wratio_comparer, self).__init__(left_on, right_on, label=label)

        self.method = method
        self.threshold = threshold
        self.missing_value = missing_value

    def _compute_vectorized(self, s_left, s_right):

        if self.method == 'rapidfuzzy_wratio':
            str_sim_alg = rapidfuzzy_wratio
        else:
            raise ValueError("The algorithm '{}' is not known.".format(
                self.method))

        c = str_sim_alg(s_left, s_right)

        if self.threshold is not None:
            c = c.where((c < self.threshold) | (pd.isnull(c)), other=1.0)
            c = c.where((c >= self.threshold) | (pd.isnull(c)), other=0.0)

        c = _fillna(c, self.missing_value)

        return c



def rapidfuzzy_wratio(s1, s2):

    conc = pd.Series(list(zip(s1, s2)))

    from rapidfuzz import fuzz
    def fuzzy_apply(x):

        try:
            return fuzz.WRatio(x[0], x[1])
        except Exception as err:
            if pd.isnull(x[0]) or pd.isnull(x[1]):
                return np.nan
            else:
                raise err

    return conc.apply(fuzzy_apply)