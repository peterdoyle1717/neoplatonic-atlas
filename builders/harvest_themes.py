#!/usr/bin/env python3
"""One-time harvest of the old deployed atlas's themed galleries
(math.dartmouth.edu/~doyle/docs/atlas/gallery/*.html, saved locally)
into committed data files:

  data/theme_<g>.txt      net names, document order
  data/dented_old.tsv     name, dented-vertex k, old glb URL

Usage: python3 builders/harvest_themes.py <dir-with-old_<g>.html>
"""
import os, re, sys

TOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEMES = ("bucky", "phyllo31", "phyllo22", "phyllo41", "phyllo51",
          "flops", "nonprime", "preapproved", "small", "dented")
BASE = "https://math.dartmouth.edu/~doyle/docs/atlas"


def names_in_order(html):
    out, seen = [], set()
    for m in re.finditer(r'\b([ABCDE]{8,})\b', html):
        nm = m.group(1)
        if nm not in seen:
            seen.add(nm)
            out.append(nm)
    return out


def main(srcdir):
    for g in THEMES:
        p = os.path.join(srcdir, f"old_{g}.html")
        if not os.path.exists(p):
            print(f"missing {p}")
            continue
        html = open(p).read()
        names = names_in_order(html)
        with open(os.path.join(TOP, "data", f"theme_{g}.txt"), "w") as f:
            f.write('\n'.join(names) + '\n')
        print(f"theme_{g}.txt: {len(names)}")
        if g == "dented":
            rows = []
            for m in re.finditer(
                    r'src="\.\./glb/dented/(dented_([ABCDE]+)_v(\d+)\.glb)"',
                    html):
                rows.append((m.group(2), m.group(3),
                             f"{BASE}/glb/dented/{m.group(1)}"))
            with open(os.path.join(TOP, "data", "dented_old.tsv"), "w") as f:
                f.write("name\tk\turl\n")
                for r in rows:
                    f.write('\t'.join(r) + '\n')
            print(f"dented_old.tsv: {len(rows)}")


if __name__ == "__main__":
    main(sys.argv[1])
