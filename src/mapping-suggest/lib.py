#!/usr/bin/env python
# coding: utf-8

"""
Library of functions for the IHCC data dictionary mapping pipeline
"""

import os
import yaml
import json
import csv
import re
from datetime import datetime
import pandas as pd
import urllib.request, urllib.parse
from sklearn.metrics import f1_score
from sklearn.metrics import accuracy_score


obo_purl="http://purl.obolibrary.org/obo/"


def generate_zooma_dataset(df):
    zooma_file_basic = []
    zooma_file_simplestring = [] 
    current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for index, row in df.iterrows():
        fromE = row['from']
        toE = obo_id_to_iri(row['to'])
        propertyE = row['property']
        label = process_label(row['label'])
        zooma_file_basic.append(["IHCC Basic",fromE,"information_entity",label,toE,"Knocean",current_date])
        zooma_file_simplestring.append(["IHCC Simple String",fromE,"information_entity",label,toE,"Knocean",current_date])
        string_variants = compute_string_variants(label)
        for string_variant in string_variants:
            zooma_file_simplestring.append(["IHCC Simple String",fromE,"information_entity",string_variant,toE,"Knocean",current_date])

    df_basic_out=pd.DataFrame(zooma_file_basic,columns=['STUDY','BIOENTITY','PROPERTY_TYPE','PROPERTY_VALUE','SEMANTIC_TAG','ANNOTATOR','ANNOTATION_DATE'])
    df_simplestring_out=pd.DataFrame(zooma_file_simplestring,columns=['STUDY','BIOENTITY','PROPERTY_TYPE','PROPERTY_VALUE','SEMANTIC_TAG','ANNOTATOR','ANNOTATION_DATE'])
    return df_basic_out, df_simplestring_out

def obo_id_to_iri(obo_id):
    if isinstance(obo_id,str):
        if obo_id.startswith(obo_purl):
            return obo_id
        elif ":" in obo_id:
            return obo_purl+obo_id.replace(":","_")
    else:
        print("Warning, "+str(obo_id)+" is no string!")
    return obo_id

def compute_string_variants(label):
    label_alpha = re.sub('[^0-9a-zA-Z ]+', ' ', label)
    label_alpha = re.sub('\s+', ' ', label_alpha)
    label_split_numerics_alpha = re.sub('(?<=\d)(?!\d)|(?<!\d)(?=\d)', ' ', label_alpha)
    label_split_numerics_alpha_camel = re.sub("([a-z])([A-Z])","\g<1> \g<2>",label_split_numerics_alpha)
    label_split_numerics_alpha = re.sub('\s+', ' ', label_split_numerics_alpha)
    label_split_numerics_alpha_camel = re.sub('\s+', ' ', label_split_numerics_alpha_camel)
    #label_split_numerics = re.sub('(?<=\d)(?!\d)|(?<!\d)(?=\d)', ' ', label)
    #label_split_numerics = re.sub('\s+', ' ', label_split_numerics)
    return [label_split_numerics_alpha_camel]

def process_label(label):
    return re.sub('\s+', ' ', label)

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
    
def print_accuracy_results(y_test,y_pred):
    acc = accuracy_score(y_test,y_pred)
    print('Overall accuracy : '+str(acc))
    f1_micro = f1_score(y_test, y_pred, average = 'micro')
    f1_macro = f1_score(y_test, y_pred, average = 'macro')
    f1_all = f1_score(y_test, y_pred, average = None)

    print('F1 micro : ' +str(f1_micro))
    print('F1 macro : ' +str(f1_macro))
    print('F1 for each class : ' +str(f1_all))
    

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)