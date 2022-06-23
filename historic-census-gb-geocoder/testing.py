import pandas as pd

# census = pd.read_csv('data/input/census_anonymisation_egress/EW1851_anonymised.txt',sep="\t",quoting=3,encoding = "latin-1",na_values=".")

# trial = census.sample(1000000)

# trial.to_csv('data/input/census_anonymisation_egress/EW1851_anonymised_s.txt',sep="\t",quoting=3,encoding = "latin-1",index=False)

geom_attributes =  {
	"data_path": "data/input/gb1900_gazetteer_complete_july_2018.csv",
	"projection": "EPSG:27700",
	"file_type": "csv",
	"geom_type": "point",
	"geometry_format": "coords",
	"file_name": "",
	"data_fields":{
	"uid_field": "pin_id",
	"address_field": "final_text",
	"long_field":"osgb_east",
	"lat_field":"osgb_north"
}}

cols_to_keep = [*geom_attributes['data_fields'].values()]
print(cols_to_keep)