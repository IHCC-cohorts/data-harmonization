# IHCC Demonstration Makefile
# James A. Overton <james@overton.ca>
#
# WARN: This file contains significant whitespace, i.e. tabs!
# Ensure that your text editor shows you those characters.

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
TEMPLATES := templates/gecko.csv $(foreach C,$(COHORTS),templates/$(C).tcv)

# ROBOT templates containing cohort -> GECKO mappings
MAPPINGS := mappings/index.csv mappings/properties.csv $(foreach C,$(COHORTS),mappings/$(C).csv)

# --- These files are not in version control (all in build directory) ---

# OWL file in the build directory for all cohorts (contains xrefs)
ONTS := build/gecko.owl $(foreach C,$(COHORTS),build/$(C).owl)

# HTML tree browser and table for each cohort
TREES := build/gecko-tree.html  $(foreach C,$(COHORTS),build/$(C)-tree.html)
MAPPING_TREES := $(foreach C,$(COHORTS),build/$(C)-gecko.html)
TABLES := build/gecko.html $(foreach C,$(COHORTS),build/$(C).html)

# --- These files are intermediate build files ---

# ROBOT templates for providing xrefs for cohort terms to mapped GECKO terms
XREFS := $(foreach C,$(COHORTS),build/$(C)-xrefs.tsv)

# ontology (in turtle format) versions of cohort -> GECKO mappings
TTL_MAPPINGS := $(foreach C,$(COHORTS),build/intermediate/$(C)-gecko.ttl)


### General Tasks

.PHONY: refresh
refresh:
	rm -rf $(TEMPLATES) $(MAPPINGS) build/mapping/gecko-mapping.xlsx
	make $(TEMPLATES)
	make $(MAPPINGS)

.PHONY: clean
clean:
	rm -rf build

.PHONY: all
all: $(TREES) $(TABLES) $(MAPPING_TREES)
all: build/index.html
all: data/cohort-data.json

update: refresh all

rebuild: clean update

build/index.html: src/create_index.py src/index.html.jinja2 data/metadata.json | $(ONTS) $(TREES) $(TABLES) $(MAPPING_TREES)
	python3 $^ $@


### Cohort OWL Files 

# Run `make owl` to generate all cohort OWL files
owl: $(ONTS)

# The OWL files are based on:
#    - ROBOT template (build/<cohort-short-name>.tsv)
#    - GECKO mapping template (build/intermediate/<cohort-short-name>-xrefs.tsv)
#    - A metadata header (metadata/<cohort-short-name>.ttl)

# In order to build an OWL file, you MUST have all three items (see docs for full details):
#    - The ROBOT template must be added to the Makefile below
#    - The mapping sheet must be added to the master Google mapping sheet
#    - The metadata header must be created and added to the `metadata` folder
# You must also add the cohort details to data/metadata.json and src/prefixes.json

build/%.owl: build/intermediate/properties.owl templates/%.csv build/intermediate/%-xrefs.tsv metadata/%.ttl | build/robot.jar
	$(ROBOT) template --input $< \
	--merge-before \
	--template $(word 2,$^) \
	template \
	--template $(word 3,$^) \
	--merge-before \
	merge \
	--input $(word 4,$^) \
	--include-annotations true \
	annotate --ontology-iri "http://example.com/$(notdir $@)" \
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

templates/%.csv: src/xlsx2csv.py build/templates.xlsx
	python3 $^ $(basename $(notdir $@)) > $@


### GECKO Mapping TSVs

build/gecko-mapping.xlsx: | build/mapping
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1IRAv5gKADr329kx2rJnJgtpYYqUhZcwLutKke8Q48j4/export?format=xlsx"

# Run `make refresh` to get updated mapping TSVs

mappings/index.csv: src/xlsx2csv.py build/gecko-mapping.xlsx
	python3 $^ index > $@

mappings/properties.csv: src/xlsx2csv.py build/gecko-mapping.xlsx
	python3 $^ properties > $@

mappings/%.csv: src/xlsx2csv.py build/gecko-mapping.xlsx
	python3 $^ $(basename $(notdir $@)) > $@

# GECKO terms as xrefs for main files
# These are required to build the cohort OWL file

build/intermediate/%-xrefs.tsv: src/create_xref_template.py mappings/%.csv mappings/index.csv | build/intermediate
	python3 $^ $@


### GECKO Mapping Files

build/%-gecko.html: build/intermediate/%-gecko.ttl | build/robot-tree.jar
	java -jar build/robot-tree.jar tree \
	--input $< \
	--tree $@

# Intermediate files for GECKO mappings

# Cohort terms + GECKO terms from template
# The GECKO terms are just referenced and do not have structure/annotations
build/intermediate/%-mapping.ttl: build/intermediate/gecko-full.owl build/%.owl mappings/%.csv | build/intermediate build/robot.jar
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

build/%.html: build/%.owl templates/%.csv | src/prefixes.json build/robot-validate.jar
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
	python3 $(filter-out $(JSON_MAPPINGS),$^) $@

# Real cohort data + randomly-generated cohort data

data/full-cohort-data.json: data/cohort-data.json data/random-data.json
	sed '$$d' $< | sed '$$d' >> $@
	echo '  },' >> $@
	sed '1d' $(word 2,$^) >> $@


### Pre-build Tasks

build build/intermediate:
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


### GECKO Tasks - to be moved into separate repo

# GECKO does not have an xref template
build/gecko.owl: build/intermediate/properties.owl build/gecko.tsv metadata/gecko.ttl | build/robot.jar
	$(ROBOT) template --input $< \
	--merge-before \
	--template $(word 2,$^) \
	merge \
	--input $(word 3,$^) \
	--include-annotations true \
	annotate --ontology-iri "http://example.com/$(notdir $@)" \
	--output $@

# GECKO plus OBO terms
build/indermediate/index.owl: mappings/properties.csv mappings/index.csv | build/intermediate build/robot.jar
	$(ROBOT) template --template $< \
	template --merge-before \
	--template $(word 2,$^) \
	--output $@

# TODO - move GECKO to its own repo
build/intermediate/gecko-full.owl: build/gecko.owl build/intermediate/index.owl | build/robot.jar
	$(ROBOT) merge --input $< \
	--input $(word 2,$^) \
	reason reduce \
	--output $@

# NCIT Module - NCIT terms that have been mapped to GECKO terms

#.PRECIOUS: build/ncit.owl.gz
#build/ncit.owl.gz: | build
#	curl -L http://purl.obolibrary.org/obo/ncit.owl | gzip > $@

#build/ncit-terms.txt: build/gecko.owl src/gecko/get-ncit-ids.rq src/gecko/ncit-annotation-properites.txt | build/robot.jar
#	$(ROBOT) query --input $< --query $(word 2,$^) $@
#	tail -n +2 $@ > $@.tmp
#	cat $@.tmp $(word 3,$^) > $@ && rm $@.tmp

#build/ncit-module.owl: build/ncit.owl.gz build/ncit-terms.txt | build/robot-rdfxml.jar
#	$(ROBOT_RDFXML) extract --input $< \
#	--term-file $(word 2,$^) \
#	--method rdfxml \
#	--intermediates minimal --output $@
