#!/usr/bin/env bash
set -euo pipefail

# publish_test_serve.sh
# Version: SOP_BUILD_PUBLISH_TEST_SERVE_v1.0
# Built: 2025-12-13 America/New_York
#
# Purpose:
#   Serve publish_test/docs on port 8080 for local browser testing.
#
# Usage:
#   bash scripts/publish_test_serve.sh
#
# Stop:
#   Ctrl+C

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
DOCS="$ROOT/publish_test/docs"

if [ ! -d "$DOCS" ]; then
  echo "ERROR: missing $DOCS"
  echo "Run: bash scripts/init_publish_test_tree.sh"
  exit 2
fi

echo "Serving: $DOCS"
echo "URL: http://localhost:8080/"
python -m http.server 8080 --directory "$DOCS"
