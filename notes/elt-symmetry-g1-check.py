#!/usr/bin/env python3
"""Check one minimum-v representative per Euclidean symmetry type."""

import csv
import json
from collections import defaultdict
from pathlib import Path


TOP = Path(__file__).resolve().parents[1]
TYPE_ORDER = (
    "*532", "532", "*432", "432", "*332", "332",
    "*622", "*522", "*422", "*322", "*222",
    "2*6", "2*5", "2*4", "2*3", "2*2", "2*",
    "622", "522", "422", "322", "222", "22",
    "*55", "*33", "*22", "*",
    "55", "33", "1", "2x", "x",
)
records = {
    row["id"]: row
    for row in map(
        json.loads,
        (TOP / "data" / "atlas_records.jsonl").read_text().splitlines(),
    )
}
conway = {
    row["id"]: row["conway"]
    for row in csv.DictReader(
        (TOP / "data" / "conway.tsv").open(), delimiter="\t"
    )
}
classes = defaultdict(list)
for row in csv.DictReader(
    (TOP / "data" / "symmetry.tsv").open(), delimiter="\t"
):
    record = records.get(row["id"])
    assert record is not None
    assert row["id"] in conway
    key = (int(row["order"]), int(row["nrefl"]) > 0, conway[row["id"]])
    classes[key].append(record)

by_symbol = {key[2]: key for key in classes}
assert set(by_symbol) == set(TYPE_ORDER)
chosen = []
for symbol in TYPE_ORDER:
    key = by_symbol[symbol]
    record = min(classes[key], key=lambda item: (item["v"], item["name"]))
    chosen.append((key, record))
    print(f"{key[2]}\torder={key[0]}\tv={record['v']}\t{record['id']}")

assert len(chosen) == len(classes)
assert len({key for key, _ in chosen}) == len(chosen)
assert len({record["id"] for _, record in chosen}) == len(chosen)
print(f"types={len(classes)} representatives={len(chosen)} pass")
