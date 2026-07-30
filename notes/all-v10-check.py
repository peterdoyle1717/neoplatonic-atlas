#!/usr/bin/env python3
"""Pre-implementation census check for notes/all-v10-g1-spec.md."""

from collections import Counter
import hashlib
from itertools import combinations
import argparse
import os
import subprocess
import sys


EXPECTED_TOTALS = {4: 1, 5: 1, 6: 2, 7: 5, 8: 14, 9: 50, 10: 233}


def rotations(line):
    head, body = line.strip().split(maxsplit=1)
    n = int(head)
    rows = body.split(",")
    assert len(rows) == n
    return [[ord(c) - ord("a") + 1 for c in row] for row in rows]


def faces_from_rotations(rows):
    occurrences = {}
    for a, nbrs in enumerate(rows, 1):
        assert len(nbrs) == len(set(nbrs))
        assert a not in nbrs
        for i, b in enumerate(nbrs):
            assert a in rows[b - 1]
            c = nbrs[(i + 1) % len(nbrs)]
            occurrences.setdefault(frozenset((a, b, c)), []).append((a, b, c))
    faces = []
    for key, directed in occurrences.items():
        assert len(key) == 3
        assert len(directed) == 3
        a, b, c = directed[0]
        cyclic = {(a, b, c), (b, c, a), (c, a, b)}
        assert set(directed) == cyclic
        faces.append((a, b, c))
    return faces


def validate(faces, v):
    vertices = {x for f in faces for x in f}
    edges = Counter(
        frozenset((f[i], f[(i + 1) % 3]))
        for f in faces
        for i in range(3)
    )
    degrees = Counter(x for e in edges for x in e)
    assert vertices == set(range(1, v + 1))
    assert len(faces) == 2 * v - 4
    assert len(edges) == 3 * v - 6
    assert set(edges.values()) == {2}
    assert max(degrees.values()) <= 6
    assert sum(6 - degrees[x] for x in vertices) == 12

    edge_to_faces = {}
    for i, face in enumerate(faces):
        for j in range(3):
            edge = frozenset((face[j], face[(j + 1) % 3]))
            edge_to_faces.setdefault(edge, []).append(i)
    dual = {i: set() for i in range(len(faces))}
    for incident in edge_to_faces.values():
        dual[incident[0]].add(incident[1])
        dual[incident[1]].add(incident[0])
    reached, stack = set(), [0]
    while stack:
        i = stack.pop()
        if i not in reached:
            reached.add(i)
            stack.extend(dual[i] - reached)
    assert len(reached) == len(faces)

    for x in vertices:
        link = {}
        for face in faces:
            if x not in face:
                continue
            i = face.index(x)
            a, b = face[(i + 1) % 3], face[(i + 2) % 3]
            link.setdefault(a, set()).add(b)
            link.setdefault(b, set()).add(a)
        assert set(link) == {y for e in edges if x in e for y in e if y != x}
        assert all(len(nbrs) == 2 for nbrs in link.values())
        start = next(iter(link))
        seen, previous, current = {start}, start, next(iter(link[start]))
        while current != start:
            assert current not in seen
            seen.add(current)
            following = next(y for y in link[current] if y != previous)
            previous, current = current, following
        assert seen == set(link)


def is_prime(faces, v):
    facial = {frozenset(f) for f in faces}
    adj = {a: set() for a in range(1, v + 1)}
    for a, b, c in faces:
        adj[a].update((b, c))
        adj[b].update((a, c))
        adj[c].update((a, b))
    triangles = {
        frozenset((a, b, c))
        for a, b, c in combinations(range(1, v + 1), 3)
        if b in adj[a] and c in adj[a] and c in adj[b]
    }
    return triangles == facial


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plantri", required=True)
    parser.add_argument("--clers-src", required=True)
    parser.add_argument("--clers-commit", required=True)
    parser.add_argument("--atlas-root", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    sys.path.insert(0, args.clers_src)
    from clers import decode, official_unoriented_name

    census = {}
    for v, expected in EXPECTED_TOTALS.items():
        run = subprocess.run(
            [args.plantri, "-a", str(v)],
            check=True,
            text=True,
            capture_output=True,
        )
        lines = [line for line in run.stdout.splitlines() if line.strip()]
        assert len(lines) == expected, (v, len(lines), expected)
        accepted = []
        for line in lines:
            rows = rotations(line)
            if max(map(len, rows)) > 6:
                continue
            faces = faces_from_rotations(rows)
            validate(faces, v)
            name = official_unoriented_name(faces)
            canonical = decode(name, verify=True)
            validate(canonical, v)
            assert official_unoriented_name(canonical) == name
            assert official_unoriented_name(faces) == name
            netcode = ";".join(",".join(map(str, face)) for face in canonical)
            accepted.append((name, is_prime(canonical, v), netcode))
        names = [name for name, _, _ in accepted]
        assert len(names) == len(set(names))
        census[v] = accepted
        print(
            f"v={v}: plantri={len(lines)}  maxdeg<=6={len(accepted)}  "
            f"prime={sum(prime for _, prime, _ in accepted)}  "
            f"nonprime={sum(not prime for _, prime, _ in accepted)}"
        )

    frozen = set()
    with open(os.path.join(args.atlas_root, "data", "nets_v4_14.txt")) as source:
        for line in source:
            name = line.split()[0]
            if (len(name) + 4) // 2 <= 10:
                frozen.add(name)
    measured = {
        name
        for rows in census.values()
        for name, prime, _ in rows
        if prime
    }
    assert measured == frozen, (
        f"prime mismatch: missing={sorted(frozen - measured)}, "
        f"extra={sorted(measured - frozen)}"
    )
    print(f"prime subset matches data/nets_v4_14.txt exactly ({len(frozen)} names)")
    digest = hashlib.sha256(
        "".join(
            f"v{v}{name}\n"
            for v, rows in sorted(census.items())
            for name, _, _ in sorted(rows)
        ).encode()
    ).hexdigest()
    print(f"canonical-name sha256={digest}")
    if args.output:
        counts = " ".join(
            f"v{v}={len(rows)}" for v, rows in sorted(census.items())
        )
        with open(args.output, "w") as output:
            output.write("# All simple sphere triangulations with 4<=v<=10 "
                         "and maximum vertex degree <=6.\n")
            output.write("# plantri 5.8 (2026-03-04); "
                         "https://users.cecs.anu.edu.au/~bdm/plantri/\n")
            output.write(f"# clers commit {args.clers_commit}\n")
            output.write("# generated by: python3 notes/all-v10-check.py "
                         "--plantri PLANTRI --clers-src CLERS/src "
                         f"--clers-commit {args.clers_commit} "
                         "--atlas-root . --output data/nets_all_v4_10.txt\n")
            output.write(f"# counts: {counts}; total="
                         f"{sum(len(rows) for rows in census.values())}\n")
            output.write(f"# canonical-name sha256: {digest}\n")
            output.write("# columns: v class clers netcode\n")
            for v, rows in sorted(census.items()):
                for name, prime, netcode in sorted(rows):
                    label = "prime" if prime else "nonprime"
                    output.write(f"{v} {label} {name} {netcode}\n")
        print(f"wrote {args.output}")
    print(
        "all checks passed; census total="
        + str(sum(len(rows) for rows in census.values()))
    )


if __name__ == "__main__":
    main()
