#!/usr/bin/env python3
"""Build the gallery of candidate nets for the ELT paper."""

import html
import json
import os
import sys

from all_v10 import CSS, load_census, load_record_index, validate
from views import net_id


TOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(TOP, "site", "personal")
BEND_TOL = 1e-6
GALLERY_AZIMUTH = 0
GALLERY_ELEVATION = 35

V10_NAMES = [
    "CCACCCACCACABDEE",
    "CCCACACACCAACAAE",
    "CCCACCACACAACAAE",
    "CCCACCACACACAAAE",
]
DROP = {
    "v6CCACACAE",
    "v7CCACCABCAE",
    "v7CCACCACAAE",
    "v9CCCACACACCAABE",
    "v10CCACCCACCACABDEE",
    "v10CCCACACACCAACAAE",
    "v10CCCACCACACACAAAE",
}
TOP_EIGHT = [
    "v4CCAE",
    "v5CCACAE",
    "v6CCCACAAE",
    "v7CCCACACAAE",
    "v8CCCACACACAAE",
    "v9CCCACCACACAAAE",
    "v10CCCACCACACAACAAE",
    "v12CCCCACCACACACAACAAAE",
]
NEGATIVE_IDS = [
    "v23CCCACACACCAACACACCAACACACCAACACACCAACACAAE",
    "v28CCCACACCACACACACCACACACACACCACACACADECACACACAACACAAE",
    "v107h025ed392ab598a98",
]
EXTRA_IDS = [
    "v14CCCCACCACACACACACAACAAAE",
    "v24CCCACCACCACCACACACACCACACCAAACACACAACACDEAAE",
    "v452hdf751e9c22065e97",
]
CAPTIONS = {
    "v4CCAE": "tetrahedron",
    "v5CCACAE": "triangular bipyramid",
    "v6CCCACAAE": "octahedron",
    "v7CCACACACAE": "short 3NA",
    "v7CCACACCABE": "four around an axis",
    "v7CCCACACAAE": "pentagonal bipyramid",
    "v8CCACCCABCABE": "triakis tetrahedron",
    "v8CCCACACACAAE": "snub disphenoid",
    "v8CCCACACCAABE": "pancake",
    "v9CCCACAACCACAAE": "stack of two octahedra",
    "v9CCCACACACACAAE": "negative-bend example",
    "v9CCCACCACACAAAE": "triaugmented triangular prism",
    "v10CCCACCACACAACAAE": "gyroelongated square bipyramid",
    "v12CCCCACCACACACAACAAAE": "icosahedron",
    "v23CCCACACACCAACACACCAACACACCAACACACCAACACAAE":
        "(2,2)-phyllohedron",
    "v28CCCACACCACACACACCACACACACACCACACACADECACACACAACACAAE":
        "buried vertices example",
    "v107h025ed392ab598a98": "T=21 (4,1) subdivision",
    "v14CCCCACCACACACACACAACAAAE": "hexagonal antiprism",
    "v24CCCACCACCACCACACACACCACACCAAACACACAACACDEAAE":
        "large (5,1)-phyllohedron",
    "v452hdf751e9c22065e97": "order-5 limit example",
}
ICOSA = {
    "v": 12,
    "kind": "prime",
    "name": "CCCCACCACACACAACAAAE",
}


def bend_counts(nid, v):
    path = os.path.join(TOP, "data", "bends", f"{nid}.json")
    with open(path) as source:
        bends = json.load(source)["hero"].values()
    positive = sum(bend > BEND_TOL for bend in bends)
    zero = sum(abs(bend) <= BEND_TOL for bend in bends)
    negative = sum(bend < -BEND_TOL for bend in bends)
    assert positive + zero + negative == 3 * v - 6
    return positive, zero, negative


def selection():
    census = load_census()
    validate(census)
    by_v = {
        v: [row for row in census if row["v"] == v]
        for v in range(4, 11)
    }
    chosen = (
        sum((by_v[v] for v in range(4, 8)), [])
        + by_v[8][-3:]
        + by_v[9][-4:]
        + [
            next(row for row in by_v[10] if row["name"] == name)
            for name in V10_NAMES
        ]
        + [ICOSA]
    )
    chosen = [
        row for row in chosen
        if f"v{row['v']}{row['name']}" not in DROP
    ]

    record_path = os.path.join(TOP, "data", "atlas_records.jsonl")
    by_id = {
        rec["id"]: rec
        for rec in (
            json.loads(line) for line in open(record_path) if line.strip()
        )
    }
    for nid in NEGATIVE_IDS + EXTRA_IDS:
        rec = by_id[nid]
        chosen.append({
            "v": rec["v"],
            "name": rec["clers"],
            "kind": "prime",
            "id": nid,
        })

    by_key = {
        row.get("id", f"v{row['v']}{row['name']}"): row
        for row in chosen
    }
    remaining = [
        row for row in chosen
        if row.get("id", f"v{row['v']}{row['name']}")
        not in TOP_EIGHT
    ]
    chosen = [by_key[nid] for nid in TOP_EIGHT] + sorted(
        remaining, key=lambda row: row["v"]
    )
    keys = [
        row.get("id", f"v{row['v']}{row['name']}")
        for row in chosen
    ]
    assert len(keys) == len(set(keys)) == 20
    for row, key in zip(chosen, keys):
        row["caption"] = CAPTIONS[key]
        positive, zero, negative = bend_counts(key, row["v"])
        row["remark"] = f"(+{positive}, {zero}, \u2212{negative})"
    return [("ELT paper", chosen)]


