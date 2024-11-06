import pandas as pd
import numpy as np


geoms = ["openroads", "gb1900"]

output_suffix = "final"

cen_list = [
    "1851_EW",
    "1861_EW",
    "1881_EW",
    "1891_EW",
    "1901_EW",
    "1911_EW",
    "1851_scot",
    "1861_scot",
    "1871_scot",
    "1881_scot",
    "1891_scot",
    "1901_scot",
]


# read in manual results
manual_sample = pd.read_csv(
    "../data/validation_samples/manual_eval_sample.tsv",
    sep="\t",
)
print(manual_sample)
print(manual_sample.shape)

# create unique recid lookups by combining the recid, year and country

manual_sample_list = []

for census in cen_list:
    year = census.split("_")[0]
    country = census.split("_")[1]
    print(year, country)

    manual_sample_subset = manual_sample[
        (
            (manual_sample["year"] == int(year))
            & (manual_sample["country"] == country.upper())
        )
    ].copy()

    # read osopenroads addressgb file (only street_uid and nameTOID columns)
    openroads_addressgb = pd.read_csv(
        f"../data/addressgb/{country}_{year}_osopenroads.tsv",
        sep="\t",
        usecols=["street_uid", "nameTOID"],
    )

    # read gb1900 addressgb file (only street_uid, pin_id, pin_id_duplicates columns)
    gb1900_addressgb = pd.read_csv(
        f"../data/addressgb/{country}_{year}_gb1900.tsv",
        sep="\t",
        usecols=["street_uid", "pin_id", "pin_id_duplicates"],
    )

    # read osopenroads recid lookup (only recid and streetuid columns)
    openroads_addressgb_recidlkup = pd.read_csv(
        f"../data/addressgb/{country}_{year}_osopenroads_recidlkup.tsv",
        sep="\t",
        usecols=["street_uid", "RecID"],
    )

    # read gb1900 recid lookup (only recid and streetuid columns)
    gb1900_addressgb_recidlkup = pd.read_csv(
        f"../data/addressgb/{country}_{year}_gb1900_recidlkup.tsv",
        sep="\t",
        usecols=["street_uid", "RecID"],
    )

    # merge osopenroads to recid lookup file on streetuid; do the same for gb1900
    openroads_merged = pd.merge(
        left=openroads_addressgb_recidlkup,
        right=openroads_addressgb,
        on="street_uid",
        how="left",
    )

    openroads_merged["year"] = int(year)
    openroads_merged["country"] = country.upper()

    gb1900_merged = pd.merge(
        left=gb1900_addressgb_recidlkup,
        right=gb1900_addressgb,
        on="street_uid",
        how="left",
    )

    gb1900_merged["year"] = int(year)
    gb1900_merged["country"] = country.upper()

    # merge the addressgb recid unique lookup onto the manual results

    manual_sample_m1 = pd.merge(
        left=manual_sample_subset,
        right=openroads_merged,
        left_on=["year", "country", "recid"],
        right_on=["year", "country", "RecID"],
        how="left",
        validate="1:1",
    ).drop(columns=["RecID", "street_uid"])

    manual_sample_m2 = pd.merge(
        left=manual_sample_m1,
        right=gb1900_merged,
        left_on=["year", "country", "recid"],
        right_on=["year", "country", "RecID"],
        how="left",
        validate="1:1",
    ).drop(columns=["RecID", "street_uid"])

    # after all this, perform check on the data marking TP, FP, TN, FN (use manual marker of gb1900, openroads, both etc because NaN fields don't help here)

    manual_sample_eval = manual_sample_m2.copy()

    manual_sample_eval = manual_sample_eval.rename(
        columns={"nameTOID": "openroads_geocoder", "pin_id": "gb1900_geocoder"}
    )

    manual_sample_eval["openroads_eval"] = np.where(
        (
            (
                manual_sample_eval["openroads_man"]
                == manual_sample_eval["openroads_geocoder"]
            )
            & manual_sample_eval["geocode_man_status"].isin(["openroads", "both"])
        ),
        "True Positive",
        np.where(
            (
                (manual_sample_eval["openroads_geocoder"].isna())
                & manual_sample_eval["geocode_man_status"].isin(
                    ["not geocoded", "gb1900"]
                )
            ),
            "True Negative",
            np.where(
                (
                    (
                        manual_sample_eval["openroads_man"]
                        != manual_sample_eval["openroads_geocoder"]
                    )
                    & (manual_sample_eval["openroads_geocoder"].isna() == False)
                ),
                "False Positive",
                np.where(
                    (
                        (manual_sample_eval["openroads_geocoder"].isna())
                        & manual_sample_eval["geocode_man_status"].isin(
                            ["both", "openroads"]
                        )
                    ),
                    "False Negative",
                    "error",
                ),
            ),
        ),
    )

    manual_sample_eval["gb1900_eval"] = np.where(
        (
            (manual_sample_eval["gb1900_man"] == manual_sample_eval["gb1900_geocoder"])
            & manual_sample_eval["geocode_man_status"].isin(["gb1900", "both"])
        ),
        "True Positive",
        np.where(
            (
                (manual_sample_eval["gb1900_geocoder"].isna())
                & manual_sample_eval["geocode_man_status"].isin(
                    ["not geocoded", "openroads"]
                )
            ),
            "True Negative",
            np.where(
                (
                    (
                        manual_sample_eval["gb1900_man"]
                        != manual_sample_eval["gb1900_geocoder"]
                    )
                    & (manual_sample_eval["gb1900_geocoder"].isna() == False)
                ),
                "False Positive",
                np.where(
                    (
                        (manual_sample_eval["gb1900_geocoder"].isna())
                        & manual_sample_eval["geocode_man_status"].isin(
                            ["both", "gb1900"]
                        )
                    ),
                    "False Negative",
                    "error",
                ),
            ),
        ),
    )

    # overwrites eval fields for entries where there are multiple possible geo-coded links produced manually or by CensusGeocoder
    for geom in geoms:

        manual_sample_eval[f"{geom}_nobrckts"] = manual_sample_eval[
            f"{geom}_man"
        ].str.replace("\]|\[|\s", "", regex=True)

        if geom == "gb1900":
            manual_sample_eval[f"{geom}_geocoder_nobrckts"] = manual_sample_eval[
                "pin_id_duplicates"
            ].str.replace("\]|\[|\s|'", "", regex=True)
        else:
            manual_sample_eval[f"{geom}_geocoder_nobrckts"] = manual_sample_eval[
                f"{geom}_geocoder"
            ].str.replace("\]|\[|\s|'", "", regex=True)

        manual_sample_eval[f"{geom}_comb"] = manual_sample_eval[
            f"{geom}_nobrckts"
        ].str.cat(manual_sample_eval[f"{geom}_geocoder_nobrckts"], sep=",", na_rep="")

        manual_sample_eval[f"{geom}_len"] = manual_sample_eval.apply(
            lambda x: (len(set(x[f"{geom}_comb"].split(","))))
            - (len(x[f"{geom}_comb"].split(","))),
            axis=1,
        )

        manual_sample_eval[f"{geom}_eval_overwrite"] = np.where(
            manual_sample_eval[f"{geom}_len"] != 0, 1, np.nan
        )

        manual_sample_eval[f"{geom}_eval"] = np.where(
            (
                (manual_sample_eval[f"{geom}_eval"] == "False Positive")
                & (manual_sample_eval[f"{geom}_eval_overwrite"] == 1)
            ),
            "True Positive",
            manual_sample_eval[f"{geom}_eval"],
        )

        manual_sample_eval = manual_sample_eval.drop(
            columns=[
                f"{geom}_nobrckts",
                f"{geom}_geocoder_nobrckts",
                f"{geom}_comb",
                f"{geom}_len",
                f"{geom}_eval_overwrite",
            ]
        )

    len_openroads = len(manual_sample_eval[manual_sample_eval["openroads_eval"].isna()])
    len_gb1900 = len(manual_sample_eval[manual_sample_eval["gb1900_eval"].isna()])

    if len_openroads + len_gb1900 > 0:
        raise ValueError("missing status")

    manual_sample_list.append(manual_sample_eval)


manual_sample_eval_output = pd.concat(manual_sample_list)

manual_sample_eval_output.to_csv(
    "../data/validation_samples/addressgb_manual_evaluation_sample.tsv",
    sep="\t",
    index=False,
)
