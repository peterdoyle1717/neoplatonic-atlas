#!/usr/bin/env python3
"""Exact-gated continuation ladder (PD-sanctioned for dented ideals) on ALL
walker dent sets, all 70 nets. Per case: endpoint alpha, max|b| there, hinge
edge. Classifies: REACHED (alpha=1), HINGE (died with max|b| > 3.10), OTHER.
Parallel pool, nice'd."""
import subprocess, json, glob, math, os, sys
from multiprocessing import Pool

BIN = "/Users/doyle/Dropbox/neo/bendprover/csrc/euclid_lm_mp"
HERE = os.path.dirname(os.path.abspath(__file__))

CASES = []
for f in sorted(glob.glob('/Users/doyle/Dropbox/neo/atlas2/data/walks/*.json')):
    d = json.load(open(f))
    for key, bends in d['atlas'].items():
        if key:
            CASES.append((d['netcode'], d['V'], key, bends))


def solve(nc, alpha, dents_str, seedfile):
    args = [BIN, "--bends-only", "--alpha", f"{alpha:.6f}", "--name", "X",
            "--dents", dents_str, "--dents-exact", "--seed", seedfile, nc]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return None
    if "end" not in r.stdout:
        return None
    return {(int(t[3]), int(t[4])): float(t[5]) for t in
            (ln.split() for ln in r.stdout.splitlines())
            if len(t) >= 6 and t[0] == '#' and t[1] == 'bend'}


def ladder(case):
    nc, V, key, wbends = case
    tag = f'{abs(hash(nc)) % 10**8}_{key.replace(",", "_")}'
    seedfile = os.path.join(HERE, f'hs_{tag}.txt')
    with open(seedfile, 'w') as f:
        for k, v in wbends.items():
            i, j = k.split(',')
            f.write(f'{i} {j} {v!r}\n')
    alpha, step, nfail, cur = 60.0, 2.0, 0, None
    while alpha > 1.0 and nfail < 12 and step >= 1e-3:
        a = max(alpha - step, 1.0)
        b = solve(nc, a, key, seedfile)
        if b is None:
            nfail += 1
            step /= 2
            continue
        nfail = 0
        alpha, cur = a, b
        with open(seedfile, 'w') as f:
            for (i, j), v in sorted(b.items()):
                f.write(f'{i} {j} {v!r}\n')
        step = min(step * 1.6, 4.0)
    os.remove(seedfile)
    if cur is None:
        return (nc, key, 'NOSTART', 60.0, None, None)
    mxe, mxv = max(cur.items(), key=lambda kv: abs(kv[1]))
    if alpha <= 1.0:
        cls = 'REACHED'
    elif abs(mxv) > 3.10:
        cls = 'HINGE'
    else:
        cls = 'OTHER'
    return (nc, key, cls, alpha, round(abs(mxv), 5), mxe)


if __name__ == '__main__':
    os.nice(19)
    out = open(os.path.join(HERE, 'hinge_sweep.tsv'), 'w', buffering=1)
    with Pool(6) as pool:
        for r in pool.imap_unordered(ladder, CASES):
            out.write('\t'.join(map(str, r)) + '\n')
    out.write('# DONE\n')
