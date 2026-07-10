#!/usr/bin/env python3
"""Build the atlas 'failures' gallery: embedded dented realizations whose
continuation toward the ideal fails, with morph movies (Klein model), plus
the climbs of the direct ideal roots for the same dent patterns."""
import json, glob, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUILDERS = '/Users/doyle/Dropbox/neo/atlas2/builders'
SITE = '/Users/doyle/Dropbox/neo/atlas2/site/failures'
sys.path.insert(0, BUILDERS)
sys.path.insert(0, HERE)
import ideal_limit as IL
from walklib import develop
from realize_h import develop_h, klein, center
from glb import retreat_to_incenter, write_gltf_like

os.makedirs(os.path.join(SITE, 'glb'), exist_ok=True)

STYLE = """body{font-family:Georgia,serif;max-width:900px;margin:2em auto;line-height:1.55;color:#222;padding:0 1em}
h1{font-size:1.3em}h2{font-family:monospace;font-size:1.0em;word-break:break-all;margin:1.6em 0 .2em;border-top:1px solid #ddd;padding-top:1em}
h2 a{color:inherit;text-decoration:none}.facts{font-size:.9em;color:#555;margin:.2em 0 .6em}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:1em}.cell model-viewer{width:100%;height:340px;background:#f0f0f0}
.label{text-align:center;font-size:.85em;color:#777;margin-top:.15em}input[type=range]{width:100%}
p.intro{font-size:.95em}"""

def glb_frames(tag, nc, frames):
    """Klein-model GLB per frame; returns list of (alpha, glbname)."""
    faces = [tuple(int(x) for x in ff.split(',')) for ff in nc.split(';')]
    V = max(max(f) for f in faces)
    fidx = [(a-1, b-1, c-1) for a, b, c in faces]
    out = []
    for i, (alpha, bd) in enumerate(sorted(frames, key=lambda fr: fr[0])):
        bends = {}
        for k, v in bd.items():
            a, b = (int(x) for x in k.split(','))
            bends[(min(a, b), max(a, b))] = v
        try:
            if alpha >= 59.999:
                pos, _ = develop(faces, bends)
                P = {v2: np.asarray(pos[v2]) for v2 in pos}
                c0 = sum(P.values()) / len(P)
                P = {v2: P[v2] - c0 for v2 in P}
            else:
                pos = center(develop_h(faces, bends, math.radians(max(alpha, 0.05)))[0])
                P = klein(pos)
        except Exception:
            continue
        verts = [tuple(P[v2]) for v2 in range(1, V+1)]
        v2_, f2_, mats = retreat_to_incenter(verts, fidx, 0.9)
        name = f'{tag}_{i:02d}.glb'
        write_gltf_like(os.path.join(SITE, 'glb', name), v2_, f2_, mats)
        out.append((alpha, name))
    return out

def viewer(vid, frames):
    alphas = json.dumps([round(a, 3) for a, _ in frames])
    names = json.dumps([n for _, n in frames])
    n = len(frames)
    return (f'<div class=cell><model-viewer id="mv{vid}" src="glb/{frames[-1][1]}" camera-controls></model-viewer>'
            f'<input type=range min=0 max={n-1} value={n-1} '
            f'oninput=\'(function(i){{var A={alphas},N={names};'
            f'document.getElementById("mv{vid}").src="glb/"+N[i];'
            f'document.getElementById("lb{vid}").textContent="alpha = "+A[i]+" deg";}})(this.value)\'>'
            f'<div class=label id="lb{vid}">alpha = {frames[-1][0]:.3f} deg</div></div>')

runs = {}
for f in glob.glob(os.path.join(HERE, 'failure_frames', '*.json')):
    d = json.load(open(f))
    runs.setdefault((d['name'], d['key']), {})[d['kind']] = d

walks = {}
for f in glob.glob('/Users/doyle/Dropbox/neo/atlas2/data/walks/*.json'):
    d = json.load(open(f))
    walks[d['netcode']] = d

