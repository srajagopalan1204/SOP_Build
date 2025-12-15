#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_player.py

Purpose:
  Build a SOP-specific *_player.html from story.json using a SOP player template.

Key compatibility fix (GitHub Pages):
  Converts leading-slash asset paths like "/outputs/images/..." into portable
  relative paths from outputs/players/*.html:
    /outputs/images/X.png  -> ../images/X.png
    /outputs/faq           -> ../faq
    /outputs/quiz          -> ../quiz

Version:
  SOP_BUILD_build_player_v1.1
Date:
  2025-12-13 America/New_York

Notes:
  - Template placeholder matching is tolerant: supports multiple token styles.
  - If the template has no obvious placeholder for story data, the script injects
    a <script>window.SOP_STORY=...</script> block just before </body>.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo


# -----------------------
# Provenance / versioning
# -----------------------

NY_TZ = ZoneInfo("America/New_York")
BUILD_DT = datetime.now(NY_TZ).strftime("%Y-%m-%d %H:%M %Z")
BUILD_STAMP = datetime.now(NY_TZ).strftime("%Y%m%d_%H%M")
BUILD_VERSION = "SOP_BUILD_build_player_v1.1"


# -----------------------
# Helpers
# -----------------------

def _ensure_parent_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_text(p: Path, s: str) -> None:
    _ensure_parent_dir(p)
    p.write_text(s, encoding="utf-8", newline="\n")


def _log(msg: str, log_path: Optional[Path]) -> None:
    line = f"[{datetime.now(NY_TZ).strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    if log_path:
        _ensure_parent_dir(log_path)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def _detect_base_rel_for_outputs_players(out_html: Path) -> str:
    """
    Determine the relative prefix from the player HTML location to the 'outputs' root.

    If the output path includes .../outputs/players/<file>.html then:
      base_rel = ".."  (because from players/ -> outputs/)

    Otherwise default to ".." (safe for your standard layout).
    """
    parts = [p.lower() for p in out_html.parts]
    # Find "... outputs / players ..."
    for i in range(len(parts) - 1):
        if parts[i] == "outputs" and i + 1 < len(parts) and parts[i + 1] == "players":
            return ".."
    return ".."


def _normalize_outputs_web_paths(story: Dict[str, Any], base_rel: str) -> Dict[str, Any]:
    """
    Make asset paths portable across GitHub Pages repo subpaths.

    Converts:
      /outputs/images/... -> {base_rel}/images/...
      outputs/images/...  -> {base_rel}/images/...

      /outputs/faq or outputs/faq -> {base_rel}/faq
      /outputs/quiz or outputs/quiz -> {base_rel}/quiz

    Leaves already-relative paths alone (../images/..., images/..., etc.).
    """
    img_from_1 = r"^/outputs/images/"
    img_from_2 = r"^outputs/images/"
    img_to = f"{base_rel}/images/"

    def fix(p: Any) -> Any:
        if not isinstance(p, str) or not p:
            return p
        p2 = re.sub(img_from_1, img_to, p)
        p2 = re.sub(img_from_2, img_to, p2)

        # FAQ / Quiz folder locations (exact folder strings)
        if p2 in ("/outputs/faq", "outputs/faq"):
            p2 = f"{base_rel}/faq"
        if p2 in ("/outputs/quiz", "outputs/quiz"):
            p2 = f"{base_rel}/quiz"
        return p2

    # Your story appears to be { "frames": [ ... ] }
    frames = None
    for key in ("frames", "Frames", "slides", "Slides"):
        if isinstance(story.get(key), list):
            frames = story.get(key)
            break
    if frames is None:
        return story

    for fr in frames:
        if not isinstance(fr, dict):
            continue
        if "image" in fr:
            fr["image"] = fix(fr["image"])
        if "FAQ_Loc" in fr:
            fr["FAQ_Loc"] = fix(fr["FAQ_Loc"])
        if "Quiz_Loc" in fr:
            fr["Quiz_Loc"] = fix(fr["Quiz_Loc"])
        # In case you later add other asset fields, you can extend here:
        # for k in ("readme_loc","audio_loc","uap_loc"): ...

    return story


def _default_title_from_story(story: Dict[str, Any], fallback: str) -> str:
    meta = story.get("meta") or {}
    fn = meta.get("function") or meta.get("Function") or ""
    sub = meta.get("subentity") or meta.get("SubEntity") or ""
    sop = story.get("sop_id") or meta.get("sop_id") or ""
    parts = [p for p in [fn, sub, sop] if p]
    if parts:
        return " – ".join(parts) + " SOP Player – EdxBuild"
    return fallback


def _replace_any(template: str, replacements: Dict[str, str]) -> str:
    """
    Replace multiple placeholder styles:
      {{KEY}}, __KEY__, %%KEY%%, <!--KEY-->
    """
    out = template
    for k, v in replacements.items():
        out = out.replace(f"{{{{{k}}}}}", v)
        out = out.replace(f"__{k}__", v)
        out = out.replace(f"%%{k}%%", v)
        out = out.replace(f"<!--{k}-->", v)
    return out


def _inject_story_if_needed(html: str, story_json_str: str) -> str:
    """
    If no placeholder replaced it, inject a script block before </body>.
    """
    if "window.SOP_STORY" in html or "__STORY_JSON__" in html or "{{STORY_JSON}}" in html:
        return html

    inject = (
        "\n<!-- injected by build_player.py -->\n"
        "<script>\n"
        "  window.SOP_STORY = "
        + story_json_str
        + ";\n"
        "</script>\n"
    )
    if "</body>" in html:
        return html.replace("</body>", inject + "</body>")
    return html + inject


def _inject_provenance_comment(html: str) -> str:
    comment = (
        f"<!--\n"
        f"  Built by: build_player.py\n"
        f"  Version: {BUILD_VERSION}\n"
        f"  Built: {BUILD_DT}\n"
        f"-->\n"
    )
    if "<!doctype html" in html.lower():
        # Put after doctype line if possible
        lines = html.splitlines(True)
        if lines:
            return lines[0] + comment + "".join(lines[1:])
    return comment + html


# -----------------------
# CLI
# -----------------------

@dataclass
class Args:
    story: Path
    out: Path
    title: Optional[str]
    mode: str
    image_width: int
    exit_href: str
    template: Optional[Path]
    story_web: Optional[str]
    log: Optional[Path]


def parse_args() -> Args:
    ap = argparse.ArgumentParser(
        description="Build a SOP-specific *_player.html from story.json using the SOP player template."
    )
    ap.add_argument("--story", required=True, help="Filesystem path to story.json (as used by csv_to_story.py).")
    ap.add_argument("--out", required=True, help="Output HTML path for the SOP-specific player (e.g. site/BUILD/..._player.html).")
    ap.add_argument("--title", default=None, help="Browser tab title. If omitted, uses story meta if available.")
    ap.add_argument("--mode", default="dev", help="Mode (dev/prod). Informational only; kept for CLI compatibility.")
    ap.add_argument("--image-width", type=int, default=65, help="Slide image width in percent (e.g. 65).")
    ap.add_argument("--exit", dest="exit_href", default="index.html", help="Exit/Home href used by template tokens if present.")
    ap.add_argument("--template", default=None, help="Template HTML path. If omitted, uses src/templates/SOP_player.html.")
    ap.add_argument("--story-web", default=None, help="Optional: web path to story.json (if template expects it).")
    ap.add_argument("--log", default=None, help="Optional log file path.")
    ns = ap.parse_args()

    return Args(
        story=Path(ns.story),
        out=Path(ns.out),
        title=ns.title,
        mode=ns.mode,
        image_width=int(ns.image_width),
        exit_href=str(ns.exit_href),
        template=Path(ns.template) if ns.template else None,
        story_web=ns.story_web,
        log=Path(ns.log) if ns.log else None,
    )


def main() -> int:
    a = parse_args()

    if not a.story.exists():
        raise FileNotFoundError(f"story.json not found: {a.story}")

    # Default template location
    if a.template is None:
        # assume repo structure: src/python/build_player.py -> src/templates/SOP_player.html
        repo_root_guess = a.out
        # Use current working dir if possible
        cwd = Path.cwd()
        # Prefer git top-level if available (best-effort)
        git_top = None
        try:
            import subprocess
            p = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
            if p.returncode == 0:
                git_top = Path(p.stdout.strip())
        except Exception:
            pass
        base = git_top or cwd
        a.template = base / "src" / "templates" / "SOP_player.html"

    if not a.template.exists():
        raise FileNotFoundError(f"Template not found: {a.template}")

    _log(f"build_player.py {BUILD_VERSION} ({BUILD_DT})", a.log)
    _log(f"Story: {a.story}", a.log)
    _log(f"Template: {a.template}", a.log)
    _log(f"Out: {a.out}", a.log)

    story = json.loads(_read_text(a.story))

    # Normalize paths for GitHub Pages portability
    base_rel = _detect_base_rel_for_outputs_players(a.out)
    story = _normalize_outputs_web_paths(story, base_rel=base_rel)

    title = a.title or _default_title_from_story(story, fallback="SOP Player – EdxBuild")

    template_html = _read_text(a.template)

    # JSON for embedding (compact-ish but readable)
    story_json_str = json.dumps(story, ensure_ascii=False)

    replacements = {
        "PAGE_TITLE": title,
        "TITLE": title,
        "MODE": a.mode,
        "IMAGE_WIDTH": str(a.image_width),
        "EXIT_HREF": a.exit_href,
        "STORY_WEB": a.story_web or "",
        "STORY_JSON": story_json_str,
        "BUILD_VERSION": BUILD_VERSION,
        "BUILD_DT": BUILD_DT,
        "BUILD_STAMP": BUILD_STAMP,
    }

    html = _replace_any(template_html, replacements)

    # If template didn’t have a story placeholder, inject story as window.SOP_STORY.
    # (Your template JS should read window.SOP_STORY; if it doesn’t yet, you can add that once.)
    html = _inject_story_if_needed(html, story_json_str)

    # Always add provenance comment
    html = _inject_provenance_comment(html)

    _write_text(a.out, html)
    _log(f"Wrote: {a.out} ({a.out.stat().st_size} bytes)", a.log)
    _log("Done.", a.log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
