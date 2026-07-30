#!/usr/bin/env python3
"""Cross-check the actual all-v10, ELT-paper, and symmetry gallery contracts."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
BUILDERS = os.path.join(TOP, "builders")
SITE = os.path.join(TOP, "site", "personal")
sys.path[:0] = [BUILDERS, HERE]

from all_v10 import load_census, validate
from elt_paper import selection
from views import net_id

legacy_spec = importlib.util.spec_from_file_location(
    "elt_stills_g1_check",
    os.path.join(HERE, "elt-stills-g1-check.py"),
)
legacy = importlib.util.module_from_spec(legacy_spec)
legacy_spec.loader.exec_module(legacy)
LEGACY_SELECTED = legacy.SELECTED
check_glb = legacy.check_glb


def ids_from_selection():
    rows = [row for _, group in selection() for row in group]
    return [
        row.get("id", net_id(row["v"], row["name"]))
        for row in rows
    ]


def records():
    path = os.path.join(TOP, "data", "atlas_records.jsonl")
    return {
        record["id"]: record
        for record in (
            json.loads(line) for line in open(path) if line.strip()
        )
    }


def all_v10_contract(by_id):
    census = load_census()
    validate(census)
    expected = [f'v{row["v"]}{row["name"]}' for row in census]
    page = open(os.path.join(SITE, "gallery", "all-v10.html")).read()
    links = re.findall(r'href="\.\./nets/([^/]+)/"', page)
    sources = re.findall(r'src="\.\./nets/([^/]+)/rb\.glb"', page)
    assert len(expected) == len(set(expected)) == 64
    assert set(links) == set(expected)
    assert set(sources) == set(expected)
    assert len(links) == len(sources) == 64
    for nid in expected:
        record = by_id[nid]
        netdir = os.path.join(SITE, "nets", nid)
        ordinary = json.load(open(os.path.join(netdir, "net.json")))
        assert ordinary["id"] == record["id"] == nid
        assert record["artifacts"]["rb"]
        assert os.path.isfile(os.path.join(netdir, "rb.glb"))
        assert os.path.isfile(os.path.join(netdir, "index.html"))
    print("all-v10 census=64 records=64 links=64 rb=64 pass")


def elt_contract():
    expected = ids_from_selection()
    page = open(os.path.join(SITE, "gallery", "elt-paper.html")).read()
    links = re.findall(r'class=still href="\.\./nets/([^/]+)/"', page)
    sources = re.findall(r'data-file="nets/([^/]+)/rb\.glb"', page)
    assert len(expected) == len(set(expected)) == 20
    assert links == sources == expected
    assert page.count("static=1&capture=1") == 1
    assert "&azimuth=0&elevation=35" in page
    assert "activeCapture.frame.remove()" in page
    for nid in expected:
        check_glb(Path(SITE, "nets", nid, "rb.glb"))
    missing = sorted(set(expected) - set(LEGACY_SELECTED))
    extra = sorted(set(LEGACY_SELECTED) - set(expected))
    print("elt-paper selection=20 links=20 rb=20 camera=(0,35) pass")
    print("legacy_missing=" + ",".join(missing))
    print("legacy_extra=" + ",".join(extra))
    return not missing and not extra


def symmetry_contract():
    command = [sys.executable,
               os.path.join(HERE, "elt-symmetry-euclidean-g1-check.py")]
    measured = subprocess.run(command, check=True, capture_output=True).stdout
    expected = open(
        os.path.join(HERE, "elt-symmetry-euclidean-g1-check.out"), "rb"
    ).read()
    assert measured == expected
    print("symmetry types=33 corrections=3 output=exact pass")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-legacy-current", action="store_true")
    args = parser.parse_args()
    by_id = records()
    all_v10_contract(by_id)
    legacy_current = elt_contract()
    symmetry_contract()
    if args.require_legacy_current:
        assert legacy_current, "legacy still checker selection is stale"
    print("actual_contracts=pass legacy_current="
          + str(legacy_current).lower())


if __name__ == "__main__":
    main()
