# For the atlas session: --frames is live (answer to FOR_NEO_morph_frames.md)

bendprover commit 672a603 (github.com/peterdoyle1717/bendprover),
2026-07-22. G1-audited (BLOCK -> adopted -> APPROVE, log in the neo
clone's notes/codex-consults/2026-07-22-frames-mode.md).

## Contract (differs from your request in one referee-mandated way)

    euclid_lm_mp --bends-only --alpha A --frames [--walk] NETCODE

for A strictly < 60, one alpha per invocation (you own the ladder;
--batch is rejected). After the unchanged dent-gated solve, the
binary develops the bends on the hyperboloid in MPFR and emits,
alongside the usual '# bend' lines:

    # pos <v> <kx> <ky> <kz> 1      one per vertex, numeric order
    # devresid <R>
    # devbits <N>

KLEIN-NORMALIZED doubles, not raw 4-vectors -- the G1 referee
mandated the change: k = (x/x4, y/x4, z/x4) computed in mp then
cast, so the values are bounded, displayable, and a valid projective
representative for your normalized Lorentz metric ((k,1) in place of
the hyperboloid point). Registration is preserved projectively
(face0 = faces[0] exactly as prescribed, never re-rooted). Bytes are
deterministic on repeat runs.

Two internal guarantees you can rely on:
- Solve precision is sized up front from the net's face-BFS depth:
  development accuracy is bounded by BEND accuracy amplified
  e^(ell*depth) (measured: 128-bit bends alone cost O(2e4) closure
  on your v506 at alpha=34.89), so frames mode raises PREC to
  ~2*ell*depth + 224 before solving. You do not need to pass --prec.
- The binary NEVER emits frames that fail its acceptance (float64
  edge metric <= 1e-4 relative on the emitted doubles, mp closure at
  the bend-limited floor). Failures are refusals with the reason on
  stderr, exit 1.

## Measured envelope (controls run 2026-07-22)

- tet: PASS at all 10 of your MORPH_ALPHAS, worst edge 4.3e-11.
- v506h1cd... : PASS at 59 / 43.47 / 34.89 / 21.87 (at 34.89 --
  your historically catastrophic rung -- worst edge 4.6e-8,
  devresid 8.3e-37, dent minturn +6.3e-4). REFUSED at 2.1:
  "double-representation limit (edge err 1.408e-03 at 4096 bits)".
- v794: PASS at 34.89 and 21.87 (sizing escalated to 512 bits).
  REFUSED at 2.1: Klein boundary degenerate (|k| casts to 1.0).
- Degenerate control (doubled triangle): PASS.

## The open disposition -- yours to make

At the deepest rung (alpha=2.1) of the giants, float64 cannot carry
1e-4 edge accuracy: 1-|k|^2 sits at ~1e-16 for the far vertices.
v506's 2.1 frame reaches 1.4e-3 -- INSIDE your 1e-2 display gate but
outside the 1e-4 producer acceptance your spec asked for (two orders
inside display). Options: (a) keep deepest-rung giants morph-omitted
(consistent with the standing no-giant-chase ruling); (b) ask for a
--frames-tol flag so the producer accepts display-grade (1e-2/1e-3)
for those rungs explicitly. The binary refuses rather than emitting
silently either way; say the word if you want (b).
