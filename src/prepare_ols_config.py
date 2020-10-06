#!/usr/bin/env python

"""
This script updates the zooma-annotation-dao.xml in the loaders directory with content curated in the ols-config.yaml.
author: Nico Matentzoglu for Knocean Inc., 26 August 2020
"""


import yaml
from argparse import ArgumentParser
from rdflib import Graph
from pathlib import Path
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


query_results = []

for f in args.metadata_files:
    g = Graph()
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

    columns = [str(v) for v in qres.vars]
    df = pd.DataFrame(qres, columns=columns)
    df['id'] = Path(f).stem
    query_results.append(df)

df = pd.concat(query_results)

data_dictionaries = []

for index, row in df.iterrows():
    did = str(row['id'])
    dpurl = f"https://raw.githubusercontent.com/IHCC-cohorts/data-harmonization/master/data_dictionaries/{did}.owl"
    base_uri = "https://purl.ihccglobal.org/%s_" % did.upper()
    dd = {'id': did, 'title': row['title'].toPython(),
          'preferredPrefix': did.upper(),
          'ontology_purl': dpurl,
          'base_uri': [base_uri]}
    if row['license']:
        dd['license'] = row['license'].toPython()
    if row['description']:
        dd['description'] = row['description'].toPython()
    data_dictionaries.append(dd)

with open(args.ols_config_path, "r") as f:
    ols_sources = yaml.safe_load(f)

ols_sources['ontologies'] = data_dictionaries

with open(args.ols_config_path, "w") as f:
    yaml.safe_dump(ols_sources, f)

print("Preparing OLS config successful")