# IHCC Demonstration Makefile
# James A. Overton <james@overton.ca>
#
# WARN: This file contains significant whitespace, i.e. tabs!
# Ensure that your text editor shows you those characters.

### Workflow
#
# - GECKO
#   [source table](https://docs.google.com/spreadsheets/d/1ZXqTMIhFtGOaodw7Fns5YghvY_pWos-RuSa2BFnO5l4),
#   [term table](build/gecko.html),
#   [tree view](build/gecko-tree.html),
#   [gecko.owl](build/gecko.owl)
#     - GECKO NCIT
#       [tree view](build/ncit-module-tree.html),
#       [ncit-module.owl](build/ncit-module.owl)
#     - GECKO full 
#       [tree view](build/gecko-full-tree.html),
#       [gecko-full.owl](build/gecko-full.owl)
# - Genomics England
#   [term table](build/genomics-england.html),
#   [tree view](build/genomics-england-tree.html),
#   [genomics-england.owl](build/genomics-england.owl)
# - Golestan Cohort Study (GCS),
#   [term table](build/gcs.html),
#   [tree view](build/gcs-tree.html),
#   [gcs.owl](build/gcs.owl)
#     - GCS to GECKO mapping
#        [tree view](build/gcs-gecko-tree.html),
#        [gcs-gecko.owl](build/gcs-gecko.owl)
# - Korean Genome and Epidemiology Study (KoGES)
#   [source document](https://drive.google.com/file/d/1Hh_cG9HcZWXs70FEun8iDZZbt0H_J1oq/view),
#   [term table](build/koges.html),
#   [tree view](build/koges-tree.html),
#   [koges.owl](build/koges.owl)
#     - KoGES to GECKO mapping
#       [tree view](build/koges-gecko-tree.html),
#       [koges-gecko.owl](build/koges-gecko.owl)
# - SAPRIN
#   [source table](https://docs.google.com/spreadsheets/d/1KjULwQ38IkWqJxOCZZ2em8ge7NZJEngOZqI3ebC9Wkk/edit?usp=sharing),
#   [term table](build/saprin.html),
#   [tree view](build/saprin-tree.html),
#   [saprin.owl](build/saprin.owl)
# - Vukuzazi
#   [term table](build/vukuzazi.html),
#   [tree view](build/vukuzazi-tree.html),
#   [vukuzazi.owl](build/vukuzazi.owl)
# - [View mockup](build/index.html)
# - [Rebuild](all)

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

### Pre-build Tasks

build build/mapping build/cohorts:
	mkdir -p $@

build/robot.jar: | build
	curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/curie-provider/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-tree.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/tree-view/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-validate.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/validate/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-rdfxml.jar: | build
	curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/mireot-rdfxml/lastSuccessfulBuild/artifact/bin/robot.jar

build/properties.owl: src/properties.tsv | build/robot.jar
	$(ROBOT) template --template $< --output $@

### GECKO Tasks

# GECKO from CINECA

data/cineca.tsv:
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1ZXqTMIhFtGOaodw7Fns5YghvY_pWos-RuSa2BFnO5l4/export?format=tsv"

build/gecko.tsv: src/convert/gecko.py data/cineca.tsv src/indexes/gecko.tsv | build
	python3 $^ $@

# NCIT Module - NCIT terms that have been mapped to GECKO terms

.PRECIOUS: build/ncit.owl.gz
build/ncit.owl.gz: | build
	curl -L http://purl.obolibrary.org/obo/ncit.owl | gzip > $@

build/ncit-terms.txt: build/gecko.owl src/gecko/get-ncit-ids.rq src/gecko/ncit-annotation-properites.txt | build/robot.jar
	$(ROBOT) query --input $< --query $(word 2,$^) $@
	tail -n +2 $@ > $@.tmp
	cat $@.tmp $(word 3,$^) > $@ && rm $@.tmp

build/ncit-module.owl: build/ncit.owl.gz build/ncit-terms.txt | build/robot-rdfxml.jar
	$(ROBOT_RDFXML) extract --input $< \
	--term-file $(word 2,$^) \
	--method rdfxml \
	--intermediates minimal --output $@


