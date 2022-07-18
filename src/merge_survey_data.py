import json
import re

import pandas as pd


def main():
    cohort_json = json.load(open('../data/cohort-data-copy.json'))
    cohort_map = {}
    for cohort in cohort_json:
        cohort_map[cohort['cohort_name']] = cohort

    survey_df = pd.read_csv('../data/survey_data.csv')
    survey_df.set_index('Identifiers', inplace=True)
    survey_df = survey_df.transpose()
    for index, row in survey_df.iterrows():
        cohort = {'cohort_name': row['Cohort Name']}
        if not pd.isna(row['Description']):
            cohort['description'] = row['Description']

        add_field(cohort, 'description', row['Description'])
        add_field(cohort, 'dictionary_harmonized', row['Dictionary harmonized'])
        add_field(cohort, 'license_data_dictionary', row['License data dictionary'])
        add_field(cohort, 'rights_data_dictionary', row['Rights data dictionary'])
        add_field(cohort, 'website', row['Website'])
        add_field(cohort, 'pi_lead', row['PI/Lead name'])
        add_array_field(cohort, 'countries', row['Countries'])
        add_percentage_field(cohort, 'irb_approved_data_sharing', row['Data Sharing'])
        add_duration_field(cohort, 'enrollment_period', row['Enrollment Start Year'], row['Enrollment End Year'])
        add_integer_field(cohort, 'current_enrollment', row['Current Enrollment'])
        add_integer_field(cohort, 'target_enrollment', row['Target Enrollment'])

        type_of_cohort = {}
        cohort['type_of_cohort'] = type_of_cohort
        add_boolean_filed(type_of_cohort, 'case_control', row['Case-control'])
        add_boolean_filed(type_of_cohort, 'cross_sectional', row['Cross-sectional'])
        add_boolean_filed(type_of_cohort, 'longitudinal', row['Longitudinal'])
        add_boolean_filed(type_of_cohort, 'health_records', row['Health records'])
        add_boolean_filed(type_of_cohort, 'other', row['Other'][0])

        cohort_ancestry = {}
        cohort['cohort_ancestry'] = cohort_ancestry
        add_percentage_field(cohort_ancestry, 'asian', row['Asian'])
        add_percentage_field(cohort_ancestry, 'black_african_american_or_african', row['Black, African American, or African'])
        add_percentage_field(cohort_ancestry, 'european_or_white', row['European or White'])
        add_percentage_field(cohort_ancestry, 'hispanic_latino_or_spanish', row['Hispanic, Latino, or Spanish'])
        add_percentage_field(cohort_ancestry, 'middle_eastern_or_north_african', row['Middle Eastern or North African'])
        add_percentage_field(cohort_ancestry, 'other', row['Other'][0])

        available_data_types = {}
        cohort['available_data_types'] = available_data_types
        add_percentage_field(available_data_types, 'biospecimens', row['Biospecimens'])
        add_percentage_field(available_data_types, 'genomic_data', row['Genomic Data'])
        add_percentage_field(available_data_types, 'genomic_data_wgs', row['Genomic Data - WGS'])
        add_percentage_field(available_data_types, 'genomic_data_wes', row['Genomic Data - WES'])
        add_percentage_field(available_data_types, 'genomic_data_array', row['Genomic Data - Genotype Array'])
        add_percentage_field(available_data_types, 'genomic_data_other', row['Genomic Data - Other'])
        add_boolean_filed(available_data_types, 'demographic_data', row['Demographic data'])
        add_percentage_field(available_data_types, 'imaging_data', row['Imaging Data'])
        add_percentage_field(available_data_types, 'participants_address_or_geocode_data', row["Participants' Address or Geocode Data"])
        add_percentage_field(available_data_types, 'electronic_health_record_data', row['Electronic Health Record Data'])
        add_percentage_field(available_data_types, 'phenotypic_clinical_data', row['Phenotypic/Clinical Data'])

        # cohort = {
        #     # 'cohort_id': row['Cohort ID'],
        #     'cohort_name': row['Cohort Name'],
        #     'description': row['Description'],
        #     'dictionary_harmonized': row['Dictionary harmonized'],
        #     'license_data_dictionary': row['License data dictionary'],
        #     'rights_data_dictionary': row['Rights data dictionary'],
        #     'website': row['Website'],
        #     'pi_lead': row['PI/Lead name'],
        #     'countries': str(row['Countries']).split(','),
        #     'irb_approved_data_sharing': row['Data Sharing'],
        #     'type_of_cohort': {
        #         'case_control': row['Case-control'],
        #         'cross_sectional': row['Cross-sectional'],
        #         'longitudinal': row['Longitudinal'],
        #         'health_records': row['Health records'],
        #         'other': row['Other'][0]  # conflict here
        #     },
        #     'cohort_ancestry': {
        #         'asian': row['Asian'],
        #         'black_african_american_or_african': row['Black, African American, or African'],
        #         'european_or_white': row['European or White'],
        #         'hispanic_latino_or_spanish': row['Hispanic, Latino, or Spanish'],
        #         'middle_eastern_or_north_african': row['Middle Eastern or North African'],
        #         'other': row['Other'][1]  # conflict here
        #     },
        #     'enrollment_period': str(row['Enrollment Start Year']) + ':' + str(row['Enrollment End Year']),
        #     'current_enrollment': row['Current Enrollment'],
        #     'target_enrollment': row['Target Enrollment'],
        #     'available_data_types': {
        #         'biospecimens': row['Biospecimens'],
        #         'genomic_data': row['Genomic Data'],
        #         'genomic_data_wgs': row['Genomic Data - WGS'],
        #         'genomic_data_wes': row['Genomic Data - WES'],
        #         'genomic_data_array': row['Genomic Data - Genotype Array'],
        #         'genomic_data_other': row['Genomic Data - Other'],
        #         'demographic_data': row['Demographic data'],
        #         'imaging_data': row['Imaging Data'],
        #         'participants_address_or_geocode_data': row["Participants' Address or Geocode Data"],
        #         'electronic_health_record_data': row['Electronic Health Record Data'],
        #         'phenotypic_clinical_data': row['Phenotypic/Clinical Data']
        #     }
        # }

        if cohort['cohort_name'] in cohort_map.keys():
            print("Merged cohorts: " + cohort['cohort_name'])
            old_cohort = cohort_map[cohort['cohort_name']]
            if 'questionnaire_survey_data' in old_cohort.keys():
                cohort['questionnaire_survey_data'] = old_cohort['questionnaire_survey_data']
            if 'survey_administration' in old_cohort.keys():
                cohort['survey_administration'] = old_cohort['survey_administration']
            if 'biosample' in old_cohort.keys():
                cohort['biosample'] = old_cohort['biosample']

            cohort_map[cohort['cohort_name']] = cohort
        else:
            cohort_map[cohort['cohort_name']] = cohort

    json.dump(list(cohort_map.values()), open("../data/cohort-data-all.json", "w"), indent=2)
    print("Total number of cohorts: " + str(len(cohort_map)))


