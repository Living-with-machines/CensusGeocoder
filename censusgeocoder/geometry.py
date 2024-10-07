import geopandas as gpd
import pandas as pd
from dataclasses import dataclass, field
import utils

point = "point"
line = "line"
polygon = "polygon"


@dataclass
class Geometry_vars:
    """Base Class for storing geometry variables


    Attributes
    ----------

    geom_name: str
        Name of Geometry

    census_year: int
        Year of census, e.g. 1851

    census_country: str
        Census country, e.g. EW or Scotland

    gis_file: str
        Path to geometry file.

    gis_uid_field: str
        Name of pd.Series containing geometry uid.

    gis_read_params: dict
        Parameters for reading `gis_file` passed to read library specified in `utils.get_readlibrary()`.

    lkup_file: str
        Path to lookup file

    lkup_field_uid: str
        Name of pd.Series containing uid of lkup.

    lkup_field_censuslink: str
        Name of pd.Series containing lookup values linking lkup to census.

    lkup_read_params: dict
        Parameters for reading `lkup_file` passed to read library specified in `utils.get_readlibrary()`.

    gis_write_params: dict
        Paramaters for writing geometry data passed to `utils.write_df_to_file()`.

    output_path: str
        Directory to write output files to.

    output_filetype: str
        Output file suffix, e.g. ".tsv".

    gis_lat_long: bool
        Indicates if geometry data stored in lat/long format across two columns.

    gis_long_field: str
        Name of pd.Series containing longitude data.

    gis_lat_field: str
        Name of pd.Series containing latitude data.

    gis_projection: str
        CRS Projection of the geometry data, e.g. "EPSG:27700"

    process
    ##############Need to add.



    geom_type: str:
        Type of geometry: Point, Line, Polygon etc. Set by inspecting geometry data, see `_setgeomtype()`.

    uid: str
        ####Unsure need to check


    """

    geom_name: str
    census_year: int
    census_country: str
    gis_file: str = None

    gis_uid_field: str = None
    gis_read_params: dict = None

    lkup_file: str = None
    lkup_field_uid: str = None
    lkup_field_censuslink: str = None
    lkup_read_params: dict = None

    gis_write_params: dict = None

    output_path: str = "../data/output"
    output_filetype: str = ".tsv"

    gis_lat_long: bool = False
    gis_long_field: str = None
    gis_lat_field: str = None
    gis_projection: str = None

    process: bool = True

    geom_type: str = field(init=False)
    uid: str | list = field(init=False)

    def __post_init__(self):
        if self.process is not True:
            self.geom_type = None  # remove?
            self.uid = None  # remove?


@dataclass
class TargetGeometry_vars(Geometry_vars):
    """Class for storing target geometry variables

    Attributes
    ----------

    gis_field_to_clean: str
        Name of pd.Series containing field (e.g. Address data) to clean and standardise.

    gis_standardisation_file: str
        Path to standardisation file for cleaning and standardising `gis_field_to_clean`.

    gis_min_len: int
        Minimum length in characters of entries in `gis_geocode_field` can be.

    cleaned_field_suffix: str
        Suffix to add to `gis_field_to_clean` after cleaning and standardising.

    dedup: bool
        Indicates whether to deduplicate entries in geometry data or not.

    dedup_max_points: int
         For point geometries only - max number of points in a geo-blocking unit before they are considered duplicates.
         For more information, see Documentation about processing GB1900 data.

    dedup_max_distance_between_points: int
        Distance between points used to determine if points refer to same entity (e.g. a long road) or different entities.
        For more information, see Documentation about processing GB1900 data.

    item_per_unit_uid: str
        Unique identifier of each entity in the target geometry dataset. Calculated for each geo-blocking unit, so streets
        that span multiple geo-blocking units will have different `item_per_unit_uid` values.

    gis_convert_non_ascii: bool
        Indicates whether non ascii characters should be converted or not.
        See documentation about converting Welsh placenames in GB1900.

    gis_geocode_field: str
        Name of pd.Series in geometry data that contains address data to link to census addresses.

    blockcols: str | list
        Name or list of names of pd.Series columns containing the geo-blocking ids, e.g. ConParID, CEN_1851 etc

    """

    gis_field_to_clean: str = None
    gis_standardisation_file: str = None
    gis_min_len: int = None
    cleaned_field_suffix: str = None

    dedup: bool = False
    dedup_max_points: int = None
    dedup_max_distance_between_points: int = None

    item_per_unit_uid: str = "tg_uid"

    gis_convert_non_ascii: bool = False
    gis_geocode_field: str = None

    blockcols: str | list = None


