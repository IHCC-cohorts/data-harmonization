import csv
import json
import rdflib

from argparse import ArgumentParser, FileType


def main():
    p = ArgumentParser()
    p.add_argument('input', help="Cohort mapping template", type=FileType('r'))
    p.add_argument("index", help="GECKO index", type=FileType("r"))
    p.add_argument('output', help="Cohort mapping JSON", type=FileType('w'))
    args = p.parse_args()

    # Read in index
    index_file = args.index
    reader = csv.reader(index_file, delimiter="\t")

    # Skip header and template
    next(reader)
    next(reader)

    label_to_id = {}
    for row in reader:
        gecko_id = row[0]
        label = row[1]
        label_to_id[label] = gecko_id

    # Read in cohort input
    input_file = args.input
    reader = csv.reader(input_file, delimiter="\t")

    # Skip header, template, and validation
    next(reader)
    next(reader)
    next(reader)

    # Get the categories for each cohort term
    cat_map = {}
    for row in reader:
        subject = row[0]
        gecko_labels = row[4]
        for gecko_label in gecko_labels.split("|"):
            if gecko_label == "":
                continue
            if gecko_label not in label_to_id:
                print(f"ERROR: Missing GECKO category '{gecko_label}'")
                continue
            gecko_id = label_to_id[gecko_label]

            if gecko_id in cat_map:
                vals = cat_map[gecko_id]
            else:
                vals = []
            vals.append(subject)
            cat_map[gecko_id] = vals

    # Write to JSON file
    output_file = args.output
    output_file.write(json.dumps(cat_map, indent=2))
    output_file.close()


if __name__ == '__main__':
    main()
