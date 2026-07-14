#!/usr/bin/env python3
"""The classics, neoplatonized (PD 2026-07-14: "faces are in the eye
of the beholder ... let's fill in the missing named solids. so far we
don't even have the soccer ball!").

For every catalog solid (Platonic, Archimedean, prisms/antiprisms
n=3..6, Johnson j1..j92) whose faces all have <= 6 sides: keep
triangle faces, cap squares and pentagons with unit pyramids (apex at
height sqrt(1-R^2) over the centroid), fill hexagons with a flat unit
6-fan (R = 1 exactly, apex height 0). The result is a unit-triangle
net; canonicalize with clers.encode. Validate: every constructed edge
unit to 1e-6, encode/decode round-trip.

Output: data/classics.tsv (solid, label, CLERS, v) and
data/theme_classics.txt; notes text per net in classics.tsv's label.
"""
import math, os, subprocess, sys
import numpy as np
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
NEO = os.path.dirname(TOP)
BIN = os.path.expanduser("~/local/antiprism-0.32/bin")

spec = importlib.util.spec_from_file_location(
    "clers", os.path.join(NEO, "clers", "src", "clers.py"))
clers_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clers_mod)

PRETTY = {"tet": "tetrahedron", "cube": "cube", "oct": "octahedron",
          "ico": "icosahedron", "dod": "dodecahedron",
          "truncated_icosahedron": "truncated icosahedron (soccer ball)"}

CATALOG = (["tet", "cube", "oct", "ico", "dod",
            "cuboctahedron", "truncated_tetrahedron",
            "truncated_octahedron", "rhombicuboctahedron", "snub_cube",
            "icosidodecahedron", "truncated_icosahedron",
            "rhombicosidodecahedron", "snub_dodecahedron"]
           + [f"pri{n}" for n in (3, 4, 5, 6)]
           + [f"ant{n}" for n in (3, 4, 5, 6)]
           + [f"j{i}" for i in range(1, 93)])


def load_off(name):
    r = subprocess.run([f"{BIN}/off_util", name],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.startswith("OFF"):
        return None
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    nv, nf, _ = (int(x) for x in lines[1].split()[:3])
    P = np.array([[float(x) for x in lines[2+i].split()[:3]]
                  for i in range(nv)])
    F = []
    for l in lines[2+nv:2+nv+nf]:
        t = l.split()
        n = int(t[0])
        if n >= 3:
            F.append([int(x) for x in t[1:1+n]])
    return P, F


def neoplatonize(P, F):
    """returns (faces 1-based, coords) or None if a face > 6 sides or
    validation fails."""
    if any(len(f) > 6 for f in F):
        return None
    els = []
    for f in F:
        for i in range(len(f)):
            els.append(np.linalg.norm(P[f[i]] - P[f[(i+1) % len(f)]]))
    e = np.mean(els)
    if np.max(np.abs(np.array(els) - e)) > 1e-9 * max(1, e):
        return None
    P = (P - P.mean(axis=0)) / e
    pts = [tuple(p) for p in P]
    tris = []
    for f in F:
        # outward winding: normal away from the origin
        c = P[f].mean(axis=0)
        n = np.zeros(3)
        for i in range(len(f)):
            n += np.cross(P[f[i]] - c, P[f[(i+1) % len(f)]] - c)
        fo = f if np.dot(n, c) > 0 else f[::-1]
        if len(fo) == 3:
            tris.append(tuple(x + 1 for x in fo))
            continue
        R = float(np.mean([np.linalg.norm(P[x] - c) for x in fo]))
        h2 = 1.0 - R * R
        if h2 < -1e-9:
            return None
        nn = np.zeros(3)
        for i in range(len(fo)):
            nn += np.cross(P[fo[i]] - c, P[fo[(i+1) % len(fo)]] - c)
        nn = nn / np.linalg.norm(nn)
        apex = c + math.sqrt(max(0.0, h2)) * nn
        ai = len(pts)
        pts.append(tuple(apex))
        for i in range(len(fo)):
            tris.append((fo[i] + 1, fo[(i+1) % len(fo)] + 1, ai + 1))
    Q = np.array(pts)
    for a, b, c_ in tris:
        for x, y in ((a, b), (b, c_), (c_, a)):
            if abs(np.linalg.norm(Q[x-1] - Q[y-1]) - 1.0) > 1e-6:
                return None
    return tris, Q


def main():
    rows = []
    for name in CATALOG:
        off = load_off(name)
        if off is None:
            continue
        z = neoplatonize(*off)
        if z is None:
            continue
        tris, Q = z
        V = len(Q)
        nc = ';'.join(','.join(str(x) for x in f) for f in tris)
        p1 = subprocess.run([os.path.join(NEO, "clers", "bin", "clers"), "name"],
                            input=nc, capture_output=True, text=True)
        if p1.returncode != 0:
            print(f"{name}: clers name FAIL")
            continue
        cn = p1.stdout.strip()
        faces2 = clers_mod.decode(cn)
        if max(max(f) for f in faces2) != V:
            print(f"{name}: V mismatch after canonicalization")
            continue
        pretty = PRETTY.get(name, name.replace("_", " "))
        rows.append((name, pretty, cn, V))
        print(f"{name:26s} -> v={V}  {cn[:40]}", flush=True)
    with open(os.path.join(TOP, "data", "classics.tsv"), "w") as f:
        f.write("solid\tpretty\tCLERS\tv\n")
        for r in rows:
            f.write('\t'.join(str(x) for x in r) + '\n')
    with open(os.path.join(TOP, "data", "theme_classics.txt"), "w") as f:
        seen = set()
        for _, _, cn, _ in rows:
            if cn not in seen:
                seen.add(cn)
                f.write(cn + '\n')
    print(f"{len(rows)} classics; {len(seen)} distinct nets")


if __name__ == "__main__":
    main()
