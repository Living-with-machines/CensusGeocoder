# historic-census-gb-geocoder

Geocode Historic Great British Census Data 1851-1911

## How to run

*I've added some details here that you wouldn't normally find in a section like this - can remove when made public.*

### 1. Connect to VM

Connect to the census-geocoder VM on Azure. Navigate to `/datadrive`. There should be a `data/` folder in this directory, which is connected via blobfuse to `--account-name censusplacelinking` `--container-name data`. There should also be a clone of the github repo `historic-census-gb-geocoder`. Make sure that's it's up-to-date and running off the `main` branch.

To set the parameters of the geocoding script, you need to edit `data/historic-census-gb-geocoder-params.json`.

The file will look something like this. Change "no" to either "testing" or "full" depending on if you want to run the geocoding script on the full datasets (e.g. all census entries, all OS Roads, and all GB1900) or if you want to just run it on a sample of those for testing purposes.

```json
{"EW_1851":"no",
"EW_1861":"no",
"EW_1881":"no",
"EW_1891":"no",
"EW_1901":"no",
"EW_1911":"no",
"scot_1851":"no",
"scot_1861":"no",
"scot_1871":"no",
"scot_1881":"no",
"scot_1891":"no",
"scot_1901":"testing"}
```
### 2. Enter the following in the terminal

Activate the python virtual environment, using:

`conda activate geocode_env`

To run the script:

`python3 historic-census-gb-geocoder/historic-census-gb-geocoder/historic_census_gb_geocoder.py`

Alternatively, to allow the script to carry on running even after you've exited your session (but have left the VM on), use instead:

`nohup python3 /historic-census-gb-geocoder/historic-census-gb-geocoder/historic_census_gb_geocoder.py &`

This will write the print statements to `nohup.out` in the `/datadrive` folder. You can view the progress by entering:

`clear`

Followed by

`tail -f nohup.out`

Press Control + C to stop viewing the output, and enter `exit` to quit the session. The script will carry on running in the background.

## Documentation

### Data Input
This is a list and discription of the datasets you need to download and store in `data/input` in order to run the scripts correctly.

#### 1. Integrated Census Microdata (I-CeM)

*Some information here is specific to LwM Project because of the need to ingress and egress between Tier 1 and Tier 3 DataSafeHaven. Readme and code will need editing to remove safehaven steps upon public release.*

`census_anonymisation_egress` contains igitised individual-level 19th and early 20th century census data for Great Britain, covering England and Wales 1851-1911 (except 1871), and Scotland 1851-1901.

 There are two versions of I-CeM with different access restrictions. You need both to perform geocoding on the full I-CeM dataset. There is an anonymised version ([SN 7481](https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=7481)) and a 'Names and Addresses - Special Licence' version ([SN 7856](https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=7856)). The anonymised version ([SN 7481](https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=7481)) is downloadable via the UKDS after signing up to their standard end user licence. The anonymised version does not contain individuals' names and addresses but contains a unique id `RecID` for each person that links them to their name and address held in the 'Special Licence' version ([SN 7856](https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=7856)). As its name suggests, access to the name and address data in I-CeM is by application for a special licence, which requires review by UKDS and the owners ([Findmypast](https://www.findmypast.co.uk)) of the transcriptions on which I-CeM is based.

