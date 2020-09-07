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
# 4. [View results](build/)
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
GECKO_PURL = http://purl.obolibrary.org/obo/gecko/views/ihcc-gecko.owl

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
COHORTS := gcs genomics-england koges saprin vukuzazi

# --- DO NOT EDIT BELOW THIS LINE ---

TEMPLATES := $(foreach C,$(COHORTS),templates/$(C).tsv)

# --- These files are not in version control (all in build directory) ---

# OWL file in the build directory for all cohorts (contains xrefs)
ONTS := $(foreach C,$(COHORTS),build/$(C).owl)

# HTML tree browser and table for each cohort
TREES := build/gecko-tree.html  $(foreach C,$(COHORTS),build/$(C)-tree.html)
TABLES := $(foreach C,$(COHORTS),build/$(C).html)


### General Tasks

.PHONY: clean
clean:
	rm -rf build

.PHONY: all
all: $(TREES) $(TABLES)
all: build/index.html
all: data/cohort-data.json
all: owl

.PHONY: update
update: clean all

build/index.html: src/create_index.py src/index.html.jinja2 data/metadata.json | $(ONTS) $(TREES) $(TABLES)
	python3 $^ $@


### Cohort OWL Files

# Run `make owl` to generate all cohort OWL files
.PHONY: owl
owl: $(ONTS) | data_dictionaries
	cp $^ data_dictionaries/

build/%.owl: build/intermediate/properties.owl templates/%.tsv build/intermediate/%-xrefs.tsv | build/robot.jar
	$(ROBOT) template --input $< \
	--merge-before \
	--template $(word 2,$^) \
	template \
	--template $(word 3,$^) \
	--merge-before \
	annotate --ontology-iri "https://purl.ihccglobal.org/$(notdir $@)" \
	--output $@


### GECKO Mapping TSVs

# Intermediate files for GECKO mappings

# GECKO terms as xrefs for main files
# These are required to build the cohort OWL file
# The xrefs are generated from the mapping template

build/intermediate/%-xrefs.tsv: src/create_xref_template.py templates/%.tsv templates/index.tsv | build/intermediate
	python3 $^ $@


### Trees and Tables

build/%-tree.html: build/%.owl | build/robot-tree.jar
	java -jar build/robot-tree.jar tree \
	--input $< \
	--tree $@

build/%.html: build/%.owl templates/%.tsv | src/prefixes.json build/robot.jar
	$(ROBOT) validate \
	--input $< \
	--table $(word 2,$^) \
	--skip-row 2 \
	--format HTML \
	--standalone true \
	--write-all true \
	--output-dir build/


### JSON Data for Real Browser

# Top-level cohort data

build/gecko_structure.json: build/gecko.owl | build/robot-tree.jar src/prefixes.json
	java -jar build/robot-tree.jar \
	--prefixes src/prefixes.json \
	tree --input $< \
	--format json \
	--tree $@

data/cohort-data.json: src/generate_cohort_json.py data/member_cohorts.csv data/metadata.json build/gecko_structure.json $(TEMPLATES)
	python3 $(filter-out $(TEMPLATES),$^) $@

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
	echo "UNSKIP THIS"
	#curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/master/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-tree.jar: | build
	echo "UNSKIP THIS"
	#curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/tree-view/lastSuccessfulBuild/artifact/bin/robot.jar

build/intermediate/properties.owl: src/properties.tsv | build/intermediate build/robot.jar
	$(ROBOT) template --template $< --output $@

build/gecko.owl: | build
	curl -L -o $@ $(GECKO_PURL)


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

# This is used to drive aggregations
build/browser/cineca.json: build/gecko.owl | build/browser
	$(ROBOT) export \
	--input $< \
	--header "ID|LABEL|subclasses" \
	--sort "LABEL" \
	--export $@

build/browser/index.html: src/browser/browser.html | build/browser
	cp $< $@

# JSON of ancestor GECKO term (key) -> list of cohort terms (value)
# This is used to drive the filter functionality in the browser
build/browser/%-mapping.json: src/browser/generate_mapping_json.py templates/%.tsv templates/index.tsv | build/browser
	python3 $^ $@

# Top-level cohort data as HTML pages 

COHORT_PAGES := $(foreach C,$(COHORTS),build/browser/cohorts/$(C).html)

$(COHORT_PAGES): src/browser/create_cohort_html.py data/cohort-data.json data/metadata.json src/browser/cohort.html.jinja2 build/browser/cohorts
	python3 $^

BROWSER := build/browser/index.html \
           build/browser/cineca.json \
           build/browser/cohorts.json \
           build/browser/metadata.json \
           $(foreach C,$(COHORTS),build/browser/$(C)-mapping.json) \
           $(foreach C,$(COHORTS),build/browser/$(C)-data.json) \
           $(COHORT_PAGES)

.PHONY: browser
browser: $(BROWSER)

.PHONY: serve
serve: $(BROWSER)
	cd build/browser && python3 -m http.server 8000

# Pipeline to generate mapping suggestions for a template

.PHONY: mapping_suggest_%
mapping_suggest_%: src/mapping-suggest/zooma_matcher.py src/mapping-suggest/mapping-suggest-config.yml templates/%.tsv
	python3 $< -c src/mapping-suggest/mapping-suggest-config.yml -t templates/$*.tsv -o templates/_$*.tsv

MAP_DATA := $(foreach C,$(COHORTS),build/intermediate/$(C)-xrefs-sparql.csv)

build/intermediate/%-xrefs-sparql.csv: data_dictionaries/%.owl src/queries/ihcc-mapping.sparql | build/intermediate build/robot.jar
	$(ROBOT) query --input $< --query src/queries/ihcc-mapping.sparql $@
	
build/intermediate/gecko-xrefs-sparql.csv: build/gecko.owl src/queries/ihcc-mapping-gecko.sparql | build/intermediate build/robot.jar
	$(ROBOT) query --input $< --query src/queries/ihcc-mapping-gecko.sparql $@

data/ihcc-mapping-suggestions-zooma.csv: build/intermediate/gecko-xrefs-sparql.csv $(MAP_DATA)
	echo $^
	
