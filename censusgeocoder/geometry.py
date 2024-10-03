import geopandas as gpd
import pandas as pd
from dataclasses import dataclass, field, fields
import utils
import pathlib

point = "point"
line = "line"
polygon = "polygon"


@dataclass
class Geometry_vars:
    """Class for storing and validating geometry variables"""

    geom_name: str
    census_year: int
    census_country: str
    gis_file: str | list = None
    gis_file_type: str = None
    gis_uid_field: str = None
    gis_read_params: dict = None
    geom_format: str = None
    gis_field_to_clean: str = None
    gis_standardisation_file: str = None
    gis_min_len: int = None
    cleaned_field_suffix: str = None

    lkup_file: str = None
    lkup_field_uid: str = None
    lkup_field_censuslink: str = None
    lkup_read_params: dict = None

    gis_read_library: str = field(init=False)
    lkup_read_library: str = field(init=False)
    gis_write_params: dict = None
    # geom_type: str = None

    output_path: str = "../data/output_new_scotrdtesting"
    output_filetype: str = ".tsv"

    gis_convert_non_ascii: bool = False
    gis_geocode_field: str = None
    gis_lat_long: bool = False
    gis_long_field: str = None
    gis_lat_field: str = None
    gis_projection: str = None

    process: bool = True

    dedup: bool = False
    dedup_max_points: int = None
    dedup_max_distance_between_points: int = None


    merge_method: str = "intersection"

    item_per_unit_uid: str = None
    blockcols: str | list = None
    geom_type: str = field(init=False)
    uid: str | list = field(init=False)

    # _created_from_merge: bool = False

    def __post_init__(self):
        if self.process != True:
            self.geom_type = None
            self.uid = None

        if self.gis_file == None:
            self.gis_read_library = None
        else:
            self.gis_read_library = utils.get_readlibrary(
                self.gis_file,
                self.gis_read_params,
            )

        if self.lkup_file == None:
            self.lkup_read_library = None
        else:
            self.lkup_read_library = utils.get_readlibrary(
                self.lkup_file,
                self.lkup_read_params,
            )

    # def create_uid(self,
    #                list_of_idcols,
    #                ):
    #     uid = "_".join([str(idcol) for idcol in list_of_idcols])
    #     print(uid)
    #     self.data[uid] = self.data[list_of_idcols].astype(str).agg('_'.join, axis=1)


