#!/usr/bin/env python3
"""Front page + themed galleries for the personal atlas, in the old
atlas's markup (CSS and cell structure lifted from the deployed
math.dartmouth.edu/~doyle/docs/atlas pages).

Layout: site/personal/index.html (front), site/personal/gallery/*.html
(themed thumbnail grids of model-viewers, captions linking to the
per-net pages at <v>/<NAME>/).

Galleries built here: hull-buried (exemplar list from the old atlas,
depths recomputed), convex, pancakes. Classification is computed from
the solved bends and developed coordinates of every net that has a
page (data/nets_v4_14.txt + data/nets_buried_old.txt).
"""
import math, os, sys
import numpy as np
from scipy.spatial import ConvexHull

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
OUT = os.path.join(TOP, "site", "personal")
sys.path.insert(0, HERE)
from walklib import develop
from personal import solve_prove_60, MV

GALLERY_CSS = (
    "body{font-family:Georgia,serif;max-width:1000px;margin:2em auto;"
    "line-height:1.6;color:#222;padding:0 1em}h1{font-size:1.3em}"
    "h1 a{color:inherit;text-decoration:none}h1 a:hover{text-decoration:underline}"
    "p.desc{font-size:.9em;color:#555}"
    ".grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1.5em;margin-top:1em}"
    ".item{text-align:center}.item .cell{position:relative;width:100%;padding-bottom:100%}"
    ".item .cell model-viewer{position:absolute;top:0;left:0;width:100%;height:100%;"
    "background:#f0f0f0;--poster-color:transparent}"
    ".item a{font-family:monospace;font-size:.75em;color:#2255aa;"
    "text-decoration:none;word-break:break-all}.item a:hover{text-decoration:underline}"
    ".item .v{font-size:.7em;color:#888}")

FRONT_CSS = (
    "body{font-family:Georgia,serif;max-width:720px;margin:3em auto;"
    "line-height:1.6;color:#222;padding:0 1em}"
    "h1{font-size:1.4em}h2{font-size:1.1em;margin-top:2em}"
    ".authors{font-size:.95em;color:#444;margin-top:-.5em}"
    "a{color:#2255aa;text-decoration:none}a:hover{text-decoration:underline}"
    ".example-row{margin:1.5em 0;display:flex;align-items:flex-start;gap:1.5em}"
    ".example-row .blurb{flex:1;font-size:.95em;color:#444;line-height:1.5}"
    ".example-row .thumb{width:240px;flex-shrink:0}"
    ".example-row .thumb model-viewer{width:100%;height:240px;background:#f0f0f0;"
    "--poster-color:transparent;display:block}"
    ".example-row .thumb .label{text-align:center;margin-top:.3em}"
    ".example-row .thumb .label a{font-family:monospace;font-size:.85em}"
    ".example-full{width:100%;height:720px;border:1px solid #ddd;background:#fff;"
    "display:block;margin:.5em 0 1em}"
    ".gallery-links{margin:1em 0;line-height:2.2}"
    ".gallery-links a{display:inline-block;padding:.15em .6em;margin:.1em .15em;"
    "background:#f0f0f0;border-radius:4px;font-size:.9em}"
    ".gallery-links a:hover{background:#dde4f0}"
    ".search{margin:1.5em 0}"
    ".search input{font-family:monospace;font-size:.95em;padding:.3em .5em;width:70%}"
    ".search button{padding:.3em .8em;cursor:pointer}"
    "#search-msg{font-size:.85em;color:#888;margin-top:.3em}"
    "#search-msg.err{color:#c33}")


def solve_and_develop(nc):
    """(P, V, bends) for one net; P = V x 3 developed coordinates."""
    faces = [tuple(int(x) for x in f.split(',')) for f in nc.split(';')]
    V = max(max(f) for f in faces)
    bends = solve_prove_60(nc)
    if bends is None:
        return None, None, None
    pos, _ = develop(faces, {tuple(sorted(e)): b for e, b in bends.items()})
    return np.array([pos[v] for v in range(1, V + 1)]), V, bends


def is_flat(P):
    Q = P - P.mean(axis=0)
    return np.linalg.svd(Q, compute_uv=False)[2] < 1e-9 * len(P)


def buried_info(P, tol=1e-6):
    """(count, max depth) of vertices strictly inside the hull; depth =
    min facet-plane distance = distance to the hull boundary."""
    if is_flat(P):
        return 0, 0.0
    hull = ConvexHull(P)
    A = hull.equations[:, :3]
    b = hull.equations[:, 3]
    depths = -(P @ A.T + b[None, :]).max(axis=1)
    buried = depths[depths > tol]
    return len(buried), (float(buried.max()) if len(buried) else 0.0)


def item(name, V, caption):
    return (f'<div class=item><div class=cell>'
            f'<model-viewer src="../{V}/{name}/rb.glb" '
            f'camera-orbit="0deg 100deg auto" camera-controls '
            f'interaction-prompt=none></model-viewer></div>'
            f'<a href="../{V}/{name}/">{name}</a> '
            f'<span class=v>{caption}</span></div>')


