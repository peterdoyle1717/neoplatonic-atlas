#!/usr/bin/env python3
"""Preflight the selected ELT rb.glb assets for the still renderer."""

import argparse
import json
import math
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

TOP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOP / "builders"))
from elt_paper import selection
from views import net_id

SELECTED = [
    row.get("id", net_id(row["v"], row["name"]))
    for _, group in selection()
    for row in group
]


def gltf(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", data)
    assert magic == b"glTF" and version == 2 and length == len(data)
    offset = 12
    doc = None
    while offset < length:
        size, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset:offset + size]
        offset += size
        if kind == 0x4E4F534A:
            doc = json.loads(chunk.decode().rstrip("\x00 "))
    assert doc is not None
    return doc


def check_glb(path):
    doc = gltf(path)
    assert len(doc.get("materials", [])) == 2
    assert len(doc.get("meshes", [])) == 1
    primitives = doc["meshes"][0]["primitives"]
    assert len(primitives) == 2
    assert [p.get("mode", 4) for p in primitives] == [4, 4]
    assert [p["material"] for p in primitives] == [0, 1]
    for primitive in primitives:
        accessor = doc["accessors"][primitive["indices"]]
        assert accessor["count"] % 3 == 0
        assert accessor["count"] > 0
    position = doc["accessors"][primitives[0]["attributes"]["POSITION"]]
    assert position["type"] == "VEC3" and position["count"] > 3
    bounds = position["min"] + position["max"]
    assert all(math.isfinite(x) for x in bounds)
    assert any(a < b for a, b in zip(position["min"], position["max"]))


def check_png(path):
    data = path.read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    assert data.endswith(b"IEND\xaeB`\x82")
    offset = 8
    idat = []
    width = height = None
    while offset < len(data):
        size = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + size]
        offset += 12 + size
        if kind == b"IHDR":
            width, height, depth, color, _, _, _ = struct.unpack(
                ">IIBBBBB", payload
            )
            assert width == height and depth == 8 and color == 2
        elif kind == b"IDAT":
            idat.append(payload)
    raw = zlib.decompress(b"".join(idat))
    stride = 1 + 3 * width
    assert len(raw) == height * stride
    rows = []
    for y in range(height):
        row = raw[y * stride:(y + 1) * stride]
        assert row[0] == 0
        rows.append(np.frombuffer(row[1:], dtype=np.uint8).reshape(width, 3))
    image = np.stack(rows)
    mask = np.any(image < 250, axis=2)
    yy, xx = np.where(mask)
    assert len(xx) > 0
    span = max(xx.max() - xx.min() + 1, yy.max() - yy.min() + 1)
    occupancy = span / width
    center_x = (xx.min() + xx.max()) / 2
    center_y = (yy.min() + yy.max()) / 2
    target = (width - 1) / 2
    assert 0.70 <= occupancy <= 0.74, (path, occupancy)
    assert abs(center_x - target) <= 2, (path, center_x)
    assert abs(center_y - target) <= 2, (path, center_y)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("nets", type=Path)
    parser.add_argument("--png", type=Path)
    args = parser.parse_args()
    for name in SELECTED:
        check_glb(args.nets / name / "rb.glb")
        if args.png:
            check_png(args.png / f"{name}.png")
    print(f"selected={len(SELECTED)} glb_layout=pass"
          + (" png_structure=pass" if args.png else ""))


if __name__ == "__main__":
    main()
