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
# - Genomics England
#   [term table](build/genomics-england.html),
#   [tree view](build/genomics-england-tree.html),
#   [genomics-england.owl](build/genomics-england.owl)
# - Golestan Cohort Study (GCS)
#	[term table](build/gcs.html)
#	[tree view](build/gcs-tree.html)
#	[gcs.owl](build/gcs.owl)
# - Vukuzazi
#	[term table](build/vukuzazi.html)
#	[tree view](build/vukuzazi-tree.html)
#	[vukuzazi.owl](build/vukuzazi.owl)
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

#ROBOT = java -jar build/robot.jar --prefixes src/prefixes.json
ROBOT = robot --prefixes src/prefixes.json
ROBOT_RDFXML = java -jar build/robot-rdfxml.jar

### Pre-build Tasks

build:
	mkdir -p $@

build/robot.jar: | build
	curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/curie-provider/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-tree.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/tree-view/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-validate.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/validate/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-rdfxml.jar: | build
	curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/mireot-rdfxml/lastSuccessfulBuild/artifact/bin/robot.jar

### GECKO Tasks

data/cineca.tsv:
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1ZXqTMIhFtGOaodw7Fns5YghvY_pWos-RuSa2BFnO5l4/export?format=tsv"

build/gecko.tsv: src/convert/gecko.py data/cineca.tsv src/gecko/index.tsv | build
	python3 $^ $@

build/properties.owl: src/properties.tsv | build/robot.jar
	$(ROBOT) template --template $< --output $@

build/gecko.owl: build/properties.owl build/gecko.tsv metadata/gecko.ttl | build/robot.jar
	$(ROBOT) template --input $< \
	--merge-before \
	--template $(word 2,$^) \
	merge --input $(word 3,$^) \
	--include-annotations true \
	annotate --ontology-iri "http://example.com/gecko.owl" \
	--output $@

.PRECIOUS: build/ncit.owl.gz
build/ncit.owl.gz: | build/robot.jar
	$(ROBOT) convert --input-iri http://purl.obolibrary.org/obo/ncit.owl --output $@

build/ncit-terms.txt: build/gecko.owl src/gecko/get-ncit-ids.rq src/gecko/ncit-annotation-properites.txt | build/robot.jar
	$(ROBOT) query --input $< --query $(word 2,$^) $@
	tail -n +2 $@ > $@.tmp
	cat $@.tmp $(word 3,$^) > $@ && rm $@.tmp

build/ncit-module.owl: build/ncit.owl.gz build/ncit-terms.txt | build/robot-rdfxml.jar
	$(ROBOT_RDFXML) extract --input $< \
	--term-file $(word 2,$^) \
	--method rdfxml \
	--intermediates minimal --output $@ 

build/gecko-mapping.tsv: | build
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1IRAv5gKADr329kx2rJnJgtpYYqUhZcwLutKke8Q48j4/export?format=tsv"

build/gecko-terms.txt: build/gecko-mapping.tsv
	tail -n+2 $< | awk '{ print $$4 }' FS='\t' | awk '!seen[$$0]++' > $@

build/cmo.owl: | build
	curl -Lk -o $@ http://purl.obolibrary.org/obo/cmo.owl

build/hp.owl: | build
	curl -Lk -o $@ http://purl.obolibrary.org/obo/hp.owl

build/chebi.owl.gz: | build
	curl -Lk -o $@ http://purl.obolibrary.org/obo/chebi.owl.gz

build/cmo-module.owl: build/cmo.owl build/gecko-terms.txt src/gecko/measurement.ru | build/robot.jar
	$(ROBOT) extract --input $< \
	--method MIREOT \
	--lower-terms $(word 2,$^) \
	--intermediates none \
	query --update $(word 3,$^) \
	--output $@

build/hp-module.owl: build/hp.owl build/gecko-terms.txt src/gecko/clinical-finding.ru | build/robot.jar
	$(ROBOT) extract --input $< \
	--method MIREOT \
	--lower-terms $(word 2,$^) \
	--intermediates none \
	query --update $(word 3,$^) \
	--output $@

build/chebi-module.owl: build/chebi.owl.gz build/gecko-terms.txt src/gecko/exposure-event.ru | build/robot.jar
	$(ROBOT) extract --input $< \
	--method RDFXML \
	--term-file $(word 2,$^) \
	--intermediates none \
	query --update $(word 3,$^) \
	--output $@

build/gecko-ext.owl: src/gecko/gecko-upper.ttl build/cmo-module.owl build/hp-module.owl build/chebi-module.owl | build/robot.jar
	$(ROBOT) merge --input $< \
	--input $(word 2,$^) \
	--input $(word 3,$^) \
	--input $(word 4,$^) \
	--output $@


