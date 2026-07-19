#!/bin/bash
# Package the atlas + create a Zenodo DRAFT with reserved DOI + upload.
# NEVER prints the token. Does NOT publish.
set -e
ATLAS=/Users/doyle/Dropbox/projects/neo/atlas2
STAGE="${ATLAS}/dist"
# clear staging but keep the big site tarball (step 3 skips re-tarring it)
mkdir -p "$STAGE"
find "$STAGE" -mindepth 1 -maxdepth 1 ! -name 'neoplatonic-atlas.tar.gz' -exec /bin/rm -rf {} +

# 1. aggregate records
python3 - <<'PYEOF'
import json, os
NETS = "/Users/doyle/Dropbox/projects/neo/atlas2/site/personal/nets"
out = "/Users/doyle/Dropbox/projects/neo/atlas2/data/atlas_records.jsonl"
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
  ./serve.sh            # Linux/macOS terminal (needs python3)
  serve.command         # macOS: double-click
  serve.bat             # Windows: double-click
It picks a free local port, prints the address, and opens your
browser at http://127.0.0.1:<port>/personal/ automatically.

atlas_records.jsonl is the database: one JSON record per net
(identity, netcode, classification flags, symmetry, Eisenstein
relations, names, notes, artifact inventory).

Regeneration: github.com/peterdoyle1717 (bendprover + atlas builders).
REOF
/bin/cp "$ATLAS/builders/assets/serve.py" "$STAGE/serve.py"
cat > "$STAGE/serve.sh" <<'SEOF'
#!/bin/sh
cd "$(dirname "$0")" && exec python3 serve.py
SEOF
/bin/cp "$STAGE/serve.sh" "$STAGE/serve.command"
cat > "$STAGE/serve.bat" <<'BEOF'
@echo off
cd /d %~dp0
py serve.py || python serve.py
BEOF
chmod +x "$STAGE/serve.sh" "$STAGE/serve.command" "$STAGE/serve.py"
/bin/cp "$ATLAS/data/atlas_records.jsonl" "$STAGE/"

# 3. tarball (site copied in via tar to keep the 'personal/' root)
if [ -f "$STAGE/neoplatonic-atlas.tar.gz" ]; then echo "tarball exists, keeping"; else
echo "tarring..."
tar -C "$ATLAS/site" -cf "$STAGE/_site.tar" personal
tar -C "$STAGE" -rf "$STAGE/_site.tar" README.md serve.py serve.sh serve.command serve.bat atlas_records.jsonl
gzip -1 -c "$STAGE/_site.tar" > "$STAGE/neoplatonic-atlas.tar.gz"
/bin/rm "$STAGE/_site.tar"
fi
ls -la "$STAGE/neoplatonic-atlas.tar.gz" | awk '{print "tarball bytes:", $5}'
MD5=$(md5 -q "$STAGE/neoplatonic-atlas.tar.gz")
echo "local md5: $MD5"

# database tarball: the primary object (records + tables), tiny
DB="$STAGE/db"; /bin/rm -rf "$DB"; mkdir -p "$DB"
/bin/cp "$ATLAS/data/atlas_records.jsonl" "$DB/"
for t in class_v30 symmetry conway eisenstein themes recognized_v30 icorel_v30 decap_v30 decap_names classics theme_desc; do
  [ -f "$ATLAS/data/$t.tsv" ] && /bin/cp "$ATLAS/data/$t.tsv" "$DB/"
done
/bin/cp "$ATLAS/data/nets_pages.txt" "$DB/" 2>/dev/null || true
cat > "$DB/README.md" <<'DBEOF'
# Neoplatonic Atlas: the database

This is the atlas's primary object: everything the atlas asserts, with
no presentation attached. atlas_records.jsonl holds one JSON record
per net (identity, CLERS name, netcode/face list, classification
flags, Conway symmetry symbol, Eisenstein family relations, common
names, notes, artifact inventory). The TSVs are the census-level
tables the records were stamped from (classification over all 79,349
primes v<=30, symmetry, Conway symbols, Eisenstein lattices, angle
recognition, cap-replacement results, the neoplatonized classics).

The companion site tarball is ONE presentation of this database;
anyone can build another. Regeneration/builders: see the code
repository referenced by the Zenodo record.
DBEOF
tar -C "$STAGE" -czf "$STAGE/neoplatonic-atlas-database.tar.gz" db
DBMD5=$(md5 -q "$STAGE/neoplatonic-atlas-database.tar.gz")
ls -la "$STAGE/neoplatonic-atlas-database.tar.gz" | awk '{print "db tarball bytes:", $5}'
echo "db md5: $DBMD5"

# 4. Zenodo draft + reserved DOI (token from ~/.config/zenodo/token)
TOKEN=$(cat ~/.config/zenodo/token 2>/dev/null)
if [ -z "$TOKEN" ]; then echo "NO ZENODO TOKEN FOUND"; exit 1; fi
DEP=$(curl -s -X POST "https://zenodo.org/api/deposit/depositions" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"metadata": {"prereserve_doi": true}}')
DEPID=$(echo "$DEP" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
DOI=$(echo "$DEP" | python3 -c "import json,sys; print(json.load(sys.stdin)['metadata']['prereserve_doi']['doi'])")
BUCKET=$(echo "$DEP" | python3 -c "import json,sys; print(json.load(sys.stdin)['links']['bucket'])")
echo "deposition: $DEPID"
echo "RESERVED DOI: $DOI"
echo "bucket: $BUCKET"

# 5. metadata
curl -s -X PUT "https://zenodo.org/api/deposit/depositions/$DEPID" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"metadata": {"title": "The Neoplatonic Atlas", "upload_type": "dataset", "description": "Interactive atlas of neoplatonic solids: unit-equilateral-triangle polyhedra (6-nets), their ideal and hyperbolic forms, Eisenstein subdivision families, classifications, Conway symmetry symbols, and themed galleries. Self-contained: unpack and run serve.sh (macOS: serve.command; Windows: serve.bat), which serves the atlas on a free local port and opens your browser. atlas_records.jsonl is the per-net database.", "creators": [{"name": "Doyle, Peter"}, {"name": "Ellison, Matthew"}], "license": "cc-zero", "keywords": ["polyhedra", "equilateral triangles", "hyperbolic geometry", "ideal polyhedra", "triangulations"], "prereserve_doi": true}}' > /dev/null
echo "metadata set"

# 6. upload (big)
echo "uploading tarball..."
curl -s -o /dev/null -w "upload http %{http_code}, %{size_upload} bytes, %{time_total}s\n" \
  -H "Authorization: Bearer $TOKEN" \
  --upload-file "$STAGE/neoplatonic-atlas.tar.gz" \
  "$BUCKET/neoplatonic-atlas.tar.gz"
curl -s -o /dev/null -w "db upload http %{http_code}\n" \
  -H "Authorization: Bearer $TOKEN" \
  --upload-file "$STAGE/neoplatonic-atlas-database.tar.gz" "$BUCKET/neoplatonic-atlas-database.tar.gz"

# 7. verify checksums server-side
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://zenodo.org/api/deposit/depositions/$DEPID/files" | \
python3 -c "
import json, sys
for f in json.load(sys.stdin):
    print('zenodo file:', f['filename'], f['filesize'], 'md5:', f['checksum'])"
echo "local md5 again: $MD5"
echo "DRAFT ONLY - not published. DOI reserved: $DOI"
