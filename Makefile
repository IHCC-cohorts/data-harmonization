# IHCC Demonstration Makefile
# James A. Overton <james@overton.ca>
#
# WARN: This file contains significant whitespace, i.e. tabs!
# Ensure that your text editor shows you those characters.

### Workflow
#
# 1. Edit [mapping table](https://docs.google.com/spreadsheets/d/1IRAv5gKADr329kx2rJnJgtpYYqUhZcwLutKke8Q48j4/edit)
# 2. [Update files](update)
# 3. [Build Mappings](owl)
# 4. [View results](build/index.html)
#
# Demo browser:
#
# 1. [Update browser](browser)
# 2. [View browser](build/browser/index.html)

### Configuration
#
# These are standard options to make Make sane:
# <http://clarkgrubb.com/makefile-style-guide#toc2>

MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:
.SECONDARY:

ROBOT = java -jar build/robot.jar --prefixes src/prefixes.json
ROBOT_RDFXML = java -jar build/robot-rdfxml.jar
GECKO_PURL = http://purl.obolibrary.org/obo/gecko.owl

# Detect the OS and provide proper command
# WARNING - will not work with Windows OS
UNAME = $(shell uname)
ifeq ($(UNAME), Darwin)
	SED = sed -i .bak
else
	SED = sed -i
endif


### Variables

# List of cohorts to generate files for (lowercase, using short ID where possible)
# This short name is used throughout all build tasks and should be consistent for all files
# --- THIS IS THE ONLY LINE THAT SHOULD BE EDITED WHEN ADDING A NEW COHORT ---
COHORTS := gcs genomics-england koges maelstrom saprin vukuzazi
# --- DO NOT EDIT BELOW THIS LINE ---

# --- These files are maintained in version control ---

# TSVs that generate the OWL files for each cohort (no mappings)
TEMPLATES := $(foreach C,$(COHORTS),templates/$(C).tsv)

# ROBOT templates containing cohort -> GECKO mappings
MAPPINGS := mappings/index.tsv mappings/properties.tsv $(foreach C,$(COHORTS),mappings/$(C).tsv)

# --- These files are not in version control (all in build directory) ---

# OWL file in the build directory for all cohorts (contains xrefs)
ONTS := $(foreach C,$(COHORTS),build/$(C).owl)

# HTML tree browser and table for each cohort
TREES := build/gecko-tree.html  $(foreach C,$(COHORTS),build/$(C)-tree.html)
MAPPING_TREES := $(foreach C,$(COHORTS),build/$(C)-gecko.html)
TABLES := $(foreach C,$(COHORTS),build/$(C).html)

# --- These files are intermediate build files ---

# ROBOT templates for providing xrefs for cohort terms to mapped GECKO terms
XREFS := $(foreach C,$(COHORTS),build/$(C)-xrefs.tsv)

# ontology (in turtle format) versions of cohort -> GECKO mappings
TTL_MAPPINGS := $(foreach C,$(COHORTS),build/intermediate/$(C)-gecko.ttl)


### General Tasks

.PHONY: refresh
refresh:
	rm -rf $(TEMPLATES) $(MAPPINGS) build/gecko-mapping.xlsx build/templates.xlsx
	make $(TEMPLATES)
	make $(MAPPINGS)

.PHONY: clean
clean:
	rm -rf build

.PHONY: all
all: $(TREES) $(TABLES) $(MAPPING_TREES)
all: build/index.html
all: data/cohort-data.json
all: owl

.PHONY: update
update: refresh all

.PHONY: rebuild
rebuild: clean update

build/index.html: src/create_index.py src/index.html.jinja2 data/metadata.json | $(ONTS) $(TREES) $(TABLES) $(MAPPING_TREES)
	python3 $^ $@


### Cohort OWL Files

# Run `make owl` to generate all cohort OWL files
.PHONY: owl
owl: $(ONTS) | data_dictionaries
	cp $^ data_dictionaries/

# The OWL files are based on:
#    - ROBOT template (build/<cohort-short-name>.tsv)
#    - GECKO mapping template (build/intermediate/<cohort-short-name>-xrefs.tsv)
#    - A metadata header (metadata/<cohort-short-name>.ttl)

# In order to build an OWL file, you MUST have all three items (see docs for full details):
#    - The ROBOT template must be added to the Makefile below
#    - The mapping sheet must be added to the master Google mapping sheet
#    - The metadata header must be created and added to the `metadata` folder
# You must also add the cohort details to data/metadata.json and src/prefixes.json

