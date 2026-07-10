"""walklib.py -- geometry + page pieces salvaged from the dent walker."""
import math, os
import numpy as np
from collections import deque

# canonical CLERS names, from the definitive run's records
NAMES = {}
_cur = None
_nc_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "names.tsv")
if os.path.exists(_nc_src):
    for _ln in open(_nc_src):
        _name, _nc = _ln.rstrip("\n").split("\t")
        NAMES[_nc] = _name

STYLE = """body{font-family:Georgia,serif;max-width:1000px;margin:2em auto;line-height:1.6;color:#222;padding:0 1em}h1{font-size:1.3em}h1 a{color:inherit;text-decoration:none}h1 a:hover{text-decoration:underline}h2{font-size:1em;font-family:monospace;margin:2em 0 .2em}h2 a{color:#2255aa;text-decoration:none}h2 a:hover{text-decoration:underline}h2 .v{font-size:.8em;color:#888;font-family:Georgia,serif}p.desc{font-size:.9em;color:#555}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1.5em;margin-top:.4em}.item{text-align:center}.item .cell{position:relative;width:100%;padding-bottom:100%}.item .cell model-viewer{position:absolute;top:0;left:0;width:100%;height:100%;background:#f0f0f0;--poster-color:transparent}.item .d{font-family:monospace;font-size:.75em;color:#333}.item .o{font-size:.7em;color:#888}"""

def page(title, desc, rows, out):
    body = [f'<!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>{title} - Neoplatonic solids</title><script type=module src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js"></script><style>{STYLE}</style></head><body>']
    body.append(f'<h1><a href="https://math.dartmouth.edu/~doyle/docs/atlas/">Neoplatonic solids</a> - {title}</h1>')
    body.append(f'<p class=desc>{desc}</p>')
    cur = None
    for V, name, D, orb, glb in rows:
        if name != cur:
            if cur is not None: body.append('</div>')
            body.append(f'<h2><a href="https://math.dartmouth.edu/~doyle/docs/atlas/web/{V}/{name}.html">{name}</a> <span class=v>v={V}</span></h2><div class=grid>')
            cur = name
        dstr = "&empty;" if not D else "{" + ",".join(map(str, D)) + "}"
        orbs = f' <span class=o>&times;{orb}</span>' if orb > 1 else ""
        body.append(f'<div class=item><div class=cell><model-viewer src="glb/{glb}" camera-orbit="0deg 100deg auto" camera-controls interaction-prompt=none></model-viewer></div><span class=d>{dstr}</span>{orbs}</div>')
    body.append('</div></body></html>')
    open(out, "w").write("\n".join(body))

def develop(faces, bend):
    apex = {}
    for a, b, c in faces:
        apex[(a, b)] = c; apex[(b, c)] = a; apex[(c, a)] = b
    a0, b0, c0 = faces[0]
    pos = {a0: np.array([0., 0., 0.]), b0: np.array([1., 0., 0.]),
           c0: np.array([0.5, math.sqrt(3) / 2, 0.])}
    def fkey(f): return min(f, f[1:] + f[:1], f[2:] + f[:2])
    seen = {fkey((a0, b0, c0))}
    dq = deque([(a0, b0, c0)])
    while dq:
        f0 = dq.popleft()
        for i in range(3):
            x, y = f0[i], f0[(i + 1) % 3]
            d = apex[(y, x)]
            f1 = (y, x, d)
            if fkey(f1) in seen: continue
            A, B, P = pos[x], pos[y], pos[f0[(i + 2) % 3]]
            M = 0.5 * (A + B)
            w = P - M; w /= np.linalg.norm(w)
            n = np.cross(w, B - A); n /= np.linalg.norm(n)
            th = bend[tuple(sorted((x, y)))]
            pos[d] = M + (math.sqrt(3) / 2) * (-math.cos(th) * w + math.sin(th) * n)
            seen.add(fkey(f1)); dq.append(f1)
    return pos, apex

def bends_from_coords(faces, pos, apex):
    out = {}
    for (a, b), c in apex.items():
        if a > b: continue
        d = apex[(b, a)]
        A, B, C, D = pos[a], pos[b], pos[c], pos[d]
        u = B - A; u /= np.linalg.norm(u)
        n1 = np.cross(u, C - A); n1 /= np.linalg.norm(n1)
        n2 = np.cross(D - A, u); n2 /= np.linalg.norm(n2)
        out[(a, b)] = math.atan2(np.dot(np.cross(n1, n2), u), np.dot(n1, n2))
    return out

