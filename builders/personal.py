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

BIN = os.environ.get("DW_BIN", "/Users/doyle/Dropbox/neo/bendprover/csrc/euclid_lm_mp")
HOROZ = os.environ.get("HOROZ_BIN", "/Users/doyle/Dropbox/neo/ideal/src/horoz_c")
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

MV = ('<script type="module" src="https://ajax.googleapis.com/ajax/libs/'
      'model-viewer/3.5.0/model-viewer.min.js"></script>')


def solve_prove_60(nc):
    r = subprocess.run([BIN, "--prove", "--alpha", "60.0", "--name", "X", nc],
                       capture_output=True, text=True, timeout=1800)
    if "end" not in r.stdout:
        return None
    bends = {}
    for ln in r.stdout.splitlines():
        t = ln.split()
        if t and t[0] == "b":
            bends[(int(t[1]), int(t[2]))] = float(t[3]) * math.pi
    return bends


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


def glb_hero(name, faces, V, pos, outdir):
    """red-black + CLERS GLBs from given coordinates (Klein model for
    degree-7 nets at alpha_max)."""
    verts = [tuple(map(float, pos[v])) for v in range(1, V + 1)]
    fidx = [(a - 1, b - 1, c - 1) for a, b, c in faces]
    v2, f2, mats = retreat_to_incenter(verts, fidx, 0.9)
    write_gltf_like(os.path.join(outdir, "rb.glb"), v2, f2, mats)
    groups = [(BLACK, [f2[k] for k in range(len(f2)) if mats[k] == "border"])]
    for L, rgb in RGB.items():
        gf = [f2[7 * i + 6] for i, ch in enumerate(name) if ch == L]
        if gf:
            groups.append((rgb, gf))
    write_gltf_groups(os.path.join(outdir, "clers.glb"), v2, groups)


def glb_euclid(name, faces, V, bends, outdir):
    pos, _ = develop(faces, {tuple(sorted(e)): b for e, b in bends.items()})
    verts = [tuple(map(float, pos[v])) for v in range(1, V + 1)]
    fidx = [(a - 1, b - 1, c - 1) for a, b, c in faces]
    v2, f2, mats = retreat_to_incenter(verts, fidx, 0.9)
    write_gltf_like(os.path.join(outdir, "rb.glb"), v2, f2, mats)
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


def glb_movies(name, faces, V, nc, outdir, alphas=None, euclid_end=True):
    """two animated morph GLBs (Poincare, Klein): ideal end first,
    then either the exact Euclidean solid (alpha_max = 60) or the
    hyperbolic realization at the final rung (degree-7 nets:
    alpha_max = 360/maxdeg)."""
    grid = bary_grid(SUBDIV)
    fp, fk, tris = [], [], None
    for a in (alphas or MORPH_ALPHAS):
        bends = solve_alpha(nc, a)
        if bends is None:
            return 0
        bd = {tuple(sorted(e)): b for e, b in bends.items()}
        pos = center(develop_h(faces, bd, math.radians(a))[0])
        vk, tris = subdivided_frame(faces, klein(pos), grid)
        fk.append(vk)
        fp.append(klein_to_poincare(vk))
    if euclid_end:
        bends60 = solve_prove_60(nc)
        if bends60 is None:
            return 0
        pos60, _ = develop(faces, {tuple(sorted(e)): b for e, b in bends60.items()})
        ctr = sum(pos60.values()) / len(pos60)
        ve, tris = subdivided_frame(faces, {v: p - ctr for v, p in pos60.items()}, grid)
        fp.append(ve)
        fk.append(ve)
    fp = align_frames(fp)
    fk = align_frames(fk)
    write_gltf_morph(os.path.join(outdir, "morph_p.glb"), fp, tris)
    write_gltf_morph(os.path.join(outdir, "morph_k.glb"), fk, tris)
    return len(fp)

def build_net(job):
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
    deg = {}
    for f in faces:
        for x in f:
            deg[x] = deg.get(x, 0) + 1
    maxdeg = max(deg.values())
    amax = 60.0 if maxdeg <= 6 else 360.0 / maxdeg
    alphas = (MORPH_ALPHAS if maxdeg <= 6 else
              [a * amax / 60.0 for a in MORPH_ALPHAS] + [amax])
    if not (os.path.exists(os.path.join(netdir, "rb.glb"))
            and os.path.exists(os.path.join(netdir, "clers.glb"))):
        if maxdeg <= 6:
            bends = solve_prove_60(nc)
            if bends is None:
                return (vname, "SOLVE-FAIL")
            glb_euclid(name, faces, V, bends, netdir)
        else:
            bends = solve_alpha(nc, amax)
            if bends is None:
                return (vname, "SOLVE-FAIL")
            bd = {tuple(sorted(e)): b for e, b in bends.items()}
            pos = center(develop_h(faces, bd, math.radians(amax))[0])
            K = klein(pos)
            glb_hero(name, faces, V, {v: np.asarray(K[v]) for v in K}, netdir)
    if (os.path.exists(os.path.join(netdir, "morph_p.glb"))
            and os.path.exists(os.path.join(netdir, "morph_k.glb"))):
        built = "reused"
    else:
        nframes = glb_movies(name, faces, V, nc, netdir,
                             alphas=alphas, euclid_end=(maxdeg <= 6))
        built = f"built {nframes} frames"
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
        rec["morph_labels"] = [f"{a:.1f}" for a in alphas]
    rec.setdefault("flags", {})
    rec.setdefault("eisenstein", {"ancestors": [], "descendants": []})
    with open(recpath, "w") as f:
        json.dump(rec, f, indent=1)
    render_page(netdir)
    return (vname, f"OK morphs {built}")


def main(input_path=None):
    """Build records + artifacts + pages for the nets in input_path
    (default data/nets_pages.txt, lines: name netcode). Listing pages,
    galleries, and the front page are special.py's job."""
    os.makedirs(OUT, exist_ok=True)
    # viewer wrappers: source of truth is builders/assets/
    import shutil
    for w in ("morph.html", "turntable.html"):
        shutil.copy(os.path.join(HERE, "assets", w), os.path.join(OUT, w))
    jobs = []
    with open(input_path or os.path.join(TOP, "data", "nets_pages.txt")) as f:
        for ln in f:
            t = ln.split()
            jobs.append((t[0], t[1]))
    with Pool(6) as pool:
        results = pool.map(build_net, jobs)
    fails = [n for n, msg in results if "FAIL" in msg]
    for name, msg in results:
        print(name, msg, flush=True)
    print(f"built {len(results) - len(fails)}/{len(results)}"
          + (f"  FAILURES: {fails}" if fails else ""), flush=True)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
