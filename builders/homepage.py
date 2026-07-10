"""homepage.py -- full per-net pages for v <= 13, old-atlas style.

Per net: Euclidean model | Poincare morph slider; Klein morph slider |
UHS horoballs (salvaged asset); CLERS colored (salvaged asset) | CLERS
unfolding (regenerated, validated against the old pages); then every
denting with gap and its own morph-toward-ideal slider (frames for as
many alpha rungs as the gated solve converges).

Morph frames: seedless `euclid_lm_mp --prove --alpha A [--dents sigma]`
per rung, developed in H^3 by realize_h, shown in the Poincare or Klein
ball at true scale.
"""
import json, glob, math, os, subprocess, sys, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
SITE = os.path.join(TOP, "site")
sys.path.insert(0, HERE)
from glb import retreat_to_incenter, write_gltf_like
from walklib import automorphisms, develop, clearance, NAMES, STYLE
from realize_h import develop_h, klein, poincare, center

BIN = os.environ.get("DW_BIN", "/Users/doyle/Dropbox/neo/bendprover/csrc/euclid_lm_mp")
ALPHAS = [60.0 - 57.9 * (0.87 ** i) for i in range(24)][::-1]   # ~2.1 .. 59.9

PAGE_STYLE = """body{font-family:Georgia,serif;max-width:680px;margin:2em auto;line-height:1.6;color:#222;padding:0 1em}h1{font-family:monospace;font-size:1.2em;word-break:break-all}h1 a{color:inherit;text-decoration:none}.info{font-size:.9em;color:#555;margin:-.5em 0 .5em}.hint{font-size:.8em;color:#aaa;font-style:italic;margin-bottom:1em}.pair{display:grid;grid-template-columns:1fr 1fr;gap:.8em;margin-bottom:1em}.cell{position:relative;width:100%;padding-bottom:100%}.cell model-viewer{position:absolute;top:0;left:0;width:100%;height:100%;background:#f0f0f0}.cell .svgwrap{position:absolute;top:0;left:0;width:100%;height:100%;display:flex;align-items:center;justify-content:center;border:1px solid #ddd;box-sizing:border-box}.cell .svgwrap svg{max-width:90%;max-height:90%}.label{text-align:center;font-size:.8em;color:#888;margin-top:.2em}input[type=range]{width:100%}.dent{margin-top:1.5em;border-top:1px solid #ddd;padding-top:.6em}.dent h3{font-family:monospace;font-size:.95em;margin:.2em 0}.code{font-family:monospace;font-size:.85em;word-break:break-all;color:#444;margin-top:2em;border-top:1px solid #ddd;padding-top:1em}"""


def solve_alpha(nc, alpha, dents):
    args = [BIN, "--prove", "--alpha", f"{alpha:.6f}", "--name", "H"]
    if dents:
        args += ["--dents", ",".join(map(str, sorted(dents)))]
    args.append(nc)
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return None
    if "end" not in r.stdout:
        return None
    bends = {}
    for ln in r.stdout.splitlines():
        t = ln.split()
        if t and t[0] == "b":
            bends[(int(t[1]), int(t[2]))] = (0.0 if t[3] == "0" else float(t[3])) * math.pi
    return bends


def morph_frames(name, nc, faces, V, dents, outdir, tag):
    """GLB frames along the alpha ladder; returns (frames, alphas)."""
    os.makedirs(outdir, exist_ok=True)
    fidx = [(a - 1, b - 1, c - 1) for a, b, c in faces]
    done = []
    for i, a in enumerate(ALPHAS):
        bends = solve_alpha(nc, a, dents)
        if bends is None:
            done = []          # ladder must be contiguous from the ideal end;
            continue           # restart collection at the next rung
        pos = center(develop_h(faces, bends, math.radians(a))[0])
        for proj, lab in ((poincare, "p"), (klein, "k")):
            P = proj(pos)
            verts = [tuple(P[v]) for v in range(1, V + 1)]
            v2, f2, mats = retreat_to_incenter(verts, fidx, 0.9)
            write_gltf_like(os.path.join(outdir, f"{tag}_{lab}{i:02d}.glb"), v2, f2, mats)
        done.append((i, a))
    return done


