#!/usr/bin/env bash
set -euo pipefail

# export_one_sop_bundle_v1_0.sh
# Version: SOP_BUILD_EXPORT_ONE_SOP_v1.0
# Built: 2025-12-14 America/New_York
# Owner: Subi

TZ=${TZ:-America/New_York}
STAMP=$(TZ="$TZ" date +%Y%m%d_%H%M)

if [ $# -lt 1 ]; then
  echo "USAGE: bash export_one_sop_bundle_v1_0.sh LineEnt"
  exit 2
fi

SOP="$1"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SRCDOCS="$ROOT/docs"
OUTDIR="$ROOT/rep_new"
ZIP="$OUTDIR/SOPB_${SOP}_for_STAGE_${STAMP}.zip"

# Paths inside docs/outputs
PLAYER="outputs/players/${SOP}_player.html"
STORY="outputs/story/${SOP}/story.json"
IMGDIR="outputs/images/${SOP}"
FAQDIR="outputs/faq"
QUIZDIR="outputs/quiz"

mkdir -p "$OUTDIR"
cd "$SRCDOCS"

# Validate existence of key items (player + story + image dir)
[ -f "$PLAYER" ] || { echo "Missing $SRCDOCS/$PLAYER"; exit 2; }
[ -f "$STORY" ]  || { echo "Missing $SRCDOCS/$STORY"; exit 2; }
[ -d "$IMGDIR" ] || { echo "Missing $SRCDOCS/$IMGDIR"; exit 2; }

# Zip only the SOP-specific pieces + faq/quiz (we include whole faq/quiz dirs because they are shared)
zip -rq "$ZIP" \
  "$PLAYER" \
  "$STORY" \
  "$IMGDIR" \
  "$FAQDIR" \
  "$QUIZDIR" \
  -x "outputs/**/Prev/*" "outputs/**/Prev/**"

echo "Created: $ZIP"
