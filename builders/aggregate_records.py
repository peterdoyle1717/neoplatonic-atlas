#!/usr/bin/env python3
"""Aggregate built personal-page records into data/atlas_records.jsonl."""

import json
import os


HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
NETS = os.path.join(TOP, "site", "personal", "nets")
DEFAULT_OUT = os.path.join(TOP, "data", "atlas_records.jsonl")


def build(target=DEFAULT_OUT):
    records = []
    for directory in sorted(os.listdir(NETS)):
        path = os.path.join(NETS, directory, "net.json")
        if not os.path.isfile(path):
            continue
        with open(path) as source:
            record = json.load(source)
        assert record["id"] == directory, (directory, record["id"])
        records.append(record)

    with open(target, "w") as output:
        for record in records:
            output.write(json.dumps(record, separators=(",", ":")) + "\n")
    print(f"atlas_records.jsonl: {len(records)} records")
    return target


if __name__ == "__main__":
    build()
