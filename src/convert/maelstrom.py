import csv
import yaml

from argparse import ArgumentParser

CHILD_PARENTS = {}
LABELS = {}
FR_SYNONYMS = {}
DEFINITIONS = {}
FR_DEFINITIONS = {}
INTERNAL_IDS = {}
MAPPINGS = {}

NUM_ID = 0


def parse_item(item, parent):
    global NUM_ID
    curie = "MAELSTROM:" + str(NUM_ID).zfill(7)
    CHILD_PARENTS[curie] = parent
    LABELS[curie] = item['title']['en']
    FR_SYNONYMS[curie] = item['title']['fr']
    DEFINITIONS[curie] = item['description']['en']
    FR_DEFINITIONS[curie] = item['description']['fr']
    INTERNAL_IDS[curie] = item['name']

    # TODO - these are currently all empty
    # attrs = item['attributes']
    # keywords = item['keywords']

    children = item['terms']
    for c in children:
        parse_item(c, curie)
        NUM_ID += 1


def main():
    global NUM_ID
    p = ArgumentParser()
    p.add_argument('input', help="Maelstrom YAML file")
    p.add_argument("template", help="Maelstrom template")
    args = p.parse_args()

    with open(args.template, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        next(reader)
        for row in reader:
            MAPPINGS[row["Internal ID"]] = row["GECKO Category"]

    with open(args.input, "r") as f:
        next(f)
        maelstrom = yaml.safe_load(f)

    for item in maelstrom['vocabularies']:
        parse_item(item, '')
        NUM_ID += 1

    with open(args.template, "w") as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['ID', 'Label', 'Definition', 'Parent', 'French Synonym', 'French Definition', "Internal ID", "GECKO Category"])
        for curie, parent in CHILD_PARENTS.items():
            internal_id = INTERNAL_IDS[curie]
            mapping = MAPPINGS.get(internal_id)
            writer.writerow([curie, LABELS[curie], DEFINITIONS[curie], parent, FR_SYNONYMS[curie], FR_DEFINITIONS[curie], internal_id, mapping])


if __name__ == '__main__':
    main()
