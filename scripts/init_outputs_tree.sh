#!/usr/bin/env bash
set -euo pipefail

# init_outputs_tree.sh
# Built: 2025-12-13 America/New_York
# Purpose: Ensure SOP_Build/outputs tree exists (stable publish structure)

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
OUT="$ROOT/outputs"

mkdir -p "$OUT"/{build_in,faq,quiz,players,images,story}
mkdir -p "$OUT/build_in/Prev"
mkdir -p "$OUT/players/Prev"

# Story & images are SOP-name specific; keep base folders only
echo "OK: created/verified outputs tree at: $OUT"
echo "Tree:"
( command -v tree >/dev/null 2>&1 && tree -L 2 "$OUT" ) || ls -R "$OUT" | head -n 60
