#!/usr/bin/env bash
# cloud-build-trigger.sh v2.2 — UserPromptSubmit hook for Claude Code
#
# Resilient version with:
# - JSON parsing of stdin (Claude Code wraps user message in {"message":"..."})
# - URL/path false-positive exclusion (GH URLs, file paths)
# - Strong trigger phrases (verb-form, case-insensitive)
#
# Trigger phrases (verb-form):
#   - build on (the )?cloud
#   - run this plan on the cloud
#   - kick off a cloud build
#   - build this remotely
#   - dispatch (this )?to the cloud
#   - send (this )?to the cloud
#   - execute (this )?on the cloud
#
# Excluded (false-positive triggers from v1):
#   - "cloud build" alone (fires on repo names like cb-X-build)
#   - "superpowers cloud" (matches repo name superpowers-cloud-build-source)
#   - "on the cloud" alone (too broad)
#   - "use cloud" alone (too ambiguous)
#
# False-positive exclusions:
#   - URLs (https://..., github.com/...)
#   - File paths (.git, .md, .py, .sh, etc.)
#   - Repo names (any string with /<user>/<repo>-<word> pattern)

set -uo pipefail

# Read user message from stdin (Claude Code passes JSON: {"message":"..."})
RAW="$(cat)"

# Extract message from JSON
MSG=$(echo "$RAW" | sed -n 's/.*"message"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
if [ -z "$MSG" ]; then
  MSG="$RAW"
fi

# If empty, exit
if [ -z "$MSG" ]; then
  exit 0
fi

# Skip if message looks like a URL/path (any false-positive context)
# Heuristic: contains a URL pattern, a file extension, or a /<user>/<repo> pattern
if echo "$MSG" | grep -qE '(^https?://|github\.com|\.git(/|$)|/blob/|/tree/|\.(md|py|sh|json|yaml|yml|ts|tsx|js|jsx)$|/[^[:space:]]+/[^[:space:]]+/[^[:space:]]+)'; then
  exit 0
fi

# Check for trigger phrases anywhere in the message (case-insensitive)
TRIGGERED=""

# Each pattern is a verb phrase that strongly indicates "dispatch to cloud build"
PATTERNS=(
  'build on (the )?cloud\b'
  'run this plan on the cloud\b'
  'kick off a cloud build\b'
  'build this remotely\b'
  'dispatch (this )?(to )?the cloud\b'
  'send (this )?to the cloud\b'
  'execute (this )?on the cloud\b'
  'cloud-build this'           # explicit "cloud-build" verb form
  'cloud-build: '             # explicit "cloud-build:" prefix
)

for pattern in "${PATTERNS[@]}"; do
  if echo "$MSG" | grep -qiE "$pattern"; then
    TRIGGERED="yes"
    break
  fi
done

# No match — no-op
if [ -z "$TRIGGERED" ]; then
  exit 0
fi

# Match found. Output directive for Claude Code.
cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[cloud-build-trigger v2.2] Detected canonical Cloud Build phrase. The user wants to dispatch this work to the Superpowers Cloud Build box (cloud.superpowers.build, GLM-5.2 via internal proxy). Invoke /super with the user's full request as $ARGUMENTS — do NOT silently substitute local subagents, claudeg, or OpenRouter. If /super fails with 'run identity conflict', retry with a fresh slug (timestamp suffix). If preflight fails, surface the EXACT error from preflight-local.sh — do NOT fall back to local subagents."}}
EOF
exit 0
