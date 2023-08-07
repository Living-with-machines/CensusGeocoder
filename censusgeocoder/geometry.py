import geopandas as gpd
import pandas as pd

import utils

class Geometry:
    def __init__(self, 
                 name, 
                 file_path, 
                #  geom_type, 
                 fields, 
                 read_params,
                 write_params,
                 ):

        self.name = name
        self.file_path = file_path

        self.fields = fields

        self.read_params = read_params
        self.write_params = write_params
        self.data = None


        
        self.field_list = utils.fieldtolist(self.fields, )

    def add_lkup(self, **kwargs, ):
        self.data = utils.add_lkup(self, **kwargs, )


    def create_uid(self,
                   list_of_idcols,
                   ):
        uid = "_".join([idcol for idcol in list_of_idcols])
        self.data[uid] = self.data[list_of_idcols].astype(str).agg('_'.join, axis=1)

    def read_geometry_file(self, 
                             ):

        if self.read_params["filetype"] == "csv":
            geometry_data = utils.read_csv_geom(self.file_path, self.field_list, self.read_params, )
        elif self.read_params["filetype"] == "shp":
            geometry_data = utils.read_shp_geom(self.file_path, self.field_list, self.read_params, )
        else:
            raise ValueError("Currently only delimited text files or shp accepted")

        return geometry_data
    

    def get_geometry_data(self, 
                          ):
        self.data = self.read_geometry_file()

        if self.read_params["geometry_format"] == "coords":

            self.data = utils.process_coords(self.data, 
                                                 self.fields["long_field"], 
                                                 self.fields["lat_field"],
                                                 self.read_params["projection"], 
                                                 )
        
        # elif read_params["geometry_format"] == "wkt":
        else:
            "do nothing"

        return self.data

    
    def assigntoboundary(self, ):
        pass
    



class TargetGeometry(Geometry):
    def __init__(self, 
                 standardisation_file, 
                 census_country, 
                 census_year, 
                 geom_type,
                 *args,
                 **kwargs, 
                 ):


        self.standardisation_file = standardisation_file
        self.census_country = census_country
        self.census_year = census_year
        self.geom_type = geom_type

        super().__init__(*args, **kwargs)

        self.uid = self.create_uid(self.name, 
                            self.census_country, 
                            self.census_year, 
                            )
        
        self.data = utils.clean_address_data(self.data, 
                                            self.fields["address"], 
                                            self.standardisation_file, )


class Boundary(Geometry):
    def __init__(self, 
                *args,
                **kwargs, 
                ):
        
        super().__init__(*args, **kwargs)


    def merge_boundaries(self, boundary_list, ):
        
        base_bndry_name = self.name
        merged_boundaries = Boundary(name = base_bndry_name + "_" + "_".join([x.name for x in boundary_list]),
                                     file_path = None,
                                     fields = {},
                                     read_params = None,
                                     write_params = None, )

        for boundary in boundary_list:
            merged_boundaries.data =  gpd.overlay(
                            self.data, boundary.data, how="intersection", keep_geom_type=True
                                    )

        return merged_boundaries
    

    def dissolve_boundaries(self, dissolve_field,  ):

        self.data.geometry = self.data.geometry.buffer(0)
        self.data = self.data.dissolve(by=dissolve_field).reset_index()
        return self.data