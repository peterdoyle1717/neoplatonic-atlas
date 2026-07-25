# Build-twice verification — 2026-07-25 (tet-assembly round)

Tree: the tet-assembly completion commit (11/8/8 non-prime; 2,251 nets).

Procedure: `./regen_personal.sh` run twice from the same committed
data (full wipe + rebuild each time; consumer tier, numpy-only), then
a per-file sha256 manifest of `site/personal/` after each run:

    (cd site/personal && find . -type f -print0 | sort -z \
       | xargs -0 shasum -a 256) > site_manifest_{A,B}.txt

Result: manifests byte-identical.

    sha256(site_manifest_A.txt) = 51982f0505566a29f09cb05214ead63b75ad5b788c1eb37f64d4a046c250ac8c
    sha256(site_manifest_B.txt) = 51982f0505566a29f09cb05214ead63b75ad5b788c1eb37f64d4a046c250ac8c
    files: 20,492   diff A B: EMPTY

(An earlier pair at this round's first tree, sha 477dcacc…, was
superseded when the gallery blurb was rescoped to the enumerated
range after the gate review; the manifests here are from the final
tree.)

Non-prime gallery after regen: 11 / 8 / 8 (tet assemblies / oct
stacks / prime-core+tets). Logs: regen_A.log, regen_B.log (run B tail:
"rendered 2251 pages").
