#!/usr/bin/env python3
"""Classify every prime net v <= 30 from the doob-generated OBJ
coordinates (neo/data/objs/v*/<CLERS>.obj) -- no solving.

Per net: decode the CLERS name to faces, read the OBJ vertices,
sanity-check unit edges, then flag pancake (flat), convex
(min bend >= -1e-4), strictly convex (min bend > 1e-4), buried
vertices (hull depth > 1e-3), and floppy (membership in the
322-flopper census list, euclid_hp/explore/floppers.txt).

Output: data/class_v30.tsv
  name  v  pancake  convex  strict  nburied  depth  floppy  edgeerr
where name = v{V}{CLERS}.
"""
import math, os, sys, importlib.util
from multiprocessing import Pool
import numpy as np
from scipy.spatial import ConvexHull

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
NEO = os.path.dirname(TOP)
OBJS = os.path.join(NEO, "data", "objs")
FLOPPERS = os.path.join(NEO, "euclid_hp", "explore", "floppers.txt")
sys.path.insert(0, HERE)
from walklib import bends_from_coords

spec = importlib.util.spec_from_file_location(
    "clers", os.path.join(NEO, "clers", "src", "clers.py"))
clers_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clers_mod)
decode = clers_mod.decode

flopset = set()
if os.path.exists(FLOPPERS):
    flopset = {ln.strip() for ln in open(FLOPPERS) if ln.strip()}


def classify(args):
    v, fname = args
    name = fname[:-4]
    path = os.path.join(OBJS, f"v{v}", fname)
    faces = [tuple(f) for f in decode(name)]
    V = max(max(f) for f in faces)
    coords = []
    for ln in open(path):
        if ln.startswith("v "):
            coords.append([float(x) for x in ln.split()[1:4]])
    if len(coords) != V:
        return f"v{V}{name}\t{V}\tERR\tvertex-count"
    P = np.array(coords)
    apex = {}
    for a, b, c in faces:
        apex[(a, b)] = c; apex[(b, c)] = a; apex[(c, a)] = b
    pos = {i + 1: P[i] for i in range(V)}
    # unit-edge sanity (also catches OBJ-vs-decode numbering mismatch)
    edgeerr = 0.0
    for (a, b) in apex:
        if a < b:
            edgeerr = max(edgeerr, abs(float(np.linalg.norm(P[a-1] - P[b-1])) - 1.0))
    Q = P - P.mean(axis=0)
    sv = np.linalg.svd(Q, compute_uv=False)
    # relative flatness: OBJ coords carry ~1e-6 noise (10-decimal ASCII),
    # measured sigma_3 for known pancakes is 2e-6..4e-6
    pancake = bool(sv[2] < 1e-5 * sv[0])
    if pancake:
        convex = strict = False
        nburied, depth = 0, 0.0
    else:
        bends = bends_from_coords(faces, pos, apex)
        bmin = min(bends.values())
        convex = bool(bmin >= -1e-4)
        strict = bool(bmin > 1e-4)
        hull = ConvexHull(P)
        A = hull.equations[:, :3]
        b = hull.equations[:, 3]
        depths = -(P @ A.T + b[None, :]).max(axis=1)
        buried = depths[depths > 1e-3]
        nburied, depth = len(buried), (float(buried.max()) if len(buried) else 0.0)
    return (f"v{V}{name}\t{V}\t{int(pancake)}\t{int(convex)}\t{int(strict)}"
            f"\t{nburied}\t{depth:.4f}\t{int(name in flopset)}\t{edgeerr:.2e}")


def main():
    jobs = []
    for v in range(4, 31):
        d = os.path.join(OBJS, f"v{v}")
        if not os.path.isdir(d):
            continue
        for fname in sorted(os.listdir(d)):
            if fname.endswith(".obj"):
                jobs.append((v, fname))
    print(f"{len(jobs)} nets", flush=True)
    out = os.path.join(TOP, "data", "class_v30.tsv")
    with Pool(6) as pool, open(out, "w") as f:
        f.write("name\tv\tpancake\tconvex\tstrict\tnburied\tdepth\tfloppy\tedgeerr\n")
        for i, row in enumerate(pool.imap_unordered(classify, jobs, chunksize=200)):
            f.write(row + "\n")
            if i % 10000 == 0:
                print(i, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
