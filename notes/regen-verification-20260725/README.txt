source: the 2026-07-25 working tree (oct-core exemplars + census completion; commit hash recorded in the commit that carries this file)
run A: bash regen_personal.sh   # exit 0
       find site/personal -type f -exec shasum -a 256 {} + | sort -k2 > site_manifest_A.txt
run B: bash regen_personal.sh   # exit 0, immediately after
       find site/personal -type f -exec shasum -a 256 {} + | sort -k2 > site_manifest_B.txt
70e8156408b89cc979f38f3a65bb7e722fe76584827f22c6c4315a309e1f6f3a  notes/regen-verification-20260725/site_manifest_A.txt
70e8156408b89cc979f38f3a65bb7e722fe76584827f22c6c4315a309e1f6f3a  notes/regen-verification-20260725/site_manifest_B.txt
file count: 20474
diff A B: EMPTY (byte-identical builds)