def slider(tag, frames, viewers):
    """HTML: one range input driving the given (elementid, lab) viewers."""
    idxs = [i for i, _ in frames]
    alphas = {i: a for i, a in frames}
    first = idxs[-1]           # start at the Euclidean end
    cells = "".join(
        f'<div><div class=cell><model-viewer id="{tag}{lab}" '
        f'src="glb/{tag}_{lab}{first:02d}.glb" camera-orbit="0deg 100deg auto" '
        f'camera-controls interaction-prompt=none></model-viewer></div>'
        f'<div class=label>{title}</div></div>'
        for lab, title in viewers)
    js_idx = json.dumps(idxs)
    js_alp = json.dumps({str(i): round(alphas[i], 2) for i in idxs})
    labs = json.dumps([lab for lab, _ in viewers])
    return (f'<div class=pair>{cells}</div>'
            f'<input type=range id="s{tag}" min=0 max={len(idxs)-1} value={len(idxs)-1}>'
            f'<div class=label id="l{tag}"></div>'
            f'<script>(function(){{const idx={js_idx},alp={js_alp},labs={labs};'
            f'const s=document.getElementById("s{tag}");'
            f'function u(){{const i=idx[+s.value];'
            f'labs.forEach(l=>document.getElementById("{tag}"+l).src='
            f'`glb/{tag}_`+l+String(i).padStart(2,"0")+".glb");'
            f'document.getElementById("l{tag}").textContent="alpha = "+alp[i]+" deg";}}'
            f's.addEventListener("input",u);u();}})();</script>')


