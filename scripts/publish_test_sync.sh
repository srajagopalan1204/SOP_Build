#!/usr/bin/env bash
set -euo pipefail

# publish_test_sync.sh
# Version: SOP_BUILD_PUBLISH_TEST_SYNC_v1.0
# Built: 2025-12-13 America/New_York
#
# Purpose:
#   Sync SOP_Build/outputs (factory truth) into publish_test/docs/outputs
#   so you can test locally exactly like GitHub Pages (/docs).
#
# Usage:
#   bash scripts/publish_test_sync.sh

TZ=${TZ:-America/New_York}
STAMP=$(TZ="$TZ" date +%Y%m%d_%H%M)

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SRC="$ROOT/outputs"
DST="$ROOT/publish_test/docs/outputs"
BACK="$ROOT/publish_test/Prev_sync/$STAMP"

if [ ! -d "$SRC" ]; then
  echo "ERROR: missing $SRC"
  echo "Run: bash scripts/init_publish_test_tree.sh"
  exit 2
fi

mkdir -p "$ROOT/publish_test/docs" "$ROOT/publish_test/Prev_sync"

# Backup existing publish-test outputs (if any)
if [ -d "$DST" ]; then
  mkdir -p "$BACK"
  cp -a "$DST" "$BACK/outputs"
  echo "Backed up previous publish_test outputs to: $BACK/outputs"
fi

# Recreate destination and sync
rm -rf "$DST"
mkdir -p "$DST"

if command -v rsync >/dev/null 2>&1; then
  # --delete is safe because DST was just removed/recreated
  rsync -a "$SRC"/ "$DST"/
else
  # Fallback if rsync is missing
  cp -a "$SRC"/. "$DST"/
fi

echo "OK: Synced:"
echo "  From: $SRC"
echo "  To:   $DST"
