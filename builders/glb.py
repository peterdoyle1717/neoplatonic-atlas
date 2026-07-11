#!/usr/bin/env python3
import sys, pathlib, re, argparse, math, struct, base64
import pygltflib as pg

def parse_obj(path):
    verts = []
    faces = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s.startswith("v "):
                parts = s.split()
                if len(parts) >= 4:
                    try:
                        verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
                    except ValueError:
                        pass
            elif s.startswith("f "):
                parts = s.split()[1:]
                idx = []
                for p in parts:
                    m = re.match(r"^(\d+)", p)
                    if m:
                        idx.append(int(m.group(1)) - 1)
                if len(idx) >= 3:
                    faces.append(tuple(idx[:3]))
    lastpos = {}
    for i, tri in enumerate(faces):
        key = tuple(sorted(tri))
        lastpos[key] = i
    keep = sorted(lastpos.values())
    faces = [faces[i] for i in keep]
    return verts, faces

def dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)

def incenter(p, q, r):
    a = dist(q, r)
    b = dist(r, p)
    c = dist(p, q)
    s = a + b + c
    if s == 0:
        return p
    return (
        (a*p[0] + b*q[0] + c*r[0]) / s,
        (a*p[1] + b*q[1] + c*r[1]) / s,
        (a*p[2] + b*q[2] + c*r[2]) / s
    )

def retreat_to_incenter(verts, faces, edge):
    newverts = []
    newfaces = []
    mats = []
    for tri in faces:
        p, q, r = verts[tri[0]], verts[tri[1]], verts[tri[2]]
        c = incenter(p, q, r)
        p2 = (edge*p[0] + (1-edge)*c[0], edge*p[1] + (1-edge)*c[1], edge*p[2] + (1-edge)*c[2])
        q2 = (edge*q[0] + (1-edge)*c[0], edge*q[1] + (1-edge)*c[1], edge*q[2] + (1-edge)*c[2])
        r2 = (edge*r[0] + (1-edge)*c[0], edge*r[1] + (1-edge)*c[1], edge*r[2] + (1-edge)*c[2])

        i0 = len(newverts)
        newverts.extend([p, q, r, p2, q2, r2])

        newfaces.extend([
            (i0, i0+1, i0+4),
            (i0, i0+4, i0+3),
            (i0+1, i0+2, i0+5),
            (i0+1, i0+5, i0+4),
            (i0+2, i0, i0+3),
            (i0+2, i0+3, i0+5),
            (i0+3, i0+4, i0+5)
        ])
        mats.extend([
            "border","border",
            "border","border",
            "border","border",
            "center"
        ])
    return newverts, newfaces, mats

def pad4(b):
    return b + b"\x00" * ((4 - (len(b) % 4)) % 4)

def axis_to_yup(verts):
    return [(x, z, -y) for (x, y, z) in verts]

def make_material(base, metallic, roughness):
    return pg.Material(
        pbrMetallicRoughness=pg.PbrMetallicRoughness(
            baseColorFactor=base + [1.0],
            metallicFactor=metallic,
            roughnessFactor=roughness
        ),
        doubleSided=False
    )

