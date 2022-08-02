import pandas as pd
import pathlib
import geopandas as gpd

"""Create GB1900 sample"""

gb1900 = pd.read_csv(
    "data/input/target_geoms/gb1900_gazetteer_complete_july_2018.csv",
    sep=",",
    encoding="utf-16",
)

sample_size = round(len(gb1900) * 0.1)

gb1900_sample = gb1900.sample(sample_size, random_state=1)

gb1900_sample.to_csv(
    f"data/input/sample/target_geoms/gb1900_gazetteer_complete_july_2018.csv",
    sep=",",
    encoding="utf-16",
    index=False,
)

"""Create OS Open Roads Sample"""

geom_files = []
p = pathlib.Path("data/input/target_geoms/oproad_essh_gb-2/data")
for file_p in p.iterdir():
    if "RoadLink.shp" in str(file_p):
        geom_files.append(str(file_p))
        grid = str(file_p).split("_RoadLink.shp")[0].split("/")[-1]
        print(grid)

        os_roads = gpd.read_file(file_p)
        # print(os_roads)
        sample_size = round(len(os_roads) * 0.1)

        os_roads_sample = os_roads.sample(sample_size, random_state=1)
        # print(os_roads_sample)
        os_roads_sample.to_file(
            f"data/input/sample/target_geoms/oproad_essh_gb-2/data/{grid}_RoadLink.shp"
        )
