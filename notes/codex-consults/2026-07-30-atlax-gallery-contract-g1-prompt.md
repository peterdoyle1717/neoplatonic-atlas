# G1 revise-and-resubmit — actual Atlax gallery contracts

Do not edit files. Audit the actual evolved gallery contracts and the planned
checker correction. End with `PASS`, `WARN`, or `BLOCK`.

Read in full:

- `HANDOFF.md`
- `notes/atlax-gallery-contract-g1-spec.md`
- `notes/atlax-gallery-contract-g1-check.py`
- `notes/atlax-gallery-contract-g1-check.out`
- `builders/all_v10.py`
- `builders/elt_paper.py`
- `builders/elt_symmetry.py`
- `builders/personal.py`
- `regen_personal.sh`
- `notes/elt-stills-g1-check.py`
- `notes/elt-symmetry-euclidean-g1-check.py`
- `notes/elt-symmetry-euclidean-g1-check.out`
- `notes/codex-consults/2026-07-29-all-v10-g1-pass.jsonl`
- `notes/codex-consults/2026-07-30-elt-symmetry-euclidean-g1-attempt4.jsonl`
- `notes/codex-consults/2026-07-30-150252-codex-gate-7c5e4211af34f755a8cfdc5ba0a63da4d1510227.txt`

The post-commit gate found two missing G1 approvals and one real coverage
gap. This resubmission addresses all three:

1. The all-v10 census itself is unchanged from the prior PASS. After the
   missing 28 ordinary records were generated, Peter required normal personal
   pages and GLB thumbnails. Audit that evolved display/link contract.
2. The prior symmetry BLOCK confirmed the 33-type catalog but required three
   verification corrections. Audit the now-passing checker and implementation
   of those exact corrections.
3. The legacy ELT still checker copied an obsolete selection. The measured
   output names the five missing and five extra ids. Audit the proposed change
   to derive `SELECTED` directly from `elt_paper.selection()` and require the
   exact current gallery/link/source equality.

Stored triangle winding remains an input invariant. No signed-volume
orientation check or correction is proposed.
