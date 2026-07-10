"""realize_h.py -- develop a bend record in H^3 (hyperboloid model).

Faces are equilateral hyperbolic triangles with corner angle alpha;
side length from cosh(ell) = cos(alpha)/(1 - cos(alpha)) (alpha -> 60
degrees gives ell -> 0, the Euclidean shrink limit; alpha -> 0 gives
ideal). Development mirrors the Euclidean place_third offset form:
midpoint frame (u along the edge, w toward the old apex, n normal),
new apex at geodesic distance alt along -cos(theta) w + sin(theta) n.

Signature (+,+,+,-): mdot(x,y) = x1y1 + x2y2 + x3y3 - x4y4;
points have mdot(x,x) = -1, x4 > 0; tangents are spacelike.
"""
import math
import numpy as np
from collections import deque


def mdot(x, y):
    return x[0]*y[0] + x[1]*y[1] + x[2]*y[2] - x[3]*y[3]

def norm_pt(x):
    return x / math.sqrt(-mdot(x, x))

def norm_sp(t):
    return t / math.sqrt(mdot(t, t))

def tangent_at(M, X):
    """tangent at M pointing toward X (projection of X to M-perp)."""
    t = X + mdot(X, M) * M
    return t

def side_length(alpha):
    ca = math.cos(alpha)
    return math.acosh(ca / (1.0 - ca))

def develop_h(faces, bend, alpha):
    """bend: {(a,b) sorted: radians}; returns {v: 4-vector}, closure resid."""
    ell = side_length(alpha)
    chl, shl = math.cosh(ell), math.sinh(ell)
    alt = math.acosh(math.cosh(ell) / math.cosh(ell / 2.0))
    cha, sha = math.cosh(alt), math.sinh(alt)

    apex = {}
    for a, b, c in faces:
        apex[(a, b)] = c; apex[(b, c)] = a; apex[(c, a)] = b
    a0, b0, c0 = faces[0]
    O = np.array([0.0, 0.0, 0.0, 1.0])
    e1 = np.array([1.0, 0.0, 0.0, 0.0])
    e2 = np.array([0.0, 1.0, 0.0, 0.0])
    pos = {a0: O,
           b0: chl * O + shl * e1,
           c0: chl * O + shl * (math.cos(alpha) * e1 + math.sin(alpha) * e2)}

    def place(A, B, P, theta):
        M = norm_pt(A + B)
        u = norm_sp(tangent_at(M, B))
        wt = tangent_at(M, P)
        wt = wt - mdot(wt, u) * u
        w = norm_sp(wt)
        # n: spacelike unit vector orthogonal to M, u, w; sign fixed so the
        # Euclidean limit matches the flat developer (calibrated below)
        n = None
        for cand in (np.array([0.,0.,1.,0.]), np.array([0.,1.,0.,0.]),
                     np.array([1.,0.,0.,0.]), np.array([0.,0.,0.,1.])):
            t = cand + mdot(cand, M) * M
            t = t - mdot(t, u) * u - mdot(t, w) * w
            q = mdot(t, t)
            if q > 1e-12:
                n = t / math.sqrt(q); break
        # orientation: det(M, w, u, n) fixes handedness of the frame
        if np.linalg.det(np.stack([M, w, u, n])) < 0:
            n = -n
        d = -math.cos(theta) * w + math.sin(theta) * n
        return cha * M + sha * d

    def fkey(f):
        return min(f, f[1:] + f[:1], f[2:] + f[:2])
    seen = {fkey((a0, b0, c0))}
    dq = deque([(a0, b0, c0)])
    resid = 0.0
    while dq:
        f0 = dq.popleft()
        for i in range(3):
            x, y = f0[i], f0[(i + 1) % 3]
            d = apex[(y, x)]
            f1 = (y, x, d)
            th = bend[tuple(sorted((x, y)))]
            D = place(pos[x], pos[y], pos[f0[(i + 2) % 3]], th)
            if fkey(f1) in seen:
                resid = max(resid, float(np.max(np.abs(D - pos[d]))))
                continue
            pos[d] = D
            seen.add(fkey(f1)); dq.append(f1)
    return pos, resid

def klein(pos):
    return {v: x[:3] / x[3] for v, x in pos.items()}

def poincare(pos):
    return {v: x[:3] / (1.0 + x[3]) for v, x in pos.items()}

def center(pos):
    """boost the Minkowski mean of the vertex 4-vectors to the x4 axis
    (salvaged from the old atlas lorentz.py, matrix form identical)."""
    C = np.mean([x for x in pos.values()], axis=0)
    q = mdot(C, C)
    if q >= 0:
        return dict(pos)
    x1, x2, x3, x4 = C
    c = math.sqrt(-q)
    dd = x4 - x3
    if dd <= 0:
        return dict(pos)
    a = x1 / dd; b = x2 / dd; s = c / dd
    M = np.array([
        [1,     0,     a,                     -a],
        [0,     1,     b,                     -b],
        [-a/s, -b/s,  (1-a*a-b*b+s*s)/(2*s),  (1+a*a+b*b-s*s)/(2*s)],
        [-a/s, -b/s,  (1-a*a-b*b-s*s)/(2*s),  (1+a*a+b*b+s*s)/(2*s)],
    ])
    return {v: M @ x for v, x in pos.items()}

def edge_length_check(faces, pos):
    """max deviation of edge geodesic lengths from their common value."""
    ds = []
    seen = set()
    for a, b, c in faces:
        for x, y in ((a, b), (b, c), (c, a)):
            k = (min(x, y), max(x, y))
            if k in seen: continue
            seen.add(k)
            ds.append(math.acosh(max(1.0, -mdot(pos[x], pos[y]))))
    return min(ds), max(ds)
