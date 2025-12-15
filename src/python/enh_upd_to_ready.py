#!/usr/bin/env python3
"""
enh_upd_to_ready.py  (v2 – with Narr1/Narr2/Narr3 build)

Purpose
-------
Convert an ENH_UPD narration CSV into a "READY" CSV for csv_to_story.py.

- Normalizes column names (e.g., " FAQ_File" -> "FAQ_File").
- Ensures key columns exist:
    Start_Here, Entity, Function, SubEntity, Exclude,
    FAQ_Loc, FAQ_File, FAQ_Label,
    Quiz_Loc, Quiz_File, Quiz_Label,
    Narr1, Narr2, Narr3.
- Fills defaults:
    Start_Here -> "No" if blank.
- Builds Narr1 using Code + Title_short + Narr1_seed:
    "Slide S000. Opening Slide for ... — <Narr1_seed>."
  (only if Narr1 is currently blank; does not overwrite manual Narr1)
- Copies Narr2_seed -> Narr2 and Narr3_seed -> Narr3 if those final
  columns are blank.

Usage
-----
python src/enh_upd_to_ready.py \
  --csv inputs/raw/LineEnt2_Raw_120925_1558_READYBASE_ENH_UPD.csv \
  --out outputs/build_in/LineEnt2_mk_tw_in_READY_251210_1015.csv
"""

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert ENH_UPD CSV -> READY CSV for csv_to_story.py")
    p.add_argument("--csv", required=True, help="Input ENH_UPD CSV path")
    p.add_argument("--out", required=True, help="Output READY CSV path")
    return p.parse_args()


def build_narr1(code: str, title_short: str, seed: str) -> str:
    """
    Build Narr1 from Code, Title_short, and Narr1_seed.

    Example:
      Code        = "S000"
      Title_short = "Opening Slide for Sales Order Line Entry Deck"
      seed        = "This slide introduces..."

    Result:
      "Slide S000. Opening Slide for Sales Order Line Entry Deck — This slide introduces..."
    """
    code = (code or "").strip()
    title_short = (title_short or "").strip()
    seed = (seed or "").strip()

    if not code and not title_short and not seed:
        return ""

    # Main text body from seed, as a clean sentence
    main = seed or title_short
    main = main.strip()
    if main and main[-1] not in (".", "!", "?"):
        main += "."

    parts = []

    if code:
        parts.append(f"Slide {code}.")
    if title_short:
        # If we already had "Slide S000." we can add the title after a space
        if parts:
            parts[-1] = parts[-1] + f" {title_short}"
        else:
            parts.append(title_short)

    # Join code+title part and the main text with a long dash if both exist
    if parts and main:
        prefix = parts[0]
        # Avoid duplicating the same sentence if seed == title_short
        if main and main != title_short:
            return f"{prefix} — {main}"
        else:
            return prefix
    elif parts:
        return parts[0]
    else:
        return main


def main() -> None:
    args = parse_args()
    in_path = Path(args.csv)
    out_path = Path(args.out)

    if not in_path.exists():
        raise SystemExit(f"Input CSV not found: {in_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Read input CSV
    with in_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise SystemExit(f"Input CSV appears empty: {in_path}")

    # Normalize column names: strip & collapse spaces
    orig_fieldnames = reader.fieldnames or []
    norm_map = {}
    for name in orig_fieldnames:
        if name is None:
            continue
        clean = name.strip()
        clean = " ".join(clean.split())
        norm_map[name] = clean

    norm_rows = []
    for row in rows:
        new_row = {}
        for old_name, value in row.items():
            if old_name is None:
                continue
            new_name = norm_map.get(old_name, old_name)
            new_row[new_name] = value
        norm_rows.append(new_row)

    fieldnames = list(norm_rows[0].keys())

    # Columns we want to guarantee exist
    required_extra_cols = [
        "Start_Here",
        "Entity",
        "Function",
        "SubEntity",
        "Exclude",
        "FAQ_Loc",
        "FAQ_File",
        "FAQ_Label",
        "Quiz_Loc",
        "Quiz_File",
        "Quiz_Label",
        "Narr1",
        "Narr2",
        "Narr3",
    ]

    for col in required_extra_cols:
        if col not in fieldnames:
            fieldnames.append(col)
            for row in norm_rows:
                row[col] = ""

    # Row-level cleanup and narration generation
    for row in norm_rows:
        # Trim whitespace for all fields
        for k, v in list(row.items()):
            if isinstance(v, str):
                row[k] = v.strip()

        # Default Start_Here to "No" if blank
        if not row.get("Start_Here"):
            row["Start_Here"] = "No"

        # Ensure FAQ/Quiz cols are at least empty strings
        for col in ["FAQ_Loc", "FAQ_File", "FAQ_Label", "Quiz_Loc", "Quiz_File", "Quiz_Label"]:
            if row.get(col) is None:
                row[col] = ""

        # Build Narr1 if blank
        if not row.get("Narr1"):
            code = row.get("Code", "")
            title_short = row.get("Title_short", "")
            narr1_seed = row.get("Narr1_seed", "")
            row["Narr1"] = build_narr1(code, title_short, narr1_seed)

        # OPTIONAL: Copy seeds into Narr2 / Narr3 if you’ve created them
        if not row.get("Narr2") and row.get("Narr2_seed"):
            row["Narr2"] = row["Narr2_seed"].strip()
        if not row.get("Narr3") and row.get("Narr3_seed"):
            row["Narr3"] = row["Narr3_seed"].strip()

    # Preferred column ordering (any extra columns get appended)
    core_order = [
        "Source_PPT", "SlideIndex", "SelectionTitle", "Title", "Code", "Title_short",
        "Image_sub_url",
        "Deci_Question", "Next1_Code", "Next2_Code",
        "Desc_Next1", "Desc_Next2", "Desi_Ques",
        "Narr1_seed", "Narr2_seed", "Narr3_seed",
        "Narr1", "Narr2", "Narr3",
        "UAP_Label", "UAP_URL",
        "Start_Here",
        "Entity", "Function", "SubEntity",
        "Exclude",
        "FAQ_Loc", "FAQ_File", "FAQ_Label",
        "Quiz_Loc", "Quiz_File", "Quiz_Label",
    ]

    extras = [c for c in fieldnames if c not in core_order]
    final_fields = [c for c in core_order if c in fieldnames] + extras

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=final_fields)
        writer.writeheader()
        for row in norm_rows:
            writer.writerow(row)

    print(f"Input : {in_path}")
    print(f"Output: {out_path}")
    print(f"Rows  : {len(norm_rows)}")
    print("Done: ENH_UPD -> READY CSV with Narr1/2/3.")


if __name__ == "__main__":
    main()
