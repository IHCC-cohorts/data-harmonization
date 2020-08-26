import collections
import csv

from argparse import ArgumentParser


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


def main():
    p = ArgumentParser()
    p.add_argument("labels")
    p.add_argument("namespace")
    p.add_argument("output")
    args = p.parse_args()

    gecko_labels = []
    with open(args.labels, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        # Skip header
        next(reader)
        for row in reader:
            gecko_labels.append(row[0])

    ns = args.namespace
    table = f"templates/{ns}.tsv"

    problems = []
    problem_count = 0
    # row -> ID
    ids = {}
    # label -> locs
    labels = {}
    # loc -> parent_term
    parent_terms = {}

    lines = []

    with open(table, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        # Skip template & validation strings
        lines.append(next(reader))
        lines.append(next(reader))

        row_idx = 3
        for row in reader:
            lines.append(row)
            row_idx += 1

            # Add ID to IDs (note that this may be empty)
            local_id = row["Term ID"].strip()
            ids[row_idx] = local_id

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
            if gecko_cat != "" and gecko_cat not in gecko_labels:
                problem_count += 1
                problems.append(
                    {
                        "ID": problem_count,
                        "table": ns,
                        "cell": idx_to_a1(row_idx, 5),
                        "level": "error",
                        "rule ID": "",
                        "rule name": "Invalid GECKO category",
                        "value": gecko_cat,
                        "fix": "",
                        "instructions": "select a valid GECKO category",
                    }
                )

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
                        "table": ns,
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
                        "table": ns,
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

    # Maybe assign IDs
    id_counter = 0
    updated_ids = {}

    # First get existing max ID number if there are existing IDs
    for local_id in ids.values():
        if local_id == "":
            continue
        try:
            num_id = int(local_id.split(":")[1].lstrip("0"))
        except ValueError:
            # Not a number - stick with whatever ID counter is currently at
            num_id = id_counter
        if num_id > id_counter:
            id_counter = num_id

    # Then assign IDs to any without
    for row, local_id in ids.items():
        if local_id == "":
            id_counter += 1
            id_str = str(id_counter).zfill(7)
            local_id = f"{ns}:{id_str}"
            updated_ids[row] = local_id

    if updated_ids:
        # Write new IDs if we have them
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
            row_idx = 1
            for line in lines:
                row_idx += 1
                if row_idx in updated_ids:
                    local_id = updated_ids[row_idx]
                    line["Term ID"] = local_id
                writer.writerow(line)

    if problems:
        # Write any problems if we have them
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
            writer.writerows(problems)


if __name__ == "__main__":
    main()
