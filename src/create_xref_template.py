import csv

from argparse import ArgumentParser, FileType

ignore = ['koges', 'gcs', 'vukuzazi', 'saprin', 'genomics england']


def main():
    p = ArgumentParser()
    p.add_argument('mapping_template', type=FileType('r'))
    p.add_argument('mapping_index', type=FileType('r'))
    p.add_argument('xref_template', type=FileType('w'))
    args = p.parse_args()

    mapping_template = args.mapping_template
    mapping_index = args.mapping_index
    xref_template = args.xref_template

    # make a map of index label to ID
    reader = csv.reader(mapping_index, delimiter='\t')
    next(reader)
    next(reader)
    label_to_id = {}
    for row in reader:
        if not row:
            continue
        gecko_id = row[0].strip()
        if gecko_id == '':
            continue
        alt_label = row[1].strip()
        gecko_label = row[2].strip()
        if gecko_label == '':
            continue
        if gecko_label in label_to_id:
            print('WARNING: label "{0}" already exists with as {1}'.format(
                gecko_label, label_to_id[gecko_label]))
            continue
        if alt_label != '' and alt_label not in label_to_id:
            label_to_id[alt_label] = gecko_id
        label_to_id[gecko_label] = gecko_id
    mapping_index.close()

    writer = csv.writer(xref_template, delimiter='\t')
    writer.writerow(['Label', 'Xref'])
    writer.writerow(['LABEL', 'AI database_cross_reference SPLIT=|'])
    reader = csv.reader(mapping_template, delimiter='\t')
    next(reader)
    next(reader)
    for row in reader:
        label = row[0].strip()
        gecko_labels = row[2].strip()
        if gecko_labels == '':
            continue
        iris = []
        for gl in gecko_labels.split('|'):
            if gl == '':
                continue
            if gl.lower() in ignore:
                continue
            if gl.strip() not in label_to_id:
                print('ERROR: "{0}" not in index!'.format(gl))
                continue
            iris.append(label_to_id[gl.strip()].replace('GECKO:', 'http://example.com/GECKO_'))
        writer.writerow([label, '|'.join(iris)])


if __name__ == '__main__':
    main()
