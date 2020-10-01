#!/usr/bin/env python

import csv
import logging
import re

from argparse import ArgumentParser


def main():
    p = ArgumentParser()
    p.add_argument("table")
    p.add_argument("gecko_labels")
    p.add_argument("output")
    args = p.parse_args()

    gecko_labels = []
    with open(args.gecko_labels, "r") as f:
        next(f)
        for line in f:
            gecko_labels.append(line.strip())

    # Create the rows for the data-validation sheet
    dv_rows = []
    with open(args.table, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        row_num = 2
        for row in reader:
            # Copy of the GECKO labels that we can mess with
            gecko_copy = gecko_labels.copy()
            # NLP & Zooma suggested GECKO Categories
            suggested_cats = row["Suggested Categories"]

            # Parse suggested categories into a list
            cat_names = []
            for sc in suggested_cats.split(" | "):
                match = re.search(r"[^ ]+ [A-Z]+:[0-9]+ (.+)", sc)
                if match:
                    cat_names.append(match.group(1))

            # Then add them to the sheet
            if cat_names:
                # Add the rest of the allowed categories in after the suggested categories
                for cn in cat_names:
                    if cn not in gecko_copy:
                        logging.error(f"'{cn}' suggested on row {row_num} is not a GECKO term")
                    else:
                        gecko_copy.remove(cn)
                cat_names.extend(gecko_copy)
            else:
                # No suggested categories, add all the labels in alphabetical order
                cat_names = gecko_copy
            dv_rows.append(
                {
                    "table": "terminology",
                    "range": f"E{row_num}",
                    "condition": "ONE_OF_LIST",
                    "value": ", ".join(cat_names),
                }
            )
            row_num += 1

    # Write a data-validation sheet for `cogs apply`
    with open(args.output, "w") as f:
        writer = csv.DictWriter(
            f, delimiter="\t", fieldnames=["table", "range", "condition", "value"]
        )
        writer.writeheader()
        writer.writerows(dv_rows)


if __name__ == "__main__":
    main()
