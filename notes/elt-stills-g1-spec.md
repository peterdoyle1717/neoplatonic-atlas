# G1 spec: ELT-paper still thumbnails

1. **Rendering formulas.**  Each still is rendered directly from the two
   triangle primitives in its published `rb.glb`.  Let the stored position be
   \(p\), the arithmetic mean of all positions be \(c\), and \(q=p-c\).
   For each model use the exact \((\theta,\phi)\) pair stored in
   `builders/render_elt_stills.py::ORBITS`, tuned against its position in
   Peter's reference screenshot.  The target-to-camera unit vector is
   \(d=(\sin\phi\sin\theta,\cos\phi,-\sin\phi\cos\theta)\), using
   model-viewer's zero-azimuth convention on the negative z axis.
   With world-up \(u_0=(0,1,0)\), screen-right is
   \(r=\operatorname{normalize}(u_0\times d)\) and screen-up is
   \(u=d\times r\).  Orthographic screen coordinates are
   \(x=q\cdot r,\ y=q\cdot u\); depth is \(z=q\cdot d\).
   Translate and uniformly scale the projected bounding box to occupy 72% of
   a square image.  Rasterize with a depth buffer at 3x resolution and box
   downsample.  Face color is red with flat directional shading; the second
   GLB material (the established black edge geometry) is rendered black.

2. **Coordinates and orientation.**  Stored GLB coordinates and triangle
   winding are input invariants.  The renderer performs no orientation check
   or correction and never computes signed volume.  The per-model cameras
   preserve approximately the views in Peter's screenshot.  Uniform
   projected-bounds scaling, rather than geometric rescaling, makes the
   apparent sizes comparable.

3. **Strongest validation invariant.**  For every one of the 20 selected
   records: the GLB has exactly two indexed triangle primitives using material
   0 (faces) and material 1 (edges); all position and index values are finite
   and in range; the projected span is nonzero; the PNG decodes structurally;
   its non-white bounding box is centered within 2 pixels and occupies
   70--74% of the image in its larger dimension.  The HTML must contain 20
   linked `<img>` stills, no `<model-viewer>`, and 20 atlas-page links.

4. **Failure modes caught.**  The checks catch missing/corrupt assets, a
   changed GLB primitive/material layout, invalid geometry, a degenerate
   camera projection, clipping or inconsistent apparent scale, malformed
   PNG output, accidental interactive thumbnails, missing links, and an
   incorrect selection count.

5. **Files and exact checks.**  Add `builders/render_elt_stills.py`; change
   `builders/elt_paper.py`; deploy `gallery/elt-paper.html` and
   `gallery/elt-stills/*.png`.  Before implementation:
   `python3.13 notes/elt-stills-g1-check.py /tmp/atlax-preview.HkhLwV/nets`.
   After implementation:
   `python3.13 builders/render_elt_stills.py --nets
   /tmp/atlax-preview.HkhLwV/nets --out
   /tmp/atlax-pages.ezRJsB/gallery/elt-stills`;
   `python3.13 notes/elt-stills-g1-check.py
   /tmp/atlax-preview.HkhLwV/nets --png
   /tmp/atlax-pages.ezRJsB/gallery/elt-stills`;
   `python3.13 builders/elt_paper.py /tmp/atlax-pages.ezRJsB`;
   then HTML count checks, `git diff --check`, `py_compile`, remote
   file/link checks, and HTTP 200 checks.
