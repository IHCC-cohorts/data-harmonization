#!/usr/bin/env python

import csv
import logging
import re

from argparse import ArgumentParser


def main():
    p = ArgumentParser()
    p.add_argument("table")
    p.add_argument("gecko_labels")
    p.add_argument("data_validation")
    p.add_argument("problem_table")
    args = p.parse_args()

    gecko_labels = []
    with open(args.gecko_labels, "r") as f:
        next(f)
        for line in f:
            gecko_labels.append(line.strip())
    gecko_labels = sorted(gecko_labels, key=str.casefold)

    # Create the rows for the data-validation sheet
    dv_rows = []
    updated_rows = []
    problem_rows = []
    rewrite_table = False
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
            auto_assigned = False
            for sc in suggested_cats.split(" | "):
                match = re.search(r"([^ ]+) [A-Z]+:[0-9]+ (.+)", sc)
                if match:
                    gecko_cat = match.group(2)
                    cat_names.append(gecko_cat)
                    score = float(match.group(1))
                    if score > 0.65 and not auto_assigned:
                        auto_assigned = True
                        rewrite_table = True
                        row["GECKO Category"] = gecko_cat
                        problem_rows.append(
                            {
                                "table": "Terminology",
                                "cell": f"E{row_num}",
                                "level": "INFO",
                                "rule ID": "automatically_assigned_category",
                                "rule": f"this is an automatically assigned category based on a score of {score}",
                            }
                        )
            updated_rows.append(row)

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
                    "table": "Terminology",
                    "range": f"E{row_num}",
                    "condition": "ONE_OF_LIST",
                    "value": ", ".join(cat_names),
                }
            )
            row_num += 1

    if rewrite_table:
        # Write updated rows (with top-scored categories)
        with open(args.table, "w") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "Term ID",
                    "Label",
                    "Parent Term",
                    "Definition",
                    "GECKO Category",
                    "Internal ID",
                    "Suggested Categories",
                    "Comment",
                ],
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(updated_rows)

    # Create a "problems table" to apply (not really a problem)
    # These are just the INFO messages for the auto-assigned categories
    with open(args.problem_table, "w") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "table",
                "cell",
                "level",
                "rule ID",
                "rule",
            ],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(problem_rows)

    # Write a data-validation sheet for `cogs apply`
    with open(args.data_validation, "w") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["table", "range", "condition", "value"],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(dv_rows)


if __name__ == "__main__":
    main()
