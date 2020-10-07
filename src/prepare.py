import csv
import json
import logging
import shutil
import sys

from argparse import ArgumentParser
from rdflib import Graph, Literal, OWL, RDF, URIRef
import pandas as pd


# Perpare the newly added cohort for building by doing the following:
# - create metadata/[cohort_id].ttl file from build/metadata.tsv
# - create templates/[cohort_id].tsv from build/terminology.tsv
# - add [COHORT_ID] to src/prefixes.json


# Metadata keywords to property IRIs
props = {
    "Title": "http://purl.org/dc/terms/title",
    "Description": "http://purl.org/dc/elements/1.1/description",
    "License": "http://purl.org/dc/terms/license",
    "Rights": "http://purl.org/dc/terms/rights",
}


def main():
    p = ArgumentParser()
    p.add_argument("cohort_metadata")
    p.add_argument("terminology")
    p.add_argument("prefixes")
    p.add_argument("all_metadata")
    args = p.parse_args()

    # Create a graph to store the triples about the cohort
    gout = Graph()
    gout.bind("dcterms", "http://purl.org/dc/terms/")
    gout.bind("dc", "http://purl.org/dc/elements/1.1/")
    gout.bind("owl", OWL)

    # Parse the metadata file and add contents to the graph
    cohort_id = None
    ontology_iri = None
    title = None
    with open(args.cohort_metadata, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        idx = 1
        for row in reader:
            key = row[0]
            if key == "Cohort ID":
                cohort_id = row[1].lower().strip()
                ontology_iri = f"https://purl.ihccglobal.org/{cohort_id}.owl"
                gout.add((URIRef(ontology_iri), RDF.type, OWL.Ontology))
            elif key in props:
                if key == "Title":
                    title = row[1].strip()
                if not ontology_iri:
                    logging.critical("This sheet must define a 'Cohort ID' first")
                    sys.exit(1)
                prop = props[key]
                gout.add((URIRef(ontology_iri), URIRef(prop), Literal(row[1].strip())))
            else:
                logging.critical(f"Unknown key on line {idx}: {key}")
                sys.exit(1)
            idx += 1
    # Save metadata ttl
    gout.serialize(f"metadata/{cohort_id}.ttl", format="turtle")

    # Add a prefix for this cohort
    with open(args.prefixes, "r") as f:
        prefixes = json.load(f)
    prefix = cohort_id.upper()
    prefixes["@context"][prefix] = f"https://purl.ihccglobal.org/{prefix}_"
    with open(args.prefixes, "w") as f:
        f.write(json.dumps(prefixes, indent=4, sort_keys=True))

    # Add cohort details to data/metadata.json
    if not title:
        logging.error(
            "Cohort title is missing from the metadata sheet "
            "- this cohort will not appear in the index!"
        )
    else:
        with open(args.all_metadata, "r") as f:
            metadata = json.load(f)
        metadata[title] = {"id": prefix, "prefix": prefix, "data_dictionary": "", "mapping": ""}
        with open(args.all_metadata, "w") as f:
            f.write(json.dumps(metadata, indent=4, sort_keys=True))

    # Remove Suggested Categories from template and safe.
    df = pd.read_csv(args.terminology, sep="\t")
    df["Suggested Categories"] = ""
    df.to_csv(f"templates/{cohort_id}.tsv", sep="\t")


if __name__ == "__main__":
    main()
