import csv
import pandas as pd
import re

from argparse import ArgumentParser, FileType


def main():
    p = ArgumentParser()
    p.add_argument('input', type=str)
    p.add_argument('output', type=FileType('w'))
    args = p.parse_args()

    input_xlsx = args.input
    output_file = args.output

    xlsx = pd.ExcelFile(input_xlsx)
    sheet_names = ['APC', 'CC', 'OP', 'AE', 'DID', 'DID_Bridge', 'PROMS', 'MHMD_v4_Record', 'MHMD_v4_Event',
                   'MHMD_v4_Episode', 'CEN', 'ONS', 'SACT']

    labels = {}
    definitions = {}
    categories = {}
    values = {}
    comments = {}

    all_categories = []
    all_ids = []

    for sn in sheet_names:
        sheet = pd.read_excel(xlsx, sn)
        sheet.replace('NA', '', inplace=True)
        sheet.fillna('', inplace=True)
        for idx, row in sheet.iterrows():
            short_id = row['Field'].strip()
            if short_id == '':
                continue

            if 'Category' in sheet.columns:
                category = str(row['Category']).strip()
            else:
                category = ''

            if 'Short Name' in sheet.columns:
                label = str(row['Short Name']).strip()
            else:
                label = ''

            if 'Description' in sheet.columns:
                definition = str(row['Description']).strip()
            else:
                definition = ''

            if 'Value' in sheet.columns:
                value = str(row['Value']).strip()
            else:
                value = ''

            if 'Notes' in sheet.columns:
                comment = str(row['Notes']).strip()
                if 'removed' in comment.lower():
                    # TODO - if we can get the cell color that would be a better way to determine removed
                    # but xlrd throws error when loading with formatting_info=True
                    continue
            else:
                comment = ''

            # Add values to dicts
            if short_id not in all_ids:
                all_ids.append(short_id)

            if category not in all_categories and category != label:
                all_categories.append(category)

            if short_id in categories:
                existing_cats = categories[short_id]
                if category not in existing_cats and category != label:
                    existing_cats.append(category)
                categories[short_id] = existing_cats
            else:
                if category != label:
                    categories[short_id] = [category]
                else:
                    categories[short_id] = []

            if short_id in labels:
                existing_labels = labels[short_id]
                if label not in existing_labels:
                    existing_labels.append(label)
                labels[short_id] = existing_labels
            else:
                labels[short_id] = [label]

            if short_id in definitions:
                existing_defs = definitions[short_id]
                if definition not in existing_defs:
                    existing_defs.append(definition)
                definitions[short_id] = existing_defs
            else:
                definitions[short_id] = [definition]

            if short_id in values:
                existing_values = values[short_id]
                if value not in existing_values:
                    existing_values.append(value)
                values[short_id] = existing_values
            else:
                values[short_id] = [value]

            if short_id in comments:
                existing_comments = comments[short_id]
                if comment not in existing_comments:
                    existing_comments.append(comment)
                comments[short_id] = existing_comments
            else:
                comments[short_id] = [comment]

    # Write template headers, ROBOT template strings, ROBOT validation strings
    writer = csv.writer(output_file, delimiter='\t')
    writer.writerow(['ID', 'Label', 'Alternative Term(s)', 'Definition(s)', 'Parent(s)', 'Value(s)',
                     'Comment(s)'])
    writer.writerow(['ID', 'LABEL', 'A alternative term SPLIT=|', 'A definition SPLIT=|', 'SC %SPLIT=|',
                     'A value SPLIT=|', 'A rdfs:comment SPLIT=|'])
    writer.writerow(['', '', '', '', '',
                     '', ''])

    # Add the top-level categories
    if '' in all_categories:
        all_categories.remove('')
    for category in all_categories:
        # Skip any category that matches an existing label
        skip = False
        for vals in labels.values():
            if category in vals:
                skip = True
                break
        if skip:
            continue

        # Create a short ID and write to template
        short_id = re.sub(
            r'_+', '_', category.lower().replace(' ', '_').replace('/', '_').replace(';', '').replace('(', '').replace(
                ')', ''))
        writer.writerow(['ge:' + short_id, category, '', '', 'owl:Thing', '', ''])

    # Add the values from the sheet
    for short_id in all_ids:
        this_labels = labels[short_id]
        this_definitions = definitions[short_id]
        this_categories = categories[short_id]
        this_values = values[short_id]
        this_comments = comments[short_id]

        if len(this_labels) > 1 and '' in this_labels:
            this_labels.remove('')
        if len(this_definitions) > 1 and '' in this_definitions:
            this_definitions.remove('')
        if len(this_categories) > 1 and '' in this_categories:
            this_categories.remove('')
        if len(this_values) > 1 and '' in this_values:
            this_values.remove('')
        if len(this_comments) > 1 and '' in this_comments:
            this_comments.remove('')

        # Handle other identifiers that have the label 'Patient Identifier' (may be mixed case)
        synonyms = []
        if short_id != 'participant_id':
            if 'Patient identifier' in this_labels:
                this_labels.remove('Patient identifier')
                synonyms.append('Patient identifier')
            elif 'Patient Identifier' in this_labels:
                this_labels.remove('Patient Identifier')
                synonyms.append('Patient Identifier')

        if len(this_labels) > 1:
            # Pick the first label of the list
            label = this_labels.pop(0)
            synonyms.extend(this_labels)
        else:
            label = this_labels[0]

        if label.strip() == '':
            label = short_id

        writer.writerow(['ge:' + short_id, label, '|'.join(synonyms), '|'.join(this_definitions),
                         '|'.join(this_categories), '|'.join(this_values), '|'.join(this_comments)])

    output_file.close()


if __name__ == '__main__':
    main()
