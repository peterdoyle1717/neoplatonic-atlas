# Build-twice verification — 2026-07-26 (front-page archive pointers)

Tree: the archive-pointers round (front page gains the "Archives &
code" line: atlas concept DOI 21367249, primes concept DOI 19761389,
proof-software frozen DOI 21609862, GitHub).

Two ./regen_personal.sh runs from the same committed data, per-file
sha256 manifests of site/personal after each:

    sha256(site_manifest_A.txt) = 99c1ee415657f22718a1be35741dd6b06ad026a179ea111232e627024f6f4ae5
    sha256(site_manifest_B.txt) = 99c1ee415657f22718a1be35741dd6b06ad026a179ea111232e627024f6f4ae5
    files: 20,492   diff A B: EMPTY

(Run A's first log redirect failed before the directory existed; the
fallback created the directory and ran regen A with its log. Both
logs present.)
