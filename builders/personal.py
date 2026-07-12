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
ALPHAS = [60.0 - 57.9 * (0.87 ** i) for i in range(24)][::-1]   # ~2.1 .. 59.9

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
                       capture_output=True, text=True, timeout=300)
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
                       capture_output=True, text=True, timeout=180)
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


def glb_euclid(name, faces, V, bends, outdir):
    pos, _ = develop(faces, {tuple(sorted(e)): b for e, b in bends.items()})
    verts = [tuple(map(float, pos[v])) for v in range(1, V + 1)]
    fidx = [(a - 1, b - 1, c - 1) for a, b, c in faces]
    v2, f2, mats = retreat_to_incenter(verts, fidx, 0.9)
    write_gltf_like(os.path.join(outdir, f"{name}_rb.glb"), v2, f2, mats)
    # CLERS coloring: retreat emits 7 faces per original (6 border, 1 center)
    groups = [(BLACK, [f2[k] for k in range(len(f2)) if mats[k] == "border"])]
    for L, rgb in RGB.items():
        gf = [f2[7 * i + 6] for i, ch in enumerate(name) if ch == L]
        if gf:
            groups.append((rgb, gf))
    write_gltf_groups(os.path.join(outdir, f"{name}_clers.glb"), v2, groups)


def glb_movies(name, faces, V, nc, outdir):
    """two animated morph GLBs (Poincare, Klein), ideal end -> Euclidean."""
    fidx = [(a - 1, b - 1, c - 1) for a, b, c in faces]
    fp, fk, f2ref = [], [], None
    for a in ALPHAS:
        bends = solve_alpha(nc, a)
        if bends is None:
            fp, fk = [], []          # contiguous from the ideal end
            continue
        bd = {tuple(sorted(e)): b for e, b in bends.items()}
        pos = center(develop_h(faces, bd, math.radians(a))[0])
        for proj, acc in ((poincare, fp), (klein, fk)):
            P = proj(pos)
            verts = [tuple(map(float, P[v])) for v in range(1, V + 1)]
            v2, f2, _ = retreat_to_incenter(verts, fidx, 0.9)
            acc.append(v2)
            f2ref = f2
    if len(fp) >= 2:
        write_gltf_morph(os.path.join(outdir, f"{name}_morph_p.glb"), fp, f2ref)
        write_gltf_morph(os.path.join(outdir, f"{name}_morph_k.glb"), fk, f2ref)
    return len(fp)

def build_net(job):
    name, nc = job
    faces = [tuple(int(x) for x in f.split(',')) for f in nc.split(';')]
    V = max(max(f) for f in faces)
    outdir = os.path.join(OUT, "glb")
    os.makedirs(outdir, exist_ok=True)
    if not (os.path.exists(os.path.join(outdir, f"{name}_rb.glb"))
            and os.path.exists(os.path.join(outdir, f"{name}_clers.glb"))):
        bends = solve_prove_60(nc)
        if bends is None:
            return (name, "SOLVE-FAIL")
        glb_euclid(name, faces, V, bends, outdir)
    if (os.path.exists(os.path.join(outdir, f"{name}_morph_p.glb"))
            and os.path.exists(os.path.join(outdir, f"{name}_morph_k.glb"))):
        nframes = 24
    else:
        nframes = glb_movies(name, faces, V, nc, outdir)
    E = len({tuple(sorted((a, b))) for f in faces for a, b in zip(f, f[1:] + f[:1])})

    def cell_iframe(src, label):
        return (f'<div><div class=cell><iframe src="{src}"></iframe></div>'
                f'<div class=label>{label}</div></div>')

    body = [f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>{name}</title><style>{STYLE}</style></head><body>'
            f'<nav><a href="index.html">{V} vertices</a> &middot; '
            f'<a href="../index.html">neoplatonic solids</a></nav>'
            f'<h1>{name}</h1>'
            f'<p class=info>V={V} &nbsp; E={E} &nbsp; F={len(faces)}</p>'
            f'<p class=hint>Models can be manipulated.</p>',
            '<div class=pair>',
            cell_iframe(f'../turntable.html?file=glb/{name}_rb.glb', 'Euclidean')]
    inet = ideal_net_svg(nc, faces)
    if inet:
        body.append(f'<div><div class=cell><div class=svgwrap>{inet}</div></div>'
                    f'<div class=label>ideal net</div></div>')
    body.append('</div>')
    if nframes >= 2:
        body += ['<div class=pair>',
                 cell_iframe(f'../morph.html?file=glb/{name}_morph_p.glb',
                             'ideal to Euclidean, Poincar&eacute;'),
                 cell_iframe(f'../morph.html?file=glb/{name}_morph_k.glb',
                             'ideal to Euclidean, Klein'),
                 '</div>']
    body += ['<div class=pair>',
             cell_iframe(f'../turntable.html?file=glb/{name}_clers.glb',
                         'CLERS colored'),
             f'<div><div class=cell><div class=svgwrap>{clers_svg(name)}</div></div>'
             f'<div class=label>CLERS layout</div></div>',
             '</div>', '</body></html>']
    vdir = os.path.join(OUT, str(V))
    os.makedirs(vdir, exist_ok=True)
    with open(os.path.join(vdir, f"{name}.html"), "w") as f:
        f.write('\n'.join(body))
    return (name, f"OK {nframes} frames")


