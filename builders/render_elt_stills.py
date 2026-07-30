#!/usr/bin/env python3
"""Render publication-style PNG stills from the selected rb.glb models."""

import argparse
import json
import math
import struct
import zlib
from pathlib import Path

import numpy as np

from elt_paper import selection


SIZE = 400
SUPERSAMPLE = 3
OCCUPANCY = 0.72
ORBITS = {
    # Tuned against Peter's 4-by-5 reference screenshot.
    "v4CCAE": (315, 80),
    "v5CCACAE": (330, 40),
    "v6CCACACAE": (195, 60),
    "v6CCCACAAE": (105, 60),
    "v7CCACACACAE": (315, 120),
    "v7CCACACCABE": (210, 60),
    "v7CCACCACAAE": (270, 80),
    "v7CCCACACAAE": (150, 120),
    "v8CCACCCABCABE": (75, 50),
    "v8CCCACACACAAE": (300, 70),
    "v8CCCACACCAABE": (300, 120),
    "v9CCCACAACCACAAE": (330, 140),
    "v9CCCACCACACAAAE": (30, 100),
    "v10CCACCCACCACABDEE": (180, 140),
    "v10CCCACACACCAACAAE": (135, 100),
    "v10CCCACCACACAACAAE": (15, 120),
    "v12CCCCACCACACACAACAAAE": (330, 110),
    "v14CCCCACCACACACACACAACAAAE": (0, 30),
    "v452hdf751e9c22065e97": (0, 100),
    "v443h91956484cfa84d32": (0, 100),
}
COMPONENTS = {
    5121: np.uint8,
    5123: np.uint16,
    5125: np.uint32,
    5126: np.float32,
}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def load_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", data)
    assert magic == b"glTF" and version == 2 and length == len(data)
    offset = 12
    doc = binary = None
    while offset < length:
        size, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset:offset + size]
        offset += size
        if kind == 0x4E4F534A:
            doc = json.loads(chunk.decode().rstrip("\x00 "))
        elif kind == 0x004E4942:
            binary = chunk
    assert doc is not None and binary is not None
    return doc, binary


def accessor(doc, binary, index):
    spec = doc["accessors"][index]
    view = doc["bufferViews"][spec["bufferView"]]
    dtype = np.dtype(COMPONENTS[spec["componentType"]]).newbyteorder("<")
    width = WIDTH[spec["type"]]
    count = spec["count"]
    itemsize = dtype.itemsize * width
    stride = view.get("byteStride", itemsize)
    offset = view.get("byteOffset", 0) + spec.get("byteOffset", 0)
    if stride == itemsize:
        values = np.frombuffer(
            binary, dtype=dtype, count=count * width, offset=offset
        )
        return values.reshape(count, width)
    return np.ndarray(
        (count, width),
        dtype=dtype,
        buffer=binary,
        offset=offset,
        strides=(stride, dtype.itemsize),
    ).copy()


def geometry(path):
    doc, binary = load_glb(path)
    primitives = doc["meshes"][0]["primitives"]
    assert len(primitives) == 2
    assert [p["material"] for p in primitives] == [0, 1]
    position_index = primitives[0]["attributes"]["POSITION"]
    assert all(p["attributes"]["POSITION"] == position_index for p in primitives)
    points = accessor(doc, binary, position_index).astype(np.float64)
    triangles = [
        accessor(doc, binary, p["indices"]).reshape(-1, 3).astype(np.int64)
        for p in primitives
    ]
    assert np.isfinite(points).all()
    assert all((0 <= t).all() and (t < len(points)).all() for t in triangles)
    return points, triangles


def camera_projection(points, theta_degrees, phi_degrees):
    theta = math.radians(theta_degrees)
    phi = math.radians(phi_degrees)
    direction = np.array([
        math.sin(phi) * math.sin(theta),
        math.cos(phi),
        -math.sin(phi) * math.cos(theta),
    ])
    world_up = np.array([0.0, 1.0, 0.0])
    right = np.cross(world_up, direction)
    right /= np.linalg.norm(right)
    up = np.cross(direction, right)
    q = points - points.mean(axis=0)
    projected = np.column_stack((q @ right, q @ up, q @ direction))
    span_x = np.ptp(projected[:, 0])
    span_y = np.ptp(projected[:, 1])
    span = max(span_x, span_y)
    assert span > 0
    canvas = SIZE * SUPERSAMPLE
    scale = OCCUPANCY * canvas / span
    midpoint = (
        (projected[:, :2].min(axis=0) + projected[:, :2].max(axis=0)) / 2
    )
    screen = np.empty_like(projected)
    screen[:, 0] = (projected[:, 0] - midpoint[0]) * scale + (canvas - 1) / 2
    screen[:, 1] = -(projected[:, 1] - midpoint[1]) * scale + (canvas - 1) / 2
    screen[:, 2] = projected[:, 2]
    return screen, direction