sections = []
vid = 0
for (name, key), kinds in sorted(runs.items(), key=lambda kv: (len(kv[0][0]), kv[0][0], kv[0][1])):
    nc = kinds[next(iter(kinds))]['netcode']
    faces = [tuple(int(x) for x in ff.split(',')) for ff in nc.split(';')]
    V = max(max(f) for f in faces)
    edges = sorted({(min(a,b),max(a,b)) for fc in faces for a,b in zip(fc,fc[1:]+fc[:1])})
    eidx = {e: i for i, e in enumerate(edges)}
    cyc = IL.links(V, faces)
    dents = set(int(x) for x in key.split(','))
    sigma = {v: (-1 if v in dents else 1) for v in range(1, V+1)}
    A = np.zeros((V, len(edges)))
    for i,(a_,b_) in enumerate(edges): A[a_-1,i]=A[b_-1,i]=1
    t = np.array([sigma[v]*2*math.pi for v in range(1,V+1)])
    bI, _, resI = IL.gauss_newton(np.linalg.lstsq(A,t,rcond=None)[0], edges, V, cyc, sigma)
    have_root = resI < 1e-10

    facts = []
    body = '<div class=pair>'
    for kind in ('descent', 'climb'):
        if kind not in kinds:
            body += '<div class=cell><div class=label>no ideal solution to climb from</div></div>'
            continue
        d = kinds[kind]
        frames = d['frames']
        tag = f'{name}_{key.replace(",","_")}_{kind}'
        fr = glb_frames(tag, nc, frames)
        end = d['endpoint']
        blast = frames[-1][1] if kind == 'climb' else frames[-1][1]
        bv = np.zeros(len(edges))
        for k2, v in (frames[-1][1] if kind=='climb' else frames[-1][1]).items():
            a_, b_ = (int(x) for x in k2.split(','))
            bv[eidx[(min(a_,b_),max(a_,b_))]] = v
        if kind == 'descent':
            lo = min(a for a, _ in fr)
            mx = float(np.max(np.abs(bv)))
            mxe = edges[int(np.argmax(np.abs(bv)))]
            note = f'descent from the embedded realization: reaches alpha = {lo:.2f} deg'
            if lo > 1.0:
                note += f'; DIES there with max|b| = {mx:.3f} at edge {mxe}'
            elif have_root:
                dev = float(np.max(np.abs(bv - bI)))
                note += (f'; reaches the ideal end, {"the SAME root as the direct solve" if dev < 5e-3 else f"a DIFFERENT ideal root (diff {dev:.3f} from the direct one)"}')
            facts.append(note)
        else:
            hi = max(a for a, _ in fr)
            note = f'climb of the direct ideal root: reaches alpha = {hi:.2f} deg'
            if hi < 59.999:
                note += ' (STALLS there)'
            else:
                wb = walks[nc]['atlas'][key]
                bw = np.zeros(len(edges))
                for k2, v in wb.items():
                    a_, b_ = (int(x) for x in k2.split(','))
                    bw[eidx[(min(a_,b_),max(a_,b_))]] = v
                dev = float(np.max(np.abs(bv - bw)))
                mx = float(np.max(np.abs(bv)))
                note += (f'; lands ON the embedded realization' if dev < 1e-3 else
                         f'; lands on a DIFFERENT realization (diff {dev:.2f} from embedded, max|b| = {mx:.2f} > pi: nonembedded)')
            facts.append(note)
        body += viewer(vid, fr)
        vid += 1
    body += '</div>'
    href = f'../web/{V}/{name}.html'
    sections.append(f'<h2><a href="{href}">{name}</a> dents {{{key}}}</h2>'
                    f'<div class=facts>{" &mdash; ".join(facts)}</div>{body}')

html = (f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
        f'<meta name=viewport content="width=device-width,initial-scale=1">'
        f'<title>Dented branches that fail to reach the ideal</title>'
        f'<script type=module src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js"></script>'
        f'<style>{STYLE}</style></head><body>'
        f'<h1>Dented branches that fail to reach the ideal</h1>'
        f'<p class=intro>Left: the embedded dented realization continued from 60&deg; toward the ideal '
        f'(plain dent gate; bends may pass &pi;), rendered in the Klein model, until the continuation dies. '
        f'Right: the direct ideal solution for the same dent pattern continued from the ideal end up toward 60&deg;. '
        f'Slider = corner angle &alpha;.</p>'
        + '\n'.join(sections) + '</body></html>')
open(os.path.join(SITE, 'index.html'), 'w').write(html)
print('sections:', len(sections), ' glbs:', len(glob.glob(os.path.join(SITE, "glb", "*.glb"))))
