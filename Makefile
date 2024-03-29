# IHCC Demonstration Makefile
# James A. Overton <james@overton.ca>
#
# WARN: This file contains significant whitespace, i.e. tabs!
# Ensure that your text editor shows you those characters.

### Workflow
# The following workflow defines all tasks necessary to upload,
# preprocess, share, and map a new data dictionary.
#
# 1. [Upload cohort data](./src/workflow.py?action=create)
# 2. [Open Google Sheet](./src/workflow.py?action=open)
# 3. [Run automated mapping for new data dictionary](automated_mapping)
# 4. [Share Google Sheet with submitter](./src/workflow.py?action=share)
# 5. [Prepare data dictionary for build](prepare_build)
# 6. [Run automated validation](automated_validation)
# 7. [Build data dictionary](all)
# 8. [View results](build/)
# 9. [Add data dictionary to Version Control](finalize)
# 10. Prepare git commit (click on `Commit` in `Version Control` menu)
# 11. Push changes to GitHub (click on `Push` in `Version Control` menu), and make pull request.
# 12. [Delete Google sheet (Caution, cannot be undone)](cogs_delete)
#
#### IHCC Data Admin Tasks
# * [Update all data, including data dictionaries](all)
# * [Update only data dictionaries](owl)
# * [Run all mappings (quality control)](all_mapping_suggest)
# * [Clean build directory](clean)
# [](./src/tree.sh)

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
TODAY ?= $(shell date +%Y-%m-%d)

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
COHORTS := $(filter-out maelstrom, $(patsubst %.ttl, %, $(notdir $(wildcard metadata/*.ttl))))

TEMPLATES := $(foreach C,$(COHORTS),templates/$(C).tsv)
METADATA := $(foreach C,$(COHORTS),metadata/$(C).ttl)
ZOOMA_DATASET = data/ihcc-mapping-suggestions-zooma.tsv
OLS_CONFIG = data/ols-config.yaml

# --- These files are not in version control (all in build directory) ---

# OWL file in the build directory for all cohorts (contains xrefs)
ONTS := $(foreach C,$(COHORTS),build/$(C).owl)

# HTML tree browser and table for each cohort
DBS := build/gecko.db $(foreach C,$(COHORTS),build/$(C).db)
TABLES := $(foreach C,$(COHORTS),build/$(C).html)


### General Tasks

.PHONY: clean
clean:
	rm -rf build

.PHONY: all
all: $(DBS) $(TABLES)
all: build/index.html
all: data/cohort-data.json
all: build/member_cohorts.csv
all: owl
all: $(ZOOMA_DATASET)
all: $(OLS_CONFIG)


.PHONY: update
update: clean all

build/index.html: src/create_index.py src/index.html.jinja2 data/metadata.json | $(DBS) $(TABLES)
	python3 $^ $@

.PHONY: finalize
finalize: src/finalize.py build/metadata.tsv
	python3 $^


### MAELSTROM Tasks

.PHONY: refresh-maelstrom
refresh-maelstrom:
	rm data/maelstrom.yml
	make data/maelstrom.yml

data/maelstrom.yml:
	curl -Lk https://raw.githubusercontent.com/maelstrom-research/maelstrom-taxonomies/master/AreaOfInformation.yml > $@

.PHONY: update-maelstrom-template
update-maelstrom-template: src/convert/maelstrom.py data/maelstrom.yml templates/maelstrom.tsv
	python3 $^

# Maelstrom has different headers than other templates
build/maelstrom.tsv: templates/maelstrom.tsv
	sed -E '2s/^/ID	AL rdfs:label@en	AL definition@en	SC %	AL label@fr	AL definition@fr	A internal ID#	is-required;#/' $< | tr '#' '\n' > $@

### Cohort OWL Files

# Run `make owl` to generate all cohort OWL files
.PHONY: owl
owl: $(ONTS) | data_dictionaries
	cp $^ data_dictionaries/

build/%.tsv: templates/%.tsv
	sed -E '2s/^/ID	LABEL	C % SPLIT=|	A definition		A internal ID#	is-required;#/' $< | tr '#' '\n' > $@

build/%.owl: build/intermediate/properties.owl build/%.tsv build/intermediate/%-xrefs.tsv metadata/%.ttl | build/robot.jar
	$(ROBOT) template --input $< \
	--merge-before \
	--template $(word 2,$^) \
	template \
	--template $(word 3,$^) \
	--merge-before \
	annotate --ontology-iri "https://purl.ihccglobal.org/$(notdir $@)" \
	--version-iri "https://purl.ihccglobal.org/$(notdir $(basename $@))/releases/$(TODAY)/$(notdir $@)" \
	--annotation-file $(word 4,$^) \
	--output $@

# Generate a metadata file for the current cohort, move the terminology to templates, & add the prefix
# TODO - this should not be a phony task name,
#        ideally we should use the branch name here but all other tasks are using the "metadata" file
.PHONY: prepare_build
prepare_build: src/prepare.py build/metadata.tsv build/terminology.tsv src/prefixes.json data/metadata.json
	python3 $^


### GECKO Mapping TSVs

# Intermediate files for GECKO mappings

# GECKO terms as xrefs for main files
# These are required to build the cohort OWL file
# The xrefs are generated from the mapping template

build/intermediate/gecko_index.tsv: build/gecko.owl | build/robot.jar build/intermediate
	$(ROBOT) export --input $< \
	 --header "ID|LABEL" \
	 --sort "ID" \
	 --export $@

build/intermediate/%-xrefs.tsv: src/create_xref_template.py build/%.tsv build/intermediate/gecko_index.tsv | build/intermediate
	python3 $^ $@


### Trees and Tables

build/prefixes.sql: src/convert_prefixes.py src/prefixes.json | build
	python3 $^ $@

build/%.db: build/prefixes.sql build/%.owl | build/rdftab
	rm -rf $@
	sqlite3 $@ < $<
	./build/rdftab $@ < $(word 2,$^)

UC = $(shell echo '$*' | tr '[:lower:]' '[:upper:]')
PREDICATES := CURIE label rdfs:subClassOf definition oboInOwl:hasDbXref IHCC:internal-id

build/%.html: build/%.db
	python3 -m gizmos.export \
	-d $< \
	-f html \
	$(foreach P,$(PREDICATES),-p $(P)) \
	-V CURIE \
	-w "stanza LIKE '$(call UC,$(basename $(notdir $@))):%'" | \
	sed 's/rdfs:subClassOf/parent/g' | \
	sed 's/oboInOwl:hasDbXref/GECKO category/g' | \
	sed 's/IHCC:internal-id/internal ID/g' > $@


### JSON Data for Real Browser

# Top-level cohort data

build/gecko_structure.json: src/get_gecko_structure.py build/gecko.db
	python3 $^ > $@

data/cohort-data.json: src/generate_cohort_json.py data/metadata.json build/gecko_structure.json $(TEMPLATES)
	python3 $(filter-out $(TEMPLATES),$^) $@

# Real cohort data + randomly-generated cohort data

data/full-cohort-data.json: data/cohort-data.json data/random-data.json
	rm -f $@
	sed '$$d' $< | sed '$$d' >> $@
	echo '  },' >> $@
	sed '1d' $(word 2,$^) >> $@


### Admin Metadata

build/member_cohorts.csv: src/convert_metadata.py data/metadata.json
	python3 $^ $@


### COGS Set Up & Tasks

# The branch name should be the namespace for the new cohort
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

init-cogs: .cogs

templates/$(BRANCH).tsv:
	echo -e "Term ID\tLabel\tParent Term\tDefinition\tGECKO Category\tSuggested Categories\tComment\n" > $@

# required env var GOOGLE_CREDENTIALS
.cogs: | templates/$(BRANCH).tsv
	cogs init -u $(EMAIL) -t $(BRANCH)
	cogs add templates/$(BRANCH).tsv -r 2
	cogs push
	cogs open

cogs-apply-%: build/cogs-%.tsv
	cogs apply $<

destroy-cogs: | .cogs
	cogs delete -f


### Pre-build Tasks

build build/intermediate build/browser build/browser/cohorts data_dictionaries:
	mkdir -p $@

build/robot.jar: | build
	curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/master/lastSuccessfulBuild/artifact/bin/robot.jar

UNAME := $(shell uname)
ifeq ($(UNAME), Darwin)
	RDFTAB_URL := https://github.com/ontodev/rdftab.rs/releases/download/v0.1.1/rdftab-x86_64-apple-darwin
else
	RDFTAB_URL := https://github.com/ontodev/rdftab.rs/releases/download/v0.1.1/rdftab-x86_64-unknown-linux-musl
endif

build/rdftab: | build
	curl -L -o $@ $(RDFTAB_URL)
	chmod +x $@

build/intermediate/properties.owl: templates/properties.tsv | build/intermediate build/robot.jar
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
build/browser/%-mapping.json: src/browser/generate_mapping_json.py build/%.tsv build/intermediate/gecko_index.tsv | build/browser
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

##################################################
####### IHCC Mapping validation pipeline #########
##################################################

build/gecko_labels.tsv: build/gecko.owl | build/robot.jar
	$(ROBOT) export \
	--input $< \
	--header "LABEL" \
	--export $@

# We always get the latest changes before running validation
build/cogs-problems.tsv: src/validate.py src/metadata-schema.json data/metadata.json build/terminology.tsv build/gecko_labels.tsv
	python3 $^ $@

.PHONY: automated_validation
automated_validation:
	make cogs_pull
	make cogs-apply-problems
	cogs push

###################################################
####### IHCC Mapping suggestions pipeline #########
###################################################

# Pipeline to generate mapping suggestions for a template. The template file is loaded,
# the suggestions generated and added as a colum "Suggested Categories" to the template.

MAP_SUGGEST := $(foreach C, $(COHORTS), build/suggestions_$(C).tsv)
GECKO_LEXICAL = build/intermediate/gecko-xrefs-sparql.csv
MAP_SCRIPT_DIR = src/mapping-suggest
MAP_SCRIPT_CONFIG = $(MAP_SCRIPT_DIR)/mapping-suggest-config.yml

.PHONY: all_mapping_suggest
all_mapping_suggest: src/mapping-suggest/mapping-suggest-qc.py $(MAP_SUGGEST)
	python3 $< --templates $(MAP_SUGGEST) -v -o build/$@_report.tsv

.PHONY: id_generation_%
id_generation_%: $(MAP_SCRIPT_DIR)/id-generator-templates.py templates/%.tsv
	python3 $< -t $(word 2,$^)
	
id_generation_cogs: $(MAP_SCRIPT_DIR)/id-generator-templates.py templates/cogs.tsv build/metadata.tsv
	python3 $< -t $(word 2,$^) -m build/metadata.tsv

build/intermediate/%_mapping_suggestions_nlp.tsv: $(MAP_SCRIPT_DIR)/mapping-suggest-nlp.py \
													templates/%.tsv $(GECKO_LEXICAL) \
													id_generation_% | build/intermediate
	python3 $< -z $(ZOOMA_DATASET) -c $(MAP_SCRIPT_CONFIG) -t templates/$*.tsv -g $(GECKO_LEXICAL) -o $@

build/intermediate/%_mapping_suggestions_zooma.tsv: $(MAP_SCRIPT_DIR)/mapping-suggest-zooma.py \
													$(MAP_SCRIPT_CONFIG) templates/%.tsv \
													id_generation_% | build/intermediate
	python3 $< -c $(MAP_SCRIPT_CONFIG) -t templates/$*.tsv -o $@

# All of the mapping suggestion tables should have the following columns: ["confidence", "match", "match_label"]
build/suggestions_%.tsv: templates/%.tsv \
					build/intermediate/%_mapping_suggestions_zooma.tsv \
					build/intermediate/%_mapping_suggestions_nlp.tsv
	python3 $(MAP_SCRIPT_DIR)/merge-mapping-suggestions.py -t $< $(patsubst %, -s %, $(filter-out $<,$^)) -o $@

build/cogs-data-validation.tsv build/cogs-info-table.tsv: $(MAP_SCRIPT_DIR)/create-data-validation.py build/terminology.tsv build/gecko_labels.tsv
	python3 $^ build/cogs-data-validation.tsv build/cogs-info-table.tsv

# Pipeline to build a the zooma dataset that stores the existing mappings

MAP_DATA := $(foreach C, $(COHORTS), build/intermediate/$(C)-xrefs-sparql.csv)

# TODO: Should this depend on data_dictionaries/%.owl or better build/%.owl?
build/intermediate/%-xrefs-sparql.csv: build/%.owl src/queries/ihcc-mapping.sparql | build/intermediate build/robot.jar
	$(ROBOT) query --input $< --query $(word 2,$^) $@

$(GECKO_LEXICAL): build/gecko.owl src/queries/ihcc-mapping-gecko.sparql | build/intermediate build/robot.jar
	$(ROBOT) query --input $< --query $(word 2,$^) $@

$(ZOOMA_DATASET): $(MAP_SCRIPT_DIR)/ihcc-zooma-dataset.py $(GECKO_LEXICAL) $(MAP_DATA)
	python3 $< $(patsubst %, -l %, $(filter-out $<,$^)) -w $(shell pwd) -o $@

.PHONY: update_ols
update_ols: $(OLS_CONFIG)

$(OLS_CONFIG): src/prepare_ols_config.py $(METADATA)
	python3 $< $(patsubst %, -m %, $(METADATA)) -o $(OLS_CONFIG)

.PHONY: cogs_pull
cogs_pull:
	cogs fetch
	cogs pull
	
.PHONY: cogs_delete
cogs_delete:
	cogs delete -f

.PHONY: automated_mapping
automated_mapping:
	make cogs_pull
	cp build/terminology.tsv templates/cogs.tsv
	make build/suggestions_cogs.tsv
	cp build/suggestions_cogs.tsv build/terminology.tsv
	rm -f templates/cogs.tsv
	make cogs-apply-data-validation
	make cogs-apply-info-table
	cogs push
