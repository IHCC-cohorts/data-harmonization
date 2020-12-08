import csv
import json
import logging
import os

from argparse import ArgumentParser, FileType

bottom_level = []


def main():
    parser = ArgumentParser(description="Create JSON for IHCC cohort browser")
    parser.add_argument(
        "cohorts_csv", type=FileType("r", encoding='ISO-8859-1'), help="IHCC member cohort details"
    )
    parser.add_argument(
        "cohorts_metadata",
        type=FileType("r"),
        help="Cohort metadata (name -> ID, prefix)",
    )
    parser.add_argument("gecko", type=FileType("r"), help="JSON structure of GECKO")
    parser.add_argument("output", type=FileType("w"), help="output JSON")

    args = parser.parse_args()
    cohorts_file = args.cohorts_csv
    metadata_file = args.cohorts_metadata
    output_file = args.output

    metadata = json.loads(metadata_file.read())
    gecko = json.loads(args.gecko.read())[1]
    gecko_hierarchy = build_hierarchy(gecko)

    cohort_data = {}
    reader = csv.DictReader(cohorts_file)
    for row in reader:
        # Parse countries
        countries = [x.strip() for x in row["Regions"].split(",")]

        # Get available datatypes
        genomic = row["Genomic Data "]
        environment = row["Env. Data"]
        biospecimen = row["Bio specimens"]
        clinical = row["Phenotypic Data"]
        datatypes = {
            "genomic_data": False,
            "environmental_data": False,
            "biospecimens": False,
            "phenotypic_clinical_data": False,
        }
        if genomic == "Yes":
            datatypes["genomic_data"] = True
        if environment == "Yes":
            datatypes["environmental_data"] = True
        if biospecimen == "Yes":
            datatypes["biospecimens"] = True
        if clinical == "Yes":
            datatypes["phenotypic_clinical_data"] = True

        cur_enroll = row["Enrolled"].replace(",", "").strip()
        target_enroll = row["Target Enrollment"].replace(",", "").strip()

        if cur_enroll == "":
            cur_enroll = None
        else:
            cur_enroll = int(float(cur_enroll))

        if target_enroll == "":
            target_enroll = None
        else:
            target_enroll = int(float(target_enroll))

        enroll_start = row["Enroll Start"]
        enroll_end = row["Enroll End"]
        if not enroll_start and not enroll_end:
            enroll_period = None
        elif enroll_end and not enroll_start:
            enroll_period = enroll_end
        else:
            enroll_period = f"{enroll_start}:{enroll_end}"

        cohort_data[row["Cohort Name"]] = {
            "cohort_name": row["Cohort Name"],
            "countries": countries,
            "pi_lead": row["PI/Lead"],
            "website": row["Study website"],
            "current_enrollment": cur_enroll,
            "target_enrollment": target_enroll,
            "enrollment_period": enroll_period,
            "available_data_types": datatypes,
        }

    all_data = []
    for cohort_name, cohort_metadata in metadata.items():
        cohort_id = cohort_metadata["prefix"].lower()
        file_name = f"templates/{cohort_id}.tsv"
        if not os.path.exists(file_name):
            logging.critical(f"{cohort_name} template {file_name} does not exist!")
            continue
        gecko_cats = []
        with open(file_name, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                gecko_cat = row["GECKO Category"]
                if gecko_cat.strip() == "":
                    continue
                gecko_cats.extend(gecko_cat.split("|"))
        gecko_cats = list(set(gecko_cats))
        data = get_categories(gecko_cats, gecko_hierarchy)
        if cohort_name in cohort_data:
            this_cohort = cohort_data[cohort_name]
            this_cohort.update(data)
        else:
            this_cohort = {
                "cohort_name": cohort_name,
                "countries": [],
                "pi_lead": "",
                "website": "",
                "current_enrollment": "",
                "target_enrollment": "",
                "enrollment_period": "",
                "available_data_types": [],
            }

        # Add other metadata elements
        for key in ["recontact_in_place", "irb_approved_data_sharing", "longitudinal_data"]:
            this_cohort.update({key: cohort_metadata.get(key, False)})
        
        all_data.append(this_cohort)

    json_obj = json.dumps(all_data, indent=2, sort_keys=True)
    output_file.write(json_obj)
    output_file.close()


def build_hierarchy(node):
    """Build the GECKO hierarchy based on the JSON output from ROBOT tree.

    :param node: current node in nested dict
    :return: hierarchy dict
    """
    global bottom_level
    if isinstance(node, list):
        # List of children -> transform to dict
        nodes = {}
        gen_vars = []
        for itm in node:
            if "children" in itm:
                nodes[itm["id"]] = build_hierarchy(itm)
            else:
                gen_vars.append(itm["id"])
        if gen_vars and nodes:
            nodes["general_variables"] = gen_vars
        if gen_vars and not nodes:
            return gen_vars
    else:
        # Is a dict
        if "children" in node:
            return build_hierarchy(node["children"])
        else:
            bottom_level.append(node["id"])
            return None
    return nodes


def build_nested(nested_dict, reverse_path):
    """Build a nested dictionary from a reversed path (lowest level -> highest level)

    :param nested_dict: starting dictionary
    :param reverse_path: path from current level up
    :return: nested dictionary from path
    """
    if len(reverse_path) == 0:
        return nested_dict
    cur_level = reverse_path.pop(0)
    new_dict = {cur_level: nested_dict}
    if len(reverse_path) > 0:
        return build_nested(new_dict, reverse_path)
    else:
        return new_dict


def clean_dict(d):
    """Clean dictionary by replacing any spaces and special characters in keys and values with
    underscores.

    :param d: dictionary to clean
    :return: cleaned dictionary
    """
    new = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = clean_dict(v)
        if isinstance(v, list):
            v = [x.capitalize() for x in v]
            v = sorted(v)
        new[clean_string(k)] = v
    return new


def clean_string(string):
    return (
        string.replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "")
    )


def get_categories(categories, gecko):
    """Get the CINECA categories used in a cohort as structured dictionary.

    :param categories:
    :param gecko:
    :return:
    """
    subset = {}
    for leaf in categories:
        result = get_path(gecko, leaf)
        if result is None:
            logging.error(f'unable to find "{leaf}"')
            continue
        path = result[0]
        if path is None:
            logging.error(f'unable to find "{leaf}"')
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
            if key in target and not target[key]:
                target[key] = {}
            node = target.setdefault(key, {})
            merge(value, node)
        else:
            if key in target:
                target_value = target[key]
                if isinstance(target_value, list) and isinstance(value, list):
                    target_value.extend(value)
                    target[key] = target_value
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


if __name__ == "__main__":
    main()
