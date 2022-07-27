from dataclasses import dataclass, fields, field
import pathlib
import pandas as pd


def validate_sim_thresh(sim_thresh):
    """Checks that similarity threshold is between 0 and 1."""
    if 0 <= sim_thresh <= 1:
        pass
    else:
        msg = f"Threshold must be between 0 and 1, you specified {sim_thresh}"
        raise ValueError(msg)


def validate_sep(sep):
    """Checks that separator provided is valid by
    comparing against commonly used seperators."""
    seplist = ["\t", ",", "|"]
    if sep not in seplist:
        msg = (
            f"Are you sure '{sep}' is the correct separator, "
            f"it's not one of these common ones {seplist}"
        )
        raise ValueError(msg)


def validate_quoting(quoting):
    """Checks quoting value passed to pandas or dask read_csv is valid."""
    if quoting not in [0, 1, 2, 3]:
        msg = (
            "Quoting parameter must be either 0, 1, 2, or 3. "
            "See pandas read_csv doc for more info."
        )
        raise ValueError(msg)


def first_validate(instance):
    """Checks that datatype specified matches datatype given."""
    for fieldx in fields(instance):
        attr = getattr(instance, fieldx.name)
        if not isinstance(attr, fieldx.type):
            msg = (
                f"Field '{fieldx.name}' is of type "
                f"{type(attr)}, should be {fieldx.type}"
            )
            raise ValueError(msg)


def validate_paths(filepath):
    """Checks the filepaths are valid. If not, returns an error"""

    new_path = pathlib.Path(filepath)
    if not new_path.exists():
        msg = f"'{new_path}' is not a valid file path."
        raise ValueError(msg)


def validate_projection(projection):
    """Checks if specified projection is an authority string
    (eg “EPSG:4326”). Although geopandas projection will accept
    other formats e.g. the int 4326, for ease of data validation
    projection must be specified in the format "EPSG:****"
    """
    projection_split = projection.split(":")
    authority_code_list = ["4326", "27700", "3857"]  # add to this if more needed
    if projection_split[0] != "EPSG" or projection_split[1] not in authority_code_list:

        msg = (
            f"Projection '{projection}' is not a valid authority string; must be "
            f"in the format like 'EPSG:4326'. Currently only codes '4326', '27700', "
            f"or '3857' are accepted"
        )
        raise ValueError(msg)


def validate_partition(partition_field, col_list):
    """Checks if partition field specified in input
    is in the list of given census columns"""
    if partition_field not in col_list:
        msg = (
            f"Partition field '{partition_field}' not in list"
            f" of columns '{col_list}'"
        )
        raise ValueError(msg)


@dataclass
class Comparison_params:
    """A class with string comparison parameters.

    Attributes
    ----------
    sim_thresh: str
        The minimum accepted threshold for fuzzy string matching comparisons
        to be considered a match.
    
    string_comp_alg: str
        The algorithm used for fuzzy string matching.
    """

    sim_thresh: float
    string_comp_alg: str

    def __post_init__(self):
        first_validate(self)
        validate_sim_thresh(self.sim_thresh)


@dataclass
class Census_fields:
    """A class storing census fields shared by both England and Wales and Scotland.

    Attributes
    ----------
    uid: str
        The name of the unique id field for each person in census data, e.g. `RecID`.

    address: str
        The name of the address field containing people's addresses.

    parid: str
        The name of the field containing the `ParID` census variable.

    county: str
        The name of the field containing the `RegCnty` or Registration County variable.
    """

    uid: str
    address: str
    parid: str
    county: str

    def __post_init__(self):
        first_validate(self)

    def list_cols(self):
        col_list = []
        for x in fields(self):
            attr = getattr(self, x.name)
            if attr != "":
                col_list.append(attr)
        return col_list


@dataclass
class EWcensus_fields(Census_fields):
    """A class storing census fields valid only for England and Wales.

    Attributes
    ----------
    conparid: str
        The name of the field containing the `Consistent parish ID` census variable.
    """

    conparid: str

    def __post_init__(self):
        first_validate(self)


@dataclass
class SCOTcensus_fields(Census_fields):
    """A class storing census fields valid only for Scotland."""

    pass


