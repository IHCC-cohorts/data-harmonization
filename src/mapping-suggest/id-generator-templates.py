#!/usr/bin/env python
# coding: utf-8

"""
This script loads a template file and fills in IDs in columns where they are missing
author: Nico Matentzoglu for Knocean Inc., 22 September 2020
"""

import pandas as pd
import numpy as np
from pathlib import Path
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument(
    "-t", "--template", dest="template_file", help="Template file", metavar="FILE", required=True
)
parser.add_argument(
    "-m",
    "--metadata-table",
    dest="metadata_table_path",
    help="Path to the IHCC metadata table",
    metavar="FILE",
)
parser.add_argument(
    "-l",
    "--length-id",
    dest="length_of_id",
    help="How many characters should your id by at most?",
    metavar="FILE",
    default=7,
)
args = parser.parse_args()

# Get the data dictionary id. If a metada data file is supplied,
# get it from there, else use the path to uppercase
if args.metadata_table_path:
    df = pd.read_csv(args.metadata_table_path, header=None, sep="\t")
    dd_id = df[df.iloc[:, 0] == "Cohort ID"].iloc[:, 1].iloc[0]
else:
    dd_id = Path(args.template_file).stem
    dd_id = dd_id.upper()

print("Generating IDs for data dictionary: %s" % dd_id)
NUM_PADDED_ZERO = args.length_of_id
MAX_ID = int("9" * NUM_PADDED_ZERO)
PREFIX = "%s:" % dd_id
COL_TERM_ID = "Term ID"
COL_LABEL = "Label"

df = pd.read_csv(args.template_file, sep="\t", dtype=str)
len_pre = len(df)

highest_current_id = 0

if COL_TERM_ID in df.columns:
    df_nn = df[df[COL_TERM_ID].notnull()]
    ids = df_nn[df_nn[COL_TERM_ID].str.startswith(PREFIX)][COL_TERM_ID].tolist()
    ids = [i.replace(PREFIX, "") for i in ids]
    ids_int = [int(i) for i in ids if i.isdigit()]
    if ids_int:
        highest_current_id = max(ids_int)
else:
    df[COL_TERM_ID] = ""


for index, row in df.iterrows():
    value = row[COL_TERM_ID]
    if row[COL_LABEL] or (value.dtype == float and not np.isnan(value)):
        print(str(value) + " " + str(row[COL_LABEL]))
        if (type(value) != str) or (not value.startswith(PREFIX)):
            highest_current_id = highest_current_id + 1
            if highest_current_id > MAX_ID:
                raise RuntimeError(
                    "The maximum number of digits is exhausted (%d), "
                    + "you need to pick a larger range!" % NUM_PADDED_ZERO
                )
            highest_current_id_str = str(highest_current_id)
            df.at[index, COL_TERM_ID] = "%s%s" % (
                PREFIX,
                highest_current_id_str.zfill(NUM_PADDED_ZERO),
            )

if len_pre != len(df):
    raise RuntimeError(
        "The size of the dictionary changed " + "during the process - something went wrong (KTD)."
    )

# Save template
with open(args.template_file, "w") as write_csv:
    write_csv.write(df.to_csv(sep="\t", index=False))