def write_gltf_like(outpath, verts, faces, mats=None, embedded=True,
                    solid_color=None, border_color=None, center_color=None,
                    meshname=None):
    nverts = len(verts)
    all_faces = faces

    if mats is None or len(set(mats)) == 1:
        center_faces = all_faces
        border_faces = []
    else:
        border_faces = [f for f, m in zip(all_faces, mats) if m == "border"]
        center_faces = [f for f, m in zip(all_faces, mats) if m == "center"]

    center_indices = [i for tri in center_faces for i in tri]
    border_indices = [i for tri in border_faces for i in tri]

    use32 = nverts > 65535
    idx_comp = pg.UNSIGNED_INT if use32 else pg.UNSIGNED_SHORT

    def pack_indices(idxs):
        if not idxs:
            return b""
        fmt = "<" + ("I" if use32 else "H") * len(idxs)
        return struct.pack(fmt, *idxs)

    blobs = []
    bufferViews = []
    accessors = []
    offset = 0

    def add_index_stream(idxs):
        nonlocal offset
        raw = pack_indices(idxs)
        padded = pad4(raw)
        view_index = len(bufferViews)
        bufferViews.append(pg.BufferView(
            buffer=0,
            byteOffset=offset,
            byteLength=len(raw),
            target=pg.ELEMENT_ARRAY_BUFFER
        ))
        accessor_index = len(accessors)
        accessors.append(pg.Accessor(
            bufferView=view_index,
            byteOffset=0,
            componentType=idx_comp,
            count=len(idxs),
            type=pg.SCALAR,
            max=[max(idxs)] if idxs else [0],
            min=[min(idxs)] if idxs else [0]
        ))
        blobs.append(padded)
        offset += len(padded)
        return accessor_index

    center_accessor = add_index_stream(center_indices)
    border_accessor = add_index_stream(border_indices) if border_indices else None

    # Center vertices at origin for proper orbit pivot in viewers
    cx = sum(v[0] for v in verts) / len(verts)
    cy = sum(v[1] for v in verts) / len(verts)
    cz = sum(v[2] for v in verts) / len(verts)
    verts = [(v[0]-cx, v[1]-cy, v[2]-cz) for v in verts]
    pos_flat = [c for v in verts for c in v]
    pos_raw = struct.pack("<" + "f" * len(pos_flat), *pos_flat)
    pos_padded = pad4(pos_raw)
    pos_view = len(bufferViews)
    bufferViews.append(pg.BufferView(
        buffer=0,
        byteOffset=offset,
        byteLength=len(pos_raw),
        target=pg.ARRAY_BUFFER
    ))
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    pos_accessor = len(accessors)
    accessors.append(pg.Accessor(
        bufferView=pos_view,
        byteOffset=0,
        componentType=pg.FLOAT,
        count=nverts,
        type=pg.VEC3,
        max=[max(xs), max(ys), max(zs)],
        min=[min(xs), min(ys), min(zs)]
    ))
    blobs.append(pos_padded)
    offset += len(pos_padded)

    binary_blob = b"".join(blobs)

    gltf = pg.GLTF2()
    gltf.asset = pg.Asset(version="2.0")

    gltf.buffers = [pg.Buffer(byteLength=len(binary_blob))]
    gltf.bufferViews = bufferViews
    gltf.accessors = accessors

    c_color = solid_color or center_color or [1.0, 0.0, 0.0]
    b_color = border_color or [0.0, 0.0, 0.0]
    materials = [make_material(c_color, 1.0, 0.45)]
    if border_faces:
        materials.append(make_material(b_color, 1.0, 0.35))
    gltf.materials = materials

    primitives = []
    prim_center = pg.Primitive()
    prim_center.attributes.POSITION = pos_accessor
    prim_center.indices = center_accessor
    prim_center.material = 0
    primitives.append(prim_center)

    if border_faces:
        prim_border = pg.Primitive()
        prim_border.attributes.POSITION = pos_accessor
        prim_border.indices = border_accessor
        prim_border.material = 1
        primitives.append(prim_border)

    gltf.meshes = [pg.Mesh(name=meshname, primitives=primitives)]
    gltf.nodes = [pg.Node(name=meshname, mesh=0)]
    gltf.scenes = [pg.Scene(name=meshname, nodes=[0])]
    gltf.scene = 0

    gltf.set_binary_blob(binary_blob)

    if embedded:
        gltf.convert_buffers(pg.BufferFormat.DATAURI)
        gltf.save(str(outpath))
    else:
        gltf.save_binary(str(outpath))

def main(argv):
    ap = argparse.ArgumentParser(prog="obj2gltf")
    ap.add_argument("objs", nargs="+")
    ap.add_argument("--edge", type=float, default=0.9)
    ap.add_argument("--format", choices=["glb", "gltf"], default="glb")
    ap.add_argument("--yup", action="store_true")
    args = ap.parse_args(argv[1:])

    outdir = pathlib.Path("glb")
    outdir.mkdir(parents=True, exist_ok=True)

    for obj in args.objs:
        p = pathlib.Path(obj)
        verts, faces = parse_obj(p)
        if not verts or not faces:
            continue

        mats = None
        if args.edge != 1.0:
            verts, faces, mats = retreat_to_incenter(verts, faces, args.edge)

        if args.yup:
            verts = axis_to_yup(verts)

        if args.format == "gltf":
            outpath = outdir / (p.stem + ".gltf")
            write_gltf_like(outpath, verts, faces, mats=mats, embedded=True)
        else:
            outpath = outdir / (p.stem + ".glb")
            write_gltf_like(outpath, verts, faces, mats=mats, embedded=False)

    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


