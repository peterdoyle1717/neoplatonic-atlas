#!/usr/bin/env python3
"""Personal pages, clean pipeline (PD spec 2026-07-11): for every prime
net v <= 14, exactly five artifacts on one page --
  1. red-black GLB (Euclidean realization),
  2. morph from Poincare (alpha ladder, seedless per rung),
  3. morph from Klein,
  4. CLERS-colored GLB (faces colored by their CLERS letter),
  5. CLERS layout (colored planar unfolding, SVG inline).
Rerunnable from scratch: input is data/nets_v4_14.txt (name + netcode,
from doob prove_final_v4_50/input.txt); everything else is solved here
(euclid_lm_mp, seedless).  Output: site/personal/<v>/<NAME>.html with
GLBs under site/personal/glb/.
"""
import math, os, subprocess, sys
from functools import partial
from multiprocessing import Pool
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
OUT = os.path.join(TOP, "site", "personal")
sys.path.insert(0, HERE)
from glb import retreat_to_incenter, write_gltf_like, write_gltf_groups, write_gltf_morph
from realize_h import develop_h, klein, poincare, center
from walklib import develop
from clers_tools import clers_svg, COLORS

BIN = os.environ.get("DW_BIN", "/Users/doyle/Dropbox/projects/neo/bendprover/csrc/euclid_lm_mp")
HOROZ = os.environ.get("HOROZ_BIN", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "horoz_c"))
RGB = {'A': (1.0, 0.0, 0.0), 'B': (1.0, 0.53, 0.0), 'C': (1.0, 0.8, 0.0),
       'D': (0.0, 0.67, 0.0), 'E': (0.0, 0.4, 1.0)}
BLACK = (0.0, 0.0, 0.0)

STYLE = ("body{font-family:Georgia,serif;max-width:680px;margin:2em auto;"
         "line-height:1.6;color:#222;padding:0 1em}"
         "h1{font-family:monospace;font-size:1.2em;word-break:break-all}"
         "nav{font-size:.9em}nav a{color:#2255aa;text-decoration:none}"
         "nav a:hover{text-decoration:underline}"
         ".info{font-size:.9em;color:#555;margin:-.5em 0 .5em}"
         ".hint{font-size:.8em;color:#aaa;font-style:italic;margin-bottom:1em}"
         ".pair{display:grid;grid-template-columns:1fr 1fr;gap:.8em;margin-bottom:1em}"
         ".cell{position:relative;width:100%;padding-bottom:100%}"
         ".cell iframe{position:absolute;top:0;left:0;width:100%;height:100%;border:none}"
         ".cell .svgwrap{position:absolute;top:0;left:0;width:100%;height:100%;"
         "display:flex;align-items:center;justify-content:center;"
         "border:1px solid #ddd;box-sizing:border-box}"
         ".cell .svgwrap svg{max-width:90%;max-height:90%}"
         ".label{text-align:center;font-size:.8em;color:#888;margin-top:.2em}"
         "a{color:#2255aa}")

MV = ('<script type="module" src="../vendor/model-viewer.min.js">'
      '</script>')   # 1-deep pages (gallery/, by-v/); front page swaps to vendor/


def solve_prove_60(nc):
    """seedless dent-gated LM via the binary's --walk fallback (rung
    ladder 59.9/59/57/54, within-member seeding only, no
    randomization -- the relabel retries were removed 2026-07-21;
    swept: 2245-row nets_pages, 2209 direct + 11 walk + 25
    hyperbolic-skip, 0 failures). Route logged to stderr per net."""
    import sys
    cmd = [BIN, "--prove", "--alpha", "60.0", "--walk", "--name", "X"]
    r = subprocess.run(cmd + [nc], capture_output=True, text=True, timeout=1800)
    if "end" not in r.stdout:
        return None
    route = next((ln[2:].strip() for ln in r.stdout.splitlines()
                  if ln.startswith("# route")), "route ?")
    print(f"  {route}", file=sys.stderr, flush=True)
    bends = {}
    for ln in r.stdout.splitlines():
        t = ln.split()
        if t and t[0] == "b":
            bends[(int(t[1]), int(t[2]))] = float(t[3]) * math.pi
    return bends


def _bends_alpha_raw(nc, a, seed=None):
    """'# bend' lines (internal radians, as strings) at hyperbolic alpha."""
    cmd = [BIN, "--bends-only", "--alpha", f"{a:.6f}", "--name", "X"]
    if seed:
        cmd += ["--seed", seed]
    r = subprocess.run(cmd + [nc], capture_output=True, text=True, timeout=900)
    if "end" not in r.stdout:
        return None
    return {(int(t[3]), int(t[4])): t[5] for t in
            (ln.split() for ln in r.stdout.splitlines())
            if len(t) >= 6 and t[0] == '#' and t[1] == 'bend'}


