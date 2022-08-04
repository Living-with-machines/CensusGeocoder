import pandas as pd
import recordlinkage
import utils


def create_candidate_links(
    census, target_geom_data, census_blocking_cols, geom_blocking_cols
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

    if census.empty or target_geom_data.empty:
        print("No census or target geom data for this county")
        target_candidate_links = pd.DataFrame()
    else:
        targetgeom_indexer = recordlinkage.Index()
        blocking_fields_l = census_blocking_cols
        blocking_fields_r = geom_blocking_cols
        targetgeom_indexer.block(left_on=blocking_fields_l, right_on=blocking_fields_r)
        target_candidate_links = targetgeom_indexer.index(census, target_geom_data)

    return target_candidate_links


def compare(
    census, target_geom_data, target_candidate_links, geom_config, census_params,
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
        if census_params.comparison_params.string_comp_alg in [
            "rapidfuzzy_wratio",
            "rapidfuzzy_partial_ratio",
        ]:
            target_comparison.add(
                utils.rapidfuzzy_wratio_comparer(
                    left_on=census_params.census_fields.address,
                    right_on=geom_config.data_fields.address_field,
                    method=census_params.comparison_params.string_comp_alg,
                    label=f"{census_params.comparison_params.string_comp_alg}_s",
                )
            )
        else:
            target_comparison.string(
                left_on=census_params.census_fields.address,
                right_on=geom_config.data_fields.address_field,
                method=census_params.comparison_params.string_comp_alg,
                label=f"{census_params.comparison_params.string_comp_alg}_s",
            )

        target_results = target_comparison.compute(
            target_candidate_links, census, target_geom_data
        )
        target_results = target_results.sort_index()
        target_results = target_results[
            target_results[f"{census_params.comparison_params.string_comp_alg}_s"]
            >= census_params.comparison_params.sim_thresh
        ].copy()
    return target_results


def process_results(
    target_results, census, target_geom_data, census_params, geom_config, new_uid
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
            f"No matches >= {census_params.comparison_params.sim_thresh} string similarity"
        )
        linked = pd.DataFrame()
        linked_duplicates = pd.DataFrame()
    else:
        linked_1 = pd.merge(
            census,
            target_results,
            left_index=True,
            right_on=census_params.census_output_params.new_uid,
        ).reset_index()

        linked_all = pd.merge(
            target_geom_data[[geom_config.data_fields.address_field]],
            linked_1,
            left_index=True,
            right_on=new_uid,
        )

        linked_all = linked_all.sort_values(
            by=census_params.census_output_params.new_uid
        )

        linked_all[f"{census_params.comparison_params.string_comp_alg}_ws"] = (
            linked_all[f"{census_params.comparison_params.string_comp_alg}_s"]
            * linked_all["tfidf_w"]
        )
        linked_all_maxonly = linked_all[
            linked_all[f"{census_params.comparison_params.string_comp_alg}_ws"]
            == linked_all.groupby(census_params.census_output_params.new_uid)[
                f"{census_params.comparison_params.string_comp_alg}_ws"
            ].transform("max")
        ]

        linked = linked_all_maxonly.drop_duplicates(
            subset=[census_params.census_output_params.new_uid], keep=False
        )
        linked_duplicates = linked_all_maxonly[
            linked_all_maxonly.duplicated(
                subset=[census_params.census_output_params.new_uid], keep=False
            )
        ]

    return linked, linked_duplicates
