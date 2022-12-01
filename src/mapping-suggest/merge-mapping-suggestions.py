#!/usr/bin/env python
# coding: utf-8

"""
This script is responsible for merging, prioritising and formatting incoming mapping tables,
generated, for example, by the mapping-suggest-zooma or mapping-suggest-nlp pipeline.
author: Nico Matentzoglu for Knocean Inc., 15 September 2020
"""

import pandas as pd
from argparse import ArgumentParser
from lib import ihcc_purl_prefix, format_suggestions, QCError

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

TEMPLATE_COLUMNS = [
    "Term ID",
    "Label",
    "Parent Term",
    "Definition",
    "GECKO Category",
    "Internal ID",
    "Suggested Categories",
    "Comment",
]

print(args.mapping_suggestion_files)
df = pd.concat([pd.read_csv(f, sep="\t") for f in args.mapping_suggestion_files])
print("Mapping suggestions files concat:")
print(df.head(20))

template = pd.read_csv(args.template_file, sep="\t")
if "Suggested Categories" in template.columns:
    del template["Suggested Categories"]

len_pre = len(template)

if not set(template.columns.tolist()).issubset(TEMPLATE_COLUMNS):
    raise ValueError(
        "There are columns in the template that are not allowed by the spec; "
        + "please remove them: %s (allowed %s)."
        % (str(template.columns.tolist()), str(TEMPLATE_COLUMNS))
    )

# Transform matches into the right format and merge into template
dfs = df[~df["match"].str.startswith(ihcc_purl_prefix)].copy()
dfs["confidence"] = ["%.2f" % item for item in dfs["confidence"]]
dfs["confidence"] = dfs["confidence"].astype(str)
dfs["Suggested Categories"] = dfs[["confidence", "match", "match_label"]].agg(" ".join, axis=1)
dfs = dfs[["term", "Suggested Categories"]]
dfsagg = dfs.groupby("term", as_index=False).agg(lambda x: " | ".join(set(x.dropna())))
dfx = pd.merge(template, dfsagg, how="left", left_on=["Label"], right_on=["term"])
del dfx["term"]

dfx["Suggested Categories"] = [
    format_suggestions(suggestions) for suggestions in dfx["Suggested Categories"]
]

if len_pre != len(template):
    raise RuntimeError(
        "The size of the dictionary changed " + "during the process - something went wrong (KTD)."
    )

for col in TEMPLATE_COLUMNS:
    if col not in dfx.columns:
        dfx[col] = ""

if len(dfx) > 0:
    print("Merging suggestions successful. First twenty results:")
    print(dfx[TEMPLATE_COLUMNS].head(20))
else:
    raise QCError("Merging the suggestions failed: empty result.")

# Save template
with open(args.mapping_suggestions_out_path, "w") as write_csv:
    write_csv.write(dfx[TEMPLATE_COLUMNS].to_csv(sep="\t", index=False))
