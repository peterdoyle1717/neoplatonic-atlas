Audit this proposed G1 design before implementation. Return PASS or BLOCK,
then list any required corrections. Focus on the bend-sign convention,
camera coordinates, validation invariant, and whether the plan preserves the
atlas rule that triangle winding is an input invariant.

Inputs:
- notes/elt-gallery-bends-view-g1-spec.md
- output of notes/elt-gallery-bends-view-g1-check.py
- builders/assets/turntable.html
- builders/personal.py lines defining FLAT_BEND_TOL and orientation policy
- builders/elt_paper.py
- HANDOFF.md

Do not propose signed-volume checks, face-winding validation, or automatic
orientation correction.
