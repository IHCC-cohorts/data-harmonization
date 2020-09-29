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

from lib import load_ihcc_config, map_term

parser = ArgumentParser()
parser.add_argument("-c", "--config", dest="config_file", help="Config file", metavar="FILE")
parser.add_argument("-t", "--template", dest="tsv_path", help="Template file", metavar="FILE")
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
print(config)

# Loading data
tsv = pd.read_csv(args.tsv_path, sep="\t")
tsv_terms = tsv["Label"].values[2:]

# Generating matches
matches = []

for term in tsv_terms:
    if isinstance(term, str):
        print("Matching " + term)
        matches.extend(map_term(term, zooma_annotate, ols_term, ols_oboid, confidence_map))
    else:
        print("ERROR term '%s' does not seem to be a string!" % term)

df = pd.DataFrame(matches, columns=["term", "match", "match_label", "confidence"])

zooma_confidence_map = {"LOW": 0.5, "MEDIUM": 0.75, "GOOD": 0.99, "HIGH": 1.0}
if "zooma_confidence_mappings" in config:
    zooma_confidence_map = config["zooma_confidence_mappings"]

df["confidence"] = df["confidence"].replace(zooma_confidence_map)

print("Zooma matching successful. First rows:")
print(df.head(3))


# Save template
with open(args.tsv_out_path, "w") as write_csv:
    write_csv.write(df.to_csv(sep="\t", index=False))
