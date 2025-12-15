#!/usr/bin/env bash
set -euo pipefail

# backup_repo_zip.sh
# Version: v1.0
# Built: 2025-12-13 America/New_York
# Purpose: Create a timestamped repo backup ZIP in the repo root.

TZ="America/New_York"
ts="$(date +'%Y%m%d_%H%M')"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
zip_name="SOP_Build_backup_${ts}.zip"
zip_path="${repo_root}/${zip_name}"

echo "Repo root : ${repo_root}"
echo "ZIP path  : ${zip_path}"

cd "${repo_root}"

# Don't include .git or previous zips in the backup.
# (We keep docs/outputs and outputs because they are useful provenance.)
exclude_args=(
  "-x" ".git/*"
  "-x" "*.zip"
  "-x" "__pycache__/*"
  "-x" "**/__pycache__/*"
  "-x" ".pytest_cache/*"
  "-x" "**/.pytest_cache/*"
)

if command -v zip >/dev/null 2>&1; then
  echo "Using system zip..."
  zip -r "${zip_path}" . "${exclude_args[@]}"
else
  echo "zip not found; using Python zipfile fallback..."
  python - <<PY
import os, zipfile, fnmatch
repo = ${repo_root!r}
outp = ${zip_path!r}
ex = [
  ".git/*",
  "*.zip",
  "__pycache__/*",
  "**/__pycache__/*",
  ".pytest_cache/*",
  "**/.pytest_cache/*",
]
def excluded(path):
  rel = os.path.relpath(path, repo).replace("\\","/")
  for pat in ex:
    if fnmatch.fnmatch(rel, pat):
      return True
  return False

with zipfile.ZipFile(outp, "w", compression=zipfile.ZIP_DEFLATED) as z:
  for root, dirs, files in os.walk(repo):
    # skip .git quickly
    if os.path.relpath(root, repo).replace("\\","/").startswith(".git"):
      dirs[:] = []
      continue
    for f in files:
      p = os.path.join(root, f)
      if excluded(p):
        continue
      rel = os.path.relpath(p, repo)
      z.write(p, rel)
print("Wrote:", outp)
PY
fi

echo "DONE: ${zip_name}"
ls -lh "${zip_path}" || true
