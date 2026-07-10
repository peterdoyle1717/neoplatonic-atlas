#!/usr/bin/env python3
"""Collect morph frames for the failing dented continuations.

For each case: DESCENT = walker embedded realization laddered from 60 down
(plain gate) recording bends at every accepted rung, until it dies; CLIMB =
direct ideal root laddered up from 0. JSON per case with all frames.
"""
import subprocess, json, glob, math, os, sys
from multiprocessing import Pool
import numpy as np
import ideal_limit as IL

BIN = "/Users/doyle/Dropbox/neo/bendprover/csrc/euclid_lm_mp"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'failure_frames')
os.makedirs(OUT, exist_ok=True)

name_of = {}
for blk in open('/Users/doyle/Dropbox/neo/atlas2/data/records.bends').read().split('net ')[1:]:
    nm = blk.split()[0]
    for ln in blk.splitlines():
        if ln.startswith('faces '): name_of[ln[6:].strip()] = nm

walks = {}
for f in glob.glob('/Users/doyle/Dropbox/neo/atlas2/data/walks/*.json'):
    d = json.load(open(f))
    walks[d['netcode']] = d

# cases from climb_all.tsv
OTHER, STALL = [], []
for l in open(os.path.join(HERE, 'climb_all.tsv')):
    if l.startswith('#'): continue
    t = l.rstrip('\n').split('\t')
    if t[2] == 'OTHER': OTHER.append((t[0], t[1]))
    elif t[2] == 'STALL': STALL.append((t[0], t[1]))
FOLD = [(nc, '5,9') for nc in walks if name_of.get(nc) == 'CCCACCACACCACACACAABBE']

JOBS = ([(nc, k, 'descent') for nc, k in OTHER + STALL + FOLD] +
        [(nc, k, 'climb') for nc, k in OTHER + STALL])


def solve(nc, alpha, key, seedfile):
    args = [BIN, "--bends-only", "--alpha", f"{alpha:.6f}", "--name", "X",
            "--dents", key, "--seed", seedfile, nc]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return None
    if "end" not in r.stdout: return None
    return {f'{tk[3]},{tk[4]}': float(tk[5]) for tk in
            (l.split() for l in r.stdout.splitlines())
            if len(tk) >= 6 and tk[0] == '#' and tk[1] == 'bend'}


def job(j):
    nc, key, kind = j
    nm = name_of.get(nc, 'unknown')
    tag = f'{nm}_{key.replace(",", "_")}_{kind}'
    seedfile = os.path.join(OUT, f'seed_{tag}.txt')
    frames = []
    if kind == 'descent':
        wb = walks[nc]['atlas'][key]
        frames.append([60.0, dict(wb)])
        with open(seedfile, 'w') as f:
            for k2, v in wb.items():
                i, jx = k2.split(','); f.write(f'{i} {jx} {float(v)!r}\n')
        alpha, step, nfail = 60.0, 1.0, 0
        while alpha > 0.6 and nfail < 12 and step >= 1e-3:
            a = max(alpha - step, 0.6)
            b = solve(nc, a, key, seedfile)
            if b is None: nfail += 1; step /= 2; continue
            nfail = 0; alpha = a; frames.append([a, b])
            with open(seedfile, 'w') as f:
                for k2, v in b.items():
                    i, jx = k2.split(','); f.write(f'{i} {jx} {float(v)!r}\n')
            step = min(step * 1.6, 2.0)
    else:  # climb from direct ideal root
        faces = [tuple(int(x) for x in ff.split(',')) for ff in nc.split(';')]
        V = max(max(f) for f in faces)
        cyc = IL.links(V, faces)
        edges = sorted({(min(a, b), max(a, b)) for fc in faces for a, b in zip(fc, fc[1:] + fc[:1])})
        E = len(edges)
        dents = set(int(x) for x in key.split(','))
        sigma = {v: (-1 if v in dents else 1) for v in range(1, V + 1)}
        A = np.zeros((V, E))
        for i, (a_, b_) in enumerate(edges): A[a_-1, i] = A[b_-1, i] = 1
        t = np.array([sigma[v] * 2 * math.pi for v in range(1, V + 1)])
        bI, _, res = IL.gauss_newton(np.linalg.lstsq(A, t, rcond=None)[0], edges, V, cyc, sigma)
        if res > 1e-10:
            return (tag, 'NOIDEAL', 0)
        frames.append([0.0, {f'{a_},{b_}': float(bI[i]) for i, (a_, b_) in enumerate(edges)}])
        with open(seedfile, 'w') as f:
            for i, (a_, b_) in enumerate(edges): f.write(f'{a_} {b_} {float(bI[i])!r}\n')
        alpha, step, nfail = 0.0, 1.0, 0
        while alpha < 60.0 and nfail < 12 and step >= 1e-3:
            a = min(alpha + step, 60.0)
            b = solve(nc, a, key, seedfile)
            if b is None: nfail += 1; step /= 2; continue
            nfail = 0; alpha = a; frames.append([a, b])
            with open(seedfile, 'w') as f:
                for k2, v in b.items():
                    i, jx = k2.split(','); f.write(f'{i} {jx} {float(v)!r}\n')
            step = min(step * 1.6, 2.0)
    os.remove(seedfile)
    json.dump({'netcode': nc, 'name': nm, 'key': key, 'kind': kind,
               'endpoint': frames[-1][0], 'frames': frames},
              open(os.path.join(OUT, f'{tag}.json'), 'w'))
    return (tag, 'OK', len(frames))


if __name__ == '__main__':
    os.nice(19)
    with Pool(6) as pool:
        for r in pool.imap_unordered(job, JOBS):
            print(*r, flush=True)
    print('FRAMES-DONE')
