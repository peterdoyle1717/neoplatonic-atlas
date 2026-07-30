G1 REVISE-AND-RESUBMIT. Do not edit files. Audit the revised atlas census
design and checker after your prior BLOCK. End with exactly one verdict token
on its own line: PASS, WARN, or BLOCK.

Read in full:

- `HANDOFF.md`
- `notes/all-v10-g1-spec.md`
- `notes/all-v10-check.py`
- `notes/all-v10-check.out`
- `notes/codex-consults/2026-07-29-all-v10-g1-block.jsonl`
- `data/nets_v4_14.txt`
- `builders/clers_tools.py`
- the relevant gallery/front-page sections of `builders/special.py`

The prior BLOCK named three defects. The revision now:

1. checks reciprocal adjacency and requires the three rotation-system
   occurrences of every face to be the same cyclic orientation;
2. checks connected face duals, single-cycle vertex links, edge incidence,
   Euler counts, degree bound, and `sum(6-degree)=12`; and
3. requires canonical re-encoding equality for both the originating plantri
   faces and the decoded CLERS faces.

Observed revised checker output is in `notes/all-v10-check.out`, including the
canonical-name checksum. The production consumer will read a committed census
file and use `builders/clers_tools.py::clers_svg`; it will not invoke plantri,
external clers, or any geometry solver. Pictures will be labeled
“combinatorial unfoldings”, and newly included rows without atlas records will
not receive personal-page links.

Confirm whether the concrete defects are closed and whether implementation may
proceed. A BLOCK must name a remaining concrete defect and required correction.
