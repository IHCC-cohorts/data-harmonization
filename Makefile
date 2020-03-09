# IHCC Demonstration Makefile
# James A. Overton <james@overton.ca>
#
# WARN: This file contains significant whitespace, i.e. tabs!
# Ensure that your text editor shows you those characters.

### Workflow
#
# - CINECA
#   [source table](https://docs.google.com/spreadsheets/d/1ZXqTMIhFtGOaodw7Fns5YghvY_pWos-RuSa2BFnO5l4),
#   [term table](build/cineca.html),
#   [tree view](build/cineca-tree.html),
#   [cineca.owl](build/cineca.owl)
#
# [Refresh](all)

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

build/robot-tree.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/tree-view/lastSuccessfulBuild/artifact/bin/robot.jar

build/robot-validate.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/validate/lastSuccessfulBuild/artifact/bin/robot.jar

### CINECA Tasks

data/cineca.tsv:
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1ZXqTMIhFtGOaodw7Fns5YghvY_pWos-RuSa2BFnO5l4/export?format=tsv"

build/cineca.tsv: src/cineca.py data/cineca.tsv | build
	python3 $^ $@

build/properties.owl: src/properties.tsv | build/robot.jar
	$(ROBOT) template --template $< --output $@

build/cineca.owl: build/properties.owl build/cineca.tsv | build/robot.jar
	$(ROBOT) template --input $< --merge-before --template $(word 2,$^) --output $@


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


### General Tasks

.PHONY: refresh
refresh:
	rm -r data/cineca.tsv

.PHONY: clean
clean:
	rm -rf build

.PHONY: all
all: build/cineca.html build/cineca-tree.html
