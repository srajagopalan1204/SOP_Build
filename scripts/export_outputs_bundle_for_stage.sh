#!/usr/bin/env bash
set -euo pipefail

# export_outputs_bundle_for_stage.sh
# Version: SOP_BUILD_EXPORT_OUTPUTS_v1.0
# Built: 2025-12-13 America/New_York
#
# Creates a zip containing outputs/ (excluding any Prev folders).

TZ=${TZ:-America/New_York}
STAMP=$(TZ="$TZ" date +%Y%m%d_%H%M)

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
OUTDIR="$ROOT/rep_new"
ZIP="$OUTDIR/SOPB_outputs_for_SOP_Stage_${STAMP}.zip"

if [ ! -d "$ROOT/outputs" ]; then
  echo "ERROR: outputs/ not found. Build first."
  exit 2
fi

mkdir -p "$OUTDIR"
cd "$ROOT"

zip -rq "$ZIP" outputs \
  -x "outputs/**/Prev/*" "outputs/**/Prev/**"

echo "Created: $ZIP"
