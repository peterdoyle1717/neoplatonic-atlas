# G1 spec: ELT bend counts and uniform thumbnail view

1. **Formulas.**  For each selected net, read the committed
   `data/bends/<id>.json` hero map.  With `t = 1e-6`, count
   `positive = #{b > t}`, `zero = #{|b| <= t}`, and
   `negative = #{b < -t}`; display `(+positive, 0zero, -negative)`.
   The tolerance is the atlas's existing
   `builders/personal.py::FLAT_BEND_TOL`.

   Static gallery captures use one camera for all models.  With Y-up GLB
   coordinates, azimuth `a` is measured from +Z toward +X and elevation `e`
   above the XZ plane.  For distance `d`,
   `camera = d (cos(e) sin(a), sin(e), cos(e) cos(a))`, looking at the
   centered model.  The audited search set is
   `a in {0, 30, 45}` degrees and `e in {25, 35, 45}` degrees.  The final
   pair selected from the full 20-model contact sheets is `(0, 35)`
   degrees; it keeps the established azimuth and raises the camera from the
   existing 10-degree elevation.  The same pair is passed to every gallery
   capture.  Personal-page interactive views are unchanged.

2. **Coordinates and orientation.**  GLB coordinates and face winding are
   input invariants.  No signed volume, orientation check, or face reversal
   is permitted.  The shared camera changes only static gallery capture.

3. **Strongest validation invariant.**  For every selected net, the hero
   bend values are finite and the three counts partition the complete edge
   map: `positive + zero + negative = len(hero) = 3v - 6`.  Every still
   capture carries the same audited azimuth/elevation pair.  A rendered
   contact sheet must contain all 20 nonblank thumbnails without clipping.

4. **Failure modes caught.**  The checks catch missing bend records,
   nonfinite bends, omitted or duplicated edges, numerical dust mislabeled
   as a genuine sign, stale hand-entered remarks, mixed per-model cameras,
   pole-singular views, blank captures, and clipping.  They do not pretend
   to turn the subjective choice of the most revealing contact sheet into a
   theorem.

5. **Files and checks.**  Change `builders/elt_paper.py` to derive all bend
   counts from the store; change `builders/assets/turntable.html` to accept
   gallery-only azimuth/elevation parameters; record the result in
   `HANDOFF.md`.  Run:
   `python3.13 notes/elt-gallery-bends-view-g1-check.py`;
   build the 20 selected GLBs from the committed store into a temporary
   preview; render and inspect the nine candidate contact sheets; rebuild
   `builders/elt_paper.py`; verify 20 count triples and one shared camera
   pair; then deploy and compare the public HTML byte-for-byte.

The required `codex exec` audit was attempted twice and could not initialize:
both attempts returned `Operation not permitted` before creating a session.
The full failures are logged under `notes/codex-consults/`.  This continues
the same ELT-stills work for which Peter previously said `proceed` after the
same runner failure.
