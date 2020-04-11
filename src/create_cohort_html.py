#!/usr/bin/env python3

import json
import os

from argparse import ArgumentParser, FileType
from jinja2 import Template


def main():
    parser = ArgumentParser(description='Create HTML pages for cohorts')
    parser.add_argument('json', type=FileType('r'), help='Cohorts JSON data')
    parser.add_argument('metadata', type=FileType('r'), help='Cohort JSON metadata')
    parser.add_argument('template', type=FileType('r'), help='HTML template')
    parser.add_argument('output_dir', type=str, help='HTML output directory')
    args = parser.parse_args()

    metadata_str = args.metadata.read()
    metadata = json.loads(metadata_str)

    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    json_str = args.json.read()
    data = json.loads(json_str)

    template_str = args.template.read()

    for cohort_data in data:
        name = cohort_data['cohort_name']
        cohort_data['countries'] = ', '.join(cohort_data['countries'])

        if name not in metadata:
            print('ERROR: no metadata for ' + name)
            continue
        cohort_md = metadata[name]
        cohort_id = cohort_md['id'].lower().replace(' ', '-')

        cohort_data.update(cohort_md)
        cohort_data['tree'] = '../{0}-tree.html'.format(cohort_id)
        cohort_data['owl'] = '../{0}.owl'.format(cohort_id)

        template = Template(template_str)
        res = template.render(o=cohort_data)

        output_file = '{0}/{1}.html'.format(output_dir, cohort_id)
        with open(output_file, 'w+') as f:
            f.write(res)
        print('Created ' + output_file)


if __name__ == '__main__':
    main()
