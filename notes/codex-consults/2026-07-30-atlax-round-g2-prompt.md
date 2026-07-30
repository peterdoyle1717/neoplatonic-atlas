# Atlax round — G2 exact staged-tree review

Review the exact staged tree in `/Users/doyle/Dropbox/chat/euclid/atlax-source`
as a commit gate.  Do not edit files.

Scope:

- add the complete all-nets-through-v=10 gallery and normal personal
  pages for its missing records;
- add the 20-model ELT paper gallery and static-thumbnail machinery;
- add the 33-type Euclidean Conway-symmetry gallery, including four
  ordinary atlas records needed to complete it;
- make consumer regeneration rebuild the aggregate record database;
- carry the generated census pins and bend stores required by those
  pages.

Read:

- `.session/claude-commit-evidence.md`
- `git diff --cached`
- `HANDOFF.md`
- the G1 specs, checkers, recorded outputs, and consults cited in the
  evidence file.

Check in particular:

- staged files are coherent with the stated scope;
- the four new symmetry examples are normal personal-page records;
- low-v incomplete morph stores are rejected and high-v records cannot
  retain stale morph artifacts;
- the gallery contains all and only the 33 Euclidean degree-at-most-6
  Conway types in the frozen order;
- no code infers or changes triangle orientation from signed volume;
- generated metadata is reproducible from the ordinary personal-page
  records.

Return `PASS`, `WARN`, or `BLOCK`, followed by concrete evidence.  A
`BLOCK` must name a correctness or reproducibility defect in this exact
staged tree.
