source: commit 540ac2a (pre-amend working tree identical to committed builders/ + data/), tree 7cf8fe9a923b2f8c38d759cc6254ee814fa98c0a
run A: bash regen_personal.sh                                # 2026-07-24, exit 0
       find site/personal -type f -exec shasum -a 256 {} + | sort -k2 > site_manifest_A.txt
run B: bash regen_personal.sh                                # immediately after, exit 0
       find site/personal -type f -exec shasum -a 256 {} + | sort -k2 > site_manifest_B.txt
manifest sha256s:
05c183daad697ae54a962dea47269b834b43851ee584c9d99647b76e44ae6b30  notes/regen-verification-20260724/site_manifest_A.txt
05c183daad697ae54a962dea47269b834b43851ee584c9d99647b76e44ae6b30  notes/regen-verification-20260724/site_manifest_B.txt
file count: 20438
diff A B: EMPTY (byte-identical builds)
