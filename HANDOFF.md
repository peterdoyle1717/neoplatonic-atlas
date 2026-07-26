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
- `data/bends/` (2,249 json) — the bend store: hero + morph-ladder
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

## Site content (2026-07-25)

2,251 nets. Front title "Atlas of neoplatonic solids". Chips: Primes
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

## State (2026-07-25)

Live at math.dartmouth.edu/~doyle/docs/atlas; redeploy after each
landed round. Floppy census kept as pinned (PD): the 67 flags trace to
data/floppers.txt (in-repo; classify hard-fails if missing). Zenodo READY
TO PUBLISH (2026-07-25, PD: "get zenodo ready to go"): two refreshed
drafts, all server-side md5s verified against local — 21367250 "The
Neoplatonic Atlas" (site 2,251 nets + database; cc-zero) and 19761390
"Prime neoplatonic solids" (CLERS lists v4–60 = 44,646,598 primes,
checked against the registered MANIFEST on doob + OBJs v4–50;
cc-zero, flipped from cc-by-4.0 per PD 2026-07-25 "move everything to
cc-zero"). The paper cites the CONCEPT DOIs 10.5281/zenodo.21367249
(atlas) and 10.5281/zenodo.19761389 (primes) — see
notes/FOR_GPT_arxiv_assembly.md; they resolve at first publish — PD's
button, timed to the arXiv submission. CAUTION: zenodo_dist.sh step 4
CREATES A NEW deposition every run — to refresh the existing drafts
use API PUTs to the deposition + bucket (this round's method; big
uploads also work from doob, token present there). Pushed 2026-07-25 (PD: "push
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
