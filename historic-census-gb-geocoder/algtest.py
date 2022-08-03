import rapidfuzz
import pandas as pd

# streetdict = {
#     "CHASTON ROAD": [],
#     "WESTFIELD ROAD": [],
#     "BURISTEAD ROAD": [],
#     "ORCHARD ROAD": [],
#     "CAMBRIDGE ROAD": [],
#     "GRANHAM'S ROAD": [],
#     "SHELFORD ROAD": [],
#     "STATION ROAD": [],
#     "WOODLANDS ROAD": [],
#     "BABRAHAM ROAD": [],
#     "STONEHILL ROAD": [],
# }


# target = "ABBERLY GREENHAM ROAD"


# for street, scorelist in streetdict.items():
#     scorelist.append(rapidfuzz.fuzz.WRatio(street, target) / 100)
#     scorelist.append(rapidfuzz.fuzz.ratio(street, target) / 100)
#     scorelist.append(rapidfuzz.fuzz.partial_ratio(street, target) / 100)
#     # scorelist.append(rapidfuzz.fuzz.partial_ratio_alignment(street, target) / 100)
#     scorelist.append(rapidfuzz.fuzz.token_set_ratio(street, target) / 100)
#     scorelist.append(rapidfuzz.fuzz.partial_token_set_ratio(street, target) / 100)
#     scorelist.append(rapidfuzz.fuzz.token_sort_ratio(street, target) / 100)
#     scorelist.append(rapidfuzz.fuzz.partial_token_sort_ratio(street, target) / 100)
#     scorelist.append(rapidfuzz.fuzz.token_sort_ratio(street, target) / 100)
#     scorelist.append(rapidfuzz.fuzz.partial_token_ratio(street, target) / 100)

# print(streetdict)

# df = pd.DataFrame(
#     streetdict,
#     index=[
#         "WRatio",
#         "ratio",
#         "partial_ratio",
#         "token_set_ratio",
#         "partial_token_set_ratio",
#         "token_sort_ratio",
#         "partial_token_sort_ratio",
#         "token_sort_ratio",
#         "partial_token_ratio",
#     ],
# )

# print(df)

# df.to_csv("algdf.txt", sep="\t")

street = "CAMBRIDGE ROAD"
target = "ABINGTON GRANGE CAMBRIDGE ROAD"

street1 = "OAKINGTON ROAD"
target1 = "ABINGTON ROAD"


print(rapidfuzz.fuzz.partial_ratio(street1, target1) / 100)
print(rapidfuzz.fuzz.ratio(street1, target1) / 100)