@dataclass
class Boundary_vars(Geometry_vars):
    """Class for storing boundary variables"""

    pass


class Geometry:
    """Base Geometry Class

    Attributes
    ----------

    vars: `Geometry_vars`
        Instance of `Geometry_vars` storing variables for reading and processing geometry data.

    Methods
    -------


    `get_geometry_data()`
        Reads geometry data

    `process()`
        Processes geometry data by adding lookup if available and dissolving geometries on specified uid field.
        

    Notes
    -----

    Private methods:

    `_addvars()`
        Checks vars is type `Geometry_vars`

    `_setgeomtype()`
        Checks geometry type of geometry data

    `_write_geom_data()`
        Writes geometry data to file.


    """

    def __init__(self, vars):
        self._addvars(vars)

    def _addvars(self, vars):
        """Checks vars is type `Geometry_vars` and assigns to self.vars. If not raise TypeError.

        Parameters
        ----------

        vars: `Geometry_vars`
            A `Geometry_vars` instance containing geometry variables.
        """
        if type(vars) is Geometry_vars:
            self.vars = vars
        else:
            raise TypeError(
                f"vars is {vars.__class__.__name__} must be {Geometry_vars.__name__}"
            )

    def get_geometry_data(
        self,
    ):
        """Reads geometry data into a gpd.GeoDataFrame, checks if geometries stored in 2 lat/long columns - creates a WKT geometry column if so;
        also sets geometry type (which determines boundary assignment method for target geometries).

        """

        self.data = utils.read_file(
            self.vars.gis_file,
            self.vars.gis_read_params,
        )

        if (
            self.vars.gis_lat_long == True
        ):  # checks if geometry data in latlong columns; if true process to convert to wkt geom column
            self.data = utils.process_coords(
                self.data,
                self.vars.gis_long_field,
                self.vars.gis_lat_field,
                self.vars.gis_projection,
            )

        self._setgeomtype()

    def process(
        self,
    ):
        """Processes geometry data by adding lookup if available and dissolving geometries on specified uid field."""
        if self.vars.lkup_file is not None:

            self.data = utils.add_lkup(
                data=self.data,
                lkup_file=self.vars.lkup_file,
                lkup_params=self.vars.lkup_read_params,
                left_on=self.vars.gis_uid_field,
                right_on=self.vars.lkup_field_uid,
                fields_to_drop=[
                    self.vars.gis_uid_field,
                    self.vars.lkup_field_uid,
                ],
            )

            self.vars.uid = self.vars.lkup_field_censuslink

            self.data = self.data.dissolve(
                by=self.vars.lkup_field_censuslink, as_index=False
            )

        else:
            self.data = self.data.dissolve(by=self.vars.gis_uid_field, as_index=False)
            self.vars.uid = self.vars.gis_uid_field

        self._write_geom_data(
            "processed",  # specifies part of output name to identify this file
            self.vars.gis_write_params,
        )

    def read_processed_geom(  # TO DEAL WITH
        self,
    ):
        self.data = self._read_geometry_file()  # change to utils read file

    def _setgeomtype(
        self,
    ):
        """Checks geometry type of geometry data. Raises ValueError if mixed types since CensusGeocoder only works for geometry datasets of a single type.
        Sets geometry type to either 'point', 'line' or 'polygon'. Used to determine boundary assignment operations for target geometry datasets.

        """
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

    def _write_geom_data(self, status, params):
        """Writes geometry data to file.

        Parameters
        ----------

        status: str
            Description of output file, e.g. 'processed' indicating stage of geocoding process that file is from.

        params: dict
            Dictionary containing parameters to pass to `utils.write_df_to_file()` used by `pd.to_csv()`

        """

        filename = f"{self.vars.census_country}_{self.vars.census_year}_{self.vars.geom_name}_{status}{self.vars.output_filetype}"
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

        utils.write_df_to_file(self.data, output_path_components, params)


