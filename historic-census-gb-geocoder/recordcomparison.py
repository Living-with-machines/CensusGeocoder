import pandas as pd
import recordlinkage
import utils


def create_candidate_links(
    census, segmented_os_roads, census_blocking_cols, geom_blocking_cols
):
    """Create candidate links based on geo-blocking to pass to the string comparison
    function. Returns a pandas.MultiIndex of two records, one from the census and one
    from OS Roads.

    Parameters
    ----------
    census: pandas.Dataframe
        A pandas dataframe containing census data.

    segemented_os_roads: geopandas.Geodataframe
        A geopandas dataframe containing OS Roads data.

    field_dict: dictionary
        Dictionary with field values.

    Returns
    -------
    pandas.MultiIndex
        A pandas MultiIndex of two records, one from the census and one from OS Roads
        Data.
    """

    if census.empty:
        print("No census data for this county")
        os_candidate_links = pd.DataFrame()
    else:
        os_indexer = recordlinkage.Index()
        blocking_fields_l = census_blocking_cols
        blocking_fields_r = geom_blocking_cols

        # if field_dict['country'] == 'SCOT':
        # 	blocking_fields_l.append('ParID')
        # 	blocking_fields_r.append(field_dict['scot_parish'])
        # elif field_dict['country'] == 'EW':
        # 	blocking_fields_l.append('ConParID')
        # 	blocking_fields_l.append(field_dict['cen'])
        # 	blocking_fields_r.append(field_dict['conparid'])
        # 	blocking_fields_r.append(field_dict['cen'])

        os_indexer.block(left_on=blocking_fields_l, right_on=blocking_fields_r)
        print("Creating candidate links between os and census")
        os_candidate_links = os_indexer.index(census, segmented_os_roads)

    return os_candidate_links


def compare(
    census,
    os,
    os_candidate_links,
    new_uid,
    geom_attributes,
    census_fields,
    comparison_params,
    census_output_params,
):
    """
    Performs fuzzy string matching between candidate links identified between OS Roads and census. Selects best batch using a combination of fuzzy string matching score and tf-idf weighting. Candidate links with more than one strong match are stored in a duplicates table. Returns matches and duplicate matches.

    Parameters
    ----------
    census: pandas.Dataframe
        A pandas dataframe containing census data.

    os: geopandas.Geodataframe
        A geopandas dataframe containing OS Roads data.

    os_candidate_links: pandas.MultiIndex
        A pandas MultiIndex of two records, one from the census and one from OS Roads data.

    field_dict: dictionary
        Dictionary with field values.

    Returns
    -------
    pandas.Dataframe
        A pandas dataframe of high-quality matches between OS Roads and census.
    pandas.Dataframe
        A pandas dataframe of duplicate matches between OS Roads and census (where there are more than 2 or more matches of high quality and there needs to be disambiguation)

    """
    if os_candidate_links.empty:
        print("no candidate links to compare")
        os_census_roads_output_filtered_deduplicated = pd.DataFrame()
        os_census_roads_output_filtered_duplicates = pd.DataFrame()
    else:
        os_comparison = recordlinkage.Compare()  # Set up comparison

        os_comparison.add(
            utils.rapidfuzzy_wratio_comparer(
                left_on=census_fields.address,
                right_on=geom_attributes.data_fields.address_field,
                method=comparison_params.string_comp_alg,
                label=f"{comparison_params.string_comp_alg}_score",
            )
        )

        print("Computing os / census string comparison")

        # print(os.info())
        # print(census.info())

        os_comparison_results = os_comparison.compute(os_candidate_links, census, os)
        os_comparison_results = os_comparison_results.sort_index()
        os_comparison_results = os_comparison_results[
            os_comparison_results[f"{comparison_params.string_comp_alg}_score"]
            >= comparison_params.sim_thresh
        ].copy()

        if os_comparison_results.empty:
            print(f"No matches >= {comparison_params.sim_thresh} string similarity")
            os_census_roads_output_filtered_deduplicated = pd.DataFrame()
            os_census_roads_output_filtered_duplicates = pd.DataFrame()
        else:

            # Link comparison results to I-CeM data and OS Road Vector data
            # print(os_comparison_results.info())
            # os_census_roads_output = os_comparison_results.reset_index()

            os_census_roads_output = pd.merge(
                census,
                os_comparison_results,
                left_index=True,
                right_on=census_output_params.new_uid,
            ).reset_index()

            print(os_census_roads_output.info())

            os_census_roads_output = pd.merge(
                os[[f"{geom_attributes.data_fields.address_field}"]],
                os_census_roads_output,
                left_index=True,
                right_on=new_uid,
            )

            # cols_to_use = os_census_roads_output.columns.difference(os.columns)
            # os_census_roads_output = pd.merge(os, os_census_roads_output[cols_to_use],left_index=True,right_on=new_uid)
            # os_census_roads_output = os_census_roads_output.reset_index()
            os_census_roads_output = os_census_roads_output.sort_values(
                by=census_output_params.new_uid
            )

            os_census_roads_output["rfuzz_weighted"] = (
                os_census_roads_output[f"{comparison_params.string_comp_alg}_score"]
                * os_census_roads_output["tfidf_weighting"]
            )
            os_census_roads_output_maxonly = os_census_roads_output[
                os_census_roads_output["rfuzz_weighted"]
                == os_census_roads_output.groupby(census_output_params.new_uid)[
                    "rfuzz_weighted"
                ].transform("max")
            ]
            # print(len(os_census_roads_output_maxonly))
            os_census_roads_output_filtered_deduplicated = os_census_roads_output_maxonly.drop_duplicates(
                subset=[census_output_params.new_uid], keep=False
            )
            os_census_roads_output_filtered_duplicates = os_census_roads_output_maxonly[
                os_census_roads_output_maxonly.duplicated(
                    subset=[census_output_params.new_uid], keep=False
                )
            ]
            # print(os_census_roads_output_filtered_duplicates)

    return (
        os_census_roads_output_filtered_deduplicated,
        os_census_roads_output_filtered_duplicates,
    )


"""
def gb1900_aggregate(gb1900_linked, gb1900_duplicates, census):

    gb1900_not_linked = pd.concat([gb1900_deduplicated,census]).drop_duplicates(subset=['unique_add_id'],keep=False)

    gb1900_census_roads_not_linked = gb1900_census_roads_not_linked.assign(dup_dropped=gb1900_census_roads_not_linked['unique_add_id'].isin(gb1900_census_roads_output_filtered_duplicates['unique_add_id']))
    pass
"""