def draw_triangle(image, depth, screen, world, tri, color):
    p = screen[tri]
    w = world[tri]
    normal = np.cross(w[1] - w[0], w[2] - w[0])
    norm = np.linalg.norm(normal)
    if norm == 0:
        return
    normal /= norm
    xmin = max(0, int(math.floor(p[:, 0].min())))
    xmax = min(image.shape[1] - 1, int(math.ceil(p[:, 0].max())))
    ymin = max(0, int(math.floor(p[:, 1].min())))
    ymax = min(image.shape[0] - 1, int(math.ceil(p[:, 1].max())))
    if xmin > xmax or ymin > ymax:
        return
    x0, y0 = p[0, :2]
    x1, y1 = p[1, :2]
    x2, y2 = p[2, :2]
    denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(denominator) < 1e-12:
        return
    yy, xx = np.mgrid[ymin:ymax + 1, xmin:xmax + 1]
    a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / denominator
    b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / denominator
    c = 1 - a - b
    inside = (a >= -1e-9) & (b >= -1e-9) & (c >= -1e-9)
    z = a * p[0, 2] + b * p[1, 2] + c * p[2, 2]
    old = depth[ymin:ymax + 1, xmin:xmax + 1]
    update = inside & (z > old)
    if not np.any(update):
        return
    old[update] = z[update]
    block = image[ymin:ymax + 1, xmin:xmax + 1]
    block[update] = color


def render(path, theta_degrees=0, phi_degrees=100):
    points, primitives = geometry(path)
    screen, camera = camera_projection(points, theta_degrees, phi_degrees)
    canvas = SIZE * SUPERSAMPLE
    image = np.full((canvas, canvas, 3), 255, dtype=np.uint8)
    depth = np.full((canvas, canvas), -np.inf, dtype=np.float64)
    light = np.array([-0.35, 0.65, 0.68])
    light /= np.linalg.norm(light)

    colored = []
    for tri in primitives[0]:
        w = points[tri]
        normal = np.cross(w[1] - w[0], w[2] - w[0])
        norm = np.linalg.norm(normal)
        if norm == 0:
            continue
        normal /= norm
        if np.dot(normal, camera) <= 0:
            continue
        shade = 0.48 + 0.52 * max(0.0, float(np.dot(normal, light)))
        color = np.array(
            [min(255, round(255 * shade)), round(42 * shade), round(52 * shade)],
            dtype=np.uint8,
        )
        colored.append((tri, color))
    for tri, color in colored:
        draw_triangle(image, depth, screen, points, tri, color)
    for tri in primitives[1]:
        draw_triangle(
            image, depth, screen, points, tri, np.array([8, 8, 8], dtype=np.uint8)
        )

    image = image.reshape(
        SIZE, SUPERSAMPLE, SIZE, SUPERSAMPLE, 3
    ).mean(axis=(1, 3)).round().astype(np.uint8)
    return image


def png_chunk(kind, data):
    payload = kind + data
    return (
        struct.pack(">I", len(data))
        + payload
        + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
    )


def write_png(path, image):
    height, width, channels = image.shape
    assert channels == 3
    raw = b"".join(b"\0" + image[y].tobytes() for y in range(height))
    data = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0),
        )
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nets", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = [row for _, group in selection() for row in group]
    for row in rows:
        name = f"v{row['v']}{row['name']}"
        nid = row.get("id", name)
        source = args.nets / nid / "rb.glb"
        target = args.out / f"{nid}.png"
        theta, phi = ORBITS.get(nid, (0, 100))
        write_png(target, render(source, theta, phi))
        print(target)


if __name__ == "__main__":
    main()
