#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./builder/scripts/mk_outputs_tree.sh
#   ./builder/scripts/mk_outputs_tree.sh LineEnt2   # (optional) also creates story/<SOP_ID>/

SOP_ID="${1:-}"

ROOT="docs/outputs"

mkdir -p \
  "$ROOT/players" \
  "$ROOT/images" \
  "$ROOT/faq" \
  "$ROOT/quiz" \
  "$ROOT/story"

# Optional: create story/<SOP_ID>/ and images/<SOP_ID>/
if [[ -n "$SOP_ID" ]]; then
  mkdir -p \
    "$ROOT/story/$SOP_ID" \
    "$ROOT/images/$SOP_ID"
fi

echo "OK: created outputs tree under $ROOT"
if [[ -n "$SOP_ID" ]]; then
  echo "OK: created SOP folders: $ROOT/story/$SOP_ID and $ROOT/images/$SOP_ID"
fi
