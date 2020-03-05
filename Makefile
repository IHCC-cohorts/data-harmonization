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


### CINECA Tasks

data/cineca.tsv:
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1ZXqTMIhFtGOaodw7Fns5YghvY_pWos-RuSa2BFnO5l4/export?format=tsv"

build/cineca.tsv: src/cineca.py
	python3 $^ $@

build/cineca.owl: build/cineca.tsv | build/robot.jar
	$(ROBOT) template --template $< --output $@


### General Tasks

build:
	mkdir -p $@

.PHONY: refresh
refresh:
	rm -r data/cineca.tsv

.PHONY: clean
clean:
	rm -rf build

.PHONY: all
all: build/cineca.owl