def solve_alpha(nc, a):
    r = subprocess.run([BIN, "--bends-only", "--alpha", f"{a:.6f}",
                        "--name", "X", nc],
                       capture_output=True, text=True, timeout=900)
    if "end" not in r.stdout:
        return None
    return {(int(t[3]), int(t[4])): float(t[5]) for t in
            (ln.split() for ln in r.stdout.splitlines())
            if len(t) >= 6 and t[0] == '#' and t[1] == 'bend'}



def make_svg(positions, edges, size=100, pad=6):
    """Inline SVG wireframe (lifted from atlas/python/build_ideal.py)."""
    pts = list(positions.values())
    if not pts:
        return ''
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    w = xmax - xmin or 1.0
    h = ymax - ymin or 1.0
    scale = (size - 2 * pad) / max(w, h)
    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0
    mid = (size - 2 * pad) / 2.0

    def tx(x):
        return pad + (x - cx) * scale + mid

    def ty(y):
        return pad + (cy - y) * scale + mid

    lines = []
    for u, w2 in edges:
        if u not in positions or w2 not in positions:
            continue
        x1, y1 = tx(positions[u][0]), ty(positions[u][1])
        x2, y2 = tx(positions[w2][0]), ty(positions[w2][1])
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
                     f'y2="{y2:.1f}" stroke="#000" stroke-width="0.7"/>')
    return (f'<svg viewBox="0 0 {size} {size}" width="100%" '
            f'xmlns="http://www.w3.org/2000/svg" style="display:block">'
            + ''.join(lines) + '</svg>')


def ideal_net_svg(nc, faces):
    """The ideal net: Perron placement via horoz_c (vertex 1 at infinity),
    edges not through vertex 1, rendered as segments."""
    import struct
    try:
        r = subprocess.run([HOROZ], input=(nc + "\n").encode(),
                           capture_output=True, timeout=120)
        data = r.stdout
    except Exception:
        return ''
    V = max(max(f) for f in faces)
    if len(data) < V * 24:
        return ''
    positions = {}
    for vi in range(V):
        u, x, y = struct.unpack_from('<ddd', data, vi * 24)
        if vi == 0 or math.isnan(u):
            continue
        positions[vi + 1] = (x, y)
    edges = set()
    for a, b, c in faces:
        for u2, w2 in ((a, b), (b, c), (a, c)):
            if u2 == 1 or w2 == 1:
                continue
            edges.add((min(u2, w2), max(u2, w2)))
    return make_svg(positions, sorted(edges))


def glb_hero(name, faces, V, pos, outdir, bends=None):
    """blue-black + CLERS GLBs from given coordinates (Klein model for
    degree-7 nets at alpha_max; blue is the hyperbolic color, matching
    the morph viewer's BLUE 0.25,0.55,0.85)."""
    mt, dbad = display_min_turn(pos, link_rings(faces), bends)
    if dbad or mt < -DENT_TURN_TOL:  # tripwire: a dented hero must never ship
        raise RuntimeError(f"dented/uncertified hero display (min turn {mt:.2e})")
    verts = [tuple(map(float, pos[v])) for v in range(1, V + 1)]
    fidx = [(a - 1, b - 1, c - 1) for a, b, c in faces]
    v2, f2, mats = retreat_to_incenter(verts, fidx, 0.9)
    write_gltf_like(os.path.join(outdir, "rb.glb"), v2, f2, mats,
                    center_color=[0.25, 0.55, 0.85])
    # smooth view: original shared vertices, no borders, no normals
    # (viewer computes smooth vertex normals) -- the conemanifold look
    write_gltf_like(os.path.join(outdir, "smooth.glb"), verts, fidx,
                    solid_color=[0.25, 0.55, 0.85])
    groups = [(BLACK, [f2[k] for k in range(len(f2)) if mats[k] == "border"])]
    for L, rgb in RGB.items():
        gf = [f2[7 * i + 6] for i, ch in enumerate(name) if ch == L]
        if gf:
            groups.append((rgb, gf))
    write_gltf_groups(os.path.join(outdir, "clers.glb"), v2, groups)


def euclid_closure_resid(faces, bd, pos):
    """Max mismatch between every face's apex as re-placed from its
    neighbor (walklib.develop's placement formula) and the kept position.
    Rigid placement makes KEPT edge lengths unit by construction, so bad
    bends surface only here (proven by the corrupted-store test, G1 r3):
    walklib.develop skips revisited faces without comparing, computing no
    residual at all. Checked over ALL directed adjacencies, a superset of
    any single BFS's closure events. Edge scale is 1, so this bounds the
    true edge-length error of the displayed configuration."""
    apex = {}
    for a, b, c in faces:
        apex[(a, b)] = c; apex[(b, c)] = a; apex[(c, a)] = b
    r = 0.0
    for f0 in faces:
        for i in range(3):
            x, y = f0[i], f0[(i + 1) % 3]
            d = apex[(y, x)]
            A, B, P = pos[x], pos[y], pos[f0[(i + 2) % 3]]
            M = 0.5 * (A + B)
            w = P - M
            w = w / np.linalg.norm(w)
            n = np.cross(w, B - A)
            n = n / np.linalg.norm(n)
            th = bd[tuple(sorted((x, y)))]
            D = M + (math.sqrt(3) / 2) * (-math.cos(th) * w + math.sin(th) * n)
            r = max(r, float(np.max(np.abs(D - pos[d]))))
    return r


