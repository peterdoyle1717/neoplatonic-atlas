#!/usr/bin/env python3
"""Eisenstein lattice maps ("eisenmaps"), PD spec 2026-07-13 rev 2:

  - the full 60-degree sector: the fundamental half-sector 0 <= b <= a
    AND its mirror below the x-axis (conjugates (a+b, -b)). With
    reflections lumped the two halves show the same nets; for a chiral
    unit net they would be distinct - noted on the page.
  - EVERY lattice point with T <= the family's cap is a genuine net
    (the (a,b)-subdivision of the unit) and takes the full class
    coloring: red = the selected net, blue = ancestors (divisors),
    green = descendants (multiples), grey = cousins. Built nets are
    solid and clickable; known-but-unbuilt are pale, unlabeled.
  - the dashed ray marks the selected net's Z-multiples.

Two outputs: standalone family pages (eisenmap/<family>.html, colored
by ?net=<id> in JS) and per-net static eismap.svg written into the
directory of every net with a built ancestor or descendant, embedded
inline on its page by views.py.
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
OUT = os.path.join(TOP, "site", "personal")
sys.path.insert(0, HERE)
from views import net_id
from members import eis_divides

SQ3 = 3 ** 0.5
SCALE = 64
PAD = 42

COL = {"self": "#c33", "anc": "#2255aa", "desc": "#0a8a2a", "cousin": "#999"}

CSS = ("body{font-family:Georgia,serif;max-width:860px;margin:2em auto;"
       "line-height:1.6;color:#222;padding:0 1em}h1{font-size:1.3em}"
       "h1 a{color:inherit;text-decoration:none}h1 a:hover{text-decoration:underline}"
       "p.desc{font-size:.9em;color:#555}"
       ".legend{font-size:.85em;color:#555;margin:.4em 0}"
       ".legend span{display:inline-block;margin-right:1.2em}"
       ".legend i{display:inline-block;width:.8em;height:.8em;border-radius:50%;"
       "margin-right:.35em;vertical-align:-.05em}"
       "svg{width:100%;height:auto;background:#fafafa;border:1px solid #ddd}"
       "text{font-family:monospace}")


def sector_points(tmax):
    """(a, b) in the half-sector 0 <= b <= a with T <= tmax."""
    pts = []
    a = 1
    while a * a <= tmax:
        a += 1
    amax = a
    for a in range(1, amax + 1):
        for b in range(0, a + 1):
            if a * a + a * b + b * b <= tmax:
                pts.append((a, b))
    return pts


def classify(a, b, sa, sb):
    """class of lattice net (a,b) relative to selection (sa,sb),
    mirror-lumped (divisibility tested both ways)."""
    if (a, b) == (sa, sb):
        return "self"
    if eis_divides(a, b, sa, sb) or eis_divides(b, a, sa, sb):
        return "anc"
    if eis_divides(sa, sb, a, b) or eis_divides(sb, sa, a, b):
        return "desc"
    return "cousin"


def load_families():
    fams = {}
    with open(os.path.join(TOP, "data", "eisenstein.tsv")) as f:
        for r in csv.DictReader(f, delimiter='\t'):
            name = r['name']
            i = 1
            while i < len(name) and name[i].isdigit():
                i += 1
            V, clers = int(name[1:i]), name[i:]
            nid = net_id(V, clers)
            built = os.path.exists(os.path.join(OUT, "nets", nid, "net.json"))
            fams.setdefault(r['family'], {})[(int(r['a']), int(r['b']))] = {
                "id": nid, "name": name, "T": int(r['T']),
                "a": int(r['a']), "b": int(r['b']), "v": V, "built": built}
    return fams


def draw(fam, members, sel=None, js=False):
    """SVG of the family lattice. sel=(a,b) colors statically; js=True
    leaves dots grey with ids for the page script."""
    tmax = max(m["T"] for m in members.values())
    pts = sector_points(tmax)
    amax = max(a for a, b in pts)
    xmax = max(a + b / 2.0 for a, b in pts) + 0.6
    ymax = max(b for a, b in pts) * SQ3 / 2.0 + 0.6

    def xy(a, b):
        return PAD + SCALE * (a + b / 2.0), PAD + SCALE * ymax - SCALE * (b * SQ3 / 2.0)

    W = int(2 * PAD + SCALE * xmax)
    H = int(2 * PAD + SCALE * 2 * ymax)
    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    x0, y0 = xy(0, 0)
    for (aa, bb) in ((amax + 1, 0), (amax, amax), (amax, -amax)):
        xe = PAD + SCALE * (aa + bb / 2.0)
        ye = PAD + SCALE * ymax - SCALE * (bb * SQ3 / 2.0)
        parts.append(f'<line x1="{x0}" y1="{y0}" x2="{xe:.0f}" y2="{ye:.0f}" '
                     f'stroke="#eee"/>')
    ray = ''
    if sel:
        sa, sb = sel
        k = min((xmax) / (sa + sb / 2.0), ymax / sb if sb > 0 else 1e9)
        xe = PAD + SCALE * k * (sa + sb / 2.0)
        ye = PAD + SCALE * ymax - SCALE * k * (sb * SQ3 / 2.0)
        ray = (f'<line x1="{x0}" y1="{y0}" x2="{xe:.0f}" y2="{ye:.0f}" '
               f'stroke="#c33" stroke-dasharray="5 4" stroke-width="1.2"/>')
    parts.append(f'<line id="ray" x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0}" '
                 f'stroke="#c33" stroke-dasharray="5 4" stroke-width="1.2" '
                 f'visibility="hidden"/>' if js else ray)

    for a, b in pts:
        m = members.get((a, b))
        cls = classify(a, b, *sel) if sel else "cousin"
        col = COL[cls]
        built = bool(m and m["built"])
        for mirror in ((False, True) if b > 0 else (False,)):
            x, y = xy(a, b)
            if mirror:
                y = PAD + SCALE * ymax + SCALE * (b * SQ3 / 2.0)
            did = f'm{a}_{b}' + ('r' if mirror else '')
            style = (f'fill="{col}"' if built else
                     f'fill="{col}" fill-opacity="0.22" stroke="{col}" '
                     f'stroke-opacity="0.5" stroke-dasharray="2 2"')
            dot = (f'<circle id="{did}" data-a="{a}" data-b="{b}" '
                   f'cx="{x:.1f}" cy="{y:.1f}" r="10" {style}>'
                   f'<title>T={a*a+a*b+b*b} ({a},{b})'
                   + (f' v={m["v"]}' if m else '') + '</title></circle>')
            if built and not mirror:
                T = a*a + a*b + b*b
                dot = (f'<a href="../nets/{m["id"]}/">{dot}'
                       f'<text x="{x:.1f}" y="{y-14:.1f}" font-size="10" '
                       f'text-anchor="middle" fill="#555">T{T} ({a},{b})</text>'
                       f'<text x="{x:.1f}" y="{y+24:.1f}" font-size="8.5" '
                       f'text-anchor="middle" fill="#aaa">v={m["v"]}</text></a>')
            elif built:
                dot = f'<a href="../nets/{m["id"]}/">{dot}</a>'
            parts.append(dot)
    parts.append('</svg>')
    return ''.join(parts), tmax


def family_page(fam, members):
    svg, tmax = draw(fam, members, sel=None, js=True)
    data = json.dumps([{k: m[k] for k in ("id", "a", "b")}
                       for m in members.values()])
    return f'''<!DOCTYPE html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Eisenstein map &mdash; {fam}</title><style>{CSS}</style></head><body>
<h1><a href="../index.html">Neoplatonic solids</a> &middot; Eisenstein map: {fam}</h1>
<p class=desc>The {fam} family: the unit net subdivided by a + b&omega;
(T = a&sup2;+ab+b&sup2;), every lattice point a genuine net, drawn with its
mirror sector below the axis. Reflections are lumped, so the two
half-sectors show the same nets; for a chiral unit they would be
distinct. Solid dots are built (click to open); pale dots are not
built yet. T is not injective: e.g. (7,0) and (5,3) are different nets
with T = 49. Subdivisions are computed with
<a href="https://www.antiprism.com/">Antiprism</a> (Adrian Rossiter&rsquo;s
<code>geodesic</code>).</p>
<div class=legend>
<span><i style="background:#c33"></i>this net</span>
<span><i style="background:#2255aa"></i>ancestors</span>
<span><i style="background:#0a8a2a"></i>descendants</span>
<span><i style="background:#999"></i>cousins</span>
</div>
{svg}
<script>
const MEMBERS = {data};
function divides(a, b, c, d) {{
  const N = a*a + a*b + b*b;
  if (!N) return false;
  const p = c*a + c*b + d*b, q = d*a - c*b;
  return p % N === 0 && q % N === 0;
}}
function divM(a1,b1,a2,b2) {{
  return divides(a1,b1,a2,b2) || divides(b1,a1,a2,b2);
}}
const sel = new URLSearchParams(location.search).get('net');
const me = MEMBERS.find(m => m.id === sel)
  || MEMBERS.find(m => m.a === 1 && m.b === 0);   // default: the unit's view
if (me) {{
  for (const el of document.querySelectorAll('circle[data-a]')) {{
    const a = +el.dataset.a, b = +el.dataset.b;
    let col = '#999';
    if (a === me.a && b === me.b) col = '#c33';
    else if (divM(a, b, me.a, me.b)) col = '#2255aa';
    else if (divM(me.a, me.b, a, b)) col = '#0a8a2a';
    el.setAttribute('fill', col);
    if (el.getAttribute('stroke')) el.setAttribute('stroke', col);
  }}
  const ray = document.getElementById('ray');
  const x0 = +ray.getAttribute('x1'), y0 = +ray.getAttribute('y1');
  const home = document.getElementById('m' + me.a + '_' + me.b);
  const k = 2.2;
  ray.setAttribute('x2', x0 + k * (+home.getAttribute('cx') - x0));
  ray.setAttribute('y2', y0 + k * (+home.getAttribute('cy') - y0));
  ray.setAttribute('visibility', 'visible');
}}
</script>
</body></html>'''


def generate():
    fams = load_families()
    os.makedirs(os.path.join(OUT, "eisenmap"), exist_ok=True)
    for fam, members in fams.items():
        with open(os.path.join(OUT, "eisenmap", f"{fam}.html"), 'w') as f:
            f.write(family_page(fam, members))
        nb = sum(m["built"] for m in members.values())
        print(f'eisenmap/{fam}.html ({nb}/{len(members)} built)')
        # per-net static SVGs for built nets with a built ancestor or
        # descendant (PD: embed on those personal pages)
        n_svg = 0
        for (a, b), m in members.items():
            if not m["built"]:
                continue
            rel = [m2 for (a2, b2), m2 in members.items()
                   if (a2, b2) != (a, b) and m2["built"]
                   and (classify(a2, b2, a, b) in ("anc", "desc"))]
            netdir = os.path.join(OUT, "nets", m["id"])
            svgpath = os.path.join(netdir, "eismap.svg")
            if rel:
                svg, _ = draw(fam, members, sel=(a, b), js=False)
                # links from inside a net dir go up one level less
                svg = svg.replace('href="../nets/', 'href="../')
                svg = svg.replace('<svg ', '<svg style="width:100%;'
                                  'background:#fafafa;border:1px solid #ddd" ', 1)
                with open(svgpath, 'w') as f:
                    f.write(svg)
                n_svg += 1
            elif os.path.exists(svgpath):
                os.remove(svgpath)
        print(f'  per-net eismaps: {n_svg}')


if __name__ == "__main__":
    generate()
