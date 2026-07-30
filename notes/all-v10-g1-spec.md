# G1 spec: all 6-nets through v=10

1. **Exact set and formulas.**  The new page contains one representative of
   every unoriented isomorphism class of simple sphere triangulations with
   `4 <= V <= 10` and `max(degree) <= 6`.  For each row, `E = 3V - 6` and
   `F = 2V - 4`.  A row is marked prime exactly when every 3-clique is a
   facial triangle; otherwise it is marked non-prime.

2. **Embedding, orientation, and name conventions.**  Census input is
   plantri ASCII code: vertices are `a`, `b`, ... and each neighbor list is
   the clockwise rotation at that vertex.  For every consecutive neighbor
   pair `(b,c)` around `a`, the unoriented face is `{a,b,c}`.  The face list
   is oriented consistently from the rotation system, with no volume-sign
   calculation or orientation correction.  Display identity is the
   `official_unoriented_name` from the frozen `clers` implementation used by
   the atlas.  The committed census stores that name and its decoded
   canonical face list.

3. **Strongest validation invariant.**  Before a row is accepted: the
   rotation system has reciprocal adjacency and gives three cyclically
   agreeing directed occurrences of each face; it yields exactly `2V-4`
   distinct triangular faces; every edge occurs in exactly two faces; the
   face dual is connected; every vertex link is one cycle; the vertex set is
   `1..V`; the edge and face counts satisfy the formulas above;
   `sum(6-degree) = 12`; and the maximum degree is at most 6.  Canonical
   CLERS names are unique, and decoding and canonically re-encoding each name
   gives the same name while satisfying the same sphere invariants.  The
   plantri totals before degree filtering are `1,1,2,5,14,50,233` for
   `V=4..10`.  Existing atlas prime names through v=10 must be exactly the
   prime subset of the census.

4. **Failure modes caught.**  The checks reject a reversed/misread rotation
   list that does not close, inconsistent cyclic face orientation, a missed
   or duplicated face, a disconnected or branching pseudomanifold, a
   degree-7 graph, duplicate isomorphism classes, a CLERS encode/decode
   mismatch, a census command that omits or duplicates plantri classes, and
   disagreement with the atlas's frozen prime census.

5. **Files and exact checks.**  Add `data/nets_all_v4_10.txt` and a small
   builder for `site/personal/gallery/all-v10.html`; call it from the normal
   consumer regeneration and add one front-page gallery link.  The page
   labels its pictures “combinatorial unfoldings” and generates them with
   `clers_tools.clers_svg`; it does not solve geometry, claim foldability, or
   invent Euclidean artifacts or personal-page links for newly included
   non-primes.  The census records the plantri release, clers commit,
   generation command, per-v counts, and canonical-name checksum.  Run the
   census checker; build the page twice and compare hashes; parse every
   generated link/name; serve the deployed `/atlax/` clone and fetch the
   front page and gallery over HTTP.
