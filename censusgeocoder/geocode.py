import pandas as pd
import recordlinkage
import utils



class GeoCode:
    """
    A class to geocode census data.
    
    Attributes
    ----------


    census_data: pandas.DataFrame
        DataFrame containing census data.

    census_geocode_field: str
        Column name of pandas.Series containing text (e.g. Addresses) to geocode in census_data.

    census_indexfield: str
        Column name of pandas.Series in census_data DataFrame containing index values.

    target_geometry_data: pandas.DataFrame
        DataFrame containing target geometry data (no geometries stored).

    target_geometry_geocode_field: str
        Column name of pandas.Series containing field in target_geometry_data to perform string comparison with census_geocode_field.

    target_geometry_indexfield:
        Column name of pandas.Series in target_geometry_data DataFrame containing index values.

    census_block: list
        List of column name(s) of pandas.Series in census_data DataFrame to limit string comparisons between census_data and target_geometry_data.

    target_geom_block: list
        List of column name(s) of pandas.Series in target_geometry_data DataFrame to limit string comparisons between census_data and target_geometry_data.

    comparers: dict
        Dictionary of comparison functions and corresponding labels to pass to utils.rapidfuzzy_wratio_comparer.

    sim_thresh: int
        Threshold to filter string similarity comparison scores; possible matches must have a similarity score equal to or higher than sim_thresh.

    align_thresh: int
        Threshold to filter length of string alignment; possible matches have an alignment length equal to or higher than align_thresh.

    comparison_method: str
        Name of comparison method to calculate final comparison score in _calc_finalscore()

    final_score_field: str
        Label to set column name of pandas.Series containing final comparison scores.

    Methods
    -------

    create_candidate_links()
        Creates candidate links based on geo-blocking to pass to the string comparison function.
    compare()
        Performs fuzzy string matching between candidate links and filters results by similarity and alignment thresholds.
    process_results()
        Links target matches to census_data and target_geometry data; calculates final scores.


    """
    def __init__(self, 
                 census_data,
                 census_geocode_field,
                 census_indexfield,
                 target_geometry_data,
                 target_geometry_geocode_field,
                 target_geometry_indexfield,
                 census_block,
                 target_geom_block,
                 comparers,
                 sim_thresh,
                 align_thresh,
                 comparison_method,
                 final_score_field,
                 ) -> None:


        self.census_data = census_data
        self.census_indexfield = census_indexfield
        self.target_geometry_indexfield = target_geometry_indexfield
        self.target_geometry_data = target_geometry_data
        self.census_block = census_block
        self.target_geom_block = target_geom_block
        self.comparers = comparers
        self.sim_thresh = sim_thresh
        self.comparison_method = comparison_method
        self.census_geocode_field = census_geocode_field
        self.target_geometry_geocode_field = target_geometry_geocode_field
        self.final_score_field = final_score_field
        self.align_thresh = align_thresh


        self.census_data = self.census_data.set_index(self.census_indexfield)

        self.target_geometry_data = self.target_geometry_data.set_index(self.target_geometry_indexfield)

        self.cand_links = self.create_candidate_links()

        self.tgt_rslts = self.compare(self.cand_links)

        self.lnked, self.lnked_dup, self.lnked_left = self.process_results(self.tgt_rslts)


    def create_candidate_links(self, 
    ):
        """Create candidate links based on geo-blocking to pass to the string comparison
        function. Returns a pandas.MultiIndex of two records, one from the census and one
        from the target geometry dataset.

        Parameters
        ----------
        census: pandas.DataFrame
            A pandas dataframe containing census data.

        target_geom_data: geopandas.Geodataframe
            A geopandas dataframe containing target geometry data.

        census_blocking_cols: list
            List of column names from census on which to apply blocking.
            
        geom_blocking_cols: list
            List of column names from target geometry dataset on which to apply blocking.

        Returns
        -------
        target_candidate_links: pandas.MultiIndex
            A pandas MultiIndex of two records, one from the census and one from target
            geometry data.
        """

        if self.census_data.empty or self.target_geometry_data.empty:
            print("No census or target geom data for this county")
            target_candidate_links = pd.DataFrame()
        else:
            targetgeom_indexer = recordlinkage.Index()
            blocking_fields_l = self.census_block
            blocking_fields_r = self.target_geom_block
            targetgeom_indexer.block(left_on=blocking_fields_l, right_on=blocking_fields_r)

            target_candidate_links = targetgeom_indexer.index(self.census_data, self.target_geometry_data)

        return target_candidate_links


    def compare(self, target_candidate_links,
    ):
        """
        Performs fuzzy string matching between candidate links identified between
        target geometry data and census. Returns a dataframe of all possible matches
        above set similarity threshold.

        Parameters
        ----------
        census: pandas.DataFrame
            A pandas dataframe containing census data.

        target_geom_data: geopandas.GeoDataFrame
            A geopandas dataframe containing target geometry data.

        target_candidate_links: pandas.MultiIndex
            A pandas MultiIndex of two records, one from the census and one from target
            geometry data.

        geom_config: Dataclass
            Dataclass containing parameters for target geometry data.

        census_params: Dataclass
            Dataclass containing parameters for census year.

        Returns
        -------
        target_results: pandas.Dataframe
            A pandas dataframe of all matches between census and target geometry data.
        """
        if target_candidate_links.empty:
            print("No candidate links to compare")
            target_results = pd.DataFrame()

        else:
            target_comparison = recordlinkage.Compare()  # Set up comparison

            target_comparison = self._set_comparisons(target_comparison, )

            target_results = target_comparison.compute(
                target_candidate_links, self.census_data, self.target_geometry_data
            )
            target_results = target_results.sort_index()

            target_results = self._filterbythreshold(target_results)
            
        return target_results.reset_index()


    def process_results(self,
        target_results, 
    ):
        """Processes target results by selecting best batch using a combination of
        fuzzy string matching score and tf-idf weighting. Candidate links with more
        than one strong match are stored in a duplicates table. Returns matches and
        duplicate matches.

        Parameters
        ----------
        census: pandas.DataFrame
            A pandas dataframe containing census data.

        target_geom_data: geopandas.GeoDataFrame
            A geopandas dataframe containing target geometry data.

        census_params: Dataclass
            Dataclass containing parameters for census year.

        geom_config: Dataclass
            Dataclass containing parameters for target geometry data.

        new_uid: str
            Name of unique identifier column created from target geometry name
            and census year.

        Returns
        -------
        linked: pandas.Dataframe
            A pandas dataframe of high-quality matches between target geometry data
            and census.

        linked_duplicates: pandas.Dataframe
            A pandas dataframe of duplicate matches between target geometry data and census 
            (where there are more than one matches of high quality).
        """

        if target_results.empty:
            print(
                f"No matches >= {self.sim_thresh} string similarity"
            )
            linked = pd.DataFrame()
            linked_duplicates = pd.DataFrame()
            linked_leftovers = pd.DataFrame()
        else:

            linked_all = target_results.merge(
                self.census_data[self.census_geocode_field],
                left_on=self.census_data.index.name, 
                right_index = True,#sort this out
                ).merge(self.target_geometry_data[[self.target_geometry_geocode_field]],
                    left_on = self.target_geometry_data.index.name,
                    right_index = True)

            linked_all = self._calc_finalscore(linked_all)

            linked_all_maxonly = linked_all[linked_all[self.final_score_field] == linked_all.groupby(self.census_data.index.name)[self.final_score_field].transform("max")]



            linked = linked_all_maxonly.drop_duplicates(
                subset=[self.census_data.index.name], keep=False
            )
            linked_duplicates = linked_all_maxonly[
                linked_all_maxonly.duplicated(
                    subset=[self.census_data.index.name], keep=False
                )
            ]

            linked_leftovers = linked_all[(linked_all.index.isin(linked.index) == False) & (linked_all.index.isin(linked_duplicates) == False)]

        return linked, linked_duplicates, linked_leftovers



    def _set_comparisons(self, target_comparison, ):

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
    

    def _calc_finalscore(self, linked_all):

        if self.comparison_method == "1911_bespoke":

            linked_all[list(self.comparers.values())[2]] = linked_all.groupby(self.census_data.index.name)[list(self.comparers.values())[2]].transform("rank", ascending = False)
            
        
        linked_all[self.final_score_field] = linked_all[list(self.comparers.values())].prod(axis="columns")

        return linked_all.copy()
    

    def _filterbythreshold(self, target_results):

        if self.sim_thresh != None:
            target_results = target_results[target_results[list(self.comparers.values())[0]]>= self.sim_thresh]
            
        if self.align_thresh != None:
            target_results = target_results[target_results[list(self.comparers.values())[1]]>= self.align_thresh]

        return target_results.copy()