def main(input_path=None, exemplars=False):
    """Build pages for the nets in input_path (default data/nets_v4_14.txt,
    lines: name netcode [extra columns ignored]). exemplars=True is for
    extra sets beyond the browse range: per-v indexes list just what was
    built and the master index is left alone (special.py owns it)."""
    os.makedirs(os.path.join(OUT, "glb"), exist_ok=True)
    # viewer wrappers: source of truth is builders/assets/
    import shutil
    for w in ("morph.html", "turntable.html"):
        shutil.copy(os.path.join(HERE, "assets", w), os.path.join(OUT, w))
    jobs = []
    with open(input_path or os.path.join(TOP, "data", "nets_v4_14.txt")) as f:
        for ln in f:
            t = ln.split()
            jobs.append((t[0], t[1]))
    with Pool(6) as pool:
        results = pool.map(build_net, jobs)
    for name, msg in results:
        print(name, msg, flush=True)
    # per-v indexes and master index (glb paths are relative to the v-dirs,
    # so symlink glb into each v-dir? no: pages live in <v>/ and reference
    # glb/... -> place a relative link one level up instead)
    byv = {}
    for name, nc in jobs:
        V = max(max(int(x) for x in f.split(',')) for f in nc.split(';'))
        byv.setdefault(V, []).append(name)
    master = ['<!DOCTYPE html><html><head><meta charset=utf-8>'
              f'<title>personal pages</title><style>{STYLE}</style></head><body>'
              '<h1>Prime nets, v &le; 14</h1>']
    for V in sorted(byv):
        names = sorted(byv[V])
        master.append(f'<p><a href="{V}/index.html">v = {V}</a> ({len(names)} nets)</p>')
        note = (' &middot; exemplars only, not the full set at this size'
                if exemplars else '')
        rows = [f'<!DOCTYPE html><html><head><meta charset=utf-8>'
                f'<title>v = {V}</title><style>{STYLE}</style></head><body>'
                f'<h1>v = {V}</h1><div class=info>'
                f'<a href="../index.html">all</a>{note}</div>']
        rows += [f'<p><a href="{n}.html">{n}</a></p>' for n in names]
        rows.append('</body></html>')
        with open(os.path.join(OUT, str(V), "index.html"), "w") as f:
            f.write('\n'.join(rows))
    if not exemplars:
        master.append('</body></html>')
        with open(os.path.join(OUT, "index.html"), "w") as f:
            f.write('\n'.join(master))
    print("indexes written", flush=True)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main(sys.argv[1], exemplars=True)
    else:
        main()
