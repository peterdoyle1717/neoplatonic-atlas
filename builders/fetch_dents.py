#!/usr/bin/env python3
"""Fetch the old atlas's 26 dented-realization GLBs into the owning
nets' directories (nets/<id>/dent_v<k>.glb) and record them in
net.json (artifacts.dents). Dented realizations are data about a net,
so they live in the net's own record dir (PD)."""
import csv, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
OUT = os.path.join(TOP, "site", "personal")
sys.path.insert(0, HERE)
from views import net_id

def main():
    got = miss = 0
    with open(os.path.join(TOP, "data", "dented_old.tsv")) as f:
        for r in csv.DictReader(f, delimiter='\t'):
            name, k, url = r['name'], r['k'], r['url']
            V = (len(name) + 4) // 2
            nid = net_id(V, name)
            netdir = os.path.join(OUT, "nets", nid)
            recp = os.path.join(netdir, "net.json")
            if not os.path.exists(recp):
                print(f"no record for {name} (v{V}) - skipping")
                miss += 1
                continue
            dst = os.path.join(netdir, f"dent_v{k}.glb")
            if not os.path.exists(dst):
                urllib.request.urlretrieve(url, dst)
            rec = json.load(open(recp))
            dents = set(rec.get("artifacts", {}).get("dents", []))
            dents.add(int(k))
            rec.setdefault("artifacts", {})["dents"] = sorted(dents)
            with open(recp, "w") as fh:
                json.dump(rec, fh, indent=1)
            got += 1
    print(f"dents: {got} fetched/recorded, {miss} missing records")

if __name__ == "__main__":
    main()
