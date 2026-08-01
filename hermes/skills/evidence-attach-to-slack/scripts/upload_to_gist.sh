#!/usr/bin/env bash
# upload_to_gist.sh — end-to-end binary-to-gist upload for PR evidence.
#
# Usage: ./upload_to_gist.sh <evidence_dir> "<gist_description>" [github_user]
#
# What it does:
#   1. Creates a gist with the text files in <evidence_dir> (PNGs are rejected
#      by `gh gist create`, so we add them via git clone afterward).
#   2. Clones the gist as a writable git repo.
#   3. Copies all PNGs/JPGs/GIFs from <evidence_dir> into the repo.
#   4. Commits + pushes real binary bytes.
#   5. Verifies every PNG serves `content-type: image/png` on the raw URL.
#   6. Prints a JSON-ready mapping: <filename>|<raw_url>
#
# Output: gist URL on stdout; full raw-URL map at /tmp/gist-raw-urls.txt
#
# Proven 2026-07-08 on PR #8269 (load-older-top-only fix, 12 PNG bundle).
# See references/github-gist-binary-upload.md for the full why.

set -euo pipefail

EVIDENCE_DIR="${1:-}"
DESCRIPTION="${2:-PR evidence bundle}"
GITHUB_USER="${3:-$(gh auth status 2>/dev/null | awk -F' account ' '/account/ {print $2}' | awk '{print $1}' | tr -d '()')}"

if [[ -z "$EVIDENCE_DIR" || ! -d "$EVIDENCE_DIR" ]]; then
  echo "Usage: $0 <evidence_dir> \"<gist_description>\" [github_user]" >&2
  echo "  <evidence_dir>: directory containing PNGs + optional text files" >&2
  echo "  <gist_description>: short description for the gist" >&2
  echo "  [github_user]: defaults to current gh auth user (e.g. jleechan2015)" >&2
  exit 1
fi

if [[ -z "$GITHUB_USER" ]]; then
  echo "ERROR: cannot determine GitHub user. Run 'gh auth status' or pass as 3rd arg." >&2
  exit 1
fi

echo "== Uploading evidence bundle from: $EVIDENCE_DIR"
echo "== Gist description: $DESCRIPTION"
echo "== GitHub user: $GITHUB_USER"

# Step 1: Create gist with text files only (PNGs would be rejected by CLI)
TEXT_FILES=()
while IFS= read -r -d '' f; do
  TEXT_FILES+=("$f")
done < <(find "$EVIDENCE_DIR" -maxdepth 1 -type f \( -name "*.md" -o -name "*.txt" -o -name "*.json" -o -name "*.py" -o -name "*.yml" -o -name "*.yaml" \) -print0)

if [[ ${#TEXT_FILES[@]} -eq 0 ]]; then
  # No text files; create gist with empty placeholder
  TMP_PLACEHOLDER=$(mktemp -t gist-placeholder.XXXXXX.txt)
  echo "no-text-placeholder" > "$TMP_PLACEHOLDER"
  TEXT_FILES=("$TMP_PLACEHOLDER")
fi

echo ""
echo "== Step 1: gh gist create (text files only)"
GIST_URL=$(gh gist create --public --desc "$DESCRIPTION" "${TEXT_FILES[@]}" | tail -1)
GIST_ID="${GIST_URL##*/}"
echo "  Created: $GIST_URL"
echo "  ID: $GIST_ID"

# Step 2: Clone the gist
echo ""
echo "== Step 2: gh gist clone"
WORKDIR=$(mktemp -d)
gh gist clone "$GIST_ID" "$WORKDIR"
cd "$WORKDIR"

# Step 3: Remove any placeholder, copy real binary files
echo ""
echo "== Step 3: copy binary files"
# Clean up any placeholder text files we just pushed (preserve user text files)
for placeholder in "gist-no-text-placeholder.txt" "no-text-placeholder.txt"; do
  if [[ -f "$placeholder" && "$EVIDENCE_DIR" != *"$placeholder" ]]; then
    rm -f "$placeholder"
  fi
done
find "$EVIDENCE_DIR" -maxdepth 1 -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.gif" -o -name "*.webp" -o -name "*.mp4" -o -name "*.pdf" \) -exec cp {} . \;

# Step 4: Commit + push
echo ""
echo "== Step 4: git commit + push"
git config user.email "${GITHUB_USER}@users.noreply.github.com"
git config user.name "$GITHUB_USER"
git add -A
git commit -m "evidence: real binary files (avoiding gist API base64-as-text trap)" >/dev/null
git push origin HEAD

# Step 5: Verify and build raw-URL map
echo ""
echo "== Step 5: verify raw URLs serve image/png (or correct type)"
URL_MAP="/tmp/gist-raw-urls.txt"
> "$URL_MAP"
echo "GIST_URL=$GIST_URL" >> "$URL_MAP"
echo "GIST_ID=$GIST_ID" >> "$URL_MAP"
echo "" >> "$URL_MAP"

ALL_OK=true
verify_file() {
  local f="$1"
  local SHA RAW_URL CT STATUS
  SHA=$(git ls-tree HEAD "$f" | awk '{print $3}')
  RAW_URL="https://gist.githubusercontent.com/${GITHUB_USER}/${GIST_ID}/raw/${SHA}/${f}"
  CT=$(curl -fsI "$RAW_URL" 2>/dev/null | grep -i "^content-type:" | tr -d '\r' || echo "ERROR")
  if echo "$CT" | grep -qE "image/(png|jpeg|gif|webp)|video/mp4|application/pdf"; then
    STATUS="OK"
  else
    STATUS="FAIL"
    ALL_OK=false
  fi
  echo "  [$f] $STATUS  CT=$CT"
  echo "${f}|${RAW_URL}" >> "$URL_MAP"
}

# Verify all binary types
while IFS= read -r -d '' f; do verify_file "$f"; done < <(find . -maxdepth 1 -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.gif" -o -name "*.webp" -o -name "*.mp4" -o -name "*.pdf" \) -printf '%f\0' | sort -z)

echo ""
if $ALL_OK; then
  echo "OK All files served with correct content-type."
else
  echo "FAIL Some files failed content-type check." >&2
  echo "  Likely cause: stale base64-as-text content. Delete gist + retry." >&2
  exit 1
fi

echo ""
echo "== DONE =="
echo "  Gist URL:  $GIST_URL"
echo "  Gist ID:   $GIST_ID"
echo "  Raw URLs:  $URL_MAP"
echo ""
echo "To embed in PR description markdown:"
echo "  ![caption]($GIST_URL#file-<filename>)"
echo ""
echo "Or use the raw URLs from $URL_MAP directly:"
echo "  ![caption](https://gist.githubusercontent.com/${GITHUB_USER}/${GIST_ID}/raw/<sha>/<filename>)"
echo ""
echo "(Temporary workdir preserved at $WORKDIR for inspection; rm -rf when done.)"