#!/usr/bin/env python
# coding: utf-8

"""
This script uses a mix of IHCC services to generate mapping suggestions for data dictionaries.
The input is a ROBOT template with the usual IHCC data dictionary. This dictionary is augmented with
Suggested mappings, which are added the 'Suggested Mappings' column of the template.
author: Nico Matentzoglu for Knocean Inc., 26 August 2020
"""

from argparse import ArgumentParser

import pandas as pd

from lib import load_ihcc_config, map_term, clean_term, remove_hierarchy_term, DictionaryMappingHelper

parser = ArgumentParser()
parser.add_argument("-c", "--config", dest="config_file", help="Config file", metavar="FILE")
parser.add_argument("-t", "--template", dest="tsv_path", help="Template file", metavar="FILE")
parser.add_argument("-p", "--preprocess", dest="preprocess", help="preprocess and clean labels", metavar="FILE")
parser.add_argument("-o", "--output", dest="tsv_out_path", help="Output file", metavar="FILE")
args = parser.parse_args()

# Loading config
config = load_ihcc_config(args.config_file)
zooma_annotate = config["zooma_annotate"]
oxo_mapping = config["oxo_mapping"]
ols_term = config["ols_term"]
ols_oboid = config["ols_oboid"]

# These are the default confidence levels from Zooma
confidence_map = ["HIGH", "GOOD", "MEDIUM", "LOW"]
print("Zooma config: %s" % str(config))

# Loading data
tsv = pd.read_csv(args.tsv_path, sep="\t")
tsv_terms = tsv["Label"].values[0:]

# Generating matches
matches = []

for term in tsv_terms:
    if isinstance(term, str):
        if args.preprocess == "WORD_BOUNDARY":
            zooma_matching_term_list = map_term(clean_term(term), zooma_annotate, ols_term, ols_oboid, confidence_map)
            for matching_term in zooma_matching_term_list:
                matching_term[0] = term
            matches.extend(zooma_matching_term_list)
        if args.preprocess == "HIERARCHY":
            zooma_matching_term_list = map_term(remove_hierarchy_term(term), zooma_annotate, ols_term, ols_oboid, confidence_map)
            for matching_term in zooma_matching_term_list:
                matching_term[0] = term
            matches.extend(zooma_matching_term_list)
        if args.preprocess == "DEFINITION":
            tsv['Definition'].fillna(tsv['Label'], inplace=True)
            definition_mapper = DictionaryMappingHelper(tsv)

            zooma_matching_term_list = map_term(definition_mapper.get_mapping(term), zooma_annotate, ols_term, ols_oboid, confidence_map)
            for matching_term in zooma_matching_term_list:
                matching_term[0] = term
            matches.extend(zooma_matching_term_list)
        else:
            zooma_matching_term_list = map_term(term, zooma_annotate, ols_term, ols_oboid, confidence_map)
            matches.extend(zooma_matching_term_list)
    else:
        print("ERROR term '%s' does not seem to be a string!" % term)

df = pd.DataFrame(matches, columns=["term", "match", "match_label", "confidence"])

zooma_confidence_map = {"LOW": 0.5, "MEDIUM": 0.75, "GOOD": 0.99, "HIGH": 1.0}
if "zooma_confidence_mappings" in config:
    zooma_confidence_map = config["zooma_confidence_mappings"]

df["confidence"] = df["confidence"].replace(zooma_confidence_map)

if len(df) > 0:
    print("Zooma matching successful. First twenty results:")
    print(df[["term", "match", "confidence"]].head(20))
else:
    print("WARNING: Zooma matching did not yield any results at all")

# Save template
with open(args.tsv_out_path, "w") as write_csv:
    write_csv.write(df.to_csv(sep="\t", index=False))
