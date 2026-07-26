# For GPT: wiring the paper's data/code links for arXiv

You're assembling the arXiv submission; this note is how to point at
the atlas, the data, and the code so the paper never needs updating
when they do. The DOI numbers below are final (reserved on Zenodo);
they begin resolving when the records are published, which happens no
later than the arXiv announcement — coordinate the date with Peter.

## The one rule: cite concept DOIs, not version DOIs

Zenodo gives every record two DOIs. The *version DOI* is a frozen
snapshot; the *concept DOI* is the permanent umbrella that always
leads to the latest version. Published files can never be edited, but
a "new version" can be published under the same concept DOI at any
time — so a paper citing the concept DOI stays current forever.

- **The Neoplatonic Atlas** (browsable site + per-net database):
  concept DOI **10.5281/zenodo.21367249**
  (version DOI of the release at time of writing: 10.5281/zenodo.21367250)
- **Prime neoplatonic solids** (CLERS lists v = 4..60, Euclidean OBJs
  v = 4..50): concept DOI **10.5281/zenodo.19761389**
  (version DOI at time of writing: 10.5281/zenodo.19761390)

If the paper needs to pin exactly what was analyzed, add one clause
citing the version DOI ("…as archived in version 10.5281/zenodo.21367250"),
but every reader-facing pointer is the concept DOI.

## Three-layer pointers (most current first, most durable last)

1. Live site: https://math.dartmouth.edu/~doyle/docs/atlas/
2. Concept DOIs (above) — survive the death of the Dartmouth URL.
3. Search phrase — the title "Atlas of neoplatonic solids" is the
   fallback of last resort; a sentence inviting the reader to search
   for it survives all link rot.

Suggested data-availability paragraph (adapt freely):

> The atlas of neoplatonic solids is browsable at
> math.dartmouth.edu/~doyle/docs/atlas/ and archived, together with
> its per-net database, at doi:10.5281/zenodo.21367249. The
> underlying census — canonical CLERS lists of all 44,646,598 primes
> with 4 ≤ v ≤ 60 and Euclidean OBJ realizations of all 8,239,684
> primes with v ≤ 50 — is archived at doi:10.5281/zenodo.19761389.
> Should these links rot, searching for "Atlas of neoplatonic
> solids" will find the current copy.

## arXiv mechanics — hard constraints, verified against arXiv docs

- **Ancillary files cannot be your update channel.** They are stored
  with a specific paper version and "cannot be changed independently
  from the article" — updating them means submitting a new version of
  the paper. Anything that will evolve lives behind the concept DOI
  or the live URL, never in `anc/`.
- Ancillary files only work with TeX-source submissions (not
  PDF-only). A few static exemplars in `anc/` are fine if wanted, but
  unnecessary — Zenodo carries the corpus.
- The only arXiv metadata editable without generating a new paper
  version: journal-ref, DOI, report-number — and the DOI field is
  reserved for the journal version of the article itself. Do not put
  Zenodo DOIs there; they belong in the paper text and bibliography.

## Bibliography entries

```bibtex
@misc{neoplatonic-atlas,
  author    = {Doyle, Peter and Ellison, Matthew},
  title     = {The Neoplatonic Atlas},
  publisher = {Zenodo},
  year      = {2026},
  doi       = {10.5281/zenodo.21367249},
  note      = {Interactive atlas and per-net database; live copy at
               \url{https://math.dartmouth.edu/~doyle/docs/atlas/}}
}

@misc{neoplatonic-primes,
  author    = {Doyle, Peter},
  title     = {Prime neoplatonic solids: lists ($v = 4$ to $60$) and
               Euclidean OBJs ($v = 4$ to $50$)},
  publisher = {Zenodo},
  year      = {2026},
  doi       = {10.5281/zenodo.19761389}
}
```

## Code availability (one line, if wanted)

All code is public under MIT: the atlas repository
(github.com/peterdoyle1717/neoplatonic-atlas) regenerates the entire
site byte-for-byte from its committed data (`./regen_personal.sh`;
python3 + numpy + a C compiler — no solver runs at build); the solver
is github.com/peterdoyle1717/bendprover, canonical CLERS naming
github.com/peterdoyle1717/clers, and the prime enumeration +
existence-certification pipeline github.com/peterdoyle1717/undented.

## Numbers safe to state (all checked against the registered census)

- 2,251 nets in the atlas at this refresh.
- 44,646,598 primes with 4 ≤ v ≤ 60 (per-v counts and sha256
  checksums in the corpus MANIFEST).
- 8,239,684 primes with v ≤ 50 (the range covered by the OBJ
  tarballs), consistent with the same MANIFEST.

## Coordination with Peter

The Zenodo records are staged as drafts, one button from publish.
Publishing is Peter's click, timed to the arXiv submission — the
concept DOIs above resolve from that moment on. Nothing in the paper
needs to change when the atlas later updates: new Zenodo versions
land under the same concept DOIs.
