Audit the proposed ELT symmetry-representative selection before
implementation. Return PASS or BLOCK, followed by required corrections.
Check the class key, representative ordering, validation invariant, and
compliance with the atlas triangle-winding rule.

Inputs:
- notes/elt-symmetry-g1-spec.md
- output of notes/elt-symmetry-g1-check.py
- the symmetry-gallery block in builders/special.py
- HANDOFF.md

Do not propose signed-volume checks, winding validation, or orientation
correction.
