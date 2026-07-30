# G1 spec: all and only Euclidean ELT symmetry types

1. **Exact classification and ordering.**  A Euclidean 6-net is a
   triangulated sphere with every vertex degree at most 6.  Duality turns it
   into a cubic polyhedral graph whose face sizes are 3, 4, 5, or 6.  Use the
   complete point-group classification of Deza, Dutour Sikirić, and Fowler,
   “The symmetries of cubic polyhedral graphs with face size no larger than
   6,” MATCH 61 (2009), Theorems 2.1 and 2.2.  In Conway notation its union is
   exactly the following 33 symbols:

   ```
   *532 532  *432 432  *332 3*2 332
   *622 *522 *422 *322 *222
   2*6 2*5 2*4 2*3 2*2
   622 522 422 322 222
   *33 *22 *
   3* 2*
   33 22 1
   3x 2x x
   ```

   The rows follow Conway and Huson's finite-sphere families, with `x`
   patterns moved to the end by Peter's ruling.  `*55` and `55` are not in
   the classification and must not appear.

2. **Representatives and stored-data convention.**  Join
   `data/symmetry.tsv`, `data/conway.tsv`, and
   `data/atlas_records.jsonl` by atlas id, discard records with
   `maxdeg > 6`, and choose the minimum `(v, name)` record for each symbol.
   Four missing or incorrectly represented symbols are supplied by these
   canonical CLERS records:

   ```
   3*  v24CCCACCACACCACACCACACACCACACACCACACADABCAAEAE
   422 v26CCCACCCACCACCACACCACACACACACACAACACAACAACAAACAAE
   3x  v36CCCCACCACCACCACCACACCACACACACCAACACACACCACACAACACCAACAACACCAAAABABAE
   3*2 v48CCCCACCACCACCACCACACCACACCACACCACACCACACACCACACACCAACACCAAACCACAACACCAAACACDEACDECADEACDEAAE
   ```

   They become ordinary atlas records and personal pages, not gallery-only
   exceptions.  For `v > 30`, the established personal-page policy omits
   morphs.  Such a record may therefore persist a hero-only bend store with
   an empty `morph` list iff `v > MORPH_VMAX`; consumer mode must reject an
   empty morph list at or below that cutoff.

3. **Strongest validation invariant.**  The executable checker independently
   decodes all four supplemental CLERS names and recomputes their Conway
   symbols, automorphism orders, reflection flags, vertex counts, face counts,
   and maximum degrees.  The final page must contain exactly 33 distinct
   symbols and 33 distinct ids, in the frozen order above; every chosen record
   has `maxdeg <= 6`; every existing Euclidean atlas symbol is in the frozen
   set; and each chosen record is the minimum `(v, name)` candidate after the
   four records are added.

4. **Failure modes caught.**  These invariants catch accidental retention of
   `*55` or `55`, omission of `3*`, `3x`, `3*2`, or the Euclidean `422`,
   duplicate types or representatives, a hyperbolic representative, a
   misdecoded supplemental CLERS name, an incorrect Conway label, and a
   hero-only store below the morph cutoff.  Triangle winding remains an input
   invariant.  No signed-volume check, winding validation, or orientation
   correction is introduced.

5. **Files and exact checks.**  Edit `builders/elt_symmetry.py`,
   `builders/personal.py`, `data/nets_pages.txt`, generated atlas metadata,
   bend stores, and `HANDOFF.md`.  Run
   `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
   notes/elt-symmetry-euclidean-g1-check.py`, build the four personal pages
   and the gallery, rerun the checker against the built data, assert 33 tiles
   and 33 links, verify every local target exists, deploy to gauss, and
   compare local and deployed hashes.

Primary classification:
https://match.pmf.kg.ac.rs/electronic_versions/Match61/n3/match61n3_589-602.pdf
