#!/usr/bin/env python
# coding: utf-8

"""
Library of functions for the IHCC data dictionary mapping pipeline
"""

import os
import yaml
import json
import re
from datetime import datetime
import pandas as pd
import urllib.request
import urllib.parse
from sklearn.metrics import f1_score
from sklearn.metrics import accuracy_score


obo_purl = "http://purl.obolibrary.org/obo/"
ihcc_purl_prefix = "https://purl.ihccglobal.org/"


def generate_zooma_dataset(df):
    zooma_file_basic = []
    zooma_file_simplestring = []
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for index, row in df.iterrows():
        from_e = row["from"]
        to_e = obo_id_to_iri(row["to"])
        # propertyE = row['property']
        label = process_label(row["label"])
        zooma_file_basic.append(
            ["IHCC Basic", from_e, "information_entity", label, to_e, "Knocean", current_date]
        )
        zooma_file_simplestring.append(
            [
                "IHCC Simple String",
                from_e,
                "information_entity",
                label,
                to_e,
                "Knocean",
                current_date,
            ]
        )
        string_variants = compute_string_variants(label)
        for string_variant in string_variants:
            zooma_file_simplestring.append(
                [
                    "IHCC Simple String",
                    from_e,
                    "information_entity",
                    string_variant,
                    to_e,
                    "Knocean",
                    current_date,
                ]
            )
    columns = [
        "STUDY",
        "BIOENTITY",
        "PROPERTY_TYPE",
        "PROPERTY_VALUE",
        "SEMANTIC_TAG",
        "ANNOTATOR",
        "ANNOTATION_DATE",
    ]
    df_basic_out = pd.DataFrame(zooma_file_basic, columns=columns)
    df_simplestring_out = pd.DataFrame(zooma_file_simplestring, columns=columns)
    return df_basic_out, df_simplestring_out


def obo_id_to_iri(obo_id):
    if isinstance(obo_id, str):
        if obo_id.startswith(obo_purl):
            return obo_id
        elif ":" in obo_id:
            return obo_purl + obo_id.replace(":", "_")
    else:
        print("Warning, " + str(obo_id) + " is no string!")
    return obo_id


def compute_string_variants(label):
    label_alpha = re.sub(r"[^0-9a-zA-Z ]+", " ", label)
    label_alpha = re.sub(r"\s+", " ", label_alpha)
    label_split_numerics_alpha = re.sub(r"(?<=\d)(?!\d)|(?<!\d)(?=\d)", " ", label_alpha)
    label_split_numerics_alpha_camel = re.sub(
        r"([a-z])([A-Z])", r"\g<1> \g<2>", label_split_numerics_alpha
    )
    # label_split_numerics_alpha = re.sub(r'\s+', ' ', label_split_numerics_alpha)
    label_split_numerics_alpha_camel = re.sub(r"\s+", " ", label_split_numerics_alpha_camel)
    # label_split_numerics = re.sub('(?<=\d)(?!\d)|(?<!\d)(?=\d)', ' ', label)
    # label_split_numerics = re.sub('\s+', ' ', label_split_numerics)
    return [label_split_numerics_alpha_camel]


def process_label(label):
    return re.sub(r"\s+", " ", label)


