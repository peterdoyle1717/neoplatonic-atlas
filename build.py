#!/usr/bin/env python3
"""Rebuild the atlas site/ from data/, wholesale. Rerunnable; nothing in
site/ is hand-edited.

  data/records.bends -- solver records (FORMAT.md) for the working v-range
  data/walks/        -- dent-walk atlases (bends per dent set, embcheck-gated)
  data/names.tsv     -- canonical CLERS name <-> face-list netcode

Modules: dentings, convex (incl. pancakes), floppers, symmetry, deep
dents, index. Morph movies are cut separately (need the solver binary)
and land in site/morph-*/.
"""
import json, glob, math, os, sys, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
sys.path.insert(0, os.path.join(HERE, "builders"))
from glb import retreat_to_incenter, write_gltf_like
from walklib import automorphisms, develop, clearance, NAMES, STYLE

ATLAS_OLD = "https://math.dartmouth.edu/~doyle/docs/atlas/"

# ---------------------------------------------------------------- records
def load_records():
    recs = {}
    name = None; faces = None; bends = {}
    for ln in open(os.path.join(HERE, "data", "records.bends")):
        t = ln.split()
        if not t: continue
        if t[0] == "net": name = t[1]; faces = None; bends = {}
        elif t[0] == "faces":
            faces = [tuple(int(x) for x in f.split(",")) for f in t[1].split(";")]
        elif t[0] == "b": bends[(int(t[1]), int(t[2]))] = t[3]
        elif t[0] == "end" and faces: recs[name] = (faces, dict(bends))
    return recs

def load_walks():
    walks = {}
    for f in sorted(glob.glob(os.path.join(HERE, "data", "walks", "atlas_*.json"))):
        d = json.load(open(f))
        walks[NAMES.get(d["netcode"], d["netcode"][:20])] = d
    return walks

# ---------------------------------------------------------------- helpers
def model_glb(outdir, name, tag, faces, bends_rad, V):
    """develop, write GLB with content-hashed filename; returns (file, gap)."""
    pos, apex = develop(faces, bends_rad)
    gap = clearance(faces, pos)
    ctr = np.mean([pos[v] for v in range(1, V + 1)], axis=0)
    verts = [tuple(pos[v] - ctr) for v in range(1, V + 1)]
    fidx = [(a - 1, b - 1, c - 1) for a, b, c in faces]
    v2, f2, mats = retreat_to_incenter(verts, fidx, 0.9)
    hid = hashlib.sha1(json.dumps(sorted(map(repr, bends_rad.items()))).encode()).hexdigest()[:8]
    fn = f"{name}__{tag}.{hid}.glb"
    write_gltf_like(os.path.join(outdir, fn), v2, f2, mats)
    return fn, gap

def header(title):
    return (f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>{title} - Neoplatonic solids</title>'
            f'<script type=module src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js"></script>'
            f'<style>{STYLE}</style></head><body>'
            f'<h1><a href="../">Neoplatonic solids</a> - {title}</h1>')

def cell(glbrel, caption, sub=""):
    return (f'<div class=item><div class=cell><model-viewer src="{glbrel}" '
            f'camera-orbit="0deg 100deg auto" camera-controls interaction-prompt=none>'
            f'</model-viewer></div><span class=d>{caption}</span>'
            f'{f" <span class=o>{sub}</span>" if sub else ""}</div>')

def nethead(V, name):
    return (f'<h2><a href="../web/{V}/{name}.html">{name}</a> '
            f'<span class=v>v={V}</span></h2>')

def emit(path, html):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(html)

