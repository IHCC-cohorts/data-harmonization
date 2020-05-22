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
COHORTS := gcs genomics-england koges maelstrom saprin vukuzazi

# OWL file in the build directory for all cohorts (contains xrefs)
ONTS := build/gecko.owl $(foreach C,$(COHORTS),build/$(C).owl)

# TSVs that generate the OWL files for each cohort (no mappings)
DATA_DICTS := $(foreach C,$(COHORTS),build/$(C).tsv)
DATA_NOT_TSV := gcs genomics-england maelstrom vukuzazi
MASTER_DATA := $(foreach C,$(filter-out $(DATA_NOT_TSV), $(COHORTS)),data/$(C).tsv) \
               data/genomics-england.xlsx \
               data/golestan-cohort-study.xlsx \
               data/maelstrom.yml \
               data/vukuzazi.xlsx

# TSVs containing cohort -> GECKO mappings
MASTER_MAPPINGS := mappings/index.tsv mappings/properties.tsv $(foreach C,$(COHORTS),mappings/$(C).tsv)

# TSVs for providing xrefs for cohort terms to mapped GECKO terms
XREFS := $(foreach C,$(COHORTS),build/$(C)-xrefs.tsv)

# OWL and JSON versions of cohort -> GECKO mappings
OWL_MAPPINGS := $(foreach C,$(COHORTS),build/$(C)-gecko.owl)
JSON_MAPPINGS := $(foreach C,$(COHORTS),build/$(C)-mapping.json)

# HTML tree browser and table for each cohort (no mappings)
TREES := build/gecko-tree.html  $(foreach C,$(COHORTS),build/$(C)-tree.html)
MAPPING_TREES := $(foreach C,$(COHORTS),build/$(C)-gecko.html)
TABLES := build/gecko.html $(foreach C,$(COHORTS),build/$(C).html)


### General Tasks

.PHONY: refresh
refresh:
	rm -rf $(MASTER_DATA) $(MASTER_MAPPINGS) build/mapping/gecko-mapping.xlsx
	make $(MASTER_DATA)
	make $(MASTER_MAPPINGS)

.PHONY: clean
clean:
	rm -rf build

.PHONY: all
all: $(TREES) $(TABLES) $(MAPPING_TREES)
all: index.html
all: data/cohort-data.json

update: refresh all

index.html: src/create_index.py src/index.html.jinja2 data/metadata.json | $(ONTS) $(MASTER_DATA) $(TREES) $(TABLES) $(MAPPING_TREES)
	python3 $^ $@


### Cohort OWL Files 

# Run `make owl` to generate all cohort OWL files
owl: $(ONTS)

# The OWL files are based on:
#    - ROBOT template (build/<cohort-short-name>.tsv)
#    - GECKO mapping template (build/<cohort-short-name>-xrefs.tsv)
#    - A metadata header (metadata/<cohort-short-name>.ttl)

# In order to build an OWL file, you MUST have all three items (see docs for full details):
#    - The ROBOT template must be added to the Makefile below
#    - The mapping sheet must be added to the master Google mapping sheet
#    - The metadata header must be created and added to the `metadata` folder
# You must also add the cohort details to data/metadata.json and src/prefixes.json

build/%.owl: build/properties.owl templates/%.csv build/%-xrefs.tsv metadata/%.ttl | build/robot.jar
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

# GECKO from CINECA

data/cineca.tsv:
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1ZXqTMIhFtGOaodw7Fns5YghvY_pWos-RuSa2BFnO5l4/export?format=tsv"

build/gecko.tsv: src/convert/gecko.py data/cineca.tsv src/indexes/gecko.tsv | build
	python3 $^ $@

# GECKO does not have an xref template
build/gecko.owl: build/properties.owl build/gecko.tsv metadata/gecko.ttl | build/robot.jar
	$(ROBOT) template --input $< \
	--merge-before \
	--template $(word 2,$^) \
	merge \
	--input $(word 3,$^) \
	--include-annotations true \
	annotate --ontology-iri "http://example.com/$(notdir $@)" \
	--output $@

# We use the TTL file for some python scripts
build/gecko.ttl: build/gecko.owl | build/robot.jar
	$(ROBOT) convert --input $< --output $@

# Genomics England Tasks

data/genomics-england.xlsx:
	curl -L -o $@ "https://cnfl.extge.co.uk/download/attachments/113189195/Data%20Dictionary%20Main%20Programme%20v6%20%281%29.xlsx?version=1&modificationDate=1551371214157&api=v2"

build/genomics-england.tsv: src/convert/genomics-england.py data/genomics-england.xlsx | build
	python3 $^ $@

# Golestan Cohort Study (GCS) Tasks

data/golestan-cohort-study.xlsx:
	curl -L -o $@ "https://drive.google.com/uc?export=download&id=1ZLw-D6AZFKrBjTNsc4wzlthYq4w4KmOJ"

build/gcs.tsv: src/convert/golestan-cohort-study.py data/golestan-cohort-study.xlsx | build
	python3 $^ $@

# KoGES Tasks

data/koges.tsv:
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1hPcCzjFWHJ7iiqMHBpuodFCrrTvSmCKfQu0f93JPhU8/export?format=tsv"