def glb_euclid(name, faces, V, bends, outdir):
    bd = {tuple(sorted(e)): b for e, b in bends.items()}
    pos, _ = develop(faces, bd)
    # hero tripwires: closure AND edge lengths AND undented display
    cres = euclid_closure_resid(faces, bd, pos)
    eerr = max(abs(float(np.linalg.norm(pos[u] - pos[v])) - 1.0)
               for u, v in _edges_of(faces))
    mt, dbad = display_min_turn(pos, link_rings(faces), bd)
    if not (math.isfinite(eerr) and math.isfinite(cres)) \
            or cres > EDGE_LEN_TOL or eerr > EDGE_LEN_TOL or dbad \
            or mt < -DENT_TURN_TOL:
        raise RuntimeError(
            f"hero fails display gates (closure {cres:.2e}, "
            f"eerr {eerr:.2e}, min turn {mt:.2e})")
    verts = [tuple(map(float, pos[v])) for v in range(1, V + 1)]
    fidx = [(a - 1, b - 1, c - 1) for a, b, c in faces]
    v2, f2, mats = retreat_to_incenter(verts, fidx, 0.9)
    write_gltf_like(os.path.join(outdir, "rb.glb"), v2, f2, mats)
    write_gltf_like(os.path.join(outdir, "smooth.glb"), verts, fidx)
    # CLERS coloring: retreat emits 7 faces per original (6 border, 1 center)
    groups = [(BLACK, [f2[k] for k in range(len(f2)) if mats[k] == "border"])]
    for L, rgb in RGB.items():
        gf = [f2[7 * i + 6] for i, ch in enumerate(name) if ch == L]
        if gf:
            groups.append((rgb, gf))
    write_gltf_groups(os.path.join(outdir, "clers.glb"), v2, groups)


## geometric from the ideal end, then a linear tail so the arrival at 60
## is even-paced (shape change near Euclid scales like 60 - alpha)
MORPH_ALPHAS = ([60.0 - 57.9 * (0.87 ** i) for i in range(0, 24, 3)]
                + [58.0, 59.0])  # 2.1 .. 56.9, 58, 59 (then exact 60)
SUBDIV = 10


def bary_grid(n):
    """barycentric weights + triangle pattern for one subdivided face,
    wound consistently with the face's (a, b, c) orientation."""
    pts, idx = [], {}
    for i in range(n + 1):
        for j in range(n + 1 - i):
            idx[(i, j)] = len(pts)
            pts.append(((n - i - j) / n, i / n, j / n))
    tris = []
    for i in range(n):
        for j in range(n - i):
            a, b, c = idx[(i, j)], idx[(i + 1, j)], idx[(i, j + 1)]
            tris.append((a, b, c))
            if j < n - i - 1:
                tris.append((b, idx[(i + 1, j + 1)], c))
    return pts, tris


def subdivided_frame(faces, P, grid):
    """sample each face on the barycentric grid, linearly in the given
    3d coordinates (in Klein, chords are geodesics, so the linear
    samples lie on the hyperbolic face; in Euclidean they lie on the
    flat face). Returns (verts, tris) with per-face vertex blocks."""
    wts, pat = grid
    verts, tris = [], []
    for a, b, c in faces:
        base = len(verts)
        A, B, C = P[a], P[b], P[c]
        for wa, wb, wc in wts:
            verts.append((wa * A[0] + wb * B[0] + wc * C[0],
                          wa * A[1] + wb * B[1] + wc * C[1],
                          wa * A[2] + wb * B[2] + wc * C[2]))
        tris += [(base + i, base + j, base + k) for i, j, k in pat]
    return verts, tris


def klein_to_poincare(verts):
    out = []
    for x, y, z in verts:
        q = math.sqrt(max(0.0, 1.0 - (x * x + y * y + z * z)))
        s = 1.0 / (1.0 + q)
        out.append((x * s, y * s, z * s))
    return out


def align_frames(frames):
    """remove the spurious rigid rotation between consecutive frames
    (each is developed and centered independently), anchoring at the
    LAST frame: the Euclidean end keeps the flat developer's own
    coordinates -- the same frame the red-black GLB is built in -- and
    each earlier frame is rotated onto its successor (best-fit proper
    rotation via SVD, the standard point-set superposition recipe)."""
    import numpy as np
    n = len(frames)
    out = [None] * n
    out[-1] = np.asarray(frames[-1], float)
    for k in range(n - 2, -1, -1):
        A = np.asarray(frames[k], float)
        A = A - A.mean(axis=0)
        B = out[k + 1] - out[k + 1].mean(axis=0)
        U, _, Vt = np.linalg.svd(A.T @ B)
        d = 1.0 if np.linalg.det(U @ Vt) > 0 else -1.0
        R = U @ np.diag([1.0, 1.0, d]) @ Vt
        out[k] = A @ R
    return [[tuple(v) for v in F] for F in out]