build/%.owl: build/intermediate/properties.owl templates/%.tsv build/intermediate/%-xrefs.tsv metadata/%.ttl | build/robot.jar
	$(ROBOT) template --input $< \
	--merge-before \
	--template $(word 2,$^) \
	template \
	--template $(word 3,$^) \
	--merge-before \
	merge \
	--input $(word 4,$^) \
	--include-annotations true \
	annotate --ontology-iri "https://purl.ihccglobal.org/$(notdir $@)" \
	--output $@


### ROBOT Templates for Cohort Data Dictionaries

# To add a new ROBOT template (based on a Google sheet in correct ROBOT template format):
# data/<cohort-short-name>.tsv:
#	curl -L -o $@ "<link-to-google-sheet>"
#
# build/<cohort-short-name>.tsv: data/<cohort-short-name>.tsv
#	cp $< $@

# Run `make refresh` to get all new data dictionary TSVs

build/templates.xlsx: | build
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1FwYYlJPzFAAItZyaKY2YnP01yQw6BkARq3CPifQSx1A/export?format=xlsx"

templates/%.tsv: build/templates.xlsx
	xlsx2csv -d tab --ignoreempty -n $(basename $(notdir $@)) $< $@


### GECKO Mapping TSVs

# This Google Sheet contains mappings for each cohort -> GECKO

build/gecko-mapping.xlsx: | build
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1IRAv5gKADr329kx2rJnJgtpYYqUhZcwLutKke8Q48j4/export?format=xlsx"

# Run `make refresh` to get updated mapping TSVs

# The index contains granular OBO terms that are descendants of GECKO terms

mappings/index.tsv: build/gecko-mapping.xlsx
	xlsx2csv -d tab --ignoreempty -n index $< $@

mappings/properties.tsv: build/gecko-mapping.xlsx
	xlsx2csv -d tab --ignoreempty -n properties $< $@

# Each cohort has it's own tab in the mappings XLSX

mappings/%.tsv: build/gecko-mapping.xlsx
	xlsx2csv -d tab --ignoreempty -n $(basename $(notdir $@)) $< $@

# GECKO terms as xrefs for main files
# These are required to build the cohort OWL file
# The xrefs are generated from the mapping template

build/intermediate/%-xrefs.tsv: src/create_xref_template.py mappings/%.tsv mappings/index.tsv | build/intermediate
	python3 $^ $@


### GECKO Mapping Files

build/%-gecko.html: build/intermediate/%-gecko.ttl | build/robot-tree.jar
	java -jar build/robot-tree.jar tree \
	--input $< \
	--tree $@

# Intermediate files for GECKO mappings

# Cohort terms + GECKO terms from template
# The GECKO terms are just referenced and do not have structure/annotations
build/intermediate/%-mapping.ttl: build/intermediate/gecko-full.owl build/%.owl mappings/%.tsv | build/intermediate build/robot.jar
	$(ROBOT) merge \
	--input $< \
	--input $(word 2,$^) \
	template \
	--template $(word 3,$^) \
	merge \
	--input $(word 2,$^) \
	reason reduce \
	--output $@

# List of GECKO terms used by the cohort
build/intermediate/gecko-%.txt: build/intermediate/%-mapping.ttl src/queries/get-extract-terms.rq | build/robot.jar
	$(ROBOT) query \
	--input $< \
	--query $(word 2,$^) $@

# TTL version of full mapping structure
build/intermediate/%-gecko.ttl: build/intermediate/gecko-full.owl build/intermediate/gecko-%.txt build/intermediate/%-mapping.ttl | build/robot.jar
	$(ROBOT) extract --input $< \
	--method MIREOT \
	--lower-terms $(word 2,$^) \
	merge \
	--input $(word 3,$^) \
	relax reduce \
	remove --axioms equivalent \
	--output $@


### Trees and Tables

build/%-tree.html: build/%.owl | build/robot-tree.jar
	java -jar build/robot-tree.jar tree \
	--input $< \
	--tree $@

build/%.html: build/%.owl templates/%.tsv | src/prefixes.json build/robot-validate.jar
	java -jar build/robot-validate.jar validate \
	--prefixes src/prefixes.json \
	--input $< \
	--table $(word 2,$^) \
	--skip-row 2 \
	--format HTML \
	--standalone true \
	--output-dir build/


