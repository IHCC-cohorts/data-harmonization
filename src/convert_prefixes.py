import json

from argparse import ArgumentParser, FileType


def main():
	parser = ArgumentParser()
	parser.add_argument("json", type=FileType("r"))
	parser.add_argument("sql", type=FileType("w"))
	args = parser.parse_args()

	prefixes = json.loads(args.json.read())["@context"]

	sql = """CREATE TABLE IF NOT EXISTS prefix (
  prefix TEXT PRIMARY KEY,
  base TEXT NOT NULL
);

INSERT OR IGNORE INTO prefix VALUES
"""

	lines = []
	for prefix, namespace in prefixes.items():
		lines.append(f'("{prefix}", "{namespace}")')

	sql += ",\n".join(lines)
	sql += ";"

	args.sql.write(sql)


if __name__ == '__main__':
	main()