# Length-fidelity gate (PD spec 2026-07-22, final): every edge of a
# displayed frame must have the length it is supposed to have, within 1%.
# Hyperbolic frames: every edge of every equilateral face has exact
# hyperbolic length ell(alpha) (realize_h.side_length); the metric is
# max over edges of |d_H(u,v) - ell| / ell, with d_H = acosh(-mdot).
# Euclidean end frame: every edge has length 1; max |len - 1|.
# Accumulated development divergence lands exactly here: edges whose
# endpoints arrive via different development paths inherit the drift.
EDGE_LEN_TOL = 1e-2

# Morph movies are built only for v <= MORPH_VMAX (PD 2026-07-24: "no
# need to include any morph movies beyond v=30 -- waste of time and
# space"). A build-policy choice, not a correctness gate: the realizer
# (bendprover --frames) can generate any finite realization on demand,
# and the atlas owns frame assembly; what gets built is up to us.
MORPH_VMAX = 30


def _edges_of(faces):
    return {tuple(sorted((a, b))) for f in faces
            for a, b in zip(f, f[1:] + f[:1])}


# Undented display gate (PD 2026-07-22: "make sure what we display is
# actually undented"). dent_index link-turning check (port of
# undented/src/dent_check.c inner loop -- turning per vertex, NEVER
# volume sign) run on the displayed coordinates themselves. Degenerate
# case, measured 2026-07-22 on the v12 pancake: an exactly-coplanar
# vertex link makes every triple product B.(AxC) exact-zero, and where
# den < 0 the atan2 lands on the branch cut -- +-pi decided by 1e-17
# rounding noise, so per-vertex totals {-2pi, 0, +2pi} are branch picks,
# not geometry. Such vertices are excluded: a dent needs non-planarity,
# and a coplanar link is the flat degenerate boundary (pancakes). Their
# flatness is already certified by the solved bends (all-plus turning
# system). Calibration over all 2245 stores
# (notes/gate-calibration-20260722/dent_turn.tsv): every displayed hero
# and morph frame passes; tightest genuine margin +3.0e-7; noise floor
# ~1e-16.
DENT_TURN_TOL = 1e-9        # reject a displayed frame if min turn < -this
COPLANAR_NUM_TOL = 1e-12    # all |B.(AxC)| below this => degenerate vertex
FLAT_BEND_TOL = 1e-6        # bend within this of {0, +-pi} counts as flat/fold


def link_rings(faces):
    """vertex -> cyclic neighbor ring, from the face structure."""
    succ = {}
    for a, b, c in faces:
        succ.setdefault(a, {})[b] = c
        succ.setdefault(b, {})[c] = a
        succ.setdefault(c, {})[a] = b
    rings = {}
    for v, nxt in succ.items():
        start = next(iter(nxt))
        ring, cur = [start], nxt[start]
        while cur != start:
            ring.append(cur)
            cur = nxt[cur]
        rings[v] = ring
    return rings


def display_min_turn(pos, rings, bends=None):
    """(min_turn, bad) over the displayed positions. min_turn is the
    minimum link turning over non-degenerate vertices (+inf if none).

    G1 revision (consult 2026-07-22-161343): a coplanar-degenerate vertex
    (all |B.(AxC)| < COPLANAR_NUM_TOL, where the atan2 branch is noise)
    is SKIPPED only when its flatness is independently certified by the
    solved bends -- every incident bend within FLAT_BEND_TOL of 0 or
    +-pi, the doubled-flat/pancake signature. A coplanar link WITHOUT
    that certificate may hide a near-flat dent, so bad=True and the
    caller must reject the frame. Nonfinite coordinates or turning sums
    also set bad=True.
    """
    mt, bad = float('inf'), False
    for v, ring in rings.items():
        k = len(ring)
        if k < 3:
            continue
        dirs = []
        for nb in ring:
            d = np.asarray(pos[nb], float) - np.asarray(pos[v], float)
            n = float(np.linalg.norm(d))
            if not math.isfinite(n):
                bad = True
                break
            dirs.append(d / (n if n > 1e-15 else 1e-15))
        else:
            nums, dens = [], []
            for i in range(k):
                A, B, C = dirs[(i - 1) % k], dirs[i], dirs[(i + 1) % k]
                nums.append(float(np.dot(B, np.cross(A, C))))
                dens.append(float(np.dot(A, B) * np.dot(B, C) - np.dot(A, C)))
            if max(abs(x) for x in nums) < COPLANAR_NUM_TOL:
                flat_ok = bends is not None
                if flat_ok:
                    for nb in ring:
                        b = bends.get(tuple(sorted((v, nb))))
                        # a MISSING bend is uncertified, never flat (G1 r2)
                        if b is None or not (abs(b) < FLAT_BEND_TOL
                                             or abs(abs(b) - math.pi) < FLAT_BEND_TOL):
                            flat_ok = False
                            break
                if not flat_ok:
                    bad = True       # degenerate link, flatness uncertified
                continue
            t = sum(math.atan2(n_, d_) for n_, d_ in zip(nums, dens))
            if not math.isfinite(t):
                bad = True
                continue
            mt = min(mt, t)
            continue
        break                        # nonfinite direction: stop, frame bad
    return mt, bad


