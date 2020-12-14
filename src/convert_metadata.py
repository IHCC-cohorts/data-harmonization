import csv
import json

from argparse import ArgumentParser, FileType


csv_headers = [
    "Cohort Name",
    "PI/Lead",
    "Regions",
    "Enroll Start",
    "Enroll End",
    "Enrolled",
    "Target Enrollment",
    "Genomic Data",
    "Environmental Data",
    "Biospecimens",
    "Phenotypic/Clinical Data",
    "Data Sharing",
    "Study Website",
]


def main():
    p = ArgumentParser()
    p.add_argument("json", type=FileType("r"))
    p.add_argument("csv", type=FileType("w"))
    args = p.parse_args()

    json_metadata = json.load(args.json)

    rows = []
    for details in json_metadata.values():
        row = {
            "Cohort Name": details["cohort_name"],
            "PI/Lead": details["pi_lead"],
            "Regions": ", ".join(details["countries"]),
            "Enroll Start": details["enrollment_period"].split(":")[0],
            "Enroll End": details["enrollment_period"].split(":")[1],
            "Enrolled": details["current_enrollment"],
            "Target Enrollment": details["target_enrollment"],
            "Study Website": details["website"],
        }
        for k, v in details["available_data_types"].items():
            if k == "phenotypic_clinical_data":
                k = "Phenotypic/Clinical Data"
            else:
                k = k.replace("_", " ").title()
            if v:
                v = "Yes"
            else:
                v = "No"
            row[k] = v
        data_sharing = details["irb_approved_data_sharing"]
        if data_sharing:
            data_sharing = "Yes"
        else:
            data_sharing = "No"
        row["Data Sharing"] = data_sharing
        rows.append(row)

    writer = csv.DictWriter(args.csv, lineterminator="\n", fieldnames=csv_headers)
    writer.writeheader()
    writer.writerows(rows)


if __name__ == '__main__':
    main()
