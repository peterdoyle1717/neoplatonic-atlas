#!/bin/bash
# CONSUMER regen: rebuild site/personal from committed data, wholesale.
# No solver, no neo, no network, no scipy -- reads data/bends (committed
# bend store), data/*.tsv (committed classification/census outputs),
# data/walks (dent-walk scan). Deterministic: build twice, diff empty.
# Producer-tier steps (classify/members/symmetry -- solver sweeps and
# census classification that WRITE committed data) live in
# producer_census.sh and run only when the census changes.
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3.13}"

# preflight BEFORE the destructive rm: wrong interpreter must fail
# while the built site is still intact (consumer needs numpy only)
"$PYTHON" -c 'import numpy' || {
    echo "FATAL: $PYTHON lacks numpy -- set PYTHON" >&2; exit 1; }
[ -x builders/horoz_c ] || cc -O2 -o builders/horoz_c builders/horoz_c.c -lm

/bin/rm -rf site/personal
"$PYTHON" builders/personal.py     # records + gated artifacts + pages
"$PYTHON" builders/special.py      # stamps, galleries, by-v, front, eismaps
"$PYTHON" builders/aggregate_records.py # aggregate stamped personal-page records
"$PYTHON" builders/elt_paper.py    # ELT still gallery
"$PYTHON" builders/elt_symmetry.py # one ELT example per symmetry type
