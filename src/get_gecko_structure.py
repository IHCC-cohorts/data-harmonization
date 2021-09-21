import json
import sqlite3

from argparse import ArgumentParser


def get_subclass_array(cur, term_id):
    children = []
    cur.execute(
        "SELECT DISTINCT stanza FROM statements WHERE predicate = 'rdfs:subClassOf' AND object = ?",
        (term_id,),
    )
    for res in cur.fetchall():
        if res[0] == "GECKO:0000019":
            # Skip "blood collected from fasting subject"
            continue
        next_level = parse_class(cur, res[0])
        if not next_level:
            continue
        children.append(next_level)
    return children


def parse_class(cur, term_id):
    cur.execute(
        "SELECT value FROM statements WHERE predicate = 'rdfs:label' AND stanza = ?", (term_id,)
    )
    res = cur.fetchone()
    if res:
        label = res[0]
    else:
        label = term_id
    children = get_subclass_array(cur, term_id)
    if children:
        return {"id": label, "children": get_subclass_array(cur, term_id)}
    return {"id": label}


def main():
    parser = ArgumentParser()
    parser.add_argument("db")
    args = parser.parse_args()

    with sqlite3.connect(args.db) as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT stanza FROM statements WHERE stanza NOT IN
               (SELECT stanza FROM statements WHERE predicate = 'rdfs:subClassOf')
               AND predicate = 'rdf:type' AND object = 'owl:Class';"""
        )
        classes = []
        for res in cur.fetchall():
            classes.append(parse_class(cur, res[0]))
        out = {"id": "http://www.w3.org/2002/07/owl#Thing", "text": "Classes", "children": classes}
    print(json.dumps(out, indent=4))


if __name__ == "__main__":
    main()
