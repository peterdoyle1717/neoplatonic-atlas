#!/usr/bin/env python3
"""Special pages + front page for the personal atlas.

Currently: the buried-vertices gallery (every net with a vertex strictly
inside the convex hull of its realization, caption = count and depth)
and the front page (definition, search, counts by v, special pages).
Reads data/nets_v4_14.txt; solves each net at 60 degrees to get coords.
"""
import math, os, subprocess, sys
import numpy as np
from scipy.spatial import ConvexHull

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
OUT = os.path.join(TOP, "site", "personal")
sys.path.insert(0, HERE)
from walklib import develop
from personal import solve_prove_60, STYLE

def coords(name, nc):
    faces = [tuple(int(x) for x in f.split(',')) for f in nc.split(';')]
    V = max(max(f) for f in faces)
    bends = solve_prove_60(nc)
    if bends is None:
        return None, None
    pos, _ = develop(faces, {tuple(sorted(e)): b for e, b in bends.items()})
    return np.array([pos[v] for v in range(1, V + 1)]), V

def buried_info(P, tol=1e-6):
    """(count, max depth) of vertices strictly inside the hull.

    Depth = min over facets of the distance to the facet plane, which
    for a point inside a convex polytope equals the distance to the
    hull boundary. Vertices on the boundary (hull corners, points on
    flat hull faces or edges) get depth ~0 and don't count. Flat
    solids (pancakes) have no interior, hence no buried vertices."""
    Q = P - P.mean(axis=0)
    if np.linalg.svd(Q, compute_uv=False)[2] < 1e-9 * len(P):
        return 0, 0.0
    hull = ConvexHull(P)
    A = hull.equations[:, :3]
    b = hull.equations[:, 3]
    depths = -(P @ A.T + b[None, :]).max(axis=1)
    buried = depths[depths > tol]
    return len(buried), (float(buried.max()) if len(buried) else 0.0)

def cell(name, V, caption):
    return (f'<div><div class=cell>'
            f'<iframe src="../turntable.html?file=glb/{name}_rb.glb"></iframe></div>'
            f'<div class=label><a href="../{V}/{name}.html" '
            f'style="color:#888">{name}</a><br>{caption}</div></div>')

def page(title, intro, cells, outpath):
    html = (f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{STYLE}</style></head><body>'
            f'<nav><a href="../index.html">neoplatonic solids</a></nav>'
            f'<h1 style="font-family:Georgia,serif">{title}</h1>'
            f'<p class=info>{intro}</p><div class=pair>'
            + ''.join(cells) + '</div></body></html>')
    with open(outpath, 'w') as f:
        f.write(html)

def main():
    jobs = []
    with open(os.path.join(TOP, "data", "nets_v4_14.txt")) as f:
        for ln in f:
            name, nc = ln.split()
            jobs.append((name, nc, None))
    # exemplars beyond the browse range: the old atlas's hull-buried
    # gallery (v = 17..24), third column = its published depth
    extra = os.path.join(TOP, "data", "nets_buried_old.txt")
    if os.path.exists(extra):
        with open(extra) as f:
            for ln in f:
                name, nc, d = ln.split()
                jobs.append((name, nc, float(d)))

    os.makedirs(os.path.join(OUT, "special"), exist_ok=True)
    buried = []
    byv = {}
    for name, nc, dold in jobs:
        P, V = coords(name, nc)
        if P is None:
            print(f'SOLVE FAILED {name}')
            continue
        if dold is None:
            byv.setdefault(V, []).append(name)
        k, d = buried_info(P)
        if k:
            buried.append((V, name, k, d))
        if dold is not None:
            tag = 'ok' if abs(d - dold) < 5e-3 else 'MISMATCH'
            print(f'{tag} v={V} depth={d:.3f} old={dold:.3f} {name}')
    n14 = sum(1 for _, _, dold in jobs if dold is None)
    buried.sort()
    cells = [cell(name, V,
                  f'v = {V} &middot; {k} buried '
                  f'vert{"ex" if k == 1 else "ices"}, depth {d:.3f}')
             for V, name, k, d in buried]
    page('Buried vertices',
         f'Solids with a vertex strictly inside their convex hull. '
         f'None of the {n14} nets with v &le; 14 has one; the first appears '
         f'at v = 17. Shown: the {len(buried)} examples of the previous '
         f'atlas&rsquo;s hull-buried gallery (v = 17&ndash;24), recomputed '
         f'here. Depth is the distance from the deepest buried vertex to '
         f'the hull boundary (edge length 1).',
         cells, os.path.join(OUT, 'special', 'buried.html'))
    print(f'buried.html: {len(buried)} nets')

    # front page
    counts = ''.join(
        f'<tr><td class=v>v = {v}</td><td class=num>{len(byv[v])}</td>'
        f'<td><a href="{v}/index.html">browse</a></td></tr>'
        for v in sorted(byv))
    front = f'''<!DOCTYPE html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Neoplatonic solids</title><style>{STYLE}
h1{{font-family:Georgia,serif;font-size:1.4em}}
.counts{{font-size:.9em;border-collapse:collapse}}
.counts td{{padding:.12em .6em .12em 0}}
.counts td.v{{color:#888;text-align:right;padding-right:.4em}}
.counts td.num{{text-align:right;font-variant-numeric:tabular-nums;padding-right:1.5em}}
.search input{{font-family:monospace;font-size:.95em;padding:.3em .5em;width:65%}}
.search button{{padding:.3em .8em;cursor:pointer}}
#msg{{font-size:.85em;color:#c33;margin-top:.3em}}
.links a{{display:inline-block;padding:.15em .6em;margin:.1em .15em;background:#f0f0f0;border-radius:4px;font-size:.9em;text-decoration:none}}
</style></head><body>
<h1>Neoplatonic solids</h1>
<p>A <em>neoplatonic solid</em> is an undented Euclidean polyhedron with
equilateral triangle faces, meeting at most six to a vertex. Every prime
6-net has exactly one; this atlas shows them all for v &le; 14, each with
its ideal form and the morph between the two.</p>
<h2 style="font-size:1.1em">Special pages</h2>
<div class=links>
<a href="special/buried.html">Buried vertices</a>
</div>
<h2 style="font-size:1.1em">Find a net</h2>
<div class=search>
<input id=q placeholder="CLERS name, e.g. CCCACACACACACAAE">
<button onclick="go()">go</button>
<div id=msg></div>
</div>
<script>
function go() {{
  var s = document.getElementById('q').value.trim().toUpperCase();
  if (!/^[ABCDE]+$/.test(s)) {{ document.getElementById('msg').textContent = 'letters ABCDE only'; return; }}
  var v = (s.length + 4) / 2;
  if (v !== Math.floor(v)) {{ document.getElementById('msg').textContent = 'length must be even'; return; }}
  window.location = v + '/' + s + '.html';
}}
document.getElementById('q').addEventListener('keydown', function(e) {{ if (e.key === 'Enter') go(); }});
</script>
<h2 style="font-size:1.1em">All nets by size</h2>
<table class=counts>{counts}</table>
</body></html>'''
    with open(os.path.join(OUT, 'index.html'), 'w') as f:
        f.write(front)
    print('front page written')

if __name__ == "__main__":
    main()
