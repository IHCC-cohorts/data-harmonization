import json

from argparse import ArgumentParser, FileType
from jinja2 import Template


def main():
    p = ArgumentParser()
    p.add_argument('template', type=FileType('r'))
    p.add_argument('metadata', type=FileType('r'))
    p.add_argument('index', type=FileType('w'))
    args = p.parse_args()

    t = Template(args.template.read())
    data = json.loads(args.metadata.read())

    items = []
    for cohort, item in data.items():
        short_name = item['id']
        item['name'] = cohort
        item['template'] = 'templates/{0}.tsv'.format(short_name)
        item['terms'] = 'build/{0}.html'.format(short_name)
        item['tree'] = 'build/{0}-tree.html'.format(short_name)
        item['mapping'] = 'build/{0}-gecko.html'.format(short_name)
        items.append(item)

    html = t.render(items=items)
    args.index.write(html)


if __name__ == '__main__':
    main()
