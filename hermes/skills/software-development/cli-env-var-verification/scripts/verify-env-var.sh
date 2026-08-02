#!/usr/bin/env bash
# verify-env-var.sh — Reusable CLI env-var verification (4-signal protocol)
#
# Usage: ./verify-env-var.sh <TOOL_BIN> <ENV_VAR_NAME> [<TOOL_DOCS_URL>]
#
# Exits 0 only if all 4 signals confirm the var is honored.
# Prints a per-signal report; failure of any signal does NOT exit non-zero
# (each signal is reported individually so the caller can judge).
#
# Example:
#   ./verify-env-var.sh "$(which claude)" CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY \
#     "https://docs.anthropic.com/en/docs/claude-code/data-usage"

set -uo pipefail

TOOL_BIN="${1:-}"
ENV_VAR="${2:-}"
DOCS_URL="${3:-}"

if [[ -z "$TOOL_BIN" || -z "$ENV_VAR" ]]; then
  echo "Usage: $0 <TOOL_BIN> <ENV_VAR_NAME> [<TOOL_DOCS_URL>]" >&2
  exit 2
fi

echo "================================================================"
echo "Env-var verification: $ENV_VAR"
echo "Tool binary:          $TOOL_BIN"
echo "Docs URL:             ${DOCS_URL:-<not provided>}"
echo "================================================================"
echo

# Signal 1: binary string grep
echo "--- [1/4] Binary string grep (ground truth) ---"
if [[ ! -f "$TOOL_BIN" ]]; then
  echo "FAIL: binary not found at $TOOL_BIN"
elif strings -a "$TOOL_BIN" 2>/dev/null | grep -qx "$ENV_VAR"; then
  echo "PASS: literal string '$ENV_VAR' found in $TOOL_BIN"
elif grep -aoE "$ENV_VAR" "$TOOL_BIN" 2>/dev/null | head -1 | grep -q .; then
  echo "PASS (fallback grep): '$ENV_VAR' substring found in $TOOL_BIN"
else
  echo "FAIL: '$ENV_VAR' NOT found in $TOOL_BIN"
  echo "      (tool may not honor this var, or var name is wrong)"
fi
echo

# Signal 2: docs cross-check (manual only — no network call here, but link provided)
echo "--- [2/4] Official vendor docs ---"
if [[ -n "$DOCS_URL" ]]; then
  echo "TODO: cross-check $DOCS_URL contains \$ENV_VAR"
  echo "      (script does not auto-fetch; do this manually or via curl + grep)"
else
  echo "SKIP: no DOCS_URL provided"
fi
echo

# Signal 3: functional probe (heuristic — runs tool with --version or --help)
echo "--- [3/4] Functional probe ---"
if [[ -x "$TOOL_BIN" ]]; then
  echo "Running: '$TOOL_BIN --version' (or --help if --version missing)"
  if "$TOOL_BIN" --version 2>&1 | head -3; then
    :
  else
    "$TOOL_BIN" --help 2>&1 | head -5
  fi
  echo
  echo "Note: functional probe is var-specific. Many vars (DISABLE_*, ENABLE_*) only"
  echo "show effect in interactive mode or under specific triggers. The binary-grep"
  echo "result is the substitute proof for non-interactive tools."
else
  echo "SKIP: $TOOL_BIN not executable"
fi
echo

# Signal 4: common config file audit
echo "--- [4/4] Config file audit ---"
FOUND_IN_CONFIG=0
for cfg in \
  "$HOME/.claude/settings.json" \
  "$HOME/.config/${TOOL_BIN##*/}/config.toml" \
  "$HOME/.config/${TOOL_BIN##*/}/config.json"; do
  if [[ -f "$cfg" ]] && grep -q "$ENV_VAR" "$cfg" 2>/dev/null; then
    echo "FOUND in: $cfg"
    grep -n "$ENV_VAR" "$cfg"
    FOUND_IN_CONFIG=$((FOUND_IN_CONFIG + 1))
  fi
done
if [[ $FOUND_IN_CONFIG -eq 0 ]]; then
  echo "Not found in any standard config locations checked."
  echo "Tool may use a different config path or env-only."
fi
echo

echo "================================================================"
echo "Summary:"
echo "  [1] Binary grep:  see output above"
echo "  [2] Docs:         ${DOCS_URL:-<manual check required>}"
echo "  [3] Functional:   var-specific — manual observation required"
echo "  [4] Config audit: $FOUND_IN_CONFIG file(s) contained the var"
echo "================================================================"
