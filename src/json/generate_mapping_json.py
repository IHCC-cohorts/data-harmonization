import csv
import json
import rdflib

from argparse import ArgumentParser, FileType

cohorts = {'KoGES': 'build/mapping/koges-to-gecko.ttl'}


def main():
    p = ArgumentParser()
    p.add_argument('input', type=FileType('r'))
    p.add_argument('output', type=FileType('w'))
    args = p.parse_args()

    input_file = args.input
    reader = csv.reader(input_file)
    next(reader)
    cat_map = {}
    for row in reader:
        subject = to_curie(row[0])
        cineca = to_curie(row[1])
        if cineca in cat_map:
            vals = cat_map[cineca]
        else:
            vals = []
        vals.append(subject)
        cat_map[cineca] = vals

    output_file = args.output
    output_file.write(json.dumps(cat_map, indent=2))
    output_file.close()


def to_curie(iri):
    return iri.replace('http://example.com/', '').replace('_', ':')


if __name__ == '__main__':
    main()