@dataclass
class Csv_params:
    """A class storing parameters to read census data to pass to dask
    and pandas read_csv.

    Attributes
    ----------
    sep: str
        The value used to delimit fields in the file, e.g. "\t", a tab.
    
    encoding: str
        The file encoding, e.g. 'utf-8'.
    
    blocksize: str
        The number of bytes by which to cut up larger files - see dask read_csv
        documentation.

    quoting: int
        Indicates if / how quotation marks are used in the csv file, see read_csv
        documentation.

    na_values: str
        Values representing null data in the file. see read_csv documentation.
    """

    sep: str
    encoding: str
    blocksize: str  # may want to change this in future to include int
    quoting: int
    na_values: str  # may want to change this in future to include list

    def __post_init__(self):
        first_validate(self)
        validate_sep(self.sep)
        validate_quoting(self.quoting)


@dataclass
class Census_output_params:
    """A class storing parameters to output processed census data and other outputs.

    Attributes
    ----------
    partition_on: str
        The value on which to create directory-based partitioning by splitting files.
        See dask to_parquet documentation.
    
    new_uid: str
        The name of the new unique id field used for storing unique census addresses.

    sep: str
        The value used to delimit fields in the file, e.g. "\t", a tab.

    index: bool
        Indicates if the dataframe index should be written to output file.
        See pandas to_csv documentation.

    filetype: str
        File extension for delimited text file e.g. '.csv' or '.tsv'.
        Passed to pandas to_csv.
    """

    partition_on: str
    new_uid: str
    sep: str
    index: bool
    filetype: str

    def __post_init__(self):
        first_validate(self)


@dataclass
class Censusconfiguration:
    """A class storing parameters for a specific year and country of the census.

    Attributes
    ----------
    country: str
        Census country, to differentiate between the census files for England and Wales
        and Scotland.
    
    year: int
        Year of census, e.g 1851

    runtype: bool
        Specifies if census geocoding should be run or not.

    census_file: str
        Path to the census file.
    
    census_fields: Dataclass
        Dataclass containing the fieldnames from the census data.

    csv_params: Dataclass
        Dataclass storing parameters to read census data to pass to dask
        and pandas read_csv.

    census_standardisation_file: str
        Path to standardisation json file containing regex patterns to apply to
        census address field.
    
    comparison_params: Dataclass
        Dataclass with string comparison parameters

    census_output_parmas: Dataclass
        Dataclass storing parameters to output processed census data and other outputs.

    Methods
    -------
    validate_censuscols()
        Checks that values passed to `census_fields` are valid columns in
        the `census_file`. Raises an error message if one or more columns is
        not present.

    """

    country: str
    year: int
    runtype: bool
    census_file: str
    census_fields: Census_fields
    csv_params: Csv_params  # parameters passed to dask read_csv

    census_standardisation_file: str
    comparison_params: Comparison_params
    census_output_params: Census_output_params

    def __post_init__(self):

        validate_paths(self.census_file)
        if isinstance(self.census_fields, dict):
            if self.country == "EW":
                self.census_fields = EWcensus_fields(**self.census_fields)
            elif self.country == "SCOT":
                self.census_fields = SCOTcensus_fields(**self.census_fields)

        if isinstance(self.csv_params, dict):
            self.csv_params = Csv_params(**self.csv_params)
        if isinstance(self.census_output_params, dict):
            self.census_output_params = Census_output_params(
                **self.census_output_params
            )
        if isinstance(self.comparison_params, dict):
            self.comparison_params = Comparison_params(**self.comparison_params)
        self.validate_censuscols(
            self.census_fields,
            self.census_file,
            self.csv_params,
            self.year,
            self.country,
        )
        first_validate(self)
        validate_partition(
            self.census_output_params.partition_on, self.census_fields.list_cols()
        )

    def validate_censuscols(
        self, census_fields, census_file, csv_params, year, country
    ):
        """Checks that census fields given in input are valid columns
        in the census file"""
        col_list = []
        for fieldx in fields(census_fields):
            attr = getattr(census_fields, fieldx.name)
            col_list.append(attr)

        col_only_df = pd.read_csv(
            census_file, sep=csv_params.sep, encoding=csv_params.encoding, nrows=0,
        )

        cols_in_df = col_only_df.columns.to_list()
        missing_cols = [i for i in col_list if i not in cols_in_df]

        if missing_cols != []:
            msg = (
                f"The following columns {missing_cols} are not present"
                f" in the census file for {country} {year}"
            )
            raise ValueError(msg)


