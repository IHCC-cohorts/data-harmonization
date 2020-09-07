#!/usr/bin/env python
# coding: utf-8

"""
Library of functions for the IHCC data dictionary mapping pipeline
"""

import os
import yaml
import json
import urllib.request, urllib.parse

def load_ihcc_config(config_file):
    config = {}
    with open(config_file, 'r') as stream:
        try:
            config=yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return config

def get_json_from_url(api,query):
    #print("API: "+api+query)
    data = {}
    try:
        q = api+urllib.parse.quote(query)
        with urllib.request.urlopen(q) as url:
            data = json.loads(url.read().decode())
    except:
        print("Problem with API: "+q)
    return data

def get_label(curie, ols_oboid):
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

def map_term(term, zooma_annotate, ols_term, ols_oboid):
    matches = []
    data = get_json_from_url(zooma_annotate,term)
    for match in data:
        match_iris = match['semanticTags']
        confidence = match['confidence']
        for match_iri in match_iris:
            term_xrefs = parse_ols_first(get_json_from_url(ols_term,match_iri),['curie','iri','database_cross_reference'])
            if term_xrefs and 'curie' in term_xrefs and not match_iri.startswith("https://purl.ihccglobal.org/"):
                matches.append([term,term_xrefs['curie'],get_label(term_xrefs['curie'], ols_oboid),confidence])
            # sometimes the parent has the xref, not the term itself
            if term_xrefs and 'database_cross_reference' in term_xrefs:
                for term_xref in term_xrefs['database_cross_reference']:
                    xrefconfidence = confidence_map.index(confidence)
                    if xrefconfidence<3:
                         matches.append([term,term_xref,get_label(term_xref, ols_oboid),confidence_map[xrefconfidence+1]])
    return matches