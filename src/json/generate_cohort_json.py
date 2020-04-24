import csv
import json
import rdflib

from argparse import ArgumentParser, FileType

master_map = {}
ignore_variables = ['venous or arterial', 'fasting or non-fasting', 'DNA/Genotyping', 'WGS', 'WES', 'Sequence variants',
                    'Epigenetics', 'Metagenomics', 'Microbiome markers', 'RNAseq/gene expression', 'eQTL', 'other']
general_variables = ['signs and symptoms']


def main():
    global master_map
    parser = ArgumentParser(description='TODO')
    parser.add_argument('cohorts_csv', type=FileType('r'))
    parser.add_argument('cohorts_metadata', type=FileType('r'))
    parser.add_argument('cineca', type=FileType('r'))
    parser.add_argument('output', type=FileType('w'), help='output JSON')

    args = parser.parse_args()
    cohorts_file = args.cohorts_csv
    metadata_file = args.cohorts_metadata
    cineca_file = args.cineca
    output_file = args.output

    metadata = json.loads(metadata_file.read())
    cineca = json.loads(cineca_file.read())

    cohort_data = {}
    reader = csv.reader(cohorts_file)
    next(reader)
    for row in reader:
        # Parse countries
        countries = [x.strip() for x in row[2].split(',')]

        # Get available datatypes
        genomic = row[6]
        environment = row[7]
        biospecimen = row[8]
        clinical = row[9]
        datatypes = {'genomic_data': False,
                     'environmental_data': False,
                     'biospecimens': False,
                     'phenotypic_clinical_data': False}
        if genomic == 'Yes':
            datatypes['genomic_data'] = True
        if environment == 'Yes':
            datatypes['environmental_data'] = True
        if biospecimen == 'Yes':
            datatypes['biospecimens'] = True
        if clinical == 'Yes':
            datatypes['phenotypic_clinical_data'] = True

        cur_enroll = row[3].replace(',', '').strip()
        target_enroll = row[4].replace(',', '').strip()

        if cur_enroll == '':
            cur_enroll = None
        else:
            cur_enroll = int(cur_enroll)

        if target_enroll == '':
            target_enroll = None
        else:
            target_enroll = int(target_enroll)

        cohort_data[row[0]] = {'cohort_name': row[0],
                               'countries': countries,
                               'pi_lead': row[1],
                               'website': row[11],
                               'current_enrollment': cur_enroll,
                               'target_enrollment': target_enroll,
                               'enrollment_period': row[5],
                               'available_data_types': datatypes}

    all_data = []
    for cohort_name, cohort_metadata in metadata.items():
        file_name = 'build/mapping/{0}-gecko.ttl'.format(cohort_metadata['id'].lower())
        gin = rdflib.Graph()
        gin.parse(file_name, format='turtle')
        child_to_parent = get_children(gin, 'http://example.com/GECKO_9999998')
        master_map = {}
        data = get_categories(child_to_parent, cineca)
        if cohort_name in cohort_data:
            this_cohort = cohort_data[cohort_name]
            this_cohort.update(data)
            all_data.append(this_cohort)

    json_obj = json.dumps(all_data, indent=2)
    output_file.write(json_obj)
    output_file.close()


def build_nested(nested_dict, reverse_path):
    """Build a nested dictionary from a reveresed path (lowest level -> highest level)

    :param nested_dict: starting dictionary
    :param reverse_path: path from current level up
    :return: nested dictionary from path
    """
    cur_level = reverse_path.pop(0)
    new_dict = {cur_level: nested_dict}
    if reverse_path:
        return build_nested(new_dict, reverse_path)
    else:
        return new_dict


def clean_dict(d):
    """Clean dictionary by replacing any spaces and special characters in keys and values with underscores.

    :param d: dictionary to clean
    :return: cleaned dictionary
    """
    new = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = clean_dict(v)
        if isinstance(v, list):
            v = [clean_string(x) for x in v]
        new[clean_string(k)] = v
    return new


def clean_string(string):
    return string.replace(
        ' ', '_').replace('-', '_').replace('/', '_').replace('(', '').replace(')', '').replace('.', '')


def get_children(gin, node):
    """Get map of child -> parent terms.

    :param gin: rdflib Graph
    :param node: node to get children of
    :return: map of child -> parent terms
    """
    nodes = {}
    query = '''SELECT ?s ?label ?parent
               WHERE {
                       <%s> rdfs:label ?parent .
                       ?s rdfs:subClassOf <%s> ;
                          rdfs:label ?label .
                       FILTER(STRSTARTS(STR(?s), "http://example.com/GECKO_0")) }
               ORDER BY ?label''' % (node, node)

    qres = gin.query(query)
    for row in qres:
        if not row.s:
            continue

        label = str(row.label)
        if label in ignore_variables:
            continue

        nodes[label] = str(row.parent)
        this_children = get_children(gin, row.s)
        if len(this_children) > 0:
            nodes.update(this_children)

    return nodes


def get_categories(child_to_parent, cineca):
    """Get the CINECA categories used in a cohort as structured dictionary.

    :param child_to_parent: map of all children to their parent terms
    :param cineca: CINECA structure
    :return: subset of CINECA structure consisting of only categories used in this cohort
    """
    global master_map
    bottom_level = []
    for child, parent in child_to_parent.items():
        if child not in child_to_parent.values():
            bottom_level.append(child)

    subset = {}
    for leaf in bottom_level:
        result = get_path(cineca, leaf)
        if result is None:
            print('ERROR - unable to find "{0}"'.format(leaf))
            continue
        path = result[0]
        if path is None:
            print('ERROR - unable to find "{0}"'.format(leaf))
            continue
        has_children = result[1]
        path.reverse()
        if has_children:
            cur_level = path.pop(0)
            new_dict = build_nested({cur_level: []}, path)
        else:
            cur_level = path.pop(0)
            new_dict = build_nested([cur_level], path)
        subset = merge(new_dict, subset)
    return clean_dict(subset)


def merge(source, target):
    """Merge a source dictionary into a target dictionary

    :param source: source dictionary
    :param target: target dictionary
    :return: source merged into target
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = target.setdefault(key, {})
            merge(value, node)
        else:
            target[key] = value

    return target


def get_path(haystack, needle, path=None):
    """Search a nested dictionary for the path to a specific value.
    The value may be a key in a dict or a value in a list.

    :param haystack: nested dictionary to search
    :param needle: string value to search for
    :param path: pre-path
    :return: path to value as list
    """
    if path is None:
        path = []
    if isinstance(haystack, dict):
        if needle in haystack:
            # Value is a key and has children
            path.append(needle)
            return path, True
        for k, v in haystack.items():
            # Value not yet found
            result = get_path(v, needle, path + [k])
            if result is not None:
                return result
    elif isinstance(haystack, list):
        # Value is in a list and does not have children
        if needle in haystack:
            path.append(needle)
            return path, False
    else:
        # Value is not in this path
        return None, None


if __name__ == '__main__':
    main()
