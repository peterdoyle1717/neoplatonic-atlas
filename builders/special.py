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
    sym = {}
    spath = os.path.join(TOP, "data", "symmetry.tsv")
    if os.path.exists(spath):
        for ln in open(spath).read().splitlines()[1:]:
            t = ln.split('\t')
            sym[t[0]] = (int(t[3]), int(t[4]), int(t[5]))
    classics = {}
    cxpath = os.path.join(TOP, "data", "classics.tsv")
    if os.path.exists(cxpath):
        for ln in open(cxpath).read().splitlines()[1:]:
            t = ln.split('\t')
            V = int(t[3])
            classics.setdefault(f"v{V}{t[2]}", []).append(t[1])
    themes = {}
    tpath = os.path.join(TOP, "data", "themes.tsv")
    if os.path.exists(tpath):
        for r in csv.DictReader(open(tpath), delimiter='\t'):
            themes[r['name']] = r['themes'].split(',')
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
        cx = classics.get(rec.get("name", d))
        if cx:
            tag = ("The neoplatonic (capped/fanned) form of: "
                   + "; ".join(dict.fromkeys(cx)) + ".")
            if tag not in rec.get("notes", ""):
                rec["notes"] = (rec.get("notes", "") + " " + tag).strip()
                changed = True
        sy = sym.get(d)
        if sy and (rec.get("flags", {}).get("sym_order") != sy[0]
                   or rec.get("flags", {}).get("sym_refl") != (sy[2] > 0)):
            rec.setdefault("flags", {})["sym_order"] = sy[0]
            rec["flags"]["sym_refl"] = sy[2] > 0
            changed = True
        t = themes.get(rec.get("name", d))
        if t is not None and rec.get("themes") != t:
            rec["themes"] = t
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
            f'<nav style="font-size:.9em"><a href="../index.html">'
            f'neoplatonic solids</a></nav>'
            f'<h1>{title}</h1>'
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
                  for r in buried[:120]])
            + '<h2>All built hull-buried nets</h2><p class=desc>'
            + ' &middot; '.join(
                f'<a href="../nets/{r.get("id", r["name"])}/">'
                f'{display(r["name"], 30)}</a> d={r["flags"]["buried_depth"]:.3f}'
                for r in buried) + '</p>')

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
            'Subdivisions are computed with the <a href="https://www.antiprism.com/">'
            'Antiprism</a> package by Adrian Rossiter (the <code>geodesic</code> '
            'program). '
            'Members up to v = 132 are built so far; each page lists '
            'the net&rsquo;s Eisenstein ancestors and descendants.',
            ''.join(parts))

    # -- symmetry gallery ----------------------------------------------
    symrows = []
    spath = os.path.join(TOP, "data", "symmetry.tsv")
    if os.path.exists(spath):
        for ln in open(spath).read().splitlines()[1:]:
            t = ln.split('\t')
            r = recs.get(t[0])
            if r:
                symrows.append((int(t[3]), int(t[5]) > 0, int(t[2]), r))
    classes = {}
    for order, refl, v, r in symrows:
        classes.setdefault((order, refl), []).append((v, r))
    parts = []
    for (order, refl) in sorted(classes, key=lambda k: (-k[0], k[1])):
        rows_ = sorted(classes[(order, refl)], key=lambda t: (t[0], t[1]["name"]))
        kind = 'with reflections' if refl else 'chiral'
        parts.append(f'<h2>order {order}, {kind} &mdash; '
                     f'{len(rows_)} built nets</h2>')
        parts.append(grid([item(r, f'v={v}') for v, r in rows_[:8]]))
    gallery('symmetry.html', 'Symmetry',
            'One class per automorphism-group order and chirality, over '
            'the nets built in this atlas (combinatorial automorphisms; '
            'by uniqueness of the realization these act as isometries of '
            'the solid). Up to 8 exemplars per class, smallest first. '
            'Rotation-only groups are marked chiral.',
            ''.join(parts))

    byname_pre = {r["name"]: r for r in recs.values()}
    # -- all-recognized-angles gallery (data lands from
    # recognize_sweep.py; criterion v1, PD: every bend a construction
    # angle, at least one icosahedral atom I) -------------------------
    rpath = os.path.join(TOP, "data", "recognized_v30.tsv")
    if os.path.exists(rpath):
        rrows = []
        for ln in open(rpath).read().splitlines()[1:]:
            t = ln.split('\t')
            if len(t) >= 4 and t[2] == '1':
                V = int(t[1])
                r = byname_pre.get(f"v{V}{t[0]}")
                if r:
                    rrows.append((V, int(t[3]), r))
        rrows.sort(key=lambda x: (x[0], x[2]["name"]))
        gallery('recognized.html', 'All angles recognized',
                f'All {len(rrows)} prime nets v &le; 30 whose every bend '
                'is a recognized construction angle (library of '
                'notes/bend_recognize.py, |b| matched at 1e-7 against '
                'solver-emitted bends). PD: this mostly detects pentagon '
                '(and square) pyramid vertices; the icosahedral-relative '
                'criterion is under construction. Captions mark '
                'icosahedral-atom counts where present.',
                grid([item(r, f'v={v}' + (f' &middot; {k}&times;I' if k else ''))
                      for v, k, r in rrows]))

    # cap-replaced convex gallery (decap_search.py)
    dpath2 = os.path.join(TOP, "data", "decap_v30.tsv")
    if os.path.exists(dpath2):
        JNAME = {"j1": "square pyramid", "j14": "elong. tri. bipyramid",
                 "j26": "gyrobifastigium", "j27": "tri. orthobicupola",
                 "j44": "elong. tri. gyrobicupola",
                 "j50": "biaug. triangular prism",
                 "j85": "snub square antiprism", "j86": "sphenocorona",
                 "j88": "sphenomegacorona", "j89": "hebesphenomegacorona",
                 "ico": "icosahedron", "pri3": "triangular prism",
                 "ant4": "square antiprism", "cube,pri4": "cube",
                 "cuboctahedron,j27": "cubocta / tri. orthobicupola"}
        dnames = {}
        npath = os.path.join(TOP, "data", "decap_names.tsv")
        if os.path.exists(npath):
            for ln in open(npath).read().splitlines()[1:]:
                t = ln.split('\t')
                dnames[t[0]] = JNAME.get(t[4], t[4] if t[4] != '-' else '')
        drows2 = []
        for ln in open(dpath2).read().splitlines()[1:]:
            t = ln.split('\t')
            if t[4] == 'CONVEX':
                V = int(t[1])
                r = byname_pre.get(f"v{V}{t[0]}")
                if r:
                    drows2.append((V, int(t[2]), int(t[3]), r,
                                   dnames.get(t[0], '')))
        drows2.sort(key=lambda x: (x[0], x[3]["name"]))
        gallery('decap.html', 'Cap-replaced convex',
                f'Nets whose realization carries exact square or pentagon '
                f'pyramid caps (planar unit ring, diagonals &radic;2 or '
                f'&phi;, tol 1e-4) and becomes CONVEX when every cap is '
                f'replaced by its flat polygon &mdash; all '
                f'{len(drows2)} such prime nets v &le; 30 '
                f'(decap_search.py over the census coordinates).',
                grid([item(r, f'v={v} &middot; {ns} sq, {np_} pent'
                           + (f' &middot; {dn}' if dn else ''))
                      for v, ns, np_, r, dn in drows2]))

    # -- icosahedral-relatives gallery (icorel_sweep.py) ----------------
    ipath = os.path.join(TOP, "data", "icorel_v30.tsv")
    if os.path.exists(ipath):
        RELNAME = {"dod": "dodecahedron", "ico": "icosahedron",
                   "idd": "icosidodecahedron", "rid1": "rhombicosidodeca (3-4)",
                   "rid2": "rhombicosidodeca (4-5)", "snub1": "snub dodeca (3-3)",
                   "snub2": "snub dodeca (3-4)"}
        irows = []
        for ln in open(ipath).read().splitlines()[1:]:
            t = ln.split('\t')
            if len(t) >= 9 and t[2]:
                V = int(t[1])
                r = byname_pre.get(f"v{V}{t[0]}")
                if r:
                    cap = ', '.join(f"{RELNAME.get(h.split(':')[0], h)}&times;{h.split(':')[1]}"
                                    for h in t[2].split(','))
                    irows.append((V, cap, r))
        irows.sort(key=lambda x: (x[0], x[2]["name"]))
        gallery('icorel.html', 'Icosahedral relatives',
                'Nets sharing a bend with an icosahedral-family solid '
                '(dodecahedron, icosahedron, icosidodecahedron, '
                'rhombicosidodecahedron, snub dodecahedron; dihedrals '
                'measured from Antiprism models, matched at 1e-7 against '
                'solver-emitted Euclidean bends). Only '
                f'{len(irows)} prime nets v &le; 30 qualify; no net below '
                'v = 30 carries the icosidodecahedral or snub values.',
                grid([item(r, f'v={v} &middot; {cap}') for v, cap, r in irows]))

    # -- degree-7 classics, hyperbolically -------------------------------
    d7path = os.path.join(TOP, "data", "theme_deg7.txt")
    if os.path.exists(d7path):
        d7rows = []
        cxnames = {}
        for ln in open(os.path.join(TOP, "data", "classics.tsv")).read().splitlines()[1:]:
            t = ln.split('\t')
            if t[4] == '0':
                cxnames.setdefault(t[2], []).append(t[1])
        for nm in open(d7path).read().split():
            V = (len(nm) + 4) // 2
            r = byname_pre.get(f"v{V}{nm}")
            if r:
                d7rows.append((V, '; '.join(dict.fromkeys(cxnames.get(nm, [])))[:60], r))
        d7rows.sort(key=lambda x: (x[1].startswith('j'), x[0], x[2]["name"]))
        gallery('deg7.html', 'Degree-7 classics, hyperbolically',
                'Classics whose capping forces a degree-7 vertex have no '
                'Euclidean neoplatonic form (7 unit triangles = 420&deg;), '
                'but they exist as ideal polyhedra and as equilateral '
                'hyperbolic polyhedra for corner angles up to '
                '&alpha; = 360/7 &asymp; 51.43&deg;, where the degree-7 '
                'vertices go flat. Hero models show the Klein-ball view at '
                '&alpha; = 360/7; morphs run from the ideal end up to it.',
                grid([item(r, f'v={v} &middot; {names}') for v, names, r in d7rows]))

    # -- classics gallery ----------------------------------------------
    cxpath = os.path.join(TOP, "data", "classics.tsv")
    if os.path.exists(cxpath):
        seenc, crows = set(), []
        for ln in open(cxpath).read().splitlines()[1:]:
            t = ln.split('\t')
            V = int(t[3])
            hyp = len(t) > 4 and t[4] == '0'
            nm = f"v{V}{t[2]}"
            if nm in seenc:
                for c in crows:
                    if c[2]["name"] == nm and t[1] not in c[1]:
                        c[1].append(t[1])
                continue
            seenc.add(nm)
            r = byname_pre.get(nm)
            if r:
                crows.append([V, [t[1]], r, hyp])
        def rank_of(names):
            first = names[0]
            if first in ('tetrahedron', 'cube', 'octahedron', 'icosahedron',
                         'dodecahedron'):
                return 0
            if not first.startswith(('j', 'pri', 'ant')):
                return 1
            if first.startswith(('pri', 'ant')):
                return 2
            return 3

        def cap(v, names, hyp):
            c = f'v={v} &middot; ' + '; '.join(names[:2])
            if len(names) > 2:
                c += '&hellip;'
            if hyp:
                c += ' &middot; hyperbolic, &alpha; &le; 360/7'
            return c
        SECT = {0: 'Platonic', 1: 'Archimedean', 2: 'Prisms and antiprisms'}
        parts = []
        for rank in (0, 1, 2):
            sel = [(v, names, r, hyp) for v, names, r, hyp in crows
                   if rank_of(names) == rank]
            if not sel:
                continue
            parts.append(f'<h2>{SECT[rank]}</h2>')
            parts.append(grid([item(r, cap(v, names, hyp))
                               for v, names, r, hyp in sel]))
        gallery('classics.html', 'The classics, neoplatonized',
                'Named solids in their neoplatonic reading: triangle faces '
                'kept, squares and pentagons capped by unit pyramids, '
                'hexagons filled by flat unit fans (faces are in the eye '
                'of the beholder). Generated from Antiprism models '
                '(builders/classics.py); variants that collapse to the '
                'same net share a cell. Blue models are the degree-7 '
                'members: no Euclidean form, realized hyperbolically up '
                'to &alpha; = 360/7 (see the degree-7 annex). Johnson '
                'solids have their own gallery, Odds and ends.',
                ''.join(parts))

        jsel = [(v, names, r, hyp) for v, names, r, hyp in crows
                if rank_of(names) == 3]
        gallery('oddsends.html', 'Odds and ends',
                'Johnson solids and other named constructions in their '
                'neoplatonic reading. Blue models are degree-7 members, '
                'realized hyperbolically up to &alpha; = 360/7.',
                grid([item(r, cap(v, names, hyp))
                      for v, names, r, hyp in jsel]))

    # -- themed galleries from the old atlas ---------------------------
    tdesc = {}
    dpath = os.path.join(TOP, "data", "theme_desc.tsv")
    if os.path.exists(dpath):
        for r in csv.DictReader(open(dpath), delimiter='\t'):
            tdesc[r['theme']] = (r['title'], r['desc'])
    byname = {r["name"]: r for r in recs.values()}

    def theme_list(tag):
        out = []
        tp = os.path.join(TOP, "data", f"theme_{tag}.txt")
        if os.path.exists(tp):
            for nm in open(tp).read().split():
                V = (len(nm) + 4) // 2
                r = byname.get(f"v{V}{nm}")
                if r:
                    out.append(r)
        return out

    for tag in ("bucky", "phyllo31", "phyllo22", "phyllo41", "phyllo51",
                "flops", "nonprime", "preapproved", "small"):
        rows = theme_list(tag)
        title, desc = tdesc.get(tag, (tag, ""))
        if tag == "bucky":
            parts = []
            byvv = {}
            for r in rows:
                byvv.setdefault(r["v"], []).append(r)
            for vv in sorted(byvv):
                parts.append(f'<h2>v = {vv}</h2>')
                parts.append(grid([item(r, f'v={vv}') for r in byvv[vv]]))
            body_html = ''.join(parts)
        else:
            body_html = grid([item(r, f'v={r["v"]}') for r in rows])
        gallery(f'{tag}.html', title, desc, body_html)

    # dented: old-atlas dent GLBs living in the owning nets' dirs,
    # thumbnails linking through to the (undented) net page
    drows = []
    ddpath = os.path.join(TOP, "data", "dented_old.tsv")
    if os.path.exists(ddpath):
        for r in csv.DictReader(open(ddpath), delimiter='\t'):
            V = (len(r['name']) + 4) // 2
            rec = byname.get(f"v{V}{r['name']}")
            if not rec:
                continue
            nid = rec.get("id", rec["name"])
            if os.path.exists(os.path.join(NETS, nid, f"dent_v{r['k']}.glb")):
                drows.append(
                    f'<div class=item><div class=cell>'
                    f'<model-viewer src="../nets/{nid}/dent_v{r["k"]}.glb" '
                    f'camera-orbit="0deg 100deg auto" camera-controls '
                    f'interaction-prompt=none></model-viewer></div>'
                    f'<a href="../nets/{nid}/">{display(rec["name"])}</a> '
                    f'<span class=v>v={V} dent at vertex {r["k"]}</span></div>')
    title, desc = tdesc.get("dented", ("Dented", ""))
    gallery('dented.html', title,
            desc + ' Thumbnails link to the undented realization.',
            grid(drows))

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
                grid([item(r, f'v={v}'
                           + (' non-prime' if 'nonprime' in r.get("themes", [])
                              else '')
                           + (f' deg {r["maxdeg"]}' if r.get("maxdeg", 6) > 6
                              else '')) for r in
                      sorted(rows, key=lambda r: (r.get("maxdeg", 6) > 6,
                                                  r["name"]))]),
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
<a href="about.html">More &rarr;</a>
</p>

