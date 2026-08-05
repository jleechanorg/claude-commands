#!/usr/bin/env bash
# e2e_smoke.sh — /web-advice transport smoke test
#
# NON-DESTRUCTIVE. Probes each rung of the transport ladder documented in
# ../SKILL.md and prints a seat-availability matrix. It never submits a
# prompt to any model, never opens a browser tab, and never decrypts/reads
# cookie contents — only checks that the DB file exists.
#
# This is a DIAGNOSTIC, not a gate: it exits 0 (with the matrix printed)
# even when some or most rungs are down, because a partial ladder is a
# normal, working /web-advice session (see SKILL.md "Honest seat
# accounting"). It exits 1 ONLY when every single rung is down — that is
# exactly the HARD-FAIL condition in SKILL.md's HARD-FAIL CONTRACT, where
# /web-advice must stop and report rather than substitute an API/CLI/subagent.
#
# Usage:
#   ./e2e_smoke.sh

set -uo pipefail

CHROME_COOKIES_DB="$HOME/Library/Application Support/Google/Chrome/Default/Cookies"
TIMEOUT_BIN="$(command -v timeout || command -v gtimeout || true)"

run_with_timeout() {
  local secs="$1"
  shift
  if [ -n "$TIMEOUT_BIN" ]; then
    "$TIMEOUT_BIN" "$secs" "$@"
  else
    "$@"
  fi
}

pass=0
total=0
ROWS=()

record() {
  local name="$1" transport="$2" status="$3" detail="$4"
  ROWS+=("${name}|${transport}|${status}|${detail}")
  total=$((total + 1))
  [ "$status" = "UP" ] && pass=$((pass + 1))
}

# --- Rung 1: Aside daemon reachable + at least one signed-in account -------
aside_accounts_out="$(run_with_timeout 10 aside account list 2>&1)"
aside_accounts_rc=$?
if [ $aside_accounts_rc -eq 0 ] && echo "$aside_accounts_out" | grep -q "signed in"; then
  n_accounts=$(echo "$aside_accounts_out" | grep -c "signed in")
  record "1. Aside daemon" "mcp__aside-mcp__repl / aside CLI" "UP" \
    "${n_accounts} account(s) signed in"
else
  record "1. Aside daemon" "mcp__aside-mcp__repl / aside CLI" "DOWN" \
    "rc=${aside_accounts_rc}: $(echo "$aside_accounts_out" | head -1)"
fi

# --- Rung 2: Aside browser window reachable (read-only tab count) ----------
aside_repl_out="$(run_with_timeout 15 aside repl "console.log((await listBrowserTabs()).length)" 2>&1)"
aside_repl_rc=$?
n_tabs="$(echo "$aside_repl_out" | grep -oE '^[0-9]+$' | head -1)"
if [ $aside_repl_rc -eq 0 ] && [ -n "$n_tabs" ]; then
  record "2. Aside browser window" "aside repl (real browser tabs)" "UP" \
    "${n_tabs} tab(s) currently open"
elif echo "$aside_repl_out" | grep -qi "No last-focused window"; then
  record "2. Aside browser window" "aside repl (real browser tabs)" "DOWN" \
    "No last-focused window — repair: open -g -a \"/Applications/Aside.app\" (never plain open -a)"
else
  record "2. Aside browser window" "aside repl (real browser tabs)" "DOWN" \
    "rc=${aside_repl_rc}: $(echo "$aside_repl_out" | head -1)"
fi

# --- Rung 3: Chrome remote-debugging port (CDP attach / claude-in-chrome) --
cdp_out="$(curl -s -m 3 http://127.0.0.1:9222/json/version 2>&1)"
cdp_rc=$?
if [ $cdp_rc -eq 0 ] && echo "$cdp_out" | grep -q '"Browser"'; then
  record "3. Chrome CDP :9222" "claude-in-chrome / CDP attach" "UP" \
    "$(echo "$cdp_out" | tr -d '\n' | cut -c1-80)"
else
  record "3. Chrome CDP :9222" "claude-in-chrome / CDP attach" "DOWN" \
    "not listening (curl rc=${cdp_rc}) — needs Chrome relaunched with --remote-debugging-port=9222, or extension Connect click"
fi

# --- Rung 4: Chrome cookie DB present (existence/readability only) ---------
if [ -f "$CHROME_COOKIES_DB" ] && [ -r "$CHROME_COOKIES_DB" ]; then
  size="$(du -h "$CHROME_COOKIES_DB" 2>/dev/null | cut -f1)"
  record "4. Chrome cookie DB" "chrome-headless + browserclaw cookies" "UP" \
    "present & readable, ${size} ($CHROME_COOKIES_DB)"
else
  record "4. Chrome cookie DB" "chrome-headless + browserclaw cookies" "DOWN" \
    "not found/readable at $CHROME_COOKIES_DB"
fi

# --- Report ------------------------------------------------------------------
echo "==============================================================================="
echo " /web-advice E2E transport smoke test — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo " Diagnostic only. No prompt was submitted to any model. No tab was opened."
echo "==============================================================================="
printf "%-24s %-40s %-6s %s\n" "RUNG" "TRANSPORT" "STATE" "DETAIL"
printf "%-24s %-40s %-6s %s\n" "----" "---------" "-----" "------"
for row in "${ROWS[@]}"; do
  IFS='|' read -r name transport status detail <<< "$row"
  printf "%-24s %-40s %-6s %s\n" "$name" "$transport" "$status" "$detail"
done
echo "-------------------------------------------------------------------------------"
echo " ${pass} of ${total} rungs UP"

if [ "$pass" -eq 0 ]; then
  echo ""
  echo " HARD-FAIL: every transport rung is down."
  echo " Per SKILL.md's HARD-FAIL CONTRACT: /web-advice must STOP and report this"
  echo " verbatim to the user — never substitute a provider API, CLI model, or"
  echo " in-session subagent and call it /web-advice."
  exit 1
fi

exit 0
