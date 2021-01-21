import csv
import json
import logging
import sys

from argparse import ArgumentParser
from rdflib import Graph, Literal, OWL, RDF, URIRef


# Prepare the newly added cohort for building by doing the following:
# - create metadata/[cohort_id].ttl file from build/metadata.tsv
# - create templates/[cohort_id].tsv from build/terminology.tsv
# - add [COHORT_ID] to src/prefixes.json
# - add [COHORT_ID] and metadata to data/metadata.json


# Metadata keywords to property IRIs
props = {
    "Description": "http://purl.org/dc/elements/1.1/description",
    "License": "http://purl.org/dc/terms/license",
    "Rights": "http://purl.org/dc/terms/rights",
}

datatypes = ["Biospecimens", "Environmental Data", "Genomic Data", "Phenotypic/Clinical Data"]


def main():
    p = ArgumentParser()
    # The metadata tab of the registration template
    p.add_argument("cohort_metadata")
    # The terminology tab of the registration template
    p.add_argument("terminology")
    # The JSON prefixes data for all cohorts
    p.add_argument("prefixes")
    # The JSON metadata for all cohorts (the file that will be updated)
    p.add_argument("all_metadata")
    args = p.parse_args()

    # Create a graph for the TTL metadata (title, description, license, rights)
    gout = Graph()
    gout.bind("dcterms", "http://purl.org/dc/terms/")
    gout.bind("dc", "http://purl.org/dc/elements/1.1/")
    gout.bind("owl", OWL)

    cohort_id = None
    ontology_iri = None

    # Cohort metadata dictionary
    d = {
        "available_data_types": {
            "biospecimens": False,
            "environmental_data": False,
            "genomic_data": False,
            "phenotypic_clinical_data": False,
        },
        "cohort_name": None,
        "countries": None,
        "current_enrollment": None,
        "enrollment_period": None,
        "irb_approved_data_sharing": False,
        "pi_lead": None,
        "target_enrollment": None,
        "website": None,
    }

    enroll_start = None
    enroll_end = None
    with open(args.cohort_metadata, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        idx = 1
        for row in reader:
            key = row[0]
            val = row[1].strip()
            if not val or key == "Available Datatypes":
                continue
            if key == "Cohort ID":
                cohort_id = val
                ontology_iri = f"https://purl.ihccglobal.org/{cohort_id.lower()}.owl"
                gout.add((URIRef(ontology_iri), RDF.type, OWL.Ontology))
            elif key == "Cohort Name":
                d["cohort_name"] = val
                gout.add(
                    (URIRef(ontology_iri), URIRef("http://purl.org/dc/terms/title"), Literal(val))
                )
            elif key in props:
                prop = props[key]
                gout.add((URIRef(ontology_iri), URIRef(prop), Literal(val)))
            elif key == "Total Enrollment":
                d["current_enrollment"] = int(val)
            elif key == "Target Enrollment":
                d["target_enrollment"] = int(val)
            elif key == "Enrollment Start Year":
                enroll_start = int(val)
            elif key == "Enrollment End Year":
                enroll_end = int(val)
            elif key in datatypes:
                bool_val = False
                if val.lower() == "true":
                    bool_val = True
                dt_key = key.lower().replace(" ", "_").replace("/", "_")
                d["available_data_types"][dt_key] = bool_val
            elif key == "Countries":
                d["countries"] = val.split(", ")
            elif key == "Data Sharing":
                bool_val = False
                if val.lower() == "true":
                    bool_val = True
                d["irb_approved_data_sharing"] = bool_val
            else:
                key_fixed = key.lower().replace(" ", "_").replace("/", "_")
                if key_fixed not in d:
                    print(f"Unknown key on line {idx}: {key}")
                    sys.exit(1)
                d[key_fixed] = val
            idx += 1

    if enroll_start and enroll_end:
        d["enrollment_period"] = f"{enroll_start}:{enroll_end}"
    else:
        d["enrollment_period"] = f"{enroll_start}:Ongoing"

    # Save metadata ttl
    gout.serialize(f"metadata/{cohort_id.lower()}.ttl", format="turtle")

    # Add a prefix for this cohort
    with open(args.prefixes, "r") as f:
        prefixes = json.load(f)
    prefixes["@context"][cohort_id] = f"https://purl.ihccglobal.org/{cohort_id}_"
    with open(args.prefixes, "w") as f:
        f.write(json.dumps(prefixes, indent=4, sort_keys=True))

    # Add cohort details to data/metadata.json
    with open(args.all_metadata, "r") as f:
        metadata = json.load(f)
    metadata[cohort_id] = d
    with open(args.all_metadata, "w") as f:
        f.write(json.dumps(metadata, indent=4, sort_keys=True))

    # Remove Suggested Categories from template and save
    rows = []
    headers = []
    with open(args.terminology, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = reader.fieldnames
        for row in reader:
            if "Suggested Categories" in row:
                del row["Suggested Categories"]
            rows.append(row)
    with open(f"templates/{cohort_id.lower()}.tsv", "w") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
