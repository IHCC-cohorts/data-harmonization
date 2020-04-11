import csv
import json
import rdflib

from argparse import ArgumentParser, FileType

master_map = {}

cohorts = {'Korean Genome and Epidemiologyl Study (KoGES)': 'build/mapping/gecko-in-koges.ttl',
           'Golestan Cohort Study': 'build/mapping/gecko-in-gcs.ttl'}

ignore_variables = ['venous or arterial', 'fasting or non-fasting', 'DNA/Genotyping', 'WGS', 'WES', 'Sequence variants',
                    'Epigenetics', 'Metagenomics', 'Microbiome markers', 'RNAseq/gene expression', 'eQTL', 'other']


def main():
    global master_map
    parser = ArgumentParser(description='TODO')
    parser.add_argument('cohorts', type=FileType('r'))
    parser.add_argument('output', type=FileType('w'), help='output JSON')

    args = parser.parse_args()
    cohorts_file = args.cohorts
    output_file = args.output

    cohort_data = {}
    reader = csv.reader(cohorts_file)
    next(reader)
    for row in reader:
        countries = [x.strip() for x in row[2].split(',')]
        cohort_data[row[0]] = {'cohort_name': row[0], 'countries': countries, 'pi_lead': row[1], 'website': row[11]}

    all_data = []
    for cohort_name, file_name in cohorts.items():
        gin = rdflib.Graph()
        gin.parse(file_name, format='turtle')
        child_to_parent = get_children(gin, 'http://example.com/GECKO_9999998')
        master_map = {}
        data = get_data(child_to_parent)
        if cohort_name in cohort_data:
            this_cohort = cohort_data[cohort_name]
            this_cohort.update(data)
            all_data.append(this_cohort)

    json_obj = json.dumps(all_data, indent=2)
    output_file.write(json_obj)
    output_file.close()


def get_children(gin, node):
    """

    :param gin:
    :param node:
    :return:
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


def get_data(child_to_parent):
    global master_map
    bottom_level = {}
    for child, parent in child_to_parent.items():
        if child not in child_to_parent.values():
            if parent in bottom_level:
                children = bottom_level[parent]
            else:
                children = {}
            children[child] = {}
            bottom_level[parent] = children

    build_map(bottom_level, child_to_parent)
    clean(master_map)
    return master_map['CINECA']


def build_map(current_level, child_to_parent):
    global master_map

    next_level = {}
    for parent, children in current_level.items():
        if parent == 'CINECA':
            if 'CINECA' in current_level:
                master_map = merge(current_level, master_map)
            else:
                master_map = merge({'CINECA': current_level}, master_map)

        if parent in child_to_parent:
            next_parent = child_to_parent[parent]
            if next_parent in next_level:
                next_children = next_level[next_parent]
            else:
                next_children = {}
            next_children.update({parent: children})

            next_level[next_parent] = next_children
            build_map(next_level, child_to_parent)


def merge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination


def clean(dictionary):
    for key, value in dictionary.items():
        list_items = []
        for k, v in value.items():
            if not v:
                list_items.append(k)
        if list_items:
            dictionary[key] = list_items
            print(list_items)
        else:
            clean(value)



if __name__ == '__main__':
    main()