# closure-noise coefficient, MEASURED (notes/gate-calibration-20260722/
# closure_C.txt: 756001 clean-frame events; |q-1|/(eps*s^2) median 0.38,
# p99 7.6, large-s (>1e5) bound 62). C = 128 = 2x the measured bound.
C_CLOSURE = 128.0


def develop_h_certified(faces, bd, alpha_rad, edges=None):
    """develop_h -> center -> edge-length gate ON THE CENTERED (displayed)
    coordinates. Returns (pos_centered, err, ok, n_unverifiable):
    err = max relative hyperbolic edge-length error vs ell(alpha);
    n_unverifiable = closure events where the float64 noise floor alone
    exceeds the 1% budget, so closure is certified-where-resolvable and
    skipped there (PD ruling 2026-07-22), corruption rejection still
    applying. Callers record a caveat when n_unverifiable > 0.

    G1 revisions (consult 2026-07-22-161343): the distance is the
    NORMALIZED form d_H = acosh(-mdot(u,v)/sqrt((-mdot(u,u))(-mdot(v,v))))
    -- the raw acosh(-mdot) is valid only on exact unit timelike vectors
    and silently mis-measures off-hyperboloid drift; every point must be
    finite, timelike (-mdot(x,x) > 0), and future (x4 > 0); certification
    runs after center() so it validates exactly what is rendered.

    A numerical blow-up anywhere (off-hyperboloid sqrt in develop/center,
    nonfinite coordinates) is a hard rejection (err = inf), never a crash.
    """
    from realize_h import mdot, side_length
    n_unv = 0
    try:
        raw, _, events = develop_h(faces, bd, alpha_rad)
        ell = side_length(alpha_rad)
        # closure gate (G1 r4): rigid placement can keep edge lengths
        # near-exact while paths disagree, so every closure event is
        # gated on the PER-EVENT normalized Lorentz discrepancy between
        # the predicted and retained lifts -- acosh of the normalized
        # Minkowski product, a Lorentz-invariant hyperbolic distance,
        # frame- and scale-independent (the earlier global resid/scale
        # form was frame-dependent: one large unrelated coordinate
        # weakened every check). Bound: within 1% of an edge length.
        for d, D in events:
            qd, qp = -mdot(D, D), -mdot(raw[d], raw[d])
            if not (math.isfinite(qd) and math.isfinite(qp)
                    and qd > 0.0 and qp > 0.0
                    and float(D[3]) > 0.0 and float(raw[d][3]) > 0.0):
                return None, float('inf'), False, n_unv
            q = -mdot(D, raw[d]) / math.sqrt(qd * qp)
            # for unit timelike lifts q >= 1 exactly; materially below 1
            # is numerical corruption (G1 r5). Materiality is SCALE-AWARE
            # with the MEASURED coefficient (closure_C.txt): the Minkowski
            # products cancel at coordinate scale s with absolute error
            # <= C_CLOSURE*eps*s^2. The uncertainty never becomes an
            # allowance (G1 r6): where resolvable, the frame is certified
            # against the conservative UPPER bound (largest closure
            # consistent with the measurement). Where the noise floor
            # ALONE exceeds the budget, closure is unverifiable in
            # float64: certify-where-resolvable (PD ruling 2026-07-22) --
            # the event is skipped, counted, and the caller records the
            # caveat; corruption rejection still applies.
            s = max(float(np.max(np.abs(D))), float(np.max(np.abs(raw[d]))))
            tol_q = max(1e-9, C_CLOSURE * 2.22e-16 * s * s)
            if not math.isfinite(q) or q < 1.0 - tol_q:
                return None, float('inf'), False, n_unv
            if math.acosh(1.0 + tol_q) > EDGE_LEN_TOL * ell:
                n_unv += 1
                continue
            dcl_ub = math.acosh(max(1.0, q) + tol_q)
            if dcl_ub / ell > EDGE_LEN_TOL:
                return None, dcl_ub / ell, False, n_unv
        posh = center(raw)
        norm2 = {}
        for v, x in posh.items():
            q = -mdot(x, x)
            if not (math.isfinite(q) and q > 0.0 and float(x[3]) > 0.0):
                return None, float('inf'), False, n_unv
            norm2[v] = q
        err = 0.0
        for u, v in (edges or _edges_of(faces)):
            m = -mdot(posh[u], posh[v]) / math.sqrt(norm2[u] * norm2[v])
            # same clamp discipline as the closure gate (G1 r5): q >= 1
            # for unit timelike vectors; materially below 1 = corruption
            if not math.isfinite(m) or m < 1.0 - 1e-9:
                return None, float('inf'), False, n_unv
            dh = math.acosh(m) if m > 1.0 else 0.0
            err = max(err, abs(dh - ell) / ell)
        if not math.isfinite(err):
            return None, float('inf'), False, n_unv
    except (ValueError, FloatingPointError, ZeroDivisionError, OverflowError):
        return None, float('inf'), False, n_unv
    return posh, err, err <= EDGE_LEN_TOL, n_unv


