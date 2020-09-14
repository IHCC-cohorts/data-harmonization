#!/usr/bin/env python
# coding: utf-8

"""
Zooma allows the mapping of datasets. The mappings themselves can be configured: 
The idea here is that all existing mappings and some very simple syntactic derivations are loaded into Zooma, 
which can then be mapped with very high confidence when a new data dictionary tries to map the exact 
same (or very similar) term. In this notebook, we load all the (previously generated) lexical data of all 
existing data dictionaries (and GECKO) and generate a Zooma dataset file.

author: Nico Matentzoglu for Knocean Inc., 26 August 2020
"""

import pandas as pd
import sys, os
from argparse import ArgumentParser
import csv
# Library code
from lib import generate_zooma_dataset, dir_path


parser = ArgumentParser()
parser.add_argument("-w", "--workingdir", dest="working_dir",
                    help="The working directory of this script (default: script location)", type=dir_path, required=True)
parser.add_argument("-l", "--lexicaldata", action="append", dest="datasets",
                    help="Space seperated list of datasets containing labels and synonyms and their corresponding GECKO term.")
parser.add_argument("-o", "--output", dest="zooma_dataset",
                    help="The Zomma dataset output file", metavar="FILE", required=True)
args = parser.parse_args()

os.chdir(args.working_dir)

## Loading all label data from data dictionaries (and GECKO)
df = pd.concat([pd.read_csv(f) for f in args.datasets])
df.head()

## Building the Zooma dataset from lexical data
df_basic_out, df_simplestring_out = generate_zooma_dataset(df)

## Saving the Zooma dataset
df_simplestring_out.drop_duplicates().to_csv(args.zooma_dataset,index=False, sep="\t", quoting=csv.QUOTE_NONE, escapechar="\\")

