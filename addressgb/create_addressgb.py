import pandas as pd
from collections import namedtuple
import pathlib
import numpy as np


list_of_census = [
    "EW_1851",
    # "EW_1861",
    # "EW_1881",
    # "EW_1891",
    # "EW_1901",
    # "EW_1911",
    # "scot_1851",
    # "scot_1861",
    # "scot_1871",
    # "scot_1881",
    # "scot_1891",
    # "scot_1901",
]

Geom = namedtuple('geom', 'osopenroads gb1900')
geoms = Geom("osopenroads", "gb1900")

output_suffix = "final"

def set_blockcols(country, year, ):

    blockcols = []

    if country == "EW":
        # if year <= 1891:
        #     conparid = "conparid_51-91"
        # else:
        #     conparid = "conparid_01-11"

        cen_rsd = f"CEN_{year}"

        blockcols.append("ConParID")
        blockcols.append(cen_rsd)
    else:
        blockcols.append("merged_id", "conrd_town")

    return blockcols


empty_files = []

cols_1911 = ["address_uid", "street_uid", "rapidfuzzy_wratio_s", "align", "fs", "src_start_pos"]
cols_other = ["address_uid", "street_uid", "rapidfuzzy_wratio_s", "align", "fs",]

for census in list_of_census:
    country = census.split("_")[0]
    year = census.split("_")[1]

    geom_fcols = []
    geom_icols = ["street_uid", ]

    if country == "EW" and int(year) < 1901:
        conparid = "conparid_51-91"
        geom_icols.append(conparid)
    elif country == "EW" and int(year) >1891:
        conparid = "conparid_01-11"
        geom_icols.append(conparid)

    if country == "EW":
        cen = f"CEN_{year}"
        geom_icols.append(cen)
    else:
        merged_id = "merged_id"
        contownrd =  "conrd_town"
        geom_icols.append(merged_id)
        geom_icols.append(contownrd)


    print(year, country)
    for geom in geoms:
        geom_output_dir1 = pathlib.Path(f"../data/output_final/{country}/{year}/{geom}")
        if geom == "gb1900":
            suffix = "_deduped_distcount2"
            geom_fcols.append("dist_calc")
            geom_icols.append("count")
            if country == "EW":
                col_order = ["street_uid", "pin_id", "final_text", "final_text_alt", conparid, cen, "count", "dist_calc", "pin_id_removed", "geometry"]
            else:
                col_order = ["street_uid", "pin_id", "final_text", "final_text_alt", "merged_id", "conrd_town", "count", "dist_calc", "pin_id_removed", "geometry"]
        else:
            suffix = "_deduped_nodistcalc"
            if country == "EW":
                col_order = ["street_uid", "nameTOID", "name1", "name1_alt", conparid, cen, "geometry"]
            else:
                col_order = ["street_uid", "nameTOID", "name1", "name1_alt", "merged_id", "conrd_town", "geometry"]


        geom_data = pd.read_csv(geom_output_dir1 / f"{country}_{year}_{geom}{suffix}.tsv", sep = "\t", nrows = 10000) #remove row limiter


        geom_data[geom_icols] = geom_data[geom_icols].apply(pd.to_numeric, downcast = "integer" )
        geom_data[geom_fcols] = geom_data[geom_fcols].apply(pd.to_numeric, downcast = "float" )

        geom_data = geom_data[col_order]

        if geom == "gb1900":
            geom_data = geom_data.rename(columns = {"pin_id_removed":"pin_id_duplicates"})

        print(geom_data.info(verbose=True))

        geom_data = geom_data.sort_values(by = "street_uid", axis = 0)
        geom_data.to_csv(f"../data/addressgb/{country}_{year}_{geom}.tsv", sep = "\t", index = False)

        df_datatypes = pd.DataFrame(geom_data.dtypes).rename(columns = {0:"dtype"})
        df_null_count = pd.DataFrame(geom_data.count()).rename(columns = {0:"not_null_values"})
        info_output = pd.merge(left = df_datatypes, right = df_null_count, left_index=True, right_index=True, how = "outer").reset_index(names = "field")
        info_output.to_csv(f"../data/addressgb/{country}_{year}_{geom}_metadata.tsv", sep = "\t", index = False)

        merged_list = []
        geom_output_dir = pathlib.Path(f"../data/output_{output_suffix}/{country}/{year}/")
        for p in geom_output_dir.rglob("*"):
            # print(p)
            if p.is_dir():
                for file_p in p.iterdir():
                    partition = file_p.parent.name
                    if file_p.stem == f"{country}_{year}_{geom}_matches_{partition}":

                        try:
                            if int(year) == 1911:
                                linked_partion = pd.read_csv(file_p, 
                                    sep="\t", 
                                    usecols=cols_1911,)
                            else:
                                linked_partion = pd.read_csv(file_p, 
                                    sep="\t", 
                                    usecols=cols_other,)
                            
                            blockcols = set_blockcols(country=country,
                                                    year=year)
                            cols_to_read = []
                            cols_to_read.extend(["RecID", "address_uid", ])
                            cols_to_read.extend(blockcols)
                            lkup = pd.read_csv(f"../data/output_{output_suffix}/{country}/{year}/{partition}/{country}_{year}_address_uid_{partition}.tsv", 
                                                sep="\t",
                                                usecols=["RecID", "address_uid"],)
                            


                            merged = pd.merge(left = lkup, right = linked_partion, on = "address_uid", how = "left", indicator="geocode_status")
                            merged["geocode_status"] = np.where(merged["geocode_status"] == "left_only", "notgeocoded", 
                                                        np.where(merged["geocode_status"] == "both", "geocoded", "error"))
                            merged_list.append(merged)

                        except pd.errors.EmptyDataError:
                            empty_files.append(file_p)
                            
        merged_all = pd.concat(merged_list)


        output_file = merged_all[merged_all["geocode_status"] != "notgeocoded"].copy()

        output_file = output_file.rename(columns = {"rapidfuzzy_wratio_s":"sim_score",
                                    "align":"align_len", 
                                    "fs":"final_score"})

        fcols = ["sim_score", "final_score"]

        icols = ["street_uid", "align_len", "RecID"] 

        if int(year) == 1911:
            output_file = output_file.rename(columns = {"src_start_pos":"align_rank"})
            icols.append("align_rank")
        
        output_file = output_file.drop(columns=["geocode_status", "address_uid"])


        output_file[icols] = output_file[icols].apply(pd.to_numeric, downcast = "integer" )
        output_file[fcols] = output_file[fcols].apply(pd.to_numeric, downcast = "float" )

        output_file = output_file.sort_values(by = "RecID", axis = 0)
        output_file.to_csv(f"../data/addressgb/{country}_{year}_{geom}_recidlkup.tsv", sep = "\t", index = False,)

        df_datatypes = pd.DataFrame(output_file.dtypes).rename(columns = {0:"dtype"})
        df_null_count = pd.DataFrame(output_file.count()).rename(columns = {0:"not_null_values"})
        info_output = pd.merge(left = df_datatypes, right = df_null_count, left_index=True, right_index=True, how = "outer").reset_index(names = "field")
        info_output.to_csv(f"../data/addressgb/{country}_{year}_{geom}_recidlkup_metadata.tsv", sep = "\t", index = False)




        # perform checks
        addressgb_lkup = pd.read_csv(f"../data/addressgb/{country}_{year}_{geom}_recidlkup.tsv", sep = "\t", )
        addressgb_geomdata = pd.read_csv(f"../data/addressgb/{country}_{year}_{geom}.tsv", sep = "\t",)


        combined = pd.merge(left = addressgb_lkup, right = addressgb_geomdata.drop("geometry", axis=1), on = "street_uid", how = "left", validate="m:1")

        if geom == "gb1900":
            na_values = len(combined[combined["pin_id"].isna()])
        elif geom == "osopenroads":
            na_values = len(combined[combined["nameTOID"].isna()])

        if na_values > 0:
            raise ValueError("Error in merging census lkup with geom lkup")