def glb_movies(name, faces, V, nc, outdir, alphas=None, euclid_end=True,
               stored=None, write=True):
    """Two animated morph GLBs (Poincare, Klein): ideal end first, then
    either the exact Euclidean solid (alpha_max = 60) or the hyperbolic
    realization at the final rung (degree-7 nets: alpha_max = 360/maxdeg).

    Consumer mode: when `stored` (the data/bends record: {"hero": bd,
    "morph": {rounded-alpha: bd}}) provides a rung, its bends are used and
    the solver is never invoked for it -- the deterministic no-solver
    build path. Missing rungs fall back to the solver (producer mode) and
    are returned in `solved` for persistence.

    Every develop_h frame is certified (develop_h_certified, Klein-length
    gate). If any frame fails, NO GLB is written and a reason is returned
    -- never a partial or silently-broken morph. Returns (nframes, note,
    solved). The euclidean end frame uses the flat developer
    (walklib.develop), which the v506 diagnosis exonerated, so it is not
    gated here.
    """
    grid = bary_grid(SUBDIV)
    fp, fk, tris = [], [], None
    solved = {}                     # alpha -> bend dict, freshly solved only
    unv_total = 0                   # closure events unverifiable in float64
    edges = _edges_of(faces)
    rings = link_rings(faces)
    for a in (alphas or MORPH_ALPHAS):
        bd = (stored or {}).get("morph", {}).get(round(a, 6))
        if bd is None:
            if stored is not None:
                # store present => store-only (G1 r2): never fall back to
                # the solver, neither in certify-only nor in build mode --
                # an incomplete store means the morphs stay unbuilt.
                return 0, f"store incomplete at alpha={a:.2f}", solved, unv_total
            bends = solve_alpha(nc, a)
            if bends is None:
                return 0, f"solve_alpha failed at alpha={a:.2f}", solved, unv_total
            bd = {tuple(sorted(e)): b for e, b in bends.items()}
            solved[a] = bd
        posh, err, ok, nunv = develop_h_certified(faces, bd, math.radians(a), edges)
        unv_total += nunv
        if not ok:
            return 0, f"edge length err {err:.2e} at alpha={a:.2f}", solved, unv_total
        K = klein(posh)              # posh is already centered (displayed)
        mt, dbad = display_min_turn(K, rings, bd)
        if dbad:
            return 0, f"uncertified degenerate frame at alpha={a:.2f}", solved, unv_total
        if mt < -DENT_TURN_TOL:
            return 0, f"dented frame at alpha={a:.2f} (min turn {mt:.2e})", solved, unv_total
        if write:
            vk, tris = subdivided_frame(faces, K, grid)
            fk.append(vk)
            fp.append(klein_to_poincare(vk))
    if euclid_end:
        bd60 = (stored or {}).get("hero")
        if bd60 is None:
            bends60 = solve_prove_60(nc)
            if bends60 is None:
                return 0, "solve_prove_60 failed (euclidean end frame)", solved, unv_total
            bd60 = {tuple(sorted(e)): b for e, b in bends60.items()}
        pos60, _ = develop(faces, bd60)
        cres = euclid_closure_resid(faces, bd60, pos60)
        eerr = max(abs(float(np.linalg.norm(pos60[u] - pos60[v])) - 1.0)
                   for u, v in edges)
        if not (math.isfinite(eerr) and math.isfinite(cres)) \
                or cres > EDGE_LEN_TOL or eerr > EDGE_LEN_TOL:
            return 0, f"euclid closure/edge err {cres:.2e}/{eerr:.2e}", solved, unv_total
        mt, dbad = display_min_turn(pos60, rings, bd60)
        if dbad:
            return 0, "uncertified degenerate euclid frame", solved, unv_total
        if mt < -DENT_TURN_TOL:
            return 0, f"dented euclid frame (min turn {mt:.2e})", solved, unv_total
        if write:
            ctr = sum(pos60.values()) / len(pos60)
            ve, tris = subdivided_frame(faces, {v: p - ctr for v, p in pos60.items()}, grid)
            fp.append(ve)
            fk.append(ve)
    if not write:                    # certification-only pass (reuse path)
        return 0, None, solved, unv_total
    fp = align_frames(fp)
    fk = align_frames(fk)
    write_gltf_morph(os.path.join(outdir, "morph_p.glb"), fp, tris)
    write_gltf_morph(os.path.join(outdir, "morph_k.glb"), fk, tris)
    return len(fp), None, solved, unv_total