build/koges.tsv: src/convert/koges.py data/koges.tsv src/indexes/koges.tsv | build
	python3 $^ $@

# Maelstrom Tasks

data/maelstrom.yml:
	curl -L -o $@ https://raw.githubusercontent.com/maelstrom-research/maelstrom-taxonomies/master/AreaOfInformation.yml

build/maelstrom.tsv: src/convert/maelstrom.py data/maelstrom.yml | build
	python3 $^ $@

# SAPRIN Tasks

data/saprin.tsv:
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1KjULwQ38IkWqJxOCZZ2em8ge7NZJEngOZqI3ebC9Wkk/export?format=tsv"

build/saprin.tsv: src/convert/saprin.py data/saprin.tsv | build
	python3 $^ $@

# Vukuzazi Tasks

data/vukuzazi.xlsx:
	curl -L -o $@ "https://drive.google.com/uc?export=download&id=1YpwjiYDos5ZkXMQR6wG4Qug7sMmKB5xC"

build/vukuzazi.tsv: src/convert/vukuzazi.py data/vukuzazi.xlsx | build
	python3 $^ $@


### GECKO Mapping TSVs

build/mapping/gecko-mapping.xlsx: | build/mapping
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1IRAv5gKADr329kx2rJnJgtpYYqUhZcwLutKke8Q48j4/export?format=xlsx"

# Run `make refresh` to get updated mapping TSVs

mappings/index.csv: src/xlsx2csv.py build/mapping/gecko-mapping.xlsx
	python3 $^ index > $@

mappings/properties.csv: src/xlsx2csv.py build/mapping/gecko-mapping.xlsx
	python3 $^ properties > $@

mappings/%.csv: src/xlsx2csv.py build/mapping/gecko-mapping.xlsx
	python3 $^ $(basename $(notdir $@)) > $@

# GECKO terms as xrefs for main files
# These are required to build the cohort OWL file

build/%-xrefs.tsv: src/create_xref_template.py mappings/%.csv mappings/index.csv
	python3 $^ $@


### Pre-build Tasks

build build/mapping build/cohorts:
	mkdir -p $@

build/robot.jar: | build
	curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/master/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-tree.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/tree-view/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-validate.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/validate/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-rdfxml.jar: | build
	curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/mireot-rdfxml/lastSuccessfulBuild/artifact/bin/robot.jar

build/properties.owl: src/properties.tsv | build/robot.jar
	$(ROBOT) template --template $< --output $@


### Main Mapping Files

# GECKO plus OBO terms

build/mapping/index.owl: mappings/properties.csv mappings/index.csv
	$(ROBOT) template --template $< \
	template --merge-before \
	--template $(word 2,$^) \
	--output $@

build/gecko-full.owl: build/gecko.owl build/mapping/index.owl | build/robot.jar
	$(ROBOT) merge --input $< \
	--input $(word 2,$^) \
	reason reduce \
	--output $@

# Cohort -> GECKO Mappings

# OWL version of mapping

build/%-gecko.owl: build/mapping/%-gecko.ttl
	$(ROBOT) convert --input $< --output $@

# Intermediate files for GECKO mappings (stored in build/mapping)

# Cohort terms + GECKO terms from template
# The GECKO terms are just referenced and do not have structure/annotations
build/mapping/%-mapping.owl: build/gecko-full.owl build/%.owl mappings/%.csv | build/robot.jar
	$(ROBOT) merge \
	--input $< \
	--input $(word 2,$^) \
	template \
	--template $(word 3,$^) \
	merge \
	--input $(word 2,$^) \
	reason reduce \
	--output $@

# Cohort terms + GECKO terms (full version)
# TTL version of mapping for loading into rdflib
build/mapping/%-gecko.ttl: build/mapping/gecko-%.ttl build/mapping/%-mapping.owl | build/robot.jar
	$(ROBOT) merge --input $< \
	--input $(word 2,$^) \
	relax reduce \
	remove --axioms equivalent \
	--output $@

# List of GECKO terms used by the cohort
build/mapping/gecko-%.txt: build/mapping/%-mapping.owl src/queries/get-extract-terms.rq | build/robot.jar
	$(ROBOT) query \
	--input $< \
	--query $(word 2,$^) $@

# GECKO terms used by the cohort as TTL
build/mapping/gecko-%.ttl: build/gecko-full.owl build/mapping/gecko-%.txt | build/robot.jar
	$(ROBOT) extract --input $< \
	--method MIREOT \
	--lower-terms $(word 2,$^) \
	--output $@

build/%-gecko.html: build/%-gecko.owl | build/robot-tree.jar
	java -jar build/robot-tree.jar tree \
	--input $< \
	--tree $@

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

data/cohort-data.json: src/json/generate_cohort_json.py data/member_cohorts.csv data/metadata.json src/json/cineca_structure.json | $(JSON_MAPPINGS)
	python3 $^ $@

# Real cohort data + randomly-generated cohort data

data/full-cohort-data.json: data/cohort-data.json data/random-data.json
	sed '$$d' $< | sed '$$d' >> $@
	echo '  },' >> $@
	sed '1d' $(word 2,$^) >> $@

