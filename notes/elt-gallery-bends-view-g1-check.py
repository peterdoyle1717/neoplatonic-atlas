#!/usr/bin/env python3
"""Check the bend-count partition and shared-camera formula."""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "builders"))
from elt_paper import selection


TOP = Path(__file__).resolve().parents[1]
TOL = 1e-6
AZIMUTH = 0.0
ELEVATION = 35.0


def camera_unit(azimuth, elevation):
    a = math.radians(azimuth)
    e = math.radians(elevation)
    return (
        math.cos(e) * math.sin(a),
        math.sin(e),
        math.cos(e) * math.cos(a),
    )


rows = [row for _, group in selection() for row in group]
assert len(rows) == 20
for row in rows:
    nid = row.get("id", f"v{row['v']}{row['name']}")
    record = json.loads((TOP / "data" / "bends" / f"{nid}.json").read_text())
    bends = list(record["hero"].values())
    assert bends and all(math.isfinite(bend) for bend in bends)
    positive = sum(bend > TOL for bend in bends)
    zero = sum(abs(bend) <= TOL for bend in bends)
    negative = sum(bend < -TOL for bend in bends)
    assert positive + zero + negative == len(bends) == 3 * row["v"] - 6
    print(f"{nid} (+{positive},0{zero},-{negative})")

camera = camera_unit(AZIMUTH, ELEVATION)
assert abs(sum(value * value for value in camera) - 1.0) < 1e-15
assert camera[1] > 0
print(
    f"selected={len(rows)} bend_partition=pass "
    f"camera=({AZIMUTH:g},{ELEVATION:g}) unit=pass"
)