@dataclass
class Parish_gis_config:
    """A class storing parameters for England and Wales Parish GIS Boundary Data.

    Attributes
    ----------
    filepath: str
        Path to England and Wales Parish GIS Boundary Data.
    
    projection: str
        Projection string to pass to geopandas when reading data or setting crs.
        See `validate_projection()` for valid format.

    id_field: str
        Name of the unique id field.
    """

    filepath: str
    projection: str
    id_field: str

    def __post_init__(self):
        validate_projection(self.projection)
        validate_paths(self.filepath)


@dataclass
class Rsd_gis_config:
    """A class storing parameters for England and Wales Registration Sub-District
    (RSD) GIS Boundary Data.

    Attributes
    ----------
    filepath: str
        Path to England and Wales Parish GIS Boundary Data.
    
    projection: str
        Projection string to pass to geopandas when reading data or setting crs.
        See `validate_projection()` for valid format.
    """

    filepath: str
    projection: str

    def __post_init__(self):
        validate_paths(self.filepath)
        validate_projection(self.projection)


@dataclass
class Rsd_dictionary_config:
    """A class storing parameters for England and Wales Registration Sub-District
    (RSD) Lookup Table.

    Attributes
    ----------
    filepath: str
        Path to England and Wales Parish GIS Boundary Data.

    cen_parid_field: str
        Name of the field containing `ParID` variable from I-CeM.

    rsd_id_field: str
        Name of the unique rsd id field, e.g. 'CEN_1881'.

    encoding: str
        The file encoding, e.g. 'utf-8'.

    sep: str
        The value used to delimit fields in the file, e.g. "\t", a tab.
    
    quoting: int
        Indicates if / how quotation marks are used in the csv file, see read_csv
        documentation.
    """

    filepath: str
    cen_parid_field: str
    rsd_id_field: str
    encoding: str
    sep: str
    quoting: int

    def __post_init__(self):
        first_validate(self)
        validate_paths(self.filepath)
        validate_sep(self.sep)
        validate_quoting(self.quoting)


@dataclass
class Parish_icem_lkup_config:
    """A class storing parameters for England and Wales Parish Lookup Table.

    Attributes
    ----------
    filepath: str
        Path to England and Wales Parish GIS Boundary Data.

    sheet: str
        Name of the sheet of the Excel Spreadsheet where the data is located.

    ukds_id_field: str
        Name of the unique id field.

    na_values: str
        Value indicating null values in data.

    conparid51_91_field: str
        Name of the field containing the consistent parish ids for 1851 to 1891.

    conparid01_11_field: str
        Name of the field containing the consistent parish ids for 1901 to 1911.

    conparid: str
        Appropriate value from either `conparid51_91_field` or `conparid01_11_field`
        for the specified census year.

    Methods
    -------
    set_conparid()
        Sets the correct conparid field name based on the specified census year.
    """

    filepath: str
    sheet: str
    ukds_id_field: str
    na_values: str
    conparid51_91_field: str
    conparid01_11_field: str
    conparid: str = field(init=False)

    def __post_init__(self):
        validate_paths(self.filepath)

    def set_conparid(self, census_year):
        if census_year < 1901:
            self.conparid = self.conparid51_91_field
        else:
            self.conparid = self.conparid01_11_field
        return self.conparid


@dataclass
class EW_configuration:
    """A class for storing parameters for England and Wales geocoding.
    
    Attributes
    ----------
    year: int
        Census year

    parish_gis_config: Dataclass
        Dataclass storing parameters for England and Wales Parish GIS Boundary Data.

    rsd_gis_config: Dataclass
        Dataclass storing parameters for England and Wales Registration Sub-District
        (RSD) GIS Boundary Data.

    rsd_dictionary_config: Dataclass
        Dataclass storing parameters for England and Wales Registration Sub-District
        (RSD) Lookup Table.

    parish_icem_lkup_config: Dataclass
        Dataclass storing parameters for England and Wales Parish Lookup Table.
"""

    year: int
    parish_gis_config: Parish_gis_config
    rsd_gis_config: Rsd_gis_config
    rsd_dictionary_config: Rsd_dictionary_config
    parish_icem_lkup_config: Parish_icem_lkup_config

    def __post_init__(self):
        if isinstance(self.parish_gis_config, dict):
            self.parish_gis_config = Parish_gis_config(**self.parish_gis_config)
        if isinstance(self.rsd_gis_config, dict):
            self.rsd_gis_config = Rsd_gis_config(**self.rsd_gis_config)
        if isinstance(self.rsd_dictionary_config, dict):
            self.rsd_dictionary_config = Rsd_dictionary_config(
                **self.rsd_dictionary_config[f"{str(self.year)}"]
            )
        if isinstance(self.parish_icem_lkup_config, dict):
            self.parish_icem_lkup_config = Parish_icem_lkup_config(
                **self.parish_icem_lkup_config
            )

        Parish_icem_lkup_config.set_conparid(self.parish_icem_lkup_config, self.year)