def write_gltf_groups(outpath, verts, groups, embedded=True, meshname=None):
    """Like write_gltf_like but with one primitive per color group.
    groups: list of (rgb_triple, list_of_faces)."""
    nverts = len(verts)
    use32 = nverts > 65535
    idx_comp = pg.UNSIGNED_INT if use32 else pg.UNSIGNED_SHORT

    def pack_indices(idxs):
        if not idxs:
            return b""
        fmt = "<" + ("I" if use32 else "H") * len(idxs)
        return struct.pack(fmt, *idxs)

    blobs = []
    bufferViews = []
    accessors = []
    offset = 0

    def add_index_stream(idxs):
        nonlocal offset
        raw = pack_indices(idxs)
        padded = pad4(raw)
        view_index = len(bufferViews)
        bufferViews.append(pg.BufferView(
            buffer=0, byteOffset=offset, byteLength=len(raw),
            target=pg.ELEMENT_ARRAY_BUFFER))
        accessor_index = len(accessors)
        accessors.append(pg.Accessor(
            bufferView=view_index, byteOffset=0, componentType=idx_comp,
            count=len(idxs), type=pg.SCALAR,
            max=[max(idxs)] if idxs else [0],
            min=[min(idxs)] if idxs else [0]))
        blobs.append(padded)
        offset += len(padded)
        return accessor_index

    group_accessors = []
    for _, gfaces in groups:
        idxs = [i for tri in gfaces for i in tri]
        group_accessors.append(add_index_stream(idxs) if idxs else None)

    cx = sum(v[0] for v in verts) / len(verts)
    cy = sum(v[1] for v in verts) / len(verts)
    cz = sum(v[2] for v in verts) / len(verts)
    verts = [(v[0]-cx, v[1]-cy, v[2]-cz) for v in verts]
    pos_flat = [c for v in verts for c in v]
    pos_raw = struct.pack("<" + "f" * len(pos_flat), *pos_flat)
    pos_padded = pad4(pos_raw)
    pos_view = len(bufferViews)
    bufferViews.append(pg.BufferView(
        buffer=0, byteOffset=offset, byteLength=len(pos_raw),
        target=pg.ARRAY_BUFFER))
    xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
    pos_accessor = len(accessors)
    accessors.append(pg.Accessor(
        bufferView=pos_view, byteOffset=0, componentType=pg.FLOAT,
        count=nverts, type=pg.VEC3,
        max=[max(xs), max(ys), max(zs)], min=[min(xs), min(ys), min(zs)]))
    blobs.append(pos_padded)
    offset += len(pos_padded)

    binary_blob = b"".join(blobs)
    gltf = pg.GLTF2()
    gltf.asset = pg.Asset(version="2.0")
    gltf.buffers = [pg.Buffer(byteLength=len(binary_blob))]
    gltf.bufferViews = bufferViews
    gltf.accessors = accessors
    gltf.materials = [make_material(list(color), 1.0, 0.45) for color, _ in groups]

    primitives = []
    for m, acc in enumerate(group_accessors):
        if acc is None:
            continue
        prim = pg.Primitive()
        prim.attributes.POSITION = pos_accessor
        prim.indices = acc
        prim.material = m
        primitives.append(prim)
    gltf.meshes = [pg.Mesh(name=meshname, primitives=primitives)]
    gltf.nodes = [pg.Node(name=meshname, mesh=0)]
    gltf.scenes = [pg.Scene(name=meshname, nodes=[0])]
    gltf.scene = 0
    gltf.set_binary_blob(binary_blob)
    if embedded:
        gltf.convert_buffers(pg.BufferFormat.DATAURI)
        gltf.save(str(outpath))
    else:
        gltf.save_binary(str(outpath))
