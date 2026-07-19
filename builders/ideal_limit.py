#!/usr/bin/env python3
"""alpha->0 renormalization check + direct ideal solve.

Derivation being tested: with W_v(alpha,b) = prod_j Rz(alpha) Rx(b_j) in SU(2),
  W_v = e^{i s_d/2} + (alpha/2) e^{-i s_d/2} T_v k + O(alpha^2),
  T_v = sum_{j=0}^{d-1} e^{i s_j},  s_j = b_1+...+b_j  (cyclic order at v).
So against target -1 (s_d near sigma_v 2pi):
  |W_v + 1|^2 = (Delta_v/2)^2 + (alpha/2)^2 |T_v|^2 + h.o.,
  Delta_v = s_d - sigma_v 2pi.
Predictions at the solver's finite-alpha roots: max|Delta| ~ C alpha^2,
max|T| ~ C' alpha, and bends -> ideal root at rate O(alpha).
Ideal root = zero of R(b) = (Delta_v, Re T_v, Im T_v)_v  (3V eqns, 3V-6 unknowns).
"""
import json, glob, math, cmath, subprocess, sys
import numpy as np

BIN = "/Users/doyle/Dropbox/projects/neo/bendprover/csrc/euclid_lm_mp"
REC = "/Users/doyle/Dropbox/projects/neo/atlas2/data/records.bends"
TWO_PI = 2 * math.pi


def load_net(name):
    for blk in open(REC).read().split("net ")[1:]:
        if blk.split()[0] == name:
            V = int([l for l in blk.splitlines() if l.startswith("v ")][0].split()[1])
            fl = [l for l in blk.splitlines() if l.startswith("faces ")][0][6:].strip()
            faces = [tuple(int(x) for x in f.split(",")) for f in fl.split(";")]
            return V, faces, fl
    raise KeyError(name)


def links(V, faces):
    succ = {v: {} for v in range(1, V + 1)}
    for a, b, c in faces:
        for v, x, y in ((a, b, c), (b, c, a), (c, a, b)):
            succ[v][x] = y
    cyc = {}
    for v in range(1, V + 1):
        start = next(iter(succ[v]))
        out = [start]
        cur = succ[v][start]
        while cur != start:
            out.append(cur)
            cur = succ[v][cur]
        assert len(out) == len(succ[v]), f"link at {v} not a single cycle"
        cyc[v] = out
    return cyc


def solve_alpha(nc, alpha, dents=None):
    args = [BIN, "--prove", "--alpha", f"{alpha:.6f}", "--name", "X"]
    if dents:
        args += ["--dents", ",".join(map(str, sorted(dents)))]
    args.append(nc)
    r = subprocess.run(args, capture_output=True, text=True, timeout=300)
    if "end" not in r.stdout:
        return None
    bends = {}
    for ln in r.stdout.splitlines():
        t = ln.split()
        if t and t[0] == "b":
            bends[(int(t[1]), int(t[2]))] = float(t[3]) * math.pi
    return bends


def defects(V, cyc, bends, sigma):
    """per-vertex (Delta_v, T_v): unit-step planar path, turn b before each
    subsequent step (step at heading s_{j-1})."""
    out = []
    for v in range(1, V + 1):
        s, T = 0.0, 0j
        for u in cyc[v]:
            T += cmath.exp(1j * s)
            s += bends.get((v, u), bends.get((u, v)))
        out.append((s - sigma[v] * TWO_PI, T))
    return out


def residual(bvec, edges, V, cyc, sigma):
    bends = {e: bvec[i] for i, e in enumerate(edges)}
    r = []
    for d, T in defects(V, cyc, bends, sigma):
        r += [d, T.real, T.imag]
    return np.array(r)


def gauss_newton(b0, edges, V, cyc, sigma, itmax=80):
    b = b0.copy()
    for it in range(itmax):
        r = residual(b, edges, V, cyc, sigma)
        if np.max(np.abs(r)) < 1e-14:
            return b, it, np.max(np.abs(r))
        J = np.zeros((len(r), len(b)))
        h = 1e-7
        for i in range(len(b)):
            bp = b.copy(); bp[i] += h
            J[:, i] = (residual(bp, edges, V, cyc, sigma) - r) / h
        step, *_ = np.linalg.lstsq(J, -r, rcond=None)
        t = 1.0
        for _ in range(30):  # backtrack
            if np.linalg.norm(residual(b + t * step, edges, V, cyc, sigma)) < np.linalg.norm(r):
                break
            t /= 2
        b = b + t * step
    return b, itmax, np.max(np.abs(residual(b, edges, V, cyc, sigma)))


def run_case(name, dents):
    V, faces, nc = load_net(name)
    cyc = links(V, faces)
    edges = sorted({(min(a, b), max(a, b)) for f in faces for a, b in zip(f, f[1:] + f[:1])})
    E = len(edges)
    sigma = {v: (-1 if v in dents else 1) for v in range(1, V + 1)}
    print(f"\n=== {name}  V={V} E={E}  dents={sorted(dents) or 'none'} ===")

    # rung solves
    rung = {}
    for a in (16.0, 8.0, 4.0, 2.0, 1.0):
        bends = solve_alpha(nc, a, dents)
        if bends is None:
            print(f"  alpha={a:5.1f}  SOLVER FAILED")
            continue
        ds = defects(V, cyc, bends, sigma)
        rung[a] = np.array([bends.get(e, bends.get(e[::-1])) for e in edges])
        print(f"  alpha={a:5.1f}  max|Delta|={max(abs(d) for d,_ in ds):.3e}"
              f"  max|T|={max(abs(T) for _,T in ds):.3e}")

    # direct ideal solve from the wish (L2-min point of the sigma-slice)
    A = np.zeros((V, E))
    for i, (a_, b_) in enumerate(edges):
        A[a_ - 1, i] = A[b_ - 1, i] = 1
    t = np.array([sigma[v] * TWO_PI for v in range(1, V + 1)])
    b_wish = np.linalg.lstsq(A, t, rcond=None)[0]
    b_star, its, res = gauss_newton(b_wish, edges, V, cyc, sigma)
    print(f"  ideal GN from wish: {its} iters, max residual {res:.2e}")
    if res < 1e-10:
        r0 = residual(b_star, edges, V, cyc, sigma)
        J = np.zeros((len(r0), E)); h = 1e-7
        for i in range(E):
            bp = b_star.copy(); bp[i] += h
            J[:, i] = (residual(bp, edges, V, cyc, sigma) - r0) / h
        sv = np.linalg.svd(J, compute_uv=False)
        rank = int(np.sum(sv > 1e-8 * sv[0]))
        print(f"  Jacobian at ideal root: {3*V}x{E}, rank {rank} "
              f"(cokernel {3*V - rank}), sigma_min {sv[rank-1]:.3e}, kernel {E - rank}")
        for a in sorted(rung):
            print(f"  ||b({a:.0f}deg) - b*||_inf = {np.max(np.abs(rung[a] - b_star)):.3e}")
    return rung


if __name__ == "__main__":
    run_case("CCCACACACACACAAE", set())
    run_case("CCCACCACACAACAAE", set())
    run_case("CCCACCACACAACAAE", {1})
