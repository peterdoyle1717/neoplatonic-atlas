#!/bin/bash
# Regenerate the personal pages from scratch. Everything is derived from
# builders/ + data/nets_v4_14.txt; solver binaries are built if missing.
set -u
cd "$(dirname "$0")"
NEO="$(cd .. && pwd)"

[ -x "$NEO/bendprover/csrc/euclid_lm_mp" ] || make -C "$NEO/bendprover/csrc" euclid_lm_mp
[ -x "$NEO/ideal/src/horoz_c" ] || make -C "$NEO/ideal" src/horoz_c

/bin/rm -rf site/personal
python3 builders/personal.py
# hull-buried exemplars (v=17..24) + front page + special pages
python3 builders/personal.py data/nets_buried_old.txt
python3 builders/special.py
