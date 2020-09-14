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
from argparse import ArgumentParser
import csv
# Library code
from lib import generate_zooma_dataset


parser = ArgumentParser()
parser.add_argument("-c", "--config", dest="config_file",
                    help="Config file", metavar="FILE")
parser.add_argument("-l", "--lexicaldata", nargs="+", dest="datasets",
                    help="Space seperated list of datasets containing labels and synonyms and their corresponding GECKO term.", metavar="FILE")
parser.add_argument("-z", "--zoomadata", dest="zooma_dataset",
                    help="Output file", metavar="FILE")
args = parser.parse_args()

## Loading all label data from data dictionaries (and GECKO)
df = pd.concat([pd.read_csv(f) for f in datasets])
df.head()

## Building the Zooma dataset from lexical data
df_basic_out, df_simplestring_out = generate_zooma_dataset(df)

## Saving the Zooma dataset
df_simplestring_out.drop_duplicates().to_csv(zooma_dataset,index=False, sep="\t", quoting=csv.QUOTE_NONE, escapechar="\\")

