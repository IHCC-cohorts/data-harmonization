import csv
import re

from argparse import ArgumentParser, FileType

# These are duplicated field names
# We will append the mid- or top-level category name to the start of the label to differentiate
bot_duplicates = ['Identifier', 'Individual', 'Type', 'Location', 'Date', 'Birth', 'StartEvent', 'EndEvent',
                  'External identifier', 'Place', 'Membership', 'Household', 'Observation']
mid_duplicates = ['Membership']


def main():
    p = ArgumentParser()
    p.add_argument('input', type=FileType('r'))
    p.add_argument('output', type=FileType('w'))
    args = p.parse_args()

    input_file = args.input
    output_file = args.output

    reader = csv.reader(input_file, delimiter='\t')
    top_cat = ''
    top_cat_id = ''
    mid_cat = ''
    mid_cat_id = ''
    details = []
    for row in reader:
        item = row[0]
        notes = re.sub(r'  +', '\n', row[1])
        if '.' not in item:
            # Not part of the numbered items
            continue
        label = item.split('.')[1].strip()
        short_id = re.sub(r' *\(.+\)', '', label).replace('HIV-', 'HIVNeg').replace('HIV+', 'HIVPos').replace(' ', '_')

        # A -> 1 -> a
        if re.match(r'^[A-Z]\.', item):
            top_cat = label
            top_cat_id = short_id
            details.append({'Short ID': 'SAPRIN:' + short_id,
                            'Label': label,
                            'Definition': notes})
        elif re.match(r'^[0-9]\.', item):
            for dup in mid_duplicates:
                if label == dup:
                    label = ' '.join([label, top_cat])
                    short_id = '_'.join([short_id, top_cat_id])
            mid_cat = label
            mid_cat_id = short_id
            details.append({'Short ID': 'SAPRIN:' + short_id,
                            'Label': label,
                            'Parent': top_cat,
                            'Definition': notes})
        else:
            for dup in bot_duplicates:
                if label == dup:
                    label = ' '.join([label, '({0})'.format(mid_cat)])
                    short_id = '_'.join([short_id, mid_cat_id])

            if re.match(r'(.|\n)*i\. (.|\n)+ii\.', notes):
                # Extract values and definition
                vals = []
                definition_lines = []
                for line in notes.split('\n'):
                    if re.match(r'^[ivx]+\.', line.strip()):
                        vals.append(line.strip())
                    else:
                        definition_lines.append(line.strip())
                val_string = '\n'.join(vals)
                definition = '\n'.join(definition_lines)
            else:
                val_string = ''
                definition = notes

            details.append({'Short ID': 'SAPRIN:' + short_id,
                            'Label': label,
                            'Parent': mid_cat,
                            'Definition': definition,
                            'Value': val_string})
    input_file.close()

    writer = csv.DictWriter(output_file, fieldnames=['Short ID', 'Label', 'Parent', 'Definition', 'Value'],
                            delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerow({'Short ID': 'ID',
                     'Label': 'LABEL',
                     'Parent': 'SC %',
                     'Definition': 'A definition',
                     'Value': 'A value'})
    # TODO: add validation
    writer.writerow({})
    writer.writerows(details)
    output_file.close()


if __name__ == '__main__':
    main()
