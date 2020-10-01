#!/usr/bin/env python3

import csv
import os
import subprocess
import sys

from argparse import ArgumentParser


def main():
    p = ArgumentParser()
    p.add_argument("metadata")
    args = p.parse_args()

    cohort_id = None
    with open(args.metadata, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if row[0] == "Cohort ID":
                cohort_id = row[1].strip().lower()

    if not cohort_id:
        print("ERROR: No 'Cohort ID' found in metadata")
        sys.exit(1)

    # New files to add
    template = f"templates/{cohort_id}.tsv"
    if not os.path.exists(template):
        print(f"ERROR: '{template}' does not exists - run update task and try again")
        sys.exit(1)
    owl = f"data_dictionaries/{cohort_id}.owl"
    if not os.path.exists(owl):
        print(f"ERROR: '{template}' does not exists - run update task and try again")
        sys.exit(1)
    metadata = f"metadata/{cohort_id}.ttl"
    if not os.path.exists(metadata):
        print(f"ERROR: '{template}' does not exists - run update task and try again")
        sys.exit(1)

    for file in [
        template,
        owl,
        metadata,
        "data/cohort-data.json",
        "data/metadata.json",
        "src/prefixes.json",
    ]:
        print(f"Adding {file}...")
        subprocess.call(["git", "add", file], cwd=".")


if __name__ == "__main__":
    main()
