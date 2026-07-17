#!/usr/bin/env python3
"""Generate Eisenstein-subdivision rows via Antiprism's geodesic.

usage: gen_ray.py BASE a,b [a,b ...]

BASE is an Antiprism builtin (tet, oct, ico, ...) or a path to an
.obj/.off model of the base net (any realization works: the planar
method's combinatorics don't depend on the coordinates). Prints
subdiv_base/subdiv_extra rows (label T a b base V CLERS) on stdout;
the label's base field is the builtin name or the file's basename.
Faces are canonicalized by clers name.
"""
import os, subprocess, sys

GEO = os.path.expanduser("~/local/bin/geodesic")
HERE = os.path.dirname(os.path.abspath(__file__))
CLERS = os.path.join(HERE, "..", "..", "clers", "clers")


def faces_from_off(txt):
    lines = [ln.split('#')[0].strip() for ln in txt.splitlines()]
    lines = [ln for ln in lines if ln]
    assert lines[0] == "OFF", "not an OFF file"
    nv, nf, _ = (int(x) for x in lines[1].split())
    faces = []
    for ln in lines[2 + nv:2 + nv + nf]:
        t = ln.split()
        if int(t[0]) == 3:  # skip Antiprism's 1/2-vertex color elements
            faces.append(tuple(int(x) + 1 for x in t[1:4]))
    assert len(faces) == 2 * nv - 4, f"face count {len(faces)} != 2V-4"
    return nv, faces


def obj_to_off(path):
    verts, faces = [], []
    for ln in open(path):
        t = ln.split()
        if t and t[0] == "v":
            verts.append(tuple(float(x) for x in t[1:4]))
        elif t and t[0] == "f":
            faces.append(tuple(int(p.split("/")[0]) - 1 for p in t[1:4]))
    out = [f"OFF\n{len(verts)} {len(faces)} 0"]
    out += [f"{x} {y} {z}" for x, y, z in verts]
    out += ["3 " + " ".join(str(i) for i in f) for f in faces]
    return "\n".join(out) + "\n"


def gen(base, a, b):
    T = a * a + a * b + b * b
    if base.endswith(".obj"):
        off = subprocess.run([GEO, "-c", f"{a},{b}", "-M", "p"],
                             input=obj_to_off(base),
                             capture_output=True, text=True, check=True).stdout
    else:
        off = subprocess.run([GEO, "-c", f"{a},{b}", "-M", "p", base],
                             capture_output=True, text=True, check=True).stdout
    nv, faces = faces_from_off(off)
    line = ';'.join(f"{x},{y},{z}" for x, y, z in faces)
    nm = subprocess.run([CLERS, "name"], input=line + "\n",
                        capture_output=True, text=True, check=True).stdout.strip()
    assert nm, "clers name returned nothing"
    return T, nv, nm


if __name__ == "__main__":
    base = sys.argv[1]
    label = os.path.splitext(os.path.basename(base))[0]
    for ab in sys.argv[2:]:
        a, b = (int(x) for x in ab.split(','))
        T, nv, nm = gen(base, a, b)
        print(f"{label}_T{T}_{a}_{b}\t{T}\t{a}\t{b}\t{label}\t{nv}\t{nm}")
