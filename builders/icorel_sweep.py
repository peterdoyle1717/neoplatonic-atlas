#!/usr/bin/env python3
"""Sweep all primes v<=30: solver-emitted bends matched against the
seven icosahedral-relative dihedral values (bends = pi - dihedral;
dihedrals measured from Antiprism models via off_report, 2026-07-14:
dodeca 116.56505117707799, ico 138.18968510422141, icosidodeca
142.62263185935029, rhombicosidodeca 148.28252558853902 +
159.09484255211072, snub 152.92992027583506 + 164.17536605603391 deg).
Also per net: min/max bend, and wish-starter quality (min/max of the
wish vs solved, sup and l2 distance).
Output: data/icorel_v30.tsv."""
import math, os, subprocess, sys, importlib.util
from multiprocessing import Pool
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
NEO = os.path.dirname(TOP)
BIN = os.path.join(NEO, "bendprover", "csrc", "euclid_lm_mp")

DIHED = {"dod": 116.56505117707799, "ico": 138.18968510422141,
         "idd": 142.62263185935029, "rid1": 148.28252558853902,
         "rid2": 159.09484255211072, "snub1": 152.92992027583506,
         "snub2": 164.17536605603391}
RELB = {k: math.pi - math.radians(d) for k, d in DIHED.items()}
TOL = 1e-7

spec = importlib.util.spec_from_file_location(
    "clers", os.path.join(NEO, "clers", "src", "clers.py"))
clers_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clers_mod)
decode = clers_mod.decode


def one(nm):
    faces = decode(nm)
    V = max(max(f) for f in faces)
    nc = ';'.join(','.join(str(x) for x in f) for f in faces)
    edges = sorted({(min(a, b), max(a, b)) for f in faces
                    for a, b in zip(f, f[1:] + f[:1])})
    try:
        r = subprocess.run([BIN, "--prove", "--alpha", "60.0", "--name", "X", nc],
                           capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return f"{nm}\t{V}\tERR"
    if "end" not in r.stdout:
        return f"{nm}\t{V}\tERR"
    bd = {}
    for ln in r.stdout.splitlines():
        t = ln.split()
        if t and t[0] == "b":
            bd[(int(t[1]), int(t[2]))] = float(t[3]) * math.pi
    b = np.array([bd.get(e, bd.get(e[::-1])) for e in edges])
    hits = []
    for k, val in RELB.items():
        n = int(np.sum(np.abs(np.abs(b) - val) <= TOL))
        if n:
            hits.append(f"{k}:{n}")
    A = np.zeros((V, len(edges)))
    for i, (p, q) in enumerate(edges):
        A[p-1, i] = A[q-1, i] = 1
    wish = np.linalg.lstsq(A, np.full(V, 2*math.pi), rcond=None)[0]
    return (f"{nm}\t{V}\t{','.join(hits)}\t{b.min():.8f}\t{b.max():.8f}"
            f"\t{wish.min():.6f}\t{wish.max():.6f}"
            f"\t{np.abs(wish-b).max():.6f}\t{np.linalg.norm(wish-b):.6f}")


def main():
    names = []
    for v in range(4, 31):
        p = os.path.join(NEO, "data", "primes", f"{v}.txt")
        if os.path.exists(p):
            names += [ln.strip() for ln in open(p) if ln.strip()]
    print(f"{len(names)} nets", flush=True)
    out = os.path.join(TOP, "data", "icorel_v30.tsv")
    with Pool(6) as pool, open(out, "w") as f:
        f.write("name\tv\trelhits\tminb\tmaxb\twishmin\twishmax\twishdinf\twishd2\n")
        for i, row in enumerate(pool.imap_unordered(one, names, chunksize=50)):
            f.write(row + "\n")
            if i % 10000 == 0:
                print(i, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
