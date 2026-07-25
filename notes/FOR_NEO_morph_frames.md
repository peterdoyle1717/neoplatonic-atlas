# For the neo session: emit morph frames from the realizer (mp development)

Standing request from the atlas side (branch `next`, commit c0a599a+).
Goal: the realizer in neo always succeeds at producing DISPLAYABLE morph
frames, so the atlas never develops hyperbolic coordinates itself.

## The problem, measured (atlas session 2026-07-22)

The atlas currently builds morph frames by float64 development of the
solver's bends (`atlas/builders/realize_h.py::develop_h`, hyperboloid
model). Per-step float64 rounding is amplified ~ e^(ell(alpha) * BFS
depth) by geodesic divergence — the same mechanism as neo's own v506
diagnosis of 2026-07-21. Measured casualties in the committed atlas
(gates + calibration under `atlas/notes/gate-calibration-20260722/`,
design record `atlas/MORPH_GATE_TODO.md`):

- 121 nets v>50: no morphs (66 with stored-rung edge errors up to 103
  percent; 55 stores left incomplete — deep rungs never solved).
- v48 (5.9e-2), v30 (5.5e-2 — its alpha=2.1 points sit 57 percent off
  the hyperboloid while the naive metric read 7e-5), v28 (1.9e-2
  closure): morphs omitted.
- At alpha=2.1 deg, ell ~ 8 and coordinates reach ~1e7; float64 closure
  measurement noise is ~ C*eps*s^2 with C measured <= 62 over 756k
  events (`closure_C.txt`) — above s ~ 5e5 float64 cannot even VERIFY
  1 percent closure, let alone guarantee it.

The atlas display spec (PD): every displayed edge within 1 percent of
its exact length (hyperbolic rungs: ell(alpha); Euclidean end: 1);
undented display (dent_index link turning, never volume sign). The
atlas GATES are done, committed, codex-audited (7 G1 rounds); they
refuse bad frames. What is missing is a GENERATOR that always passes
them. That generator belongs in neo (producer -> consumer rule:
the atlas consumes committed solver output).

## What to build (bendprover)

`~/Dropbox/projects/neo/bendprover/csrc/euclid_lm_mp.c` (+ `embcheck_mp.c`,
which already does MPFR-precision geometry — likely the code to lift).

Add a frames mode: for each requested alpha, after the existing
(dent-gated, unchanged) bend solve, DEVELOP the vertex coordinates on
the hyperboloid in MPFR and emit them:

- Emission (stdout protocol, additive — do not disturb '# bend' lines):
  `# pos <v> <x> <y> <z> <w>` per vertex (hyperboloid 4-vector,
  printed %.17g — double-accurate output is all the atlas needs; the
  mp is internal), plus `# devresid <R>` (mp closure residual, max
  over re-reached vertices) and `# devbits <N>`.
- Precision: adaptive. Start at 256 bits; if the mp closure residual
  exceeds tol (say 1e-30 * scale), double and redo. Rule-of-thumb
  need: ell(alpha)*depth/ln2 + guard; v794 at alpha=2.1 is
  ~8*40/0.693 ~ 460 bits, so 512 will usually settle it. Cheap
  relative to the LM solve.
- Alphas: the atlas ladder is MORPH_ALPHAS = [60 - 57.9*0.87^i for
  i in 0,3,...,21] + [58.0, 59.0] (10 rungs, deepest 2.1 first), and
  for maxdeg-7 nets the scaled ladder + alpha_max = 360/maxdeg
  (see `atlas/builders/personal.py`). Take alphas on the command line
  (repeatable --alpha, or --alphas csv) so the caller owns the ladder.
- The development convention must match the atlas's (realize_h.py):
  faces are equilateral hyperbolic triangles, corner angle alpha,
  cosh(ell) = cos(alpha)/(1-cos(alpha)); BFS from faces[0] with the
  registration convention (face0 placement is prescribed — do NOT
  re-root); midpoint frame placement, n-sign fixed by
  det(M,w,u,n) < 0 calibrated against the Euclidean limit. Port from
  realize_h.py or lift embcheck's development if it matches.

## Acceptance (measurable, atlas-side spec two orders inside display)

For every net in `atlas/data/nets_pages.txt` (2245, incl. v794) and
every ladder alpha, the emitted double-precision coordinates satisfy,
evaluated in plain float64:

1. edges: max |d_H(u,v) - ell(alpha)| / ell <= 1e-4, with
   d_H = acosh(-mdot(u,v)/sqrt((-mdot(u,u))(-mdot(v,v)))),
   every point finite, timelike, future;
2. closure: the mp devresid, mapped to double, <= 1e-4 * ell in the
   per-event normalized Lorentz sense;
3. undented: dent_index min link turning >= -1e-9 on the displayed
   coordinates (coplanar-degenerate vertices carry the flat-bends
   certificate: every incident bend within 1e-6 of 0 or +-pi);
4. determinism: identical bytes on repeat runs (fixed formatting, no
   randomization) — the atlas commits solver output as data-of-record.

Controls: tet(alpha) against closed form at every rung; v506 and v794
at alpha=2.1 (the historically failing cases); one pancake (exact 0/pi
bends) for the degenerate path.

## What the atlas does once this exists (do NOT do this in neo)

The atlas will extend its committed store (data/bends/<nid>.json) with
per-alpha coordinates (or a sibling data/frames/), retire develop_h
for morph geometry, and keep its display gates as independent
verification of the emitted coordinates. The 55 incomplete-store
giants and the 66+3 gate-omitted nets then get certified morphs on the
next producer run — no atlas-side numerics change needed.

Process notes for the neo session: this adds an emission convention
(G1 there per neo's discipline); the solver's dent gate and bends
protocol are untouched; keep the mode behind a flag so nothing
downstream moves until the atlas migrates.

## ANSWERED (atlas, 2026-07-24) — disposition closed, no changes needed

--frames verified here against your note: tet control (devresid
1.6e-56), v506 PASS at 34.89 (devresid 2.4e-36, 506 pos lines), v506
REFUSED at 2.1 with your exact message. An end-to-end assembly test
(v506 partial ladder, 9 frames, atlas gates re-verified each frame at
3e-12..4e-7 edge error) worked on the first try — then PD ruled the
policy question moot:

- NO --frames-tol. Refusal semantics are exactly right.
- The atlas builds morph movies only for v <= 30 (MORPH_VMAX policy,
  "waste of time and space" beyond). Your --frames capability is the
  contract we wanted: any finite realization on demand, atlas in
  charge of what gets assembled. Nothing further requested.
