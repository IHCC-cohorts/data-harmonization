import csv
import pandas as pd

from argparse import ArgumentParser, FileType


def main():
    p = ArgumentParser()
    p.add_argument('input', type=str)
    p.add_argument('output', type=FileType('w'))
    args = p.parse_args()

    input_xlsx = args.input
    output_file = args.output

    xlsx = pd.ExcelFile(input_xlsx)

    catid_strings = {}
    var_categories = pd.read_excel(xlsx, 'Variable Categories')

    cat_ids = var_categories['CategoryId'].unique().tolist()
    cat_ids = [int(x) for x in cat_ids]
    current_cat_id = 1
    while current_cat_id <= max(cat_ids):
        current_cats = var_categories.loc[var_categories['CategoryId'] == current_cat_id]
        cat_strings = []
        for idx, row in current_cats.iterrows():
            cat_value = int(row['CategoryValue'])
            label = str(row['Description'])
            cat_strings.append('{0} = {1}'.format(cat_value, label))
        catid_strings[current_cat_id] = '\n'.join(cat_strings)
        current_cat_id += 1

    entities = []
    variables = pd.read_excel(xlsx, 'Variables')
    for idx, row in variables.iterrows():
        local_id = str(row['VariableName']).strip()
        name = str(row['Description']).strip()
        cat_id = int(row['CategoryId'])
        cat_string = catid_strings[cat_id]
        entities.append({'Short ID': 'VZ:' + local_id, 'Label': name, 'Value': cat_string})

    writer = csv.DictWriter(output_file, fieldnames=['Short ID', 'Label', 'Value'], delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerow({'Short ID': 'ID', 'Label': 'LABEL', 'Value': 'A value'})
    # TODO: Add validation
    writer.writerow({})
    for entity in entities:
        writer.writerow(entity)
    output_file.close()


if __name__ == '__main__':
    main()
