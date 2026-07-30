# G1 revise-and-resubmit: actual Atlax gallery contracts

This audit closes the procedural and coverage gaps identified by the
post-commit review of `7c5e4211af34f755a8cfdc5ba0a63da4d1510227`.
It supersedes only the obsolete rendering portions of the earlier specs;
the audited census and Conway classifications are unchanged.

1. **Exact sets and rendering contracts.**

   - `all-v10.html` contains exactly the 64 canonical census rows in
     `data/nets_all_v4_10.txt`.  Every row now has an ordinary personal-page
     record and a certified Euclidean `rb.glb`, so its tile uses that GLB and
     links to the corresponding personal page.  This replaces the earlier
     pre-production plan to show combinatorial CLERS SVGs without links.
   - `elt-paper.html` contains exactly the 20 ids returned by
     `builders/elt_paper.py::selection`.  Each tile starts as an ordinary
     `<img>` whose source is filled by one temporary, sequential
     `turntable.html?static=1&capture=1` iframe.  The common camera is
     azimuth 0 degrees, elevation 35 degrees.  The iframe is removed and its
     WebGL context released before the next capture.
   - `elt-symmetry.html` contains exactly the frozen 33 Euclidean Conway
     types already confirmed by the previous audit.  Its four supplements
     are ordinary personal-page records.

2. **Coordinates, orientation, and identity.**  Canonical unoriented CLERS
   remains the census identity.  Stored GLB coordinates and triangle winding
   are input invariants.  Gallery code does not compute signed volume,
   validate orientation, reverse faces, or correct winding.  The thumbnails
   change only presentation and camera.

3. **Strongest validation invariant.**  The all-v10 checker equates, as
   sets, census ids, aggregate records, ordinary `net.json` ids, gallery
   links, and gallery GLB sources, and checks all 64 `rb` artifact flags and
   files.  The ELT checker derives the current selection from the builder,
   equates it with the 20 gallery links and 20 `data-file` GLB sources, and
   validates the two indexed triangle primitives in every selected `rb.glb`.
   The symmetry checker must reproduce its frozen 33-line output and directly
   test all three corrections requested by the earlier BLOCK: reject an
   incomplete low-v store, reject stale high-v morph files, and parse and
   cross-check each supplement's real `net.json`.

4. **Failure modes caught.**  These checks reject a missing or extra census
   tile, a gallery-specific stub in place of an ordinary record, a stale
   aggregate, missing Euclidean artifacts, stale links or GLB sources after
   an editorial selection change, malformed GLB primitive layout, incomplete
   low-v morph storage, stale high-v morph artifacts, a missing Euclidean
   symmetry type, and any drift from the frozen type order.

5. **Files and exact checks.**  Add
   `notes/atlax-gallery-contract-g1-check.py` and its measured output.  After
   approval, change `notes/elt-stills-g1-check.py` so `SELECTED` is derived
   from `builders/elt_paper.py::selection` rather than a stale copied list.
   Run:

   - `python3.13 notes/atlax-gallery-contract-g1-check.py
     --require-legacy-current`;
   - `python3.13 notes/elt-stills-g1-check.py site/personal/nets`;
   - `python3.13 notes/elt-symmetry-euclidean-g1-check.py | diff -u
     notes/elt-symmetry-euclidean-g1-check.out -`;
   - `python3.13 -m py_compile builders/*.py notes/*-check.py`;
   - `git diff --check`.