def load_ihcc_config(config_file):
    config = {}
    with open(config_file, "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return config


def get_json_from_url(api, query):
    # print("API: "+api+query)
    q = ""
    try:
        q = api + urllib.parse.quote(query)
        with urllib.request.urlopen(q) as url:
            data = json.loads(url.read().decode())
        return data
    except Exception:
        raise FailedWebServiceCallError(f"Problem with API: {q}")


def get_label(curie, ols_oboid):
    label = ""
    data = parse_ols_first(get_json_from_url(ols_oboid, curie), ["iri", "label"], ols_oboid)
    if data:
        if "label" in data:
            label = data["label"]
    return label


def parse_ols_first(json_data, fields, ols_oboid):
    data = {}
    if "_embedded" in json_data:
        if "terms" in json_data["_embedded"]:
            for term in json_data["_embedded"]["terms"]:
                if "iri" in term and "iri" in fields:
                    data["iri"] = term["iri"]
                if "obo_id" in term and "curie" in fields:
                    data["curie"] = term["obo_id"]
                if "label" in term and "label" in fields:
                    data["label"] = term["label"]
                if "annotation" in term:
                    if (
                        "database_cross_reference" in term["annotation"]
                        and "database_cross_reference" in fields
                    ):
                        data["database_cross_reference"] = []
                        for xref_curie in term["annotation"]["database_cross_reference"]:
                            xref_data = parse_ols_first(
                                get_json_from_url(ols_oboid, xref_curie),
                                ["iri", "curie"],
                                ols_oboid,
                            )
                            if xref_data:
                                curie = xref_data["curie"]
                                if not xref_data["iri"].startswith(ihcc_purl_prefix):
                                    data["database_cross_reference"].append(curie)
                break
    return data


def map_term(term, zooma_annotate, ols_term, ols_oboid, confidence_map):
    matches = []
    data = get_json_from_url(zooma_annotate, term)
    for match in data:
        match_iris = match["semanticTags"]
        confidence = match["confidence"]
        for match_iri in match_iris:
            term_xrefs = parse_ols_first(
                get_json_from_url(ols_term, match_iri),
                ["curie", "iri", "database_cross_reference"],
                ols_oboid,
            )
            if term_xrefs and "curie" in term_xrefs and not match_iri.startswith(ihcc_purl_prefix):
                matches.append(
                    [
                        term,
                        term_xrefs["curie"],
                        get_label(term_xrefs["curie"], ols_oboid),
                        confidence,
                    ]
                )
            # sometimes the parent has the xref, not the term itself
            if term_xrefs and "database_cross_reference" in term_xrefs:
                for term_xref in term_xrefs["database_cross_reference"]:
                    xrefconfidence = confidence_map.index(confidence)
                    if xrefconfidence < 3:
                        matches.append(
                            [
                                term,
                                term_xref,
                                get_label(term_xref, ols_oboid),
                                confidence_map[xrefconfidence + 1],
                            ]
                        )
    return matches


def print_accuracy_results(y_test, y_pred):
    acc = accuracy_score(y_test, y_pred)
    print("Overall accuracy : " + str(acc))
    f1_micro = f1_score(y_test, y_pred, average="micro")
    f1_macro = f1_score(y_test, y_pred, average="macro")
    f1_all = f1_score(y_test, y_pred, average=None)

    print("F1 micro : " + str(f1_micro))
    print("F1 macro : " + str(f1_macro))
    print("F1 for each class : " + str(f1_all))


def format_suggestions(suggestions):
    if not isinstance(suggestions, str):
        return ""
    if not (len(suggestions) > 4):
        # There have to be at least 5 characters even in the
        # most conservative of assumptions: '0 A A'
        print("WARNING: %s is not a valid suggestion and will be removed!" % suggestions)
        return ""
    splitted = sorted([x.strip() for x in suggestions.split("|")], reverse=True)
    covered = []
    filtered = []
    for suggestion in splitted:
        mapping = [x.strip() for x in suggestion.split(" ")][1]
        # print(mapping)
        if mapping not in covered:
            filtered.append(suggestion)
            covered.append(mapping)
    return " | ".join(filtered).strip()


def top_suggestion(suggestions):
    if not isinstance(suggestions, str):
        return ""
    if not (len(suggestions) > 4):
        # There have to be at least 5 characters even in the
        # most conservative of assumptions: '0 A A'
        print("WARNING: %s is not a valid suggestion and will be removed!" % suggestions)
        return ""
    splitted = sorted([x.strip() for x in suggestions.split("|")], reverse=True)
    if splitted:
        mapping = " ".join([x.strip() for x in splitted[0].split(" ")][2:])
        return mapping
    return ""


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


class Error(Exception):
    pass


class FailedWebServiceCallError(Error):
    pass


class QCError(Error):
    pass
