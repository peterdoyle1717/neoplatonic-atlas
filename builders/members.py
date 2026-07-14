#!/usr/bin/env python3
"""Assemble the page-worthy net list (data/nets_pages.txt: name netcode)
and the sidecar metadata used to stamp records:

  - all prime nets v <= 14 (the complete browse range),
  - from data/class_v30.tsv: all pancakes, all convex, all floppy
    (v <= 30), and the 8 deepest hull-buried nets per v,
  - the old atlas's hull-buried gallery list (kept for continuity),
  - Eisenstein subdivision families from atlas/subdiv/names.tsv,
    capped at V <= 132 for this pass (T <= 13).

Also writes data/eisenstein.tsv: name, family, T, a, b, ancestors,
descendants (ancestry = divisibility of a+b*omega in Z[omega] within
the same family, T ascending).
"""
import csv, os, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
NEO = os.path.dirname(TOP)
sys.path.insert(0, HERE)

spec = importlib.util.spec_from_file_location(
    "clers", os.path.join(NEO, "clers", "src", "clers.py"))
clers_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clers_mod)
decode = clers_mod.decode

SUBDIV_VCAP = 164


def netcode_of(name):
    faces = decode(name)
    return ';'.join(','.join(str(x) for x in f) for f in faces)


def eis_divides(a, b, c, d):
    """(a + b w) | (c + d w) in Z[w], w = exp(2 pi i/3)? Compute the
    quotient via norms: (c+dw)/(a+bw) = (c+dw)(conj)/N, integer test."""
    N = a * a + a * b + b * b
    if N == 0:
        return False
    # (c + d w)(a + b w-bar): w * w-bar identities give
    # real-part p = c*a + c*b + d*b, w-part q = d*a - c*b
    p = c * a + c * b + d * b
    q = d * a - c * b
    return p % N == 0 and q % N == 0


def main():
    seen = {}

    def add(name, nc=None):
        if name not in seen:
            seen[name] = nc or netcode_of(name)

    with open(os.path.join(TOP, "data", "nets_v4_14.txt")) as f:
        for ln in f:
            n, nc = ln.split()
            add(n, nc)
    with open(os.path.join(TOP, "data", "nets_buried_old.txt")) as f:
        for ln in f:
            n, nc, _ = ln.split()
            add(n, nc)

    rows = [r for r in csv.DictReader(
        open(os.path.join(TOP, "data", "class_v30.tsv")), delimiter='\t')
        if r['pancake'] != 'ERR']
    byv_buried = {}
    for r in rows:
        clers = r['name'][len(f"v{r['v']}"):]
        if int(r['pancake']) or int(r['convex']) or int(r['floppy']):
            add(clers)
        if int(r['nburied']):
            byv_buried.setdefault(int(r['v']), []).append(
                (float(r['depth']), clers))
    for v, lst in byv_buried.items():
        for _, clers in sorted(lst, reverse=True)[:8]:
            add(clers)

    # Eisenstein subdivision families
    fam = []
    for src in (os.path.join(NEO, "atlas", "subdiv", "names.tsv"),
                os.path.join(TOP, "data", "subdiv_extra.tsv")):
        if not os.path.exists(src):
            continue
        with open(src) as f:
            for row in csv.DictReader(f, delimiter='\t'):
                fam.append((row['base'], int(row['T']), int(row['a']),
                            int(row['b']), int(row['V']), row['CLERS']))
    eis_rows = []
    for base, T, a, b, V, clers in fam:
        anc, desc = [], []
        for base2, T2, a2, b2, V2, clers2 in fam:
            if base2 != base or (a2, b2) == (a, b):
                continue
            if T2 < T and eis_divides(a2, b2, a, b):
                anc.append((T2, f"v{V2}{clers2}"))
            if T2 > T and eis_divides(a, b, a2, b2):
                desc.append((T2, f"v{V2}{clers2}"))
        eis_rows.append((f"v{V}{clers}", base, T, a, b,
                         ','.join(n for _, n in sorted(anc)),
                         ','.join(n for _, n in sorted(desc))))
        if V <= SUBDIV_VCAP:
            add(clers)

    with open(os.path.join(TOP, "data", "eisenstein.tsv"), "w") as f:
        f.write("name\tfamily\tT\ta\tb\tancestors\tdescendants\n")
        for row in eis_rows:
            f.write('\t'.join(str(x) for x in row) + '\n')

    out = os.path.join(TOP, "data", "nets_pages.txt")
    with open(out, "w") as f:
        for name, nc in sorted(seen.items(), key=lambda kv: (len(kv[0]), kv[0])):
            f.write(f"{name} {nc}\n")
    print(f"{len(seen)} page-worthy nets -> {out}; "
          f"{len(eis_rows)} eisenstein rows")


if __name__ == "__main__":
    main()