class TargetGeometry(Geometry):
    """Class for target geometry processes that extends base `Geometry` class.

    Methods
    -------

    `assigntoboundary()`
        Assigns each entity in the target geometry dataset to a boundary in the boundary dataset

    `dedup_addresses()`
        Deduplicates addresses in geometry dataset.

    `create_uid_of_geocode_field()`
        Assigns uid to each address by geo-blocking unit.

    `create_tgforlinking()`
        Writes to output file slim version of target geometry dataset with only fields/values needed by `census.geocode()`

    `clean_tg()`
        Cleans target geometry dataset.

    Notes
    -----

    Private methods:

    `_addvars()`
        Checks vars is type `TargetGeometry_vars`

    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(*args, **kwargs)

    def _addvars(self, vars):
        """Checks vars is type `TargetGeometry_vars` and assigns to self.vars. If not raise TypeError.

        Parameters
        ----------

        vars: `TargetGeometry_vars`
            A `TargetGeometry_vars` instance containing target geometry variables.

        """

        if type(vars) is TargetGeometry_vars:
            self.vars = vars
        else:
            raise TypeError(
                f"vars is {vars.__class__.__name__} must be {TargetGeometry_vars.__name__}"
            )

    def assigntoboundary(
        self,
        boundary,
    ):
        """Assigns each entity in the target geometry dataset to a boundary in the boundary dataset

        Parameters
        ----------

        boundary: `Boundary`
            An instance of `Boundary` class.


        Notes
        -----

        Method of assigning target geometry to boundary depends on geometry type of target geometry. Point data is assigned by intersection with boundary,
        line data assigned by overlaying and segmenting line on boundary borders to create new geometries when lines cross boundaries. See Documentation for more information.

        """
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
            ).dropna()  # removes lines where no data is added (i.e. where street is outside boundary)

            # uids like ConParID and CEN are made float because above there are nan values; convert back to int
            numeric_cols = self.data.select_dtypes(include="number").columns
            for col in numeric_cols:
                self.data[col] = pd.to_numeric(self.data[col], downcast="integer")

            dissolve_cols = []
            if type(self.vars.blockcols) == list:
                dissolve_cols.extend(self.vars.blockcols)
            else:
                dissolve_cols.append(self.vars.blockcols)

            dissolve_cols.append(self.vars.gis_uid_field)

            self.data = self.data.dissolve(by=dissolve_cols, as_index=False)

    def dedup_addresses(
        self,
    ):
        """Deduplicates addresses in geometry dataset - primarily intended to deduplicating points in GB1900

        Notes
        -----

        When dedup is False, it drops any duplicates in the address field. When dedup is True, it calculates the distance between entities,
        which are dropped when if there are more than number specified in `vars.dedup_max_points`. When number is less than this, checks distance between
        entities is less than `vars.dedup_max_distance_between_points`, where they exceed distance they are dropped, where less, keep one (first - i.e. abitrary).

        This code could be improved in future by removing the 'deduped_nodistcalc' since removing streets/addresses with the same name leads to poorer quality matches
        on other streets, rather than duplicate matches to possibly correct street(s)/address(es) that are handled by `geocode._process_results()`.
        """

        if self.data.empty:
            pass
        else:

            if self.vars.dedup is False:

                self.data = self.data.drop_duplicates(
                    subset=self.vars.item_per_unit_uid, keep=False
                ).copy()

                self._write_geom_data(
                    "deduped_nodistcalc", self.vars.gis_write_params
                )  # should remove this because it removes valid matches and increases false positive rate slightly

            else:

                self.data["count"] = self.data.groupby(
                    self.vars.item_per_unit_uid
                ).transform("size")

                dist_grouped = (
                    self.data[self.data["count"] <= self.vars.dedup_max_points]
                    .groupby(by=self.vars.item_per_unit_uid)["geometry"]
                    .apply(lambda x: utils.calc_dist(x))
                    .reset_index(name="dist_calc")
                )

                gdf_final = pd.merge(
                    left=self.data,
                    right=dist_grouped,
                    on=self.vars.item_per_unit_uid,
                    how="left",
                )

                gdf_final = gdf_final[
                    (
                        gdf_final["dist_calc"]
                        <= self.vars.dedup_max_distance_between_points
                    )
                    | (gdf_final["dist_calc"].isna())
                ]

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

                self._write_geom_data("deduped_distcount", self.vars.gis_write_params)

                self.data = (
                    self.data[self.data["count"] <= self.vars.dedup_max_points]
                    .drop_duplicates(subset=self.vars.item_per_unit_uid, keep="first")
                    .copy()
                )

                self._write_geom_data("deduped_distcount2", self.vars.gis_write_params)

    def create_uid_of_geocode_field(
        self,
    ):
        """Assigns uid to each address by grouping field to geocode by boundary fields to create unique groups of addresses in each geo-blocking unit."""

        groupby_cols = []
        groupby_cols.extend([x for x in utils.flatten(self.vars.blockcols)])
        groupby_cols.append(self.vars.gis_geocode_field)
        self.data[self.vars.item_per_unit_uid] = self.data.groupby(
            groupby_cols
        ).ngroup()

    def clean_tg(
        self,
    ):
        """Cleans target geometry dataset, drops resulting rows of data with NaNs after cleaning, writes to output file."""

        if self.vars.gis_field_to_clean is not None:
            self.data, self.vars.gis_geocode_field = utils.clean_address_data(
                self.data,
                self.vars.gis_field_to_clean,
                self.vars.gis_standardisation_file,
                self.vars.gis_min_len,
                self.vars.cleaned_field_suffix,
                self.vars.gis_convert_non_ascii,
            )

        self.data = self.data.dropna(
            subset=self.vars.gis_geocode_field
        ).copy()  # cleaning the dataset might result in NaN values (e.g. blank entries or spaces now NaN), drop these.

        self._write_geom_data("standardised", self.vars.gis_write_params)

    def create_tgforlinking(
        self,
    ):
        """Writes to output file slim version of target geometry dataset with only fields/values needed by `census.geocode()`"""

        col_list = []
        col_list.extend(list(utils.flatten(self.vars.blockcols)))
        col_list.extend(
            [
                self.vars.gis_geocode_field,
                self.vars.item_per_unit_uid,
            ]
        )
        self.data = self.data[col_list].copy()
        self._write_geom_data("slim", self.vars.gis_write_params)


class Boundary(Geometry):
    """
    For boundaries only

    Methods
    -------

    `merge_boundaries()`
        Merges boundaries, returns `Boundary` class containing merged boundaries data.

    Notes
    -----

    Private methods:

    `_addvars()`
        Checks vars is type `Boundary_vars`"""

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

    def _addvars(self, vars):
        """Checks vars is type `Boundary_vars` and assigns to self.vars. If not raise TypeError.

        Parameters
        ----------

        vars: `Boundary_vars`
            A `Boundary_vars` instance containing boundary geometry variables.

        """

        if type(vars) is Boundary_vars:
            self.vars = vars
        else:
            raise TypeError(
                f"vars is {vars.__class__.__name__} must be {Boundary_vars.__name__}"
            )

        self.merge_method = "intersection"  # sets merge method used for combining more than one boundary dataset

    def merge_boundaries(
        self,
        boundary_list,
    ):
        """Merges boundaries, returns `Boundary` class containing merged boundaries data

        Parameters
        ----------

        boundary_list: list
            List of boundaries to merge to base boundary

        Returns
        -------

        merged_boundaries: `Boundary`
            `Boundary` class containing merged boundaries data.

        """
        boundary_uids = []
        boundary_uids.append(self.vars.uid)

        base_bndry_name = self.vars.geom_name
        merged_boundaries_name = (
            base_bndry_name + "_" + "_".join([x.vars.geom_name for x in boundary_list])
        )
        merged_boundaries = Boundary(
            Boundary_vars(
                geom_name=merged_boundaries_name,
                census_year=self.vars.census_year,
                census_country=self.vars.census_country,
                gis_write_params=self.vars.gis_write_params,
                output_path=self.vars.output_path,
            )
        )

        for boundary in boundary_list:
            boundary_uids.append(boundary.vars.uid)
            merged_boundaries.data = gpd.overlay(
                self.data,
                boundary.data,
                how=self.merge_method,
                keep_geom_type=True,
            )

        merged_boundaries._setgeomtype()
        merged_boundaries.vars.uid = boundary_uids

        merged_boundaries._write_geom_data("processed", self.vars.gis_write_params)

        return merged_boundaries
