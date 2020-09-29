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
from lib import QCError, top_suggestion


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
print(df.head())
print(df.describe())

duplicated = df[df.duplicated(['Term ID'], keep=False)]
if len(duplicated) > 0:
    pass
    print("ERROR: There are templates with duplicate ids: %s" % str(duplicated))
    # raise QCError("There are templates with duplicate ids: %s" % str(duplicated))

df["Top Suggestion"] = [
    top_suggestion(suggestions) for suggestions in df["Suggested Categories"]
]

print(len(df))
df_wrong_matches = df[df['Top Suggestion'] != df['GECKO Category']]
print(len(df_wrong_matches))
df_wrong_matches.to_csv("QC.tsv", sep="\t", index=False)
print(df_wrong_matches[['Term ID', 'GECKO Category', 'Top Suggestion']].head())

# Two checks:
# 1) does the primary recommendation correspond to the mappings?
# 2) Are their two terms that have the exact same label and map to different terms?

# Save template
# with open(args.tsv_out_path,'w') as write_csv:
#    write_csv.write(dfx.to_csv(sep='\t', index=False))

if qc_report.get_errors():
    warn = "WARNING: For some data dictionaries, the mapping recommendation now differs \
        from the orginal mapping! See %s"
    print(warn % args.report_out_path)
else:
    print("All existing mappings appear to be mapped according to the current recommendation!")
