#!/usr/bin/env python3
"""Build one ELT-paper example for each Euclidean symmetry type."""

import csv
import html
import json
import os
import re
import sys
from collections import defaultdict

from all_v10 import load_record_index
from elt_paper import CAPTIONS, CAPTURE_SCRIPT, page_css, still


TOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(TOP, "site", "personal")
TYPE_ORDER = (
    "*532", "532", "*432", "432", "*332", "3*2", "332",
    "*622", "*522", "*422", "*322", "*222",
    "2*6", "2*5", "2*4", "2*3", "2*2",
    "622", "522", "422", "322", "222",
    "*33", "*22", "*",
    "3*", "2*",
    "33", "22", "1",
    "3x", "2x", "x",
)


def representatives():
    record_path = os.path.join(TOP, "data", "atlas_records.jsonl")
    records = {
        record["id"]: record
        for record in (
            json.loads(line) for line in open(record_path) if line.strip()
        )
    }
    conway_path = os.path.join(TOP, "data", "conway.tsv")
    conway = {
        row["id"]: row["conway"]
        for row in csv.DictReader(open(conway_path), delimiter="\t")
    }
    classes = defaultdict(list)
    symmetry_path = os.path.join(TOP, "data", "symmetry.tsv")
    for row in csv.DictReader(open(symmetry_path), delimiter="\t"):
        record = records.get(row["id"])
        assert record is not None
        assert row["id"] in conway
        if record.get("maxdeg", 6) > 6:
            continue
        key = (
            int(row["order"]),
            int(row["nrefl"]) > 0,
            conway[row["id"]],
        )
        assert key[2] in TYPE_ORDER, (row["id"], key[2])
        classes[key[2]].append((key, record))

    assert set(classes) == set(TYPE_ORDER)
    chosen = []
    for symbol in TYPE_ORDER:
        signatures = {key for key, _ in classes[symbol]}
        assert len(signatures) == 1, (symbol, signatures)
        order, reflections, _ = signatures.pop()
        record = min(
            (record for _, record in classes[symbol]),
            key=lambda item: (item["v"], item["name"]),
        )
        nid = record["id"]
        common = CAPTIONS.get(nid)
        if common is None:
            stored = record.get("names", [])
            if stored and not re.fullmatch(r"(?:ant|j)\d+", stored[0]):
                common = stored[0]
        details = [
            f"order {order}",
            "reflections" if reflections else "chiral",
            f"v={record['v']}",
        ]
        if common:
            details.append(common)
        chosen.append({
            "id": nid,
            "v": record["v"],
            "name": record["clers"],
            "caption": symbol,
            "remark": " \u00b7 ".join(details),
            "type": (order, reflections, symbol),
        })

    assert len(chosen) == len(classes) == 33
    assert len({row["id"] for row in chosen}) == len(chosen)
    assert len({row["type"] for row in chosen}) == len(chosen)
    return chosen


def build(out=DEFAULT_OUT, records=None):
    rows = representatives()
    records = load_record_index(records)
    grid = (
        '<div class=grid>'
        + "".join(still(row, records) for row in rows)
        + "</div>"
    )
    css = (
        page_css(5, 1200)
        + ".name{font-size:1em;font-weight:bold}"
        + ".kind{line-height:1.3;min-height:2.6em}"
    )
    page = (
        "<!DOCTYPE html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        "<title>ELT symmetry types</title>"
        f"<style>{css}</style></head><body>"
        '<nav><a href="../index.html">neoplatonic solids</a> &middot; '
        '<a href="elt-paper.html">ELT gallery</a> &middot; '
        '<a href="symmetry.html">full symmetry gallery</a></nav>'
        "<h1>Symmetry types for the ELT paper</h1>"
        f'<p class=desc>One example of each of the '
        f'all {len(rows)} Conway symmetry types possible for a Euclidean '
        '6-net. '
        "Click any still to open its atlas page.</p>"
        + grid
        + CAPTURE_SCRIPT
        + "</body></html>"
    )
    gallery = os.path.join(out, "gallery")
    os.makedirs(gallery, exist_ok=True)
    target = os.path.join(gallery, "elt-symmetry.html")
    with open(target, "w") as output:
        output.write(page)
    print(f"gallery/elt-symmetry.html written ({len(rows)} models)")
    return target


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT)
