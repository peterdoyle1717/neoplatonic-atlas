#!/usr/bin/env python3
"""Eisenstein lattice maps ("eisenmaps"): one page per subdivision
family showing the family's lattice of derived nets in the sextant
0 <= b <= a, colored relative to a selected net (?net=<id>):

  red    the net itself
  blue   its Eisenstein ancestors  (divisors of a + b*omega)
  green  its descendants           (multiples)
  grey   its cousins               (other family members)

plus a dashed radial ray through the net: the Z-multiples direction,
whose large-k limit is the object of study. Mirror images are lumped
((a,b) ~ (b,a)); divisibility is tested against both. Clicking a built
member opens its homepage; unbuilt members (large T) are hollow.

Data comes from data/eisenstein.tsv + the net records (built = record
directory exists). Generated into site/personal/eisenmap/<family>.html.
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
OUT = os.path.join(TOP, "site", "personal")
sys.path.insert(0, HERE)
from views import net_id

SQ3 = 3 ** 0.5
AMAX = 6           # lattice drawn for 0 <= b <= a <= AMAX
SCALE = 76
PAD = 46

CSS = ("body{font-family:Georgia,serif;max-width:760px;margin:2em auto;"
       "line-height:1.6;color:#222;padding:0 1em}h1{font-size:1.3em}"
       "h1 a{color:inherit;text-decoration:none}h1 a:hover{text-decoration:underline}"
       "p.desc{font-size:.9em;color:#555}"
       ".legend{font-size:.85em;color:#555;margin:.4em 0}"
       ".legend span{display:inline-block;margin-right:1.2em}"
       ".legend i{display:inline-block;width:.8em;height:.8em;border-radius:50%;"
       "margin-right:.35em;vertical-align:-.05em}"
       "svg{width:100%;height:auto;background:#fafafa;border:1px solid #ddd}"
       "text{font-family:monospace}")


def xy(a, b):
    x = PAD + SCALE * (a + b / 2.0)
    y = PAD + SCALE * (AMAX * SQ3 / 2.0) - SCALE * (b * SQ3 / 2.0)
    return x, y


def generate():
    rows = []
    with open(os.path.join(TOP, "data", "eisenstein.tsv")) as f:
        for r in csv.DictReader(f, delimiter='\t'):
            rows.append(r)
    fams = {}
    for r in rows:
        fams.setdefault(r['family'], []).append(r)
    os.makedirs(os.path.join(OUT, "eisenmap"), exist_ok=True)

    for fam, members in fams.items():
        ms = []
        for r in sorted(members, key=lambda r: int(r['T'])):
            name = r['name']
            i = 1
            while i < len(name) and name[i].isdigit():
                i += 1
            V, clers = int(name[1:i]), name[i:]
            nid = net_id(V, clers)
            built = os.path.exists(os.path.join(OUT, "nets", nid, "net.json"))
            ms.append({"id": nid, "T": int(r['T']), "a": int(r['a']),
                       "b": int(r['b']), "v": V, "built": built})

        # static SVG: grid + member dots (JS recolors)
        parts = [f'<svg viewBox="0 0 {2*PAD + SCALE*(AMAX + AMAX/2)} '
                 f'{2*PAD + int(SCALE*AMAX*SQ3/2)}" '
                 f'xmlns="http://www.w3.org/2000/svg">']
        # sextant edges: b=0 ray and a=b ray
        x0, y0 = xy(0, 0)
        xe, ye = xy(AMAX, 0)
        xd, yd = xy(AMAX, AMAX)
        parts.append(f'<line x1="{x0}" y1="{y0}" x2="{xe}" y2="{ye}" '
                     f'stroke="#eee"/>')
        parts.append(f'<line x1="{x0}" y1="{y0}" x2="{xd}" y2="{yd}" '
                     f'stroke="#eee"/>')
        parts.append(f'<line id="ray" x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0}" '
                     f'stroke="#c33" stroke-dasharray="5 4" stroke-width="1.2" '
                     f'visibility="hidden"/>')
        for a in range(AMAX + 1):
            for b in range(a + 1):
                if a == 0:
                    continue
                x, y = xy(a, b)
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" '
                             f'fill="#e4e4e4"/>')
        for m in ms:
            x, y = xy(m["a"], m["b"])
            dot = (f'<circle id="m{m["a"]}_{m["b"]}" cx="{x:.1f}" cy="{y:.1f}" '
                   f'r="11" fill="#999"'
                   + ('' if m["built"] else ' fill-opacity="0.25" '
                      f'stroke="#999" stroke-dasharray="2 2"') + '/>')
            label = (f'<text x="{x:.1f}" y="{y - 15:.1f}" font-size="10.5" '
                     f'text-anchor="middle" fill="#555">T{m["T"]} '
                     f'({m["a"]},{m["b"]})</text>')
            vlab = (f'<text x="{x:.1f}" y="{y + 26:.1f}" font-size="9" '
                    f'text-anchor="middle" fill="#aaa">v={m["v"]}</text>')
            if m["built"]:
                parts.append(f'<a href="../nets/{m["id"]}/">{dot}{label}{vlab}</a>')
            else:
                parts.append(dot + label + vlab)
        parts.append('</svg>')
        svg = ''.join(parts)

        data = json.dumps([{k: m[k] for k in ("id", "a", "b", "built")}
                           for m in ms])
        html = f'''<!DOCTYPE html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Eisenstein map &mdash; {fam}</title><style>{CSS}</style></head><body>
<h1><a href="../index.html">Neoplatonic solids</a> &middot; Eisenstein map: {fam}</h1>
<p class=desc>The {fam} family: the unit net subdivided by a + b&omega;
(T = a&sup2;+ab+b&sup2;). Mirror images are lumped ((a,b) ~ (b,a)).
Open with <code>?net=&lt;id&gt;</code> to color relative to that net;
the dashed ray marks its Z-multiples, whose large-k limit is the thing
to understand. Hollow dots are not built yet. Clicking a dot opens the
net&rsquo;s page.</p>
<div class=legend>
<span><i style="background:#c33"></i>this net</span>
<span><i style="background:#2255aa"></i>ancestors</span>
<span><i style="background:#0a8a2a"></i>descendants</span>
<span><i style="background:#999"></i>cousins</span>
</div>
{svg}
<script>
const MEMBERS = {data};
const PAD = {PAD}, SCALE = {SCALE}, AMAX = {AMAX}, SQ3 = Math.sqrt(3);
function divides(a, b, c, d) {{
  // (a + b w) | (c + d w) in Z[w] (w = sixth root), by norm test
  const N = a*a + a*b + b*b;
  if (N === 0) return false;
  const p = c*a + c*b + d*b, q = d*a - c*b;
  return p % N === 0 && q % N === 0;
}}
function divM(m, n) {{  // mirror-lumped divisibility: m | n
  return divides(m.a, m.b, n.a, n.b) || divides(m.b, m.a, n.a, n.b);
}}
const sel = new URLSearchParams(location.search).get('net');
const me = MEMBERS.find(m => m.id === sel);
if (me) {{
  for (const m of MEMBERS) {{
    const el = document.getElementById('m' + m.a + '_' + m.b);
    if (!el) continue;
    let col = '#999';
    if (m.id === me.id) col = '#c33';
    else if (divM(m, me)) col = '#2255aa';
    else if (divM(me, m)) col = '#0a8a2a';
    el.setAttribute('fill', col);
  }}
  const k = Math.min(AMAX * 1.5 / (me.a + me.b / 2),
                     me.b > 0 ? AMAX / me.b : 1e9);
  const ray = document.getElementById('ray');
  ray.setAttribute('x2', PAD + SCALE * k * (me.a + me.b / 2));
  ray.setAttribute('y2', PAD + SCALE * (AMAX * SQ3 / 2) - SCALE * k * (me.b * SQ3 / 2));
  ray.setAttribute('visibility', 'visible');
}}
</script>
</body></html>'''
        with open(os.path.join(OUT, "eisenmap", f"{fam}.html"), 'w') as f:
            f.write(html)
        print(f'eisenmap/{fam}.html ({sum(m["built"] for m in ms)}/{len(ms)} built)')


if __name__ == "__main__":
    generate()