def _build_net(job, morphs=True):
    """One directory per net under nets/, named v{V}{CLERS}: a database
    record (net.json) plus the net's artifacts (rb.glb, clers.glb,
    morph_p.glb, morph_k.glb, ideal_net.svg, clers_layout.svg). The
    page itself is rendered from the record by views.py."""
    import json
    from views import render_page, net_id
    name, nc = job
    faces = [tuple(int(x) for x in f.split(',')) for f in nc.split(';')]
    V = max(max(f) for f in faces)
    vname = f"v{V}{name}"
    nid = net_id(V, name)
    netdir = os.path.join(OUT, "nets", nid)
    os.makedirs(netdir, exist_ok=True)
    # stale morph GLBs never survive a build (G1 r5: deleted FIRST, before
    # store parsing / solving / hero work -- any failure return or raise
    # after this point cannot leave old uncertified morphs advertised)
    for fn in ("morph_p.glb", "morph_k.glb"):
        try:
            os.remove(os.path.join(netdir, fn))
        except FileNotFoundError:
            pass
    deg = {}
    for f in faces:
        for x in f:
            deg[x] = deg.get(x, 0) + 1
    maxdeg = max(deg.values())
    amax = 60.0 if maxdeg <= 6 else 360.0 / maxdeg
    alphas = (MORPH_ALPHAS if maxdeg <= 6 else
              [a * amax / 60.0 for a in MORPH_ALPHAS] + [amax])
    # consumer mode: committed bends (data/bends/<nid>.json) supply every
    # solved quantity; the solver runs only for rungs the store lacks.
    store = None
    spath = os.path.join(TOP, "data", "bends", f"{nid}.json")
    if os.path.exists(spath):
        st = json.load(open(spath))
        store = {"hero": {tuple(int(x) for x in k.split(',')): float(v)
                          for k, v in st["hero"].items()},
                 "morph": {round(m["alpha"], 6):
                           {tuple(int(x) for x in k.split(',')): float(v)
                            for k, v in m["bends"].items()}
                           for m in st["morph"]}}
    # Displayed artifacts are ALWAYS regenerated through the gates from
    # the committed bends (G1 r3): certifying a reconstruction while
    # reusing on-disk GLBs proves nothing about the bytes actually
    # served, and regeneration is deterministic (measured byte-stable),
    # so no reuse optimization is worth that hole. Store present =>
    # store-only; no store => producer mode (solve + persist).
    hero_bends = None      # freshly-solved hero bends (persisted to the store)
    if store:
        bends = store["hero"]
    elif maxdeg <= 6:
        bends = solve_prove_60(nc)
    else:
        bends = solve_alpha(nc, amax)
    if bends is None:
        return (vname, "SOLVE-FAIL")
    if not store:
        hero_bends = bends
    if maxdeg <= 6:
        glb_euclid(name, faces, V, bends, netdir)
    else:
        bd = {tuple(sorted(e)): b for e, b in bends.items()}
        posh, herr, hok, _ = develop_h_certified(faces, bd, math.radians(amax))
        if not hok:                  # deg-7 hero edge gate (G1 r3)
            raise RuntimeError(f"hero fails edge gate ({herr:.2e})")
        K = klein(posh)              # posh already centered (displayed)
        glb_hero(name, faces, V, {v: np.asarray(K[v]) for v in K}, netdir,
                 bends=bd)
    morph_note, morph_bends, n_unv = None, None, 0
    vpolicy = morphs and V > MORPH_VMAX
    if vpolicy:
        morphs = False
        morph_note = f"not built: v>{MORPH_VMAX} morph policy (PD 2026-07-24)"
    if not morphs:
        built = (f"skipped (v>{MORPH_VMAX} policy)" if vpolicy
                 else "skipped (morphs=False)")   # generation-time opt-out
    else:
        nframes, morph_note, morph_bends, n_unv = glb_movies(
            name, faces, V, nc, netdir,
            alphas=alphas, euclid_end=(maxdeg <= 6), stored=store)
        built = (f"omitted ({morph_note})" if morph_note
                 else f"built {nframes} frames")
    inet_path = os.path.join(netdir, "ideal_net.svg")
    if not os.path.exists(inet_path):
        inet = ideal_net_svg(nc, faces)
        if inet:
            with open(inet_path, "w") as f:
                f.write(inet)
    layout_path = os.path.join(netdir, "clers_layout.svg")
    if not os.path.exists(layout_path):
        with open(layout_path, "w") as f:
            f.write(clers_svg(name))
    E = len({tuple(sorted((a, b))) for f in faces for a, b in zip(f, f[1:] + f[:1])})
    have = {k: os.path.exists(os.path.join(netdir, fn)) for k, fn in
            (("rb", "rb.glb"), ("clers_glb", "clers.glb"),
             ("morph_p", "morph_p.glb"), ("morph_k", "morph_k.glb"),
             ("ideal_net", "ideal_net.svg"), ("clers_layout", "clers_layout.svg"))}
    recpath = os.path.join(netdir, "net.json")
    rec = json.load(open(recpath)) if os.path.exists(recpath) else {}
    rec.update({"id": nid, "name": vname, "clers": name, "v": V, "E": E,
                "F": len(faces), "netcode": nc, "artifacts": have,
                "maxdeg": maxdeg})
    if maxdeg > 6:
        rec["alpha_max"] = amax
    if maxdeg > 6 and not morph_note:
        rec["morph_labels"] = [f"{a:.1f}" for a in alphas]
    else:
        rec.pop("morph_labels", None)
    if morph_note:
        rec["morph_note"] = morph_note      # why the morphs are absent (audit)
    else:
        rec.pop("morph_note", None)
    if n_unv and not morph_note:
        # certify-where-resolvable caveat (PD ruling 2026-07-22): closure
        # at the deepest rung(s) sits below the float64 noise floor; the
        # frames are certified by the edge-length + dent gates.
        rec["morph_caveat"] = (f"closure unverifiable on {n_unv} events "
                               f"(float64 noise floor at this scale)")
    else:
        rec.pop("morph_caveat", None)
    rec.setdefault("flags", {})
    rec.setdefault("eisenstein", {"ancestors": [], "descendants": []})
    with open(recpath, "w") as f:
        json.dump(rec, f, indent=1)
    # persist the solved bends to the committed store (producer step): one
    # solver build populates data/bends/, and the consumer builder reads it
    # -- no solver / neo / network at build time. Written only when this net
    # was actually solved (fresh); reused nets keep their existing store.
    # persist ONLY a complete, gate-passing snapshot (G1 r4): a partial
    # or empty morph ladder written as a store would poison later
    # store-only builds ("store incomplete" forever). Incomplete solves
    # are simply not persisted; the next build re-attempts producer mode.
    if (hero_bends is not None and morph_note is None
            and morph_bends is not None and len(morph_bends) == len(alphas)):
        def _ser(bd):
            return {f"{min(e)},{max(e)}": float(bd[e]) for e in bd}
        store = {"clers": name, "v": V, "netcode": nc, "maxdeg": maxdeg,
                 "hero": _ser(hero_bends),
                 "morph": [{"alpha": a, "bends": _ser(bd)}
                           for a, bd in morph_bends.items()]}
        bdir = os.path.join(TOP, "data", "bends")
        os.makedirs(bdir, exist_ok=True)
        with open(os.path.join(bdir, f"{nid}.json"), "w") as bf:
            json.dump(store, bf)
    render_page(netdir)
    return (vname, f"OK morphs {built}")


