import pandas as pd
import pathlib

list_of_census = [
    "EW1851",
    "EW1861",
    "EW1881",
    "EW1891",
    "EW1901",
    "EW1911",
    "SCOT1851",
    "SCOT1861",
    "SCOT1871",
    "SCOT1881",
    "SCOT1891",
    "SCOT1901",
]

p = pathlib.Path("data/input/census")
p_sample = pathlib.Path(p, "sample")
pathlib.Path(p_sample).mkdir(parents=True, exist_ok=True)

for census in list_of_census:
    print(census)
    census_df = pd.read_csv(
        p / f"{census}_anonymised.txt",
        sep="\t",
        quoting=3,
        encoding="latin-1",
        na_values=".",
        usecols=["safehaven_id", "address_anonymised", "RegCnty", "ParID", "ConParID"],
    )

    sample_size = round(len(census_df) * 0.1)

    census_sample = census_df.sample(sample_size, random_state=1)

    census_sample.to_csv(
        p_sample / f"{census}_anonymised_sample.txt",
        sep="\t",
        quoting=3,
        encoding="latin-1",
        na_rep=".",
        index=False,
    )

