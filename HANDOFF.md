# Atlas HANDOFF (chat bootstrap)

## Charter

This is the ATLAS chat: it owns the site — records, views, galleries,
eisenmaps, per-net artifacts, regeneration, deployment. Success = every
net Peter wants visible has a correct, beautiful, regenerable page. NOT
this chat: proving things or Lean. The atlas CONSUMES committed solver
output (producer→consumer rule); it never re-runs the solver at build.

Pick-up for a fresh atlas chat: read this + `git log --oneline -15` +
the auto-memory index. Live design record: `MORPH_GATE_TODO.md`.

## Architecture

Record/view: one directory per net under `site/personal/nets/<id>/` —
`net.json` is the record (identity, netcode, flags, themes, eisenstein,
artifact inventory, morph_note/caveat) beside its artifacts (rb/clers
GLBs, morph_p/k, ideal_net.svg, clers_layout.svg, eismap.svg). id =
`v{V}{CLERS}` when ≤200 chars else `v{V}h`+sha1-16 (`views.net_id`).
`views.py` is the only renderer.

Committed data is the source of truth:
- `data/bends/` (2,283 json) — the bend store: hero + morph-ladder
  bends per net, persisted by producer runs, consumed at build.
  Store-only rule: with a store present the solver is NEVER invoked.
- `data/*.tsv` — census pins (class_v30, symmetry, conway, classics,
  eisenstein, themes, floppers, …). Editorial: refresh deliberately,
  never as a build side effect.
- `data/walks/` — the dent-walk scan; the dentings gallery regenerates
  from it.

Two tiers:
- `./regen_personal.sh` — CONSUMER regen, the whole atlas from scratch:
  numpy-only, no solver/neo/network/scipy; personal.py + special.py;
  ~2.5 min; byte-deterministic (build-twice-diff proven; manifests in
  `notes/regen-verification-*/`).
- `./producer_census.sh` — PRODUCER census sweep (classify/members/
  symmetry; needs the neo tree + scipy): attended, editorial; its
  header records the measured drift semantics.
- `builders/aggregate_records.py` — deterministic consumer-side aggregation
  of the stamped `net.json` records into `data/atlas_records.jsonl`;
  `regen_personal.sh` runs it before the two ELT galleries.

Display gates (G1-audited, seven rounds; specs + calibration in
MORPH_GATE_TODO.md and notes/gate-calibration-20260722/): every
displayed edge within 1% of exact (normalized Lorentz metric, per-event
closure, certify-where-resolvable at float64 limits); dent_index
link-turning on displayed coordinates (NEVER volume sign).
Certification is only meaningful AT the solved alpha — read alphas from
the store, never retype them.

Morph policy: movies only for v ≤ 30 (MORPH_VMAX; PD 2026-07-24).
bendprover `--frames` (672a603) emits any finite realization on demand
(Klein-normalized, mp development); the atlas owns assembly.
Correspondence: notes/FOR_NEO_morph_frames.md / FOR_ATLAS_frames_ready.md.

## Site content (2026-07-30)

2,283 nets. Front title "Atlas of neoplatonic solids". Chips: Primes
v≤12 / v=13 / v=14 · Non-prime · Platonic & Archimedean · Convex ·
Hyperbolic · Dented · Hull-buried · Pancakes · Floppy · Symmetry ·
Eisenstein subdivisions · … Non-prime is organized by the paper's three
types via G1-audited clique-sum decomposition, 11/8/8: tet assemblies /
stacks of ≥2 octs / prime-core+tets. The tet-assembly family is
complete through 11 tets = v≤14 (BFS + canonical-CLERS enumeration):
one class at 2 and at 3 tets, three at 4 and at 5, helix-only from 6
through 11; captions carry the dual-tree shape (around an edge /
path / branched; G1-audited). The octahedron core is complete (all eight
attachment classes up to symmetry; four minted 2026-07-25 via the
canonical CLERS encoder in neo/clers). Convex opens with the eight
no-coplanar-faces solids (Rausenberger, later Freudenthal & van der
Waerden). Hyperbolic = the 25 degree-7 nets (Klein heroes). Dentings =
per-net dent SETS, ∅ first, from data/walks.

## Process

- Commit gate: PreToolUse hook (~/.claude/hooks/codex-commit-gate.py →
  codex-review) fires on every `git commit` and always logs to
  notes/codex-consults/<ts>-codex-gate-<tree>.txt. In this repo (no
  TEAMWORK.md) verdicts are mandatory-but-ADVISORY (PD 2026-06-11):
  READ THE TRANSCRIPT after every commit; approval = PASS/WARN for the
  exact tree (or a matching .git/claude-codex-approval stamp). Write
  .session/claude-commit-evidence.md before committing.
- G1 design audits for new conventions via `codex exec`, logged under
  notes/codex-consults/.
