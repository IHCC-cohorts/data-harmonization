import csv

from argparse import ArgumentParser, FileType

ignore = ['koges', 'gcs', 'vukuzazi', 'saprin', 'genomics england', 'maelstrom']


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
    label_to_id = {}
    reader = csv.reader(mapping_index, delimiter='\t')
    # Skip header and template rows
    next(reader)
    for row in reader:
        if not row:
            # Row is empty
            continue
        # Get the GECKO CURIE
        gecko_id = row[0].strip()
        if gecko_id == '':
            # No curie, skip row
            continue
        # Get the label
        gecko_label = row[1].strip()
        if gecko_label == '':
            # No label, skip row
            continue
        if gecko_label in label_to_id:
            print('ERROR: label "{0}" already exists with as {1}'.format(
                gecko_label, label_to_id[gecko_label]))
            continue
        # Add to map
        label_to_id[gecko_label] = gecko_id
    mapping_index.close()

    # Create the Xref template headers
    writer = csv.writer(xref_template, delimiter='\t')
    writer.writerow(['ID', 'Xref', 'Xref Label'])
    writer.writerow(['ID', 'A database_cross_reference', '>A label'])

    # Read in the mapping template to get Xrefs
    reader = csv.reader(mapping_template, delimiter='\t')
    next(reader)
    next(reader)
    for row in reader:
        if len(row) < 3:
            # No GECKO mapping
            continue

        # Get the CURIE for the subject
        curie = row[0].strip()
        # And the GECKO label (maybe more than one)
        gecko_labels = row[4].strip()
        if gecko_labels == '':
            continue
        iris_labels = {}
        # Split on pipe and get CURIEs based on label
        for gl in gecko_labels.split('|'):
            if gl == '':
                continue
            if gl.lower() in ignore:
                continue
            if gl.strip() not in label_to_id:
                print('ERROR: "{0}" not in index!'.format(gl))
                continue
            iri = label_to_id[gl.strip()]
            iris_labels[iri] = gl.strip()
        for i, l in iris_labels.items():
            writer.writerow([curie, i, l])


if __name__ == '__main__':
    main()
