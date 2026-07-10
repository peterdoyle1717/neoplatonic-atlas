#!/usr/bin/env python3
"""In-slice ideal solve, adopted discipline: direct from the hopeful starter.

b = b_wish + N y with the vertex sums pinned at sigma_v * 2pi exactly
(the slice); minimize the translation defects T_v alone (2V residuals,
2V-6 unknowns). Principal-branch gate |b_e| < pi on every accepted step.
Restarts perturb the STARTER; no continuation.
"""
import json, glob, math, cmath, sys
import numpy as np
import ideal_limit as IL

TWO_PI = 2 * math.pi


def slice_setup(V, edges, sigma):
    E = len(edges)
    A = np.zeros((V, E))
    for i, (a, b) in enumerate(edges):
        A[a - 1, i] = A[b - 1, i] = 1
    t = np.array([sigma[v] * TWO_PI for v in range(1, V + 1)])
    b_wish = np.linalg.lstsq(A, t, rcond=None)[0]      # hopeful starter
    _, s, Vt = np.linalg.svd(A)
    N = Vt[int(np.sum(s > 1e-10)):].T                  # E x (E - V)
    return b_wish, N


def T_res(b, V, cyc, edges):
    bends = {e: b[i] for i, e in enumerate(edges)}
    r = []
    for v in range(1, V + 1):
        s, T = 0.0, 0j
        for u in cyc[v]:
            T += cmath.exp(1j * s)
            s += bends.get((v, u), bends.get((u, v)))
        r += [T.real, T.imag]
    return np.array(r)


def jac_T(b, V, cyc, edges):
    eidx = {e: i for i, e in enumerate(edges)}
    J = np.zeros((2 * V, len(edges)))
    bd = {e: b[i] for i, e in enumerate(edges)}
    for v in range(1, V + 1):
        d = len(cyc[v])
        s = np.zeros(d + 1)
        for j, u in enumerate(cyc[v]):
            s[j + 1] = s[j] + bd[(min(v, u), max(v, u))]
        steps = np.exp(1j * s[:d])
        for m, u in enumerate(cyc[v], start=1):
            col = eidx[(min(v, u), max(v, u))]
            dT = 1j * np.sum(steps[m:]) if m < d else 0.0
            J[2 * (v - 1), col] += dT.real
            J[2 * (v - 1) + 1, col] += dT.imag
    return J


def lm_slice(y0, b_wish, N, V, cyc, edges, itmax=400):
    y = y0.copy()
    b = b_wish + N @ y
    r = T_res(b, V, cyc, edges)
    lam = 1e-3
    for _ in range(itmax):
        if np.max(np.abs(r)) < 1e-13:
            return y, np.max(np.abs(r))
        J = jac_T(b, V, cyc, edges) @ N
        ok = False
        for _ in range(50):
            dy = np.linalg.solve(J.T @ J + lam * np.eye(J.shape[1]), -J.T @ r)
            b2 = b_wish + N @ (y + dy)
            if np.max(np.abs(b2)) < math.pi:           # principal-branch gate
                r2 = T_res(b2, V, cyc, edges)
                if np.linalg.norm(r2) < np.linalg.norm(r):
                    y, b, r = y + dy, b2, r2
                    lam = max(lam / 3, 1e-12)
                    ok = True
                    break
            lam *= 3
        if not ok:
            break
    return y, np.max(np.abs(r))


def attack(name, dent_key, restarts=60, seed=0):
    nc = None
    for blk in open('/Users/doyle/Dropbox/neo/atlas2/data/records.bends').read().split('net ')[1:]:
        if blk.split()[0] == name:
            for ln in blk.splitlines():
                if ln.startswith('faces '):
                    nc = ln[6:].strip()
    faces = [tuple(int(x) for x in ff.split(',')) for ff in nc.split(';')]
    V = max(max(f) for f in faces)
    cyc = IL.links(V, faces)
    edges = sorted({(min(a, b), max(a, b)) for fc in faces for a, b in zip(fc, fc[1:] + fc[:1])})
    dents = set(int(x) for x in dent_key.split(',')) if dent_key else set()
    sigma = {v: (-1 if v in dents else 1) for v in range(1, V + 1)}
    b_wish, N = slice_setup(V, edges, sigma)
    rng = np.random.default_rng(seed)
    best = np.inf
    hit = None
    for k in range(restarts + 1):
        scale = 0.0 if k == 0 else (0.1, 0.3, 1.0, 3.0)[k % 4]
        y0 = scale * rng.standard_normal(N.shape[1])
        y, res = lm_slice(y0, b_wish, N, V, cyc, edges)
        if res < best:
            best = res
            if res < 1e-12:
                hit = b_wish + N @ y
                break
    tag = f'{name} dents={{{dent_key or ""}}}'
    if hit is not None:
        print(f'{tag}: ROOT FOUND, residual {best:.2e} (restart {k})')
        return hit
    print(f'{tag}: no root; best T-floor over {restarts+1} starts = {best:.4e}')
    return None


if __name__ == "__main__":
    # target
    attack('CCCACCACACCACACACAABBE', '5,9')
    # controls on the same net (converged in the sweep)
    for key in ('', '5,7', '7,9', '5,7,9'):
        attack('CCCACCACACCACACACAABBE', key, restarts=3)
