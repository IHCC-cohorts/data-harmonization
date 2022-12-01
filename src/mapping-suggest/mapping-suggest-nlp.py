#!/usr/bin/env python
# coding: utf-8

"""
This script uses a mix of IHCC services to generate mapping suggestions for data dictionaries.
The input is a ROBOT template with the usual IHCC data dictionary. This dictionary is augmented with
Suggested mappings, which are added the 'Suggested Mappings' column of the template.
author: Nico Matentzoglu for Knocean Inc., 15 September 2020
"""
import sys

import pandas as pd
from argparse import ArgumentParser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import MinMaxScaler

from lib import ihcc_purl_prefix, obo_purl, load_ihcc_config, clean_terms, remove_hierarchy_terms, DictionaryMappingHelper


parser = ArgumentParser()
# parser.add_argument("-c", "--config", dest="config_file", help="Config file", metavar="FILE")
parser.add_argument(
    "-z",
    "--zooma-data-file",
    dest="training_data_file",
    help="Zooma dataset that can be used as training data",
    metavar="FILE",
)
parser.add_argument("-t", "--template", dest="template_file", help="Template file", metavar="FILE")
parser.add_argument("-c", "--config", dest="config_file", help="Config file", metavar="FILE")
parser.add_argument(
    "-g", "--gecko", dest="gecko_labels_file", help="File containing GECKO labels", metavar="FILE"
)
parser.add_argument("-p", "--preprocess", dest="preprocess", help="preprocess and clean labels", metavar="FILE")
parser.add_argument(
    "-o",
    "--output",
    dest="prediction_results_file",
    help="Output file for the prediction results",
    metavar="FILE",
)
args = parser.parse_args()

# Loading and preprocessing data
rdfs_label = "http://www.w3.org/2000/01/rdf-schema#label"
config = load_ihcc_config(args.config_file)
min_match_probability = 0.1
if "min_match_probability" in config:
    min_match_probability = config["min_match_probability"]
zooma = pd.read_csv(args.training_data_file, sep="\t")
gecko = pd.read_csv(args.gecko_labels_file, sep=",")
gecko_labels = gecko[gecko["property"] == rdfs_label][["from", "label"]]
gecko = gecko[["from", "label"]]

template = pd.read_csv(args.template_file, sep="\t")
# template['IRI'] = ["https://purl.ihccglobal.org/"+str(item).replace(":","_")
# for item in template['Term ID']]


# Creating training data
def preprocess_term_label(term):
    # use this for adding any kind of string processing you think is useful
    return term


X = zooma["PROPERTY_VALUE"].tolist()
y = zooma["SEMANTIC_TAG"].tolist()
X.extend(gecko["label"].tolist())
y.extend(gecko["from"].tolist())
X = [preprocess_term_label(term) for term in X]

raw_data = pd.DataFrame({"X": X, "y": y})
training_data = raw_data.drop_duplicates()

# As input, we only allow terms that already have valid IDs.
template_data = template[["Term ID", "Label"]].dropna().copy()
# Next: reduce the template data to rows that actually contain
# term data (ignoring empty or header rows)
template_data = template_data[template_data["Term ID"].str.match(r"[a-zA-z]+[:].*", case=False)]

# Building a TFIDF matrix for the training data
tfidf_vect = TfidfVectorizer(ngram_range=(1, 2), min_df=2).fit(training_data["X"])
X_tfidf = tfidf_vect.transform(training_data["X"])

# Building a TFIDF matrix for the template data
print(template_data.head(5))
if args.preprocess == "WORD_BOUNDARY":
    X_template_tfidf = tfidf_vect.transform(clean_terms(template_data["Label"]))
elif args.preprocess == "HIERARCHY":
    X_template_tfidf = tfidf_vect.transform(remove_hierarchy_terms(template_data["Label"]))
elif args.preprocess == "DEFINITION":
    template['Definition'].fillna(template['Label'], inplace=True)
    definition_mapper = DictionaryMappingHelper(template)
    X_template_tfidf = tfidf_vect.transform(definition_mapper.get_mappings(template_data["Label"]))
else:
    X_template_tfidf = tfidf_vect.transform(template_data["Label"])

# Training the model
clf_lr = SGDClassifier(loss="log").fit(X_tfidf, training_data["y"])

# Getting the probabilistic matches from the input data
probs_lr = clf_lr.predict_proba(X_template_tfidf)

# Finalising the matches into an IHCC matches dataframe
scale_low = 0
scale_high = 0.95
if "rescale_nlp_matches" in config:
    if "low" in config["rescale_nlp_matches"]:
        scale_low = config["rescale_nlp_matches"]["low"]
    if "high" in config["rescale_nlp_matches"]:
        scale_high = config["rescale_nlp_matches"]["high"]
scaler = MinMaxScaler(feature_range=(scale_low, scale_high))
df_test_probs = pd.DataFrame(probs_lr, columns=clf_lr.classes_)
df_test_probs["term"] = template_data["Label"].tolist()
m = pd.melt(df_test_probs, id_vars=["term"], var_name="match", value_name="confidence")
m["confidence"] = scaler.fit_transform(m[["confidence"]])
m = m[m["confidence"] > min_match_probability]

# Merging GECKO labels back in
df_out = pd.merge(m, gecko_labels, how="left", left_on=["match"], right_on=["from"])
df_out.rename({"label": "match_label"}, axis=1, inplace=True)
df_out = df_out.fillna('-')
df_out["match"] = [
    str(item).replace(obo_purl, "").replace(ihcc_purl_prefix, "").replace("_", ":")
    for item in df_out["match"]
]
del df_out["from"]

if len(df_out) > 0:
    print("NLP matching successful. First twenty results:")
    print(df_out[["term", "match", "confidence"]].head(20))
else:
    print("WARNING: NLP matching did not yield any results at all")

# Save template
with open(args.prediction_results_file, "w") as write_csv:
    write_csv.write(df_out.to_csv(sep="\t", index=False))
