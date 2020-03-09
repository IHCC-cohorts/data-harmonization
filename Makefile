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

ROBOT = java -jar build/robot.jar
ROBOT_RDFXML = java -jar build/robot-rdfxml.jar

### Pre-build Tasks

build:
	mkdir -p $@

build/robot.jar: | build
	curl -Lk -o $@ https://github.com/ontodev/robot/releases/download/v1.6.0/robot.jar

build/robot-rdfxml.jar: | build
	curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/mireot-rdfxml/lastSuccessfulBuild/artifact/bin/robot.jar


### CINECA Tasks

data/cineca.tsv:
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1ZXqTMIhFtGOaodw7Fns5YghvY_pWos-RuSa2BFnO5l4/export?format=tsv"

build/cineca.tsv: src/cineca/cineca.py data/cineca.tsv | build
	python3 $^ $@

build/properties.owl: src/properties.tsv | build/robot.jar
	$(ROBOT) template --template $< --output $@

build/cineca.owl: build/properties.owl build/cineca.tsv | build/robot.jar
	$(ROBOT) template --input $< --merge-before --template $(word 2,$^) --output $@

build/ncit.owl: | build
	curl -Lk -o $@ http://purl.obolibrary.org/obo/ncit.owl

build/ncit-terms.txt: build/cineca.owl src/cineca/get-ncit-ids.rq src/cineca/ncit-annotation-properites.txt | build/robot.jar
	$(ROBOT) query --input $< --query $(word 2,$^) $@
	tail -n +2 $@ > $@.tmp
	cat $@.tmp $(word 3,$^) > $@ && rm $@.tmp

build/ncit-module.owl: build/ncit.owl build/ncit-terms.txt | build/robot-rdfxml.jar
	$(ROBOT_RDFXML) extract --input $< --term-file $(word 2,$^) --method rdfxml --intermediates minimal --output $@


### General Tasks

.PHONY: refresh
refresh:
	rm -r data/cineca.tsv

.PHONY: clean
clean:
	rm -rf build

.PHONY: all
all: build/cineca.owl
