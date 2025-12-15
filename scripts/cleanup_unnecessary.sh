#!/usr/bin/env bash
set -euo pipefail

# cleanup_unnecessary.sh
# Version: v1.0
# Built: 2025-12-13 America/New_York
# Purpose:
#   - Move "unnecessary / stale" folders into _trash/<timestamp>/ (default)
#   - Wipe generated outputs content so you can copy fresh images and rebuild clean
#   - Optional: --purge to permanently delete the trash after moving

TZ="America/New_York"
ts="$(date +'%Y%m%d_%H%M')"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
trash_root="${repo_root}/_trash/${ts}"

PURGE="N"
if [[ "${1-}" == "--purge" ]]; then
  PURGE="Y"
fi

echo "Repo root : ${repo_root}"
echo "Trash dir : ${trash_root}"
echo "Mode      : $([[ "${PURGE}" == "Y" ]] && echo "PURGE (permanent delete after move)" || echo "SAFE (move-to-trash)")"
echo

mkdir -p "${trash_root}"

move_to_trash () {
  local p="$1"
  if [[ -e "${repo_root}/${p}" ]]; then
    echo "Moving -> _trash: ${p}"
    mkdir -p "$(dirname "${trash_root}/${p}")"
    mv "${repo_root}/${p}" "${trash_root}/${p}"
  else
    echo "Skip (not found): ${p}"
  fi
}

wipe_dir_keep_folder () {
  local d="$1"
  if [[ -d "${repo_root}/${d}" ]]; then
    echo "Wiping contents (keeping folder): ${d}"
    rm -rf "${repo_root:?}/${d:?}/"* "${repo_root:?}/${d:?}/".* 2>/dev/null || true
    # re-create in case patterns removed nothing
    mkdir -p "${repo_root}/${d}"
  else
    echo "Skip wipe (not found): ${d}"
  fi
}

echo "=== 1) Move clearly-unneeded / clutter folders ==="
# Old doc copies / scratch
move_to_trash "docs_org"
move_to_trash "temp_data"
move_to_trash "rep_new"

# Old bundles in root (keep your newest backup you just made separately)
# Move only the stage bundles; leave other zips alone if you want.
for f in "${repo_root}"/SOPB_outputs_for_SOP_Stage_*.zip; do
  if [[ -f "$f" ]]; then
    bn="$(basename "$f")"
    echo "Moving -> _trash: ${bn}"
    mv "$f" "${trash_root}/${bn}"
  fi
done

# Optionally move heavy logs (keeps repo clean + fast)
move_to_trash "logs"

# Move Prev history folders (you can keep them if you want, but these are usually bulk)
move_to_trash "inputs/ppt_sample/Prev"
move_to_trash "inputs/raw/Prev"
move_to_trash "outputs/build_in/Prev"
move_to_trash "outputs/players/Prev"
move_to_trash "outputs/story/LineEnt2/Prev"
move_to_trash "src/Prev"
move_to_trash "src/python/Prev"
move_to_trash "src/templates/Prev"

# Move duplicate template copies (keep the primary sop_player.html + shell + json5)
for c in \
  "src/templates/sop_player copy.html" \
  "src/templates/sop_player copy 2.html" \
  "src/templates/sop_player copy 3.html" \
  "src/templates/sop_player_almost_there_121325_0930.html"
do
  [[ -e "${repo_root}/${c}" ]] && move_to_trash "${c}" || true
done

echo
echo "=== 2) Wipe generated OUTPUTS so you can copy fresh images + rebuild clean ==="
# Keep folder structure but remove generated content
wipe_dir_keep_folder "outputs/faq"
wipe_dir_keep_folder "outputs/quiz"
wipe_dir_keep_folder "outputs/players"
wipe_dir_keep_folder "outputs/images"
wipe_dir_keep_folder "outputs/story"

# Also wipe docs/outputs mirrors (these are what stage/prod serve from)
wipe_dir_keep_folder "docs/outputs/faq"
wipe_dir_keep_folder "docs/outputs/quiz"
wipe_dir_keep_folder "docs/outputs/players"
wipe_dir_keep_folder "docs/outputs/images"
wipe_dir_keep_folder "docs/outputs/story"

echo
echo "=== 3) Recreate required tree (in case wipe removed empty dirs) ==="
mkdir -p "${repo_root}/docs/outputs/players" \
         "${repo_root}/docs/outputs/images" \
         "${repo_root}/docs/outputs/faq" \
         "${repo_root}/docs/outputs/quiz" \
         "${repo_root}/docs/outputs/story"

mkdir -p "${repo_root}/outputs/players" \
         "${repo_root}/outputs/images" \
         "${repo_root}/outputs/faq" \
         "${repo_root}/outputs/quiz" \
         "${repo_root}/outputs/story" \
         "${repo_root}/outputs/build_in"

echo
echo "=== 4) Optional purge ==="
if [[ "${PURGE}" == "Y" ]]; then
  echo "Purging trash permanently: ${trash_root}"
  rm -rf "${trash_root}"
  echo "Trash purged."
else
  echo "SAFE MODE: Nothing permanently deleted."
  echo "Review trash here: ${trash_root}"
  echo "If happy, you can purge later with:"
  echo "  rm -rf \"${trash_root}\""
fi

echo
echo "DONE."
echo "Current top-level status:"
cd "${repo_root}"
git status -sb || true

