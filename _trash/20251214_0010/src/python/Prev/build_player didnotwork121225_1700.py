#!/usr/bin/env python3
"""
build_player.py  v2.2  (2025-12-12)

Provenance:
  - new_SOP_Builder_Fix 20251208_1550
  - Replaces earlier ad-hoc build_player that generated a full HTML file per SOP.
  - v2.1: add --log option to mirror csv_to_story.py / validate_env.py logging.
  - v2.2: fix story.json web path calculation for SOP_Build layout and dev server.

Purpose:
  - Take an existing story.json file for a SOP.
  - Read the standard sop_player.html template.
  - Produce a SOP-specific *_player.html with:
      * The browser tab <title> set appropriately.
      * The default story.json path in the helper input wired to the SOP's story.
      * The "Entity Menu" button wired to the correct anchor on the index page.
      * The Exit button pointing where we want (if provided).
      * The image width CSS (percent) adjusted if requested.

This is the LAST step in the pipeline. It assumes:
  - PPT → PNG has already happened.
  - mk_tw_in + csv_to_story.py have already produced story.json.
  - The sop_player.html template exists in the template_folder.
"""

import argparse
import json
import sys
import os
from pathlib import Path
import re
from datetime import datetime
from typing import Dict, Any, Optional, List


# -----------------------------------------------------------------------------
# Small logger (file + stderr)
# -----------------------------------------------------------------------------

