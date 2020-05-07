import csv
import yaml

from argparse import ArgumentParser, FileType

child_parents = {}
labels = {}
fr_synonyms = {}
definitions = {}
fr_definitions = {}


def parse_item(item, parent):
    iri = 'http://example.com/MAELSTROM_' + item['name']
    title_en = item['title']['en']
    title_fr = item['title']['fr']
    description_en = item['description']['en']
    description_fr = item['description']['fr']

    child_parents[iri] = parent
    labels[iri] = title_en
    fr_synonyms[iri] = title_fr
    definitions[iri] = description_en
    fr_definitions[iri] = description_fr

    # TODO - these are currently all empty
    # attrs = item['attributes']
    # keywords = item['keywords']

    children = item['terms']
    for c in children:
        parse_item(c, iri)


def main():
    p = ArgumentParser()
    p.add_argument('input', type=FileType('r'))
    p.add_argument('output', type=FileType('w'))
    args = p.parse_args()

    input_file = args.input
    output_file = args.output

    # Skip header line
    next(input_file)
    maelstrom = yaml.safe_load(input_file)
    input_file.close()

    for item in maelstrom['vocabularies']:
        parse_item(item, '')

    writer = csv.writer(output_file, delimiter='\t')
    writer.writerow(['ID', 'Label', 'Definition', 'Parent', 'French Synonym', 'French Definition'])
    writer.writerow(['ID', 'LABEL', 'AL definition@en', 'SC %', 'AL alternative term@fr', 'AL definition@fr'])
    writer.writerow([])
    for iri, parent in child_parents.items():
        label = labels[iri]
        definition = definitions[iri]
        alt_term = fr_synonyms[iri]
        fr_definition = fr_definitions[iri]
        writer.writerow([iri, label, definition, parent, alt_term, fr_definition])
    output_file.close()


if __name__ == '__main__':
    main()
