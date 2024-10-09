# CensusGeocoder

![overview](documentation/overview_large_new.png)

## What is CensusGecooder?

**CensusGeocoder** links addresses in [digitised historic census data for Great Britain 1851-1911](#integrated-census-microdata-i-cem) to their 'real-world' geographic location. For example, it takes the text 'Ruby Street' from the census and links it to a geometry dataset of your choice. We link to [OS Open Roads](#os-open-roads) and [GB1900](#gb1900-gazetteer) as our target geometry datasets as the best alternatives until a full vector dataset of nineteenth/early twentieth century streets is created (we'd love if this was available someday!)

**CensusGeocoder** allows you to use historic census data in new and powerful ways. Previously, the smallest spatial unit people in historic census data could be geo-located by was either a parish or registration sub-district (as well as larger units like registration districts and counties). But each of these administrative units - even parishes - necessitates aggregating individuals to quite large areas. Any sub-parish distinctions (like types of streets that people lived on, or perhaps how close someone lived to a factory or railway line) are lost. Typically, researchers used the centroids of parish polygons to conduct spatial analysis of the census. This meant that everyone in the parish was treated the same, e.g. *x* km from a station. **CensusGeocoder** locates individuals at property and street level, so we can now differentiate people street-by-street, and talk of people being *x* meters from a point of interest.

## How does it work?

It uses geo-blocking and fuzzy string matching. You can pick any or all census years in [Integrated Census Microdata (I-CeM)](#integrated-census-microdata-i-cem) and link them to a target geometry dataset (or datasets) of your choosing. It uses the relevant boundary datasets of historic administrative units (e.g. Parishes, Registration Sub-Districts) for each census year (1851-1911) and country (England and Wales, or Scotland) to assign census addresses and target geometry addresses to the appropriate historic administrative unit. This restricts fuzzy string matching between census and target geometry addresses to the correct historic boundary and disambiguates common street names found across the country (e.g. High Street), resulting in higher quality matches.

The figure below gives an overview of the process:

![flowchart](documentation/flowchart_cl.png "flowchart")

**Let's run through a specific example:**

<!-- Let's take 'Ruby Street' in South Manchester. In the 1901 census, there are 154 living on this particular Ruby Street. The Ruby Street we're interested in is located in `ParID` 

address|RegDist|Parish|ParID|ConParID
--|--|--|--|--|
RUBY STREET|Chorlton|SOUTH MANCHESTER|10873|108139
RUBY STREET|Chorlton|SOUTH MANCHESTER|10871|108139
-->

Let's take 'BOUNDARY LANE' in South Manchester in 1901 (it runs perpendicular to 'RUBY STREET' in the picture at the top). How do we link this 'BOUNDARY LANE' in the census to the same 'BOUNDARY LANE' in a GIS dataset of streets, like OS Open Roads. The challenge is that there will be lots of streets with the same name in the census and in those GIS files.

Here's the location of streets containing the words 'BOUNDARY LANE' in OS Open Roads. There are 50 streets with the name 'BOUNDARY LANE', and a further 3 named 'BOUNDARY LANE NORTH', 'BOUNDARY LANE SOUTH', and 'OLD BOUNDARY LANE'.

<!-- ![all_boundary_lanes](documentation/run_through/boundary_lane_all.png) -->

<img src="https://github.com/Living-with-machines/CensusGeocoder/blob/5ead73515372cd9747b36147e18b13356ecc2310/documentation/run_through/boundary_lane_all.png" alt="Streets containing the text 'Boundary Lane' across England and Wales" width="500" height="500">

OS Open Roads identify streets' exact locations but there's no inherent spatial relationship between them and the census. We need to classify the streets in the OS Open Roads according to historic boundaries that relate to the census data, in order to be able to differentiate all these streets with the same or similar names.

Let's look at some information about addresses that contain 'BOUNDARY LANE' in the census. The table below tells us which registration district, parish and registration sub-district each one is in. `NumInds` tells us how many people were living on each of these streets in 1901.

|RegCnty|RegDist|Parish|SubDist|ConParID|ParID|NumInds
|--|--|--|--|--|--|--|
Berkshire|Wallingford|SOUTH STOKE (OXON)|Wallingford|101064|1737|2
Buckinghamshire|Wycombe|HIGH WYCOMBE|Wycombe|101306|2115|89
Cheshire|Chester|CHESTER|Chester Castle|107952|10598|9
Cheshire|Chester|SALTNEY (FLINT)|Hawarden|107991|10650|72
Cheshire|Wirral|GAYTON|Neston|107999|10654|90
Lancashire|Chorlton|SOUTH MANCHESTER|Chorlton Upon Medlock|108139|10871|109
Lancashire|Chorlton|SOUTH MANCHESTER|Hulme|108139|10873|19
Lancashire|Ormskirk|BURSCOUGH|Scarisbrick|108085|10770|15
Lancashire|Ormskirk|SIMONSWOOD|Bickerstaffe|108071|10755|36
Lancashire|West Derby|EVERTON|South Everton|108037|10727|214
Lancashire|West Derby|KIRKBY|Fazakerley|108042|10721|6
Lancashire|West Derby|WEST DERBY|West Derby Western|108049|10729|297
London (Parts Of Middlesex, Surrey & Kent)|Camberwell|CAMBERWELL|St George|100003|235|188
London (Parts Of Middlesex, Surrey & Kent)|Southwark|NEWINGTON|St Peter Walworth|100003|211|161
Norfolk|Blofield|POSTWICK|Blofield|103249|4501|26
Norfolk|Blofield|THORPE NEXT NORWICH|Blofield|103248|4504|44
Nottinghamshire|Worksop|WORKSOP|Worksop|107257|9734|15

For each street in the census, we have quite a lot of geographical information that helps us distinguish streets with the same name. The `ConParID` and `ParID` fields link to existing GIS boundary datasets, which we can use to carve up our target geometry datasets.

`ConParID` refers to 'Consistent Parish ID'. There are two series of consistent parish boundaries - one that covers 1851 to 1891, and another set covering 1901 and 1911. Consistent parish boundaries don't reflect real parish boundaries, they're artificial units constructed by aggregating multiple parishes. See [here](https://www.essex.ac.uk/research-projects/integrated-census-microdata) for more information under the heading 'Consistent Parish Geographies'. We can map these consistent parish units: the `ConParID` field links to [Parish Boundary Data](#parish-boundary-data-england-and-wales-only) via a [lookup table](#1851engwalesparishandplace-i-cem-lookup-table-england-and-wales-only).

`ParID` is an internal parish identifier for I-CeM that links to [registration sub-district boundary data](#registration-sub-district-rsd-boundary-data-england-and-wales-only) via a [lookup table](#registration-sub-district-rsd-lookup-table-england-and-wales-only). This lookup table tells us which registration sub-district that each `ParID` is in for each census year. Registration sub-districts change from year-to-year, and they have different ids for each year. The name of the unique id field for 1901 is `CEN_1901`. The table below tells us that `ParID` 10871 is in `CEN_1901` 4640003. Once we know the unique id of each regstration sub-district, we don't need to use the `ParID` value anymore.

ParID - RSD Lookup Table:
ParID|CEN_1901|YEAR|COUNTRY|DIVISION|REGCNTY|REGDIST|SUBDIST|PARISH|
--|--|--|--|--|--|--|--|--|
10871|4640003|1901|ENG|VIII|LANCASHIRE|CHORLTON|CHORLTON UPON MEDLOCK|SOUTH MANCHESTER|
10873|4640004|1901|ENG|VIII|LANCASHIRE|CHORLTON|HULME|SOUTH MANCHESTER|

Below is a map of Manchester overlaid with these two different boundary datasets. The large area in green is the area covered by the consistent parish unit (this particular one is `ConParID` 108139). The black lines are the boundaries of the Registration Sub-Districts (RSDs) in that area. Each area bounded by a black line has its own `CEN_1901` id value.

<img src="https://github.com/Living-with-machines/CensusGeocoder/blob/5ead73515372cd9747b36147e18b13356ecc2310/documentation/run_through/manchesterconpar.png" alt="Manchester consistent parish and RSD" width="500" height="500">

Sometimes RSDs are larger than a consistent parish unit, but often they're smaller around urban centres like Manchester or London. In this example, they break up that large green area into smaller RSD/consistent parish combinations. This helps us disambiguate streets of the same name better than if we relied solely on the consistent parish unit - it's so large in this case that there are bound to be multiple streets with the same name and no way for us to know which one is which (in a systematic geographic sense for geo-blocking purposes). Creating new boundaries by combining RSDs and consistent parish units creates the smallest boundary units that we have for the historic census data.

Let's briefly turn back to OS Open Roads. We'll use these historic boundaries to classify roads in OS Open Roads. This will help us limit the number of streets to compare (we'll only be searching census streets and OS Open Roads streets that are in a similar area). 

Let's zoom in on the 'BOUNDARY LANE' to the south of Manchester:

<img src="https://github.com/Living-with-machines/CensusGeocoder/blob/5ead73515372cd9747b36147e18b13356ecc2310/documentation/run_through/boundary_lane_manchesterzoom.png" alt="Manchester consistent parish and RSD zoomed" width="500" height="500">

We're within `ConParID` 108139 now. The image shows us the modern 'BOUNDARY LANE' from OS Open Roads overlaying a historic OS map. The path of the modern road closely follows but is not exactly the same as the historic road. This is one of the many challenges of using modern road vector data in lieu of historic road vector data!

We can see the road in relation to nearby RSD boundaries. Perhaps unsurprising given its name, 'BOUNDARY LANE' runs close to the boundaries of two RSDs. The ends of the road (marked in red) are in `CEN_1901` 4640003, but the middle of the road (marked in blue) is in neighbouring `CEN_1901` 4640004.

When assigning roads to consistent parish/RSD units, roads are split at the point they cross boundaries so that we match people to the correct segment of the road they live on. This only applies to linestring geometries of roads - not points (like GB1900 data) because points lie within a boundary and don't cross boundaries. (This is a shortcoming of using GB1900 point data despite the fact the street names it contains are contemporaneous with the 1891-1911 censuses).

Now we've overlaid the historic census boundaries on the modern road data, we've created two Boundary Lanes (one for each of these RSDs) where there was just one road in the original OS Open Roads dataset. We do this for all the streets across the country. The process is slightly different for Scotland - it's simpler because we just use parish boundaries (we don't have GIS boundary datasets of registration sub-districts for Scotland).

Now we've assigned roads in OS Open Roads to historic administrative units, we can begin linking them to streets in the census.

We can select all the streets in OS Open Roads and the census with `ConParID` 108139 and `CEN_1901` 464000.

This returns 388 streets from OS Open Roads:

<img src="https://github.com/Living-with-machines/CensusGeocoder/blob/5ead73515372cd9747b36147e18b13356ecc2310/documentation/run_through/4640004_os_roads.png" alt="Roads in ConParID 4640004" width="500" height="500">

There are 1052 unique addresses in the census within the same area. These aren't all different streets, they're just the unique addresses recorded in the census (after we've removed house numbers etc). E.g. we're left with 'YORK PLACE' on which lots of people will live and more specific entries like 'THE GREYHOUND YORK PLACE'.

We can now compare these two subsets of OS Open Roads and the census data. We use a string edit distance algorithm approach (also known as fuzzy string matching) to compare how similar the names of streets in our sample of streets from OS Open Roads are to the streets in the census subset. You can read more about the algorithms we use [here](#string-comparison-parameters). It returns a score between 0 and 1 (1 being an exact match).

This table shows the 5 highest similarity scores after comparing each of those 388 street names with 'BOUNDARY LANE'. We pick the highest scoring one as our match, and in this case it's an exact match since there's a 'BOUNDARY LANE' in our sample of OS Open Roads data.

name1|similarity score
--|--
BOUNDARY LANE|1.00
HUNMANBY AVENUE|0.57
SOUTHEND AVENUE|0.57
GLADSTONE COURT|0.54
UPPER MOSS LANE|0.54

We also apply a weighting based on how common certain street names are [see here for more details](#string-comparison-parameters) so that the threshold for considering common street names like 'New Road' or 'High Street' as a match is higher than street names that are less common. We then pick the highest scoring match.

<!-- Let's return to the table of Boundary Lanes from earlier. 

|RegCnty|RegDist|Parish|SubDist|ConParID|ParID|NumInds
|--|--|--|--|--|--|--|
Lancashire|Chorlton|SOUTH MANCHESTER|Chorlton Upon Medlock|108139|10871|109
Lancashire|Chorlton|SOUTH MANCHESTER|Hulme|108139|10873|19

We can now see that these two entries for people living on a street called 'BOUNDARY LANE' are the same road. Part of it is in `ParID` 10871, which links to `CEN_1901` 4640003, and another part is in `ParID` 10873, which links to `CEN_1901` 4640004. Elsewhere, two entries like this might just be two different roads with the same name in the same consistent parish unit but in different RSDs. If there were two roads, we'd know which 'BOUNDARY LANE' in the target geometry dataset to link to which 'BOUNDARY LANE' in the census. When two or more entries are the same street, it allows us to link to the correct part of a street. -->
<!-- We can safely say that the 109 people living on a 'BOUNDARY LANE' in the 'Chorlton Upon Medlock' sub-district of Manchester were living on a different street to the 2 people living on a 'BOUNDARY LANE' in Berkshire. But it's not clear at this stage if the 19 people also living on a 'BOUNDARY LANE' in Hulme, Manchester were living on a different street, or if actually this was the same 'BOUNDARY LANE' in 'Chorlton Upon Medlock' spanning boundaries. We'll revisit this shortly.

If we didn't know where each of these streets was, then it would be quite hard (and not very accurate) to link them to a GIS dataset of streets. 


There's a bunch of information about the geographical location of 'BOUNDARY LANE' in these listings. Straightaway we can see that 

Here's a snapshot of the census data: 

address|RegDist|SubDist|Parish|ParID|ConParID
--|--|--|--|--|--|
BOUNDARY LANE|Chorlton|Hulme|SOUTH MANCHESTER|10873|108139
BOUNDARY LANE|Chorlton|Chorlton Upon Medlock|SOUTH MANCHESTER|10871|108139

We've aggregated the data slightly here - we've removed house numbers, and we haven't listed everyone living on the street, leaving just the information about the street itself. We can link back to those living on it in 1901 a bit later. 

There are two entries for 'BOUNDARY LANE' here because some people living on it are classed as being in `ParID` 10873, while others are within `ParID` 10871. In other cases, two or more entries like this could just mean there are parishes with the same  

We start with parishes in 1851. I-CeM provides a lookup table that links each parish in this file to a consistent parish id in I-CeM. They have a full explanation of why they've done this here. Briefly, using consistent parish boundaries allows researchers to examine change over time in the census more easily because ....


-->
## I just want the data!

Add details here on how to access the data outputs.

# Contents
- [What is CensusGeocoder?](#What-is-CensusGeocoder?)
- [How does it work](#how-does-it-work)
- [I just want the data!](#i-just-want-the-data)
- [Pre-installation](#pre-installation)
- [Installation and setup](#installation)
  - [Set up a conda environment](#set-up-a-conda-environment)
  - [Method 1:](#method-1)
  - [Set Parameters](#set-parameters)
  - [Folder Structure and Data](#folder-structure-and-data)
<!-- - [Overview](#overview) -->
## [Inputs](#data-input)

#### Census
  - [Integrated Census Microdata (I-CeM)](#integrated-census-microdata-i-cem)

#### England and Wales Boundaries
  - [Parish Boundary Data](#parish-boundary-data-england-and-wales-only)
  - [Parish Boundary Lookup Table](#1851engwalesparishandplace-i-cem-lookup-table-england-and-wales-only)
  - [Registration Sub-District (RSD) Boundary Data](#registration-sub-district-rsd-boundary-data-england-and-wales-only)
  - [Registration Sub-District (RSD) Lookup Table](#registration-sub-district-rsd-lookup-table-england-and-wales-only)

#### Scotland Boundaries
  - [Historic Scottish Parishes GIS](#historic-scottish-parishes-gis-scotland-only)
  - [Historic Scottish Parishes Lookup Table](#historic-scottish-parishes-lookup-table-scotland-only)
  - [Urban Subdivisions](#urban-subdivisions-scotland-only)

#### Target Geometries
  - [Target Geometry Data](#target-geometry-data)
    - [GB1900 Gazetteer](#gb1900-gazetteer)
    - [OS Open Roads](#os-open-roads)

## [Outputs](#data-output)
- [String Comparison Parameters](#string-comparison-parameters)
- [Credit, re-use terms, and how to cite](#credit-re-use-terms-and-how-to-cite)
- [Acknowledgements](#acknowledgements)


## Pre-installation

`CensusGeocoder` relies on several datasets, which are deposited with the UK Data Service (UKDS). For some, all you need to do is register, and sign their standard end user licence. But for others (the names and addresses version of the census), the application is more involved. Please see individual datasets listed under [Data Input](#data-input) to see what you require from the UKDS. Then head over to their [website](https://ukdataservice.ac.uk) and follow their instructions for accessing the data.


## Installation

### Set up a conda environment

I recommend installation via Anaconda (refer to [Anaconda website and follow the instructions](https://docs.anaconda.com/anaconda/install/)).

* Create a new environment for `CensusGeocoder` called `geocoder_py38`:

```bash
conda create -n geocoder_py38 python=3.8
```

* Activate the environment:

```bash
conda activate geocoder_py38
```
<!-- ### Method 1

***Not added to pypi yet - use method 2***
* Install `CensusGeocoder`:

 ```bash
pip install CensusGeocoder
``` -->

### Method 1

* Clone `CensusGeocoder` source code:

```bash
git clone git@github.com:Living-with-machines/CensusGeocoder.git
```

* Install:

```bash
cd /path/to/CensusGeocoder
pip install -v -e .
```

Edit `/path/to/` as appropriate to the directory that you cloned `CensusGeocoder` into. E.g. `/Users/jrhodes/CensusGeocoder`

### To run

```bash
cd census_geocoder
python3 census_geocoder.py
```

### Set parameters
### Folder structure and data

The filepaths for all the input data can be set by the user in [input_config.yaml](inputs/input_config.yaml) - for further information see the respective section under [Data Input](#data-input). We recommend the following directory structure for  `configuration`, `data/input`, and `data/output`. 

The parent output directory can also set by the user in [gen_config.yaml](inputs/gen_config.yaml):

```yaml
general:
  output_path: "data/output/"
```

The directory structure of `data/output/` is created automatically by `CensusGeocoder`. It creates directories and sub-directories for each census year, country, and subset (if provided) and target geometry dataset. See [Data Output](#data-output) for more information.

## configuration
```bash

└── configuration
    ├── EW_1851_config.yaml
    ├── EW_1861_config.yaml
    ├── EW_1881_config.yaml
    ├── EW_1891_config.yaml
    ├── EW_1901_config.yaml
    ├── EW_1911_config.yaml
    ├── scot_1851_config.yaml
    ├── scot_1861_config.yaml
    ├── scot_1871_config.yaml
    ├── scot_1881_config.yaml
    ├── scot_1891_config.yaml
    ├── scot_1901_config.yaml
    ├── gen_config.yaml
    └── standardisation_files
        ├── gb1900_standardisation.json
        ├── icem_street_standardisation.json
        └── osopenroads_standardisation.json
```

## data/input
```bash
└── data
    └── input
        ├── census
        │   ├── 1851_ew_geocode.txt
        │   ├── 1861_ew_geocode.txt
        │   ├── ...
        ├── ew
        │   ├── 1851EngWalesParishandPlace
        │   │   └── ...
        │   ├── parish_dicts_encoding
        │   │   ├── 1851_ICeM_DICTIONARY_CODED_conparidadded.txt
        │   │   └── ...
        │   ├── icem_parish_lkup
        │   │   └── UKDS_GIS_to_icem.xlsx
        │   └── rsd_boundary_data
        │       └── ...
        ├── scot
        │   └── scot_parish_boundary
        │       ├── CivilParish1930
        │       │   └── ...
        │       ├── CivilParish_pre1891
        │       │   ├── ...
        │       │   └── scotland-parishes-1755-1891.xlsx
        │       ├── conrd_town_recid
        │       │   ├── conrd_town_recid_1851.txt
        │       ├── Scotland_ConRD_Town_1851_1901
        │       │   ├── Scotland_ConRD_Town_1951_1901.shp
        │       │   └── ...
        │       └── scotboundarylinking.xlsx
        └── target_geoms
            ├── osopenroads
            │   └── ...
            ├── gb1900
            │   └── gb1900_gazetteer_complete_july_2018.csv
            └── target_geom3
                └── ...
```

## Data Input
This is a list and discription of the datasets you need to download and save locally in order to run the scripts correctly. Each section below describes the dataset, citation and copyright details, and how to set parameters in the relevant section of configuration files for the census e.g. [EW_1851_config.yaml](configuration/EW_1851_config.yaml) or target geometry [targetgeom_config.yaml](configuration/targetgeom_config.yaml).


### Integrated Census Microdata (I-CeM)
Location: `data/inputcensus/`

#### Description

I-CeM is digitised individual-level 19th and early 20th century census data for Great Britain. It includes the information collected on individuals and households at each decenniel census in England and Wales 1851-1921 (except 1871), and Scotland 1851-1901 (1921 pending). `CensusGeocoder` was developed before the 1921 census data was made available, so the the configuraton files and current outputs are based on England and Wales census data up to 1911 and Scotland up to 1901. These are stored in 12 tab delimited files (6 for England and Wales, 6 for Scotland).

These files have been created by merging two versions of the I-CeM datasets together, which contain different types of information and have different access restrictions. You need both to perform geocoding on the full I-CeM dataset. There is an anonymised version ([SN 7481](http://doi.org/10.5255/UKDA-SN-7481-3)) and a 'Names and Addresses - Special Licence' version ([SN 7856](http://doi.org/10.5255/UKDA-SN-7856-2)). The anonymised version ([SN 7481](https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=7481)) is downloadable [here](https://icem.ukdataservice.ac.uk) via the UKDS after signing up to their standard end user licence.The anonymised version contains all census variables **except** individuals' names and addresses. These are stored in a 'Special Licence' version ([SN 7856](http://doi.org/10.5255/UKDA-SN-7856-2)). For 1921 (England and Wales) names and addresses data, you need [SN 9281](http://doi.org/10.5255/UKDA-SN-9281-1).

People in the anonymised and names/addresses datasets are linked by a unique id `RecID`.

Comprehensive documentation on I-CeM, including how it was created and the variables it contains can be found [here](https://www.campop.geog.cam.ac.uk/research/projects/icem/).

`CensusGeocoder` uses the following fields from these census files:

*England and Wales only

FIELD|DESCRIPTION|I-CeM Dataset
--|--|---
RecID|Unique id for each person|Anon + Names/Addresses
Address|Address (property, street, hamlet etc)|Names/Addresses
ConParID*|Consistent Parish ID|Anon
ParID|Parish IDs|Anon
RegCnty|Registration County|Anon

*Sample Data*
RecID|Address|ConParID*|ParID|RegCnty
--|--|--|--|--
1|23 High Street|12|21|Essex
2|23 High Street|12|21|Essex
3|23 High Street|12|21|Essex
4|23 High Street|12|21|Essex
5|25 High Street|12|21|Essex
6|25 High Street|12|21|Essex

#### Citation

>Schürer, K., Higgs, E. (2024). Integrated Census Microdata (I-CeM), 1851-1911. [data collection]. UK Data Service. SN: 7481, DOI: http://doi.org/10.5255/UKDA-SN-7481-3.
>
>Schürer, K., Higgs, E. (2020). Integrated Census Microdata (I-CeM) Names and Addresses, 1851-1911: Special Licence Access. [data collection]. 2nd Edition. UK Data Service. SN: 7856, DOI: http://doi.org/10.5255/UKDA-SN-7856-2

#### Parameters in [EW_1851_config.yaml](configuration/EW_1851_config.yaml)


```yaml
census:
  country: "EW" #specify country of census (can be named anything)
  year: 1851 #specify census year
  uid_field: "RecID" #name of census uid column
  field_to_geocode: "Address" #name of the column with values you want to geocode
  boundaries_field: ["ConParID", "CEN_1851"] #name of columns that contain boundary uids to link to boundary datasets
  subset_field: "subset_id" #name of column with values to subset geocoder results by, e.g. counties. subset_id is numeric codde for counties.
  census_file: "../data/input/census/1851_ew_geocode.txt" #path to the census file
  read_csv_params: #keyword arguments passed to pandas read_csv
    sep: "\t"
    encoding: "latin-1"
    quoting: 3
    na_values: [".", " ", " - "]
    # nrows: 1000000 #optionally limit rows read (e.g. for testing smaller samples of census data)
    usecols: ["RecID", "Address", "ParID", "subset_id"] #columns in census file to read

  field_to_clean: "Address" #name of column to apply standardisation and cleaning
  standardisation_file: "../configuration/icem_street_standardisation.json" # regex replacement file to clean/standardise field_to_clean
  min_len: 5 #mininum length in characters that field_to_clean must be, e.g. addresses less than min_length are not geo-coded
  cleaned_field_suffix: "_alt" #suffix added to field_to_clean name to distinguish original and cleaned columns

  unique_field_to_geocode_name: "address_uid" #name of column for storing unique ids for addresses in each geo-blocking unit

  write_processed_csv_params: #keyword arguments passed to pandas to_csv (used to write cleaned/processed versions of census data to file for inspection)
  sep: "\t"
  encoding: "utf-8"
  index: False

  write_processed_csv_params_slim: #keyword arguments passed to pandas to_csv when writing slimmed version of census data ready for geo-coding
  columns: ["address_uid", "Address_alt", "ConParID", "CEN_1851", "subset_id"]
  sep: "\t"
  encoding: "utf-8"
  index: False
```

### Parish Boundary Data (England and Wales ONLY)
Location: `data/input/ew/1851EngWalesParishandPlace`

#### Description

A shapefile (`.shp`) and associated files of 1851 Parish Boundary data for England and Wales. The boundary dataset looks like this:

![1851EngWalesParishandPlace](documentation/1851EngWalesParishandPlace.png "1851EngWalesParishandPlace")

This boundary dataset can be linked to I-CeM using [1851EngWalesParishandPlace I-CeM Lookup Table](#1851engwalesparishandplace-i-cem-lookup-table-england-and-wales-only) to create consistent parish geographies for England and Wales across the period 1851-1911. The consistent parish geographies are used by `CensusGeocoder` in conjunction with boundary datasets for Registration Sub Districts (RSD) to assign streets in target geometry datasets to a historic parish/RSD administrative unit (see [Overview](#overview) for more details.)

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

### 1851EngWalesParishandPlace I-CeM Lookup Table (England and Wales ONLY)
Location: `data/input/ew/icem_parish_lkup`

#### Description

**N.B. A new consistent parish system known as ConParID was created by the I-CeM team in 2024 but is not currently suitable for geo-blocking - the process described below is the old system. For information on the new ConParID, see [here](https://www.campop.geog.cam.ac.uk/research/projects/icem/limitations.html#geographyone).**



A lookup table that links I-CeM to the [above](#parish-boundary-data-england-and-wales-only) GIS of parish boundaries. This table enables us to dissolve the parish GIS to create 'consistent parishes' that can be linked to I-CeM. Download the lookup table here [add new link here to zenodo]()

`CensusGeocoder` only uses three fields from the lookup table, which are:

FIELD|DESCRIPTION
--|--
UKDS_ID|ID that links to `ID` [1851 Parish Boundary Data for England and Wales](#parish-boundary-data-england-and-wales-only)
conparid_51-91|Consistent parish ID for census years 1851 to 1891; links to `ConParID` in [Integrated Census Microdata (I-CeM)](#integrated-census-microdata-i-cem)
conparid_01-11|Consistent parish ID for census years 1901 and 1911; links to `ConParID` in [Integrated Census Microdata (I-CeM)](#integrated-census-microdata-i-cem)

UKDS_ID|conparid_51-91|conparid_01-11
--|--|--
977|1|100001
909|1|100001
925|2|100001

#### Citation

The old I-CeM website never provided a citation for this lookup dictionary.

#### Parameters in [EW_1851_config.yaml](configuration/EW_1851_config.yaml)

```yaml
boundaries:
  boundary_1:
    geom_name: "parish" #name of boundary used for labelling output files
    gis_file: "../data/input/ew/1851EngWalesParishandPlace/1851EngWalesParishandPlace_valid.shp" #path to boundary file
    gis_uid_field: "ID" #name of field containing uid values
    gis_read_params: #keyword arguments passed geopandas read_file
      engine: "pyogrio"
      columns: ["ID",]
      # max_features: 10000 #optionally limit number of features read (for sampling, testing etc)
    lkup_file: "../data/input/ew/icem_parish_lkup/UKDS_GIS_to_icem.xlsx" #corresponding lookup file to link boundary to census
    lkup_field_uid: "UKDS_ID" #name of uid field in lookup data
    lkup_field_censuslink: "conparid_51-91" #field with values that link to census
    lkup_read_params: #keyword arguments passed to pandas read_excel (or read_csv, if lkup is csv)
      sheet_name: "link"
      na_values: "."
      usecols: ["UKDS_ID", "conparid_51-91", ]
    gis_write_params: #keyword arguments passed to pandas to_csv when writing output of boundary (for inspection etc)
      sep: "\t"
      encoding: "utf-8"
      index: False
```

### Registration Sub-District (RSD) Boundary Data (England and Wales ONLY)
Location: `data/input/ew/parish_dicts_encoding`

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

#### Parameters in [EW_1851_config.yaml](configuration/EW_1851_config.yaml)

Set the path to the RSD Boundary shapefile (with associated files in the same directory). The `projection` should be the same as below when this file is accessible via UKDS.

```yaml
boundaries:
  boundary_2:
    geom_name: "rsd" #name of boundary used for labelling output files
    gis_file: "../data/input/ew/rsd_boundary_data/RSD_1851_1911_JR_valid.shp" #path to boundary file
    gis_uid_field: "CEN_1851" #name of field containing uid values
    gis_read_params: #keyword arguments passed geopandas read_file
      engine: "pyogrio"
      columns: ["CEN_1851"]
      # max_features: 10000
    gis_write_params: #keyword arguments passed to pandas to_csv when writing output of boundary (for inspection etc)
      sep: "\t"
      encoding: "utf-8"
      index: False
```
### Registration Sub-District (RSD) Lookup Table (England and Wales ONLY)
Location: `data/input/ew/rsd_boundary_data`

#### Description

**N.B. Due to changes in the ConParID system introduced in 2024, a `ConparID` variable has been added to these RSD Lookup Tables. Previously, the `ConParID` field in I-CeM could be linked to the [England and Wales Parish Lookup Table](#1851engwalesparishandplace-i-cem-lookup-table-england-and-wales-only). But the new version (2024) of I-CeM, a new ConParID system has been developed. In the 2024 version of I-CeM, the `ConParID` field links to a new GIS of consistent parishes NOT the old one. To address this, I have added the old `ConParID` values to these RSD lookup tables, so that when they are linked to I-CeM using the `ParID` variable, both the RSD id (e.g. `CEN_1851`) and `ConParID` are brought over.**

*In future we will not need these RSD lookup tables because the 2024 version of I-CeM contains the `CEN` variables. Pending a check of these CEN values against the old ones, we will add the CEN field to the census data read by the geocoder and remove this lookup table. A separate ConParID lookup for the old system will replace it.*

A series of data dictionaries for linking I-CeM to the RSD Boundary Data and Consistent Parish data. 6 files - one for each census year in I-CeM - that link the `ParID` field in I-CeM to a `CEN_****` (e.g. `CEN_1851`) field in the RSD Boundary data above and a 'ConParID' value that links to the `conparid_51-91` or `conparid_01-11` fields in the [England and Wales parish lookup table](#1851engwalesparishandplace-i-cem-lookup-table-england-and-wales-only)

`CensusGeocoder` uses the following fields from the lookup tables (this example is taken from the 1851 file):

FIELD|DESCRIPTION
--|--
ParID|Parish ID in [I-CeM](#integrated-census-microdata-i-cem)
CEN_1851|RSD ID in [RSD Boundary Data](#registration-sub-district-rsd-boundary-data-ew-only)
ConParID|Consistent parish identifier in [England and Wales parish lookup table](#1851engwalesparishandplace-i-cem-lookup-table-england-and-wales-only)

*Sample Data*

ParID|CEN_1851|ConParID
--|--|--
1|10001|1
2|10002|1

#### Citation
>Day, J.D. Registration sub-district boundaries for England and Wales 1851-1911 (2016). This dataset was created by the 'Atlas of Victorian Fertility Decline' project (PI: A.M. Reid) with funding from the ESRC (ES/L015463/1).

The RSD Lookup Dictionaries were supplied directly by Joe Day at the University of Bristol and Alice Reid at the University of Cambridge. They are in the process of being deposited with UKDS and the citation may change to reflect this in due course.

#### Parameters in [EW_1851_config.yaml](configuration/EW_1851_config.yaml)

Set the file path to the Registration Sub-District (RSD) Lookup Table under the `filepath` setting. This needs to be done for each census year. The other settings work for the files supplied at time of writing - they can be changed if necessary once these files are available via UKDS.

```yaml
census:
  lkups:
    conpar:
      lkup_file: "../data/input/ew/parish_dicts_encoding/1851_ICeM_DICTIONARY_CODED_conparidadded.txt" #path to lookup file
      lkup_uid_field: "ParID" #name of column containing uid values of lookup table
      lkup_census_field: "ParID" #name of column containing values that link to I-CeM
      lkup_params: #keyword arguments passed to pandas read_csv (or read_excel etc depending on file type)
        encoding: "utf-8"
        sep: "\t"
        quoting: 3
        usecols: ["ParID", "CEN_1851", "ConParID"]

```

### Historic Scottish Parishes GIS (Scotland Only)
Location: `data/input/scot/scot_parish_boundary`

There are Scottish parish boundary datasets for pre- and post-1891 civil parishes. A detailed discussion of the dataset and changes to the boundaries of Scottish parishes, see [National Records of Scotland - Historic Civil Parishes pre-1891](https://www.nrscotland.gov.uk/statistics-and-data/geography/our-products/other-national-records-of-scotland-nrs-geographies-datasets/historic-civil-parishes-pre-1891) and [National Records of Scotland - Civil Parishes (post 1891)](https://www.nrscotland.gov.uk/statistics-and-data/geography/our-products/other-national-records-of-scotland-nrs-geographies-datasets/civil-parishes). For further information on the major boundary changes around 1891, see also [Genuki](https://www.genuki.org.uk/big/sct/shennan/boundaries).

pre-1891|post-1891
--|--|
![Pre-1891 Scottish Parish Boundaries](documentation/pre-1891_scottish_parish.png "Pre-1891 Scottish Parish Boundaries")|![Post-1891 Scottish Parish Boundaries](documentation/post-1891_scottish_parish.png "Post-1891 Scottish Parish Boundaries")|


>add citation

#### Parameters of Historic Scottish Parishes GIS in [scot_1851_config.yaml](configuration/scot_1851_config.yaml)
```yaml
boundaries:
  boundary_1:
    geom_name: "scotparish"
    gis_file: "../data/input/scot/scot_parish_boundary/CivilParish_pre1891/CivilParish_pre1891.shp"
    gis_uid_field: "JOIN_NAME_"
    gis_read_params:
      engine: "pyogrio"
      columns: ["JOIN_NAME_"]
      # max_features: 1000
    gis_write_params:
      sep: "\t"
      encoding: "utf-8"
      index: False
    lkup_file: "../data/input/scot/scot_parish_boundary/scotboundarylinking.xlsx"
    lkup_field_uid: "JOIN_NAME_"
    lkup_field_censuslink: "merged_id"
    lkup_read_params:
      sheet_name: "1851_gis"
      na_values: "."
      usecols: ["JOIN_NAME_", "merged_id" ]
    gis_write_params:
      sep: "\t"
      encoding: "utf-8"
      index: False
```

### Historic Scottish Parishes Lookup Table (Scotland Only)
Location: `data/input/scot/scotboundarylinking.xlsx`

To link the Scottish parish boundary datasets to I-CeM, a lookup table has been created that associates each parish in the pre- and post-1891 boundary files with a corresponding parish in I-CeM. A separate lookup table for each census year has been produced to use the most appropriate boundary dataset (pre or post 1891). It links the Scottish parishes to the I-CeM `ParID` variable.

The structure of the lookup table is as follows:

FIELD|VALUE
--|--
"name" / "JOIN_NAME_"|Parish name from boundary dataset; "name" for post-1891, "JOIN_NAME_" for pre-1891.
ParID|ParID of corresponding parish in I-CeM
Notes|Additional comments.

Scotland, 1901 example:

name| ParID | notes
-- | -- | --
NEW CUMNOCK | 100595 |
OLD CUMNOCK | 100597 |
DAILLY | 100572 |
SMALL ISLES | 100119 |

#### Citation
> [Add full reference] 10.5281/zenodo.10473644

#### Parameters of Historic Scottish Parishes Lookup Table in [scot_1851_config.yaml](configuration/scot_1851_config.yaml)
```yaml
census:
  lkups:
    scot_parishes:
      lkup_file: "../data/input/scot/scot_parish_boundary/scotboundarylinking.xlsx"
      lkup_uid_field: "ParID"
      lkup_census_field: "ParID"
      lkup_params:
        sheet_name: "1851_icem"
        usecols: ["ParID", "merged_id", ]
    scot_conrdtowns:
      lkup_file: "../data/input/scot/conrd_town_recid/conrd_town_recid_1851.txt"
      lkup_uid_field: "recid"
      lkup_census_field: "RecID"
      lkup_params:
        sep: ","
        quoting: 3
        usecols: ["recid", "conrd_town", ]
```
### Urban Subdivisions (Scotland Only)
Location: `data/input/scot/Scotland_ConRD_Town_1851_1901`

These are GIS files of Consistent Registration Districts with urban subdivisions of Aberdeen, Dundee, Edinburgh, Glasgow, and Paisley in Scotland. For further information on the creation of consistent registration districts and urban subdivisions, see [here](https://doi.org/10.17863/CAM.94296).

The historic Scottish parishes are excellent for geo-blocking rural locations, but treat major urban centres as one unit. This is problematic because there are many streets with the same name in Glasgow and Edinburgh, so it's important to have geo-blocking units that sub-divide these urban centres to make sure people's addresses are geo-coded correctly.

Hannaliis Jaadla (University of Cambridge) kindly provided lookup tables that link these urban subdivisions to I-CeM using `RecID`. These are not currently openly available but alternative means of linking to I-CeM may use [Jaadla, H., &amp; Schurer, K. (2023)](https://doi.org/10.17863/CAM.95058).

#### Citation
>Satchell, A. (2023). Consistent Scottish registration district boundaries with subdivisions in large towns, 1851‒1901. Apollo - University of Cambridge Repository. https://doi.org/10.17863/CAM.94398
>
>Lookup tables - contact Hannaliis Jaadla (University of Cambridge) for access.


#### Parameters of Scottish Urban subdivisions GIS in [scot_1851_config.yaml](configuration/scot_1851_config.yaml)

```yaml
boundaries:
  boundary_2:
    geom_name: "scotconrdtown"
    gis_file: "../data/input/scot/Scotland_ConRD_Town_1851_1901/Scotland_ConRD_Town_1851_1901.shp"
    gis_uid_field: "ConRD_town"
    gis_read_params:
      engine: "pyogrio"
      columns: ["ConRD_town"]
      # max_features: 1000
    gis_write_params:
      sep: "\t"
      encoding: "utf-8"
      index: False
```

#### Parameters of Scottish Urban subdivisions Lookup Table in [scot_1851_config.yaml](configuration/scot_1851_config.yaml)

```yaml
census:
  lkups:
    scot_conrdtowns:
      lkup_file: "../data/input/scot/conrd_town_recid/conrd_town_recid_1851.txt"
      lkup_uid_field: "recid"
      lkup_census_field: "RecID"
      lkup_params:
        sep: ","
        quoting: 3
        usecols: ["recid", "conrd_town", ]
```

### Target Geometry Data

Currently, `CensusGeocoder` links I-CeM data to OS Open Roads and GB1900 but users can adjust [targetgeom_config.yaml](configuration/targetgeom_config.yaml) to link census data to any number of existing target geometry datasets in shapefiles, geojson, or comma/tab separated files. To add additional target geometries, just add a third heading, copying the existing layout in the yaml file.

#### GB1900 Gazetteer
Location: `data/input/gb1900`

##### Description

GB1900 file. Contains transcriptions of text labels from the Second Edition County Series six-inch-to-one-mile maps covering the whole of Great Britain, published by the Ordnance Survey between 1888 and 1914. As well as the labels, GB1900 Gazetteer contains the geographic coordinates of the labels (usually taken from the upper, left-hand corner of the label).

The version of the GB1900 Gazetteer used in this repo is the 'COMPLETE GB1900 GAZETTEER', which can be downloaded from [here](http://www.visionofbritain.org.uk/data/#tabgb1900).

##### Citation

It is available on a CC-BY-SA licence. Taken from the data documentation:

>Please reference this work as the "GB1900 Gazetteer" made available by the GB1900 Project. You must acknowledge "the Great Britain Historical GIS Project at the University of Portsmouth, the GB1900 partners and volunteers".

>You may call any work you derive from this dataset whatever you like EXCEPT that you must not name your work "the GB1900 gazetteer", or any other name including "GB1900" or "Great Britain 1900". When using or citing the work, you should not imply endorsement by the GB1900 project or by any of the project partners.

##### Parameters for GB1900 in [targetgeom_config.yaml](configuration/targetgeom_config.yaml)

```yaml
target_geom1:
  geom_name: "gb1900" #name of geometry data (can be anything you like)
  gis_file: "../data/input/target_geoms/gb1900/gb1900_gazetteer_complete_july_2018.csv" #path to file containing data
  gis_uid_field: "pin_id" #name of column containing uid values (e.g. unique id for each label in gb1900)
  gis_geocode_field: "final_text" #name of column containing addresses to compare to census addresses
  gis_lat_long: True #indicates that geometry data in file is split across two columns, one latitude/easting and one longitude/northing
  gis_long_field: "osgb_east" #name of column containing longitude/northing data
  gis_lat_field: "osgb_north" #name of column containing latitude/easting data
  gis_projection: "EPSG:27700" #projection of geometry data
  gis_read_params: #keyword arguments to pass to either pandas read_csv or geopandas read_file (depends on type of gis_file)
    encoding: "utf-16"
    sep: ","
    usecols: ["pin_id", "final_text", "osgb_east", "osgb_north", ]
    # nrows: 20000 #optionally use to limit size of data read (e.g. for sampling / testing)

  gis_field_to_clean: "final_text" #name of column containing values to clean
  gis_convert_non_ascii: True #whether non ASCII characters in gis_field_to_clean should be converted, mainly issue with Welsh place names
  gis_standardisation_file: "../configuration/standardisation_files/gb1900_standardisation.json" #path to standardisation file for cleaning gis_field_to_clean
  gis_min_len: 5 #minimum length in characters of gis_field_to_clean, discount entries that don't meet this threshold
  cleaned_field_suffix: "_alt" #suffix to add to gis_field_to_clean name to distinguish original from altered version
  dedup: True #whether entities in geometry should be deduplicated by identifying repeated GB1900 points with same name in each geo-blocking unit
  dedup_max_points: 2 #max number of duplicate entities per geo-blocking unit allowed; if more than then remove (deals with repeated non-address map labels present in GB1900, e.g. factory, quarry etc)
  dedup_max_distance_between_points: 1000 #max distance between duplicate labels after dropping duplicate entities exceeding dedup_max_points; distance depends on projection; this is 1000 meters. If duplicate GB1900 points closer than 1000m, then keep one of them, if not discard both (since near duplicates may be same road but with 2 map labels).

  item_per_unit_uid: "street_uid" #name of column containing uid values of each entity in target geometry dataset.

  gis_write_params: #keyword arguments to pass to pandas to_csv
    sep: "\t"
    encoding: "utf-8"
    index: False
```
---

#### OS Open Roads
Location: `data/input/osopenroads`

##### Description

Shapefiles and documentation from the Ordnance Survey's Open access modern road vector data. Available here to download: https://www.ordnancesurvey.co.uk/business-government/products/open-map-roads.

The original download `oproad_essh_gb-2` contains a `data` folder, which stores `RoadLink` and `RoadNode` files. CensusGeocoder only requires the `RoadLink` files. For ease, these have been combined into a single shapefile when being read into `CensusGeocoder`. <!-- Potentially add link to code that does this -->

##### Citation

Taken from the Ordance Survey website:

>Our open data products are covered by the Open Government Licence (OGL), which allows you to: copy, distribute and transmit the data;
adapt the data; and
exploit the data commercially, whether by sub-licensing it, combining it with other data, or including it in your own product or application.
We simply ask that you acknowledge the copyright and the source of the data by including the following attribution statement: Contains OS data © Crown copyright and database right 2022.

##### Parameters for OS Open Roads in [targetgeom_config.yaml](configuration/targetgeom_config.yaml)

```yaml
target_geom2:
  geom_name: "osopenroads"
  gis_file: "../data/input/target_geoms/osopenroads/osopenroads.shp"
  gis_uid_field: "nameTOID"
  gis_convert_non_ascii: True
  gis_standardisation_file: "../configuration/standardisation_files/osopenroads_standardisation.json"
  gis_geocode_field: "name1"
  gis_field_to_clean: "name1"
  cleaned_field_suffix: "_alt"

  gis_read_params:
    engine: "pyogrio"
    columns: ["nameTOID", "name1", ]
    # max_features: 10000

  item_per_unit_uid: "street_uid"

  gis_write_params:
    sep: "\t"
    encoding: "utf-8"
    index: False
```

### Data Output

```bash
└── output
        └── EW
            └── 1851
                ├── 0
                │   ├── EW_1851_address_uid_0.tsv
                │   ├── EW_1851_census_for_linking_0.tsv
                │   ├── EW_1851_cleaned_0.tsv
                │   ├── EW_1851_gb1900_competing_matches_0.tsv
                │   ├── EW_1851_gb1900_matches_lq_0.tsv
                │   ├── EW_1851_gb1900_matches_0.tsv
                │   ├── EW_1851_osopenroads_competing_matches_0.tsv
                │   ├── EW_1851_osopenroads_matches_lq_0.tsv
                │   ├── EW_1851_osopenroads_matches_0.tsv
                ├── 1
                │   ├── EW_1851_address_uid_1.tsv
                │   └── ...
                ├── ...
                ├── gb1900
                │   ├── EW_1851_gb1900_deduped_distcount.tsv
                │   ├── EW_1851_gb1900_deduped_distcount2.tsv
                │   ├── EW_1851_gb1900_processed.tsv
                │   ├── EW_1851_gb1900_slim.tsv
                │   ├── EW_1851_gb1900_standardised.tsv
                ├── osopenroads
                │   ├── EW_1851_osopenroads_deduped_nodistcalc.tsv
                │   ├── EW_1851_osopenroads_processed.tsv
                │   ├── EW_1851_osopenroads_slim.tsv
                │   ├── EW_1851_osopenroads_standardised.tsv
                ├── parish
                │   └── EW_1851_parish_processed.tsv
                ├── parish_rsd
                │   └── EW_1851_parish_rsd_processed.tsv
                └── rsd
                    └── EW_1851_rsd_processed.tsv
```
Output files for each target geometry dataset and census year/country are written to separate directories. For each partition of the census (e.g. a county), 3 types of delimited text files are output to the corresponding directories `linked`, `linked duplicates`, `lookup`.

Filenames are structured as follows:
`{census_country}_{census_year}_{target_geometry_name}_{partition_value}`

with `link`, `linkdup`, or `lkup` appended to the end as appropriate, e.g.

e.g. `EW_1851_gb1900_Durham_lkup`.

---

#### Linked

Census addresses considered a match to an address in the target geometry dataset.

fields|
-|
target geometry address|
census address unique id|
target geometry address unique id|
census address|
tfidf weighting|
fuzzy string comparison score|
weighted fuzzy string comparison score|

*Sample output*

final_text|unique_add_id|gb1900_1851|address_anonymised|tfidf_w|rapidfuzzy_wratio_s|rapidfuzzy_wratio_ws|
--|--|--|--|--|--|--|
SOUTH HILL PARK|BAGSHOT ROAD AND SOUTH HILL PARK_1452.0_1300001.0|5815d6182c66dc3849011ef2_1452.0_1300001|BAGSHOT ROAD AND SOUTH HILL PARK|0.0743637355789496|0.9|0.06692736202105463|
BARTHOLOMEW STREET|BARTHOLOMEW STREET  SHAWS COURT_1260.0_1200002.0|5848759c2c66dcdcda000168_1260.0_1200002|BARTHOLOMEW STREET  SHAWS COURT|0.06117412360590356|0.9|0.05505671124531321|
BARTHOLOMEW STREET|BARTHOLOMEW STREET  STILLMANS COTTAGES_1260.0_1200002.0|5848759c2c66dcdcda000168_1260.0_1200002|BARTHOLOMEW STREET  STILLMANS COTTAGES|0.05017107492325159|0.9|0.04515396743092643|

---

#### Linked duplicates

Census addresses with > 1 match to an address in the target geometry dataset.

The fields are the same as the `Linked` output:

fields|
-|
target geometry address|
census address unique id|
target geometry address unique id|
census address|
tfidf weighting|
fuzzy string comparison score|
weighted fuzzy string comparison score|

*Sample output*

name1|unique_add_id|os_open_roads_1851|address_anonymised|tfidf_w|rapidfuzzy_wratio_s|rapidfuzzy_wratio_ws|
--|--|--|--|--|--|--|
OLD BRACKNELL LANE EAST|BRACKNELL_1452.0_1300001.0|osgb4000000023476747_1452.0_1300001|BRACKNELL|0.1111111111111111|0.9|0.09999999999999999
BRACKNELL ROAD|BRACKNELL_1452.0_1300001.0|osgb4000000023487824_1452.0_1300001|BRACKNELL|0.1111111111111111|0.9|0.09999999999999999
OLD BRACKNELL LANE WEST|BRACKNELL_1452.0_1300001.0|osgb4000000023488088_1452.0_1300001|BRACKNELL|0.1111111111111111|0.9|0.09999999999999999

---

#### Lookup

Unique ids for individuals from the census for each census address and target geometry in [Linked](#linked).

*Sample output*

unique census id (e.g. RecID)|unique geometry id (e.g. gb1900_EW_1851)
--|--
20|52f1d84fd9dbf10005000574_12709.0_6230001
40|5360c84879ff6e000d001256_12753.0_6230006
41|52cd3f9cba830e0005003ba1_12737.0_6230004

---

#### New geometry file

For each target geometry dataset, an output file is written containing the geometry data with added historic administrative unit ids for that census country and year. Additionally, linestring geometries are split or combined depending on whether they run across multiple administrative boundaries.

*Sample output for OS Open Roads, England and Wales 1901*

field|description
--|--
new unique id (e.g. `os_open_roads_EW_1901`)|new unique id for street constructed from target geometry unique id field and historic administrative unit id(s); e.g. `osgb4000000006295134` (OS Open Roads ID) + `109960.0` (conparid_01-11 - Consistent Parish ID for 1901) + `5610001` (CEN_1901 - RSD Unique ID for 1901) = `osgb4000000006295134_109960.0_5610001`
target geometry unique id (e.g. `nameTOID`)|original unique id from target geometry dataset; e.g. `osgb4000000006295134`
target geometry address field (e.g. `name1`)|e.g. `FOREST DRIVE`
consistent parish id (e.g. `conparid_01-11`)|consistent parish ID for 1901, e.g. `109960.0`
registration sub-district id (e.g. `CEN_1901`)|registration sub-district id for 1901, e.g. `561001.0`
geometry|Linestring geometry data


```json
{
"type": "FeatureCollection",
"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::27700" } },
"features": [
{ "type": "Feature", "properties": { "os_open_roads_EW_1901": "osgb4000000006295134_109960.0_5610001", "nameTOID": "osgb4000000006295134", "name1": "FOREST DRIVE", "conparid_01-11": 109960.0, "CEN_1901": 5610001.0 }, "geometry": { "type": "LineString", "coordinates": [ [ 373661.0, 599187.0, 0.0 ], [ 373630.13, 599178.060000000055879, 0.0 ], [ 373599.270000000018626, 599169.12, 0.0 ] ] } },
{ "type": "Feature", "properties": { "os_open_roads_EW_1901": "osgb4000000006295135_109958.0_5610001", "nameTOID": "osgb4000000006295135", "name1": "COTTONSHOPE ROAD", "conparid_01-11": 109958.0, "CEN_1901": 5610001.0 }, "geometry": { "type": "LineString", "coordinates": [ [ 378191.35999999998603, 603573.690000000060536, 0.0 ], [ 378226.19, 603658.060000000055879, 0.0 ], [ 378317.0, 603878.0, 0.0 ], [ 378433.169999999983702, 604220.520000000018626, 0.0 ], [ 378646.0, 604848.0, 0.0 ], [ 378665.0, 604869.0, 0.0 ] ] } }]
}
```

By default, the files are output as `.geojson` files in the same projection as the historic boundary datasets and OS Open Roads and GB1900, which is `EPSG:27700`. Users can change these settings in [input_config.yaml](inputs/input_config.yaml). These parameters are passed to geopandas [GeoDataFrame.to_file](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.to_file.html). Currently, you can change the projection of the output geometries to either `EPSG:3857` or `EPSG:4326` (northings, easting will be converted to longlat).

```yaml
output_params:
  file_type: ".geojson"
  crs: "EPSG:27700"
  driver: "GeoJSON"
```
---

#### Summary

Delimited text file containing summary statistics on the proportions of people linked according to each census partition.

Fields|Description|
--|--|
partition|Census partition, e.g. a county|
inds_link|Number of individuals linked to a target geometry|
adds_link|Number (unique count) of addresses linked to target geometry|
adds_linkdup_count|Number (unique count) of addresses with > 1 match to target geometry|
inds_all|Number of all individuals in census partition|
adds_all|Number (unique count) of all addresses in census partition|
inds_link_perc|Percentage of all individuals linked to target geometry|
adds_link_perc|Percentage of all addresses linked to target geometry|
adds_linkdup_perc|Percentage of all addresses with > 1 match to target geometry|

*Sample output*

RegCnty|inds_linked|adds_linked|adds_duplink_count|inds_all|adds_all|inds_linked_perc|adds_linked_perc|adds_duplink_perc
--|--|--|--|--|--|--|--|--|
Anglesey|261|43|1|4257|2176|6.13107822410148|1.9761029411764706|0.04595588235294117
Bedfordshire|1875|192|3|12827|1668|14.617603492632728|11.510791366906476|0.1798561151079137
Berkshire|1984|244|12|19583|3184|10.13123627636215|7.663316582914573|0.37688442211055273
Brecknockshire|332|32|2|5978|2531|5.553696888591502|1.264322402212564|0.07902015013828526

## String Comparison Parameters

There are lots of different algorithms for comparing the similarity of two text strings. `CensusGeocoder` allows you to choose from a variety of fuzzy string comparison algorithms.

The default string comparison is an implementation of `partial_ratio` from the [rapidfuzz](https://github.com/maxbachmann/RapidFuzz) library.

Alternatively, you can use `WRatio`, also from the [rapidfuzz](https://github.com/maxbachmann/RapidFuzz) library.

Other string comparison algorithms are made available via the [recordlinkage](https://recordlinkage.readthedocs.io/en/latest/index.html) library, which uses the [jellyfish](https://github.com/jamesturk/jellyfish) library for its string algorithms. You can view the list of algorithms accepted by `recordlinkage` [here](https://recordlinkage.readthedocs.io/en/latest/ref-compare.html#module-recordlinkage.compare).

As of August 2022, these are: 
> "jaro", "jarowinkler", "levenshtein", "damerau_levenshtein", "qgram" or "cosine"

Each algorithm computes a similarity score of two text strings between 0 and 1. The closer to 1, the more similar the two strings are.

For a discussion of the implications for using these algorithms, see #21.

<!-- NB algorithms like `Wratio` also look for shorter strings in longer strings, e.g. comparing 'PARK ROAD' would result in a score of 1 when compared to 'HYDE PARK ROAD' because the input shorter string matches exactly to a portion of the longer string. This needs to be treated with caution but is often useful for linking descriptions of addresses that would otherwise result in a low similarity score e.g. 'BACK NEW ROAD' or 'FRONT NEW ROAD' score 1 against 'NEW ROAD' using `Wratio` but lower using `levenshtein` for example. -->

You can set the minimum similarity threshold for two candidates to be considered a match using `sim_thresh`.


```yaml
comparison_params:
  sim_thresh: 0.85 # similarity threshold for string comparison
  string_comp_alg: "rapidfuzzy_wratio" # default
```

## Credit, re-use terms, and how to cite
`CensusGeocoder` relies on several datasets that require you to have an account with the UK Data Service (UKDS) to sign their standard end user licence. Please see individual datasets listed under [Data Inputs](#data-input)

## Acknowledgements

This work was supported by Living with Machines (AHRC grant AH/S01179X/1) and The Alan Turing Institute (EPSRC grant EP/N510129/1). Living with Machines, funded by the UK Research and Innovation (UKRI) Strategic Priority Fund, is a multidisciplinary collaboration delivered by the Arts and Humanities Research Council (AHRC), with The Alan Turing Institute, the British Library and the Universities of Cambridge, East Anglia, Exeter, and Queen Mary University of London.

Thanks to Joe Day and Alice Reid for supplying RSD Boundary data and lookups prior to their deposit with the UK Data Service.



<!-- Optionally, set `standardisation_file` to the path to a json standardisation file containing regex replacements to apply to the address field of the target geometry data.

For example:

```json
{
	"\\sST\\.$|\\sST$":" STREET",
	"\\sRD\\.$|\\sRD$":" ROAD",
	"\\sPL\\.$|\\sPL$":" PLACE"
}
``` -->

The `comparison_params` allow you to adjust the string comparison parameters when comparing address fields between the census and a target geometry dataset. See [String Comparison Parameters](#string-comparison-parameters) for more information.

