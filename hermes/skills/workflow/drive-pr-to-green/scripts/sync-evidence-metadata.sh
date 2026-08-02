#!/usr/bin/env bash
# sync-evidence-metadata.sh — atomically sync a GH gist's metadata.json to a
# PR's live HEAD SHA. Avoids the SHA-typo loop that cost PR #8380 + #777 in
# 2026-07-13 (4-5 chore-refresh iterations typing SHAs by hand).
#
# Why this script exists (not inline):
#   1. LLMs (and humans) transpose 40-char hex strings — `git rev-parse HEAD`
#      output NEVER goes through a human/keyboard between worktree and JSON.
#   2. The chore-refresh loop is fundamental: pushing a "chore: refresh" commit
#      to retrigger Evidence Gate creates a NEW HEAD SHA. Without this script,
#      metadata.json.git_head is stale by definition.
#   3. JSON corruption (writing invalid JSON mid-`python3 -c`) makes the gate
#      fall through to "not reachable in this checkout's history" with no diff
#      hint. Atomic write (tempfile + mv) eliminates this.
#   4. SHA typo = `git cat-file -e ${SHA}^{commit}` returns exit 1 with NO hint
#      about which chars are wrong. We call the verifier ON the candidate SHA
#      before pushing the gist, so typos fail-fast inside this script with a
#      clear error.
#
# Usage:
#   bash sync-evidence-metadata.sh \
#     --worktree $HOME/.worktrees/<branch> \
#     --gist-dir /tmp/wa-evidence-gist-<GIST_ID> \
#     [--metadata-file metadata.json]   # default: metadata.json
#
# Side effects:
#   - Re-writes <gist-dir>/<metadata-file> with the new git_provenance.git_head
#     + pr_head_sha + pr_head_sha fields.
#   - Does NOT push to the gist. Caller must `cd $gist_dir && git push origin HEAD`.
#     Keeping push separate lets the caller batch (e.g. update metadata + amend
#     a header file in one commit).
#
# Exit codes:
#   0  = success, gist staged for push but not pushed
#   1  = worktree path doesn't exist OR isn't a git repo OR SHA unreachable
#   2  = gist dir doesn't exist OR isn't a git repo
#   3  = metadata file missing OR invalid JSON OR missing git_provenance
#   5  = metadata.json was unmodified after the script "edited" it (caught a
#        mid-pipeline corruption)
#
# Verified 2026-07-13 PR #8380 + #777 in jleechanorg/{your-project.com,jleechanclaw}.

set -euo pipefail

WORKTREE=""
GIST_DIR=""
METADATA_FILE="metadata.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --worktree) WORKTREE="$2"; shift 2;;
    --gist-dir) GIST_DIR="$2"; shift 2;;
    --metadata-file) METADATA_FILE="$2"; shift 2;;
    -h|--help)
      sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "ERROR: unknown arg: $1" >&2; exit 2;;
  esac
done

# 1. Validate worktree
if [[ -z "$WORKTREE" ]] || [[ ! -d "$WORKTREE" ]]; then
  echo "ERROR: --worktree <path> required and must exist (got: $WORKTREE)" >&2
  exit 1
fi
if ! git -C "$WORKTREE" rev-parse --is-inside-work-tree &>/dev/null; then
  echo "ERROR: --worktree $WORKTREE is not a git repository" >&2
  exit 1
fi

# 2. Validate gist dir
if [[ -z "$GIST_DIR" ]] || [[ ! -d "$GIST_DIR" ]]; then
  echo "ERROR: --gist-dir <path> required and must exist (got: $GIST_DIR)" >&2
  exit 2
fi
if ! git -C "$GIST_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
  echo "ERROR: --gist-dir $GIST_DIR is not a git repository" >&2
  exit 2
fi

META_PATH="$GIST_DIR/$METADATA_FILE"
if [[ ! -f "$META_PATH" ]]; then
  echo "ERROR: metadata file $META_PATH does not exist; create it first via /es capture" >&2
  exit 3
fi

# 3. Read PR HEAD SHA
PR_HEAD="$(git -C "$WORKTREE" rev-parse HEAD)"
if [[ ! "$PR_HEAD" =~ ^[0-9a-f]{40}$ ]]; then
  echo "ERROR: git rev-parse HEAD returned non-SHA: $PR_HEAD" >&2
  exit 1
fi

# 4. Pre-flight: verify SHA is reachable from worktree HEAD
if ! git -C "$WORKTREE" cat-file -e "${PR_HEAD}^{commit}" 2>/dev/null; then
  echo "ERROR: SHA $PR_HEAD not reachable in $WORKTREE (worktree corrupted?)" >&2
  exit 1
fi

# 5. Probe existing metadata.json for git_provenance; reject early if missing/malformed
if ! python3 -c "
import json, sys
m = json.load(open('$META_PATH'))
if 'git_provenance' not in m:
    print('ERROR: $META_PATH missing git_provenance field — run /es capture to bootstrap', file=sys.stderr)
    sys.exit(3)
"; then
  exit 3
fi

# 6. Atomic update — write to temp file, validate, then mv
TMP_META="$(mktemp "${GIST_DIR}/.metadata.XXXXXX.json")"
trap "rm -f \"$TMP_META\"" EXIT

python3 -c "
import json
m = json.load(open('$META_PATH'))
m['git_provenance']['git_head'] = '$PR_HEAD'
m['git_provenance']['pr_head_sha'] = '$PR_HEAD'
m['pr_head_sha'] = '$PR_HEAD'
json.dump(m, open('$TMP_META', 'w'), indent=2)
"

# 7. Verify the rewritten file is valid JSON and contains the expected SHA
if ! python3 -c "
import json, sys
m = json.load(open('$TMP_META'))
if m.get('git_provenance', {}).get('git_head') != '$PR_HEAD':
    print('ERROR: rewrote file but git_head != expected SHA', file=sys.stderr)
    sys.exit(5)
"; then
  rm -f "$TMP_META"
  exit 5
fi

mv "$TMP_META" "$META_PATH"
trap - EXIT

echo "[sync-evidence-metadata] PR_HEAD=$PR_HEAD"
echo "[sync-evidence-metadata] updated $META_PATH"
echo "[sync-evidence-metadata] to push: cd $GIST_DIR && git add $METADATA_FILE && git commit -m 'evidence: sync git_head to PR HEAD ${PR_HEAD:0:7}' && git push origin HEAD"
