# Atlas HANDOFF (chat bootstrap)

## Charter (what this chat is about)

This is the ATLAS chat: it owns the site — records, views, galleries,
eisenmaps, per-net artifacts, regeneration, and eventually hosting.
Success = every net Peter wants visible has a correct, beautiful,
regenerable page. NOT this chat: proving things (prover chat:
~/Dropbox/neo/bendq_sandbox/boundary_cert/HANDOFF.md) or Lean (lob:
~/Dropbox/lob/TEAMWORK.md). It CONSUMES their outputs as committed
data files (classifications, certificates, specimen lists) and turns
them into pages and galleries.

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

## Distribution (2026-07-15, commit e95d48f)

Zenodo DRAFT deposition 21367250, DOI 10.5281/zenodo.21367250
reserved (live once Peter publishes). Two verified artifacts (site
tarball three-way md5 local = doob = Zenodo; db tarball two-way,
local = Zenodo — it was uploaded from home, small enough):
- neoplatonic-atlas.tar.gz 2,614,014,412 B, d57df591ef9dd03654da1a4db521b609
- neoplatonic-atlas-database.tar.gz 3,664,510 B, e526e00459623f6d2b7f0a45011f6b2d
Pipeline: builders/zenodo_dist.sh (token: ~/.config/zenodo/token —
also copied to doob; multi-GB PUTs from home failed repeatedly
(502s/resets), from doob succeeded first try in ~1 min — upload big
files from doob). Paper cites the DOI (neo.tex:209, compile-checked).
Remaining: Peter reviews + publishes; arXiv comments line.
2026-07-15 later: gauss SWAPPED (docs/atlas = new atlas, old at
docs/atlas_old; web/<v>/<NAME>.html 301-redirects via .htaccess;
all 5 paper URLs verified 200). primes_v4-60.tar.gz (208,670,491 B,
md5 a1a2b6a9...) added to the record — 3 files total, all
checksum-verified. Paper: bipyramid href canonicalized; zzz now
packages figures (compiled clean standalone on doob).

## Freeze + deploy (2026-07-15)

Public repos: github.com/peterdoyle1717/neoplatonic-atlas (this repo:
builders + data, MIT, README points at the DOI) and
github.com/peterdoyle1717/idealprover (boundary-cert scripts +
reports, copied from bendq_sandbox — originals untouched);
bendprover pushed current (ae6f915). Deployed:
math.dartmouth.edu/~doyle/docs/atlas2/personal/ (4.2G on gauss;
front page + GLB fetch both HTTP 200). OLD atlas (131G,
gauss docs/atlas) still up — paper's five links point there; retire
only after link rewrite or redirect. Local cleanup: retirees in
neo/_trash-20260715/ (5.9G; fleet pushed and/or tarballed first),
full-tree tarballs in neo/retired/ (310M, 14 tarballs).

## Conventions

Evidence discipline per user CLAUDE.md; link nets by their personal
page (memory: link-atlas-when-discussing-nets); codex Stop-hook review
applies (cwd under ~/Dropbox/neo).
