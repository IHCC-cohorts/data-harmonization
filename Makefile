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

### Pre-build Tasks

build:
	mkdir -p $@

build/robot.jar: | build
	curl -Lk -o $@ https://github.com/ontodev/robot/releases/download/v1.6.0/robot.jar


### CINECA Tasks

data/cineca.tsv:
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1ZXqTMIhFtGOaodw7Fns5YghvY_pWos-RuSa2BFnO5l4/export?format=tsv"

build/cineca.tsv: src/cineca.py data/cineca.tsv | build
	python3 $^ $@

build/properties.owl: src/properties.tsv | build/robot.jar
	$(ROBOT) template --template $< --output $@

build/cineca.owl: build/properties.owl build/cineca.tsv | build/robot.jar
	$(ROBOT) template --input $< --merge-before --template $(word 2,$^) --output $@


### Maelstrom Tasks

data/maelstrom.yml:
	curl -L -o $@ https://raw.githubusercontent.com/maelstrom-research/maelstrom-taxonomies/master/AreaOfInformation.yml

build/maelstrom.tsv: src/maelstrom.py data/maelstrom.yml | build
	python3 $^ $@

build/maelstrom.owl: metadata/maelstrom.ttl build/maelstrom.tsv | build/robot.jar
	$(ROBOT) template --input $< --merge-before --template $(word 2,$^) \
	annotate --ontology-iri http://example.com/maelstrom.owl --output $@


### General Tasks

.PHONY: refresh
refresh:
	rm -r data/cineca.tsv

.PHONY: clean
clean:
	rm -rf build

.PHONY: all
all: build/cineca.owl
