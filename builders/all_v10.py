#!/usr/bin/env python3
"""Build the complete gallery of combinatorial 6-nets through v=10."""

from collections import Counter
from itertools import combinations
import hashlib
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
DEFAULT_OUT = os.path.join(TOP, "site", "personal")
DATA = os.path.join(TOP, "data", "nets_all_v4_10.txt")
EXPECTED_COUNTS = {4: 1, 5: 1, 6: 2, 7: 5, 8: 10, 9: 15, 10: 30}
EXPECTED_SHA256 = "005e7b4fdf34a33e1082c227d35014df1b167d2b76b562ce44bdbbd0948edfd9"

sys.path.insert(0, HERE)
from clers_tools import decode
from views import display, net_id


CSS = (
    "body{font-family:Georgia,serif;max-width:1000px;margin:2em auto;"
    "line-height:1.6;color:#222;padding:0 1em}"
    "nav{font-size:.9em}a{color:#2255aa;text-decoration:none}"
    "a:hover{text-decoration:underline}h1{font-size:1.3em}"
    "h2{font-size:1em;margin-top:2em;border-bottom:1px solid #ddd;"
    "padding-bottom:.25em}h2 span{font-size:.8em;color:#777;font-weight:normal}"
    ".desc{font-size:.9em;color:#555}.grid{display:grid;"
    "grid-template-columns:repeat(4,minmax(0,1fr));gap:1.5em;margin-top:1em}"
    ".item{text-align:center;min-width:0}.cell{aspect-ratio:1;display:flex;"
    "align-items:center;justify-content:center;border:1px solid #ddd;"
    "background:#fafafa;box-sizing:border-box;padding:.45em}"
    ".cell model-viewer{width:100%;height:100%;display:block;"
    "--poster-color:transparent}"
    ".name{font-family:monospace;font-size:.75em;word-break:break-all;"
    "line-height:1.25;margin-top:.45em}.kind{font-size:.7em;color:#888}"
    "@media(max-width:700px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}"
)


def load_census(path=DATA):
    rows = []
    for line in open(path):
        if not line.strip() or line.startswith("#"):
            continue
        v, kind, name, netcode = line.split()
        rows.append({
            "v": int(v),
            "kind": kind,
            "name": name,
            "netcode": netcode,
        })
    return rows


def prime_from_faces(faces, v):
    facial = {frozenset(face) for face in faces}
    adj = {x: set() for x in range(1, v + 1)}
    for a, b, c in faces:
        adj[a].update((b, c))
        adj[b].update((a, c))
        adj[c].update((a, b))
    triangles = {
        frozenset((a, b, c))
        for a, b, c in combinations(range(1, v + 1), 3)
        if b in adj[a] and c in adj[a] and c in adj[b]
    }
    return triangles == facial


def validate(rows):
    by_v = Counter()
    names = set()
    for row in rows:
        v, kind, name = row["v"], row["kind"], row["name"]
        assert kind in {"prime", "nonprime"}
        assert (len(name) + 4) // 2 == v
        assert name not in names
        names.add(name)
        by_v[v] += 1
        faces = decode(name)
        stored_faces = [
            tuple(map(int, face.split(",")))
            for face in row["netcode"].split(";")
        ]
        assert stored_faces == faces
        vertices = {x for face in faces for x in face}
        edges = Counter(
            frozenset((face[i], face[(i + 1) % 3]))
            for face in faces
            for i in range(3)
        )
        degree = Counter(x for edge in edges for x in edge)
        assert vertices == set(range(1, v + 1))
        assert len(faces) == 2 * v - 4
        assert len(edges) == 3 * v - 6
        assert set(edges.values()) == {2}
        assert max(degree.values()) <= 6
        assert prime_from_faces(faces, v) == (kind == "prime")
    assert dict(sorted(by_v.items())) == EXPECTED_COUNTS
    digest = hashlib.sha256(
        "".join(f'v{row["v"]}{row["name"]}\n'
                for row in sorted(rows, key=lambda r: (r["v"], r["name"]))).encode()
    ).hexdigest()
    assert digest == EXPECTED_SHA256


def load_record_index(records=None):
    if records is not None:
        return {rec["name"]: rec for rec in records.values()}
    path = os.path.join(TOP, "data", "atlas_records.jsonl")
    index = {
        rec["name"]: rec
        for rec in (json.loads(line) for line in open(path) if line.strip())
    }
    local_nets = os.path.join(DEFAULT_OUT, "nets")
    if os.path.isdir(local_nets):
        for directory in os.listdir(local_nets):
            record = os.path.join(local_nets, directory, "net.json")
            if os.path.isfile(record):
                rec = json.load(open(record))
                index[rec["name"]] = rec
    return index


def tile(row, records):
    v, name, kind = row["v"], row["name"], row["kind"]
    full = f"v{v}{name}"
    rec = records.get(full)
    assert rec is not None, f"missing personal-page record for {full}"
    label = row.get("label", display(full))
    nid = rec.get("id", net_id(v, name))
    orbit = row.get("orbit", "0deg 100deg auto")
    shown = f'<a href="../nets/{nid}/">{label}</a>'
    model = (
        f'<model-viewer src="../nets/{nid}/rb.glb" data-net="{full}" '
        f'camera-orbit="{orbit}" camera-controls '
        f'interaction-prompt=none aria-label="Euclidean model of {full}">'
        f'</model-viewer>'
    )
    remark = row.get("remark", kind.replace("nonprime", "non-prime"))
    return (
        f'<div class=item><div class=cell>{model}</div>'
        f'<div class=name>{shown}</div>'
        f'<div class=kind>{html.escape(remark)}</div>'
        f'</div>'
    )


def build(out=DEFAULT_OUT, records=None):
    rows = load_census()
    validate(rows)
    records = load_record_index(records)
    parts = []
    for v in sorted(EXPECTED_COUNTS):
        section = [row for row in rows if row["v"] == v]
        primes = sum(row["kind"] == "prime" for row in section)
        nonprimes = len(section) - primes
        parts.append(
            f'<h2>v = {v} <span>{len(section)} '
            f'{"net" if len(section) == 1 else "nets"}: '
            f'{primes} prime, {nonprimes} non-prime</span></h2>'
            f'<div class=grid>'
            + "".join(tile(row, records) for row in section)
            + '</div>'
        )
    page = (
        '<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        f'<title>All 6-nets through v=10</title><style>{CSS}</style>'
        '<script type=module src="../vendor/model-viewer.min.js"></script>'
        '</head><body>'
        '<nav><a href="../index.html">neoplatonic solids</a></nav>'
        '<h1>All 6-nets through v = 10</h1>'
        '<p class=desc>Every triangulation of the sphere with at most six '
        'triangles at a vertex, through ten vertices: 64 nets, 15 prime and '
        '49 non-prime.</p>'
        + "".join(parts)
        + '</body></html>'
    )
    gallery = os.path.join(out, "gallery")
    os.makedirs(gallery, exist_ok=True)
    target = os.path.join(gallery, "all-v10.html")
    with open(target, "w") as output:
        output.write(page)
    print(f"gallery/all-v10.html written ({len(rows)} nets)")
    return target


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT)
