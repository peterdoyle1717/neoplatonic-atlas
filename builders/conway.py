#!/usr/bin/env python3
"""Conway orbifold symbols for every built net's symmetry group.

The automorphism group of a net acts (by uniqueness of the realization)
as a finite sphere group; the symbol is decided combinatorially:
  - rotation subgroup R: cyclic (nn), dihedral (22n), T (332), O (432),
    I (235) -- by |R| and the maximal rotation order;
  - with reversing elements (|G| = 2|R|): mirrors are reversing
    involutions FIXING some cell (vertex, edge pair, or face set);
    the inversion is the reversing involution fixing NOTHING;
    counting mirrors/inversion + max reversing order separates
    *nn / n* / nx, *22n / 2*n, *332 / 3*2, *432, *235.
Convention (PD 2026-07-14): digits DESCENDING, e.g. 532 and *532,
dihedral n22 / *n22 (432, 332, 3*2, 2*n as standard).
Output: data/conway.tsv (id, symbol); validation table printed.
"""
import json, math, os, sys
from functools import reduce

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
NETS = os.path.join(TOP, "site", "personal", "nets")


def autos_full(faces, V):
    apex = {}
    for a, b, c in faces:
        apex[(a, b)] = c; apex[(b, c)] = a; apex[(c, a)] = b
    darts = list(apex.keys())
    fs = set(min(f, f[1:] + f[:1], f[2:] + f[:2]) for f in faces)
    a0, b0 = darts[0]
    out = []
    for (c0, d0) in darts:
        for flip in (0, 1):
            m = {a0: c0, b0: d0}
            ok = True
            stack = [(a0, b0, c0, d0)]
            seend = set()
            while stack and ok:
                x, y, u, w = stack.pop()
                if (x, y) in seend:
                    continue
                seend.add((x, y))
                z = apex[(x, y)]
                t = apex[(u, w)] if not flip else apex[(w, u)]
                if z in m:
                    if m[z] != t:
                        ok = False
                        break
                else:
                    m[z] = t
                stack.append((y, z, w, t))
                stack.append((z, x, t, u))
                stack.append((y, x, w, u))
            if not (ok and len(m) == V and len(set(m.values())) == V):
                continue
            good = True
            for (a, b, c) in faces:
                im = (m[a], m[b], m[c]) if not flip else (m[c], m[b], m[a])
                if min(im, im[1:] + im[:1], im[2:] + im[:2]) not in fs:
                    good = False
                    break
            if good:
                out.append((m, flip))
    return out


def perm_order(m):
    seen, orders = set(), []
    for s in m:
        if s in seen:
            continue
        n, x = 0, s
        while True:
            x = m[x]; n += 1; seen.add(x)
            if x == s:
                break
        orders.append(n)
    return reduce(math.lcm, orders, 1)


def fixes_cell(m, faces, edges):
    for v in m:
        if m[v] == v:
            return True
    for a, b in edges:
        if {m[a], m[b]} == {a, b}:
            return True
    for f in faces:
        if tuple(sorted((m[f[0]], m[f[1]], m[f[2]]))) == tuple(sorted(f)):
            return True
    return False


def symbol(faces, V):
    edges = sorted({(min(a, b), max(a, b)) for f in faces
                    for a, b in zip(f, f[1:] + f[:1])})
    A = autos_full(faces, V)
    g = len(A)
    rots = [(m, perm_order(m)) for m, fl in A if fl == 0]
    revs = [(m, perm_order(m)) for m, fl in A if fl == 1]
    r = len(rots)
    maxrot = max(o for _, o in rots)
    # rotation subgroup type
    if r == 60:
        R = 'I'
    elif r == 24 and maxrot == 4:
        R = 'O'
    elif r == 12 and maxrot == 3:
        R = 'T'
    elif r == maxrot:
        R = 'C'          # cyclic C_maxrot (incl. C1)
    elif r == 2 * maxrot:
        R = 'D'          # dihedral D_maxrot
    else:
        return f'?r{r}m{maxrot}'
    n = maxrot
    def d(k):            # digit with separator for >9
        return str(k) if k < 10 else f'({k})'
    if not revs:
        return {'I': '532', 'O': '432', 'T': '332',
                'C': '1' if n == 1 else d(n) + d(n),
                'D': d(n) + '22'}[R]
    mirrors = sum(1 for m, o in revs if o == 2 and fixes_cell(m, faces, edges))
    inv = sum(1 for m, o in revs if o == 2 and not fixes_cell(m, faces, edges))
    maxrev = max(o for _, o in revs)
    if R == 'I':
        return '*532'
    if R == 'O':
        return '*432'
    if R == 'T':
        return '3*2' if inv else '*332'
    if R == 'D':
        return ('*' + d(n) + '22') if mirrors == n + 1 else ('2*' + d(n))
    # cyclic
    if n == 1:
        return '*' if mirrors else 'x'
    if mirrors == n:
        return '*' + d(n) + d(n)
    if mirrors == 1:
        return d(n) + '*'
    return d(n) + 'x'


def main():
    out = {}
    for dd in sorted(os.listdir(NETS)):
        p = os.path.join(NETS, dd, "net.json")
        if not os.path.exists(p):
            continue
        rec = json.load(open(p))
        faces = [tuple(int(x) for x in f.split(','))
                 for f in rec["netcode"].split(';')]
        out[dd] = symbol(faces, rec["v"])
    with open(os.path.join(TOP, "data", "conway.tsv"), "w") as f:
        f.write("id\tconway\n")
        for k, v in sorted(out.items()):
            f.write(f"{k}\t{v}\n")
    import collections
    print(collections.Counter(out.values()).most_common())


if __name__ == "__main__":
    main()
