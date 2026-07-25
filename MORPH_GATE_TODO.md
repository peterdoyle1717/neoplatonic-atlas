# Morph gate — RESOLVED 2026-07-22 (supersedes the 2026-07-21 baton)

Original plan was (1) a develop_h residual gate and (2) removing morphs
for V > 50. Peter's rulings during implementation replaced both:

- No arbitrary v-cap. Pages render morphs iff the record carries them,
  and morphs enter the record only through the certificate. A giant that
  certifies keeps its morphs; a small net that fails loses them.
- Final gate spec (PD, 2026-07-22): every edge of a displayed frame has
  the length it is supposed to have, within 1 percent.
  Hyperbolic rungs: max over edges of |d_H(u,v) - ell(alpha)| / ell
  <= 1e-2 (each face is an equilateral triangle of side ell(alpha), so
  ground truth is exact and intrinsic). Euclidean end frame:
  max |len - 1| <= 1e-2. A develop_h numerical blow-up (off-hyperboloid
  sqrt) is a hard rejection, not a crash. Implemented in
  builders/personal.py (EDGE_LEN_TOL, develop_h_certified, glb_movies);
  one failing frame => NO morph GLBs, reason recorded in net.json
  (morph_note). views.py renders the morph block only when the record
  has the artifacts.
- Superseded along the way (measured, then discarded): a relative
  4-vector closure gate at 1e-6 (mis-calibrated: falsely killed ~572
  good v<=50 morphs) and a Klein-length closure-witness gate at 1e-3.

Calibration of the final gate, measured from the committed bends
(notes/gate-calibration-20260722/edge_len.tsv, 2026-07-22): max rel edge error v<=30 = 1.11e-4;
Euclidean heroes exact to 7.7e-14 over 2220 nets; exactly one v<=50 net
fails (the v48, edge error ~3e-2 class at deep alpha); diverged giants
score 0.7-1.0. Verdict deltas vs the deployed morph inventory: zero in
both directions -- the gate confirms the site as built.

