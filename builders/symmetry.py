#!/usr/bin/env python3
"""Combinatorial symmetry of every built net: automorphism group order
split into rotations (orientation-preserving) and reflections. By
uniqueness of the realization, combinatorial automorphisms act as
isometries of the solid, so this is the solid's symmetry group.

Cache: data/symmetry.tsv (id, name, v, order, nrot, nrefl); computed
for records missing from the cache, so incremental runs are cheap.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
OUT = os.path.join(TOP, "site", "personal")
NETS = os.path.join(OUT, "nets")


def automorphisms_split(faces, V):
    """(n_rotations, n_reflections) of the face-structure automorphism
    group (walklib.automorphisms with the flip flag kept)."""
    apex = {}
    for a, b, c in faces:
        apex[(a, b)] = c; apex[(b, c)] = a; apex[(c, a)] = b
    darts = list(apex.keys())
    fs = set(min(f, f[1:] + f[:1], f[2:] + f[:2]) for f in faces)
    a0, b0 = darts[0]
    nrot = nrefl = 0
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
                if flip:
                    nrefl += 1
                else:
                    nrot += 1
    return nrot, nrefl


def main():
    cache = {}
    path = os.path.join(TOP, "data", "symmetry.tsv")
    if os.path.exists(path):
        for ln in open(path).read().splitlines()[1:]:
            t = ln.split('\t')
            cache[t[0]] = t
    new = 0
    for d in sorted(os.listdir(NETS)):
        if d in cache:
            continue
        p = os.path.join(NETS, d, "net.json")
        if not os.path.exists(p):
            continue
        rec = json.load(open(p))
        faces = [tuple(int(x) for x in f.split(','))
                 for f in rec["netcode"].split(';')]
        nrot, nrefl = automorphisms_split(faces, rec["v"])
        cache[d] = [d, rec["name"], str(rec["v"]),
                    str(nrot + nrefl), str(nrot), str(nrefl)]
        new += 1
        if new % 200 == 0:
            print(new, flush=True)
    with open(path, "w") as f:
        f.write("id\tname\tv\torder\tnrot\tnrefl\n")
        for d in sorted(cache):
            f.write('\t'.join(cache[d]) + '\n')
    print(f"symmetry.tsv: {len(cache)} rows ({new} new)")


if __name__ == "__main__":
    main()