class Logger:
    def __init__(self, logfile: Optional[Path] = None):
        self.logfile = logfile

    def _write(self, level: str, msg: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level}] {msg}"
        # Always echo to stderr so the user sees it
        print(line, file=sys.stderr)
        # Optionally write to a log file
        if self.logfile is not None:
            try:
                self.logfile.parent.mkdir(parents=True, exist_ok=True)
                with self.logfile.open("a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception as e:
                # We don't want logging failures to kill the run
                print(f"[WARN] Could not write to log file {self.logfile}: {e}", file=sys.stderr)

    def info(self, msg: str) -> None:
        self._write("INFO", msg)

    def warn(self, msg: str) -> None:
        self._write("WARN", msg)

    def error(self, msg: str) -> None:
        self._write("ERROR", msg)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def load_story(story_path: Path, log: Logger) -> Dict[str, Any]:
    log.info(f"Loading story JSON from {story_path}")
    if not story_path.is_file():
        log.error(f"story.json not found at: {story_path}")
        raise FileNotFoundError(f"story.json not found at: {story_path}")
    with story_path.open("r", encoding="utf-8") as f:
        story = json.load(f)
    return story


def infer_meta_from_story(story: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Try to infer entity/function/subentity from:
      - top-level story['frames'][0]['meta'] if present
      - fallback to None if missing

    Also pass back sop_id.
    """
    frames = story.get("frames", [])
    first = frames[0] if frames else {}
    meta = first.get("meta", {}) or {}
    sop_id = story.get("sop_id") or first.get("sop_id") or None

    entity = meta.get("entity") or None
    function = meta.get("function") or None
    subentity = meta.get("subentity") or None

    return {
        "sop_id": sop_id,
        "entity": entity,
        "function": function,
        "subentity": subentity,
    }


def infer_title_from_meta(meta: Dict[str, Optional[str]]) -> str:
    """
    Build a sensible HTML <title> using whatever meta we have.
    """
    sop_id = meta.get("sop_id") or "SOP"
    entity = meta.get("entity") or ""
    function = meta.get("function") or ""
    subentity = meta.get("subentity") or ""

    parts: List[str] = [sop_id]
    if entity:
        parts.append(entity)
    if function:
        parts.append(function)
    if subentity:
        parts.append(subentity)

    # Filter out any empty strings and join
    core = " – ".join(p for p in parts if p)
    if not core:
        core = "SOP Player"

    # Add a suffix to make it clear in the tab
    return f"{core} – EdxBuild SOP Player"


def fs_to_web_story_path(story_fs: Path, out_fs: Path, log: Logger) -> str:
    """
    Compute a path that the browser can use to fetch story.json.

    Strategy for SOP_Build:

      * We primarily serve from the /outputs folder in dev, with URLs like:
          /players/LineEnt2_player.html
          /story/LineEnt2/story.json

        Story and player are siblings under /outputs, so the natural path
        from the player to the story is:

          ../story/LineEnt2/story.json

      * We therefore first compute a path RELATIVE to the HTML file's
        directory (out_fs.parent). This works for:
          - Codespaces dev server from /outputs
          - Any other server where players/ and story/ sit side-by-side.

      * If that somehow fails, we fall back to a path relative to the
        current working directory (repo root), e.g.:

          /outputs/story/LineEnt2/story.json

      * As a last resort, we just return "/story.json".
    """
    story_fs = story_fs.resolve()
    out_fs = out_fs.resolve()

    # 1) Try relative path from the player directory
    try:
        rel = os.path.relpath(story_fs, start=out_fs.parent)
        web_path = rel.replace(os.sep, "/")
        log.info(f"Derived story path relative to player: {web_path}")
        return web_path
    except Exception as e:
        log.warn(f"Could not compute relative story path from player location: {e}")

    # 2) Fall back to repo-root-relative
    repo_root = Path.cwd().resolve()
    try:
        rel_root = story_fs.relative_to(repo_root)
        web_root_path = "/" + rel_root.as_posix()
        log.info(f"Derived story path relative to repo root: {web_root_path}")
        return web_root_path
    except Exception as e:
        log.warn(f"Could not compute story path relative to repo root: {e}")

    # 3) Last resort: just use the basename
    name = "/" + story_fs.name
    log.warn(f"Falling back to basename for story path: {name}")
    return name


def get_default_template(log: Logger) -> Path:
    """
    Return the default sop_player.html template path.

    For SOP_Build layout we expect:
      src/python/build_player.py
      src/templates/sop_player.html
    """
    here = Path(__file__).resolve().parent      # .../src/python
    template = here.parent / "templates" / "sop_player.html"  # .../src/templates/sop_player.html
    if not template.is_file():
        log.error(f"Template sop_player.html not found at: {template}")
        raise FileNotFoundError(f"Template sop_player.html not found at: {template}")
    log.info(f"Using template: {template}")
    return template


# -----------------------------------------------------------------------------
# HTML patching
# -----------------------------------------------------------------------------

def adjust_title(html: str, new_title: str, log: Logger) -> str:
    """
    Replace <title>...</title> with a new title.
    """
    pattern = re.compile(r"<title>.*?</title>", re.IGNORECASE | re.DOTALL)
    replacement = f"<title>{new_title}</title>"
    if pattern.search(html):
        html = pattern.sub(replacement, html, count=1)
        log.info("Updated <title> in HTML.")
    else:
        log.warn("No <title> tag found in HTML; inserting a new one in <head>.")
        head_pattern = re.compile(r"<head[^>]*>", re.IGNORECASE)
        if head_pattern.search(html):
            html = head_pattern.sub(lambda m: m.group(0) + "\n  " + replacement, html, count=1)
        else:
            # If no <head>, just prepend
            html = replacement + "\n" + html
    return html


def adjust_story_input(html: str, story_web_path: str, log: Logger) -> str:
    """
    Wire the helper input's default value to the story_web_path.

    Looks for:
      <input type="text" id="story" ... value="...">

    and replaces the value="..." with our story_web_path.
    """
    pattern = re.compile(
        r'(<input[^>]*\bid\s*=\s*"story"[^>]*\bvalue\s*=\s*")([^"]*)(")',
        re.IGNORECASE,
    )
    if pattern.search(html):
        html = pattern.sub(rf'\1{story_web_path}\3', html, count=1)
        log.info(f"Set default story path in input#story to: {story_web_path}")
    else:
        log.warn("Could not find <input id=\"story\" ... value=\"...\"> to update.")
    return html


def adjust_entity_menu(html: str, meta: Dict[str, Optional[str]], log: Logger) -> str:
    """
    Wire the "Entity Menu" button's destination anchor, based on entity/function/subentity.

    We expect the template to have something like:
      goEntityMenu("se-distro-sales")

    We rebuild that slug from meta, lowercased and joined with hyphens.
    """
    entity = (meta.get("entity") or "").strip().lower()
    function = (meta.get("function") or "").strip().lower()
    subentity = (meta.get("subentity") or "").strip().lower()

    parts = [p for p in (entity, function, subentity) if p]
    if not parts:
        log.warn("No entity/function/subentity meta; leaving goEntityMenu(...) unchanged.")
        return html

    slug = "-".join(parts)
    log.info(f"Computed entity menu slug: {slug}")

    pattern = re.compile(r'goEntityMenu\(\s*"(.*?)"\s*\)')
    if pattern.search(html):
        html = pattern.sub(f'goEntityMenu("{slug}")', html, count=1)
        log.info("Updated goEntityMenu(...) call in HTML.")
    else:
        log.warn("Could not find goEntityMenu(\"...\") in HTML to update.")

    return html


def adjust_exit_link(html: str, exit_href: Optional[str], log: Logger) -> str:
    """
    If exit_href is provided, wire the Exit button href.

    We look for a small script that sets:
      document.getElementById('exit-btn').href = '...';

    and replace the '...' with exit_href.
    """
    if not exit_href:
        log.info("No --exit provided; leaving Exit button as-is.")
        return html

    pattern = re.compile(
        r"(document\.getElementById\('exit-btn'\)\.href\s*=\s*')[^']*(';)",
        re.IGNORECASE,
    )
    if pattern.search(html):
        html = pattern.sub(rf"\1{exit_href}\2", html, count=1)
        log.info(f"Updated exit-btn href to: {exit_href}")
    else:
        log.warn("Could not find script that sets exit-btn href; no changes made.")
    return html


def adjust_image_width(html: str, image_width: Optional[int], log: Logger) -> str:
    """
    If an image_width (percent) is provided, adjust the CSS rule for #imgbox img.
    """
    if image_width is None:
        log.info("No --image-width provided; leaving image width CSS as-is.")
        return html

    pattern = re.compile(
        r"(#imgbox\s+img\s*\{\s*max-width:\s*)\d+(\s*%;\s*\})",
        re.IGNORECASE,
    )
    if pattern.search(html):
        html = pattern.sub(rf"\g<1>{image_width}\g<2>", html, count=1)
        log.info(f"Updated #imgbox img max-width to: {image_width}%")
    else:
        log.warn("Could not find #imgbox img { max-width: ... } rule; no width changes made.")
    return html


# -----------------------------------------------------------------------------
# Main build function
# -----------------------------------------------------------------------------

def build_player(
    story_path: Path,
    out_path: Path,
    title: Optional[str],
    mode: str,
    image_width: Optional[int],
    exit_href: Optional[str],
    template_path: Optional[Path],
    logger: Logger,
) -> None:
    logger.info("Starting build_player...")
    logger.info(
        f"Arguments: story={story_path}, out={out_path}, title={title}, "
        f"mode={mode}, image_width={image_width}, exit={exit_href}, "
        f"template={template_path}"
    )

    # Load story.json
    story = load_story(story_path, logger)
    meta = infer_meta_from_story(story)
    logger.info(f"Inferred meta from story: {meta}")

    # Determine title if not provided
    if not title:
        title = infer_title_from_meta(meta)
        logger.info(f"No --title provided; inferred title: {title}")
    else:
        logger.info(f"Using provided title: {title}")

    # Determine web story path (as seen by the browser)
    story_web_path = fs_to_web_story_path(story_path, out_path, logger)

    # Template
    if template_path is None:
        template_path = get_default_template(logger)
    else:
        if not template_path.is_file():
            logger.error(f"Provided template not found: {template_path}")
            raise FileNotFoundError(f"Template not found: {template_path}")
        logger.info(f"Using user-provided template: {template_path}")

    # Read template
    with template_path.open("r", encoding="utf-8") as f:
        html = f.read()

    # Patch HTML pieces
    html = adjust_title(html, title, logger)
    html = adjust_story_input(html, story_web_path, logger)
    html = adjust_entity_menu(html, meta, logger)
    html = adjust_exit_link(html, exit_href, logger)
    html = adjust_image_width(html, image_width, logger)

    # Mode is currently informational, but we log it
    logger.info(f"Mode is set to: {mode} (currently informational only)")

    # Ensure output directory
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"Done. Wrote SOP player to {out_path}")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a SOP-specific *_player.html from story.json using the SOP player template."
    )
    parser.add_argument(
        "--story",
        required=True,
        help="Filesystem path to story.json (as used by csv_to_story.py).",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output HTML path for the SOP-specific player (e.g. outputs/players/LineEnt_player.html).",
    )
    parser.add_argument(
        "--title",
        required=False,
        default=None,
        help="Browser tab title. If omitted, will use '<Function> – <SubEntity> SOP Player – EdxBuild' if available.",
    )
    parser.add_argument(
        "--mode",
        required=False,
        default="prod",
        help="Mode (dev/prod). Currently informational only; kept for CLI compatibility.",
    )
    parser.add_argument(
        "--image-width",
        required=False,
        type=int,
        default=None,
        help="Slide image width in percent (e.g. 65). Adjusts .imgbox img width in template.",
    )
    parser.add_argument(
        "--exit",
        dest="exit_href",
        required=False,
        default=None,
        help="Href for Exit button (e.g. index.html or /site/BUILD/index.html#some-anchor). "
             "If omitted, template default is used.",
    )
    parser.add_argument(
        "--template",
        required=False,
        default=None,
        help="Optional path to a non-default sop_player.html template. "
             "If omitted, uses src/templates/sop_player.html next to this script.",
    )
    parser.add_argument(
        "--log",
        required=False,
        default=None,
        help="Optional log file path. If given, writes a simple text log there in addition to stderr.",
    )

    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = parse_args(argv)

    log_path = Path(args.log) if args.log else None
    logger = Logger(log_path)

    try:
        story_path = Path(args.story)
        out_path = Path(args.out)
        template_path = Path(args.template) if args.template else None

        build_player(
            story_path=story_path,
            out_path=out_path,
            title=args.title,
            mode=args.mode,
            image_width=args.image_width,
            exit_href=args.exit_href,
            template_path=template_path,
            logger=logger,
        )
        return 0
    except Exception as e:
        logger.error(f"build_player failed: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
