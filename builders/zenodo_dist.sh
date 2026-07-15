#!/bin/bash
# Package the atlas + create a Zenodo DRAFT with reserved DOI + upload.
# NEVER prints the token. Does NOT publish.
set -e
ATLAS=/Users/doyle/Dropbox/neo/atlas2
STAGE="${ATLAS}/dist"
/bin/rm -rf "$STAGE"; mkdir -p "$STAGE"

# 1. aggregate records
python3 - <<'PYEOF'
import json, os
NETS = "/Users/doyle/Dropbox/neo/atlas2/site/personal/nets"
out = "/Users/doyle/Dropbox/neo/atlas2/data/atlas_records.jsonl"
n = 0
with open(out, "w") as f:
    for d in sorted(os.listdir(NETS)):
        p = os.path.join(NETS, d, "net.json")
        if os.path.exists(p):
            f.write(json.dumps(json.load(open(p)), separators=(',', ':')) + "\n")
            n += 1
print(f"records: {n}")
PYEOF

# 2. staging
cat > "$STAGE/README.md" <<'REOF'
# The Neoplatonic Atlas

Interactive atlas of neoplatonic solids: unit-equilateral-triangle
polyhedra (6-nets), their ideal and hyperbolic forms, Eisenstein
subdivision families, classifications, symmetry (Conway symbols), and
themed galleries. Fully self-contained (viewer scripts vendored).

To browse: the 3D viewers need HTTP (browsers block local-file model
loading), so run ONE of:
  ./serve.sh            # any system with python3
  serve.command         # macOS: double-click
then open http://localhost:8901/personal/

atlas_records.jsonl is the database: one JSON record per net
(identity, netcode, classification flags, symmetry, Eisenstein
relations, names, notes, artifact inventory).

Regeneration: github.com/peterdoyle1717 (bendprover + atlas builders).
REOF
cat > "$STAGE/serve.sh" <<'SEOF'
#!/bin/sh
cd "$(dirname "$0")" && echo "open http://localhost:8901/personal/" && python3 -m http.server 8901
SEOF
cat > "$STAGE/serve.command" <<'CEOF'
#!/bin/sh
cd "$(dirname "$0")" && echo "open http://localhost:8901/personal/" && python3 -m http.server 8901
CEOF
chmod +x "$STAGE/serve.sh" "$STAGE/serve.command"
/bin/cp "$ATLAS/data/atlas_records.jsonl" "$STAGE/"

# 3. tarball (site copied in via tar to keep the 'personal/' root)
if [ -f "$STAGE/neoplatonic-atlas.tar.gz" ]; then echo "tarball exists, keeping"; else
echo "tarring..."
tar -C "$ATLAS/site" -cf "$STAGE/_site.tar" personal
tar -C "$STAGE" -rf "$STAGE/_site.tar" README.md serve.sh serve.command atlas_records.jsonl
gzip -1 -c "$STAGE/_site.tar" > "$STAGE/neoplatonic-atlas.tar.gz"
/bin/rm "$STAGE/_site.tar"
fi
ls -la "$STAGE/neoplatonic-atlas.tar.gz" | awk '{print "tarball bytes:", $5}'
MD5=$(md5 -q "$STAGE/neoplatonic-atlas.tar.gz")
echo "local md5: $MD5"

# 4. Zenodo draft + reserved DOI (token stays in env)
TOKEN=$(cat ~/.zshrc ~/.zshenv ~/.zprofile 2>/dev/null | grep -i 'zenodo' | grep -oE '=["'"'"']?[A-Za-z0-9._-]+' | head -1 | tr -d '="'"'"'')
if [ -z "$TOKEN" ]; then echo "NO ZENODO TOKEN FOUND"; exit 1; fi
DEP=$(curl -s -X POST "https://zenodo.org/api/deposit/depositions" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"metadata": {"prereserve_doi": true}}')
DEPID=$(echo "$DEP" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
DOI=$(echo "$DEP" | python3 -c "import json,sys; print(json.load(sys.stdin)['metadata']['prereserve_doi']['doi'])")
BUCKET=$(echo "$DEP" | python3 -c "import json,sys; print(json.load(sys.stdin)['links']['bucket'])")
echo "deposition: $DEPID"
echo "RESERVED DOI: $DOI"

# 5. metadata
curl -s -X PUT "https://zenodo.org/api/deposit/depositions/$DEPID" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"metadata": {"title": "The Neoplatonic Atlas", "upload_type": "dataset", "description": "Interactive atlas of neoplatonic solids: unit-equilateral-triangle polyhedra (6-nets), their ideal and hyperbolic forms, Eisenstein subdivision families, classifications, Conway symmetry symbols, and themed galleries. Self-contained: unpack and run serve.sh, then open http://localhost:8901/personal/. atlas_records.jsonl is the per-net database.", "creators": [{"name": "Doyle, Peter"}, {"name": "Ellison, Matthew"}], "license": "cc-zero", "keywords": ["polyhedra", "equilateral triangles", "hyperbolic geometry", "ideal polyhedra", "triangulations"], "prereserve_doi": true}}' > /dev/null
echo "metadata set"

# 6. upload (big)
echo "uploading tarball..."
curl -s -o /dev/null -w "upload http %{http_code}, %{size_upload} bytes, %{time_total}s\n" \
  -H "Authorization: Bearer $TOKEN" \
  --upload-file "$STAGE/neoplatonic-atlas.tar.gz" \
  "$BUCKET/neoplatonic-atlas.tar.gz"
curl -s -o /dev/null -w "records upload http %{http_code}\n" \
  -H "Authorization: Bearer $TOKEN" \
  --upload-file "$STAGE/atlas_records.jsonl" "$BUCKET/atlas_records.jsonl"

# 7. verify checksums server-side
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://zenodo.org/api/deposit/depositions/$DEPID/files" | \
python3 -c "
import json, sys
for f in json.load(sys.stdin):
    print('zenodo file:', f['filename'], f['filesize'], 'md5:', f['checksum'])"
echo "local md5 again: $MD5"
echo "DRAFT ONLY - not published. DOI reserved: $DOI"
