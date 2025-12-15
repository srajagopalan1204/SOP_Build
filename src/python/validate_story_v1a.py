#!/usr/bin/env python3
"""
validate_story_v1a.py
Version: v1a
Timestamp (America/New_York): 2025-12-13 13:19

Purpose:
Validate a story.json produced by csv_to_story.py.
Checks:
- JSON structure + required keys
- start_code exists
- frame_code uniqueness
- all choices "to" targets exist
- optional: referenced image files exist on disk
- optional: FAQ/Quiz files exist on disk (if local paths)
- warns on common mojibake sequences (â€œ â€ etc.)
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple


MOJIBAKE_PATTERNS = [
    "â€œ", "â€", "â€™", "â€“", "â€”", "â€¦", "Ã©", "_x000B_"
]


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def norm_repo_path(repo_root: str, p: str) -> str:
    """
    Convert a URL-like path used in story.json (often starting with '/')
    into a filesystem path under repo_root.
    """
    if not p:
        return ""
    p2 = p.strip()

    # If it's a URL, don't convert
    if re.match(r"^https?://", p2, re.IGNORECASE):
        return ""

    # Typical story paths start with "/outputs/..."
    if p2.startswith("/"):
        p2 = p2[1:]

    return os.path.normpath(os.path.join(repo_root, p2))


def file_exists(repo_root: str, p: str) -> bool:
    fs = norm_repo_path(repo_root, p)
    if not fs:
        return True  # treat URLs / empty as "ok"
    return os.path.isfile(fs)


def warn_mojibake(text: str) -> List[str]:
    hits = []
    if not text:
        return hits
    for pat in MOJIBAKE_PATTERNS:
        if pat in text:
            hits.append(pat)
    return hits


def validate_story(story: Dict[str, Any], repo_root: str, check_files: bool) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warns: List[str] = []

    # top-level keys
    for k in ["sop_id", "start_code", "frames"]:
        if k not in story:
            errors.append(f"Missing top-level key: {k}")

    if errors:
        return errors, warns

    frames = story.get("frames", [])
    if not isinstance(frames, list) or len(frames) == 0:
        errors.append("frames must be a non-empty list")
        return errors, warns

    start_code = story.get("start_code")
    codes = []
    seen = set()

    for idx, fr in enumerate(frames):
        code = (fr.get("frame_code") or "").strip()
        if not code:
            errors.append(f"Frame[{idx}] missing frame_code")
            continue
        if code in seen:
            errors.append(f"Duplicate frame_code: {code}")
        seen.add(code)
        codes.append(code)

        # required-ish fields
        if "choices" not in fr or not isinstance(fr["choices"], list):
            errors.append(f"Frame {code}: choices missing or not a list")

        # mojibake warnings (title/narr fields)
        for fld in ["title", "decision_question", "narr1", "narr2", "narr3"]:
            hits = warn_mojibake((fr.get(fld) or ""))
            if hits:
                warns.append(f"Frame {code}: field {fld} contains suspicious text: {', '.join(hits)}")

        # file checks
        if check_files:
            img = (fr.get("image") or "").strip()
            if img and not file_exists(repo_root, img):
                errors.append(f"Frame {code}: image file not found on disk: {img}")

            faq_loc = (fr.get("FAQ_Loc") or "").strip()
            faq_file = (fr.get("FAQ_File") or "").strip()
            if faq_loc and faq_file:
                faq_href = faq_loc.rstrip("/").lstrip("/") + "/" + faq_file.lstrip("/")
                # store as "/<path>" so norm_repo_path works
                if not file_exists(repo_root, "/" + faq_href):
                    warns.append(f"Frame {code}: FAQ file not found on disk: {faq_href}")

            quiz_loc = (fr.get("Quiz_Loc") or "").strip()
            quiz_file = (fr.get("Quiz_File") or "").strip()
            if quiz_loc and quiz_file:
                quiz_href = quiz_loc.rstrip("/").lstrip("/") + "/" + quiz_file.lstrip("/")
                if not file_exists(repo_root, "/" + quiz_href):
                    warns.append(f"Frame {code}: Quiz file not found on disk: {quiz_href}")

    # start_code must exist
    if start_code not in seen:
        errors.append(f"start_code '{start_code}' not found among frame_code values")

    # choice targets must exist
    for fr in frames:
        code = (fr.get("frame_code") or "").strip()
        for cidx, ch in enumerate(fr.get("choices", [])):
            to = (ch.get("to") or "").strip()
            if to and to not in seen:
                errors.append(f"Frame {code}: choice[{cidx}] points to missing frame_code: {to}")

    return errors, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", required=True, help="Path to story.json")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: current dir)")
    ap.add_argument("--check-files", action="store_true", help="Verify images/faq/quiz exist on disk under repo-root")
    args = ap.parse_args()

    story_path = args.story
    if not os.path.isfile(story_path):
        print(f"ERROR: story.json not found: {story_path}")
        sys.exit(2)

    story = load_json(story_path)
    errors, warns = validate_story(story, args.repo_root, args.check_files)

    print(f"SOP_ID: {story.get('sop_id')}")
    print(f"Start:  {story.get('start_code')}")
    print(f"Frames: {len(story.get('frames', []))}")
    print("")

    if warns:
        print("WARNINGS:")
        for w in warns:
            print(" - " + w)
        print("")

    if errors:
        print("ERRORS:")
        for e in errors:
            print(" - " + e)
        sys.exit(1)

    print("OK: story.json validation passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