def gallery(fname, title, desc, items):
    html = (f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{GALLERY_CSS}</style>{MV}</head><body>'
            f'<h1><a href="../index.html">Neoplatonic solids</a> &middot; {title}</h1>'
            f'<p class=desc>{desc}</p><div class=grid>'
            + ''.join(items) + '</div></body></html>')
    with open(os.path.join(OUT, "gallery", fname), 'w') as f:
        f.write(html)
    print(f'gallery/{fname}: {len(items)} items')


def main():
    jobs = []
    with open(os.path.join(TOP, "data", "nets_v4_14.txt")) as f:
        for ln in f:
            name, nc = ln.split()
            jobs.append((name, nc, None))
    extra = os.path.join(TOP, "data", "nets_buried_old.txt")
    if os.path.exists(extra):
        with open(extra) as f:
            for ln in f:
                name, nc, d = ln.split()
                jobs.append((name, nc, float(d)))

    os.makedirs(os.path.join(OUT, "gallery"), exist_ok=True)
    buried, convex, pancakes, byv = [], [], [], {}
    for name, nc, dold in jobs:
        P, V, bends = solve_and_develop(nc)
        if P is None:
            print(f'SOLVE FAILED {name}')
            continue
        if dold is None:
            byv.setdefault(V, []).append(name)
        if is_flat(P):
            pancakes.append((V, name))
        elif min(bends.values()) >= -1e-9:
            convex.append((V, name))
        k, d = buried_info(P)
        if k:
            buried.append((V, name, k, d))
        if dold is not None:
            tag = 'ok' if abs(d - dold) < 5e-3 else 'MISMATCH'
            print(f'{tag} v={V} depth={d:.3f} old={dold:.3f} {name}')

    buried.sort()
    gallery('buried.html', 'Hull-buried',
            'Solids with a vertex strictly inside the convex hull. None of '
            f'the {sum(len(v) for v in byv.values())} nets with v &le; 14 '
            'has one; the first appears at v = 17. Shown: the '
            f'{len(buried)} examples of the old atlas&rsquo;s hull-buried '
            'gallery (v = 17&ndash;24), recomputed here. d = depth of the '
            'deepest buried vertex (edge length 1).',
            [item(n, V, f'v={V} d={d:.3f}') for V, n, k, d in buried])
    convex.sort()
    gallery('convex.html', 'Convex',
            'Solids that are convex: every bend nonnegative (pancakes '
            'listed separately).',
            [item(n, V, f'v={V}') for V, n in convex])
    pancakes.sort()
    gallery('pancakes.html', 'Pancakes',
            'Flat solids: doubled polygons, the degenerate convex case.',
            [item(n, V, f'v={V}') for V, n in pancakes])

    # front page, old atlas structure (Browse-by-size table dropped)
    quick = ''.join(f'<a href="{v}/index.html">v={v}</a>\n' for v in sorted(byv))
    ex = 'CCCACACACACAAE'
    if ex not in byv.get(9, []):
        ex = sorted(byv[min(byv)])[0]
    exv = next(v for v, names in byv.items() if ex in names)
    front = f'''<!DOCTYPE html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Neoplatonic Solids</title><style>{FRONT_CSS}</style>{MV}</head><body>
<h1>Neoplatonic Solids</h1>
<p class="authors">Peter Doyle, Matthew Ellison</p>
<p>
A <em>neoplatonic solid</em> is an undented Euclidean polyhedron
with equilateral triangle faces, meeting at most six to a vertex.
</p>

<h2>Quick links by size</h2>
<div class="gallery-links">
{quick}</div>

<h2>Themed galleries</h2>
<div class="gallery-links">
<a href="gallery/buried.html">Hull-buried</a>
<a href="gallery/convex.html">Convex</a>
<a href="gallery/pancakes.html">Pancakes</a>
</div>

<h2>Example</h2>
<div class="example-row">
  <div class="blurb">
    Each neoplatonic has its own page &mdash; the Euclidean solid, the
    morph from the ideal limit in the Poincar&eacute; and Klein models,
    the ideal net, and the CLERS triangulation. <strong>Click the CLERS
    code under the model to the right</strong> to open its page; an
    embedded copy is shown below.
  </div>
  <div class="thumb">
    <model-viewer src="{exv}/{ex}/rb.glb"
      camera-orbit="0deg 100deg auto" camera-controls interaction-prompt="none"></model-viewer>
    <div class="label"><a href="{exv}/{ex}/">{ex}</a></div>
  </div>
</div>
<iframe class="example-full" src="{exv}/{ex}/" loading="lazy" title="per-net page preview"></iframe>

<h2>Find a net</h2>
<div class="search">
<input id=q placeholder="CLERS name, e.g. {ex}">
<button onclick="go()">go</button>
<div id="search-msg"></div>
</div>
<script>
function go() {{
  var m = document.getElementById('search-msg');
  var s = document.getElementById('q').value.trim().toUpperCase();
  m.className = 'err';
  if (!/^[ABCDE]+$/.test(s)) {{ m.textContent = 'letters ABCDE only'; return; }}
  var v = (s.length + 4) / 2;
  if (v !== Math.floor(v)) {{ m.textContent = 'length must be even'; return; }}
  window.location = v + '/' + s + '/';
}}
document.getElementById('q').addEventListener('keydown',
  function(e) {{ if (e.key === 'Enter') go(); }});
</script>
</body></html>'''
    with open(os.path.join(OUT, 'index.html'), 'w') as f:
        f.write(front)
    print('front page written')


if __name__ == "__main__":
    main()
