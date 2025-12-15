# SOP Build Checklists v6a (20251213_1311 America/New_York)

Owner: Subi  
Repo: `/workspaces/SOP_Build`  
Scope: End-to-end SOP build in **SOP_Build** (local), promote to **SOP_Stage**, then publish to **Production**.

---

## A) Build a new SOP end-to-end in SOP_Build (Local)

### A0. Pre-flight (one-time per codespace)
- [ ] `cd /workspaces/SOP_Build`
- [ ] `python -V` (confirm Python works)
- [ ] `pip install -r requirements.txt` (only if not already installed)

### A1. Inputs (put them in the right place)
- [ ] Create SOP ID (example: `ShipFB2`) and decide Entity/Function/SubEntity
- [ ] Copy slide PNGs to:
  - [ ] `outputs/images/<SOP_ID>/`  (example: `outputs/images/ShipFB2/`)
- [ ] Create the build CSV (mk_tw_in “READY” file) in:
  - [ ] `outputs/build_in/<SOP_ID>_mk_tw_in_READY_<MMDDYY>_<HHMM>.csv`

### A2. Generate story.json from the READY csv
- [ ] Run:
```bash
python src/python/csv_to_story.py --csv outputs/build_in/<CSV_FILE>.csv --sop-id <SOP_ID> --out outputs/story/<SOP_ID>/story.json --log outputs/logs/<SOP_ID>_csv_to_story.log
```
- [ ] Quick sanity checks:
  - [ ] `start_code` is correct
  - [ ] `image` paths resolve (no double slashes, correct folder)
  - [ ] `narr1/narr2/narr3` are populated correctly (per your rules)

### A3. Build the SOP-specific player HTML
- [ ] Run:
```bash
python src/python/build_player.py --story outputs/story/<SOP_ID>/story.json --out outputs/players/<SOP_ID>_player.html --template templates/SOP_player.html --log outputs/logs/<SOP_ID>_build_player.log
```
- [ ] Confirm the template version header in generated HTML (so “wrong version” doubt is gone)

### A4. Local test (this is the GO/NO-GO gate)
- [ ] Start a local web server from repo root:
```bash
python -m http.server 8080
```
- [ ] Open in browser:
  - [ ] `http://localhost:8080/outputs/players/<SOP_ID>_player.html`
- [ ] Local test checklist:
  - [ ] Images show (and fit vertically; image capped by `max-height`)
  - [ ] Breadcrumbs clickable (jump back + truncates stack)
  - [ ] Hear me = narr1 (TTS only; does NOT auto-show)
  - [ ] Read me = narr2 (pane opens + Close works + Esc works)
  - [ ] Hear more / Read more = narr3 (same behaviors)
  - [ ] UAP button appears only when URL+label exist
  - [ ] FAQ & Quiz buttons open the right pages
  - [ ] Decision buttons/Next behavior correct (2 choices → hide Next, 1 choice → Next relabeled)

### A5. Freeze the local artifact set (for traceability)
- [ ] Copy the “built set” (player + story + logs) to a dated folder:
  - [ ] `outputs/releases/<SOP_ID>/<YYYYMMDD_HHMM>/...`
- [ ] `git status` is clean (or commit the changes with a clear message)

---

## B) Promote from SOP_Build → SOP_Stage (Staging)

Goal: stage mirrors production structure, but is safe for testers/SMEs.

### B1. Copy only what’s needed (minimum footprint)
- [ ] `outputs/players/<SOP_ID>_player.html`
- [ ] `outputs/images/<SOP_ID>/` (all images)
- [ ] `outputs/faq/...` (if used)
- [ ] `outputs/quiz/...` (if used)
- [ ] Any index/menu entries for stage navigation

### B2. Stage test
- [ ] Verify links are correct **in stage paths**
- [ ] Verify external links (UAP) open in a new tab
- [ ] Confirm no “/workspaces/…” leaks inside HTML/JSON

### B3. Stage sign-off packet (short + practical)
- [ ] One message to SMEs:
  - [ ] What SOP is ready
  - [ ] Where to test (stage URL)
  - [ ] What to look for (1–2 bullets)
  - [ ] How to report issues (screenshot + frame code)

---

## C) Publish to Production (after Stage sign-off)

Goal: stable, repeatable, minimal surprises.

### C1. Production-ready checks
- [ ] All SOP links on production landing page work
- [ ] All images load quickly (no missing/typos)
- [ ] Quiz + FAQ pages exist and match links from player
- [ ] Template version matches the accepted template version

### C2. Publish steps
- [ ] Copy stage-approved artifacts into production repo paths
- [ ] Commit with message: `Publish <SOP_ID> vX (YYYYMMDD_HHMM)`
- [ ] Push
- [ ] Validate published URL in a clean browser session

---

## D) Next major milestone (not in scope of today’s publish)

**Quiz response logging / login / tracking** (Render + FastAPI + Postgres):
- [ ] Decide the minimal data to capture (email, SOP_ID, timestamp, score, attempt #)
- [ ] Add POST endpoint + CORS rules
- [ ] Update quiz HTML to submit results + show “Saved OK” message
- [ ] Add a lightweight admin export view (CSV)

---

## Versioning rule (to prevent “wrong file” confusion)
- Every template + generator script must include:
  - Version string (example: `v20251213_1311`)
  - America/New_York timestamp
  - “Owner: Subi” line
