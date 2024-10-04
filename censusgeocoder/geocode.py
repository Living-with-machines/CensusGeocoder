import pandas as pd
import recordlinkage
import utils


class GeoCode:
    """A class to geocode census data.

    Attributes
    ----------

    census_data: pd.DataFrame
        DataFrame containing census data.

    census_geocode_field: str
        Name of pd.Series in `census_data` containing text (e.g. Addresses) to geocode.

    census_indexfield: str
        Name of pd.Series in `census_data` containing index values.

    target_geometry_data: pd.DataFrame
        DataFrame containing target geometry data (no geometries stored - see `geometry.Geometry.create_tgforlinking()`).

    target_geometry_geocode_field: str
        Name of pd.Series in `target_geometry_data` to
        perform string comparison with `census_geocode_field`.

    target_geometry_indexfield:
        Name of pd.Series in `target_geometry_data` DataFrame containing index values.

    census_block: list
        List of name(s) of pd.Series in `census_data` to limit
        string comparisons between `census_data` and `target_geometry_data`.

    target_geom_block: list
        List of name(s) of pd.Series in `target_geometry_data`
        to limit string comparisons between `census_data` and `target_geometry_data`.

    comparers: dict
        Dictionary of comparison functions and corresponding labels to pass to `utils.rapidfuzzy_wratio_comparer()`.

    sim_thresh: int
        Threshold to filter string similarity comparison scores; possible matches
        must have a similarity score equal to or higher than sim_thresh.

    align_thresh: int
        Threshold to filter length of string alignment; possible matches have
        an alignment length equal to or higher than align_thresh.

    comparison_method: str
        Name of comparison method to calculate final comparison score in `_calc_finalscore()`.

    final_score_field: str
        Label to set name of pd.Series containing final comparison scores.

    cand_links: pd.MultiIndex
        A pd.MultiIndex of two records, one from `census_data` and one from `target_geometry_data`.

    tgt_rslts: pd.Dataframe
        A pd.DataFrame of all matches between census and target geometry data that meet given thresholds.

    rslts_dict: dict
        A dictionary of 3 geocoded pd.DataFrames, where the keys are the names of the outputs and the values are pd.DataFrame. E.g.

        ```{"matches": pd.DataFrame,
            "competing_matches": pd.DataFrame,
            "matches_lq": pd.DataFrame,
        }
        ```

    Notes
    -------

    Some details on the private methods:

    `_create_candidate_links()`
        Create candidate links based on geo-blocking to pass to the string comparison
        function `_compare`. Returns a pd.MultiIndex of pairs of records, one from `census_data` and one
        from `target_geometry_data`.

    `_compare()`
        Performs fuzzy string matching between candidate links returned by `_create_candidate_links()`.
        Returns a pd.DataFrame of all possible matches after filtering on thresholds.

    `_process_results()`
        Filters `target_results` to produce 3 sets of results. Returns dictionary containing these 3 dataframes.

    _set_comparisons()
        Add comparison algorithms specified in configuration files to instance of `recordlinkage.Compare`

    `_filterbythreshold()`
        Filters possible matches by threshold similarity score specified in configuration files.

    `_calc_finalscore()`
        Calculates final comparison scores, returns matches_all `pd.DataFrame` with scores added.
    """

    def __init__(
        self,
        census_data: pd.DataFrame,
        census_geocode_field: str,
        census_indexfield: str,
        target_geometry_data: pd.DataFrame,
        target_geometry_geocode_field: str,
        target_geometry_indexfield: str,
        census_block: list,
        target_geom_block: list,
        comparers: dict,
        sim_thresh: int,
        align_thresh: int,
        comparison_method: str,
        final_score_field: str,
    ) -> None:
        self.census_data = census_data
        self.census_geocode_field = census_geocode_field
        self.census_indexfield = census_indexfield

        self.target_geometry_data = target_geometry_data
        self.target_geometry_geocode_field = target_geometry_geocode_field
        self.target_geometry_indexfield = target_geometry_indexfield

        self.census_block = census_block
        self.target_geom_block = target_geom_block

        self.comparers = comparers
        self.sim_thresh = sim_thresh
        self.align_thresh = align_thresh
        self.comparison_method = comparison_method
        self.final_score_field = final_score_field

        self.census_data = self.census_data.set_index(
            self.census_indexfield
        )  # set index of census data to specified index field

        self.target_geometry_data = self.target_geometry_data.set_index(
            self.target_geometry_indexfield
        )  # set index of target geometry data to specified index field

        self.cand_links = self._create_candidate_links()

        self.tgt_rslts = self._compare(self.cand_links)

        self.rslts_dict = self._process_results(self.tgt_rslts)

    def _create_candidate_links(
        self,
    ) -> pd.MultiIndex:
        """Create candidate links based on geo-blocking to pass to the string comparison
        function `_compare`. Returns a pd.MultiIndex of pairs of records, one from `census_data` and one
        from `target_geometry_data`.

        Returns
        -------
        target_candidate_links: pandas.MultiIndex
            A pandas MultiIndex of two records, one from census_data and one from target_geometry_data.

        """

        if self.census_data.empty or self.target_geometry_data.empty:
            print("No census or target geom data - therefore no candidate links")
            target_candidate_links = pd.MultiIndex(
                levels=[
                    [],
                ],
                codes=[
                    [],
                ],
            )  # add blank pd.MultiIndex so that code runs even if there are no valid candidates to link, e.g. subsets of the census data with no valid addresses.
        else:
            targetgeom_indexer = recordlinkage.Index()
            blocking_fields_l = self.census_block
            blocking_fields_r = self.target_geom_block
            targetgeom_indexer.block(
                left_on=blocking_fields_l, right_on=blocking_fields_r
            )

            target_candidate_links = targetgeom_indexer.index(
                self.census_data, self.target_geometry_data
            )

        return target_candidate_links

    def _compare(
        self,
        target_candidate_links,
    ) -> pd.DataFrame:
        """Performs fuzzy string matching between candidate links returned by `create_candidate_links()`.
        Returns a DataFrame of all possible matches after filtering on thresholds.

        Parameters
        ----------

        target_candidate_links: pd.MultiIndex
            pd.MultiIndex of record pairs, one from `census_data` and one from `target_geometry_data`.

        Returns
        -------
        target_results: pd.Dataframe
            pd.DataFrame of all matches between `census_data` and `target_geometry_data`.

        """
        if target_candidate_links.empty:
            print("No candidate links to compare")
            target_results = (
                pd.DataFrame()
            )  # add blank pd.DataFrame so that code runs even if there are no valid candidates to link, e.g. subsets of the census data with no valid addresses.

        else:
            target_comparison = recordlinkage.Compare()

            target_comparison = self._set_comparisons(
                target_comparison,
            )

            target_results = target_comparison.compute(
                target_candidate_links, self.census_data, self.target_geometry_data
            )
            target_results = target_results.sort_index()

            target_results = self._filterbythreshold(target_results)

        return target_results.reset_index()

    def _process_results(
        self,
        target_results,
    ) -> dict:
        """Filters `target_results` to produce 3 sets of results:
        1. Highest scoring matches with no competing matches of equal quality (`matches`)
        2. Highest scoring matches with more than 1 competing match of equal quality (`competing_matches`)
        3. Remaining `target_results` not included in 1 or 2; matches above threshold but not highest quality (`matches_lq`)


        Parameters
        ----------

        target_results: pd.DataFrame
             pd.DataFrame of all matches between census and target geometry data that meet given thresholds.

        Returns
        -------

        A dictionary of 3 sets of results in the format:

        ```{"matches": pd.DataFrame,
            "competing_matches": pd.DataFrame,
            "matches_lq": pd.DataFrame,
        }
        ```
        """

        if target_results.empty:
            print(f"No matches or no matches meeting filter thresholds")
            matches = pd.DataFrame()
            competing_matches = pd.DataFrame()
            matches_lq = pd.DataFrame()
        else:
            matches_all = target_results.merge(
                self.census_data[self.census_geocode_field],
                left_on=self.census_data.index.name,
                right_index=True,
            ).merge(
                self.target_geometry_data[[self.target_geometry_geocode_field]],
                left_on=self.target_geometry_data.index.name,
                right_index=True,
            )

            matches_all = self._calc_finalscore(matches_all)

            matches_all_maxonly = matches_all[
                matches_all[self.final_score_field]
                == matches_all.groupby(self.census_data.index.name)[
                    self.final_score_field
                ].transform("max")
            ]

            matches = matches_all_maxonly.drop_duplicates(
                subset=[self.census_data.index.name], keep=False
            )
            competing_matches = matches_all_maxonly[
                matches_all_maxonly.duplicated(
                    subset=[self.census_data.index.name], keep=False
                )
            ]

            matches_lq = matches_all[
                (matches_all.index.isin(matches.index) == False)
                & (matches_all.index.isin(competing_matches) == False)
            ]

        return {
            "matches": matches,
            "competing_matches": competing_matches,
            "matches_lq": matches_lq,
        }

    def _set_comparisons(
        self,
        target_comparison,
    ) -> recordlinkage.Compare:
        """Add comparison algorithms specified in configuration files to instance of `recordlinkage.Compare`

        Parameters
        ----------

        target_comparison: `recordlinkage.Compare`
            Instance of `recordlinkage.Compare`

        Returns
        ----------
        target_comparison: `recordlinkage.Compare`
            Instance of `recordlinkage.Compare` with comparison algorithms added.

        """
        for comparer_method, comparer_label in self.comparers.items():
            target_comparison.add(
                utils.rapidfuzzy_wratio_comparer(
                    left_on=self.census_geocode_field,
                    right_on=self.target_geometry_geocode_field,
                    method=comparer_method,
                    label=comparer_label,
                )
            )

        return target_comparison

    def _filterbythreshold(self, target_results) -> pd.DataFrame:
        """Filters possible matches by threshold similarity score specified in configuration files.

        Parameters
        ----------

        target_results: `pd.DataFrame`
            'pd.DataFrame` containing all possible matches between census data and target geometry data.

        Returns
        ----------
        target_results: `pd.DataFrame`
            `pd.DataFrame` of matches that have similarity or align scores equal to or greater than specified thresholds.

        """
        if self.sim_thresh is not None:
            target_results = target_results[
                target_results[list(self.comparers.values())[0]] >= self.sim_thresh
            ]

        if self.align_thresh is not None:
            target_results = target_results[
                target_results[list(self.comparers.values())[1]] >= self.align_thresh
            ]

        return target_results.copy()

    def _calc_finalscore(self, matches_all) -> pd.DataFrame:
        """Calculates final comparison scores, adding these to the matches_all dataframe.

        Parameters
        ----------

        mathes_all: `pd.DataFrame`
            'pd.DataFrame` containing possible matches between census data and target geometry data.

        Returns
        ----------
        matches_all: `pd.DataFrame`
            `pd.DataFrame` containing all possible matches between census data and target geometry data with added comparison scores.

        """

        if self.comparison_method == "1911_bespoke":
            matches_all[list(self.comparers.values())[2]] = matches_all.groupby(
                self.census_data.index.name
            )[list(self.comparers.values())[2]].transform("rank", ascending=False)

        matches_all[self.final_score_field] = matches_all[
            list(self.comparers.values())
        ].prod(axis="columns")

        return matches_all.copy()
