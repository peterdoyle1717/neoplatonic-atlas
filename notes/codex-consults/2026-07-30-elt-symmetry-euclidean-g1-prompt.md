Audit the proposed replacement of the ELT symmetry gallery by all and only
symmetry types possible for Euclidean 6-nets. Return PASS or BLOCK, followed
by required corrections.

This is the revise-and-resubmit after thread
019fb430-fa98-7fb1-9bec-18253617124b. The checker now requires the four
supplements to exist in committed metadata, bend stores, and ordinary
personal pages; compares their recomputed symmetry data to the committed
rows; enforces the morph cutoff; and checks the final 33 tiles, ordering,
distinct ids, and local link targets. Its current pre-build failure is
intentional evidence that the previously missing integration is now caught.
Audit the corrected spec and checker before implementation.

Inputs:
- notes/elt-symmetry-euclidean-g1-spec.md
- notes/elt-symmetry-euclidean-g1-check.py
- notes/elt-symmetry-euclidean-g1-check.out
- notes/elt-symmetry-g1-spec.md (the superseded gallery convention)
- builders/conway.py
- builders/personal.py
- builders/elt_symmetry.py
- HANDOFF.md

The classification source is Deza, Dutour Sikirić, and Fowler, “The
symmetries of cubic polyhedral graphs with face size no larger than 6,”
MATCH 61 (2009), Theorems 2.1 and 2.2:
https://match.pmf.kg.ac.rs/electronic_versions/Match61/n3/match61n3_589-602.pdf

Check the exact 33-symbol Conway set and ordering, the four supplemental
representatives, the hero-only store rule above the established morph cutoff,
the validation invariant, and compliance with the atlas triangle-winding
rule. Do not propose signed-volume checks, winding validation, or orientation
correction.