### JSON Data for Real Browser

# Top-level cohort data

data/cohort-data.json: src/json/generate_cohort_json.py data/member_cohorts.csv data/metadata.json src/json/cineca_structure.json $(TTL_MAPPINGS)
	python3 $(filter-out $(TTL_MAPPINGS),$^) $@

# Real cohort data + randomly-generated cohort data

data/full-cohort-data.json: data/cohort-data.json data/random-data.json
	rm -f $@
	sed '$$d' $< | sed '$$d' >> $@
	echo '  },' >> $@
	sed '1d' $(word 2,$^) >> $@


### Pre-build Tasks

build build/intermediate build/browser build/browser/cohorts data_dictionaries:
	mkdir -p $@

build/robot.jar: | build
	curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/master/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-tree.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/tree-view/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-validate.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/validate/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-rdfxml.jar: | build
	curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/mireot-rdfxml/lastSuccessfulBuild/artifact/bin/robot.jar

build/intermediate/properties.owl: src/properties.tsv | build/intermediate build/robot.jar
	$(ROBOT) template --template $< --output $@

	
### GECKO Tasks

# GECKO is retrieved from the OBO PURL
build/gecko.owl: | build
	curl -L -o $@ $(GECKO_PURL)

# GECKO plus OBO terms (from the index of mappings XLSX)
build/intermediate/index.owl: mappings/properties.tsv mappings/index.tsv | build/intermediate build/robot.jar
	$(ROBOT) template --template $< \
	template --merge-before \
	--template $(word 2,$^) \
	--output $@

# GECKO + extra OBO terms (as descendants)
# This file is used to eventually build the JSON that maps each cohort term up to the GECKO terms
build/intermediate/gecko-full.owl: build/gecko.owl build/intermediate/index.owl | build/robot.jar
	$(ROBOT) merge --input $< \
	--input $(word 2,$^) \
	reason reduce \
	--output $@


# ------------------------------------------------------------------------------------------------

# Cohort data dictionary in JSON format
build/browser/%-data.json: build/%.owl | build/browser build/robot.jar
	$(ROBOT) export \
	--input $< \
	--header "ID|LABEL|definition|subclasses" \
	--sort "LABEL" \
	--export $@

# Full cohort data (copied)
build/browser/cohorts.json: data/full-cohort-data.json | build/browser
	cp $< $@

# Cohort metadata (copied)
build/browser/metadata.json: data/metadata.json | build/browser
	cp $< $@

# GECKO without OBO terms = CINECA
# This is used to drive aggregations
# TODO - automatically create this
build/browser/cineca.json: src/browser/cineca.json | build/browser
	cp $< $@

build/browser/index.html: src/browser/browser.html | build/browser
	cp $< $@

# JSON of ancestor GECKO term (key) -> list of cohort terms (value)
# This is used to drive the filter functionality in the browser

# Query to get cohort terms -> ancestor GECKO terms
build/intermediate/get-cineca-%.rq: src/queries/build_query.py data/metadata.json | build/intermediate
	$(eval NAME := $(subst get-cineca-,,$(basename $(notdir $@))))
	python3 $^ $(NAME) $@

build/intermediate/%-mapping.csv: build/intermediate/%-gecko.ttl build/intermediate/get-cineca-%.rq | build/intermediate build/robot.jar
	$(ROBOT) query --input $< --query $(word 2,$^) $@

build/browser/%-mapping.json: src/browser/generate_mapping_json.py build/intermediate/%-mapping.csv | build/browser
	python3 $^ $@

# Top-level cohort data as HTML pages 

COHORT_PAGES := $(foreach C,$(COHORTS),build/browser/cohorts/$(C).html)

$(COHORT_PAGES): src/browser/create_cohort_html.py data/cohort-data.json data/metadata.json src/browser/cohort.html.jinja2 build/browser/cohorts
	python3 $^

BROWSER := build/browser/index.html \
           build/browser/cineca.json \
           build/browser/cohorts.json \
           build/browser/metadata.json \
           build/browser/gecko-data.json \
           $(foreach C,$(COHORTS),build/browser/$(C)-mapping.json) \
           $(foreach C,$(COHORTS),build/browser/$(C)-data.json) \
           $(COHORT_PAGES)

.PHONY: browser
browser: $(BROWSER)

.PHONY: serve
serve: $(BROWSER)
	cd build/browser && python3 -m http.server 8000