def automorphisms(faces, V):
    """all label permutations preserving the face structure (as a set of
    oriented triangles up to rotation, both orientations)."""
    apex = {}
    for a, b, c in faces:
        apex[(a, b)] = c; apex[(b, c)] = a; apex[(c, a)] = b
    darts = list(apex.keys())
    autos = []
    a0, b0 = darts[0]
    for (c0, d0) in darts:
        for flip in (0, 1):
            # propagate the dart map (a0,b0)->(c0,d0); flip reverses orientation
            m = {a0: c0, b0: d0}
            ok = True
            stack = [(a0, b0, c0, d0)]
            seend = set()
            while stack and ok:
                x, y, u, w = stack.pop()
                if (x, y) in seend: continue
                seend.add((x, y))
                z = apex[(x, y)]
                t = apex[(u, w)] if not flip else apex[(w, u)]
                if z in m:
                    if m[z] != t: ok = False; break
                else:
                    m[z] = t
                stack.append((y, z, w, t))
                stack.append((z, x, t, u))
                stack.append((y, x, w, u))     # cross into the adjacent face
            if ok and len(m) == V and len(set(m.values())) == V:
                # verify all faces map to faces
                fs = set(min(f, f[1:] + f[:1], f[2:] + f[:2]) for f in
                         ((a, b, c) for a, b, c in faces))
                good = True
                for (a, b, c) in faces:
                    im = (m[a], m[b], m[c]) if not flip else (m[c], m[b], m[a])
                    if min(im, im[1:] + im[:1], im[2:] + im[:2]) not in fs:
                        good = False; break
                if good:
                    autos.append(m)
    # dedup
    uniq = []
    seen = set()
    for m in autos:
        key = tuple(m[v] for v in range(1, V + 1))
        if key not in seen:
            seen.add(key); uniq.append(m)
    return uniq


# ---- face-clearance metric (min distance between vertex-disjoint faces) ----

def _pt_tri(p, a, b, c):
    import numpy as np
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = ab @ ap, ac @ ap
    if d1 <= 0 and d2 <= 0: return float(np.linalg.norm(ap))
    bp = p - b; d3, d4 = ab @ bp, ac @ bp
    if d3 >= 0 and d4 <= d3: return float(np.linalg.norm(bp))
    cp = p - c; d5, d6 = ab @ cp, ac @ cp
    if d6 >= 0 and d5 <= d6: return float(np.linalg.norm(cp))
    vc = d1*d4 - d3*d2
    if vc <= 0 <= d1 and d3 <= 0:
        t = d1/(d1-d3); return float(np.linalg.norm(ap - t*ab))
    vb = d5*d2 - d1*d6
    if vb <= 0 <= d2 and d6 <= 0:
        t = d2/(d2-d6); return float(np.linalg.norm(ap - t*ac))
    va = d3*d6 - d5*d4
    if va <= 0 and d4-d3 >= 0 and d5-d6 >= 0:
        t = (d4-d3)/((d4-d3)+(d5-d6)); return float(np.linalg.norm(p - b - t*(c-b)))
    n = np.cross(ab, ac); n /= np.linalg.norm(n)
    return float(abs(ap @ n))

def _seg_seg(p1, q1, p2, q2):
    import numpy as np
    d1, d2, r = q1-p1, q2-p2, p1-p2
    a, e, f = d1@d1, d2@d2, d2@r
    c_, b = d1@r, d1@d2
    den = a*e - b*b
    s = float(np.clip((b*f - c_*e)/den, 0, 1)) if den > 1e-14 else 0.0
    t = (b*s + f)/e if e > 1e-14 else 0.0
    if t < 0: t = 0; s = float(np.clip(-c_/a, 0, 1)) if a > 1e-14 else 0
    elif t > 1: t = 1; s = float(np.clip((b-c_)/a, 0, 1)) if a > 1e-14 else 0
    return float(np.linalg.norm((p1 + s*d1) - (p2 + t*d2)))

def clearance(faces, pos):
    """min distance between vertex-disjoint faces of a developed model."""
    import numpy as np
    P = {v: np.array(p) for v, p in pos.items()}
    mind = float("inf")
    for i in range(len(faces)):
        for j in range(i + 1, len(faces)):
            if set(faces[i]) & set(faces[j]): continue
            t1 = [P[v] for v in faces[i]]; t2 = [P[v] for v in faces[j]]
            d = min(_pt_tri(p, *t2) for p in t1)
            d = min(d, min(_pt_tri(p, *t1) for p in t2))
            for x in range(3):
                for y in range(3):
                    d = min(d, _seg_seg(t1[x], t1[(x+1)%3], t2[y], t2[(y+1)%3]))
            mind = min(mind, d)
    return mind
