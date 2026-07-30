# G2 exact staged-tree review — Atlax audit closure

Do not edit files. Review the exact staged tree as a corrective follow-up to
commit `f7ec05a`.

Read:

- `.session/claude-commit-evidence.md`
- `git diff --cached`
- `notes/atlax-gallery-contract-g1-spec.md`
- `notes/atlax-gallery-contract-g1-check.py`
- `notes/atlax-gallery-contract-g1-check.out`
- `notes/codex-consults/2026-07-30-atlax-gallery-contract-g1.jsonl`
- `notes/codex-consults/2026-07-30-150252-codex-gate-7c5e4211af34f755a8cfdc5ba0a63da4d1510227.txt`

Verify:

- the new G1 PASS directly resolves both missing approvals named by the
  prior gate;
- the ELT still checker now derives exactly the builder's current 20 ids;
- ordered gallery links and GLB sources are checked against that selection;
- existing two-primitive GLB checks remain active;
- the measured output corresponds to the corrected checker;
- this follow-up changes no production site behavior or orientation
  convention.

Return `PASS`, `WARN`, or `BLOCK` with concrete evidence.
