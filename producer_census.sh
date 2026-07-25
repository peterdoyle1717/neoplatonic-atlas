#!/bin/bash
# PRODUCER census sweep: regenerate the committed classification/census
# data (data/class_v30.tsv, data/nets_pages.txt, data/eisenstein.tsv,
# data/symmetry.tsv). Run ONLY when the census or classification
# changes; outputs are committed data that the consumer regen
# (regen_personal.sh) reads. Requires the neo tree (data/objs) and an
# interpreter with numpy AND scipy (scipy 1.18.0 installed for
# python3.13 on 2026-07-24).
# TESTED 2026-07-24 (python3.13 + scipy 1.18.0): runs clean end-to-end.
# HISTORICAL (pre-fix) measurement from that test: 67 floppy flags
# flipped 1->0 because neo's trash-sweep had removed the flopper list
# and classify silently defaulted it empty; 9 page-worthy nets dropped
# as a consequence; ~3.1k rows reordered by unsorted output. Those
# faults are FIXED: the flopper census is pinned (data/floppers.txt,
# hard-fail if missing) and output is sorted. Remaining EXPECTED drift
# on a rerun: value columns if neo/data/objs changes, symmetry rows
# completing over newly built records, and page-worthy consequences.
# A census refresh is an EDITORIAL act: run attended, diff against the
# committed tsvs, and commit deliberately -- never as a silent step.
set -euo pipefail
cd "$(dirname "$0")"
NEO="${NEO_SRC:-$(cd .. && pwd)/neo}"
PYTHON="${PYTHON:-python3.13}"

"$PYTHON" -c 'import numpy, scipy' || {
    echo "FATAL: $PYTHON lacks numpy/scipy -- set PYTHON" >&2; exit 1; }
[ -d "$NEO/data/objs" ] || {
    echo "FATAL: $NEO/data/objs missing (classify input)" >&2; exit 1; }

"$PYTHON" builders/classify.py     # census classification sweep (neo objs)
"$PYTHON" builders/members.py      # page-worthy list + eisenstein relations
"$PYTHON" builders/symmetry.py     # automorphism census over built records
