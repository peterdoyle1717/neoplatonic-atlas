# G1 spec: ELT symmetry representatives

1. **Selection formula.**  Join committed `data/symmetry.tsv`,
   `data/conway.tsv`, and `data/atlas_records.jsonl` by atlas id.  Include
   every atlas record, Euclidean or hyperbolic.  A symmetry type is the
   existing atlas key `(group order, has reflections, Conway symbol)`.  For
   each key choose the minimum record under `(v, name)`.

2. **Order and labels.**  Follow Conway and Huson's Table III: the
   exceptional types `*532,532; *432,432; *332,3*2,332`, followed by the
   series `*22n, 2*n, 22n, *nn, n*, nx, nn`.  Specialize this to the
   symbols represented in the atlas, with decreasing `n` inside each
   series; because low-parameter series overlap, show each symbol once.
   Per Peter's ruling, move the two represented `x` symbols to the very
   end.  `3*2` has no atlas example and therefore no tile.
   Show the Conway symbol, group order, vertex count, and the first common
   name when one is stored.  Never show the CLERS name on the gallery.

3. **Strongest invariant.**  The page contains exactly one representative
   for every symmetry key in the committed census; selected ids and
   keys are both unique, and each representative equals the computed minimum
   for its class.  Every still links to that record's personal page.

4. **Failure modes caught.**  The checks catch missing joins, accidental
   exclusion of hyperbolic types, duplicate or omitted symmetry types, a
   non-minimal representative, exposed CLERS labels, and broken personal-page
   links.  Stored coordinates and triangle winding remain input invariants;
   the page performs no orientation or signed-volume operation.

5. **Files and checks.**  Add `builders/elt_symmetry.py`; call it from
   `regen_personal.sh`; link it from the ELT page and atlas front page; update
   `HANDOFF.md`.  Run the selection checker, build the page, verify the type
   and link counts, check every deployed target on gauss, and compare
   deployed bytes with the built files.

Primary ordering source: John H. Conway and Daniel H. Huson, “The Orbifold
Notation for Two-Dimensional Groups,” Table III (2002).