def build_net(job, morphs=True):
    """Backstop wrapper: no single net may crash the whole Pool. Any
    unexpected exception becomes a BUILD-FAIL result for that net so the
    rest of the sweep continues (main() reports the FAIL list)."""
    try:
        return _build_net(job, morphs)
    except Exception as e:
        return (f"v?{job[0]}", f"BUILD-FAIL {type(e).__name__}: {e}")


def main(input_path=None):
    """Build records + artifacts + pages for the nets in input_path
    (default data/nets_pages.txt, lines: name netcode). Listing pages,
    galleries, and the front page are special.py's job."""
    os.makedirs(OUT, exist_ok=True)
    # viewer wrappers: source of truth is builders/assets/
    import shutil
    for w in ("morph.html", "turntable.html"):
        shutil.copy(os.path.join(HERE, "assets", w), os.path.join(OUT, w))
    vsrc = os.path.join(HERE, "assets", "vendor")
    if os.path.isdir(vsrc):
        shutil.copytree(vsrc, os.path.join(OUT, "vendor"), dirs_exist_ok=True)
    jobs = []
    with open(input_path or os.path.join(TOP, "data", "nets_pages.txt")) as f:
        for ln in f:
            t = ln.split()
            jobs.append((t[0], t[1]))
    # morphs are generated by default; set ATLAS_MORPHS=0 to skip morph
    # generation for this run (a compute choice -- e.g. giant eisenbuddies --
    # NOT a correctness cap: pages render morphs iff the record has them, and
    # morphs enter the record only through the certified gate in glb_movies).
    gen_morphs = os.environ.get("ATLAS_MORPHS", "1") != "0"
    worker = partial(build_net, morphs=gen_morphs)
    with Pool(6) as pool:
        results = pool.map(worker, jobs)
    fails = [n for n, msg in results if "FAIL" in msg]
    omitted = [n for n, msg in results if "omitted" in msg]
    for name, msg in results:
        print(name, msg, flush=True)
    print(f"built {len(results) - len(fails)}/{len(results)}"
          + (f"  morphs omitted (gate): {len(omitted)}" if omitted else "")
          + (f"  FAILURES: {fails}" if fails else ""), flush=True)
    return 1 if fails else 0     # G1: a failed net (incl. dented hero) is a
                                 # failed build -- nonzero exit, never silent


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
