#!/usr/bin/env bash
set -euo pipefail

# export_outputs_bundle_for_stage_v1_1.sh
# Version: SOP_BUILD_EXPORT_OUTPUTS_v1.1
# Built: 2025-12-13 America/New_York
# Owner: Subi
#
# Creates a zip containing docs/outputs/ (as outputs/ inside the zip)
# Excludes any Prev folders anywhere under outputs/.

TZ=${TZ:-America/New_York}
STAMP=$(TZ="$TZ" date +%Y%m%d_%H%M)

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SRCDOCS="$ROOT/docs"
SRCOUT="$SRCDOCS/outputs"

OUTDIR="$ROOT/rep_new"
ZIP="$OUTDIR/SOPB_outputs_for_SOP_Stage_${STAMP}.zip"

if [ ! -d "$SRCOUT" ]; then
  echo "ERROR: docs/outputs/ not found. Build first."
  exit 2
fi

mkdir -p "$OUTDIR"

# Zip from docs/ so the zip contains "outputs/..." at top level
cd "$SRCDOCS"

zip -rq "$ZIP" outputs \
  -x "outputs/**/Prev/*" "outputs/**/Prev/**"

echo "Created: $ZIP"
