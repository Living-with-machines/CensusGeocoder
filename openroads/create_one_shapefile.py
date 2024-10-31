import pandas as pd
import geopandas as gpd
import pathlib

def get_file_or_filelist(file_path, 
                         file_type: str = ".shp"):
    """Accepts a directory or single filepath and creates a list of file(s).

    Parameters
    -------

    file_path: str
        Either path to file or directory

    file_type: str
        File type to search for if `file_path` is directory.

    Returns
    -------
    file_list: list
        List of file(s).
    """

    file_list = []
    p = pathlib.Path(file_path)
    if p.is_file():
        file_list.append(str(p))
    else:
        for file_p in p.iterdir():
            if file_type == file_p.suffix:
                file_list.append(str(file_p))
    print(file_list)
    return file_list

def read_shp_geom(file_path, read_params, *args, **kwargs):


    filelist = get_file_or_filelist(file_path, *args, **kwargs)

    gdf_list = []

    for file_ in filelist:

        if pathlib.Path(file_).suffix == ".shp" and "RoadLink" in file_:
            
            gdf_list.append(gpd.read_file(file_, 
                          **read_params, ))

    
    target_gdf = pd.concat(gdf_list)
    

    return target_gdf

params = {"engine":"pyogrio",
            "columns": ["nameTOID", "name1", ], }

openroads = read_shp_geom("../data/input/target_geoms/oproad_essh_gb-2/data", params, )

openroads.to_file("../data/input/target_geoms/osopenroads/osopenroads.shp" )