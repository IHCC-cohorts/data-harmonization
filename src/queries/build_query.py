import json

from argparse import ArgumentParser, FileType


def main():
    p = ArgumentParser()
    p.add_argument('metadata', type=FileType('r'))
    p.add_argument('name')
    p.add_argument('output', type=FileType('w'))
    args = p.parse_args()

    metadata = json.loads(args.metadata.read())
    name = args.name
    prefix = None
    for cohort, details in metadata.items():
        short_name = details['id'].lower()
        cur_prefix = details['prefix']
        if short_name == name:
            prefix = cur_prefix

    if not prefix:
        print('ERROR: Unable to find "{0}" in metadata!'.format(name))
    query = '''PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?s ?cineca WHERE {
    ?s rdfs:subClassOf* ?cineca .
    FILTER(STRSTARTS(STR(?cineca), "https://purl.ihccglobal.org/GECKO_0"))
    FILTER(STRSTARTS(STR(?s), "https://purl.ihccglobal.org/%s_"))
}''' % prefix

    output_file = args.output
    output_file.write(query)
    output_file.close()


if __name__ == '__main__':
    main()
