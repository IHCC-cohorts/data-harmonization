import collections
import csv
import logging
import os
import re
import sys

from argparse import ArgumentParser


expected_headers = [
    "Term ID",
    "Label",
    "Parent Term",
    "Definition",
    "GECKO Category",
    "Suggested Categories",
    "Comment",
]


def idx_to_a1(row, col):
    """Convert a row & column to A1 notation. Adapted from gspread.utils."""
    div = col
    column_label = ""

    while div:
        (div, mod) = divmod(div, 26)
        if mod == 0:
            mod = 26
            div -= 1
        column_label = chr(mod + 64) + column_label

    label = f"{column_label}{row}"
    return label


def validate(table, gecko_labels):
    """Validate an IHCC mapping table."""
    basename = os.path.splitext(os.path.basename(table))[0]
    problems = []
    problem_count = 0
    # label -> locs
    labels = {}
    # loc -> parent_term
    parent_terms = {}

    lines = []
    with open(table, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")

        # Validate headers
        headers = reader.fieldnames
        headers_valid = True
        col_idx = 0
        for h in headers:
            if col_idx < len(expected_headers):
                matching_header = expected_headers[col_idx]
                if h != matching_header:
                    headers_valid = False
                    problem_count += 1
                    problems.append(
                        {
                            "ID": problem_count,
                            "table": basename,
                            "cell": idx_to_a1(1, col_idx + 1),
                            "level": "error",
                            "rule ID": "",
                            "rule name": "Invalid header",
                            "value": h,
                            "fix": matching_header,
                            "instructions": f"This column should be '{matching_header}'",
                        }
                    )
            else:
                headers_valid = False
                problem_count += 1
                problems.append(
                    {
                        "ID": problem_count,
                        "table": basename,
                        "cell": idx_to_a1(1, col_idx + 1),
                        "level": "error",
                        "rule ID": "",
                        "rule name": "Invalid header",
                        "value": h,
                        "fix": "",
                        "instructions": f"This column should be empty",
                    }
                )
            col_idx += 1

        if not headers_valid:
            logging.critical(
                "Unable to complete validation - please fix the headers and try again!"
            )
            return None, problems

        # Validate contents
        row_idx = 2
        for row in reader:
            lines.append(row)

            # Validate that the term ID exists and matches a numeric pattern
            term_id = row["Term ID"]
            if not term_id or term_id.strip() == "":
                problem_count += 1
                problems.append(
                    {
                        "ID": problem_count,
                        "table": basename,
                        "cell": idx_to_a1(row_idx, 1),
                        "level": "error",
                        "rule ID": "",
                        "rule name": "Missing term ID",
                        "value": "",
                        "fix": "",
                        "instructions": "run the automated_mapping script to assign term IDs",
                    }
                )
            elif not re.match(r"[A-Z]+:[0-9]{7}", term_id):
                problem_count += 1
                problems.append(
                    {
                        "ID": problem_count,
                        "table": basename,
                        "cell": idx_to_a1(row_idx, 1),
                        "level": "error",
                        "rule ID": "",
                        "rule name": "Invalid term ID",
                        "value": term_id,
                        "fix": "",
                        "instructions": "the term ID must follow the pattern COHORT:num_id where "
                        "num_id has 7 digits (e.g., FOO:0000020)",
                    }
                )

            # Add label to labels map
            label = row["Label"]
            if label in labels:
                locs = labels[label]
            else:
                locs = []
            locs.append(idx_to_a1(row_idx, 2))
            labels[label] = locs

            # Add parent to parent_terms map
            parent_terms[idx_to_a1(row_idx, 3)] = row["Parent Term"].strip()

            # Check that GECKO category is valid
            gecko_cat = row["GECKO Category"].strip()
            if gecko_cat != "":
                for gc in gecko_cat.split("|"):
                    if gc not in gecko_labels:
                        problem_count += 1
                        problems.append(
                            {
                                "ID": problem_count,
                                "table": basename,
                                "cell": idx_to_a1(row_idx, 5),
                                "level": "error",
                                "rule ID": "",
                                "rule name": "Invalid GECKO category",
                                "value": gecko_cat,
                                "fix": "",
                                "instructions": "select a valid GECKO category",
                            }
                        )
            row_idx += 1

    # Validate labels
    duplicates = {k: v for k, v in labels.items() if len(v) > 1}
    if duplicates:
        for label, locs in duplicates.items():
            for loc in locs:
                problem_count += 1
                other_locs = ", ".join([x for x in locs if x != loc])
                problems.append(
                    {
                        "ID": problem_count,
                        "table": basename,
                        "cell": loc,
                        "level": "error",
                        "rule ID": "",
                        "rule name": "Duplicate label",
                        "value": label,
                        "fix": "",
                        "instructions": f"update this label & label(s) in cell(s): {other_locs}",
                    }
                )

    # Validate parent terms
    for loc, parent_term in parent_terms.items():
        if parent_term == "":
            continue
        for pt in parent_term.split("|"):
            if pt not in labels.keys():
                problem_count += 1
                problems.append(
                    {
                        "ID": problem_count,
                        "table": basename,
                        "cell": loc,
                        "level": "error",
                        "rule ID": "",
                        "rule name": "Invalid parent term",
                        "value": pt,
                        "fix": "",
                        "instructions": "make sure that the parent term is a label listed in the "
                        "label column of this table",
                    }
                )
    return lines, problems


def main():
    p = ArgumentParser()
    p.add_argument("table")
    p.add_argument("labels")
    p.add_argument("output")
    args = p.parse_args()

    gecko_labels = []
    with open(args.labels, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        # Skip header
        next(reader)
        for row in reader:
            gecko_labels.append(row[0])

    table = args.table
    lines, problems = validate(table, gecko_labels)

    if lines:
        # Fix any leading or trailing whitespace
        lines = [{k: v.strip() for k, v in x.items()} for x in lines]

        # Write new IDs and trimmed whitespace
        with open(table, "w") as f:
            writer = csv.DictWriter(
                f,
                delimiter="\t",
                lineterminator="\n",
                fieldnames=[
                    "Term ID",
                    "Label",
                    "Parent Term",
                    "Definition",
                    "GECKO Category",
                    "Suggested Categories",
                    "Comment",
                ],
            )
            writer.writeheader()
            writer.writerows(lines)

    # Write any problems if we have them (always write the headers)
    with open(args.output, "w") as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            lineterminator="\n",
            fieldnames=[
                "ID",
                "table",
                "cell",
                "level",
                "rule ID",
                "rule name",
                "value",
                "fix",
                "instructions",
            ],
        )
        writer.writeheader()
        if problems:
            logging.critical(f"Validation failed with {len(problems)} errors!")
            writer.writerows(problems)


if __name__ == "__main__":
    main()