def still(row, records):
    full = f"v{row['v']}{row['name']}"
    rec = records.get(full)
    assert rec is not None, f"missing personal-page record for {full}"
    nid = row.get("id", rec.get("id", net_id(row["v"], row["name"])))
    label = html.escape(row["caption"])
    remark = html.escape(row["remark"]) or "&nbsp;"
    return (
        '<div class=item>'
        f'<a class=still href="../nets/{nid}/">'
        '<div class=cell>'
        f'<img class=viewer-still data-file="nets/{nid}/rb.glb" '
        f'alt="{label}"></div>'
        f'<div class=name>{label}</div></a>'
        f'<div class=kind>{remark}</div></div>'
    )


def page_css(columns=4, width=1000):
    return (
        CSS
        + f"body{{max-width:{width}px}}.grid{{grid-template-columns:"
        f"repeat({columns},minmax(0,1fr));gap:1em}}"
        ".name{font-family:Georgia,serif;font-size:.78em}"
        ".kind{min-height:1.2em}.cell{padding:0}"
        ".cell img{display:block;width:100%;height:100%;object-fit:contain}"
        ".capture-frame{position:fixed;left:0;top:0;width:400px;height:400px;"
        "opacity:0;pointer-events:none;z-index:-1;border:0}"
        ".still{display:block}.still:hover{text-decoration:none}"
        ".still:hover .name{text-decoration:underline}"
        "@media(max-width:700px){.grid{grid-template-columns:"
        "repeat(2,minmax(0,1fr))}}"
    )


CAPTURE_SCRIPT = """<script>
const captureQueue = [...document.querySelectorAll('img.viewer-still')];
let activeCapture = null;
let captureNumber = 0;

function finishCapture() {
  if (!activeCapture) return;
  clearTimeout(activeCapture.timer);
  activeCapture.frame.remove();
  activeCapture = null;
  requestAnimationFrame(startCapture);
}

function startCapture() {
  const image = captureQueue.shift();
  if (!image) return;
  const token = String(++captureNumber);
  const frame = document.createElement('iframe');
  frame.className = 'capture-frame';
  frame.title = '';
  const file = encodeURIComponent(image.dataset.file);
  frame.src = `../turntable.html?file=${file}&static=1&capture=1&token=${token}`
    + `&azimuth=%d&elevation=%d`;
  activeCapture = {image, frame, token, timer: null};
  document.body.append(frame);
  activeCapture.timer = setTimeout(finishCapture, 30000);
}

addEventListener('message', event => {
  if (!activeCapture || event.origin !== location.origin
      || event.source !== activeCapture.frame.contentWindow
      || event.data?.type !== 'atlax-turntable-capture'
      || event.data.token !== activeCapture.token) return;
  activeCapture.image.src = event.data.image;
  finishCapture();
});

startCapture();
</script>""" % (GALLERY_AZIMUTH, GALLERY_ELEVATION)


def build(out=DEFAULT_OUT, records=None):
    rows = [row for _, group in selection() for row in group]
    records = load_record_index(records)
    grid = (
        '<div class=grid>'
        + "".join(still(row, records) for row in rows)
        + "</div>"
    )
    css = (
        page_css()
    )
    page = (
        "<!DOCTYPE html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        f"<title>Possibilities for the ELT paper</title><style>{css}</style>"
        "</head><body>"
        '<nav><a href="../index.html">neoplatonic solids</a> &middot; '
        '<a href="elt-symmetry.html">ELT symmetry types</a> &middot; '
        '<a href="all-v10.html">all nets through v=10</a></nav>'
        "<h1>Possibilities for the ELT paper</h1>"
        '<p class=desc>A working selection of 20 models. '
        'Click any still to open its atlas page. '
        'Bend counts are (+, 0, \u2212).</p>'
        + grid
        + CAPTURE_SCRIPT
        + "</body></html>"
    )
    gallery = os.path.join(out, "gallery")
    os.makedirs(gallery, exist_ok=True)
    target = os.path.join(gallery, "elt-paper.html")
    with open(target, "w") as output:
        output.write(page)
    print("gallery/elt-paper.html written (20 models)")
    return target


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT)
