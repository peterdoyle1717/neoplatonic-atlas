#!/usr/bin/env python3
"""Derive smooth.glb from each net's rb.glb: weld the retreat-piece
vertices back together, drop the black border material, emit a single
indexed primitive with NO normals -- the viewer then computes smooth
per-vertex normals (the conemanifold look). Idempotent; skips nets
that already have smooth.glb. Rerun any time."""
import os, struct, sys
import pygltflib as pg
from glb import write_gltf_like

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
NETS = os.path.join(TOP, "site", "personal", "nets")


def read_rb(path):
    g = pg.GLTF2().load(path)
    blob = g.binary_blob()
    if blob is None:  # data-URI buffers
        g.convert_buffers(pg.BufferFormat.BINARYBLOB)
        blob = g.binary_blob()

    def acc_data(ai, fmt, per):
        a = g.accessors[ai]
        bv = g.bufferViews[a.bufferView]
        off = (bv.byteOffset or 0) + (a.byteOffset or 0)
        n = a.count * per
        return struct.unpack_from("<" + fmt * n, blob, off)

    mesh = g.meshes[0]
    verts = None
    tris = []
    color = [1.0, 0.0, 0.0]
    for prim in mesh.primitives:
        pos = acc_data(prim.attributes.POSITION, "f", 3)
        if verts is None:
            verts = [(pos[i], pos[i + 1], pos[i + 2])
                     for i in range(0, len(pos), 3)]
        a = g.accessors[prim.indices]
        fmt = "I" if a.componentType == pg.UNSIGNED_INT else "H"
        idx = acc_data(prim.indices, fmt, 1)
        tris += [(idx[i], idx[i + 1], idx[i + 2])
                 for i in range(0, len(idx), 3)]
        if prim.material == 0 and g.materials:
            c = g.materials[0].pbrMetallicRoughness.baseColorFactor
            if c:
                color = list(c[:3])
    return verts, tris, color


def weld(verts, tris):
    key2new, remap, out = {}, [], []
    for x, y, z in verts:
        k = (round(x, 6), round(y, 6), round(z, 6))
        i = key2new.get(k)
        if i is None:
            i = len(out)
            key2new[k] = i
            out.append((x, y, z))
        remap.append(i)
    faces = []
    for a, b, c in tris:
        f = (remap[a], remap[b], remap[c])
        if len({*f}) == 3:
            faces.append(f)
    return out, faces


def convert(netdir):
    src = os.path.join(netdir, "rb.glb")
    dst = os.path.join(netdir, "smooth.glb")
    if not os.path.exists(src) or os.path.exists(dst):
        return False
    verts, tris, color = read_rb(src)
    w, f = weld(verts, tris)
    write_gltf_like(dst, w, f, solid_color=color)
    return True


if __name__ == "__main__":
    n = done = 0
    for d in sorted(os.listdir(NETS)):
        netdir = os.path.join(NETS, d)
        if not os.path.isdir(netdir):
            continue
        n += 1
        try:
            if convert(netdir):
                done += 1
        except Exception as e:
            print(f"{d}: FAILED {e}", file=sys.stderr)
    print(f"smooth.glb: {done} written ({n} net dirs)")
