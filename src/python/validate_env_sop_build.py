#!/usr/bin/env python3
"""
validate_env_sop_build.py  (simple image + CSV sanity check for SOP_Build)

Checks that:
- The CSV has a Code and Image_sub_url column.
- For each row, Image_sub_url points (by file name) to a PNG that exists
  in the images directory you pass via --images.

Usage:
  python src/python/validate_env_sop_build.py \
    --csv "/workspaces/SOP_Build/outputs/build_in/LineEnt2_mk_tw_in_READY_121125_0800.csv" \
    --images "/workspaces/SOP_Build/outputs/images/LineEnt2" \
    --log "logs/LineEnt2_validate_121125_0800.log"
"""

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Simple env/image validator for SOP_Build READY CSV")
    p.add_argument("--csv", required=True, help="READY CSV path (mk_tw_in_READY_*.csv)")
    p.add_argument("--images", required=True, help="Directory with PNG images for this SOP")
    p.add_argument("--log", required=True, help="Log file to write results into")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    img_dir = Path(args.images)
    log_path = Path(args.log)

    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")
    if not img_dir.exists():
        raise SystemExit(f"Images directory not found: {img_dir}")

    log_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []

    if "Code" not in headers:
        raise SystemExit("CSV is missing required column: Code")
    if "Image_sub_url" not in headers:
        raise SystemExit("CSV is missing required column: Image_sub_url")

    existing_imgs = {p.name for p in img_dir.glob("*.png")}

    missing_images = []
    empty_images = []
    seen_codes = set()

    for row in rows:
        code = (row.get("Code") or "").strip()
        img_sub = (row.get("Image_sub_url") or "").strip()

        if code:
            seen_codes.add(code)

        if not img_sub:
            empty_images.append(code or "(no Code)")
            continue

        # Take only the last part of the path: e.g. "/images/LineEnt2/S000.png" -> "S000.png"
        img_name = Path(img_sub).name
        if not img_name:
            empty_images.append(code or "(no Code)")
            continue

        if img_name not in existing_imgs:
            missing_images.append((code or "(no Code)", img_name))

    # Write log
    with log_path.open("w", encoding="utf-8") as lf:
        lf.write(f"CSV : {csv_path}\n")
        lf.write(f"Imgs: {img_dir}\n")
        lf.write(f"Rows: {len(rows)}\n")
        lf.write(f"Unique Codes: {len(seen_codes)}\n\n")

        if empty_images:
            lf.write("Rows with empty Image_sub_url:\n")
            for c in empty_images:
                lf.write(f"  - Code {c}\n")
            lf.write("\n")

        if missing_images:
            lf.write("Rows where image file is missing in images dir:\n")
            for code, img_name in missing_images:
                lf.write(f"  - Code {code}: expected {img_name}\n")
            lf.write("\n")
        else:
            lf.write("All Image_sub_url entries resolved to existing PNG files.\n")

    print(f"CSV : {csv_path}")
    print(f"Imgs: {img_dir}")
    print(f"Rows: {len(rows)}")
    print(f"Log : {log_path}")
    if missing_images or empty_images:
        print("DONE with warnings. See log for details.")
    else:
        print("DONE: all images present and linked correctly.")


if __name__ == "__main__":
    main()
