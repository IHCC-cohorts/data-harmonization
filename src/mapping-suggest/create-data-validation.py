#!/usr/bin/env python

import csv
import re

from argparse import ArgumentParser


def main():
	p = ArgumentParser()
	p.add_argument("table")
	p.add_argument("output")
	args = p.parse_args()

	dv_rows = []
	with open(args.table, "r") as f:
		reader = csv.DictReader(f, delimiter="\t")
		row_num = 2
		for row in reader:
			suggested_cats = row["Suggested Categories"]
			cat_names = []
			for sc in suggested_cats.split(" | "):
				match = re.search(r"[^ ]+ [A-Z]+:[0-9]+ (.+)", sc)
				if match:
					cat_names.append(match.group(1))
			if cat_names:
				dv_rows.append({"table": "terminology", "range": f"E{row_num}", "condition": "ONE_OF_LIST", "value": ", ".join(cat_names)})
			row_num += 1

	with open(args.output, "w") as f:
		writer = csv.DictWriter(f, delimiter="\t", fieldnames=["table", "range", "condition", "value"])
		writer.writeheader()
		writer.writerows(dv_rows)


if __name__ == '__main__':
	main()