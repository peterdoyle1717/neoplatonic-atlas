# The Neoplatonic Atlas — builders and database

Builders and per-net database for the Neoplatonic Atlas:
unit-equilateral-triangle polyhedra (6-nets), their ideal and
hyperbolic forms, Eisenstein subdivision families, classifications,
Conway symmetry symbols, and themed galleries.

The built site and the standalone database are archived on Zenodo at
doi:10.5281/zenodo.21367250 — `neoplatonic-atlas.tar.gz` is the
self-contained browsable site, `neoplatonic-atlas-database.tar.gz`
the records and census tables alone. The site is one presentation of
the database; anyone can build another.

## Layout

- `builders/` — the pipeline: `personal.py` (per-net records and
  GLB/morph artifacts, solving via bendprover), `views.py` (record →
  page), `classify.py`, `members.py`, `symmetry.py`, `conway.py`,
  `eisenmap.py`, `classics.py`, `special.py` (flags, names,
  galleries, front page), `zenodo_dist.sh` (packaging).
- `data/` — census-level tables the records are stamped from
  (classification over all 79,349 primes v ≤ 30, symmetry, Conway
  symbols, Eisenstein lattices, recognized angles, neoplatonized
  classics), plus `atlas_records.jsonl`, the aggregated per-net
  database.
- `site/` (untracked) — generated output; see the Zenodo record.

Regeneration chain: `classify → members → personal → fetch_dents →
symmetry → special`; `views.py` re-renders every page from the
records. Solving uses bendprover
(github.com/peterdoyle1717/bendprover). Eisenstein subdivision uses
Adrian Rossiter's Antiprism (www.antiprism.com).
