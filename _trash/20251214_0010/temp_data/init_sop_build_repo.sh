#!/usr/bin/env bash
# init_sop_build_repo.sh
# One-time (or occasional) script to create the standard SOP_Build folder structure.

set -e

echo "Initializing SOP_Build folder structure..."

# Core config + code
mkdir -p config

mkdir -p src/powershell
mkdir -p src/python

# Inputs
mkdir -p inputs/ppt_sample
mkdir -p inputs/raw
mkdir -p inputs/ready_base
mkdir -p inputs/ready_enh

# Outputs (core + quiz/FAQ)
mkdir -p outputs/images
mkdir -p outputs/story
mkdir -p outputs/players
mkdir -p outputs/quiz
mkdir -p outputs/faq

# Quiz/FAQ templates + specs (non-generated)
mkdir -p quiz_faq/templates
mkdir -p quiz_faq/specs

# Login-related files (config + docs)
mkdir -p login/config
mkdir -p login/docs

# Logs
mkdir -p logs/ppt_export
mkdir -p logs/raw_to_ready
mkdir -p logs/build_player

# Extra utility folders
mkdir -p temp_data
mkdir -p build_checklists

# Docs
mkdir -p docs

# Create stub files if they don't exist
if [ ! -f README.md ]; then
  cat > README.md <<'EOF'
# SOP_Build

This repo contains the canonical tools and process for building SOP players
from PowerPoint decks:

> PPT → PNG → RAW → READY → story.json → SOP player HTML

It is not the public training site. It is the "engine room" used to:
- Export slides and map data from PowerPoint (PowerShell).
- Enrich RAW files into READY inputs.
- Build story.json and SOP player HTML (Python).
- Prepare Quiz and FAQ content, and keep login-related configs together.

See `SOP_Build_Standard_v1.md` for the full folder and process standard.
EOF
  echo "Created README.md stub."
else
  echo "README.md already exists, leaving it unchanged."
fi

if [ ! -f SOP_Build_Standard_v1.md ]; then
  cat > SOP_Build_Standard_v1.md <<'EOF'
# SOP_Build – Folder & Process Standard (v1)

(Placeholder)
Replace this file with the full SOP_Build_Standard_v1.md content
describing the agreed folder structure, naming conventions, and build flow.
EOF
  echo "Created SOP_Build_Standard_v1.md stub."
else
  echo "SOP_Build_Standard_v1.md already exists, leaving it unchanged."
fi

if [ ! -f docs/CHANGELOG.md ]; then
  cat > docs/CHANGELOG.md <<'EOF'
# CHANGELOG – SOP_Build

- [YYYY-MM-DD HH:MM] Repo initialized.
EOF
  echo "Created docs/CHANGELOG.md stub."
else
  echo "docs/CHANGELOG.md already exists, leaving it unchanged."
fi

echo "Done. SOP_Build structure is in place."