@dataclass
class Data_fields:

    uid_field: str
    address_field: str
    geometry_field: str = ""
    long_field: str = ""
    lat_field: str = ""

    def list_cols(self):
        col_list = []
        for x in fields(self):
            attr = getattr(self, x.name)
            if attr != "":
                col_list.append(attr)
        return col_list


@dataclass
class Output_params:
    file_type: str
    crs: str
    driver: str


@dataclass
class Target_geom:
    path_to_geom: str
    projection: str
    file_type: str
    geom_type: str
    data_fields: Data_fields
    output_params: Output_params
    standardisation_file: str
    query_criteria: str
    filename_disamb: str = ""
    geometry_format: str = ""
    encoding: str = ""
    sep: str = ","

    def __post_init__(self):
        if isinstance(self.data_fields, dict):
            self.data_fields = Data_fields(**self.data_fields)
        if isinstance(self.output_params, dict):
            self.output_params = Output_params(**self.output_params)

        validate_projection(self.projection)

        validate_paths(self.path_to_geom)
        validate_sep(self.sep)


@dataclass
class General:
    """A Class with general parameters"""

    output_data_path: str
    # linked_subdir: str
    # duplicate_subdir: str

    # linked_outputdir: pathlib.Path = field(init=False)
    # duplicate_outputdir: pathlib.Path = field(init=False)

    def __post_init__(self):
        validate_paths(self.output_data_path)

        # self.linked_outputdir = pathlib.Path(self.output_data_path
        #  + self.linked_subdir)
        # pathlib.Path(self.linked_outputdir).mkdir(parents=True, exist_ok=True)

        # self.duplicate_outputdir = pathlib.Path(
        #     self.output_data_path + self.duplicate_subdir
        # )
        # pathlib.Path(self.duplicate_outputdir).mkdir(parents=True, exist_ok=True)


@dataclass
class Boundary_lkup_config:
    filepath: str
    parid_field: str
    uid: str = field(init=False)
    sheet: str = field(init=False)

    def set_sheet(self, census_year):
        self.sheet = str(census_year)
        pass

    def set_uid(self, uid_value):
        self.uid = uid_value
        pass

    def __post_init__(self):
        validate_paths(self.filepath)
        first_validate(self)


@dataclass
class Boundary_config:
    filepath: str
    uid: str
    projection: str

    def __post_init__(self):
        first_validate(self)
        validate_paths(self.filepath)


@dataclass
class SCOT_configuration:
    year: int
    pre1891_boundary_config: dict
    post1891_boundary_config: dict
    boundary_lkup_config: Boundary_lkup_config
    boundary_config: Boundary_config = field(init=False)

    def __post_init__(self):
        if self.year < 1891:

            if isinstance(self.pre1891_boundary_config, dict):
                self.boundary_config = Boundary_config(**self.pre1891_boundary_config)
        else:
            if isinstance(self.post1891_boundary_config, dict):
                self.boundary_config = Boundary_config(**self.post1891_boundary_config)
        if isinstance(self.boundary_lkup_config, dict):
            self.boundary_lkup_config = Boundary_lkup_config(
                **self.boundary_lkup_config
            )

        Boundary_lkup_config.set_sheet(self.boundary_lkup_config, self.year)
        Boundary_lkup_config.set_uid(
            self.boundary_lkup_config, self.boundary_config.uid
        )


def validate_configs(config_dict):
    """Validates full contents of input_config file before running geocoder"""
    General(**config_dict["general"])
    for x, y in config_dict["census_config"].items():
        census_configuration = Censusconfiguration(**y)
        if census_configuration.country == "EW":
            EW_configuration(census_configuration.year, **config_dict["ew_config"])
        elif census_configuration.country == "SCOT":
            pass
    for geom, geom_config in config_dict["target_geoms"].items():
        Target_geom(**geom_config)
    pass


def create_outputdirs(*args):
    """Set the output directory in the format e.g.
    `data/output/1901/EW/`. Checks if output directory exists,
    if it doesn't it creates a directory.

    Returns
    ----------
    output_dir: str
        Path to output directory.
    """
    args1 = [str(arg) for arg in args]
    output_dir = pathlib.Path(*args1)
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    return output_dir

