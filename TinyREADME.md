# SOP_Build

This repo contains the **canonical tools and process** for building SOP players from
PowerPoint decks:

> PPT → PNG → RAW → READY → story.json → SOP player HTML

It is **not** the public training site. It is the “engine room” used to:
- Export slides and map data from PowerPoint (PowerShell).
- Enrich RAW files into READY inputs.
- Build `story.json` and SOP player HTML (Python).
- Maintain a clean, repeatable process across SE, Palco, and Specialty.

To understand the **folder structure, naming conventions, and standard build flow**,  
read:

- `SOP_Build_Standard_v1.md`  ← the master process document
- `docs/CHANGELOG.md`         ← history of changes and enhancements

Anything that does not yet fit into the standard structure should go into:

- `temp_data/` (scratch space only, safe to clean)
