import pandas as pd
import recordlinkage
import string_comparison

def gb1900_candidate_links(census,gb1900,conparid,cen):

	if census.empty:
		print('No census data for this county')
		gb1900_candidate_links = pd.DataFrame()
	else:
		gb1900_indexer = recordlinkage.Index()
		gb1900_indexer.block(left_on = ['ConParID',cen],right_on = [conparid,cen])
		print('Creating candidate links between gb1900 and census')
		gb1900_candidate_links = gb1900_indexer.index(census, gb1900)

	return gb1900_candidate_links

def gb1900_compare(census,gb1900,gb1900_candidate_links):
	"""
	Performs fuzzy string matching between census addresses and labels in GB1900 data.

	Parameters
	----------
	This
	"""
	if gb1900_candidate_links.empty:
		print('no candidate links to compare')
		gb1900_census_roads_output_filtered_deduplicated = pd.DataFrame()
		gb1900_census_roads_output_filtered_duplicates = pd.DataFrame()
	else:
		gb1900_comparison = recordlinkage.Compare() # Set up comparison

		gb1900_comparison.add(string_comparison.rapidfuzzy_wratio_comparer(left_on = 'add_anon',right_on = 'final_text', method='rapidfuzzy_wratio', label='rfuzz_score'))

		print('Computing gb1900 / census string comparison')

		gb1900_comparison_results = gb1900_comparison.compute(gb1900_candidate_links, census, gb1900)
		gb1900_comparison_results = gb1900_comparison_results.sort_index()
		gb1900_comparison_results = gb1900_comparison_results[gb1900_comparison_results['rfuzz_score'] >= 90].copy()

		
		if gb1900_comparison_results.empty:
			print('No matches >= 90 string similarity')
			gb1900_census_roads_output_filtered_deduplicated = pd.DataFrame()
			gb1900_census_roads_output_filtered_duplicates = pd.DataFrame()
		else:

			# Link comparison results to I-CeM data and OS Road Vector data
			gb1900_census_roads_output = pd.merge(census,gb1900_comparison_results,left_index=True,right_on='unique_add_id')
			cols_to_use = gb1900_census_roads_output.columns.difference(gb1900.columns)
			gb1900_census_roads_output = pd.merge(gb1900, gb1900_census_roads_output[cols_to_use],left_index=True,right_on='pin_id')
			gb1900_census_roads_output = gb1900_census_roads_output.reset_index()
			gb1900_census_roads_output = gb1900_census_roads_output.sort_values(by='unique_add_id')

			gb1900_census_roads_output['rfuzz_weighted'] = gb1900_census_roads_output['rfuzz_score'] * gb1900_census_roads_output['weighting']
			gb1900_census_roads_output_maxonly = gb1900_census_roads_output[gb1900_census_roads_output['rfuzz_weighted'] == gb1900_census_roads_output.groupby('unique_add_id')['rfuzz_weighted'].transform('max')]
			#print(len(gb1900_census_roads_output_maxonly))
			gb1900_census_roads_output_filtered_deduplicated = gb1900_census_roads_output_maxonly.drop_duplicates(subset=['unique_add_id'],keep=False)
			#print(gb1900_census_roads_output_filtered_deduplicated)
			gb1900_census_roads_output_filtered_duplicates = gb1900_census_roads_output_maxonly[gb1900_census_roads_output_maxonly.duplicated(subset=['unique_add_id'],keep=False)]
			#print(gb1900_census_roads_output_filtered_duplicates)

	return gb1900_census_roads_output_filtered_deduplicated, gb1900_census_roads_output_filtered_duplicates


#todo
def os_candidate_links(census,segmented_os_roads,conparid,cen):

	if census.empty:
		print('No census data for this county')
		os_candidate_links = pd.DataFrame()
	else:
		os_indexer = recordlinkage.Index()
		os_indexer.block(left_on = ['ConParID',cen],right_on = [conparid,cen])
		print('Creating candidate links between os and census')
		os_candidate_links = os_indexer.index(census, segmented_os_roads)

	return os_candidate_links

def os_compare(census,os,os_candidate_links,os_road_id):
	"""
	Performs fuzzy string matching between census addresses and road names in OS Open Road data.

	Parameters
	----------
	This

	Returns
	-------

	"""
	if os_candidate_links.empty:
		print('no candidate links to compare')
		os_census_roads_output_filtered_deduplicated = pd.DataFrame()
		os_census_roads_output_filtered_duplicates = pd.DataFrame()
	else:
		os_comparison = recordlinkage.Compare() # Set up comparison

		os_comparison.add(string_comparison.rapidfuzzy_wratio_comparer(left_on = 'add_anon',right_on = 'name1', method='rapidfuzzy_wratio', label='rfuzz_score'))

		print('Computing os / census string comparison')

		os_comparison_results = os_comparison.compute(os_candidate_links, census, os)
		os_comparison_results = os_comparison_results.sort_index()
		os_comparison_results = os_comparison_results[os_comparison_results['rfuzz_score'] >= 90].copy()

		
		if os_comparison_results.empty:
			print('No matches >= 90 string similarity')
			os_census_roads_output_filtered_deduplicated = pd.DataFrame()
			os_census_roads_output_filtered_duplicates = pd.DataFrame()
		else:

			# Link comparison results to I-CeM data and OS Road Vector data

			os_census_roads_output = pd.merge(census,os_comparison_results,left_index=True,right_on='unique_add_id')
			cols_to_use = os_census_roads_output.columns.difference(os.columns)
			os_census_roads_output = pd.merge(os, os_census_roads_output[cols_to_use],left_index=True,right_on=os_road_id)
			os_census_roads_output = os_census_roads_output.reset_index()
			os_census_roads_output = os_census_roads_output.sort_values(by='unique_add_id')

			os_census_roads_output['rfuzz_weighted'] = os_census_roads_output['rfuzz_score'] * os_census_roads_output['weighting']
			os_census_roads_output_maxonly = os_census_roads_output[os_census_roads_output['rfuzz_weighted'] == os_census_roads_output.groupby('unique_add_id')['rfuzz_weighted'].transform('max')]
			#print(len(os_census_roads_output_maxonly))
			os_census_roads_output_filtered_deduplicated = os_census_roads_output_maxonly.drop_duplicates(subset=['unique_add_id'],keep=False)
			os_census_roads_output_filtered_duplicates = os_census_roads_output_maxonly[os_census_roads_output_maxonly.duplicated(subset=['unique_add_id'],keep=False)]
			#print(os_census_roads_output_filtered_duplicates)

	return os_census_roads_output_filtered_deduplicated, os_census_roads_output_filtered_duplicates

"""
def gb1900_aggregate(gb1900_linked, gb1900_duplicates, census):

	gb1900_not_linked = pd.concat([gb1900_deduplicated,census]).drop_duplicates(subset=['unique_add_id'],keep=False)

	gb1900_census_roads_not_linked = gb1900_census_roads_not_linked.assign(dup_dropped=gb1900_census_roads_not_linked['unique_add_id'].isin(gb1900_census_roads_output_filtered_duplicates['unique_add_id']))
	pass
"""