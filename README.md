# IHCC Data Harmonization

This is work-in-progress on a demonstration system that uses ontologies to harmonize data on various cohorts for the [International HundredK+ Cohorts Consortium (IHCC)](https://ihcc.g2mc.org).


## Adding a New Cohort

First, clone this repository to your local machine and create a new branch. Then, follow the following steps and make a pull request with all required changes.

### 1. Selecting a Short Name and Prefix

The "short name" will be the name used for all files generated for your cohort. Some guidelines to follow when selecting a short name are:
- select a name that is unique, all-lowercase, and something easy to read and remember (e.g., [Golestan Cohort Study](https://dceg2.cancer.gov/gemshare/) = `gcs`)
- use an acronym if you already have one (e.g., [South African Population Research Infrastructure Network (SAPRIN)](http://saprin.mrc.ac.za/) = `saprin`)
- replace spaces with dashes (e.g., [Genomics England](https://www.genomicsengland.co.uk/) = `genomics-england`)

Your prefix should be your short name in uppercase (e.g, `gcs` = `GCS`), unless there is some reason to change it. You should shorten your prefix if your short name uses more than one word (e.g., `genomics-england` = `GE`). We request that you do not use underscores in your prefix. Like the short names, prefixes **must** be unique across all cohorts.

### 2. Creating the ROBOT Template

Cohort data dictionaries are transformed into OWL ontologies using [ROBOT templates](http://robot.obolibrary.org/template). All new cohorts must provide a public Google spreadsheet with their data dictionary in this format.

The following information is **required**:
- ID
- Label

All IDs **must** be unique and must be in [CURIE](https://en.wikipedia.org/wiki/CURIE) format. Use the prefix you've chosen in the last step as the namespace. We recommend that you use 7-digit numeric IDs (e.g., `GCS:0000001`), but if you already have IDs for your items you may reuse those (e.g., `MAELSTROM:Blood_immune_dis`). Please note that IDs are case sensitive and once an ID has been created for a term, that ID is **permanent**.

We recommend that all labels be unique, as well, but this is not required.

The following information is **highly recommended**:
- **Parent**: category under which this data item falls (this must also be defined in your data dictionary)
- **Definition**: one-sentance description of what kind of data is collected for this item

The following information is optional:
- **Comment**: an editor's comment about this data dictionary item
- **Answer Type**: type of answer (e.g., numerical, date, etc.)
- **Formula**: formula to determine this data value, if calculated
- **Measurement Time**: time period for which is data is collection (e.g., over time?)
- **Question Description**: the question asked to collect this data

The first row of the spreadsheet should be human-readable column headers. The second row will be the [ROBOT template strings](http://robot.obolibrary.org/template) for each column. The third row should be left empty for future validation. The data dictionary entries should start on row 4.

The basic ROBOT template strings are as follows:
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

To start, add a tab to the [master GECKO mapping sheet](). This tab **must** be named with the cohort short name.

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

Include *all* your data dictionary IDs and Labels to begin. You can leave columns 3 and 4 empty for these rows until you have started your mappings. All GECKO terms can be found in the [index of the master mapping sheet](). You can also browse a hierarchical version of GECKO [here]().

### 4. Adding the Cohort Metadata

#### `data/metadata.json`

Using the following template, add an entry to [`data/metadata.json`]():
```
"[full cohort name]": {
	"id": "[cohort short name]",
	"prefix": "[cohort prefix]",
	"data_dictionary": "[link to cohort's data dictionary in ROBOT template format]",
	"mapping": "[link to cohort's tab in the master mapping document]"
}
```

Please note that the `[full cohort name]` **must** match the name recorded in [`data/member_cohorts.csv`]().
<!-- TODO: what if the cohort is not listed? -->

#### `src/prefixes.json`

Using the following template, add an entry to [`src/prefixes.json`]():
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

Before updating the [`Makefile`](), make sure you have done the following:
1. Selected a short name & prefix
2. Created a ROBOT template on Google sheets (ensure that this sheet is public) containing all data dictionary items
3. Created a tab for the cohort in the master GECKO mappings sheet and added data dictionary items to this sheet
4. Added entries in `data/metadata.json` and `src/prefix.json`
5. Created a TTL header in the `metadata` folder

To add your cohort to the build, simply add the cohort short name to the [list on line 89](). Then, add a new task [after line 188]() in the `ROBOT Templates for Cohort Data Dictionaries` section using the following template, replacing only the items in square brackets:
```
# [cohort name] Tasks

data/[cohort short name].tsv:
	curl -L -o $@ "[link to ROBOT template Google sheet]/export?format=tsv"

build/[cohort short name].tsv: data/[cohort short name].tsv
	cp $< $@
```

The link to the Google spreadsheet will be the same link in the URL bar when you are editing the sheet, except you should replace `/edit#gid=0` with `/export?format=tsv` to make sure it downloads properly (the export format is included in the above template, but make sure to remove the `/edit` portion of the URL).

Next, run `make update` to ensure all tasks complete properly. This should generate all build files for your cohort:
- `data/[cohort short name].tsv`
- `mappings/[cohort short name].tsv`
- `build/[cohort short name].owl`
- `build/cohorts/[cohort short name].owl`
- `build/[cohort short name].html`
- `build/[cohort short name]-tree.html`
- `build/[cohort short name]-gecko-tree.html`
- `build/[cohort short name]-data.json`
- `build/[cohort short name]-mapping.owl`
- `build/[cohort short name]-mapping.json`
- `build/[cohort short name]-xrefs.tsv`

You need to commit `data/[cohort short name].tsv` and `mappings/[cohort short name].tsv` to the repository. The other files in `build` do not get committed. Also commit all changes to the following files:

- `Makefile`
- `src/prefixes.json`
- `data/metadata.json`
- `data/cohort-data.json`

### Fixing Common Errors

Below are suggestions for common errors seen while running the build. If you run into any of these errors, try the recommended fixes and then run `make update` again. `make update` will always pull the latest data from Google sheets. You can also run `make refresh` to just update the data from Google sheets, and run the Make command for the individual task that failed (e.g., `make build/[cohort sort name].owl`).

#### ROBOT Errors

- `MALFORMED RULE ERROR malformed rule`: Make sure that row 3 of your cohort's ROBOT template is empty (not the mapping template)
- `UNKNOWN ENTITY ERROR could not interpret...`: Make sure you have [defined your prefix](#4-adding-the-cohort-metadata) in `src/prefixes.json`, and that all rows use this prefix in the `ID` column

TODO: add more

#### Makefile Errors

- `make: *** No rule to make target 'metadata/[cohort short name].ttl'`: Make sure you have created the TTL header and saved it with the correct short name
- `make: *** No rule to make target 'data/[cohort short name].tsv'`: Make sure you have [added the task](#5-updating-the-makefile) to download the cohort's Google spreadsheet to the `Makefile`
- `Makefile:[line]: *** missing separator`: Make sure that your newly added `Makefile` tasks use tabs and not spaces (the tab character identifies something as a "rule" to make the target in a Makefile)

TODO: add more

#### Python Errors

TODO: errors from python scripts

#### Other Errors

If you run into other errors while trying to add a new cohort, please [open an issue](https://github.com/IHCC-cohorts/data-harmonization/issues/new/choose) and include the full stack trace from the error.
