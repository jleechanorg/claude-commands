#!/usr/bin/env bash
# Smart Fake Code Detection Hook
# Runs the /fake command headlessly via claude -p for every Write operation

set -euo pipefail

# Prevent recursive invocation if the command itself triggers hooks
if [[ -n "${SMART_FAKE_HOOK_ACTIVE:-}" ]]; then
    exit 0
fi
export SMART_FAKE_HOOK_ACTIVE=1

# jq is required for parsing the hook payload
if ! command -v jq >/dev/null 2>&1; then
    echo "⚠️ smart_fake_code_detection: jq is not available; skipping /fake audit." >&2
    exit 0
fi

INPUT="$(cat)"
if [[ -z "$INPUT" ]]; then
    exit 0
fi

TOOL_NAME="$(echo "$INPUT" | jq -r '.tool_name // empty')"
if [[ "$TOOL_NAME" != "Write" ]]; then
    exit 0
fi

TARGET_FILES=()
while IFS= read -r path; do
    TARGET_FILES+=("$path")
done < <(
    printf '%s' "$INPUT" | jq -r '
        [
            .tool_input.file_path?,
            (.tool_input.files? // [])[]?.file_path?,
            (.tool_input.files? // [])[]?.path?,
            (.tool_input.edits? // [])[]?.file_path?,
            (.tool_output.created_files? // [] )[]?,
            (.tool_output.modified_files? // [] )[]?,
            (.tool_output.updated_files? // [] )[]?,
            (.tool_output.applied_edits? // [])[]?.file_path?,
            (.tool_output.files? // [])[]?.file_path?,
            (.tool_output.files? // [])[]?.path?
        ]
        | map(select(. != null and . != ""))
        | unique[]
        | gsub("^\\./"; "")
    ' 2>/dev/null || true
)

if [[ ${#TARGET_FILES[@]} -eq 0 ]]; then
    exit 0
fi

if PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
    :
else
    PROJECT_ROOT="$PWD"
fi

BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/claude"
mkdir -p "$LOG_DIR"
chmod 700 "$LOG_DIR" 2>/dev/null || true
LOG_FILE="$LOG_DIR/smart_fake_code_detection_${BRANCH_NAME}.log"

declare -a RELATIVE_FILES=()
for path in "${TARGET_FILES[@]}"; do
    if [[ -n "$PROJECT_ROOT" && "$path" = /* ]]; then
        if [[ "$path" == "$PROJECT_ROOT" ]]; then
            RELATIVE_FILES+=(".")
        elif [[ "$path" == "$PROJECT_ROOT"/* ]]; then
            RELATIVE_FILES+=("${path#"$PROJECT_ROOT"/}")
        else
            RELATIVE_FILES+=("$path")
        fi
    else
        RELATIVE_FILES+=("$path")
    fi
done

# De-duplicate after normalization to avoid redundant audits
declare -A __smart_fake_seen=()
declare -a __smart_fake_deduped=()
for f in "${RELATIVE_FILES[@]}"; do
  if [[ -z "${__smart_fake_seen[$f]:-}" ]]; then
    __smart_fake_seen[$f]=1
    __smart_fake_deduped+=("$f")
  fi
done
RELATIVE_FILES=("${__smart_fake_deduped[@]}")

printf '%s - Triggered /fake audit for %d file(s):\n' "$(date '+%Y-%m-%d %H:%M:%S')" "${#RELATIVE_FILES[@]}" >>"$LOG_FILE"
for file in "${RELATIVE_FILES[@]}"; do
    printf '  - %s\n' "$file" >>"$LOG_FILE"
done

if ! command -v claude >/dev/null 2>&1; then
    echo "⚠️ smart_fake_code_detection: claude CLI not found; skipping /fake audit." | tee -a "$LOG_FILE" >&2
    exit 0
fi

FILE_LIST=""
if [[ ${#RELATIVE_FILES[@]} -gt 0 ]]; then
    FILE_LIST="$(printf ' - %s\n' "${RELATIVE_FILES[@]}")"
fi

PROMPT=$(cat <<EOF
/fake

Branch: $BRANCH_NAME
Files touched in the latest Write operation:
${FILE_LIST}Analyze these changes for fake or simulated code, placeholder logic, speculative API responses, or fabricated data. Cite concrete issues with file names and line numbers when possible. If everything is legitimate, respond with ✅ CLEAN and a brief justification.
EOF
)

# SMART_FAKE_TIMEOUT: Optional environment variable to set the timeout for the /fake audit (default: 120s).
CLAUDE_TIMEOUT="${SMART_FAKE_TIMEOUT:-120s}"
CLAUDE_CMD=(claude -p --dangerously-skip-permissions --model sonnet)

echo "🤖 smart_fake_code_detection: Running /fake audit via claude -p for ${#RELATIVE_FILES[@]} file(s)." >&2

set +e
if command -v timeout >/dev/null 2>&1; then
    CLAUDE_OUTPUT=$(printf "%s" "$PROMPT" | timeout "$CLAUDE_TIMEOUT" "${CLAUDE_CMD[@]}" 2>&1)
    CLAUDE_STATUS=$?
else
    CLAUDE_OUTPUT=$(printf "%s" "$PROMPT" | "${CLAUDE_CMD[@]}" 2>&1)
    CLAUDE_STATUS=$?
fi
set -e

printf '%s\n' "$CLAUDE_OUTPUT" >>"$LOG_FILE"
printf "---\n" >>"$LOG_FILE"

echo "📋 /fake audit results:" >&2
printf '%s\n' "$CLAUDE_OUTPUT" >&2

if [[ $CLAUDE_STATUS -eq 124 ]]; then
    echo "⚠️ smart_fake_code_detection: /fake audit timed out after $CLAUDE_TIMEOUT." | tee -a "$LOG_FILE" >&2
elif [[ $CLAUDE_STATUS -ne 0 ]]; then
    echo "⚠️ smart_fake_code_detection: /fake audit exited with status $CLAUDE_STATUS." | tee -a "$LOG_FILE" >&2
else
    echo "✅ smart_fake_code_detection: /fake audit completed." | tee -a "$LOG_FILE" >&2
fi

exit 0
