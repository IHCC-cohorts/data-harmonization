import csv
import re

from argparse import ArgumentParser, FileType


def create_label(text):
    # Strip text in parentheses and return as a comment
    m = re.match(r'([^()]+) \((.+)\)$', text)
    comment = None
    if m:
        text = m.group(1)
        comment = m.group(2)
    return text, comment


def create_iri(label):
    # Replace illegal characters and return full IRI
    # TODO - replace with CURIE when we have a true namespace
    local_id = label.strip().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '').replace('.', '')
    return 'http://example.com/' + local_id


def main():
    p = ArgumentParser()
    p.add_argument('input', type=FileType('r'))
    p.add_argument('output', type=FileType('w'))
    args = p.parse_args()

    input_file = args.input
    output_file = args.output

    reader = csv.reader(input_file, delimiter='\t')
    read = False

    broad_cat_iri = ''
    sub_cat_iri = ''
    sub_cat_var_iri = ''
    var_iri = ''

    # Required fields
    child_parents = {}
    labels = {}

    # Optional annotations
    comments = {}
    definitions = {}
    synonyms = {}
    question_descriptions = {}
    answer_types = {}
    alt_ids = {}
    number_cohorts = {}
    use_case_requirements = {}

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
                broad_cat_iri = create_iri(bc_label)
                child_parents[broad_cat_iri] = ''
                labels[broad_cat_iri] = bc_label
                if bc_comment:
                    comments[broad_cat_iri] = bc_comment

            sub_cat = row[1].strip()
            if sub_cat != '':
                if sub_cat.startswith('*'):
                    continue
                sc_label, sc_comment = create_label(sub_cat)
                sub_cat_iri = create_iri(sc_label)
                child_parents[sub_cat_iri] = broad_cat_iri
                labels[sub_cat_iri] = sc_label
                if sc_comment:
                    comments[sub_cat_iri] = sc_comment

            sub_cat_var = row[2].strip()
            if sub_cat_var != '':
                if sub_cat_var.startswith('*'):
                    continue
                scv_label, scv_comment = create_label(sub_cat_var)
                sub_cat_var_iri = create_iri(scv_label)
                child_parents[sub_cat_var_iri] = sub_cat_iri
                labels[sub_cat_var_iri] = scv_label
                if scv_comment:
                    comments[sub_cat_var_iri] = scv_comment

            var = row[3].strip()
            if var != '':
                if var.startswith('*'):
                    continue
                v_label, v_comment = create_label(var)
                var_iri = create_iri(v_label)
                child_parents[var_iri] = sub_cat_var_iri
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

            if ontology_label != '':
                # Replace predicted label and add synonym
                synonyms[target] = labels[target]
                labels[target] = ontology_label

            question_descriptions[target] = question_desc
            answer_types[target] = answer_type
            alt_ids[target] = see_also
            definitions[target] = definition
            number_cohorts[target] = num_cohorts
            use_case_requirements[target] = use_case_reqs

            row_num += 1

    input_file.close()

    # Write template headers
    writer = csv.writer(output_file, delimiter='\t')
    writer.writerow(['IRI', 'Label', 'Definition', 'Parent', 'Synonym', 'Comment', 'Question Description',
                     'Expected Answer Type', 'See Also ID', 'Known Number of Cohorts', 'Use Cases Requirements'])
    writer.writerow(['ID', 'LABEL', 'A definition', 'SC %', 'A alternative term', 'A comment', 'A question description',
                     'A answer type', 'A see also', 'A number of cohorts', 'A use cases requirements'])
    for iri, parent_iri in child_parents.items():
        # Each class must have a parent_iri and a label
        label = labels[iri]

        # The following are optional annotations
        definition = ''
        if iri in definitions:
            definition = definitions[iri]

        synonym = ''
        if iri in synonyms:
            synonym = synonyms[iri]

        comment = ''
        if iri in comments:
            comment = comments[iri]

        question_desc = ''
        if iri in question_descriptions:
            question_desc = question_descriptions[iri]

        answer_type = ''
        if iri in answer_types:
            answer_type = answer_types[iri]

        see_also = ''
        if iri in alt_ids:
            see_also = alt_ids[iri]

        num_cohorts = ''
        if iri in number_cohorts:
            num_cohorts = number_cohorts[iri]

        use_case_reqs = ''
        if iri in use_case_requirements:
            use_case_reqs = use_case_requirements[iri]

        writer.writerow([iri, label, definition, parent_iri, synonym, comment, question_desc, answer_type, see_also,
                         num_cohorts, use_case_reqs])
    output_file.close()


if __name__ == '__main__':
    main()
