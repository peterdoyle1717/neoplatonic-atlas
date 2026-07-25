# The Neoplatonic Atlas — builders and database

Builders and per-net database for the Neoplatonic Atlas:
unit-equilateral-triangle polyhedra (6-nets), their ideal and
hyperbolic forms, Eisenstein subdivision families, classifications,
Conway symmetry symbols, and themed galleries. Browsable at
https://math.dartmouth.edu/~doyle/docs/atlas/.

The built site and the standalone database are packaged for a Zenodo
record with reserved doi:10.5281/zenodo.21367250 —
`neoplatonic-atlas.tar.gz` is the self-contained browsable site,
`neoplatonic-atlas-database.tar.gz` the records and census tables
alone. The site is one presentation of the database; anyone can build
another.

## Layout

- `builders/` — the pipeline: `personal.py` (per-net records and
  GLB/morph artifacts from the committed bend store `data/bends/`;
  the solver is never invoked at build), `views.py` (record → page),
  `classify.py`, `members.py`, `symmetry.py`, `conway.py`,
  `eisenmap.py`, `classics.py`, `special.py` (flags, names,
  galleries, front page), `zenodo_dist.sh` (packaging).
- `data/` — census-level tables the records are stamped from
  (classification over all 79,349 primes v ≤ 30, symmetry, Conway
  symbols, Eisenstein lattices, recognized angles, neoplatonized
  classics), plus `atlas_records.jsonl`, the aggregated per-net
  database.
- `site/` (untracked) — generated output of `./regen_personal.sh`.

Regeneration: `./regen_personal.sh` rebuilds `site/` wholesale from
the committed data — this repo alone, python3 with numpy plus a C
compiler; deterministic (build twice, diff empty). Producer runs
that refresh the committed census live in `producer_census.sh`
(classify/members/symmetry; needs scipy and the solver tree):
solving uses bendprover (github.com/peterdoyle1717/bendprover),
canonical CLERS naming uses clers
(github.com/peterdoyle1717/clers). Eisenstein subdivision uses
Adrian Rossiter's Antiprism (www.antiprism.com): every row of
`data/subdiv_base.tsv` / `data/subdiv_extra.tsv` is reproducible by
`builders/gen_ray.py BASE a,b` (BASE an Antiprism builtin like `tet`
or any .obj/.off realization of the base net). The ideal-net
placement tool is vendored (`builders/horoz_c.c`; built by
`regen_personal.sh`).
