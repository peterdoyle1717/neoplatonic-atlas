#!/usr/bin/env python3
"""Climb every direct ideal solution up to Euclidean 60 (PD experiment,
all-cases version). Per dented pattern with a direct ideal root: seed it,
ladder alpha 0 -> 60 (plain gate), at 60 compare with the walker's embedded
realization and embcheck the endpoint. TSV log + summary."""
import subprocess, json, glob, math, os, sys
from multiprocessing import Pool
import numpy as np
import ideal_limit as IL

BIN = "/Users/doyle/Dropbox/projects/neo/bendprover/csrc/euclid_lm_mp"
EMB = "/Users/doyle/Dropbox/projects/neo/bendprover/csrc/embcheck_mp"
HERE = os.path.dirname(os.path.abspath(__file__))

CASES = []
for f in sorted(glob.glob('/Users/doyle/Dropbox/projects/neo/atlas2/data/walks/*.json')):
    d = json.load(open(f))
    for key, bends in d['atlas'].items():
        if key:
            CASES.append((d['netcode'], d['V'], key, bends))


def one(case):
    nc, V, key, wbends = case
    faces = [tuple(int(x) for x in ff.split(',')) for ff in nc.split(';')]
    cyc = IL.links(V, faces)
    edges = sorted({(min(a, b), max(a, b)) for fc in faces for a, b in zip(fc, fc[1:] + fc[:1])})
    E = len(edges)
    eidx = {e: i for i, e in enumerate(edges)}
    dents = set(int(x) for x in key.split(','))
    sigma = {v: (-1 if v in dents else 1) for v in range(1, V + 1)}
    A = np.zeros((V, E))
    for i, (a_, b_) in enumerate(edges):
        A[a_ - 1, i] = A[b_ - 1, i] = 1
    t = np.array([sigma[v] * 2 * math.pi for v in range(1, V + 1)])
    b0 = np.linalg.lstsq(A, t, rcond=None)[0]
    bI, _, res = IL.gauss_newton(b0, edges, V, cyc, sigma)
    if res > 1e-10:
        return (nc, key, 'NOIDEAL', 0.0, None, None, None)

    tag = f'{abs(hash(nc)) % 10**8}_{key.replace(",", "_")}'
    seedfile = os.path.join(HERE, f'cl_{tag}.txt')
    with open(seedfile, 'w') as f:
        for i, (a_, b_) in enumerate(edges):
            f.write(f'{a_} {b_} {float(bI[i])!r}\n')

    alpha, step, nfail, cur = 0.0, 1.0, 0, None
    while alpha < 60.0 and nfail < 12 and step >= 1e-3:
        a = min(alpha + step, 60.0)
        args = [BIN, "--bends-only", "--alpha", f"{a:.6f}", "--name", "X",
                "--dents", key, "--seed", seedfile, nc]
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            r = None
        out = r.stdout if r and "end" in r.stdout else None
        if out is None:
            nfail += 1
            step /= 2
            continue
        nfail = 0
        alpha = a
        cur = {(int(tk[3]), int(tk[4])): float(tk[5]) for tk in
               (l.split() for l in out.splitlines())
               if len(tk) >= 6 and tk[0] == '#' and tk[1] == 'bend'}
        with open(seedfile, 'w') as f:
            for (i, j), v in sorted(cur.items()):
                f.write(f'{i} {j} {float(v)!r}\n')
        step = min(step * 1.6, 3.0)
    os.remove(seedfile)
    if alpha < 60.0 or cur is None:
        return (nc, key, 'STALL', round(alpha, 4), None, None, None)

    bv = np.zeros(E)
    for (i, j), v in cur.items():
        bv[eidx[(min(i, j), max(i, j))]] = v
    bw = np.zeros(E)
    for k2, v in wbends.items():
        i, j = (int(x) for x in k2.split(','))
        bw[eidx[(min(i, j), max(i, j))]] = v
    dev = float(np.max(np.abs(bv - bw)))
    mx = float(np.max(np.abs(bv)))
    # embcheck the endpoint
    rec = [f'net X', f'v {V}', f'e {E}', 'unit halfturns', 'benderr 1e-30',
           'faces ' + ';'.join(','.join(map(str, f)) for f in faces)]
    for (a_, b_) in edges:
        rec.append(f'b {a_} {b_} {bv[eidx[(a_, b_)]] / math.pi:.36f}')
    rec.append('end')
    rf = os.path.join(HERE, f'cl_{tag}.rec')
    open(rf, 'w').write('\n'.join(rec) + '\n')
    r = subprocess.run([EMB, rf], capture_output=True, text=True, timeout=300)
    # verdict line goes to stdout ("X\t<v>\tPASS\t..."); summary goes to stderr
    emb = 'EMB' if ('\tPASS' in r.stdout or '\tPANCAKE' in r.stdout) else 'NONEMB'
    cls = 'WALKER' if dev < 1e-3 else 'OTHER'
    return (nc, key, cls, 60.0, round(dev, 4), round(mx, 4), emb)


if __name__ == '__main__':
    os.nice(19)
    out = open(os.path.join(HERE, 'climb_all.tsv'), 'w', buffering=1)
    with Pool(6) as pool:
        for r in pool.imap_unordered(one, CASES):
            out.write('\t'.join(map(str, r)) + '\n')
    out.write('# DONE\n')
