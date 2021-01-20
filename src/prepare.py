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

# Available datatypes
datatypes = [
    "Biospecimens",
    "EHR Data",
    "Environmental Data",
    "Genomic Data",
    "Longitudial Data",
    "Phenotypic/Clinical Data",
]


def get_bool(val):
    if val.lower() == "true":
        return True
    return False


def get_int(val):
    try:
        return int(val)
    except:
        return None


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
        "active_recruitment": False,
        "available_data_types": {
            "biospecimens": False,
            "ehr_data": False,
            "environmental_data": False,
            "genomic_data": False,
            "longitudial_data": False,
            "phenotypic_clinical_data": False,
        },
        "cohort_name": None,
        "countries": None,
        "current_enrollment": None,
        "enrollment_period": None,
        "includes_50_to_60": False,
        "irb_approved_data_sharing": False,
        "pi_lead": None,
        "recontact_in_place": False,
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

            # Identifiers
            if key == "Cohort ID":
                cohort_id = val
                ontology_iri = f"https://purl.ihccglobal.org/{cohort_id.lower()}.owl"
                gout.add((URIRef(ontology_iri), RDF.type, OWL.Ontology))
            elif key == "Cohort Name":
                d["cohort_name"] = val
                gout.add(
                    (URIRef(ontology_iri), URIRef("http://purl.org/dc/terms/title"), Literal(val))
                )

            # Main metadata
            elif key in props:
                prop = props[key]
                gout.add((URIRef(ontology_iri), URIRef(prop), Literal(val)))
            elif key == "Countries":
                d["countries"] = val.split(", ")
            elif key == "Data Sharing":
                d["irb_approved_data_sharing"] = get_bool(val)

            # Enrollment
            elif key == "Total Enrollment":
                d["current_enrollment"] = get_int(val)
            elif key == "Target Enrollment":
                d["target_enrollment"] = get_int(val)
            elif key == "Enrollment Start Year":
                enroll_start = get_int(val)
            elif key == "Enrollment End Year":
                enroll_end = get_int(val)
            elif key == "Actively Recruiting":
                d["active_recruitment"] = get_bool(val)
            elif key == "Includes 50-60 y/o":
                d["includes_50_to_60"] = get_bool(val)
            elif key == "Can Recontact Participants":
                d["recontact_in_place"] = get_bool(val)

            # Datatypes
            elif key in datatypes:
                dt_key = key.lower().replace(" ", "_").replace("/", "_")
                d["available_datatypes"][dt_key] = get_bool(val)

            # Other
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
