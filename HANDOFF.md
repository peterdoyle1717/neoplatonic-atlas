# Atlas HANDOFF (chat bootstrap)

Pick-up for a fresh atlas chat: read this + `git log --oneline -15`.

## What this is

The personal atlas of neoplatonic solids, record/view architecture:
one directory per net under `site/personal/nets/<id>/` — `net.json`
is the database record (identity, netcode, flags, themes, eisenstein,
artifact inventory) beside its artifacts (rb/clers GLBs, morph_p/k,
ideal_net.svg, clers_layout.svg, eismap.svg, dent_v<k>.glb). id =
`v{V}{CLERS}` when ≤ 200 chars, else `v{V}h`+sha1-16 (`views.net_id`).
Display names always from the record, `v13CC…` style.

## Pipeline (from scratch: `./regen_personal.sh`)

classify.py (79,349 primes v≤30 from neo/data/objs → class_v30.tsv)
→ members.py (page-worthy list + themes.tsv + eisenstein.tsv)
→ personal.py (records + artifacts + pages; solver = bendprover
euclid_lm_mp, MAXV 512) → fetch_dents.py → symmetry.py →
special.py (stamps records; galleries; by-v; front; about; eisenmaps
via eisenmap.py; re-renders all pages via views.py).

views.py is the only place that knows what a net page looks like;
re-render everything in seconds (`python3 builders/views.py`).

Serve: `python3 -m http.server 8765` in ~/Dropbox/neo →
http://localhost:8765/atlas2/personal/

## State (2026-07-14)

2,133 nets built (all primes v≤14; pancake/convex/floppy classes and
8-deepest+depth≥0.1 buried to v≤30; Eisenstein families to v≤164, tet
filled to T≤60 via subdiv.py+Antiprism; old-atlas theme harvests).
16+ galleries incl. symmetry (19 classes). Old-atlas galleries all
carried over with their descriptions (data/theme_desc.tsv).

## Pending

- Recognition sweep (recognize_sweep.py → data/recognized_v30.tsv,
  all-recognized + ≥1 icosahedral-atom criterion v1): if the TSV is
  complete, add members to members.py's page-worthy set, build pages,
  rerun special.py (gallery/recognized.html is pre-wired). PD expects
  criterion tinkering.
- Unbuilt Eisenstein giants (v>164: ico T16..27 to v=272 etc.) —
  buildable since bendprover MAXV=512; raise SUBDIV_VCAP + build.
- Dented: currently the 26 old-atlas GLBs; a regeneration pipeline
  (punch + --dents solve) would replace/extend them.
- Hosting decision (GitHub Pages + Zenodo DOI was the recommendation;
  Dartmouth redirects; next arXiv version).
- Buried wholesale (13k more classified nets could get pages).

## Conventions

Evidence discipline per user CLAUDE.md; link nets by their personal
page (memory: link-atlas-when-discussing-nets); codex Stop-hook review
applies (cwd under ~/Dropbox/neo).
