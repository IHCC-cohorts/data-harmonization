import csv

from argparse import ArgumentParser, FileType


def create_label_map(index_file_path):
    global global_id

    label_map = {}
    with open(index_file_path, 'r') as index_file:
        index_reader = csv.reader(index_file, delimiter='\t')

        # Skip header
        try:
            next(index_reader)
        except StopIteration:
            # No rows in index
            return label_map

        for row in index_reader:
            curie = row[0]
            label = row[1]

            # Keep track of the latest ID number
            local_id = curie.split(':')[-1].lstrip('0')
            if local_id == '':
                local_id = 0
            else:
                local_id = int(local_id)
            if local_id > global_id:
                global_id = local_id

            label_map[label] = curie
    return label_map


def create_id(label, label_map):
    global global_id

    if label in label_map:
        # Term already has an ID, return this
        return label_map[label]

    # New term, create a new ID
    global_id += 1
    if global_id < 10:
        spaces = 6
    elif 9 < global_id < 100:
        spaces = 5
    elif 99 < global_id < 1000:
        spaces = 4
    else:
        spaces = 3
    return 'KoGES:' + ('0' * spaces) + str(global_id)


def main():
    global global_id

    p = ArgumentParser()
    p.add_argument('input', type=FileType('r'))
    p.add_argument('index', type=str)
    p.add_argument('output', type=FileType('w'))
    args = p.parse_args()

    input_file = args.input
    index_file_path = args.index
    output_file = args.output

    label_map = create_label_map(index_file_path)

    details = []
    reader = csv.reader(input_file, delimiter='\t')
    for row in reader:
        if len(row) == 0:
            continue
        label = row[0]
        if label.strip() in ['', 'CORE VARIABLES', 'SUBSTUDY VARIABLES']:
            continue
        short_id = create_id(label, label_map)
        if len(row) > 1:
            parent = row[1].strip()
        else:
            parent = ''
        details.append({'Short ID': short_id, 'Label': label, 'Parent': parent})

    input_file.close()

    # Write template headers, ROBOT template strings
    writer = csv.DictWriter(output_file, delimiter='\t', fieldnames=['Short ID', 'Label', 'Parent'])
    writer.writeheader()
    writer.writerow({'Short ID': 'ID',
                     'Label': 'LABEL',
                     'Parent': 'SC %'})
    # TODO: Add validation
    writer.writerow({})

    # Also remake the index file, adding new IDs
    index_file = open(index_file_path, 'w')
    index_writer = csv.writer(index_file, delimiter='\t', lineterminator='\n')
    index_writer.writerow(['Short ID', 'Label'])

    for d in details:
        short_id = d['Short ID']
        label = d['Label']
        writer.writerow(d)
        index_writer.writerow([short_id, label])

    output_file.close()
    index_file.close()


if __name__ == '__main__':
    global_id = 0
    main()