class Geometry:
    """Base Geometry Class"""

    def __init__(
        self,
        geometry_vars,
    ):
        if type(geometry_vars) == Geometry_vars:
            self.vars = geometry_vars
        else:
            raise TypeError("Must be a Geometry_vars class")

    def process(
        self,
    ):
        if self.vars.lkup_file != None:
            self.data = self._add_lkup()

            self.vars.uid = self.vars.lkup_field_censuslink

            self.data = self._dissolve(
                dissolve_field=self.vars.lkup_field_censuslink,
                fields_to_drop=[
                    self.vars.gis_uid_field,
                    self.vars.lkup_field_uid,
                ],
            )

        else:
            self.data = self._dissolve(dissolve_field=self.vars.gis_uid_field)
            self.vars.uid = self.vars.gis_uid_field

        self._write_geom_data("processed")  # improve by adding custom / variable name

    def _add_lkup(
        self,
    ):
        lkup_data = self.vars.lkup_read_library(
            self.vars.lkup_file,
            **self.vars.lkup_read_params,
        )

        # print(lkup_data.info())
        geom_lkup_merged = pd.merge(
            left=self.data,
            right=lkup_data,
            left_on=self.vars.gis_uid_field,
            right_on=self.vars.lkup_field_uid,
            how="left",
        )
        # print(geom_lkup_merged.info())


        lkup_cols_added = [col for col in lkup_data.columns if col != self.vars.lkup_field_uid]
        print(lkup_cols_added)

        geom_lkup_merged = geom_lkup_merged.dropna(subset = lkup_cols_added)
        for col in lkup_cols_added:
            geom_lkup_merged[col] = pd.to_numeric(
                geom_lkup_merged[col], downcast="integer"
                    )
        # print(geom_lkup_merged.info())
        
        # data.data = pd.merge(left = data.data, right = lkup, left_on = base_link, right_on = lkup_link, how = "left", )

        # data.data = data.data.dropna(subset=fieldtolist(fields)) #check

        return geom_lkup_merged

    def read_processed_geom(
        self,
    ):
        self.data = self._read_geometry_file()

    def get_geometry_data(
        self,
    ):
        self.data = self._read_geometry_file()

        if type(self.vars.gis_read_library) != utils.read_shp_geom:
            if self.vars.gis_lat_long == True:
                self.data = utils.process_coords(
                    self.data,
                    self.vars.gis_long_field,
                    self.vars.gis_lat_field,
                    self.vars.gis_projection,
                )

            else:
                "read geometry column of df"

        else:
            "do nothing"

        if self.vars.gis_field_to_clean != None:
            self.data, self.vars.gis_geocode_field = utils.clean_address_data(
                self.data,
                self.vars.gis_field_to_clean,
                self.vars.gis_standardisation_file,
                self.vars.gis_min_len,
                self.vars.cleaned_field_suffix,
                self.vars.gis_convert_non_ascii,
            )

        self._setgeomtype()

        self._write_geom_data("standardised")

        self.data = self.data.dropna(subset=self.vars.gis_geocode_field).copy()

        self._write_geom_data("standardised1")

    def _read_geometry_file(
        self,
    ):
        geometry_data = self.vars.gis_read_library(
            self.vars.gis_file,
            **self.vars.gis_read_params,
        )

        return geometry_data

    def _setgeomtype(
        self,
    ):
        geom_types = self.data.geom_type.value_counts()

        geoms = {
            point: ["Point"],
            line: [
                "LineString",
                "MultiLineString",
            ],
            polygon: [
                "Polygon",
                "MultiPolygon",
            ],
        }

        geom_l = []
        for k, v in geoms.items():
            if any(i in geom_types.index for i in v):
                geom_l.append(k)

        if len(geom_l) > 1:
            raise ValueError(f"Mixed geometry types: {geom_l}")
        else:
            self.vars.geom_type = geom_l[0]

    def _dissolve(
        self,
        dissolve_field,
        fields_to_drop=None,
    ):
        # self.data.geometry = self.data.geometry.buffer(0)
        geometry_data = self.data.dissolve(by=dissolve_field).reset_index()

        if fields_to_drop != None:
            geometry_data = geometry_data.drop(columns=fields_to_drop)

        # self.data = self.data.dissolve(by=dissolve_field).reset_index()
        return geometry_data.copy()

    def _write_geom_data(self, status):
        # output_dir = f"../data/output_art_revs1/{self.vars.census_country}/{self.vars.census_year}/{self.vars.geom_name}"
        # output_dir = utils.validate_paths(output_dir)
        # file_path = pathlib.PurePath(
        #     output_dir,
        #     f"{self.vars.census_country}_{self.vars.census_year}_{self.vars.geom_name}_{status}.tsv",
        # )

        # self.data.to_csv(
        #     file_path,
        #     **self.vars.gis_write_params,
        # )

        filename = f"{self.vars.census_country}_{self.vars.census_year}_{self.vars.geom_name}_{status}.tsv"
        output_path_components = [
            str(x)
            for x in [
                self.vars.output_path,
                self.vars.census_country,
                self.vars.census_year,
                self.vars.geom_name,
                filename,
            ]
        ]

        utils.write_df_to_file(
            self.data, output_path_components, self.vars.gis_write_params
        )

    def create_tgforlinking(
        self,
    ):
        # this will create a smaller dataset for linking and write output

        col_list = []
        col_list.extend(list(utils.flatten(self.vars.blockcols)))
        col_list.extend(
            [
                self.vars.gis_geocode_field,
                self.vars.item_per_unit_uid,
            ]
        )
        self.data = self.data[col_list].copy()
        self._write_geom_data("slim")


