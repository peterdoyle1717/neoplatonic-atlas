#!/usr/bin/env python3
"""Cap-replacement search (PD 2026-07-14): find prime nets v <= 30
whose realization has exact SQUARE caps (degree-4 vertex over a planar
unit square: diagonals sqrt2) and/or PENTAGON caps (degree-5 vertex
over a planar regular unit pentagon: diagonals phi), such that
replacing every cap by its flat polygon yields a CONVEX solid (every
edge bend of the de-capped complex >= -1e-6).

Coordinates from neo/data/objs (doob DP objs; geometric detection at
1e-4 -- value-matching only, no bend-census use). Output:
data/decap_v30.tsv: name, v, nsq, npent, verdict.
"""
import math, os, sys, importlib.util
from multiprocessing import Pool
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
NEO = os.path.dirname(TOP)
OBJS = os.path.join(NEO, "data", "objs")
TOL = 1e-4
PHI = (1 + math.sqrt(5)) / 2

spec = importlib.util.spec_from_file_location(
    "clers", os.path.join(NEO, "clers", "src", "clers.py"))
clers_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clers_mod)
decode = clers_mod.decode

def links(V, faces):
    nxt = {}
    for a, b, c in faces:
        nxt.setdefault(a, {})[b] = c
        nxt.setdefault(b, {})[c] = a
        nxt.setdefault(c, {})[a] = b
    cyc = {}
    for v in range(1, V + 1):
        m = nxt[v]
        start = next(iter(m))
        out = [start]
        while True:
            u = m[out[-1]]
            if u == start:
                break
            out.append(u)
        cyc[v] = out
    return cyc


def caps_of(P, cyc, deg):
    out = []
    for v, ring in cyc.items():
        if len(ring) != deg:
            continue
        R = np.array([P[u - 1] for u in ring])
        c = R.mean(axis=0)
        Q = R - c
        if np.linalg.svd(Q, compute_uv=False)[2] > TOL:
            continue
        ok = True
        if deg == 4:
            for i in range(2):
                if abs(np.linalg.norm(R[i] - R[i + 2]) - math.sqrt(2)) > TOL:
                    ok = False
        else:
            for i in range(5):
                if abs(np.linalg.norm(R[i] - R[(i + 2) % 5]) - PHI) > TOL:
                    ok = False
        if ok:
            out.append((v, ring))
    return out


def decap_convex(P, faces, caps):
    apexes = {v for v, _ in caps}
    polys = []
    for a, b, c in faces:
        if a in apexes or b in apexes or c in apexes:
            continue
        polys.append((a, b, c))
    for v, ring in caps:
        polys.append(tuple(ring))
    def normal(poly):
        pts = np.array([P[u - 1] for u in poly])
        c = pts.mean(axis=0)
        n = np.zeros(3)
        for i in range(len(poly)):
            n += np.cross(pts[i] - c, pts[(i + 1) % len(poly)] - c)
        return n / max(np.linalg.norm(n), 1e-30)
    edge_faces = {}
    for pi, poly in enumerate(polys):
        for i in range(len(poly)):
            e = tuple(sorted((poly[i], poly[(i + 1) % len(poly)])))
            edge_faces.setdefault(e, []).append(pi)
    normals = [normal(p) for p in polys]
    for e, fl in edge_faces.items():
        if len(fl) != 2:
            return False
        n1, n2 = normals[fl[0]], normals[fl[1]]
        bend = math.acos(float(np.clip(np.dot(n1, n2), -1, 1)))
        p1 = np.array([P[u2 - 1] for u2 in polys[fl[0]]]).mean(axis=0)
        p2 = np.array([P[u2 - 1] for u2 in polys[fl[1]]]).mean(axis=0)
        if np.dot(n1, p2 - p1) > 1e-9 and bend > 1e-6:
            return False
    return True


def one(arg):
    v, fname = arg
    name = fname[:-4]
    faces = [tuple(f) for f in decode(name)]
    V = max(max(f) for f in faces)
    P = []
    for ln in open(os.path.join(OBJS, f"v{v}", fname)):
        if ln.startswith("v "):
            P.append([float(x) for x in ln.split()[1:4]])
    P = np.array(P)
    cyc = links(V, faces)
    caps = caps_of(P, cyc, 4) + caps_of(P, cyc, 5)
    if not caps:
        return None
    apexes = {c[0] for c in caps}
    ringv = set()
    for _, ring in caps:
        ringv |= set(ring)
    if apexes & ringv:
        return f"{name}\t{V}\t{len(caps)}\t-\tCONFLICT"
    nsq = sum(1 for _, r in caps if len(r) == 4)
    npt = sum(1 for _, r in caps if len(r) == 5)
    ok = decap_convex(P, faces, caps)
    return f"{name}\t{V}\t{nsq}\t{npt}\t{'CONVEX' if ok else 'no'}"


def main():
    jobs = []
    for v in range(4, 31):
        d = os.path.join(OBJS, f"v{v}")
        if os.path.isdir(d):
            for fname in sorted(os.listdir(d)):
                if fname.endswith(".obj"):
                    jobs.append((v, fname))
    print(f"{len(jobs)} nets", flush=True)
    out = os.path.join(TOP, "data", "decap_v30.tsv")
    n = 0
    with Pool(6) as pool, open(out, "w") as f:
        f.write("name\tv\tnsq\tnpent\tverdict\n")
        for i, row in enumerate(pool.imap_unordered(one, jobs, chunksize=200)):
            if row:
                f.write(row + "\n")
                n += 1
            if i % 20000 == 0:
                print(i, flush=True)
    print(f"done: {n} nets with exact caps", flush=True)


if __name__ == "__main__":
    main()
