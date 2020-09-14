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
from lib import load_ihcc_config, map_term

class QCReport:
    """docstring for ClassName"""

    def __init__(self):
        self.errors = []
    
    def get_errors():
        return self.errors

qc_report = QCReport()
parser = ArgumentParser()
parser.add_argument('-v', '--verbose', action='store_true')
parser.add_argument('-vv', '--very-verbose', action='store_true')
parser.add_argument("-t", "--templates", nargs="+", dest="templates",
                    help="Space separated list of files", metavar="FILE")
parser.add_argument("-o", "--output", dest="report_out_path",
                    help="Output file", metavar="FILE")
args = parser.parse_args()

df = pd.concat([pd.read_csv(f) for f in datasets])
df.head()

## Two checks: 
### 1) does the primary recommendation correspond to the mappings?
### 2) Are their two terms that have the exact same label and map to different terms?

## Save template
#with open(args.tsv_out_path,'w') as write_csv:
#    write_csv.write(dfx.to_csv(sep='\t', index=False))

if qc_report.get_errors():
    print("WARNING: For some data dictionaries, the mapping recommendation now differs from the orginal mapping! See %s" % report_out_path)
else:
    print("All existing mappings appear to be mapped according to the current recommendation!")
