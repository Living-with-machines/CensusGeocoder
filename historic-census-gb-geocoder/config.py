from dataclasses import dataclass, fields
import pathlib
import pandas as pd


def validate_sep(sep):
    """Checks that separator provided is valid by
    comparing against commonly used seperators"""
    seplist = ["\t", ",", "|"]
    if sep not in seplist:
        msg = (
            f"Are you sure '{sep}' is the correct separator, "
            f"it's not one of these common ones {seplist}"
        )
        raise ValueError(msg)


def validate_quoting(quoting):
    if quoting not in [0, 1, 2, 3]:
        msg = (
            "Quoting parameter must be either 0, 1, 2, or 3. "
            "See pandas read_csv doc for more info."
        )
        raise ValueError(msg)


def first_validate(instance):
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


def validate_censuscols(census_fields, census_file, csv_params):
    """Checks that census fields given in input are valid columns in the census file"""
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
        msg = f"The following columns {missing_cols} are not present in the census file"

        raise ValueError(msg)


def validate_projection(projection):
    """Checks if specified projection is an authority string
    (eg “EPSG:4326”). Although geopandas projection will accept
    other formats e.g. the int 4326, for ease of data validation
    projection must be specified in the format "EPSG:****"
    """
    projection_split = projection.split(":")
    authority_code_list = ["4326", "27700", "3857"]
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
        msg = f"Partition field '{partition_field}' not in list of columns '{col_list}'"
        raise ValueError(msg)


@dataclass
class Census_fields:
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
    conparid: str

    # def __post_init__(self):
    # first_validate(self)
    # validate_cols(self)


@dataclass
class SCOTcensus_fields(Census_fields):
    # def __post_init__(self):
    #     validate_cols(self)

    pass


@dataclass
class Csv_params:
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
    partition_on: str
    new_uid: str
    sep: str
    index: bool
    filetype: str

    def __post_init__(self):
        first_validate(self)


@dataclass
class Censusconfiguration:
    # inputdir: str  # remove this in future
    country: str
    year: int
    runtype: bool
    census_file: str
    census_fields: Census_fields
    csv_params: Csv_params  # parameters passed to dask read_csv

    census_standardisation_file: str
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
        validate_censuscols(self.census_fields, self.census_file, self.csv_params)
        first_validate(self)
        validate_partition(
            self.census_output_params.partition_on, self.census_fields.list_cols()
        )


@dataclass
class Parish_gis_config:
    filepath: str
    projection: str
    id_field: str

    def __post_init__(self):
        validate_projection(self.projection)
        validate_paths(self.filepath)


@dataclass
class Rsd_gis_config:
    filepath: str
    projection: str

    def __post_init__(self):
        validate_paths(self.filepath)
        validate_projection(self.projection)


@dataclass
class Rsd_dictionary_config:
    filepath: str
    cen_parid_field: str
    rsd_id_field: str
    encoding: str
    sep: str
    quoting: int

    def __post_init__(self):
        validate_paths(self.filepath)
        first_validate(self)
        validate_sep(self.sep)
        validate_quoting(self.quoting)


@dataclass
class Parish_icem_lkup_config:
    filepath: str
    sheet: str
    ukds_id_field: str
    na_values: str
    conparid51_91_field: str
    conparid01_11_field: str

    def __post_init__(self):
        validate_paths(self.filepath)


@dataclass
class EW_configuration:
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
class Target_geom:
    path_to_geom: str
    projection: str
    file_type: str
    geom_type: str
    data_fields: Data_fields
    standardisation_file: str
    query_criteria: str
    filename_disamb: str = ""
    geometry_format: str = ""
    encoding: str = ""
    sep: str = ","

    def __post_init__(self):
        if isinstance(self.data_fields, dict):
            self.data_fields = Data_fields(**self.data_fields)

        validate_projection(self.projection)

        validate_paths(self.path_to_geom)
        validate_sep(self.sep)


@dataclass
class General:
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


# trial = General(
#     output_data_path="data/output/",
#     linked_subdir="linked/",
#     duplicate_subdir="duplicate/",
# )

# print(trial.duplicate_outputdir)


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


def create_conparid(parish_icem_lkup_config, census_year):
    if census_year < 1901:
        conparid = parish_icem_lkup_config.conparid51_91_field
    else:
        conparid = parish_icem_lkup_config.conparid01_11_field
    return conparid