# ---------------------------------------------------------------- dentings
def build_dentings(walks):
    out = os.path.join(SITE, "dentings")
    os.makedirs(os.path.join(out, "glb"), exist_ok=True)
    entries = []          # (V, name, [(D, orb, glbfile, gap), ...]) dentable only
    deepest = []          # feed for the deep-dents module
    for name, d in sorted(walks.items()):
        if len(d["atlas"]) <= 1: continue
        V, nc = d["V"], d["netcode"]
        faces = [tuple(int(x) for x in fc.split(",")) for fc in nc.split(";")]
        perms = [tuple(m[v] for v in range(1, V + 1)) for m in automorphisms(faces, V)]
        seen = {}
        for key in sorted(d["atlas"]):
            if not key:
                seen[()] = [key, 1]; continue
            Dk = frozenset(int(x) for x in key.split(","))
            canon = min(tuple(sorted(p[v - 1] for v in Dk)) for p in perms)
            if canon in seen: seen[canon][1] += 1
            else: seen[canon] = [key, 1]
        row = []
        for canon, (key, orb) in sorted(seen.items(), key=lambda kv: (len(kv[0]), kv[0])):
            bends = {tuple(int(x) for x in k.split(",")): v
                     for k, v in d["atlas"][key].items()}
            tag = "Dempty" if not canon else "D" + "-".join(map(str, canon))
            fn, gap = model_glb(os.path.join(out, "glb"), name, tag, faces, bends, V)
            row.append((list(canon), orb, fn, gap))
            if canon: deepest.append((len(canon), V, name, canon, fn, gap))
        entries.append((V, name, row))
    entries.sort(key=lambda e: (e[0], e[1]), reverse=True)   # richest first

    def render(rows, title, desc, out_html):
        body = [header(title), f'<p class=desc>{desc}</p>']
        for V, name, row in rows:
            body.append(nethead(V, name) + '<div class=grid>')
            for D, orb, fn, gap in row:
                dstr = "&empty;" if not D else "{" + ",".join(map(str, D)) + "}"
                sub = (f"&times;{orb} " if orb > 1 else "") + (f"gap {gap:.3f}" if D else "")
                body.append(cell(f"glb/{fn}", dstr, sub.strip()))
            body.append('</div>')
        body.append('</body></html>')
        emit(out_html, "\n".join(body))

    small = [e for e in entries if e[0] <= 12]
    v13 = [e for e in entries if e[0] == 13]
    nd = lambda es: sum(1 for e in es for r in e[2] if r[0])
    render(small, "Dentings",
           f"Every prime 6-net with v &le; 12 that has an embedded denting, richest first, "
           f"showing all of its dentings, one model per symmetry orbit, starting from the "
           f"undented realization (&empty;). &times;k marks an orbit of k dent sets; gap is "
           f"the least distance between vertex-disjoint faces, in edge lengths. "
           f"{len(small)} nets, {nd(small)} dentings. Every model is embedded and certified. "
           f'The v = 13 dentings ({nd(v13)} across {len(v13)} nets) are <a href="v13.html">here</a>.',
           os.path.join(out, "index.html"))
    render(v13, "Dentings, v = 13",
           f'Every prime 6-net with v = 13 that has an embedded denting; {nd(v13)} dentings '
           f'across {len(v13)} nets. Back to <a href="index.html">v &le; 12</a>.',
           os.path.join(out, "v13.html"))
    print(f"dentings: {len(entries)} nets, {nd(entries)} dentings")
    return deepest

# ---------------------------------------------------------------- convex
def build_convex(recs):
    out = os.path.join(SITE, "convex")
    os.makedirs(os.path.join(out, "glb"), exist_ok=True)
    rows = []
    for name, (faces, btok) in sorted(recs.items()):
        V = max(v for f in faces for v in f)
        pancake = all(t in ("0", "1", "-1") for t in btok.values())
        if pancake:
            rows.append((V, name, None, True)); continue
        vals = [0.0 if t == "0" else float(t) for t in btok.values()]
        if min(vals) < 0: continue
        bends = {k: (0.0 if t == "0" else float(t)) * math.pi for k, t in btok.items()}
        fn, gap = model_glb(os.path.join(out, "glb"), name, "convex", faces, bends, V)
        rows.append((V, name, fn, False))
    rows.sort(key=lambda r: (r[0], r[1]))
    ns, np_ = sum(1 for r in rows if not r[3]), sum(1 for r in rows if r[3])
    body = [header("Convex"),
            f'<p class=desc>Every prime 6-net with v &le; 13 whose neoplatonic realization is '
            f'convex (all bends &ge; 0), in canonical order, pancakes included: a pancake is '
            f'the degenerate doubly covered convex case, all bends exactly 0 or gem/2. '
            f'{ns} solids and {np_} pancakes.</p><div class=grid>']
    for V, name, fn, pancake in rows:
        cap = f'<a href="../web/{V}/{name}.html">{name}</a>'
        if pancake:
            body.append(f'<div class=item><div class=cell></div>'
                        f'<span class=d>{cap}</span> <span class=o>v={V} pancake (flat)</span></div>')
        else:
            body.append(cell(f"glb/{fn}", cap, f"v={V}"))
    body.append('</div></body></html>')
    emit(os.path.join(out, "index.html"), "\n".join(body))
    print(f"convex: {ns} solids + {np_} pancakes")

