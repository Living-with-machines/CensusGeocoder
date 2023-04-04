import pandas as pd
import dask.dataframe as dd

census_csv_params = {
	"sep": "\t",
	"encoding": "latin-1",
	"quoting": 3,
	"na_values": [".", " "],
	"usecols": ["RecID", "ConParID", "VessName"],
	"dtype":{"VessName": "object"},
	# "nrows":700000
}

census = dd.read_csv("/Users/wknq25/Documents/historic-census-gb-geocoder/data/input/census/EW1911_geocode_egress_2022_11_03_recid_corrected.txt", **census_csv_params)
# census = census.dropna(axis=0)

# print(census.compute())
# print(census[census["ConParID"].isna() == False].compute())
census = census.dropna(subset="ConParID").copy()
print(census.compute())
# print(census)
# census= census.astype({"ConParID":"int32"})
# print(census["ConParID"].value_counts(dropna=False))
# print(census.info(verbose=True))
# census2 = census.dropna(subset=["ConParID"],axis="rows")
# print(census.info())
# print(census[census["RecID"].between(672654, 672658)])