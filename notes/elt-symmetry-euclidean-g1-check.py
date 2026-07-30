#!/usr/bin/env python3
"""Check the built 33-type Euclidean symmetry catalog and gallery."""

import csv
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


TOP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOP / "builders"))
from clers_tools import decode
from conway import autos_full, symbol
from personal import MORPH_ALPHAS, MORPH_VMAX, load_bend_store


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
EXTRA = {
    "3*": "CCCACCACACCACACCACACACCACACACCACACADABCAAEAE",
    "422": "CCCACCCACCACCACACCACACACACACACAACACAACAACAAACAAE",
    "3x": (
        "CCCCACCACCACCACCACACCACACACACCAACACACACCACACAACACCAACA"
        "ACACCAAAABABAE"
    ),
    "3*2": (
        "CCCCACCACCACCACCACACCACACCACACCACACCACACACCACACACCAACAC"
        "CAAACCACAACACCAAACACDEACDECADEACDEAAE"
    ),
}

assert len(TYPE_ORDER) == len(set(TYPE_ORDER)) == 33
assert {"*55", "55"}.isdisjoint(TYPE_ORDER)

try:
    load_bend_store({"hero": {}, "morph": []}, 24, MORPH_ALPHAS)
except ValueError as error:
    assert "incomplete morph store" in str(error)
else:
    raise AssertionError("low-v hero-only store was accepted")

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
symmetry = {
    row["id"]: {
        "order": int(row["order"]),
        "nrot": int(row["nrot"]),
        "nrefl": int(row["nrefl"]),
    }
    for row in csv.DictReader(
        (TOP / "data" / "symmetry.tsv").open(), delimiter="\t"
    )
}
nets_pages = {}
for line in (TOP / "data" / "nets_pages.txt").read_text().splitlines():
    name, netcode = line.split()
    assert name not in nets_pages
    nets_pages[name] = netcode

candidates = defaultdict(list)
for nid in symmetry:
    assert nid in records and nid in conway
    record = records[nid]
    if record["maxdeg"] <= 6:
        assert conway[nid] in TYPE_ORDER, (nid, conway[nid])
        candidates[conway[nid]].append(record)

for expected, name in EXTRA.items():
    faces = [tuple(face) for face in decode(name, verify=True)]
    v = max(max(face) for face in faces)
    degrees = {i: 0 for i in range(1, v + 1)}
    for face in faces:
        for vertex in face:
            degrees[vertex] += 1
    got = symbol(faces, v)
    autos = autos_full(faces, v)
    order = len(autos)
    nrot = sum(not flip for _, flip in autos)
    nrefl = sum(flip for _, flip in autos)
    reflections = any(flip for _, flip in autos)
    nid = f"v{v}{name}"
    netcode = ";".join(",".join(map(str, face)) for face in faces)
    assert got == expected, (expected, got)
    assert len(faces) == 2 * v - 4
    assert max(degrees.values()) <= 6
    assert nid in records, ("missing atlas record", expected, nid)
    assert nid in conway, ("missing Conway row", expected, nid)
    assert nid in symmetry, ("missing symmetry row", expected, nid)
    record = records[nid]
    assert record["id"] == record["name"] == nid
    assert record["clers"] == name
    assert record["v"] == v
    assert record["netcode"] == netcode
    assert record["maxdeg"] == max(degrees.values())
    assert name in nets_pages, ("missing nets_pages row", expected, name)
    assert nets_pages[name] == netcode
    assert conway[nid] == expected, (expected, conway[nid])
    assert symmetry[nid] == {
        "order": order,
        "nrot": nrot,
        "nrefl": nrefl,
    }, (expected, symmetry[nid], order, nrot, nrefl)

    store_path = TOP / "data" / "bends" / f"{nid}.json"
    assert store_path.is_file(), ("missing bend store", expected, nid)
    store = json.loads(store_path.read_text())
    assert store["clers"] == name
    assert store["v"] == v
    assert store["netcode"] == netcode
    assert store["maxdeg"] == record["maxdeg"]
    assert len(store["hero"]) == 3 * v - 6
    if v <= MORPH_VMAX:
        assert len(store["morph"]) == len(MORPH_ALPHAS)
        assert [round(row["alpha"], 6) for row in store["morph"]] == [
            round(alpha, 6) for alpha in MORPH_ALPHAS
        ]
    else:
        assert store["morph"] == []

    page_dir = TOP / "site" / "personal" / "nets" / nid
    net_json_path = page_dir / "net.json"
    assert net_json_path.is_file()
    built_record = json.loads(net_json_path.read_text())
    for field in ("id", "name", "clers", "v", "netcode", "maxdeg"):
        assert built_record[field] == record[field], (expected, field)
    actual_artifacts = {
        key: (page_dir / filename).is_file()
        for key, filename in (
            ("rb", "rb.glb"),
            ("clers_glb", "clers.glb"),
            ("morph_p", "morph_p.glb"),
            ("morph_k", "morph_k.glb"),
            ("ideal_net", "ideal_net.svg"),
            ("clers_layout", "clers_layout.svg"),
        )
    }
    assert built_record["artifacts"] == actual_artifacts
    assert record["artifacts"] == actual_artifacts
    assert (page_dir / "index.html").is_file()
    assert (page_dir / "rb.glb").is_file()
    if v <= MORPH_VMAX:
        assert (page_dir / "morph_p.glb").is_file()
        assert (page_dir / "morph_k.glb").is_file()
        assert "morph_note" not in built_record
    else:
        assert not (page_dir / "morph_p.glb").exists()
        assert not (page_dir / "morph_k.glb").exists()
        assert built_record["morph_note"] == (
            f"not built: v>{MORPH_VMAX} morph policy (PD 2026-07-24)"
        )
    print(
        f"supplement {expected}\tv={v}\torder={order}\t"
        f"reflections={int(reflections)}\tmaxdeg={record['maxdeg']}"
    )

assert set(candidates) == set(TYPE_ORDER)
chosen = []
for expected in TYPE_ORDER:
    record = min(candidates[expected], key=lambda row: (row["v"], row["name"]))
    assert record["maxdeg"] <= 6
    chosen.append(record)
    print(f"{expected}\tv={record['v']}\t{record['id']}")

assert len(chosen) == len(TYPE_ORDER) == 33
assert len({row["id"] for row in chosen}) == 33

gallery = TOP / "site" / "personal" / "gallery" / "elt-symmetry.html"
page = gallery.read_text()
tile_ids = re.findall(r'class=still href="\.\./nets/([^/]+)/"', page)
tile_labels = [
    html.unescape(label)
    for label in re.findall(r"<div class=name>(.*?)</div>", page)
]
assert tile_ids == [row["id"] for row in chosen]
assert tile_labels == list(TYPE_ORDER)
assert len(tile_ids) == len(set(tile_ids)) == 33
for nid in tile_ids:
    assert (TOP / "site" / "personal" / "nets" / nid / "index.html").is_file()

from elt_symmetry import representatives

built_rows = representatives()
assert [row["id"] for row in built_rows] == tile_ids
assert [row["caption"] for row in built_rows] == tile_labels
print("types=33 representatives=33 tiles=33 local-targets=33 maxdeg<=6 pass")
