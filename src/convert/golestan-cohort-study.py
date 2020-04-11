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

    # Use the index to get the names of other tabs
    index = pd.read_excel(xlsx, 'Tables list')
    table_names = []
    label_map = {}
    details = []
    for idx, row in index.iterrows():
        short_id = str(row['Table Name'])
        label = str(row['Long Name'])
        definition = str(row['Description'])
        table_names.append(short_id)
        label_map[short_id] = label
        details.append({'Short ID': 'GCS:' + short_id, 'Label': label, 'Definition': definition})

    for tn in table_names:
        sheet = pd.read_excel(xlsx, tn)
        sheet.fillna('', inplace=True)
        for col in sheet.columns:
            sheet[col] = sheet[col].apply(lambda x: str(x).strip())
        sheet.replace('-', '', inplace=True)
        parent = label_map[tn]

        for idx, row in sheet.iterrows():
            # Columns may have different headers so just use their index
            short_id = str(row[sheet.columns[1]])
            if short_id == '':
                continue
            if tn != 'ID' and short_id == 'PID':
                # Keep PID only in Identity
                continue
            var_type = str(row[sheet.columns[2]])
            int_type = str(row[sheet.columns[3]])
            unit = str(row[sheet.columns[4]])
            definition = str(row[sheet.columns[5]])
            value = str(row[sheet.columns[6]])
            formula = str(row[sheet.columns[7]])
            measurement_time = str(row[sheet.columns[8]])

            if value == '':
                # Value might have already been set with categorical ints,
                # If not, just put the variable type
                if var_type == 'Integer' and int_type != '':
                    value = '{0} Integer'.format(int_type)
                else:
                    value = var_type
                if unit != '':
                    # Maybe add unit in parentheses
                    value = '{0} ({1})'.format(value, unit)

            details.append({'Short ID': 'GCS:' + short_id,
                            'Parent': parent,
                            'Label': short_id,
                            'Definition': definition,
                            'Value': value,
                            'Formula': formula,
                            'Measurement Time': measurement_time})
    xlsx.close()

    writer = csv.DictWriter(output_file, fieldnames=['Short ID', 'Label', 'Parent', 'Definition', 'Value',
                                                     'Formula', 'Measurement Time'],
                            delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerow({'Short ID': 'ID',
                     'Label': 'LABEL',
                     'Parent': 'SC %',
                     'Definition': 'A definition',
                     'Value': 'A value',
                     'Formula': 'A formula',
                     'Measurement Time': 'A measurement time'})
    # TODO: Add validation
    writer.writerow({})

    for d in details:
        writer.writerow(d)
    output_file.close()


if __name__ == '__main__':
    main()
