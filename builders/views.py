#!/usr/bin/env python3
"""View layer: render a net's index.html from its net.json record.

The record is the database; this file is the only place that knows
what a net's homepage looks like. Rerun over all records to change
the display (python3 builders/views.py re-renders every page under
site/personal/nets/).
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
OUT = os.path.join(TOP, "site", "personal")


def net_id(V, clers):
    """directory key for a net: the v-prefixed name when it fits the
    filesystem (255-byte path components; v=128 names hit 256), else a
    hashed key. Display names always come from the record, never from
    the key."""
    full = f"v{V}{clers}"
    if len(full) <= 200:
        return full
    return f"v{V}h" + hashlib.sha1(clers.encode()).hexdigest()[:16]


def display(name, cap=44):
    """elide long display names for gallery captions."""
    return name if len(name) <= cap else name[:cap - 12] + '&hellip;' + name[-8:]

STYLE = ("body{font-family:Georgia,serif;max-width:680px;margin:2em auto;"
         "line-height:1.6;color:#222;padding:0 1em}"
         "h1{font-family:monospace;font-size:1.2em;word-break:break-all}"
         "nav{font-size:.9em}nav a{color:#2255aa;text-decoration:none}"
         "nav a:hover{text-decoration:underline}"
         ".info{font-size:.9em;color:#555;margin:-.5em 0 .5em}"
         ".flags{font-size:.85em;color:#777;margin:0 0 .5em}"
         ".hint{font-size:.8em;color:#aaa;font-style:italic;margin-bottom:1em}"
         ".pair{display:grid;grid-template-columns:1fr 1fr;gap:.8em;margin-bottom:1em}"
         ".cell{position:relative;width:100%;padding-bottom:100%}"
         ".cell iframe{position:absolute;top:0;left:0;width:100%;height:100%;border:none}"
         ".cell .svgwrap{position:absolute;top:0;left:0;width:100%;height:100%;"
         "display:flex;align-items:center;justify-content:center;"
         "border:1px solid #ddd;box-sizing:border-box}"
         ".cell .svgwrap img{max-width:90%;max-height:90%}"
         ".label{text-align:center;font-size:.8em;color:#888;margin-top:.2em}"
         "a{color:#2255aa}")


def netlink(name):
    """name -> link to its page (recomputes the id rule)."""
    i = 1
    while i < len(name) and name[i].isdigit():
        i += 1
    V, clers = int(name[1:i]), name[i:]
    return f'<a href="../{net_id(V, clers)}/">{display(name, 28)}</a>'


def flag_line(rec):
    fl = rec.get("flags", {})
    bits = []
    if fl.get("pancake"):
        bits.append("pancake")
    elif fl.get("strictly_convex"):
        bits.append("strictly convex")
    elif fl.get("convex"):
        bits.append("convex")
    if fl.get("buried"):
        bits.append(f'{fl["buried"]} buried '
                    f'vert{"ex" if fl["buried"] == 1 else "ices"} '
                    f'(depth {fl.get("buried_depth", 0):.3f})')
    if fl.get("floppy"):
        bits.append("floppy")
    ei = rec.get("eisenstein", {})
    if ei.get("family"):
        nid = rec.get("id", rec.get("name", ""))
        bits.append(f'Eisenstein: {ei["family"]} T={ei["T"]} '
                    f'({ei["a"]},{ei["b"]}) &middot; '
                    f'<a href="../../eisenmap/{ei["family"]}.html?net={nid}">'
                    f'family map</a>')
    return " &middot; ".join(bits)


def render_page(netdir):
    rec = json.load(open(os.path.join(netdir, "net.json")))
    name, V = rec["name"], rec["v"]
    nid = rec.get("id", name)
    art = rec.get("artifacts", {})

    def cell_iframe(src, label):
        return (f'<div><div class=cell><iframe src="{src}"></iframe></div>'
                f'<div class=label>{label}</div></div>')

    def cell_svg(fname, label):
        return (f'<div><div class=cell><div class=svgwrap>'
                f'<img src="{fname}" alt="{label}"></div></div>'
                f'<div class=label>{label}</div></div>')

    flags = flag_line(rec)
    body = [f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8>'
            f'<meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>{name}</title><style>{STYLE}</style></head><body>'
            f'<nav><a href="../../by-v/{V}.html">{V} vertices</a> &middot; '
            f'<a href="../../index.html">neoplatonic solids</a></nav>'
            f'<h1>{name}</h1>'
            f'<p class=info>V={V} &nbsp; E={rec["E"]} &nbsp; F={rec["F"]}</p>'
            + (f'<p class=flags>{flags}</p>' if flags else '')
            + '<p class=hint>Models can be manipulated.</p>',
            '<div class=pair>']
    if art.get("rb"):
        body.append(cell_iframe(f'../../turntable.html?file=nets/{nid}/rb.glb',
                                'Euclidean'))
    # 2x2 block:  Euclidean | Poincare morph
    #             Klein morph | ideal net
    if art.get("morph_p"):
        body += [cell_iframe(f'../../morph.html?file=nets/{nid}/morph_p.glb',
                             'ideal to Euclidean, Poincar&eacute;'),
                 cell_iframe(f'../../morph.html?file=nets/{nid}/morph_k.glb',
                             'ideal to Euclidean, Klein')]
    if art.get("ideal_net"):
        body.append(cell_svg('ideal_net.svg', 'ideal net'))
    body.append('</div>')
    body.append('<div class=pair>')
    if art.get("clers_glb"):
        body.append(cell_iframe(f'../../turntable.html?file=nets/{nid}/clers.glb',
                                'CLERS colored'))
    if art.get("clers_layout"):
        body.append(cell_svg('clers_layout.svg', 'CLERS layout'))
    body.append('</div>')
    # Eisenstein lattice, embedded inline for nets with a built ancestor
    # or descendant (eismap.svg written by eisenmap.py; inline so the
    # dot links work)
    empath = os.path.join(netdir, "eismap.svg")
    ei = rec.get("eisenstein", {})
    if os.path.exists(empath):
        with open(empath) as f:
            emsvg = f.read()
        body += [f'<p class=info style="margin-top:1em">Eisenstein family '
                 f'{ei.get("family", "")} &mdash; red this net, blue '
                 f'ancestors, green descendants, grey cousins; mirror '
                 f'sector below the axis (reflections lumped); dashed ray = '
                 f'the Z-multiples.</p>',
                 emsvg]
    body.append('</body></html>')
    with open(os.path.join(netdir, "index.html"), "w") as f:
        f.write('\n'.join(body))


def main():
    nets = os.path.join(OUT, "nets")
    n = 0
    for d in sorted(os.listdir(nets)):
        netdir = os.path.join(nets, d)
        if os.path.exists(os.path.join(netdir, "net.json")):
            render_page(netdir)
            n += 1
    print(f"rendered {n} pages")


if __name__ == "__main__":
    main()
