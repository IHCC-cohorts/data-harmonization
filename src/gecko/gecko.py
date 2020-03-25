import csv
import re

from argparse import ArgumentParser, FileType


def create_label_map(index_file_path):
    global global_id

    label_map = {}
    with open(index_file_path, 'r') as index_file:
        index_reader = csv.reader(index_file, delimiter='\t')
        # Skip header
        next(index_reader)

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


def create_label(text):
    # Strip text in parentheses and return as a comment
    m = re.match(r'([^()]+) \((.+)\)$', text)
    comment = None
    if m:
        text = m.group(1)
        comment = m.group(2)
    return text, comment


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
    return 'gecko:' + ('0' * spaces) + str(global_id)


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

    reader = csv.reader(input_file, delimiter='\t')
    read = False

    # Create map of label -> ID
    # Also updates global ID to latest ID
    label_map = create_label_map(index_file_path)

    # Tracked variables
    broad_cat_iri = ''
    bc_label = ''
    sub_cat_iri = ''
    sc_label = ''
    sub_cat_var_iri = ''
    scv_label = ''
    var_iri = ''

    # Required fields
    child_parents = {}
    labels = {}

    # Optional annotations
    comments = {}
    details = {}

    row_num = 1
    for row in reader:
        # Skip header material
        col_a = row[0].strip()
        if col_a == 'Broad category':
            read = True
            continue

        # Expectations when reading:
        # sub-categories will always come after a defined broad category, and so on
        # anything in parentheses at the end of string is a comment, not part of the label (included as comment)
        # anything that starts with * is a comment in the sheet (not included)
        # annotations on a row will be added to the right-most class (e.g., if var exists, add to var)
        if read:
            broad_cat = col_a
            if broad_cat != '':
                if broad_cat.startswith('*'):
                    continue
                bc_label, bc_comment = create_label(broad_cat)
                broad_cat_iri = create_id(bc_label, label_map)
                child_parents[broad_cat_iri] = ''
                labels[broad_cat_iri] = bc_label
                if bc_comment:
                    comments[broad_cat_iri] = bc_comment

            sub_cat = row[1].strip()
            if sub_cat != '':
                if sub_cat.startswith('*'):
                    continue
                sc_label, sc_comment = create_label(sub_cat)
                sub_cat_iri = create_id(sc_label, label_map)
                child_parents[sub_cat_iri] = bc_label
                labels[sub_cat_iri] = sc_label
                if sc_comment:
                    comments[sub_cat_iri] = sc_comment

            sub_cat_var = row[2].strip()
            if sub_cat_var != '':
                if sub_cat_var.startswith('*'):
                    continue
                scv_label, scv_comment = create_label(sub_cat_var)
                sub_cat_var_iri = create_id(scv_label, label_map)
                child_parents[sub_cat_var_iri] = sc_label
                labels[sub_cat_var_iri] = scv_label
                if scv_comment:
                    comments[sub_cat_var_iri] = scv_comment

            var = row[3].strip()
            if var != '':
                if var.startswith('*'):
                    continue
                v_label, v_comment = create_label(var)
                var_iri = create_id(v_label, label_map)
                child_parents[var_iri] = scv_label
                labels[var_iri] = v_label
                if v_comment:
                    comments[var_iri] = v_comment

            question_desc = row[4].strip()
            answer_type = row[5].strip()
            ontology_label = row[6].strip()
            see_also = row[7].strip()
            definition = row[8].strip()
            num_cohorts = row[9].strip()
            use_case_reqs = row[10].strip()

            if var != '':
                target = var_iri
            elif sub_cat_var != '':
                target = sub_cat_var_iri
            elif sub_cat != '':
                target = sub_cat_iri
            elif broad_cat != '':
                target = broad_cat_iri
            else:
                print('Unknown target for row ' + str(row_num))
                continue

            entity = {'Question Description': question_desc,
                      'Expected Answer Type': answer_type,
                      'See Also ID': see_also,
                      'Definition': definition,
                      'Known Number of Cohorts': num_cohorts,
                      'Use Cases Requirements': use_case_reqs}

            if ontology_label != '':
                # Add ontology label to synonyms
                entity['Synonym'] = ontology_label
            else:
                entity['Synonym'] = ''

            details[target] = entity
            row_num += 1

    input_file.close()

    # Write template headers, ROBOT template strings
    # TODO - ROBOT validation strings
    writer = csv.DictWriter(output_file, delimiter='\t', fieldnames=['Short ID', 'Label', 'Definition', 'Parent',
                                                                     'Synonym', 'Comment', 'Question Description',
                                                                     'Expected Answer Type', 'See Also ID',
                                                                     'Known Number of Cohorts',
                                                                     'Use Cases Requirements'])
    writer.writeheader()
    writer.writerow({'Short ID': 'ID',
                     'Label': 'LABEL',
                     'Definition': 'A definition',
                     'Parent': 'SC %',
                     'Synonym': 'A alternative term',
                     'Comment': 'A comment',
                     'Question Description': 'A question description',
                     'Expected Answer Type': 'A answer type',
                     'See Also ID': 'A see also SPLIT=/',
                     'Known Number of Cohorts': 'A number of cohorts',
                     'Use Cases Requirements': 'A use cases requirements'})
    writer.writerow({}) # TODO: Add validation

    # Also remake the index file, adding new IDs
    index_file = open(index_file_path, 'w')
    index_writer = csv.writer(index_file, delimiter='\t')
    index_writer.writerow(['Short ID', 'Label'])

    for curie, parent in child_parents.items():
        # The following are optional annotations
        if curie in details:
            entity = details[curie]
        else:
            entity = {'Question Description': '',
                      'Expected Answer Type': '',
                      'See Also ID': '',
                      'Definition': '',
                      'Known Number of Cohorts': '',
                      'Use Cases Requirements': '',
                      'Synonym': ''}
        entity['Short ID'] = curie
        entity['Label'] = labels[curie]
        entity['Parent'] = parent
        if curie in comments:
            entity['Comment'] = comments[curie]
        else:
            entity['Comment'] = ''

        writer.writerow(entity)
        index_writer.writerow([curie, labels[curie]])

    output_file.close()
    index_file.close()


if __name__ == '__main__':
    global_id = 0
    main()