Large-v morphs: no further chase (PD: "nobody will want morphs for
large v anyway"). The ~121 v>50 nets stay morph-omitted with their
recorded reasons; the deep-alpha store rungs for 41-58 giants remain
unsolved and that is accepted. No doob batch.

Related architecture landed with this (see data/bends/): the committed
bend store -- personal.py persists solver output (producer) and builds
from committed bends when present (consumer, no solver / neo / network).

## Undented display gate — WIRED 2026-07-22 (PD: "fix the gate")

dent_index link-turning check (port of neo/_trash-20260715/undented/
undented/src/dent_check.c inner loop -- turning per vertex, NEVER volume
sign) now runs on the displayed coordinates in builders/personal.py:
- every morph rung (Klein frame post-center, exactly what renders) and
  the Euclidean end frame, in glb_movies -- failure => morphs omitted,
  reason in morph_note ("dented frame at alpha=...");
- both hero paths (glb_euclid, glb_hero) -- failure raises, surfacing as
  BUILD-FAIL: a dented hero can never ship silently.

Degenerate-case handling, forced by a measured failure mode (traced on
the v12 pancake): an exactly-coplanar vertex link makes every triple
product B.(AxC) exact-zero; where den < 0, atan2 sits on the branch cut
and returns +-pi by the sign of 1e-17 noise, so per-vertex totals
{-2pi, 0, +2pi} are branch picks, not geometry. Vertices with all
|B.(AxC)| < COPLANAR_NUM_TOL (1e-12) are therefore skipped -- a dent
requires non-planarity; flat is the degenerate boundary, already
certified by the solved bends (all-plus turning system). Gate constants:
DENT_TURN_TOL = 1e-9, COPLANAR_NUM_TOL = 1e-12. Calibration over all
2245 stores (notes/gate-calibration-20260722/dent_turn.tsv + the v10-vertex trace): zero
displayed heroes or morph frames fail; tightest genuine margin +3.0e-7;
noise floor ~1e-16. Spot-verified through build_net: pancake v12 (all
vertices skipped, passes), v13, deg-7 j45 (Klein hero + 11 rungs), and
the v48 (correctly rejected upstream by the edge-length gate, 5.9e-2).

G1 round 1 (notes/codex-consults/2026-07-22-161343-g1-display-gates.txt):
REVISE, with the formula/ring-orientation/frame choices CONFIRMED and
six findings, all addressed in the same session:
1. Normalized metric: d_H = acosh(-mdot(u,v)/sqrt((-mdot u)(-mdot v)));
   raw acosh(-mdot) mis-measures off-hyperboloid drift (codex 26 percent
   counterexample). Every point must be finite, timelike, future
   (x4 > 0). DONE (develop_h_certified).
2. Certify what renders: certification now runs AFTER center(); the
   Klein projection is taken from the certified centered points. DONE.
3. Coplanar skip could mask a near-flat dent (codex synthetic
   counterexample at max|num|=3.4e-15): a skip now REQUIRES the
   flat-bends certificate -- every incident bend within FLAT_BEND_TOL
   (1e-6) of 0 or +-pi, the doubled-flat signature; coplanar without the
   certificate rejects the frame ("uncertified degenerate"). DONE.
   COPLANAR_NUM_TOL calibration vs smallest nondegenerate |num|:
   measured over all stores (see numcal below).
4. NaN pass-through: explicit isfinite rejection in both gates. DONE.
5. Stale-artifact bypass: reuse of existing morph GLBs now goes through
   a certification-only pass from the committed bends (glb_movies
   write=False); failure deletes the GLBs and records the reason.
   Partial artifacts rebuild (both-or-neither), and views.py renders the
   morph block only when BOTH artifacts are present. DONE.
6. Dented-hero exceptions surface as BUILD-FAIL and main() now exits
   nonzero when any net failed. DONE.
Declared out of scope (per consult): global self-intersection of
displayed frames and corruption introduced downstream of certification
(subdivision, Klein->Poincare conversion, GLB encoding) -- the gates
certify the vertex geometry that feeds rendering, not the render
pipeline itself.

Spot-verified after revision: v12 pancake / v13 / deg-7 j45 all
"reused (recertified)" through the store; v48 still omitted (5.93e-02
under the normalized metric -- verdict unchanged by normalization).

Revision calibration (notes/gate-calibration-20260722/numcal.txt, all
2245 stores under the revised gates): smallest NONDEGENERATE
max|B.(AxC)| = 1.13e-7 -- COPLANAR_NUM_TOL=1e-12 sits x1.1e5 below it
(and the measured degenerate noise ~1e-16 x1e4 below the tolerance);
4449 skipped vertices on 117 nets, EVERY one carrying the flat-bends
certificate (0 uncertified). Verdicts vs built site: no morph-carrying
net fails; the apparent deltas are v>50 giants omitted with
incomplete stores whose STORED rungs all pass -- undecided, not
mis-gated; their morph_note now records "store incomplete beyond
alpha=X (deep rungs unsolved; no giant chase, PD 2026-07-22)" instead
of the superseded 1e-6-metric reason (measured split after the note pass: 55 incomplete-store, 66
giants failing a stored rung under the final gates, each carrying its
real reason).
G1 round 2 (notes/codex-consults/2026-07-22-162535-g1r2-display-gates.txt):
REVISE -- findings 1/2/4 confirmed resolved, partial-artifact
fix confirmed; four residuals, all fixed in-session:
- missing bend key treated as flat -> now uncertified (bends.get(e) is
  None => reject);
- storeless GLB reuse rendered "uncertified" -> branch removed; such
  GLBs are deleted and rebuilt through the gates in producer mode;
- write=False could fall back to the solver on incomplete stores -> the
  store-only rule: with a store present glb_movies NEVER solves, in any
  mode; a missing rung => "store incomplete", morphs stay unbuilt (this
  also hard-codes the no-giant-chase ruling into the builder);
- reused rb.glb/clers.glb heroes bypassed the hero gates -> reused
  heroes are recertified from the committed bends (edge + dent; failure
  raises => BUILD-FAIL).
Spot-verified: v12/v13/v34 "reused (recertified)"; v78 incomplete-store
giant resolves "store incomplete at alpha=21.87" in 0.1s with zero
solver calls, hero recertified in the same pass.
G1 round 3 (notes/codex-consults/2026-07-22-162856-g1r3-display-gates.txt):
REVISE -- 3'/5a'/5b' confirmed fixed; remaining: certifying a
reconstruction while REUSING on-disk GLBs proves nothing about the bytes
served, and finding 6 wanted an executed failing-exit test. Resolution:
- Reuse ELIMINATED (G1 r3): build_net always regenerates every displayed
  artifact from the committed bends through the gates; regeneration is
  deterministic (measured byte-stable), so the artifact/model gap
  vanishes by construction. Storeless nets take the producer path
  (solve + persist) -- nothing ever renders uncertified.
- Deg-7 fresh heroes now edge-gated too (develop_h_certified before
  glb_hero; previously only dent-gated).
- Exit-chain tests EXECUTED: (t2) deliberate bad input through real
  main(): exit 1; healthy input: exit 0. (t1) corrupted-store test
  (hero bend +0.7) EXPOSED A GATE HOLE all three consult rounds missed:
  the corrupted hero BUILT CLEANLY -- rigid placement keeps kept edge
  lengths unit BY CONSTRUCTION (measured eerr 1.1e-16 on the corrupt
  net), so bad bends surface only in CLOSURE, and walklib.develop
  computes no closure residual at all (revisited faces skipped
  uncompared). Fixed: euclid_closure_resid() over ALL directed face
  adjacencies gates heroes and morph euclid-ends (closure <= 1e-2, edge
  scale 1); hyperbolic side gains the supplementary closure gate
  (develop_h resid / raw scale <= 1e-2; calibrated: v<=30 max relative
  closure 5.3e-4 in rel_v50.tsv -- no verdict changes). Rerun t1:
  corrupted tet now BUILD-FAIL "closure 5.58e-01, eerr 1.11e-16" --
  the pair of numbers is the vacuousness proof and its closure.
Final sweep (notes/gate-calibration-20260722/final_sweep.txt, all 2245
stores under the r3-final gates): hero euclid closure max 8.97e-14,
zero hero failures; exactly ONE morph-carrier flipped -- a v30 whose
alpha=2.1 frame the NORMALIZED metric measures at 5.5e-2 while the old
unnormalized metric read 7.3e-5: diagnosed, its points sit 57 percent
off the hyperboloid (max |(-mdot)-1| = 0.57) and the raw inner products
conspire to look like ell -- codex round-1's drift-fooling
counterexample caught in production data. The net is rebuilt: morphs
omitted, "edge length err 5.53e-02 at alpha=2.10" recorded. Site now
fully consistent with the final gates.
G1 round 4 (notes/codex-consults/2026-07-22-163649-g1r4-display-gates.txt):
REVISE -- round-3 residuals confirmed resolved on the morph-enabled
path, euclid closure formula confirmed; three findings, fixed:
- morphs=False left stale GLBs advertised -> morph GLBs are now deleted
  unconditionally at the top of every build; the opt-out ships nothing.
- a fresh morphs=False build persisted an empty-ladder store, poisoning
  later store-only builds -> stores are persisted ONLY as complete,
  gate-passing snapshots (hero + full ladder + no note); partial solves
  are never written.
- the supplementary hyperbolic closure (global resid / max coordinate)
  was frame-dependent -> replaced by the PER-EVENT normalized Lorentz
  discrepancy between predicted and retained lifts (acosh of the
  normalized Minkowski product, <= 1% of ell), Lorentz-invariant and
  scale-independent, with finite/timelike/future validation per lift.
Verified: spot suite passes; corrupt-store t1 still BUILD-FAILs;
morphs=False leaves no GLBs and no artifact flags, committed store
untouched. Re-verdict sweep under the per-event closure caught a SECOND
production net: a v28 (same phyllo family as the v30) whose alpha=2.1
frame has a 1.49e-2 per-event closure discrepancy -- two development
paths disagreeing by 1.5 percent of an edge, invisible to the
retained-edge metric (rigid placement). Rebuilt: morphs omitted with
the measured reason. Confirmation sweep
(notes/gate-calibration-20260722/final_sweep.txt): hero closure max
8.97e-14 / 0 failures, morph-carrier failures 0 -- the site is fully
consistent with the final gate set.
G1 round 5 (notes/codex-consults/2026-07-22-164416-g1r5-display-gates.txt): REVISE -- rounds 4(b)/(c)
confirmed resolved; two findings, fixed:
- stale-morph deletion ran after store parsing / solving / hero work, so
  a failure return or raise could leave old morphs advertised -> the
  deletion now happens FIRST, immediately after netdir creation; proven
  by test (pre-planted stale morphs + corrupt-store failing build =>
  morphs gone).
- q <= 1 -> 0 clamp could zero an impossible discrepancy -> reject q
  materially below 1. Verification then EXPOSED a numerics reality: a
  fixed 1e-9 materiality false-trips every net's deepest rung -- the
  Minkowski products cancel at coordinate scale s with absolute error
  ~eps*s^2 (~1e-2 at s=1e7). The threshold is now scale-aware
  (tol_q = max(1e-9, 32*eps*s^2)), applied symmetrically: q below
  1 - tol_q rejects (corruption), closure below the same floor counts
  as closed (indistinguishable from exact). The per-edge metric keeps
  the strict bound (m ~ cosh(ell) >> 1 cannot be noise-pushed below 1).
  Both production catches survive the scale-aware clamp (v30 5.5e-2,
  v28 1.9e-2, re-measured). Honest limit, recorded: at giant scale
  (s ~ 1e7) the closure noise floor approaches the 1 percent bound --
  float64 cannot certify closure much below it there; those frames
  already fail the edge gates.
G1 round 6 (notes/codex-consults/2026-07-22-164845-g1r6-display-gates.txt): REVISE -- deletion-first confirmed
resolved by the executed test; the scale-aware clamp INVERTED into an
acceptance hole (at s=1e7, tol_q=0.71: q=1.5 would read dcl=0 despite
acosh(1.5)=0.96). Resolution sequence, all measured:
- Codex's rule adopted: uncertainty must SPEND the budget, never grant
  allowance -- certify against the conservative upper bound
  acosh(max(1,q)+tol_q) <= 1% of ell.
- That flipped 25 small carriers (v22-25 phyllo chains, bounds
  1.0-3.1e-2): their MEASURED closure is fine; what fails is float64's
  ability to CERTIFY 1% at their deep-rung coordinate scale (>~5e5).
- My 32x safety factor was an unmeasured guess -- calibrated
  (notes/gate-calibration-20260722/closure_C.txt): 756001 clean-frame
  closure events, |q-1|/(eps*s^2) median 0.38, p99 7.6, large-s bound
  62. C_CLOSURE = 128 = 2x the measured bound.
- The physics is unavoidable: closure at 1% is unresolvable in float64
  above s ~ 5e5 under ANY honest gate. PD RULING (2026-07-22):
  certify-where-resolvable -- the closure gate applies wherever float64
  resolves 1%; where the noise floor alone exceeds the budget the event
  is skipped and counted, corruption rejection still applies, and the
  net's record carries morph_caveat ("closure unverifiable on N events
  (float64 noise floor at this scale)"). Caveats stamp at the next full
  build (required before promotion by the build-twice gate anyway).
- Verified: marginal v22 passes (err 1.0e-4, 8 unverifiable events
  counted); v30/v28 stay caught on measured error (5.5e-2 / 1.9e-2).
Incident, recorded: a scripted bulk edit during this round sliced on a
comment string that occurs before the target function and DUPLICATED
the dent-gate block (link_rings/display_min_turn) while no-oping the
intended return-signature changes -- caught by the spot suite
(unpack errors), diagnosed (double unv_total, dup defs), excised
line-precise (892->793 lines, copies diffed identical first), all
returns fixed, re-verified. Lesson: structural edits by string-slicing
without boundary verification are banned; use anchored line edits.
G1 round 7 (notes/codex-consults/2026-07-22-175729-g1r7-display-gates.txt):
APPROVE -- "the round-6 acceptance hole is removed: uncertainty
increases the tested upper bound rather than zeroing discrepancies";
corruption rejection ordering confirmed; caveat plumbing confirmed;
C_CLOSURE=128 confirmed against the measured 61.586 with stated margin;
"the implementation matches the recorded certify-where-resolvable
semantics." Zero-check sweep: hero closure max 8.97e-14 / 0 failures;
morph-carrier failures 0. THE DISPLAY-GATE DESIGN IS G1-APPROVED.

## Landed — commit c0a599a (next), 2026-07-22

G2 story, recorded: the automatic commit gate ERRORED on the raw
2245-file diff (codex context exhaustion, tokens used 0, exit 1) and the
wrapper FAILED OPEN -- the initial commit 1c4fcf6 landed unreviewed.
Approval was then obtained retroactively on the exact tree via
code-diff-in-full + data-summarized bundles:
- retro-1 (notes/codex-consults/2026-07-22-180254-g2retro-1c4fcf6.txt):
  BLOCK -- regen_personal.sh masked the failure signal (set -u only);
  no entry-point test; message overclaim. Fixed: set -euo pipefail,
  numpy/scipy preflight BEFORE the destructive rm, dead fetch_dents
  step removed, executed propagation tests (PYTHON=false -> exit 1,
  site intact; the preflight EXPOSED python3.13's missing scipy --
  full regen needs PYTHON=/usr/bin/python3 or a scipy install;
  consumer path needs numpy only).
- retro-2 (g2retro2-e1a814b): BLOCK -- opening sentence still
  overclaimed. retro-3 (g2retro3-c0a599a): PASS.
Final: commit c0a599a, tree 672fac7, ~2268 files.

PROCESS BUG, Peter's hook to fix: the gate wrapper fails OPEN on codex
error (two measured instances: the gpt-5.6-sol model-cache breakage in
the 1338c63f transcript, and today's context exhaustion). Narrow fix:
fail CLOSED on nonzero codex exit (block + print transcript path), and
bundle oversized diffs as code-diff-in-full + data-files-summarized
(the retro bundle shape) instead of raw git diff --cached.

## Morph policy final (PD 2026-07-24) + frames capability

bendprover 672a603 delivers --frames (MPFR development, Klein-normalized
emission, producer-side acceptance <= 1e-4 edge, refusals over lies) --
verified here on tet + v506 controls and an end-to-end 9-frame assembly
(notes/FOR_NEO_morph_frames.md, answered). PD rulings:
- MORPH_VMAX = 30 (personal.py): morph movies only for v <= 30; the 155
  v>30 nets carry "not built: v>30 morph policy (PD 2026-07-24)" and no
  morph artifacts. 2088 carriers remain, all v <= 30. A build-policy
  choice, not a gate: the realizer generates any finite realization on
  demand and the atlas owns assembly (fetch/assemble tooling exercised
  in scratchpad, adoptable into builders/ when a use arises).
- No --frames-tol; refusals stand. The v506 demo (partial ladder) was
  built, verified, and REVERTED under the policy.
- Hyperbolic gallery (special.py): the 25 degree-7 nets get their own
  gallery (Klein heroes, blue); elsewhere they appear only where they
  belong (blue members of Platonic & Archimedean; excluded from
  symmetry/convex/census galleries as before).

## Alpha hypersensitivity of closure certification (measured 2026-07-24)

During the build-twice verification a one-net discrepancy (v28 built
morphs; my ad-hoc check said it should fail) was traced to a TEST BUG
with a striking mechanism: the ad-hoc checks hardcoded alpha=2.1 while
the ladder (and the store's solved bends) carry alpha=2.1000000000000014.
Measured, same bends, same code, one process:
  alpha = 2.1000000000000014 (solved value): edge err 5.37e-3, PASS
  alpha = 2.1 (1.4e-15 away):               closure  1.95e-2, FAIL
Closure of near-ideal developments is exponentially conditioned in
alpha: a 1e-15 perturbation of alpha against solved bends flips closure
by ~1e-2 (amplification ~1e12 at v28 scale). RULE: certification is
meaningful only AT the solved alpha (glb_movies always does this; any
external re-check must take alpha from the store, never retype it).
Corrections to this record: the "v28 production catch at 1.49e-2" was
real under the C=32-era calibration; under the final gate at the TRUE
alpha v28 PASSES (5.37e-3) with 29 caveated events and legitimately
carries morphs. v30 and v48 fail at their true alphas (5.53e-2 /
5.13e-2) -- their omissions are genuine. Final census after the v<=30
policy: 2089 carriers.

## Floppy disparity resolved (2026-07-24)

The producer-census drift's 67 floppy flips were NOT a revised flopper
census: neo's 2026-07-15 trash-sweep removed euclid_hp/explore/ (the
322-flopper list now lives only in _trash-20260715 and sandbox copies),
and classify.py silently defaulted the missing file to an EMPTY set --
zeroing all 67 committed flags. Verified: the trashed list's bare-CLERS
entries match the committed 67 floppies 67/67. Fixes: the census input
is pinned in-repo (data/floppers.txt, 322 entries); classify.py hard-
fails on a missing flopper census (silent-empty default removed); and
classify output is now sorted (imap_unordered completion order was the
measured ~3.1k-row reorder). The committed census stands unchanged --
no science moved, a file did. (PD: floppy mattered before frozen-0-bend
handling; the gallery stays for now, census pinned.)