Further documentation on I-CeM, including how it was created and the variables it contains can be found [here](https://www.essex.ac.uk/research-projects/integrated-census-microdata).


#### 2. 1851 Parish Boundary Data for England and Wales (ENGLAND AND WALES ONLY)
`data/input/1851EngWalesParishandPlace` contains a shapefile (`.shp`) and associated files of 1851 Parish Boundary data for England and Wales.
![1851EngWalesParishandPlace](documentation/1851EngWalesParishandPlace.png "1851EngWalesParishandPlace")

This boundary dataset can be linked to I-CeM using `UKDS_GIS_to_icem.xlsx` (see point 7 below) to create consistent parish geographies for England and Wales across the period 1851-1911.

The files and documentation explaining the creation of the boundaries and the fields in the dataset are available from the UKDS [here](https://reshare.ukdataservice.ac.uk/852816/). Access to the files requires registration with the UKDS. The Documentation is open access.

Citation:

>Satchell, A.E.M and Kitson, P.K and Newton, G.H and Shaw-Taylor, L. and Wrigley, E.A (2018). 1851 England and Wales census parishes, townships and places. [Data Collection]. Colchester, Essex: UK Data Archive. 10.5255/UKDA-SN-852232


#### 3. Ordnance Survey Open Roads
`data/input/oproad_essh_gb-2` contains shapefiles and documentation from the Ordnance Survey's Open access modern road vector data. Available here to download: https://www.ordnancesurvey.co.uk/business-government/products/open-map-roads.

`oproad_essh_gb-2` contains a `data` folder, which stores `RoadLink` and `RoadNode` files. historic-census-gb-geocoder only requires the `RoadLink` files.

#### 4. Registration Sub-District (RSD) Boundary Data (ENGLAND AND WALES ONLY)

*Supplied directly by Joe Day at Bristol and Alice Reid at Cambridge - supposedly in the process of being deposited with UKDS. Update this when link to UKDS ready.*

`data/input/rsd_boundary_data` contains a shapefile and associated files of boundary data for Registration Sub-Districts in England and Wales 1851-1911. The correct RSD boundaries for each year are created by 'dissolving' the geometries on the appropriate `CEN` field, e.g. `CEN_1851` to create 1851 boundaries or `CEN_1901` to create 1901 boundaries.

#### 5. Parish-Registration Sub-District (RSD) Dictionaries (ENGLAND AND WALES ONLY)

*Supplied directly by Joe Day at Bristol and Alice Reid at Cambridge - supposedly in the process of being deposited with UKDS. Update this when link to UKDS ready.*

*Folder contains the word 'encoding' because the original files given to us weren't reading correctly (no matter which encoding I specified) so I re-encoded them to 'utf-8' to get them to work. This could be tidied up in future.*

`parish_dicts_encoding` contains a series of data dictionaries for linking I-CeM to the RSD Boundary Data (point 4 above). Ignore `finalEWnondiss1851_1911.txt`, `PAR1851_RSD_MATCH.txt` and `1871_DICTIONARY_CODED.txt`.

The dictionaries link the `CEN` fields in the RSD Boundary Data, e.g. `CEN_1851` to unique parish identifier `ParID` in I-CeM. For example, the 1851 dictionary lists each `ParID` in the 1851 census file and the corresponding `CEN_1851`. This tells us which parish lies within which registration sub-district.

#### 6. GB1900 Gazetteer

`gb1900_gazetteer_complete_july_2018.csv` contains transcriptions of text labels from the Second Edition County Series six-inch-to-one-mile maps covering the whole of Great Britain, published by the Ordnance Survey between 1888 and 1914. As well as the labels, GB1900 Gazetteer contains the geographic coordinates of the labels (usually taken from the upper, left-hand corner of the label).

The version of the GB1900 Gazetteer used in this repo is the 'COMPLETE GB1900 GAZETTEER', which can be downloaded from [here](http://www.visionofbritain.org.uk/data/#tabgb1900). It is available on a CC-BY-SA licence.

#### 7. 1851EngWalesParishandPlace I-CeM Lookup Table (ENGLAND AND WALES ONLY)



#### 8. Street Standardisation

*The naming conventions need to be improved here - this file is for use with the GB1900 Gazetteer.*

*There is plenty of scope for expanding the range of regex patterns used to clean the address strings.*

`street_standardisation.json` - contains regex patterns to find and replacement words. Currently used to expand abbreviations in GB1900 Gazetteer, e.g. Rd to Road.

#### 9. I-CeM Street Standardisation

*There is plenty of scope for expanding the range of regex patterns used to clean the address strings.*

`icem_street_standardisation.json` - contains regex patterns to find and replacement words. Currently used to expand abbreviations in I-CeM, e.g. Rd to Road. Also removes extra letters left at the start of the address strings after removing digits (to comply with safehaven rules). E.g. '68A High Street' leaves 'A High Street', which is then cleaned to 'High Street'.

#### 10. Scotland Parish Boundary data (SCOTLAND ONLY)

`scot_parish_boundary/` - contains two Scottish parish boundary files and a lookup table that links the boundary files to I-CeM.

There are Scottish parish boundary datasets for pre- and post-1891 civil parishes. A detailed discussion of the dataset and changes to the boundaries of Scottish parishes, see [National Records of Scotland - Historic Civil Parishes pre-1891](https://www.nrscotland.gov.uk/statistics-and-data/geography/our-products/other-national-records-of-scotland-nrs-geographies-datasets/historic-civil-parishes-pre-1891) and [National Records of Scotland - Civil Parishes (post 1891)](https://www.nrscotland.gov.uk/statistics-and-data/geography/our-products/other-national-records-of-scotland-nrs-geographies-datasets/civil-parishes). For further information on the major boundary changes around 1891, see also [Genuki](https://www.genuki.org.uk/big/sct/shennan/boundaries).

`scot_parish_boundary/CivilParish_pre1891/` - contains the shapefile and associated files for pre-1891 Scottish parish boundaries.

`scot_parish_boundary/CivilParish1930` - contains the shapefile and associated files for post-1891 Scottish parish boundaries.

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


### Data Output

*Needs adding 






