#!/usr/bin/env bash
# protect-pr-close.sh — PreToolUse hook to enforce supersession-comment rule before gh pr close
# 3 PRs were closed in 24h without any supersession comment documenting which PR replaced them.
# Per CLAUDE.md: "Closing a PR is allowed ONLY when it is superseded by another PR."
# This hook checks for a "Superseded by #" comment before allowing the close.

set -euo pipefail

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

# Check if command contains gh pr close
if ! echo "$TOOL_INPUT" | grep -qE 'gh\s+pr\s+close'; then
  exit 0
fi

# Extract the PR number from the command
# Handles: gh pr close <num>, gh pr close <num> --comment, gh pr close <num> -c "body"
PR_NUM=$(echo "$TOOL_INPUT" | python3 -c "
import sys, re, json

raw = sys.stdin.read()
# PR numbers appear as the first positional arg after 'gh pr close'
# May be preceded by flags like --comment, -c, --body, --repo, --owner, etc.
# May be followed by flags or remain at end of command
m = re.search(r'gh\s+pr\s+close\s+(?:--comment|--body|-c|--repo\s+\S+|-r\s+\S+\s+)?(\d+)', raw)
if m:
    print(m.group(1))
else:
    print('')
" 2>/dev/null) || PR_NUM=""

if [ -z "$PR_NUM" ]; then
  echo "BLOCKED: Could not extract PR number from 'gh pr close' command."
  echo "Block the close so a human can verify the target PR."
  exit 1
fi

# Determine the repo from the command or infer from git remote
REPO_ARG=$(echo "$TOOL_INPUT" | python3 -c "
import sys, re
raw = sys.stdin.read()
m = re.search(r'--repo\s+(\S+)', raw)
if m:
    print(m.group(1))
else:
    print('')
" 2>/dev/null) || REPO_ARG=""

if [ -n "$REPO_ARG" ]; then
  REPO="$REPO_ARG"
else
  # Infer repo from git remote
  REPO=$(git remote get-url origin 2>/dev/null | python3 -c "
import sys, re
url = sys.stdin.read().strip()
m = re.search(r'github\.com[/:]([\w-]+/[\w.-]+?)(?:\.git)?$', url)
if m:
    print(m.group(1))
else:
    print('')
" 2>/dev/null) || REPO=""
fi

if [ -z "$REPO" ]; then
  echo "BLOCKED: Could not determine repository for PR #$PR_NUM."
  echo "Block the close so a human can verify the target PR."
  exit 1
fi

# Check if any PR comment contains "Superseded by #" with a valid PR number
# Use python3 to do the API call and pattern match reliably
RESULT=$(python3 - "$REPO" "$PR_NUM" <<'PYEOF'
import sys, subprocess, re

repo = sys.argv[1]
pr_num = sys.argv[2]

try:
    # Get all issue/PR comments on this PR
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/issues/{pr_num}/comments",
         "--jq", ".[].body"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        # Fallback: try pulls endpoint
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/pulls/{pr_num}/comments",
             "--jq", ".[].body"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print("ERROR:API_FAILED")
            sys.exit(0)

    body = result.stdout

    # Look for "Superseded by #<number>" pattern
    # Must have a number after the # (not just "Superseded by #" alone)
    if re.search(r'Superseded\s+by\s+#\d+', body):
        print("ALLOWED")
    else:
        print("BLOCKED")

except subprocess.TimeoutExpired:
    print("ERROR:TIMEOUT")
except Exception as e:
    print(f"ERROR:{e}")
PYEOF
) || RESULT="ERROR:UNKNOWN"

case "$RESULT" in
  ALLOWED)
    exit 0
    ;;
  BLOCKED)
    echo "BLOCKED: PR #$PR_NUM has no 'Superseded by #' comment."
    echo "Per CLAUDE.md: Closing a PR is allowed ONLY when it is superseded by another PR."
    echo "Before closing:"
    echo "  1. Verify ALL changes from PR #$PR_NUM are present in the superseding PR."
    echo "  2. Post a comment: 'Superseded by #<superseding-PR-number> — all changes verified covered.'"
    echo "  3. Ask the user to close this PR manually, or add the comment first then retry."
    echo ""
    echo "If you believe this PR should be closed without a supersession (e.g. draft/abandoned),"
    echo "ask the user to close it manually."
    exit 1
    ;;
  ERROR:API_FAILED|ERROR:TIMEOUT|ERROR:UNKNOWN|*)
    echo "BLOCKED: Could not verify supersession comment on PR #$PR_NUM (API error)."
    echo "Block the close so a human can verify the target PR."
    exit 1
    ;;
esac
