#!/usr/bin/env python

"""
This script updates the zooma-annotation-dao.xml in the loaders directory with content curated in the ols-config.yaml.
author: Nico Matentzoglu for Knocean Inc., 26 August 2020
"""


import yaml
from argparse import ArgumentParser
from rdflib import Graph
import pandas as pd

parser = ArgumentParser()
parser.add_argument(
    "-m",
    "--metadata-turtle",
    action="append",
    dest="metadata_files",
    help="The set of data dictionary metadata files.",
)
parser.add_argument(
    "-o", "--output", dest="ols_config_path", help="OLS config file", metavar="FILE"
)
args = parser.parse_args()


g = Graph()

for f in args.metadata_files:
    print(f)
    g.parse(f, format="ttl")

qres = g.query(
    """SELECT DISTINCT ?title ?description ?license
       WHERE {
          ?a <http://purl.org/dc/terms/title> ?title .
          OPTIONAL {
            ?a <http://purl.org/dc/elements/1.1/description> ?description .
          }
          OPTIONAL {
            ?a <http://purl.org/dc/elements/1.1/license> ?license .
          }
       }""")

df = pd.DataFrame(qres, columns=qres.vars)
print(df.head())
data_dictionaries = []

for index, row in df.iterrows():
    dd = {'title': row['title']}
    if row['license']:
        dd['license'] = row['license']
    if row['description']:
        dd['description'] = row['description']
    data_dictionaries.append(dd)

with open(args.ols_config_path, 'w') as stream:
    try:
        ols_sources = yaml.safe_load(stream)
        ols_sources['ontologies'] = data_dictionaries
        yaml.safe_dump(ols_sources, stream)
    except yaml.YAMLError as exc:
        print(exc)

