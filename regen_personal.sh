#!/bin/bash
# Regenerate the personal pages from scratch. Everything is derived from
# builders/ + data/nets_v4_14.txt; solver binaries are built if missing.
set -u
cd "$(dirname "$0")"
NEO="$(cd .. && pwd)"

[ -x "$NEO/bendprover/csrc/euclid_lm_mp" ] || make -C "$NEO/bendprover/csrc" euclid_lm_mp
[ -x "$NEO/ideal/src/horoz_c" ] || make -C "$NEO/ideal" src/horoz_c

/bin/rm -rf site/personal
# classification sweep (from neo/data/objs, ~2 min) and the page-worthy
# list; then records+artifacts+pages; then galleries/by-v/front
python3 builders/classify.py
python3 builders/members.py
python3 builders/personal.py
python3 builders/special.py
