import csv
import re

from argparse import ArgumentParser, FileType


def main():
    p = ArgumentParser()
    p.add_argument('input', type=FileType('r'))
    p.add_argument('output', type=FileType('w'))
    args = p.parse_args()

    input_file = args.input
    output_file = args.output

    all_ids = []

    reader = csv.reader(input_file, delimiter='\t')
    next(reader)
    for row in reader:
        gecko_id = row[3]
        if ' ' in gecko_id:
            ids = re.sub(' +', ' ', gecko_id.replace('and', '').replace('or', '')).split(' ')
            all_ids.extend(ids)
        else:
            all_ids.append(gecko_id)

    for gecko_id in set(all_ids):
        output_file.write(gecko_id + '\n')


if __name__ == '__main__':
    main()
