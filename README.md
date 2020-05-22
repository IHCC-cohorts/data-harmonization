# IHCC Data Harmonization

This is work-in-progress on a demonstration system that uses ontologies to harmonize data on various cohorts for the [International HundredK+ Cohorts Consortium (IHCC)](https://ihcc.g2mc.org).

## Running the Build

TODO


## Adding a New Cohort

First, clone this repository to your local machine and create a new branch. Then, follow the following steps and make a pull request with all required changes.

### 1. Selecting a Short Name and Prefix

The "short name" will be the lowercase name used for all files generated for your cohort. Some guidelines to follow when selecting a short name are:
- select a name that is unique and easy to remember (e.g., [Golestan Cohort Study](https://dceg2.cancer.gov/gemshare/) = `gcs`)
- use an acronyms (e.g., [South African Population Research Infrastructure Network (SAPRIN)](http://saprin.mrc.ac.za/) = `saprin`)
- replace spaces with dashes (e.g., [Genomics England](https://www.genomicsengland.co.uk/) = `genomics-england`)

Your prefix should be your short name in uppercase (e.g, `gcs` = `GCS`), unless there is some reason to change it. You should shorten your prefix if your short name uses more than one word (e.g., `genomics-england` = `GE`). We request that you do not use underscores in your prefix. Like the short names, prefixes **must** be unique across all cohorts.

### 2. Creating the ROBOT Template

Cohort data dictionaries are transformed into OWL ontologies using [ROBOT templates](http://robot.obolibrary.org/template). All new cohorts must provide a tab on our [ROBOT template Google spreadsheet](https://docs.google.com/spreadsheets/d/1FwYYlJPzFAAItZyaKY2YnP01yQw6BkARq3CPifQSx1A) with their data dictionary in this format. Name this tab with your chosen cohort short name. We recommend that you take a moment to briefly look over the template documentation, but you do not need to read it in-depth; we will provide all required template strings below.

The following information is **required**:
- ID
- Label

All IDs **must** be unique and must be in [CURIE](https://en.wikipedia.org/wiki/CURIE) format. Use the prefix you've chosen in the last step as the namespace. We recommend that you use 7-digit numeric IDs (e.g., `GCS:0000001`), but if you already have IDs for your items you may reuse those (e.g., `MAELSTROM:Blood_immune_dis`). Please note that IDs are case sensitive and once an ID has been created for a term, that ID is **permanent**.

We recommend that all labels be unique, as well, but this is not required.

The following information is **highly recommended**:
- **Parent**: category under which this data item falls (this must also be defined in your data dictionary)
- **Definition**: one-sentence description of what kind of data is collected for this item

The following information is optional:
- **Comment**: an editor's comment about this data dictionary item
- **Answer Type**: type of answer (e.g., numerical, date, etc.)
- **Formula**: formula to determine this data value, if calculated
- **Measurement Time**: time period for which is data is collection (e.g., over time?)
- **Question Description**: the question asked to collect this data

If you need another property to describe your data dictionary items, please let us know by [opening a new issue](https://github.com/IHCC-cohorts/data-harmonization/issues/new). The properties must be added to our repository before they can be used in a template.

The first row of the spreadsheet should be human-readable column headers. The second row will be the [ROBOT template strings](http://robot.obolibrary.org/template) for each column. The third row should be left empty for future validation. The data dictionary entries should start on row 4.

The basic ROBOT template strings are as follows (note that the `A` and `C` characters in the template strings are necessary for ROBOT to properly parse the contents of a column):
- ID: `ID`
- Label: `LABEL`
- Parent: `C % SPLIT=|`
- Definition: `A definition`
- Comment: `A comment`
- Answer Type: `A answer type`
- Question Description: `A question description`

The table may end up looking something like this:
| ID | Label | Parent | Definition |
| --- | --- | --- | --- |
| ID | LABEL | C % SPLIT=\| | A definition |
| | | |
| EX:0000000 | Date of Birth | Patient Data | Date of birth of patient |

Any parent used in column 3 must also be defined in the table, otherwise ROBOT will not be able to parse the row. If you have an item with more than one parent, you can separate the parents with a pipe symbol (e.g., `Parent 1|Parent 2`).

### 3. Creating the GECKO Mappings

The cohort browser is driven by [GECKO](). In order to display results for your cohort in the browser, you must map your data dictionary items to the GECKO terms.
<!-- TODO: link to GECKO? -->

To start, add a tab to the [master GECKO mapping sheet](https://docs.google.com/spreadsheets/d/1IRAv5gKADr329kx2rJnJgtpYYqUhZcwLutKke8Q48j4). This tab **must** be named with the cohort short name. You may need to request edit access to this sheet to proceed.

Each mapping sheet is also a ROBOT template. The first four columns and their ROBOT template strings are as follows:
- ID: `ID`
- Label: no ROBOT template string (labels are already defined by your first Google sheet, so ROBOT only needs the IDs)
- Mapping Type: `CLASS_TYPE`
- GECKO Term: `C % SPLIT=|`

You can add additional details starting in column 5 (e.g., comments, parents). These additional details *do not* need ROBOT template strings.

| ID | Label | Mapping Type | GECKO Term |
| --- | --- | --- | --- |
| ID | | CLASS_TYPE | C % SPLIT=\| |
| ID of term from your data dictionary | Label of term from your data dictionary | type of mapping (this determines what kind of OWL axiom is created): `subclass` (close-match, more specific) or `equivalent` (exact) | GECKO term to map to (referred to by label) |
| EX:0000000 | Date of Birth | subclass | Age/birthdate |
 
If a term from your data dictionary maps to more than one GECKO term, you can include multiple mappings in column 4 by separating the values with a pipe symbol (e.g., `Term 1|Term 2`).

Include *all* your data dictionary IDs and Labels to begin. You can leave columns 3 and 4 empty for these rows until you have started your mappings. All GECKO terms can be found in the [index of the master mapping sheet](https://docs.google.com/spreadsheets/d/1IRAv5gKADr329kx2rJnJgtpYYqUhZcwLutKke8Q48j4/edit#gid=1049779000). You can also browse a hierarchical version of GECKO [here]().
<!-- TODO: link to GECKO tree view -->

### 4. Adding the Cohort Metadata

#### `data/metadata.json`

Using the following template, add an entry to [`data/metadata.json`](https://github.com/IHCC-cohorts/data-harmonization/blob/master/data/metadata.json):
```
"[full cohort name]": {
	"id": "[cohort short name]",
	"prefix": "[cohort prefix]",
	"data_dictionary": "[link to cohort's data dictionary in ROBOT template format]",
	"mapping": "[link to cohort's tab in the master mapping document]"
}
```

Please note that the `[full cohort name]` **must** match the name recorded in [`data/member_cohorts.csv`](https://github.com/IHCC-cohorts/data-harmonization/blob/master/data/member_cohorts.csv).
<!-- TODO: what if the cohort is not listed? -->

#### `src/prefixes.json`

Using the following template, add an entry to [`src/prefixes.json`](https://github.com/IHCC-cohorts/data-harmonization/blob/master/src/prefixes.json):
```
"[cohort prefix]": "http://example.com/[cohort prefix]_"
```

### Metadata Header

You must also create a turtle-format header containing your cohort's metadata, which will be included in the ontology version of your cohort data dictionary.

To do this, create a new file in the `metadata` directory using this name: `[cohort short name].ttl`. Then, paste this template in that file and replace any square brackets. Do not change anything else.
```
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix dcterms: <http://purl.org/dc/terms/>.
@prefix prov: <http://www.w3.org/ns/prov#> .

<>
  rdf:type owl:Ontology ;
  dcterms:title "[full cohort name]" ;
  dcterms:description "[one-sentence description of your data dictionary]" ;
  dcterms:license <[link to license]> ;
  dcterms:rights "[text description of license]" .
```

### 5. Updating the Makefile

Before updating the [`Makefile`](https://github.com/IHCC-cohorts/data-harmonization/blob/master/Makefile), make sure you have done the following:
1. Selected a short name & prefix
2. Created a ROBOT template tab in the [ROBOT templates Google sheet](https://docs.google.com/spreadsheets/d/1FwYYlJPzFAAItZyaKY2YnP01yQw6BkARq3CPifQSx1A) containing all data dictionary items
3. Created a tab for the cohort in the [master GECKO mappings sheet](https://docs.google.com/spreadsheets/d/1IRAv5gKADr329kx2rJnJgtpYYqUhZcwLutKke8Q48j4) and added data dictionary items to this sheet
4. Added entries in `data/metadata.json` and `src/prefix.json`
5. Created a TTL header in the `metadata` folder

To add your cohort to the build, simply add the cohort short name to the [list on line 89](https://github.com/IHCC-cohorts/data-harmonization/blob/master/Makefile#L89). Next, run `make update` to ensure all tasks complete properly. This should generate all build files for your cohort, and add your cohort to [`index.html`](). Open the index in your browser and check that all the links direct to the proper pages.

Please commit the following *new* files (do not commit anything in the `build` directory):
- `templates/[cohort short name].tsv`
- `metadata/[cohort short name].ttl`
- `mappings/[cohort short name].tsv`

Also commit all changes to the following files:
- `Makefile`
- `index.html`
- `src/prefixes.json`
- `data/metadata.json`
- `data/cohort-data.json`

### Fixing Common Errors

Below are suggestions for common errors seen while running the build. If you run into any of these errors, try the recommended fixes and then run `make update` again. `make update` will always pull the latest data from Google sheets. You can also run `make refresh` to just update the data from Google sheets, and run the Make command for the individual task that failed (e.g., `make build/[cohort sort name].owl`).

#### ROBOT Errors

- `MALFORMED RULE ERROR malformed rule`: Make sure that row 3 of your cohort's ROBOT template is empty (not the mapping template)
- `UNKNOWN ENTITY ERROR could not interpret...`: Make sure you have [defined your prefix](#4-adding-the-cohort-metadata) in `src/prefixes.json`, and that all rows use this prefix in the `ID` column
<!-- TODO: add more errors ... e.g., label not correct for mappings -->

#### Makefile Errors

- `make: *** No rule to make target 'metadata/[cohort short name].ttl'`: Make sure you have created the TTL header and saved it with the correct short name
- `make: *** No rule to make target 'data/[cohort short name].tsv'`: Make sure you have [added the task](#5-updating-the-makefile) to download the cohort's Google spreadsheet to the `Makefile`
- `Makefile:[line]: *** missing separator`: Make sure that your newly added `Makefile` tasks use tabs and not spaces (the tab character identifies something as a "rule" to make the target in a Makefile)
<!-- TODO: more common Makefile errors? -->

#### Python Errors

TODO

#### Other Errors

If you run into other errors while trying to add a new cohort, please [open an issue](https://github.com/IHCC-cohorts/data-harmonization/issues/new) and include the full stack trace from the error.
