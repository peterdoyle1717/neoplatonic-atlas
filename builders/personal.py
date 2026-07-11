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
from glb import retreat_to_incenter, write_gltf_like, write_gltf_groups
from realize_h import develop_h, klein, poincare, center
from walklib import develop
from clers_tools import clers_svg, COLORS

BIN = os.environ.get("DW_BIN", "/Users/doyle/Dropbox/neo/bendprover/csrc/euclid_lm_mp")
ALPHAS = [60.0 - 57.9 * (0.87 ** i) for i in range(24)][::-1]   # ~2.1 .. 59.9

RGB = {'A': (1.0, 0.0, 0.0), 'B': (1.0, 0.53, 0.0), 'C': (1.0, 0.8, 0.0),
       'D': (0.0, 0.67, 0.0), 'E': (0.0, 0.4, 1.0)}
BLACK = (0.0, 0.0, 0.0)

STYLE = ("body{font-family:Georgia,serif;max-width:680px;margin:2em auto;"
         "line-height:1.6;color:#222;padding:0 1em}"
         "h1{font-family:monospace;font-size:1.15em;word-break:break-all}"
         ".info{font-size:.9em;color:#555;margin:-.4em 0 1em}"
         ".cell{position:relative;width:100%;padding-bottom:88%}"
         ".cell model-viewer{position:absolute;top:0;left:0;width:100%;"
         "height:100%;background:#f0f0f0}"
         ".svgwrap{border:1px solid #ddd;padding:2%}"
         ".svgwrap svg{width:100%;height:auto}"
         ".label{text-align:center;font-size:.85em;color:#888;margin:.2em 0 1.2em}"
         "input[type=range]{width:100%}"
         "a{color:#06c}")

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


def glb_morphs(name, faces, V, nc, outdir):
    fidx = [(a - 1, b - 1, c - 1) for a, b, c in faces]
    frames = []
    for i, a in enumerate(ALPHAS):
        bends = solve_alpha(nc, a)
        if bends is None:
            frames = []          # contiguous from the ideal end
            continue
        bd = {tuple(sorted(e)): b for e, b in bends.items()}
        pos = center(develop_h(faces, bd, math.radians(a))[0])
        for proj, tag in ((poincare, "p"), (klein, "k")):
            P = proj(pos)
            verts = [tuple(map(float, P[v])) for v in range(1, V + 1)]
            v2, f2, mats = retreat_to_incenter(verts, fidx, 0.9)
            write_gltf_like(os.path.join(outdir, f"{name}_{tag}{i:02d}.glb"),
                            v2, f2, mats)
        frames.append((i, round(a, 2)))
    return frames


def slider(name, tag, frames, label):
    idxs = [i for i, _ in frames]
    alphas = {i: a for i, a in frames}
    import json as _json
    js_i = _json.dumps(idxs)
    js_a = _json.dumps({str(i): alphas[i] for i in idxs})
    last = idxs[-1]
    return (f'<div class=cell><model-viewer id="mv_{tag}" '
            f'src="../glb/{name}_{tag}{last:02d}.glb" camera-controls></model-viewer></div>'
            f'<input type=range min=0 max={len(idxs)-1} value={len(idxs)-1} '
            f'oninput=\'(function(k){{var I={js_i},A={js_a};var i=I[k];'
            f'document.getElementById("mv_{tag}").src="../glb/{name}_"+"{tag}"+'
            f'String(i).padStart(2,"0")+".glb";'
            f'document.getElementById("lb_{tag}").textContent="{label}, alpha = "+A[i]+" deg";}})(this.value)\'>'
            f'<div class=label id="lb_{tag}">{label}, alpha = {alphas[last]} deg</div>')


def build_net(job):
    name, nc = job
    faces = [tuple(int(x) for x in f.split(',')) for f in nc.split(';')]
    V = max(max(f) for f in faces)
    outdir = os.path.join(OUT, "glb")
    os.makedirs(outdir, exist_ok=True)
    bends = solve_prove_60(nc)
    if bends is None:
        return (name, "SOLVE-FAIL")
    glb_euclid(name, faces, V, bends, outdir)
    frames = glb_morphs(name, faces, V, nc, outdir)
    E = len({tuple(sorted((a, b))) for f in faces for a, b in zip(f, f[1:] + f[:1])})
    body = [f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>{name}</title>{MV}<style>{STYLE}</style></head><body>'
            f'<h1>{name}</h1>'
            f'<div class=info>v = {V} &middot; {len(faces)} faces &middot; {E} edges'
            f' &middot; <a href="index.html">v = {V} index</a></div>'
            f'<div class=cell><model-viewer src="../glb/{name}_rb.glb" '
            f'camera-controls></model-viewer></div>'
            f'<div class=label>the realization</div>']
    if frames:
        body.append(slider(name, "p", frames, "morph, Poincar&eacute;"))
        body.append(slider(name, "k", frames, "morph, Klein"))
    body.append(f'<div class=cell><model-viewer src="../glb/{name}_clers.glb" '
                f'camera-controls></model-viewer></div>'
                f'<div class=label>CLERS coloring</div>')
    body.append(f'<div class=svgwrap>{clers_svg(name)}</div>'
                f'<div class=label>CLERS layout</div>')
    body.append('</body></html>')
    vdir = os.path.join(OUT, str(V))
    os.makedirs(vdir, exist_ok=True)
    with open(os.path.join(vdir, f"{name}.html"), "w") as f:
        f.write('\n'.join(body))
    return (name, f"OK {len(frames)} frames")


def main():
    os.makedirs(os.path.join(OUT, "glb"), exist_ok=True)
    jobs = []
    with open(os.path.join(TOP, "data", "nets_v4_14.txt")) as f:
        for ln in f:
            name, nc = ln.split()
            jobs.append((name, nc))
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
        rows = [f'<!DOCTYPE html><html><head><meta charset=utf-8>'
                f'<title>v = {V}</title><style>{STYLE}</style></head><body>'
                f'<h1>v = {V}</h1><div class=info><a href="../index.html">all</a></div>']
        rows += [f'<p><a href="{n}.html">{n}</a></p>' for n in names]
        rows.append('</body></html>')
        with open(os.path.join(OUT, str(V), "index.html"), "w") as f:
            f.write('\n'.join(rows))
    master.append('</body></html>')
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write('\n'.join(master))
    print("indexes written", flush=True)


if __name__ == "__main__":
    main()
