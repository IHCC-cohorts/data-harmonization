#!/usr/bin/env python
# coding: utf-8

"""
This script uses a mix of IHCC services to generate mapping suggestions for data dictionaries.
The input is a ROBOT template with the usual IHCC data dictionary. This dictionary is augmented with
Suggested mappings, which are added the 'Suggested Mappings' column of the template.
author: Nico Matentzoglu for Knocean Inc., 26 August 2020
"""

import yaml, os
from xml.dom import minidom
import urllib.request, json, urllib.parse
import pandas as pd
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument("-c", "--config", dest="config_file",
                    help="Config file", metavar="FILE")
parser.add_argument("-t", "--template", dest="tsv_path",
                    help="Template file file", metavar="FILE")
parser.add_argument("-o", "--output", dest="tsv_out_path",
                    help="Output file", metavar="FILE")
args = parser.parse_args()

with open(args.config_file, 'r') as stream:
    try:
        config=yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

print(config)

zooma_annotate=config["zooma_annotate"]
oxo_mapping=config["oxo_mapping"]
ols_term=config["ols_term"]
ols_oboid=config["ols_oboid"]

confidence_map = ["HIGH", "GOOD", "MEDIUM", "LOW"] # These are the default confidence levels from Zooma


def get_json_from_url(api,query):
    #print("API: "+api+query)
    try:
        with urllib.request.urlopen(api+urllib.parse.quote(query)) as url:
            data = json.loads(url.read().decode())
    except:
        print("Problem with API: "+api+" and query "+query)
    return data

def get_label(curie):
    label=""
    data=parse_ols_first(get_json_from_url(ols_oboid,curie),['iri','label'])
    if data:
        if 'label' in data:
            label = data['label']
    return label

def parse_ols_first(json,fields):
    data = {}
    if '_embedded' in json:
        if 'terms' in json['_embedded']:
            for term in json['_embedded']['terms']:
                if 'iri' in term and 'iri' in fields:
                    data['iri']=term['iri']
                if 'obo_id' in term and 'curie' in fields:
                    data['curie']=term['obo_id']
                if 'label' in term and 'label' in fields:
                    data['label']=term['label']
                if 'annotation' in term:
                    if 'database_cross_reference' in term['annotation'] and 'database_cross_reference' in fields:
                        data['database_cross_reference']=[]
                        for xref_curie in term['annotation']['database_cross_reference']:
                            xref_data = parse_ols_first(get_json_from_url(ols_oboid,xref_curie),['iri','curie'])
                            if xref_data:
                                curie = xref_data['curie']
                                if not xref_data['iri'].startswith("https://purl.ihccglobal.org/"):
                                    data['database_cross_reference'].append(curie)
                break
    return data

def map_term(term):
    matches = []
    data = get_json_from_url(zooma_annotate,term)
    for match in data:
        match_iris = match['semanticTags']
        confidence = match['confidence']
        for match_iri in match_iris:
            term_xrefs = parse_ols_first(get_json_from_url(ols_term,match_iri),['curie','iri','database_cross_reference'])
            if term_xrefs and 'curie' in term_xrefs and not match_iri.startswith("https://purl.ihccglobal.org/"):
                matches.append([term,term_xrefs['curie'],get_label(term_xrefs['curie']),confidence])
            # sometimes the parent has the xref, not the term itself
            if term_xrefs and 'database_cross_reference' in term_xrefs:
                for term_xref in term_xrefs['database_cross_reference']:
                    xrefconfidence = confidence_map.index(confidence)
                    if xrefconfidence<3:
                         matches.append([term,term_xref,get_label(term_xref),confidence_map[xrefconfidence+1]])
    return matches




tsv=pd.read_csv(args.tsv_path,sep="\t")
del tsv['Suggested Categories']

tsv_terms=tsv['Label'].values[2:]

matches=[]

for term in tsv_terms:
    matches.extend(map_term(term))
                        
df=pd.DataFrame(matches,columns=['term','match','match_label','confidence'])
dfs=df[~df['match'].str.startswith("https://purl.ihccglobal.org/")].copy()
dfs['Suggested Categories']=dfs[['confidence', 'match', 'match_label']].agg(' '.join, axis=1)
dfs=dfs[['term','Suggested Categories']]
dfsagg=dfs.groupby('term', as_index=False).agg(lambda x: ' | '.join(set(x.dropna())))
dfx = pd.merge(tsv, dfsagg, how='left', left_on=['Label'], right_on=['term'])
del dfx['term']

with open(args.tsv_out_path,'w') as write_csv:
    write_csv.write(dfx.to_csv(sep='\t', index=False))

