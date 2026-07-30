G1 DESIGN AUDIT. Do not edit files. Audit the proposed GLB-to-PNG still
rendering convention for the ELT-paper atlas gallery. End with exactly one
verdict token on its own line: PASS, WARN, or BLOCK.

Read in full:

- `HANDOFF.md`
- `notes/elt-stills-g1-spec.md`
- `notes/elt-stills-g1-check.py`
- `notes/elt-stills-g1-check.out`
- `builders/elt_paper.py`
- `builders/all_v10.py`

The user wants a non-interactive 4-by-5 page of still images, approximately
matching the attached screenshot's current model-viewer views, with comparable
apparent sizes. Each still remains a link to its atlas personal page. The
published `rb.glb` files have been measured: all 20 selected assets have one
mesh with exactly two indexed triangle primitives, material 0 for red faces
and material 1 for black edge geometry; the preflight output is included.

Check specifically:

1. whether the stated fixed-camera basis and orthographic projection are
   internally consistent with the intended `0deg 100deg auto` approximate
   view;
2. whether projected-bounds normalization is an appropriate convention for
   visually comparable thumbnail sizes;
3. whether the validation invariant is strong enough to prevent clipping,
   malformed output, or accidental loss of the still-page requirement;
4. whether the spec respects the input triangle winding invariant and avoids
   any signed-volume orientation logic; and
5. whether implementation may proceed.

A BLOCK must name a concrete defect and the required correction.
