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
bash scripts/publish_test_sync.sh
bash scripts/publish_test_serve.sh