def build_one(args):
    name, nc, walk, rec_bends = args
    faces = [tuple(int(x) for x in f.split(",")) for f in nc.split(";")]
    V = max(v for f in faces for v in f)
    E = len(set(tuple(sorted((f[i], f[(i+1)%3]))) for f in faces for i in range(3)))
    outdir = os.path.join(SITE, "web", str(V))
    glbdir = os.path.join(outdir, "glb")
    os.makedirs(glbdir, exist_ok=True)
    naut = len(automorphisms(faces, V))

    body = [f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>{name}</title>'
            f'<script type=module src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js"></script>'
            f'<style>{PAGE_STYLE}</style></head><body>'
            f'<nav><a href="../../">neoplatonic solids</a></nav><h1>{name}</h1>']

    pancake = rec_bends is not None and all(t in ("0", "1", "-1") for t in rec_bends.values())
    nflat = 0 if rec_bends is None else sum(1 for t in rec_bends.values() if t == "0")
    ndent = max(len(walk["atlas"]) - 1, 0) if walk else 0
    info = f"V={V} &nbsp; E={E} &nbsp; F={len(faces)} &nbsp; |Aut|={naut}"
    if pancake: info += " &nbsp; pancake"
    if nflat and not pancake: info += f" &nbsp; {nflat} flat edges"
    info += f" &nbsp; {ndent} dentings"
    body.append(f'<p class=info>{info}</p><p class=hint>Models can be manipulated; '
                f'sliders morph between ideal (left) and Euclidean (right).</p>')

    # Euclidean model + Poincare/Klein morphs
    if not pancake and rec_bends is not None:
        bends = {k: (0.0 if t == "0" else float(t)) * math.pi for k, t in rec_bends.items()}
        pos, _ = develop(faces, bends)
        ctr = np.mean([pos[v] for v in range(1, V + 1)], axis=0)
        verts = [tuple(pos[v] - ctr) for v in range(1, V + 1)]
        v2, f2, mats = retreat_to_incenter(verts, [(a-1, b-1, c-1) for a, b, c in faces], 0.9)
        write_gltf_like(os.path.join(glbdir, f"{name}_euclid.glb"), v2, f2, mats)
        frames = morph_frames(name, nc, faces, V, None, glbdir, name)
        body.append(f'<div class=pair><div><div class=cell>'
                    f'<model-viewer src="glb/{name}_euclid.glb" camera-orbit="0deg 100deg auto" '
                    f'camera-controls interaction-prompt=none></model-viewer></div>'
                    f'<div class=label>Euclidean</div></div>'
                    f'<div><div class=cell><div class=svgwrap>' )
        from clers_tools import clers_svg
        body.append(clers_svg(name))
        body.append('</div></div><div class=label>CLERS unfolding</div></div></div>')
        if len(frames) >= 3:
            body.append(slider(name, frames,
                               [("p", "Poincar&eacute; ball"), ("k", "Klein ball")]))
    else:
        from clers_tools import clers_svg
        body.append('<div class=pair><div><div class=cell><div class=svgwrap>')
        body.append(clers_svg(name))
        body.append('</div></div><div class=label>CLERS unfolding</div></div></div>')

    # salvaged assets: CLERS colored + UHS horoballs
    cg = os.path.join(TOP, "data", "clers_glb", str(V), f"{name}.glb")
    ig = os.path.join(TOP, "data", "ideal_glb", str(V), f"{name}.glb")
    row = []
    if os.path.exists(cg):
        os.makedirs(os.path.join(SITE, "clers_glb", str(V)), exist_ok=True)
        dst = os.path.join(SITE, "clers_glb", str(V), f"{name}.glb")
        open(dst, "wb").write(open(cg, "rb").read())
        row.append((f"../../clers_glb/{V}/{name}.glb", "CLERS colored"))
    if os.path.exists(ig):
        os.makedirs(os.path.join(SITE, "ideal", str(V)), exist_ok=True)
        dst = os.path.join(SITE, "ideal", str(V), f"{name}.glb")
        open(dst, "wb").write(open(ig, "rb").read())
        row.append((f"../../ideal/{V}/{name}.glb", "UHS horoballs"))
    if row:
        body.append('<div class=pair>')
        for src, lab in row:
            body.append(f'<div><div class=cell><model-viewer src="{src}" '
                        f'camera-orbit="0deg 100deg auto" camera-controls '
                        f'interaction-prompt=none></model-viewer></div>'
                        f'<div class=label>{lab}</div></div>')
        body.append('</div>')

    # dentings, each with model + morph toward ideal
    if walk and ndent:
        perms = [tuple(m[v] for v in range(1, V + 1)) for m in automorphisms(faces, V)]
        seen = {}
        for key in sorted(walk["atlas"]):
            if not key: continue
            Dk = frozenset(int(x) for x in key.split(","))
            canon = min(tuple(sorted(p[v-1] for v in Dk)) for p in perms)
            if canon not in seen: seen[canon] = key
        for canon, key in sorted(seen.items(), key=lambda kv: (len(kv[0]), kv[0])):
            bends = {tuple(int(x) for x in k.split(",")): v
                     for k, v in walk["atlas"][key].items()}
            pos, _ = develop(faces, bends)
            gap = clearance(faces, pos)
            ctr = np.mean([pos[v] for v in range(1, V + 1)], axis=0)
            verts = [tuple(pos[v] - ctr) for v in range(1, V + 1)]
            v2, f2, mats = retreat_to_incenter(verts, [(a-1,b-1,c-1) for a,b,c in faces], 0.9)
            dtag = "D" + "-".join(map(str, canon))
            write_gltf_like(os.path.join(glbdir, f"{name}_{dtag}.glb"), v2, f2, mats)
            dstr = "{" + ",".join(map(str, canon)) + "}"
            body.append(f'<div class=dent><h3>denting {dstr} &nbsp; '
                        f'<span style="color:#888;font-size:.85em">gap {gap:.3f}</span></h3>')
            frames = morph_frames(name, nc, faces, V, set(canon), glbdir, f"{name}_{dtag}")
            if len(frames) >= 3:
                lo = min(a for _, a in frames)
                body.append(f'<div class=pair><div><div class=cell>'
                            f'<model-viewer src="glb/{name}_{dtag}.glb" '
                            f'camera-orbit="0deg 100deg auto" camera-controls '
                            f'interaction-prompt=none></model-viewer></div>'
                            f'<div class=label>Euclidean, dented</div></div>'
                            f'<div><div class=cell></div><div class=label>'
                            f'dented branch reaches alpha = {lo:.1f} deg</div></div></div>')
                body.append(slider(f"{name}_{dtag}", frames,
                                   [("p", "Poincar&eacute;"), ("k", "Klein")]))
            else:
                body.append(f'<div class=pair><div><div class=cell>'
                            f'<model-viewer src="glb/{name}_{dtag}.glb" '
                            f'camera-orbit="0deg 100deg auto" camera-controls '
                            f'interaction-prompt=none></model-viewer></div>'
                            f'<div class=label>Euclidean, dented (no morph: gated solve '
                            f'fails away from 60&deg;)</div></div></div>')
            body.append('</div>')

    body.append(f'<p class=code>{name}<br>{nc}</p></body></html>')
    open(os.path.join(outdir, f"{name}.html"), "w").write("\n".join(body))
    return name


def build_all():
    recs = {}
    name = None; faces = None; bends = {}
    for ln in open(os.path.join(TOP, "data", "records.bends")):
        t = ln.split()
        if not t: continue
        if t[0] == "net": name = t[1]; faces = None; bends = {}
        elif t[0] == "faces": faces = t[1]
        elif t[0] == "b": bends[(int(t[1]), int(t[2]))] = t[3]
        elif t[0] == "end" and faces: recs[name] = (faces, dict(bends))
    walks = {}
    for f in sorted(glob.glob(os.path.join(TOP, "data", "walks", "atlas_*.json"))):
        d = json.load(open(f))
        walks[NAMES.get(d["netcode"], "?")] = d
    jobs = [(nm, fc, walks.get(nm), bd) for nm, (fc, bd) in sorted(recs.items())]
    from multiprocessing import Pool
    with Pool(8) as p:
        for nm in p.imap_unordered(build_one, jobs):
            print("  page", nm, flush=True)
    print(f"homepages: {len(jobs)} nets")


if __name__ == "__main__":
    build_all()