# ---------------------------------------------------------------- floppers
def build_floppers(recs):
    out = os.path.join(SITE, "floppers")
    os.makedirs(os.path.join(out, "glb"), exist_ok=True)
    rows = []
    for name, (faces, btok) in sorted(recs.items()):
        if all(t in ("0", "1", "-1") for t in btok.values()): continue
        nflat = sum(1 for t in btok.values() if t == "0")
        if nflat == 0: continue
        V = max(v for f in faces for v in f)
        bends = {k: (0.0 if t == "0" else float(t)) * math.pi for k, t in btok.items()}
        fn, gap = model_glb(os.path.join(out, "glb"), name, "flop", faces, bends, V)
        rows.append((V, name, fn, nflat))
    rows.sort(key=lambda r: (r[0], r[1]))
    body = [header("Floppers"),
            f'<p class=desc>Every prime 6-net with v &le; 13 whose realization has exactly flat '
            f'edges (bend identically 0), in canonical order &mdash; the flat regions are where '
            f'the solid flops. {len(rows)} nets.</p><div class=grid>']
    for V, name, fn, nflat in rows:
        cap = f'<a href="../web/{V}/{name}.html">{name}</a>'
        body.append(cell(f"glb/{fn}", cap, f"v={V}, {nflat} flat edges"))
    body.append('</div></body></html>')
    emit(os.path.join(out, "index.html"), "\n".join(body))
    print(f"floppers: {len(rows)} nets")

# ---------------------------------------------------------------- symmetry
def build_symmetry(recs, walks):
    out = os.path.join(SITE, "symmetry")
    os.makedirs(os.path.join(out, "glb"), exist_ok=True)
    rows = []
    for name, (faces, btok) in recs.items():
        if all(t in ("0", "1", "-1") for t in btok.values()): continue
        V = max(v for f in faces for v in f)
        naut = len(automorphisms(faces, V))
        if naut < 6: continue
        bends = {k: (0.0 if t == "0" else float(t)) * math.pi for k, t in btok.items()}
        fn, gap = model_glb(os.path.join(out, "glb"), name, "sym", faces, bends, V)
        nd = len(walks.get(name, {}).get("atlas", {})) - 1
        rows.append((naut, V, name, fn, max(nd, 0)))
    rows.sort(key=lambda r: (-r[0], r[1], r[2]))
    body = [header("Symmetry"),
            f'<p class=desc>Prime 6-nets with v &le; 13 and at least 6 automorphisms, most '
            f'symmetric first. {len(rows)} nets.</p><div class=grid>']
    for naut, V, name, fn, nd in rows:
        cap = f'<a href="../web/{V}/{name}.html">{name}</a>'
        body.append(cell(f"glb/{fn}", cap, f"v={V}, |Aut|={naut}, {nd} dentings"))
    body.append('</div></body></html>')
    emit(os.path.join(out, "index.html"), "\n".join(body))
    print(f"symmetry: {len(rows)} nets")

# ---------------------------------------------------------------- deep dents
def build_deepdents(deepest):
    out = os.path.join(SITE, "deepdents")
    os.makedirs(out, exist_ok=True)
    deepest.sort(key=lambda r: (-r[0], r[1], r[2]))
    top = deepest[:16]
    body = [header("Deepest dents"),
            f'<p class=desc>The largest dent sets found by the walks (v &le; 13), one model per '
            f'symmetry orbit; gap in edge lengths.</p><div class=grid>']
    for n, V, name, canon, fn, gap in top:
        dstr = "{" + ",".join(map(str, canon)) + "}"
        cap = f'<a href="../web/{V}/{name}.html">{name}</a> {dstr}'
        body.append(cell(f"../dentings/glb/{fn}", cap, f"v={V}, |D|={n}, gap {gap:.3f}"))
    body.append('</div></body></html>')
    emit(os.path.join(out, "index.html"), "\n".join(body))
    print(f"deepdents: top {len(top)} of {len(deepest)}")

# ---------------------------------------------------------------- index
def build_index():
    body = (f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>Neoplatonic solids - atlas2</title><style>{STYLE}</style></head><body>'
            f'<h1>Neoplatonic solids &mdash; rebuilt atlas (working slice v &le; 13)</h1>'
            f'<p class=desc>Regenerated from certified records and dent-walk data by '
            f'<code>build.py</code>; nothing hand-edited. The deployed atlas is '
            f'<a href="{ATLAS_OLD}">here</a>.</p><ul>'
            f'<li><a href="dentings/">Dentings</a> &mdash; every embedded denting, mod symmetry</li>'
            f'<li><a href="convex/">Convex</a> &mdash; including pancakes</li>'
            f'<li><a href="floppers/">Floppers</a> &mdash; exactly flat edges</li>'
            f'<li><a href="symmetry/">Symmetry</a> &mdash; most symmetric nets</li>'
            f'<li><a href="deepdents/">Deepest dents</a></li>'
            f'<li><a href="morph-icosahedron/">Morph: the icosahedron, ideal to Euclidean</a></li>'
            f'</ul></body></html>')
    emit(os.path.join(SITE, "index.html"), body)
    print("index written")

if __name__ == "__main__":
    recs = load_records()
    walks = load_walks()
    deepest = build_dentings(walks)
    build_convex(recs)
    build_floppers(recs)
    build_symmetry(recs, walks)
    build_deepdents(deepest)
    build_index()
    if "--no-homepages" not in sys.argv:
        import homepage
        homepage.build_all()
