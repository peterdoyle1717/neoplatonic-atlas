#!/usr/bin/env python3
"""Sweep all prime nets v <= 30: solve (euclid_lm_mp --prove, emitted
high-precision halfturn bends -- never coordinate recovery), match every
bend against the construction-angle library of notes/bend_recognize.py
(|b| within 1e-7; signed values recorded), and flag nets whose bends
are ALL recognized, plus which carry the icosahedral atom I.

Output: data/recognized_v30.tsv
  name  v  all_recognized  n_ico  profile
profile = comma list of library names with signs (- prefix = reflex).
"""
import math, os, subprocess, sys, importlib.util
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
NEO = os.path.dirname(TOP)
BIN = os.path.join(NEO, "bendprover", "csrc", "euclid_lm_mp")

# build the LIB exactly as bend_recognize.py does (import its module
# namespace without running its __main__ CLI tail)
import types
src = open(os.path.join(NEO, "notes", "bend_recognize.py")).read()
src = src.split("libvals=sorted(LIB.items())")[0]
mod = types.ModuleType("brlib")
mod.__dict__["sys"] = sys
sys.argv_backup = sys.argv
sys.argv = ["x", "m", "d"]
exec(src, mod.__dict__)
sys.argv = sys.argv_backup
LIB = mod.LIB
LIBV = sorted(LIB.items())
TOL = 1e-7
ICO = round(math.pi - math.acos(-math.sqrt(5) / 3), 7)

spec = importlib.util.spec_from_file_location(
    "clers", os.path.join(NEO, "clers", "src", "clers.py"))
clers_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clers_mod)
decode = clers_mod.decode


def lookup(v):
    k = round(v, 7)
    if k in LIB:
        return LIB[k]
    import bisect
    i = bisect.bisect_left(LIBV, (k,))
    for j in (i - 1, i, i + 1):
        if 0 <= j < len(LIBV) and abs(LIBV[j][0] - k) <= TOL:
            return LIBV[j][1]
    return None


def one(nm):
    faces = decode(nm)
    V = max(max(f) for f in faces)
    nc = ';'.join(','.join(str(x) for x in f) for f in faces)
    try:
        r = subprocess.run([BIN, "--prove", "--alpha", "60.0", "--name", "X", nc],
                           capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return f"{nm}\t{V}\tERR\t0\ttimeout"
    if "end" not in r.stdout:
        return f"{nm}\t{V}\tERR\t0\tsolvefail"
    prof, allrec, nico = [], True, 0
    for ln in r.stdout.splitlines():
        t = ln.split()
        if t and t[0] == "b":
            b = float(t[3]) * math.pi          # radians, signed
            nmv = lookup(abs(b))
            if nmv is None:
                allrec = False
                break
            if round(abs(b), 7) == ICO or abs(abs(b) - ICO) <= TOL:
                nico += 1
            prof.append(('-' if b < 0 else '') + nmv)
    return (f"{nm}\t{V}\t{int(allrec)}\t{nico if allrec else 0}"
            f"\t{','.join(prof) if allrec else ''}")


def main():
    names = []
    for v in range(4, 31):
        p = os.path.join(NEO, "data", "primes", f"{v}.txt")
        if os.path.exists(p):
            names += [ln.strip() for ln in open(p) if ln.strip()]
    print(f"{len(names)} nets", flush=True)
    out = os.path.join(TOP, "data", "recognized_v30.tsv")
    with Pool(6) as pool, open(out, "w") as f:
        f.write("name\tv\tall_recognized\tn_ico\tprofile\n")
        for i, row in enumerate(pool.imap_unordered(one, names, chunksize=50)):
            f.write(row + "\n")
            if i % 5000 == 0:
                print(i, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
