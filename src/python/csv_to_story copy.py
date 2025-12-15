#!/usr/bin/env python3
"""
csv_to_story.py

Template Version: CSV_TO_STORY_v20251213_0950_ET
Generated/Stamped: 2025-12-13 09:50 America/New_York
Owner: Subi
Purpose: Convert mk_tw_in CSV to story.json for SOP Player.

Notes:
- This script DOES NOT invent narr1/narr2/narr3 text; it copies what’s in the CSV.
- Any “Slide S000...” prefixes are coming from the CSV creator upstream.
"""

import argparse, csv, json, os

TEMPLATE_VERSION = "CSV_TO_STORY_v20251213_0950_ET"
STAMP_ET = "2025-12-13 09:50 America/New_York"

def truthy(v):
    return str(v).strip().lower() in {"1", "y", "yes", "true", "start", "start_here"}

def clean_text(s: str) -> str:
    """Normalize PPT artifacts and whitespace."""
    if s is None:
        return ""
    s = str(s)
    s = s.replace("_x000B_", "\n")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s.strip()

def build_story(csv_path, sop_id):
    frames = []
    start_code = None

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for _, row in enumerate(reader):
            code = clean_text(row.get("Code"))
            if not code:
                code = clean_text(row.get("SlideIndex")) or "START"

            title = clean_text(row.get("Title")) or code

            sop_path = clean_text(row.get("SOP_path")).strip("/")
            img_leaf = clean_text(row.get("Image_sub_url")).lstrip("/")

            image_full = ""
            if img_leaf:
                if img_leaf.startswith("SOP/") or img_leaf.startswith("/SOP/"):
                    image_full = "/" + img_leaf.lstrip("/")
                elif sop_path:
                    image_full = "/" + sop_path + "/" + img_leaf
                else:
                    image_full = "/" + img_leaf

                while "//" in image_full:
                    image_full = image_full.replace("//", "/")

            q = clean_text(row.get("Deci_Question"))
            choices = []
            for kcode, klabel in [("Next1_Code", "Desc_Next1"), ("Next2_Code", "Desc_Next2")]:
                nxt = clean_text(row.get(kcode))
                lbl = clean_text(row.get(klabel))
                if nxt:
                    choices.append({"to": nxt, "label": lbl or nxt})

            frame = {
                "sop_id": sop_id,
                "frame_code": code,
                "title": title,
                "image": image_full,
                "decision_question": q,
                "choices": choices,
                "narr1": clean_text(row.get("Narr1")),
                "narr2": clean_text(row.get("Narr2")),
                "narr3": clean_text(row.get("Narr3")),
                "uap_url": clean_text(row.get("UAP_URL")),
                "uap_label": clean_text(row.get("UAP_Label")),
                "FAQ_Loc": clean_text(row.get("FAQ_Loc")),
                "FAQ_File": clean_text(row.get("FAQ_File")),
                "FAQ_Label": clean_text(row.get("FAQ_Label")),
                "Quiz_Loc": clean_text(row.get("Quiz_Loc")),
                "Quiz_File": clean_text(row.get("Quiz_File")),
                "Quiz_Label": clean_text(row.get("Quiz_Label")),
                "meta": {
                    "entity": clean_text(row.get("Entity")) or "Palco",
                    "function": clean_text(row.get("Function")) or "Service",
                    "subentity": clean_text(row.get("SubEntity")),
                },
            }

            frames.append(frame)

            if start_code is None and truthy(row.get("Start_Here", "")):
                start_code = code

    if start_code is None and frames:
        start_code = frames[0]["frame_code"]

    return {
        "sop_id": sop_id,
        "start_code": start_code,
        "frames": frames,
        "_template_meta": {
            "template_version": TEMPLATE_VERSION,
            "stamp_et": STAMP_ET,
            "owner": "Subi"
        }
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--sop-id", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    story = build_story(args.csv, args.sop_id)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    msg = (
        f"[{TEMPLATE_VERSION}] Wrote {args.out} "
        f"({len(story.get('frames', []))} frames) Start={story.get('start_code')} "
        f"Stamp={STAMP_ET}"
    )
    print(msg)
    if args.log:
        with open(args.log, "w", encoding="utf-8") as lf:
            lf.write(msg + "\n")

if __name__ == "__main__":
    main()