### Genomics England Tasks

data/genomics-england.xlsx:
	curl -L -o $@ "https://cnfl.extge.co.uk/download/attachments/113189195/Data%20Dictionary%20Main%20Programme%20v6%20%281%29.xlsx?version=1&modificationDate=1551371214157&api=v2"

build/genomics-england.tsv: src/convert/genomics-england.py data/genomics-england.xlsx | build
	python3 $^ $@


### Golestan Cohort Study (GCS) Tasks

data/golestan-cohort-study.xlsx:
	curl -L -o $@ "https://drive.google.com/uc?export=download&id=1ZLw-D6AZFKrBjTNsc4wzlthYq4w4KmOJ"

build/gcs.tsv: src/convert/golestan-cohort-study.py data/golestan-cohort-study.xlsx | build
	python3 $^ $@


### KoGES Tasks

data/koges.tsv:
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1hPcCzjFWHJ7iiqMHBpuodFCrrTvSmCKfQu0f93JPhU8/export?format=tsv"

build/koges.tsv: src/convert/koges.py data/koges.tsv src/indexes/koges.tsv | build
	python3 $^ $@


### SAPRIN Tasks

data/saprin.tsv:
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1KjULwQ38IkWqJxOCZZ2em8ge7NZJEngOZqI3ebC9Wkk/export?format=tsv"

build/saprin.tsv: src/convert/saprin.py data/saprin.tsv | build
	python3 $^ $@


### Vukuzazi Tasks

data/vukuzazi.xlsx:
	curl -L -o $@ "https://drive.google.com/uc?export=download&id=1YpwjiYDos5ZkXMQR6wG4Qug7sMmKB5xC"

build/vukuzazi.tsv: src/convert/vukuzazi.py data/vukuzazi.xlsx | build
	python3 $^ $@


### Templates -> OWL 

ONTS := build/gecko.owl build/gcs.owl build/genomics-england.owl build/koges.owl build/saprin.owl build/vukuzazi.owl

build/%.owl: build/properties.owl build/%.tsv metadata/%.ttl | build/robot.jar
	$(ROBOT) template --input $< \
	--merge-before \
	--template $(word 2,$^) \
	merge --input $(word 3,$^) \
	--include-annotations true \
	annotate --ontology-iri "http://example.com/$(notdir $@)" \
	--output $@

build/gecko.ttl: build/gecko.owl | build/robot.jar
	$(ROBOT) convert --input $< --output $@


### Trees and Tables

build/%-tree.html: build/%.owl | build/robot-tree.jar
	java -jar build/robot-tree.jar tree \
	--input $< \
	--tree $@

build/%.html: build/%.owl build/%.tsv | build/robot-validate.jar
	java -jar build/robot-validate.jar validate \
	--input $< \
	--table $(word 2,$^) \
	--skip-row 2 \
	--format HTML \
	--standalone true \
	--output-dir build/


### GECKO Mapping Tasks

build/mapping/gecko-mapping.xlsx: | build/mapping
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1IRAv5gKADr329kx2rJnJgtpYYqUhZcwLutKke8Q48j4/export?format=xlsx"

build/mapping/index.tsv: src/xlsx2tsv.py build/mapping/gecko-mapping.xlsx | build/mapping
	python3 $^ Index > $@

build/mapping/properties.tsv: src/xlsx2tsv.py build/mapping/gecko-mapping.xlsx | build/mapping
	python3 $^ Properties > $@

build/mapping/koges-mapping.tsv: src/xlsx2tsv.py build/mapping/gecko-mapping.xlsx | build/mapping
	python3 $^ KoGES > $@

build/mapping/gcs-mapping.tsv: src/xlsx2tsv.py build/mapping/gecko-mapping.xlsx | build/mapping
	python3 $^ GCS > $@

# GECKO plus OBO terms

build/mapping/index.owl: build/mapping/properties.tsv build/mapping/index.tsv
	$(ROBOT) template --template $< \
	template --merge-before \
	--template $(word 2,$^) \
	--output $@