- Serve locally: persistent `python3 -m http.server 8765 --directory
  site` (root redirects to personal/). Deploy: rsync site/personal/ →
  gauss.dartmouth.edu:public_html/docs/atlas/ (preserve
  atlas_records.jsonl); old atlas parked at docs/atlas_old.
- Builders run under python3.13 (numpy 2.4.4, scipy 1.18.0).

## State (2026-07-30)

Atlax sandbox round (2026-07-29): `docs/atlax` on gauss is an
independent clone of the deployed atlas for site experiments. Its first
addition is `gallery/all-v10.html`: every unoriented simple sphere
triangulation with `4 <= V <= 10` and maximum vertex degree at most 6,
including prime and non-prime. Counts by v are 1, 1, 2, 5, 10, 15, 30
(64 total: 15 prime, 49 non-prime). Identity is canonical unoriented
CLERS; the frozen prime subset agrees exactly with `data/nets_v4_14.txt`.
Gallery thumbnails are the Euclidean `rb.glb` models, and every row
links to its personal page. G1:
`notes/codex-consults/2026-07-29-all-v10-g1-pass.jsonl` (PASS after
one BLOCK and resubmission). Census spec and measured checker output:
`notes/all-v10-g1-spec.md`, `notes/all-v10-check.out`.
All 28 previously absent census nets now also have normal personal
pages and bend stores. The established producer solved all
28 by the direct route; every page passed the existing hero/morph
display gates and has the complete artifact set (Euclidean and CLERS
GLBs, 11-frame Poincare and Klein morphs, ideal net, CLERS layout).
A store-only rebuild of all 252 generated files was byte-identical.
`nets_pages.txt` and `atlas_records.jsonl` now contain 2,283 records;
the v=4..10 by-v pages and all-v10 gallery are complete.
`gallery/elt-paper.html` is a 20-model working selection for the ELT
paper. Peter's 2026-07-29 caption pass cut three more small examples,
removed all visible CLERS names, and added the v14 hexagonal antiprism,
the largest built (5,1)-phyllohedron, and the v452 hexanti-family
example.
It is a single four-column, five-row desktop grid with paper captions
and no family remarks. Thumbnails
are non-interactive instances of the same `turntable.html` + `rb.glb`
view shown at the top left of each personal page. A single temporary
`static=1&capture=1` iframe renders each initial frame in sequence,
copies it to an ordinary PNG data-URL image, releases its WebGL context,
then advances to the next model. This avoids keeping 20 WebGL contexts
alive; each whole thumbnail links to its atlas page. The
superseded custom PNG renderer had
per-model camera orbits tuned against Peter's reference screenshot. G1
runner startup failed four times (`Operation not permitted`); Peter
explicitly said `proceed` on 2026-07-29.
The follow-up caption pass removed the provisional “Big Eight” remarks
and replaced the three `name?` placeholders with the atlas-supported
names snub disphenoid, triaugmented triangular prism, and gyroelongated
square bipyramid.  The ELT gallery is a permanent themed gallery linked
from the atlas front page as “ELT gallery.”  The provisional
Alexandrov-limit-theorem gallery was withdrawn on 2026-07-30 and will be
redesigned carefully later; the consumer regen now writes only the ELT
gallery after the ordinary atlas build.
`gallery/elt-symmetry.html` is the separate ELT symmetry page: one
representative for each of the 33 Conway symmetry types possible for a
Euclidean 6-net, in the frozen Conway-family order with the `x` types
last.  Hyperbolic-only `*55` and `55` are excluded.  Four ordinary atlas
records complete the Euclidean catalog: `3*` at v=24, chiral `422` at
v=26, `3x` at v=36, and `3*2` at v=48.  The v=24 and v=26 records have
complete morph ladders; v=36 and v=48 follow the established v>30
hero-only policy.  Representatives are the minimum `(v, name)` in each
symbol class after filtering to `maxdeg <= 6`.  Tiles are labeled by
symbol/order/v and a common name where one is stored; no CLERS name is
displayed.  The strengthened checker verifies the four ordinary records,
stored bends, symmetry rows, cutoff behavior, 33 ordered tiles, distinct
ids, and local targets; measured output is in
`notes/elt-symmetry-euclidean-g1-check.out`.
The evolved all-v10 GLB/link contract, the completed symmetry corrections,
and the current 20-id ELT still contract received a consolidated G1 PASS in
`notes/codex-consults/2026-07-30-atlax-gallery-contract-g1.jsonl`; the still
checker now derives its ids directly from `elt_paper.selection()`.
The complete 2,283-page consumer build was regenerated and deployed to
`gauss:public_html/docs/atlax/` on 2026-07-30.  A checksum rsync found
no file-content differences after deployment, and the local and remote
`atlas_records.jsonl` SHA-256 values both equal
`65420bcc09adae46fdfb80a554a7d39fdf0927a7e92709c77b788ddae89b0498`.
The next ELT pass places the eight F. and van der Waerden solids in the
first two rows without labeling the set on the gallery; the paper text
will identify them. The v=10 name is gyroelongated square bipyramid.
It removes the three-around-an-axis, three-rhombus,
subdivided-tetrahedron, and trapezoid-faced examples, replacing them
with Peter's v=23, v=28, v=107 T=21 (4,1), and v=9 negative-bend
examples. Their captions report the measured negative hero-bend counts
16, 20, 70, and 2; the v=28 caption is “buried vertices example.”
After the fixed first two rows, the remaining twelve examples are
ordered by vertex count.
Every ELT item now derives and displays its hero-bend partition
`(positive, zero, negative)` from the committed bend store using the atlas
flat-bend tolerance `1e-6`; the counts sum to `3v-6` for all 20 models.
Static gallery captures share azimuth 0 degrees and elevation 35 degrees,
chosen from a 3-by-3 contact-sheet comparison; personal-page interactive
views retain their 0-degree azimuth, 10-degree elevation default.  The G1
runner again failed before session creation with `Operation not permitted`;
the spec, checker, and two full failure logs are under `notes/`.

