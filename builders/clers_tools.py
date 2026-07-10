"""clers_tools.py -- decode (salvaged from clers/src/clers.py), planar
CLERS unfolding, and the colored unfolding SVG in the old atlas style.

The unfolding runs the decoder's stack machine and places every face as
a unit equilateral in the plane: a child's new apex is the reflection
of the parent's apex across their shared (entry) edge, so the strip
unfolds without local overlap. Letters follow the recipe, one per face
in push order -- same convention as the old clers_layout.
"""
import importlib.util, os
import numpy as np

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "clers_src", os.path.join(_here, "clers_decode_src.py"))
clers_src = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(clers_src)
decode = clers_src.decode
encode = clers_src.encode

COLORS = {'A': '#ff0000', 'B': '#ff8800', 'C': '#ffcc00',
          'D': '#00aa00', 'E': '#0066ff'}


def _reflect(p, x, y):
    """reflect point p across the line through x, y."""
    d = y - x
    d = d / np.linalg.norm(d)
    v = p - x
    return x + 2 * (v @ d) * d - v


def layout(recipe):
    """[(letter, (A, B, C) planar points)] in push (= recipe) order."""
    coords = {1: np.array([0.0, 0.0]), 2: np.array([1.0, 0.0]),
              3: np.array([0.5, np.sqrt(3) / 2])}
    out = []
    ptr = 0
    stack = []
    tile = recipe[ptr]; ptr += 1
    V = 3
    stack.append((tile, 1, 2, 3, 0))
    out.append((tile, (coords[1].copy(), coords[2].copy(), coords[3].copy())))

    def push_child(x, y, w):
        nonlocal ptr, V
        t = recipe[ptr]; ptr += 1
        V += 1
        coords[V] = _reflect(coords[w], coords[x], coords[y])
        stack.append((t, x, y, V, 0))
        out.append((t, (coords[x].copy(), coords[y].copy(), coords[V].copy())))
        return t

    while stack:
        tile, a, b, c, phase = stack[-1]
        if tile == "E":
            stack.pop()
        elif tile == "A":
            if phase == 0:
                stack[-1] = (tile, a, b, c, 1)
                push_child(c, b, a)
            else:
                stack.pop()
        elif tile in ("B", "C"):
            if phase == 0:
                stack[-1] = (tile, a, b, c, 1)
                push_child(a, c, b)
            else:
                stack.pop()
        elif tile == "D":
            if phase == 0:
                stack[-1] = (tile, a, b, c, 1)
                push_child(a, c, b)
            elif phase == 1:
                stack[-1] = (tile, a, b, c, 2)
                push_child(c, b, a)
            else:
                stack.pop()
    assert ptr == len(recipe), "layout consumed wrong number of tiles"
    return out


def clers_svg(name):
    """colored CLERS unfolding SVG, old-atlas style."""
    positions = layout(name)
    pts = [p for _, tri in positions for p in tri]
    xs = [p[0] for p in pts]; ys = [-p[1] for p in pts]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    w = xmax - xmin or 1; h = ymax - ymin or 1
    pad = 0.08 * max(w, h)
    sw = 0.015 * max(w, h)
    polys = []
    for letter, (a, b, c) in positions:
        s = f'{a[0]:.6f},{-a[1]:.6f} {b[0]:.6f},{-b[1]:.6f} {c[0]:.6f},{-c[1]:.6f}'
        polys.append(f'<polygon points="{s}" fill="{COLORS.get(letter, "#888")}" '
                     f'stroke="#1a1a1a" stroke-width="{sw:.4f}" stroke-linejoin="round"/>')
    vb = f'{xmin-pad:.4f} {ymin-pad:.4f} {w+2*pad:.4f} {h+2*pad:.4f}'
    return (f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg">\n'
            + '\n'.join(polys) + '\n</svg>')
