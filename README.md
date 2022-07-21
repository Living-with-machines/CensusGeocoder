# historic-census-gb-geocoder

Geocode Historic Great British Census Data 1851-1911

- [What is historic-census-gb-geocoder?](#What-is-historic-census-gb-geocoder)
- [Installation and setup](#installation)
  - [Set up a conda environment](#set-up-a-conda-environment)
  - [Method 1: pip](#method-1)
  - [Method 2: source code (for developers)](#method-2)
- [Overview](#overview)
- [Data Inputs](#data-inputs)
  - [Integrated Census Microdata (I-CeM)](#integrated-census-microdata-i-cem)
  - [Parish Boundary Data (EW ONLY)](#Parish-Boundary-Data-(EW-ONLY))
  - [1851EngWalesParishandPlace I-CeM Lookup Table (EW ONLY)](#1851engwalesparishandplace-i-cem-lookup-table-(EW-ONLY))

  - [Registration Sub-District (RSD) Boundary Data (EW ONLY)](#registration-sub-district-rsd-boundary-data-(ew-only))
  - [Registration Sub-District (RSD) Lookup Table (EW ONLY)](#registration-sub-district-rsd-lookup-table-ew-only)
  - [National Records of Scotland - Historic Civil Parishes pre-1891 and Civil Parishes (post 1891) Boundary Data and Lookup Table](#national-records-of-scotland---historic-civil-parishes-pre-1891-and-civil-parishes-post-1891-boundary-data-and-lookup-table)

  - [Target Geometry Data](#target-geometry-data)
      - [GB1900 Gazetteer](#gb1900-gazetteer)
      - [OS Open Roads](#os-open-roads)

- [How to cite historic-census-gb-geocoder](#how-to-cite-historic-census-gb-geocoder)
- [Credit and re-use terms](#credit-and-re-use-terms)

- [Acknowledgements](#acknowledgements)

## What is historic-census-gb-geocoder

historic-census-gb-geocoder links street addresses in historic census data to target geometry datasets.

![overview](documentation/overview_large.png)

## Installation

### Set up a conda environment

I recommend installation via Anaconda (refer to [Anaconda website and follow the instructions](https://docs.anaconda.com/anaconda/install/)).

* Create a new environment for `historic-census-gb-geocoder` called `geocoder_py38`:

```bash
conda create -n geocoder_py38 python=3.8
```

* Activate the environment:

```bash
conda activate geocoder_py38
```
### Method 1

***Not added to pypi yet - use method 2***
* Install `historic-census-gb-geocoder`:

 ```bash
pip install historic-census-gb-geocoder
```

### Method 2

* Clone `historic-census-gb-geocoder` source code:

```bash
git clone https://github.com/Living-with-machines/historic-census-gb-geocoder.git
```

* Install:

```bash
cd /path/to/historic-census-gb-geocoder
pip install -v -e .
```

Edit `/path/to/` as appropriate to the directory that you cloned `historic-census-gb-geocoder` into. E.g. `/Users/jrhodes/historic-census-gb-geocoder`

### Set parameters

#### General parameters
The `input_config.yaml` file allows you to adjust many variables for each census year. Some of the key ones are detailed below:

Set the directory where outputs should be saved: 

```yaml
general:
  output_data_path: "data/output/"
```

#### England and Wales parameters






Set the file path to the 1851EngWalesParishandPlace I-CeM Lookup Table

```yaml
parish_icem_lkup_config:
  filepath: "data/input/ew/UKDS_GIS_to_icem.xlsx"
```

#### Scotland parameters



### Folder structure and data
*to edit*

```bash
├── data
│   ├── input
│   │   ├── 1851EngWalesParishandPlace
│   │   ├── census_anonymisation_egress
│   │   ├── oproad_essh_gb-2
│   │   │   ├── data
│   │   │   └── doc
│   │   ├── parish_dicts_encoding
│   │   ├── rsd_boundary_data
│   │   └── scot_parish_boundary
│   │       ├── CivilParish1930
│   │       └── CivilParish_pre1891
│   ├── new_geocode_egress
│   ├── output
│   │   ├── 1891
│   │   │   └── EW
│   │   │       └── testing
│   │   ├── 1901
│   │   │   └── SCOT
│   │   │       └── testing
│   │   └── 1911
│   │       └── EW
│   │           └── testing
│   └── testing_outputs
│       └── data
│           └── output
│               └── 1851
│                   └── EW
│                       └── testing
├── inputs
└── testing_outputs
    └── data
        └── output
            ├── 1891
            │   └── EW
            │       └── testing
            └── 1901
                └── SCOT
                    └── full
```

### Run

```bash
python3 historic_census_gb_geocoder.py
```

## Outputs


## Overview

Something here

## Data Inputs
This is a list and discription of the datasets you need to download and save locally in order to run the scripts correctly. Each section below describes the dataset, citation and copyright details, and how to set parameters in the relevant section of [input_config.yaml](inputs/input_config.yaml).


### Integrated Census Microdata (I-CeM)

#### Description

I-CeM census datasets, which are digitised individual-level 19th and early 20th century census data for Great Britain, covering England and Wales 1851-1911 (except 1871), and Scotland 1851-1901. They are 12 `.txt` files in total, each containing tab delimited census data.

These files have been created by merging two versions of the I-CeM datasets together, which contain different types of information and have different access restrictions. You need both to perform geocoding on the full I-CeM dataset. There is an anonymised version ([SN 7481](https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=7481)) and a 'Names and Addresses - Special Licence' version ([SN 7856](https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=7856)). The anonymised version ([SN 7481](https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=7481)) is downloadable via the UKDS after signing up to their standard end user licence. The anonymised version does not contain individuals' names and addresses but contains a unique id `RecID` for each person that links them to their name and address held in the 'Special Licence' version ([SN 7856](https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=7856)). As its name suggests, access to the name and address data in I-CeM is by application for a special licence, which requires review by UKDS and the owners ([Findmypast/Brightsolid](https://www.findmypast.co.uk)) of the transcriptions on which I-CeM is based.

Further documentation on I-CeM, including how it was created and the variables it contains can be found [here](https://www.essex.ac.uk/research-projects/integrated-census-microdata).

The `historic-census-gb-geocoder` uses the following fields from these census files:

*England and Wales only

FIELD|DESCRIPTION
--|--
RecID|Unique id for each person
Address|Street Address
ConParID*|Consistent Parish ID
ParID|Parish IDs
RegCnty|Registration County

*Sample (fabricated) Data*
RecID|Address|ConParID*|ParID|RegCnty
--|--|--|--|--
1|23 High Street|12|21|Essex
2|23 High Street|12|21|Essex
3|23 High Street|12|21|Essex
4|23 High Street|12|21|Essex
5|25 High Street|12|21|Essex
6|25 High Street|12|21|Essex

#### Citation

>Schurer, K., Higgs, E. (2020). Integrated Census Microdata (I-CeM), 1851-1911. [data collection]. UK Data Service. SN: 7481, DOI: 10.5255/UKDA-SN-7481-2
Schurer, K., Higgs, E. (2022). Integrated Census Microdata (I-CeM) Names and Addresses, 1851-1911: Special Licence Access. [data collection]. 2nd Edition. UK Data Service. SN: 7856, DOI: 10.5255/UKDA-SN-7856-2

#### Parameters in `input_config.yaml`

Under the `census_config` settings for each census year (in this case England and Wales 1851):

Set `runtype` to `True` if you want to geocode this census year, or set to `False` if you want to skip this year.

Set `census_file` to the path of the census data file, you need to set this for each census year.

```yaml
census_config:
  EW_1851:
    runtype: True
    census_file: "data/input/census_anonymisation_egress/EW1851_anonymised_s.txt"
```

### Parish Boundary Data (EW ONLY)

#### Description

A shapefile (`.shp`) and associated files of 1851 Parish Boundary data for England and Wales. The boundary dataset looks like this:

![1851EngWalesParishandPlace](documentation/1851EngWalesParishandPlace.png "1851EngWalesParishandPlace")

This boundary dataset can be linked to I-CeM using [1851EngWalesParishandPlace I-CeM Lookup Table](#1851engwalesparishandplace-i-cem-lookup-table-england-and-wales-only) to create consistent parish geographies for England and Wales across the period 1851-1911. The consistent parish geographies are used by `historic-census-gb-geocoder` in conjunction with boundary datasets for Registration Sub Districts (RSD) to assign streets in target geometry datasets to a historic parish/RSD administrative unit (see [Overview](#overview) for more details.)

FIELD|DESCRIPTION
--|--
ID|Unique ID for parish, links to [1851EngWalesParishandPlace I-CeM Lookup Table](#1851engwalesparishandplace-i-cem-lookup-table-england-and-wales-only)
geometry|Polygon or Multipolygon boundary data

*Sample Data*

ID|geometry
--|--
0|MultiPolygon (((324609.9061836339533329 553449.56249322975054383, 324656.15613449434749782…)))
1|MultiPolygon (((446743.09374157758429646 400075.09375633631134406, 446731.84381735557690263…)))
2|MultiPolygon (((579932.99360200657974929 144415.23930413232301362, 579938.06249888404272497…)))
3|MultiPolygon (((408229.88241174072027206 604962.03670125640928745…)))

The files and documentation explaining the creation of the boundaries and the fields in the dataset are available from the UKDS [here](https://reshare.ukdataservice.ac.uk/852816/). Access to the files requires registration with the UKDS.

#### Citation:

>Satchell, A.E.M and Kitson, P.K and Newton, G.H and Shaw-Taylor, L. and Wrigley, E.A (2018). 1851 England and Wales census parishes, townships and places. [Data Collection]. Colchester, Essex: UK Data Archive. 10.5255/UKDA-SN-852232

#### Parameters in `input_config.yaml`

You need to set thepath to the 1851 Parish Boundary Data for England and Wales Data in the `filepath` setting. If accessing this data via UKDS, the `projection` and `id_field` should remain the same as below.

```yaml
ew_config:
  parish_gis_config:
    filepath: "data/input/ew/1851EngWalesParishandPlace/1851EngWalesParishandPlace.shp" # path to parish boundary data
    projection: "EPSG:27700" # projection authority string passed to geopandas
    id_field: "ID" # unique id field that links to parish icem lookup table 'ukds_id_field'
```

### 1851EngWalesParishandPlace I-CeM Lookup Table (EW ONLY)

#### Description
A lookup table that links I-CeM to parish boundary data. A full description of the dataset and its intended uses can be found [here - Consistent Parish Geographies](https://www.essex.ac.uk/research-projects/integrated-census-microdata)

`historic-census-gb-geocoder` only uses three fields from the lookup table, which are:

FIELD|DESCRIPTION
--|--
UKDS_ID|ID that links to `ID` [1851 Parish Boundary Data for England and Wales](#parish-boundary-data-(EW-ONLY))
conparid_51-91|Consistent parish ID for census years 1851 to 1891; links to `ConParID` in [Integrated Census Microdata (I-CeM)](#integrated-census-microdata-i-cem)
conparid_01-11|Consistent parish ID for census years 1901 and 1911; links to `ConParID` in [Integrated Census Microdata (I-CeM)](#integrated-census-microdata-i-cem)

UKDS_ID|conparid_51-91|conparid_01-11
--|--|--
977|1|100001
909|1|100001
925|2|100001

#### Citation

The I-CeM website doesn't provide a citation for this lookup dictionary. The link to the data is under the heading 'Consistent Parish Geographies' [here](https://www.essex.ac.uk/research-projects/integrated-census-microdata)

#### Parameters in `input_config.yaml`

You need to set the path to the lookup file under `filepath`. The other settings should work with a version of the lookup table downloaded from the I-CeM website.

```yaml
parish_icem_lkup_config:
  filepath: "data/input/ew/UKDS_GIS_to_icem.xlsx" # path to parish to icem lookup table
  sheet: "link" # spreadsheet sheet containing data
  ukds_id_field: "UKDS_ID" # unique id field that links to parish boundary data 'id_field'
  na_values: "." # denotes na values in table
  conparid51_91_field: "conparid_51-91" # consistent parish id field for 1851 to 1891
  conparid01_11_field: "conparid_01-11" # consistent parish id field for 1901 and 1911
```

### Registration Sub-District (RSD) Boundary Data (EW ONLY)

#### Description
A shapefile and associated files of boundary data for Registration Sub-Districts in England and Wales 1851-1911. The correct RSD boundaries for each year are created by 'dissolving' the geometries on the appropriate `CEN` field, e.g. `CEN_1851` to create 1851 boundaries or `CEN_1901` to create 1901 boundaries. The boundary dataset looks like this:

![RSD Boundary Data](documentation/RSD_boundary.png "RSD Boundary Data")

FIELD|DESCRIPTION
--|--
CEN_1851|RSD ID for 1851
CEN_1861|RSD ID for 1861
CEN_1871|RSD ID for 1871
CEN_1881|RSD ID for 1881
CEN_1891|RSD ID for 1891
CEN_1901|RSD ID for 1901
CEN_1911|RSD ID for 1911
geometry|Polygon or Multipolygon boundary data

*Sample Data*

CEN_1851|CEN_1861|CEN_1871|CEN_1881|CEN_1891|CEN_1901|CEN_1911|geometry
--|--|--|--|--|--|--|--
10001|10001|10001|10001|10101|10101|10001|MultiPolygon (((525713.3125 183236.54690000042319298, 525824.6875...)))
10002|10002|10002|10002|10102|10102|10003|MultiPolygon (((527519.875 181175.60940000042319298...)))
10002|10002|10002|10002|10102|10102|10002|MultiPolygon (((525407.86180000007152557 180858.28729999996721745...)))
10001|10001|10001|10001|10101|10101|10002|MultiPolygon (((525405 181928, 525420 181906, 525487...)))

#### Citation
>Day, J.D. Registration sub-district boundaries for England and Wales 1851-1911 (2016). This dataset was created by the 'Atlas of Victorian Fertility Decline' project (PI: A.M. Reid) with funding from the ESRC (ES/L015463/1).

The RSD Boundaries were supplied directly by Joe Day at the University of Bristol and Alice Reid at the University of Cambridge. They are in the process of being deposited with UKDS and the citation may change to reflect this in due course.

#### Parameters in `input_config.yaml`

Set the path to the RSD Boundary shapefile (with associated files in the same directory). The `projection` should be the same as below when this file is accessible via UKDS.

```yaml
rsd_gis_config:
  filepath: "data/input/ew/rsd_boundary_data/RSD_1851_1911_JR.shp" # path to rsd boundary data
  projection: "EPSG:27700" # projection authority string passed to geopandas
```
### Registration Sub-District (RSD) Lookup Table (EW ONLY)

#### Description
A series of data dictionaries for linking I-CeM to the RSD Boundary Data. You can ignore `finalEWnondiss1851_1911.txt`, `PAR1851_RSD_MATCH.txt` and `1871_DICTIONARY_CODED.txt`. There are 6 other files - one for each census year in I-CeM - that link the `ParID` field in I-CeM to a `CEN_****` (e.g. `CEN_1851`) field in the RSD Boundary data above. 

`historic-census-gb-geocoder` uses the following fields from the lookup tables (this example is taken from the 1851 file):

FIELD|DESCRIPTION
--|--
ParID|Parish ID in [I-CeM](#integrated-census-microdata-i-cem)
CEN_1851|RSD ID in [RSD Boundary Data](#registration-sub-district-rsd-boundary-data-ew-only)

*Sample Data*

ParID|CEN_1851
--|--
1|10001
2|10002

#### Citation
>Day, J.D. Registration sub-district boundaries for England and Wales 1851-1911 (2016). This dataset was created by the 'Atlas of Victorian Fertility Decline' project (PI: A.M. Reid) with funding from the ESRC (ES/L015463/1).

The RSD Lookup Dictionaries were supplied directly by Joe Day at the University of Bristol and Alice Reid at the University of Cambridge. They are in the process of being deposited with UKDS and the citation may change to reflect this in due course.

#### Parameters in `input_config.yaml`

Set the file path to the Registration Sub-District (RSD) Lookup Table under the `filepath` setting. This needs to be done for each census year. The other settings work for the files supplied at time of writing - they can be changed if necessary once these files are available via UKDS.

```yaml
rsd_dictionary_config:
  "1851":
    filepath: "data/input/ew/parish_dicts_encoding/1851_ICeM_DICTIONARY_CODED.txt" # path to rsd dictionary lookup table
    cen_parid_field: "ParID" # ParID field that links to I-CeM ParID
    rsd_id_field: "CEN_1851" # unique id of rsd unit
    encoding: "utf-8" # file encoding
    sep: "\t"
    quoting: 3
```

#### National Records of Scotland - Historic Civil Parishes pre-1891 and Civil Parishes (post 1891) Boundary Data and Lookup Table

`data/input/scot_parish_boundary/` - contains two Scottish parish boundary files and a lookup table that links the boundary files to I-CeM.

There are Scottish parish boundary datasets for pre- and post-1891 civil parishes. A detailed discussion of the dataset and changes to the boundaries of Scottish parishes, see [National Records of Scotland - Historic Civil Parishes pre-1891](https://www.nrscotland.gov.uk/statistics-and-data/geography/our-products/other-national-records-of-scotland-nrs-geographies-datasets/historic-civil-parishes-pre-1891) and [National Records of Scotland - Civil Parishes (post 1891)](https://www.nrscotland.gov.uk/statistics-and-data/geography/our-products/other-national-records-of-scotland-nrs-geographies-datasets/civil-parishes). For further information on the major boundary changes around 1891, see also [Genuki](https://www.genuki.org.uk/big/sct/shennan/boundaries).

`scot_parish_boundary/CivilParish_pre1891/` - contains the shapefile and associated files for pre-1891 Scottish parish boundaries.

![Pre-1891 Scottish Parish Boundaries](documentation/pre-1891_scottish_parish.png "Pre-1891 Scottish Parish Boundaries")

`scot_parish_boundary/CivilParish1930` - contains the shapefile and associated files for post-1891 Scottish parish boundaries.

![Post-1891 Scottish Parish Boundaries](documentation/post-1891_scottish_parish.png "Post-1891 Scottish Parish Boundaries")

Unlike the parish boundary datasets for England and Wales, there was no openly available lookup table that directly linked parish boundary data to I-CeM. Without a similar lookup table for Scotland, we would not be able to perform geo-blocking strategies required in the geo-coding script (e.g. only trying to match streets from the same parish across OS Open Roads/GB1900 and I-CeM).

To link the Scottish parish boundary datasets to I-CeM, a lookup table has been created that associates each parish in the pre- and post-1891 boundary files with a corresponding parish in I-CeM. A separate lookup table for each census year has been produced - firstly, to use the most appropriate boundary dataset (pre or post 1891), and secondly, to link to parishes from each census year via the `ParID` variable (rather than rely on consistent parish geographies across census years - the `ConParID` variable).

The structure of the lookup table is as follows:

FIELD|VALUE
--|--
"name" / "JOIN_NAME_"|Parish name from boundary dataset; "name" for post-1891, "JOIN_NAME_" for pre-1891.
ParID_link|ParID of corresponding parish in I-CeM
Notes|Notes on how the link was made; "exact" = parish names matched exactly between the boundary dataset and I-CeM; see individual files for other match types.

Scotland, 1901 example:

name| ParID_link | notes
-- | -- | --
NEW CUMNOCK | 100595 | exact
OLD CUMNOCK | 100597 | exact
DAILLY | 100572 | exact
SMALL ISLES | 100119 | exact

### Target Geometry Data

`historic-census-gb-geocoder` can link I-CeM data to any existing target geometry dataset in shapefiles or in csv files by adjusting the following settings:

```yaml
target_geoms: # geometry data to link census data to
# General
  name_of_target_geometry: # name of geometry data
    path_to_geom: "path/to/data" # path to geometry data; can be directory if multiple files or path to file.
    projection: "EPSG:****" # projection authority string passed to geopandas, eg. "EPSG:27700"
    file_type: "" # file type; accepts 'shp' or 'csv'
    geom_type: "" # type of geometry, accepts either 'line' or 'point'; determines union operations (see documentation)

    filename_disamb: "" # optional (for multiple .shp files); correct filename to read if multiple files in directory, e.g. OS Open Roads contains 'RoadNode' and 'RoadLink'. If 'RoadLink.shp' provided, it will ignore 'RoadNode.shp'.
    data_fields: # fields to read from file
      uid_field: "" # unique id field, e.g. 'nameTOID'
      address_field: "" # address field, e.g. 'name1'
      geometry_fields: "" # geometry field, e.g. 'geometry'
    standardisation_file: "" # optional; file to perform regex replacement on address field
    query_criteria: "" # optional; query to pass to pandas 'df.query'

# shp file specific

# csv file specific
    encoding: "utf-16" # for 'csv' only; file encoding passed to pandas read_csv
    sep: "," # for 'csv' only; seperator value passed to pandas read_csv
    geometry_format: "" # only for 'csv'; if  for use with 'csv' 
```

#### GB1900 Gazetteer

##### Description

GB1900 file. Contains transcriptions of text labels from the Second Edition County Series six-inch-to-one-mile maps covering the whole of Great Britain, published by the Ordnance Survey between 1888 and 1914. As well as the labels, GB1900 Gazetteer contains the geographic coordinates of the labels (usually taken from the upper, left-hand corner of the label).

The version of the GB1900 Gazetteer used in this repo is the 'COMPLETE GB1900 GAZETTEER', which can be downloaded from [here](http://www.visionofbritain.org.uk/data/#tabgb1900).

##### Citation

It is available on a CC-BY-SA licence. Taken from the data documentation:

>Please reference this work as the "GB1900 Gazetteer" made available by the GB1900 Project. You must acknowledge "the Great Britain Historical GIS Project at the University of Portsmouth, the GB1900 partners and volunteers".

>You may call any work you derive from this dataset whatever you like EXCEPT that you must not name your work "the GB1900 gazetteer", or any other name including "GB1900" or "Great Britain 1900". When using or citing the work, you should not imply endorsement by the GB1900 project or by any of the project partners.

##### Parameters in `input_config.yaml`

Insert once these geometry field changes have been made.

#### OS Open Roads
##### Description

Shapefiles and documentation from the Ordnance Survey's Open access modern road vector data. Available here to download: https://www.ordnancesurvey.co.uk/business-government/products/open-map-roads.

`oproad_essh_gb-2` contains a `data` folder, which stores `RoadLink` and `RoadNode` files. historic-census-gb-geocoder only requires the `RoadLink` files.

##### Citation

Taken from the Ordance Survey website:

>Our open data products are covered by the Open Government Licence (OGL), which allows you to: copy, distribute and transmit the data;
adapt the data; and
exploit the data commercially, whether by sub-licensing it, combining it with other data, or including it in your own product or application.
We simply ask that you acknowledge the copyright and the source of the data by including the following attribution statement: Contains OS data © Crown copyright and database right 2022

##### Parameters in `input_config.yaml`

Insert once these geometry field changes have been made.



## How to cite historic-census-gb-geocoder
## Credit and re-use terms
`historic-census-gb-geocoder` relies on several datasets that require you to have an account with the UK Data Service (UKDS) to sign their standard end user licence. Please see individual datasets listed under [Data Inputs](#data-inputs)

#### 8. Street Standardisation

*The naming conventions need to be improved here - this file is for use with the GB1900 Gazetteer.*

*There is plenty of scope for expanding the range of regex patterns used to clean the address strings.*

`street_standardisation.json` - contains regex patterns to find and replacement words. Currently used to expand abbreviations in GB1900 Gazetteer, e.g. Rd to Road.

#### 9. I-CeM Street Standardisation

*There is plenty of scope for expanding the range of regex patterns used to clean the address strings.*

`icem_street_standardisation.json` - contains regex patterns to find and replacement words. Currently used to expand abbreviations in I-CeM, e.g. Rd to Road. Also removes extra letters left at the start of the address strings after removing digits (to comply with safehaven rules). E.g. '68A High Street' leaves 'A High Street', which is then cleaned to 'High Street'.



### Data Output

*Needs adding 

## Acknowledgements

This work was supported by Living with Machines (AHRC grant AH/S01179X/1) and The Alan Turing Institute (EPSRC grant EP/N510129/1). Living with Machines, funded by the UK Research and Innovation (UKRI) Strategic Priority Fund, is a multidisciplinary collaboration delivered by the Arts and Humanities Research Council (AHRC), with The Alan Turing Institute, the British Library and the Universities of Cambridge, East Anglia, Exeter, and Queen Mary University of London.

I'd also like to  thank @mcollardanuy for reviewing the code, Joe Day and Alice Reid for supplying RSD Boundary data and lookups prior to their deposit with the UK Data Service.