build/gecko-full.owl: build/gecko.owl build/mapping/index.owl | build/robot.jar
	$(ROBOT) merge --input $< \
	--input $(word 2,$^) \
	reason reduce \
	--output $@

# Other cohorts -> GECKO mapping

MAPPINGS := build/mapping/koges-gecko.ttl build/mapping/gcs-gecko.ttl

# Cohort terms + GECKO terms from template
# The GECKO terms are just referenced and do not have structure/annotations

build/mapping/%-mapping.owl: build/gecko-full.owl build/mapping/%-mapping.tsv build/%.owl | build/robot.jar
	$(ROBOT) template \
	--input $< \
	--template $(word 2,$^) \
	merge --input $(word 3,$^) \
	reason reduce --output $@

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

# Cohort terms + GECKO terms (full version)
# TTL version of mapping for loading into rdflib

build/mapping/%-gecko.ttl: build/mapping/gecko-%.ttl build/mapping/%-mapping.owl | build/robot.jar
	$(ROBOT) merge --input $< \
	--input $(word 2,$^) \
	relax reduce \
	remove --axioms equivalent \
	--output $@

# OWL version of mapping

build/%-gecko.owl: build/mapping/%-gecko.ttl
	$(ROBOT) convert --input $< --output $@

# CSV of cohort terms -> all ancestor GECKO terms

build/mapping/%-mapping.csv: build/mapping/%-gecko.ttl src/queries/get-cineca-%.rq | build/robot.jar
	$(ROBOT) query --input $< --query $(word 2,$^) $@

# JSON of ancestor GECKO term (key) -> list of cohort terms (value)
# This is used to drive the filter functionality in the browser

build/%-mapping.json: src/json/generate_mapping_json.py build/mapping/%-mapping.csv
	python3 $^ $@

# Top-level cohort data

build/mapping/data.json: src/json/generate_cohort_json.py data/member_cohorts.csv | $(MAPPINGS)
	python3 $^ $@


### Browser

DATA := build/gcs-data.json build/gecko-data.json build/genomics-england-data.json build/koges-data.json build/saprin-data.json build/vukuzazi-data.json

build/%-data.json: build/%.owl | build/robot.jar
	$(ROBOT) export \
	--input $< \
	--header "ID|LABEL|definition|question description|value|see also|subclasses" \
	--sort "LABEL" \
	--export $@

# GECKO without OBO terms = CINECA
# This is used to drive aggregations
# TODO - automatically create this
build/cineca.json: src/json/cineca.json
	cp $< $@

build/index.html: src/index.html | build
	cp $< $@

# Top-level cohort data as HTML pages 

COHORT_PAGES := build/cohorts/koges.html build/cohorts/gcs.html

cohorts: $(COHORT_PAGES)

$(COHORT_PAGES): src/create_cohort_html.py build/mapping/data.json data/metadata.json src/cohort.html.jinja2 build/cohorts
	python3 $^

BROWSER := build/index.html build/cineca.json build/koges-mapping.json build/gcs-mapping.json cohorts $(DATA)
browser: $(BROWSER)

serve: $(BROWSER)
	cd build && python3 -m http.server 8000


### General Tasks

.PHONY: refresh
refresh:
	rm -rf data/cineca.tsv
	rm -rf data/koges.tsv
	rm -rf data/saprin.tsv
	touch data/genomics-england.xlsx
	touch data/golestan-cohort-study.xlsx
	touch data/vukuzazi.xlsx

.PHONY: clean
clean:
	rm -rf build

.PHONY: all
all: build/gecko.html build/gecko-tree.html
all: build/gecko-full-tree.html build/koges-gecko-tree.html build/gcs-gecko-tree.html
all: build/ncit-module-tree.html
all: build/genomics-england.html build/genomics-england-tree.html
all: build/gcs.html build/gcs-tree.html
all: build/koges.html build/koges-tree.html
all: build/saprin.html build/saprin-tree.html
all: build/vukuzazi.html build/vukuzazi-tree.html
all: build/mapping/data.json
all: $(BROWSER)
