#!/usr/bin/env python
# coding: utf-8

"""
This script uses a mix of IHCC services to generate mapping suggestions for data dictionaries.
The input is a ROBOT template with the usual IHCC data dictionary. This dictionary is augmented with
Suggested mappings, which are added the 'Suggested Mappings' column of the template.
author: Nico Matentzoglu for Knocean Inc., 26 August 2020
"""

import pandas as pd
from argparse import ArgumentParser


class QCReport:
    """docstring for ClassName"""

    def __init__(self):
        self.errors = []

    def get_errors(self):
        return self.errors


qc_report = QCReport()
parser = ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("-vv", "--very-verbose", action="store_true")
parser.add_argument(
    "-t",
    "--templates",
    nargs="+",
    dest="templates",
    help="Space separated list of files",
    metavar="FILE",
)
parser.add_argument("-o", "--output", dest="report_out_path", help="Output file", metavar="FILE")
args = parser.parse_args()

df = pd.concat([pd.read_csv(f, sep="\t") for f in args.templates])

duplicated = df[df.duplicated(["Term ID"], keep=False)]
if len(duplicated) > 0:
    print("ERROR: There are templates with duplicate ids: %s" % str(duplicated))
    # raise QCError("There are templates with duplicate ids: %s" % str(duplicated))


ID_COLUMN = "Term ID"
GECKO_COLUMN = "GECKO Category"
SUGGESTED_COLUMN = "Suggested Categories"
CERTAIN_MAPPING = 0.65
df_mappings = df[[ID_COLUMN, GECKO_COLUMN]].copy()
df_suggestions = df[[ID_COLUMN, SUGGESTED_COLUMN]].copy()

df_mappings.dropna(inplace=True)
df_suggestions.dropna(inplace=True)

data = []
for term in df_mappings[ID_COLUMN].unique().tolist():
    dft = df_mappings[df_mappings[ID_COLUMN] == term]
    for mapping in dft[GECKO_COLUMN].unique().tolist():
        for m in mapping.split("|"):
            data.append([term, m.strip()])
df_mappings = pd.DataFrame(data, columns=['term', 'mapping'])

data = []
for term in df_suggestions[ID_COLUMN].unique().tolist():
    dft = df_suggestions[df_suggestions[ID_COLUMN] == term]
    for mapping in dft[SUGGESTED_COLUMN].unique().tolist():
        for m in mapping.split("|"):
            m = m.strip()
            mp = " ".join([x.strip() for x in m.split(" ")][2:])
            conf = float(m.split(" ")[0])
            if conf >= CERTAIN_MAPPING:
                data.append([term, mp])

df_suggestions = pd.DataFrame(data, columns=['term', 'suggestion'])


vec_mappings = df_mappings['term'] + "-" + df_mappings['mapping']
vec_mappings = set(vec_mappings.tolist())

vec_suggestions = df_suggestions['term'] + "-" + df_suggestions['suggestion']
vec_suggestions = set(vec_suggestions.tolist())

vec_mappings_not_suggestions = vec_mappings - vec_suggestions
vec_suggestions_not_mappings = vec_suggestions - vec_mappings

print("Strong suggestions that have not been mapped: %d" % len(vec_suggestions_not_mappings))
for e in vec_suggestions_not_mappings:
    print(e)

print("Actual mappings that have not been suggested sufficiently strongly %d" % len(vec_mappings_not_suggestions))
for e in vec_mappings_not_suggestions:
    print(e)
