#!/usr/bin/env python
# coding: utf-8

"""
This script is responsible for merging, prioritising and formatting incoming mapping tables,
generated, for example, by the mapping-suggest-zooma or mapping-suggest-nlp pipeline.
author: Nico Matentzoglu for Knocean Inc., 15 September 2020
"""

import pandas as pd
from argparse import ArgumentParser
from lib import ihcc_purl_prefix

parser = ArgumentParser()
parser.add_argument(
    "-s",
    "--suggestion-table",
    action="append",
    dest="mapping_suggestion_files",
    help="The set of mapping suggestions to be merged.",
)
parser.add_argument("-t", "--template", dest="template_file", help="Template file", metavar="FILE")
parser.add_argument(
    "-o", "--output", dest="mapping_suggestions_out_path", help="Output file", metavar="FILE"
)
args = parser.parse_args()

print(args.mapping_suggestion_files)
df = pd.concat([pd.read_csv(f, sep="\t") for f in args.mapping_suggestion_files])
df.head()

template = pd.read_csv(args.template_file, sep="\t")
print(len(template))

# Transform matches into the right format and merge into template
dfs = df[~df["match"].str.startswith(ihcc_purl_prefix)].copy()
dfs["confidence"] = dfs["confidence"].astype(str)
dfs["Suggested Categories"] = dfs[["confidence", "match", "match_label"]].agg(" ".join, axis=1)
dfs = dfs[["term", "Suggested Categories"]]
dfsagg = dfs.groupby("term", as_index=False).agg(lambda x: " | ".join(set(x.dropna())))
dfx = pd.merge(template, dfsagg, how="left", left_on=["Label"], right_on=["term"])
del dfx["term"]

print(dfx.head())
print(len(dfx))

# Save template
with open(args.template_file, "w") as write_csv:
    write_csv.write(dfx.to_csv(sep="\t", index=False))
