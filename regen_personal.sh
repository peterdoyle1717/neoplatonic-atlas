#!/bin/bash
# Regenerate the personal pages from scratch. Everything is derived from
# builders/ + data/nets_v4_14.txt; solver binaries are built if missing.
# set -e: any failing step ABORTS the regen (G2 2026-07-22: personal.py
# exits nonzero on a failed net -- BUILD-FAIL/dented hero -- and that
# signal must stop the pipeline, not roll into special.py).
set -euo pipefail
cd "$(dirname "$0")"
# neo is a sibling of atlas since the 2026-07-21 move (was the parent);
# override with NEO_SRC. PYTHON must have numpy/scipy (bare python3 on this
# box is 3.14 without them; the builders run under 3.13).
NEO="${NEO_SRC:-$(cd .. && pwd)/neo}"
PYTHON="${PYTHON:-python3.13}"

# preflight BEFORE the destructive rm: wrong interpreter or missing
# toolchain must fail while the built site is still intact
"$PYTHON" -c 'import numpy, scipy' || {
    echo "FATAL: $PYTHON lacks numpy/scipy -- set PYTHON" >&2; exit 1; }
[ -x "$NEO/bendprover/csrc/euclid_lm_mp" ] || make -C "$NEO/bendprover/csrc" euclid_lm_mp
[ -x builders/horoz_c ] || cc -O2 -o builders/horoz_c builders/horoz_c.c -lm

/bin/rm -rf site/personal
# classification sweep (from neo/data/objs, ~2 min) and the page-worthy
# list; then records+artifacts+pages; then galleries/by-v/front.
# fetch_dents.py removed 2026-07-22: its dent_v GLBs are consumed by
# nothing (the dented gallery reads committed data/walks), and a dead
# network step must not be an abort vector under set -e.
"$PYTHON" builders/classify.py
"$PYTHON" builders/members.py
"$PYTHON" builders/personal.py
"$PYTHON" builders/symmetry.py
"$PYTHON" builders/special.py