### Genomics England Tasks

data/genomics-england.xlsx:
	curl -L -o $@ "https://cnfl.extge.co.uk/download/attachments/113189195/Data%20Dictionary%20Main%20Programme%20v6%20%281%29.xlsx?version=1&modificationDate=1551371214157&api=v2"

build/genomics-england.tsv: src/convert/genomics-england.py data/genomics-england.xlsx | build
	python3 $^ $@

build/genomics-england.owl: build/properties.owl build/genomics-england.tsv metadata/genomics-england.ttl | build/robot.jar
	$(ROBOT) template --input $< \
	--merge-before \
	--template $(word 2,$^) \
	merge --input $(word 3,$^) \
	--include-annotations true \
	annotate --ontology-iri "http://example.com/genomics-england.owl" \
	--output $@


### Golestan Cohort Study (GCS) Tasks

data/golestan-cohort-study.xlsx:
	curl -L -o $@ "https://drive.google.com/uc?export=download&id=1ZLw-D6AZFKrBjTNsc4wzlthYq4w4KmOJ"

build/gcs.tsv: src/convert/golestan-cohort-study.py data/golestan-cohort-study.xlsx | build
	python3 $^ $@

build/gcs.owl: build/properties.owl build/gcs.tsv metadata/gcs.ttl | build/robot.jar
	$(ROBOT) template --input $< \
	--merge-before \
	--template $(word 2,$^) \
	merge --input $(word 3,$^) \
	--include-annotations true \
	annotate --ontology-iri "http://example.com/gcs.owl" \
	--output $@


### Vukuzazi Tasks

data/vukuzazi.xlsx:
	curl -L -o $@ "https://drive.google.com/uc?export=download&id=1YpwjiYDos5ZkXMQR6wG4Qug7sMmKB5xC"

build/vukuzazi.tsv: src/convert/vukuzazi.py data/vukuzazi.xlsx | build
	python3 $^ $@

build/vukuzazi.owl: build/properties.owl build/vukuzazi.tsv metadata/vukuzazi.ttl | build/robot.jar
	$(ROBOT) template --input $< \
	--merge-before \
	--template $(word 2,$^) \
	merge --input $(word 3,$^) \
	--include-annotations true \
	annotate --ontology-iri "http://example.com/vukuzazi.owl" \
	--output $@


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


### Browser

build/gecko-ext.json: build/gecko-ext.owl | build/robot.jar
	$(ROBOT) export \
	--input $< \
	--header "ID|LABEL|definition|subclasses" \
	--sort "LABEL" \
	--export $@

build/gecko-mapping.json: src/tsv2json.py build/gecko-mapping.tsv
	python3 $^ > $@

build/gcs.json: build/gcs.owl | build/robot.jar
	$(ROBOT) export \
	--input $< \
	--header "ID|LABEL|definition|question description|value|see also" \
	--sort "LABEL" \
	--export $@

build/gecko.json: build/gecko.owl | build/robot.jar
	$(ROBOT) export \
	--input $< \
	--header "ID|LABEL|definition|question description|value|see also" \
	--sort "LABEL" \
	--export $@

build/genomics-england.json: build/genomics-england.owl | build/robot.jar
	$(ROBOT) export \
	--input $< \
	--header "ID|LABEL|definition|question description|value|see also" \
	--sort "LABEL" \
	--export $@

build/vukuzazi.json: build/vukuzazi.owl | build/robot.jar
	$(ROBOT) export \
	--input $< \
	--header "ID|LABEL|definition|question description|value|see also" \
	--sort "LABEL" \
	--export $@

build/index.html: src/index.html | build
	cp $< $@

BROWSER := build/index.html build/gcs.json build/gecko.json build/gecko-ext.json build/gecko-mapping.json build/genomics-england.json build/vukuzazi.json
browser: $(BROWSER)

serve: $(BROWSER)
	cd build && python3 -m http.server 8000


### General Tasks

.PHONY: refresh
refresh:
	rm -rf data/cineca.tsv
	touch data/genomics-england.xlsx
	touch data/golestan-cohort-study.xlsx
	touch data/vukuzazi.xlsx

.PHONY: clean
clean:
	rm -rf build

.PHONY: all
all: build/gecko.html build/gecko-tree.html
all: build/ncit-module-tree.html
all: build/genomics-england.html build/genomics-england-tree.html
all: build/gcs.html build/gcs-tree.html
all: build/vukuzazi.html build/vukuzazi-tree.html
all: $(BROWSER)