class TargetGeometry(Geometry):
    """For target geometries"""

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

    def assigntoboundary(
        self,
        boundary,
    ):
        self.vars.blockcols = boundary.vars.uid

        if self.vars.geom_type == point:
            self.data = gpd.sjoin(
                left_df=self.data,
                right_df=boundary.data,
                predicate="intersects",
                how="inner",
            ).drop(columns=["index_right"])

        elif self.vars.geom_type == line:
            self.data = gpd.overlay(
                df1=self.data, df2=boundary.data, how="identity", keep_geom_type=True
            ).dropna() #removes lines where no data is added (i.e. where street is outside boundary)
            
            #conparid and cen are made float because above there are nan values; convert back to int
            numeric_cols = self.data.select_dtypes(include="number").columns
            for col in numeric_cols:
                self.data[col] = pd.to_numeric(
                        self.data[col], downcast="integer"
                    )

            dissolve_cols = []
            if type(self.vars.blockcols) == list:
                dissolve_cols.extend(self.vars.blockcols)
            else:
                dissolve_cols.append(self.vars.blockcols)
            # print(boundary.data.info())

            dissolve_cols.append(self.vars.gis_uid_field)
            # print(dissolve_cols)
            # print(self.data.info())
            # print(boundary.data.info())
            self.data = self.data.dissolve(by=dissolve_cols, as_index=False)
            # print(boundary.data.info())
            # print(self.data.info())
            # self.data.to_csv("testing_non_unique_index.tsv", sep = "\t")

            # do I need to drop duplicates here????

    def dedup_streets(
        self,
    ):
        
        # Have added this in to avoid errors thrown/breaks when deduping a blank df; ideally not all
        # the code block would be wrapped in this if-else statement; but i want to keep the main py file
        # clean so haven't wrapped the dedup_streets function in an if-else there.
        if self.data.empty:
            pass
        else:

            if self.vars.dedup == False:
                self.data = self.data.drop_duplicates(
                    subset=self.vars.item_per_unit_uid, keep=False
                ).copy()

                self._write_geom_data("dedupedtest")

                # potentially dedup copies of street lines (multiple streets with same name in same parish/rsd)
            else:
                # dedup_fields = ["conparid_51-91", "CEN_1851", "final_text_alt"]
                # dedup_fields_flattened = list(utils.flatten(self.vars.blockcols))
                # print(dedup_fields_flattened)
                self.data["count"] = self.data.groupby(
                    self.vars.item_per_unit_uid
                ).transform("size")

                # self.data = self.data[self.data["count"] <= self.vars.dedup_max_points].copy()

                # dist_grouped = self.data.groupby(by=dedup_fields_flattened)["geometry"].apply(lambda x: utils.calc_dist(x)).reset_index(name="dist_calc")

                # print(self.data)
                print(self.data)
                print(self.data.info())
                dist_grouped = (
                    self.data[self.data["count"] <= self.vars.dedup_max_points]
                    .groupby(by=self.vars.item_per_unit_uid)["geometry"]
                    .apply(lambda x: utils.calc_dist(x))
                    .reset_index(name="dist_calc")
                )
                print(dist_grouped)
                print(dist_grouped.info())
                # print(dist_grouped)
                gdf_final = pd.merge(
                    left=self.data,
                    right=dist_grouped,
                    on=self.vars.item_per_unit_uid,
                    how="left",
                )
                print(gdf_final)
                print(gdf_final.info())

                # gdf_final["dist_calc"] = gdf_final["dist_calc"].fillna(0)
                gdf_final = gdf_final[
                    (gdf_final["dist_calc"] <= self.vars.dedup_max_distance_between_points)
                    | (gdf_final["dist_calc"].isna())
                ]
                # print(gdf_final)
                gdf_multi_only = gdf_final[
                    gdf_final.duplicated(subset=self.vars.item_per_unit_uid, keep=False)
                ]

                gdf_multi_only = (
                    gdf_multi_only.groupby(by=self.vars.item_per_unit_uid)[
                        self.vars.gis_uid_field
                    ]
                    .apply(lambda x: str(x.to_list()))
                    .reset_index(name=f"{self.vars.gis_uid_field}_removed")
                )
                self.data = pd.merge(
                    left=gdf_final,
                    right=gdf_multi_only,
                    on=self.vars.item_per_unit_uid,
                    how="left",
                )
                print(len(self.data))

                self._write_geom_data("deduped1")

                self.data = (
                    self.data[self.data["count"] <= self.vars.dedup_max_points]
                    .drop_duplicates(subset=self.vars.item_per_unit_uid, keep="first")
                    .copy()
                )

                self._write_geom_data("deduped2")

                print(len(self.data))

    def create_uid_of_geocode_field(
        self,
    ):
        """Groups field to geocode by boundary fields to create unique groups of addresses in each boundary. Assigns uid to each address"""
        # groupby_cols.extend([x for x in utils.flatten(self.vars.boundaries_field)])
        # groupby_cols.append(self.vars.gis_geocode_field)

        groupby_cols = []
        groupby_cols.extend([x for x in utils.flatten(self.vars.blockcols)])
        groupby_cols.append(self.vars.gis_geocode_field)
        self.data[self.vars.item_per_unit_uid] = self.data.groupby(
            groupby_cols
        ).ngroup()
        # self.data.to_csv("testing_non_unique_index_afteruid.tsv", sep = "\t", columns = ["conparid_01-11", "CEN_1911", "nameTOID", "name1","name1_alt", "street_uid"])
        # print(self.data.info())

class Boundary(Geometry):
    """
    For boundaries only"""

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

    def merge_boundaries(
        self,
        boundary_list,
    ):
        boundary_uids = []
        boundary_uids.append(self.vars.uid)

        base_bndry_name = self.vars.geom_name
        merged_boundaries_name = (
            base_bndry_name + "_" + "_".join([x.vars.geom_name for x in boundary_list])
        )
        merged_boundaries = Boundary(
            Geometry_vars(
                geom_name=merged_boundaries_name,
                census_year=self.vars.census_year,
                census_country=self.vars.census_country,
                gis_write_params=self.vars.gis_write_params,
            )
        )

        for boundary in boundary_list:
            boundary_uids.append(boundary.vars.uid)
            merged_boundaries.data = gpd.overlay(
                self.data, boundary.data, how=self.vars.merge_method, keep_geom_type=True
            )

        merged_boundaries._setgeomtype()
        merged_boundaries.vars.uid = boundary_uids
        # print(merged_boundaries.vars.uid)
        merged_boundaries._write_geom_data("processed")

        return merged_boundaries
