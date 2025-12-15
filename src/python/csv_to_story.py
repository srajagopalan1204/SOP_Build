#!/usr/bin/env python3
"""
csv_to_story.py
Version: v1c_subi_20251213_2315 (America/New_York)
Owner: Subi

What changed vs v1b:
- Normalize image paths so they do NOT start with "/../" (which browsers normalize to "/images/...").
  We now emit "../images/..." when the CSV provides "outputs/images/..." or "/outputs/images/...".
- Normalize FAQ_Loc / Quiz_Loc so "outputs/faq" becomes "faq" (player will resolve to ../faq/...).
- Added --version flag output (kept compatible with your CLI).
"""

import argparse, csv, json, os
from datetime import datetime, timezone

VERSION = "v1c_subi_20251213_2315"  # America/New_York label

def truthy(v):
    return str(v).strip().lower() in {"1", "y", "yes", "true", "start", "start_here"}

def _norm_slashes(s: str) -> str:
    return (s or "").replace("\\", "/")

def normalize_asset_loc(loc: str) -> str:
    """
    Convert CSV locs like:
      "outputs/faq"  -> "faq"
      "/outputs/faq" -> "faq"
      "faq"          -> "faq"
      ""             -> ""
    """
    loc = _norm_slashes(loc).strip()
    loc = loc.lstrip("/")  # remove leading /
    if loc.startswith("outputs/"):
        loc = loc[len("outputs/"):]
    return loc.strip("/")

def normalize_image_path(image_full: str) -> str:
    """
    We want image paths that work when the player is served at:
      /outputs/players/<SOP>_player.html
    and images are at:
      /outputs/images/<SOP>/<file>.png

    Best portable form is relative from players -> images:
      ../images/<SOP>/<file>.png

    Also fixes legacy "/../images/..." by removing the leading slash.
    """
    p = _norm_slashes(image_full).strip()

    # Fix the exact bad pattern you hit: "/../images/..." => "../images/..."
    if p.startswith("/../"):
        return p[1:]

    # Convert absolute or root-ish outputs paths into relative-from-players:
    # "/outputs/images/LineEnt/S000.png" => "../images/LineEnt/S000.png"
    if p.startswith("/outputs/"):
        return "../" + p[len("/outputs/"):]

    # "outputs/images/LineEnt/S000.png" => "../images/LineEnt/S000.png"
    if p.startswith("outputs/"):
        return "../" + p[len("outputs/"):]

    # Already relative (../images/...) or something else; keep as-is
    return p

def build_story(csv_path, sop_id):
    frames = []
    start_code = None

    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            code = (row.get("Code") or "").strip()
            if not code:
                code = (row.get("SlideIndex") or "START").strip()

            title = (row.get("Title") or code).strip()
            title = title.replace("_x000B_", " ").strip()

            sop_path = _norm_slashes(row.get("SOP_path") or "").strip().strip("/")
            img_leaf = _norm_slashes(row.get("Image_sub_url") or "").strip().lstrip("/")

            image_full = ""
            if img_leaf:
                # If already looks like SOP/... keep absolute web style.
                if img_leaf.startswith("SOP/") or img_leaf.startswith("/SOP/"):
                    image_full = "/" + img_leaf.lstrip("/")
                elif sop_path:
                    image_full = "/" + sop_path + "/" + img_leaf
                else:
                    image_full = "/" + img_leaf

                while "//" in image_full:
                    image_full = image_full.replace("//", "/")

            image_full = normalize_image_path(image_full)

            q = (row.get("Deci_Question") or "").strip()
            choices = []
            for kcode, klabel in [("Next1_Code","Desc_Next1"), ("Next2_Code","Desc_Next2")]:
                nxt = (row.get(kcode) or "").strip()
                lbl = (row.get(klabel) or "").strip()
                if nxt:
                    choices.append({"to": nxt, "label": lbl or nxt})

            frame = {
                "sop_id": sop_id,
                "frame_code": code,
                "title": title,
                "image": image_full,
                "decision_question": q,
                "choices": choices,
                "narr1": (row.get("Narr1") or "").strip(),
                "narr2": (row.get("Narr2") or "").strip(),
                "narr3": (row.get("Narr3") or "").strip(),
                "uap_url": (row.get("UAP_URL") or "").strip(),
                "uap_label": (row.get("UAP_Label") or "").strip(),

                # Normalize these so player won’t create /outputs/outputs/...
                "FAQ_Loc": normalize_asset_loc(row.get("FAQ_Loc") or ""),
                "FAQ_File": (row.get("FAQ_File") or "").strip(),
                "FAQ_Label": (row.get("FAQ_Label") or "").strip(),
                "Quiz_Loc": normalize_asset_loc(row.get("Quiz_Loc") or ""),
                "Quiz_File": (row.get("Quiz_File") or "").strip(),
                "Quiz_Label": (row.get("Quiz_Label") or "").strip(),

                "meta": {
                    "entity": (row.get("Entity") or "Palco").strip(),
                    "function": (row.get("Function") or "Service").strip(),
                    "subentity": (row.get("SubEntity") or "").strip()
                }
            }

            frames.append(frame)

            if start_code is None and truthy(row.get("Start_Here","")):
                start_code = code

    if start_code is None and frames:
        start_code = frames[0]["frame_code"]

    return {"sop_id": sop_id, "start_code": start_code, "frames": frames}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", action="store_true", help="Print version and exit")
    ap.add_argument("--csv", required=False)
    ap.add_argument("--sop-id", required=False)
    ap.add_argument("--out", required=False)
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    if args.version:
        print(f"csv_to_story.py {VERSION}")
        return

    if not (args.csv and args.sop_id and args.out):
        ap.error("--csv, --sop-id, and --out are required (unless --version).")

    story = build_story(args.csv, args.sop_id)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %z")
    msg = f"[{ts}] {VERSION} Wrote {args.out} with {len(story.get('frames', []))} frames. Start={story.get('start_code')}"
    print(msg)

    if args.log:
        os.makedirs(os.path.dirname(args.log), exist_ok=True)
        with open(args.log, "w", encoding="utf-8") as lf:
            lf.write(msg + "\n")

if __name__ == "__main__":
    main()
