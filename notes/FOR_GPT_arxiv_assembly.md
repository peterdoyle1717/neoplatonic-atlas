# For GPT: wiring the paper's data/code links for arXiv

Final architecture (PD-approved 2026-07-26): the paper carries NO
Zenodo DOI for the atlas — it cites the atlas by a `\seek` reference
to the front page, and the front page maintains the durable pointers
(Zenodo, GitHub, companion records). The proof software is cited by
its FROZEN version DOI, because that identifies the exact evidence
used.

STATUS UPDATE 2026-07-31: all three records were PUBLISHED on
2026-07-28 — every DOI below resolves NOW. The software record
additionally carries nonprime-v50-certificates-20260727.tar.gz
(attachment generator, two independent MPFI embeddedness checkers,
the complete 2,172,511-case primary run, exact rational construction
checks), so 10.5281/zenodo.21609862 is citable for the prime AND
non-prime v ≤ 50 proofs; its bibtex note can say so if the paper
wants.

## The two bibliography entries, blanks filled

```bibtex
@misc{euclidean:software,
  author       = {Doyle, Peter},
  title        = {Software for the computer-assisted proof of
                  Euclidean neoplatonic realizations},
  year         = {2026},
  howpublished = {Zenodo,
                  \url{https://doi.org/10.5281/zenodo.21609862}},
  note         = {Software for prime $6$-nets with $v \leq 50$}
}

@misc{atlas,
  key  = {Atlas},
  note = {\seek{Atlas of neoplatonic solids}{https://math.dartmouth.edu/~doyle/docs/atlas/}}
}
```

10.5281/zenodo.21609862 is the frozen version DOI of the software
record (snapshot of github.com/peterdoyle1717/undented at git
145d94d: enumeration + the rigorous IEEE-754 existence prover
applying Ellison's theorem, arXiv:2312.05376). It is a VERSION DOI by
design — do not swap in the concept DOI (10.5281/zenodo.21609861);
the paper pins the exact software. Author list matches the Zenodo
record (Doyle); if Peter changes the record's creators, mirror it
here.

## What the atlas front page now carries (so the paper doesn't have to)

https://math.dartmouth.edu/~doyle/docs/atlas/ has an "Archives &
code" line: the atlas's own concept DOI (10.5281/zenodo.21367249),
the prime census concept DOI (10.5281/zenodo.19761389), the proof
software's frozen DOI (above), and the GitHub repository. The
archived site tarball on Zenodo contains the same front page, so the
Zenodo copy is self-describing. Future atlas updates become new
Zenodo versions under the same concept DOI — nothing in the paper
ever changes.

## arXiv mechanics — hard constraints, verified against arXiv docs

- Ancillary files are stored with a specific paper version and
  "cannot be changed independently from the article" — they are not
  an update channel. Anything that evolves lives behind the atlas
  front page / concept DOIs, never in `anc/`.
- Ancillary files only work with TeX-source submissions. A few static
  exemplars are fine if wanted, but unnecessary — Zenodo carries the
  corpus.
- The only arXiv metadata editable without a new paper version:
  journal-ref, DOI, report-number — and that DOI field is for the
  journal version of the article itself. Zenodo DOIs go in the
  bibliography only.

## Numbers safe to state (checked against the registered census)

- 2,251 nets in the atlas at this refresh.
- 44,646,598 primes with 4 ≤ v ≤ 60 (per-v counts and sha256
  checksums in the corpus MANIFEST).
- 8,239,684 primes with v ≤ 50 — the range covered by the Euclidean
  OBJ tarballs and by the proof software's certification.

## The staged Zenodo records (all drafts, all cc-zero, publish = Peter)

- 21367250 The Neoplatonic Atlas (site + database) — concept DOI
  10.5281/zenodo.21367249.
- 19761390 Prime neoplatonic solids: lists v = 4..60, OBJs v = 4..50
  — concept DOI 10.5281/zenodo.19761389.
- 21609862 proof software (undented @ 145d94d) — cited by this
  version DOI; concept 10.5281/zenodo.21609861 exists but stays out
  of the paper.
