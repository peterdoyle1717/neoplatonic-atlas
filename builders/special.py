#!/usr/bin/env python3
"""Site generator over the net records: stamps classification flags
(data/class_v30.tsv) and Eisenstein relations (data/eisenstein.tsv)
into each net.json, re-renders every page, then builds the galleries,
the by-v listing pages, and the front page. Markup and CSS follow the
old deployed atlas.

Run after personal.py has built the net directories.
"""
import csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
OUT = os.path.join(TOP, "site", "personal")
NETS = os.path.join(OUT, "nets")
sys.path.insert(0, HERE)
from personal import MV
from views import render_page, display, net_id

GALLERY_CSS = (
    "body{font-family:Georgia,serif;max-width:1000px;margin:2em auto;"
    "line-height:1.6;color:#222;padding:0 1em}h1{font-size:1.3em}"
    "h1 a{color:inherit;text-decoration:none}h1 a:hover{text-decoration:underline}"
    "h2{font-size:1em;margin-top:1.6em}"
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


def load_records():
    recs = {}
    for d in sorted(os.listdir(NETS)):
        p = os.path.join(NETS, d, "net.json")
        if os.path.exists(p):
            recs[d] = json.load(open(p))
    return recs


def stamp(recs):
    """classification flags + eisenstein relations -> records; save +
    re-render changed pages."""
    cls = {}
    cpath = os.path.join(TOP, "data", "class_v30.tsv")
    if os.path.exists(cpath):
        for r in csv.DictReader(open(cpath), delimiter='\t'):
            if r['pancake'] != 'ERR':
                cls[r['name']] = r
    eis = {}
    epath = os.path.join(TOP, "data", "eisenstein.tsv")
    if os.path.exists(epath):
        for r in csv.DictReader(open(epath), delimiter='\t'):
            eis[r['name']] = r
    for d, rec in recs.items():
        changed = False
        c = cls.get(rec.get("name", d))
        if c:
            flags = {"pancake": bool(int(c['pancake'])),
                     "convex": bool(int(c['convex'])),
                     "strictly_convex": bool(int(c['strict'])),
                     "buried": int(c['nburied']),
                     "buried_depth": float(c['depth']),
                     "floppy": bool(int(c['floppy']))}
            if rec.get("flags") != flags:
                rec["flags"] = flags
                changed = True
        e = eis.get(rec.get("name", d))
        if e:
            ei = {"family": e['family'], "T": int(e['T']),
                  "a": int(e['a']), "b": int(e['b']),
                  "ancestors": [x for x in e['ancestors'].split(',') if x],
                  "descendants": [x for x in e['descendants'].split(',') if x]}
            if rec.get("eisenstein") != ei:
                rec["eisenstein"] = ei
                changed = True
        if changed:
            netdir = os.path.join(NETS, d)
            with open(os.path.join(netdir, "net.json"), "w") as f:
                json.dump(rec, f, indent=1)
            render_page(netdir)


def item(rec, caption):
    nid = rec.get("id", rec["name"])
    return (f'<div class=item><div class=cell>'
            f'<model-viewer src="../nets/{nid}/rb.glb" '
            f'camera-orbit="0deg 100deg auto" camera-controls '
            f'interaction-prompt=none></model-viewer></div>'
            f'<a href="../nets/{nid}/">{display(rec["name"])}</a> '
            f'<span class=v>{caption}</span></div>')


def gallery(fname, title, desc, body_html):
    html = (f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{GALLERY_CSS}</style>{MV}</head><body>'
            f'<h1><a href="../index.html">Neoplatonic solids</a> &middot; {title}</h1>'
            f'<p class=desc>{desc}</p>' + body_html + '</body></html>')
    with open(os.path.join(OUT, "gallery", fname), 'w') as f:
        f.write(html)
    print(f'gallery/{fname} written')


def grid(items):
    return '<div class=grid>' + ''.join(items) + '</div>'


def census_counts():
    """class counts over the full v<=30 census (not just built pages)."""
    n = {"total": 0, "pancake": 0, "convex": 0, "floppy": 0, "buried": 0}
    cpath = os.path.join(TOP, "data", "class_v30.tsv")
    if os.path.exists(cpath):
        for r in csv.DictReader(open(cpath), delimiter='\t'):
            if r['pancake'] == 'ERR':
                continue
            n["total"] += 1
            n["pancake"] += int(r['pancake'])
            n["convex"] += int(r['convex'])
            n["floppy"] += int(r['floppy'])
            n["buried"] += 1 if int(r['nburied']) else 0
    return n


def main():
    os.makedirs(os.path.join(OUT, "gallery"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "by-v"), exist_ok=True)
    recs = load_records()
    stamp(recs)
    recs = load_records()
    cn = census_counts()

    # -- galleries ---------------------------------------------------
    buried = sorted((r for r in recs.values() if r["flags"].get("buried")),
                    key=lambda r: -r["flags"]["buried_depth"])
    gallery('buried.html', 'Hull-buried',
            f'Solids with a vertex strictly inside the convex hull: '
            f'{cn["buried"]} of the {cn["total"]} prime nets with '
            f'v &le; 30 (none below v = 17). Shown: the deepest built '
            f'here, sorted by depth d of the deepest buried vertex '
            f'(edge length 1); up to 8 per size have pages.',
            grid([item(r, f'v={r["v"]} d={r["flags"]["buried_depth"]:.3f}')
                  for r in buried]))

    convex = sorted((r for r in recs.values() if r["flags"].get("convex")
                     and not r["flags"].get("pancake")),
                    key=lambda r: (r["v"], r["name"]))
    gallery('convex.html', 'Convex',
            f'Convex solids: every bend nonnegative &mdash; all '
            f'{cn["convex"]} among the {cn["total"]} prime nets with '
            f'v &le; 30 (pancakes listed separately). '
            f'&ldquo;strictly&rdquo; marks strictly convex (every bend '
            f'positive).',
            grid([item(r, f'v={r["v"]}'
                       + (' strictly' if r["flags"].get("strictly_convex") else ''))
                  for r in convex]))

    pancakes = sorted((r for r in recs.values() if r["flags"].get("pancake")),
                      key=lambda r: (r["v"], r["name"]))
    gallery('pancakes.html', 'Pancakes',
            f'Flat solids (doubled polygons), the degenerate convex case: '
            f'all {cn["pancake"]} among the prime nets with v &le; 30.',
            grid([item(r, f'v={r["v"]}') for r in pancakes]))

    floppy = sorted((r for r in recs.values() if r["flags"].get("floppy")),
                    key=lambda r: (r["v"], r["name"]))
    gallery('floppy.html', 'Floppy',
            f'Nets whose realization has an infinitesimal flex (rank '
            f'deficit): all {cn["floppy"]} among the prime nets with '
            f'v &le; 30, from the flopper census.',
            grid([item(r, f'v={r["v"]}') for r in floppy]))

    subdiv = [r for r in recs.values() if r.get("eisenstein", {}).get("family")]
    fams = {}
    for r in subdiv:
        fams.setdefault(r["eisenstein"]["family"], []).append(r)
    parts = []
    for fam in sorted(fams):
        rows = sorted(fams[fam], key=lambda r: r["eisenstein"]["T"])
        parts.append(f'<h2>{fam} &middot; <a href="../eisenmap/{fam}.html" '
                     f'style="font-size:.85em">lattice map</a></h2>')
        parts.append(grid([item(r, f'T={r["eisenstein"]["T"]} '
                                   f'({r["eisenstein"]["a"]},{r["eisenstein"]["b"]}) '
                                   f'v={r["v"]}') for r in rows]))
    gallery('subdiv.html', 'Eisenstein subdivisions',
            'Subdivision families: each base net subdivided by the '
            'Eisenstein integer a + b&omega;, T = a&sup2;+ab+b&sup2; '
            '(&ldquo;geodesic subdivision&rdquo; in the old atlas). '
            'Members up to v = 132 are built so far; each page lists '
            'the net&rsquo;s Eisenstein ancestors and descendants.',
            ''.join(parts))

    # -- by-v listing pages -------------------------------------------
    byv = {}
    for r in recs.values():
        byv.setdefault(r["v"], []).append(r)
    for v, rows in sorted(byv.items()):
        note = ('' if v <= 14 else
                ' &middot; exemplars only, not the full set at this size')
        body = [f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
                f'<title>v = {v}</title><style>{GALLERY_CSS}</style>{MV}</head><body>'
                f'<h1><a href="../index.html">Neoplatonic solids</a> &middot; '
                f'v = {v}</h1><p class=desc>{len(rows)} nets{note}</p>',
                grid([item(r, f'v={v}') for r in
                      sorted(rows, key=lambda r: r["name"])]),
                '</body></html>']
        with open(os.path.join(OUT, "by-v", f"{v}.html"), "w") as f:
            f.write('\n'.join(body))
    print(f'by-v pages: {len(byv)}')

    # -- front page ----------------------------------------------------
    quick = ''.join(f'<a href="by-v/{v}.html">v={v}</a>\n'
                    for v in sorted(byv) if v <= 14)
    more = ''.join(f'<a href="by-v/{v}.html">v={v}</a>\n'
                   for v in sorted(byv) if v > 14)
    ex = "v9CCCACACACACAAE"
    if ex not in recs:
        ex = sorted(recs)[0]
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
<div class="gallery-links" style="font-size:.85em">
{more}</div>

<h2>Themed galleries</h2>
<div class="gallery-links">
<a href="gallery/buried.html">Hull-buried</a>
<a href="gallery/convex.html">Convex</a>
<a href="gallery/pancakes.html">Pancakes</a>
<a href="gallery/floppy.html">Floppy</a>
<a href="gallery/subdiv.html">Eisenstein subdivisions</a>
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
    <model-viewer src="nets/{ex}/rb.glb"
      camera-orbit="0deg 100deg auto" camera-controls interaction-prompt="none"></model-viewer>
    <div class="label"><a href="nets/{ex}/">{ex}</a></div>
  </div>
</div>
<iframe class="example-full" src="nets/{ex}/" loading="lazy" title="per-net page preview"></iframe>

<h2>Find a net</h2>
<div class="search">
<input id=q placeholder="CLERS name, e.g. CCCACACACACAAE">
<button onclick="go()">go</button>
<div id="search-msg"></div>
</div>
<script>
function go() {{
  var m = document.getElementById('search-msg');
  var s = document.getElementById('q').value.trim().toUpperCase();
  m.className = 'err';
  if (/^V[0-9]+/.test(s)) s = s.replace(/^V[0-9]+/, '');
  if (!/^[ABCDE]+$/.test(s)) {{ m.textContent = 'letters ABCDE only'; return; }}
  var v = (s.length + 4) / 2;
  if (v !== Math.floor(v)) {{ m.textContent = 'length must be even'; return; }}
  window.location = 'nets/v' + v + s + '/';
}}
document.getElementById('q').addEventListener('keydown',
  function(e) {{ if (e.key === 'Enter') go(); }});
</script>
</body></html>'''
    with open(os.path.join(OUT, 'index.html'), 'w') as f:
        f.write(front)
    print('front page written')
    import eisenmap
    eisenmap.generate()


if __name__ == "__main__":
    main()
