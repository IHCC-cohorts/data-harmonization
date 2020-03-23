import json as jsonmod
from argparse import ArgumentParser, FileType


def to_json(lines):
    header = lines.pop(0)
    colnames = header.rstrip("\n").split("\t")
    line_num = 0
    print('[')
    for line in lines:
        line_num += 1
        parts = line.rstrip("\n").split("\t")
        if len(parts) != len(colnames):
            n = min(len(parts), len(colnames))
            dct = dict(zip(colnames[:n], parts[:n]))
        else:
            dct = dict(zip(colnames, parts))
        if line_num < len(lines):
            print('\t' + jsonmod.dumps(dct) + ',')
        else:
            print('\t' + jsonmod.dumps(dct))
    print(']')


def main():
    p = ArgumentParser()
    p.add_argument('tsv', type=FileType('r'))
    args = p.parse_args()
    to_json(args.tsv.readlines())


if __name__ == '__main__':
    main()