Live at math.dartmouth.edu/~doyle/docs/atlas; redeploy after each
landed round. Floppy census kept as pinned (PD): the 67 flags trace to
data/floppers.txt (in-repo; classify hard-fails if missing). Zenodo READY
TO PUBLISH (2026-07-26): three drafts, all cc-zero, all server-side
md5s verified against local — 21367250 "The Neoplatonic Atlas" (site
2,251 nets, front page carries the archive pointers, no author line,
CC0 dedication in PD's name at the foot; md5 b65c7417… + database),
19761390 "Prime neoplatonic solids" (CLERS lists v4–60 = 44,646,598
primes, MANIFEST-checked on doob + OBJs v4–50), and 21609862
"Software for the computer-assisted proof of Euclidean neoplatonic
realizations" (undented @ git 145d94d). Creators = Doyle alone on all
three records (PD 2026-07-26: "that should change too", matching the
de-authored front page). PENDING (PD 2026-07-26): link the
Doyle–Ellison arXiv paper from the front page when it appears. Citation
architecture (PD + GPT, 2026-07-26; notes/FOR_GPT_arxiv_assembly.md):
the paper cites the atlas ONLY by \seek to the live front page and
the proof software by its FROZEN version DOI 10.5281/zenodo.21609862;
the front page maintains the durable pointers (atlas concept DOI
21367249, primes concept DOI 19761389, software frozen DOI, GitHub).
DOIs resolve at first publish — PD's button, timed to the arXiv
submission. CAUTION: zenodo_dist.sh step 4 CREATES A NEW deposition
every run — refresh existing drafts via API PUTs to the deposition +
bucket (big uploads also work from doob, token present there). Pushed 2026-07-25 (PD: "push
push push"): origin main and next both carry the full arc (gates,
bend store, galleries, census pins, tet round, self-containment fix);
consumer regen from a bare clone is proven byte-identical. No tags
yet. The clers consult-log commit is pushed; bendprover public repo
already current at 672a603.

## History (compressed; details in git log and MORPH_GATE_TODO.md)

- 2026-07-15 freeze+deploy: public repos
  github.com/peterdoyle1717/neoplatonic-atlas (MIT) + idealprover;
  gauss docs/atlas swapped in, old 131G atlas at docs/atlas_old.
  Zenodo DRAFT 21367250 (DOI 10.5281/zenodo.21367250 reserved):
  site + db + primes_v4-60 tarballs, md5-verified; upload big files
  from doob (home PUTs 502). Pipeline builders/zenodo_dist.sh, token
  ~/.config/zenodo/token. Draft refreshed 2026-07-17; STALE since the
  2026-07-22+ rounds.
- 2026-07-17 tinkering: 2,215 nets, tet rays to T=252 (v506),
  smooth.glb everywhere, gallery consolidation.
- 2026-07-22 (c0a599a): display gates + committed bend store +
  always-regenerate + gallery round; seven G1 rounds; two production
  catches by the audited gates.
- 2026-07-24 (ed1365b): galleries by paper types, morph v≤30 policy,
  consumer/producer regen split with build-twice proof, census pin
  (floppers), title.
- 2026-07-25: octahedron-core exemplars (4 minted), 8/8/8 non-prime,
  symmetry/conway census completion (+57), gate-record correction,
  hook fixes (diff cap 250k, BLOCK vs ERROR distinguished); then
  tet-assembly completion → 11/8/8 (2 minted, the all-faces-capped
  tetrahedron promoted from themeless, shape captions).