<h2>Themed galleries</h2>
<div class="gallery-links">
<a href="gallery/small.html">Small (v&le;12)</a>
<a href="gallery/bucky.html">Bucky</a>
<a href="gallery/convex.html">Convex</a>
<a href="gallery/dented.html">Dented</a>
<a href="gallery/buried.html">Hull-buried</a>
<a href="gallery/pancakes.html">Pancakes</a>
<a href="gallery/floppy.html">Floppy</a>
<a href="gallery/symmetry.html">Symmetry</a>
<a href="gallery/recognized.html">All angles recognized</a>
<a href="gallery/decap.html">Cap-replaced convex</a>
<a href="gallery/classics.html">Classics</a>
<a href="gallery/oddsends.html">Odds and ends</a>
<a href="gallery/icorel.html">Icosahedral relatives</a>
<a href="gallery/deg7.html">Degree-7 classics</a>
<a href="gallery/phyllo31.html">(3,1)</a>
<a href="gallery/phyllo22.html">(2,2)</a>
<a href="gallery/phyllo41.html">(4,1)</a>
<a href="gallery/phyllo51.html">(5,1)</a>
<a href="gallery/subdiv.html">Eisenstein subdivisions</a>
<a href="gallery/preapproved.html">Preapproved</a>
<a href="gallery/nonprime.html">Non-prime</a>
<a href="gallery/flops.html">Tough cases</a>
</div>
<h2>Example</h2>
<div class="example-row">
  <div class="blurb">
    Each neoplatonic has its own page &mdash; the Euclidean solid, the
    morph from the ideal limit in the Poincar&eacute; and Klein models,
    the ideal net, and the CLERS triangulation. <strong>Click the CLERS
    code under the model to the right</strong> to open its page.
  </div>
  <div class="thumb">
    <model-viewer src="nets/{ex}/rb.glb"
      camera-orbit="0deg 100deg auto" camera-controls interaction-prompt="none"></model-viewer>
    <div class="label"><a href="nets/{ex}/">{ex}</a></div>
  </div>
</div>
<h2>Quick links by size</h2>
<div class="gallery-links">
{quick}</div>
<div class="gallery-links" style="font-size:.85em">
{more}</div>
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
    import shutil
    shutil.copy(os.path.join(HERE, "assets", "about.html"),
                os.path.join(OUT, "about.html"))
    import eisenmap
    eisenmap.generate()
    import views
    views.main()


if __name__ == "__main__":
    main()