def add_field(cohort, field_name, field):
    if not pd.isna(field):
        field = clean_field(field)
        cohort[field_name] = field


def add_boolean_filed(cohort, field_name, field):
    if not pd.isna(field):
        field = clean_field(field)

    if 'yes' in field.lower():
        cohort[field_name] = field
    elif 'no' in field.lower():
        cohort[field_name] = field
    else:
        cohort[field_name] = 'Unknown'


def add_integer_field(cohort, field_name, field):
    if not pd.isna(field):
        field = clean_field(field)
        field = clean_integers(field)
        if field != -1:
            cohort[field_name] = field


def add_percentage_field(cohort, field_name, field):
    if not pd.isna(field):
        field = clean_field(field)
        field = clean_percentage_field(field)
        cohort[field_name] = field


def add_duration_field(cohort, field_name, field_1, field_2):
    if (not pd.isna(field_1)) or (not pd.isna(field_2)):
        if pd.isna(field_1):
            field_1 = "-"
        if pd.isna(field_2):
            field_2 = "-"

        field_1 = clean_field(field_1)
        field_2 = clean_field(field_2)
        cohort[field_name] = str(field_1) + ":" + str(field_2)


def add_array_field(cohort, field_name, fields):
    if not pd.isna(fields):
        cohort[field_name] = [clean_field(f) for f in str(fields).split(',')]


def clean_field(field):
    field = field.strip()
    field = re.sub(r' +', ' ', field)
    field = "Unknown" if field == "Don't know" else field
    return field


def clean_integers(number_field):
    number_field = number_field.strip()
    number_field = number_field.replace(',', '')
    number_field = number_field.replace('.', '')
    number_field = number_field.replace(' ', '')
    numbers = re.findall(r'\d+', number_field)
    if numbers:
        number_field = int(numbers[0])
    else:
        print("Invalid number format in field: " + number_field)
        number_field = -1

    return number_field


def clean_percentage_field(field):
    percentage = re.findall(r'\d+-\d+%', field)
    if percentage:
        field = percentage[0]
    elif 'yes' in field.lower():
        field = '% Unknown'
    elif '% unknown' in field.lower():
        field = '% Unknown'
    elif 'no' in field.lower():
        field = '0%'
    return field


if __name__ == '__main__':
    main()
