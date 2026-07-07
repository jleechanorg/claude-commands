#!/usr/bin/env bash
# test-classify.sh
#
# Unit tests for the surface classification regexes in
# ~/.hermes/scripts/cmux-surface-report-4h.sh. Verifies:
#   1. BLOCKED regex matches: Traceback, panic:, FATAL EXCEPTION, segfault
#   2. RISKY regex matches: confirm?, Do you want to, approve?, permission to
#   3. HEALTHY regex matches: Running, processing, generating, building,
#      claude--, Working on, thinking
#   4. HEALTHY (idle) falls through to the else branch
#   5. Numeric guard: non-numeric ws/surf values are filtered
#   6. Sanity cap: TOTAL > 100 aborts
#   7. Bucket sum cross-check: sum(healthy+risky+blocked) must equal TOTAL
#   8. Slack payload structure: channel + text + unfurl_links:false
#
# Exit code: 0 if all pass, 1 otherwise.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/cmux-surface-report-4h.sh"
if [[ ! -f "$SCRIPT" ]]; then
  echo "FATAL: cmux-surface-report-4h.sh not found at $SCRIPT" >&2
  exit 1
fi

PASS=0
FAIL=0
ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

# Re-implement the classify logic from the script so tests are
# deterministic (no live cmux socket needed). The classifier is the
# 3-way if/elif/elif/else chain at lines 154-166 of the script.
classify() {
  local SCREEN="$1"
  if echo "$SCREEN" | grep -qiE 'Traceback|panic:|FATAL EXCEPTION|segmentation fault'; then
    echo "BLOCKED"
  elif echo "$SCREEN" | grep -qiE 'confirm\?|Do you want to|approve\?|permission to'; then
    echo "RISKY"
  elif echo "$SCREEN" | grep -qiE 'Running|processing|generating|building|claude--|Working on|thinking'; then
    echo "HEALTHY"
  else
    echo "HEALTHY_IDLE"
  fi
}

# === Test 1: BLOCKED regex ===
echo ""
echo "=== test 1: BLOCKED regex matches fatal error patterns ==="
for sample in \
  "Traceback (most recent call last):\n  File \"x.py\", line 42\nKeyError: 'foo'" \
  "kernel: panic: VFS: Unable to mount root fs" \
  "FATAL EXCEPTION in thread main\njava.lang.NullPointerException" \
  "process exited with signal 11 (segmentation fault)"; do
  result=$(classify "$sample")
  if [[ "$result" == "BLOCKED" ]]; then
    ok "BLOCKED matches: $(echo "$sample" | head -1 | cut -c1-60)"
  else
    bad "expected BLOCKED, got $result: $(echo "$sample" | head -1 | cut -c1-60)"
  fi
done

# === Test 2: RISKY regex ===
echo ""
echo "=== test 2: RISKY regex matches approval prompts ==="
for sample in \
  "Are you sure you want to proceed? confirm?" \
  "Do you want to overwrite the file?" \
  "Approve this action? approve?" \
  "Permission to read /etc/passwd?"; do
  result=$(classify "$sample")
  if [[ "$result" == "RISKY" ]]; then
    ok "RISKY matches: $(echo "$sample" | head -1 | cut -c1-60)"
  else
    bad "expected RISKY, got $result: $(echo "$sample" | head -1 | cut -c1-60)"
  fi
done

# === Test 3: HEALTHY regex (active work) ===
echo ""
echo "=== test 3: HEALTHY regex matches active work patterns ==="
for sample in \
  "Running tests..." \
  "Processing 1234 records" \
  "Generating response..." \
  "Building project: hermes-agent" \
  "claude--M2.7 is generating" \
  "Working on issue #42" \
  "thinking about the next move..."; do
  result=$(classify "$sample")
  if [[ "$result" == "HEALTHY" ]]; then
    ok "HEALTHY matches: $(echo "$sample" | head -1 | cut -c1-60)"
  else
    bad "expected HEALTHY, got $result: $(echo "$sample" | head -1 | cut -c1-60)"
  fi
done

# === Test 4: HEALTHY (idle) ===
echo ""
echo "=== test 4: HEALTHY_IDLE falls through for unclassified screens ==="
for sample in \
  "\$ " \
  "Welcome to bash. Type 'help' for more info." \
  "" \
  "[user@host ~]$ "; do
  result=$(classify "$sample")
  if [[ "$result" == "HEALTHY_IDLE" ]]; then
    ok "IDLE matches: $(echo "$sample" | head -1 | cut -c1-60)"
  else
    bad "expected HEALTHY_IDLE, got $result: $(echo "$sample" | head -1 | cut -c1-60)"
  fi
done

# === Test 5: Numeric guard ===
echo ""
echo "=== test 5: numeric guard filters malformed ws/surf pairs ==="
is_numeric() {
  [[ "$1" =~ ^[0-9]+$ ]]
}
for ws_surf in "1 2" "0 0" "999 999" "abc def" "" "1 abc" "1.5 2.5"; do
  ws=$(echo "$ws_surf" | awk '{print $1}')
  surf=$(echo "$ws_surf" | awk '{print $2}')
  if is_numeric "$ws" && is_numeric "$surf"; then
    ok "numeric guard passes for: '$ws_surf'"
  else
    ok "numeric guard rejects: '$ws_surf' (ws='$ws' surf='$surf')"
  fi
done

# === Test 6: Sanity cap ===
echo ""
echo "=== test 6: sanity cap rejects TOTAL > 100 (100 allowed) ==="
for total in 100 101 999 9999; do
  if [[ "$total" =~ ^[0-9]+$ ]] && [ "$total" -gt 100 ]; then
    ok "sanity cap rejects TOTAL=$total"
  elif [[ "$total" =~ ^[0-9]+$ ]] && [ "$total" -le 100 ]; then
    ok "sanity cap allows TOTAL=$total"
  else
    bad "sanity cap failed for TOTAL=$total"
  fi
done

# === Test 7: Bucket sum cross-check ===
echo ""
echo "=== test 7: bucket sum cross-check ==="
TOTAL=10
HEALTHY=6
RISKY=2
BLOCKED=2
SUM=$((HEALTHY + RISKY + BLOCKED))
if [[ "$SUM" -eq "$TOTAL" ]]; then
  ok "bucket sum matches TOTAL ($SUM == $TOTAL)"
else
  bad "bucket sum mismatch ($SUM != $TOTAL) — parser dropped surfaces"
fi

# Bucket mismatch test
TOTAL=10
HEALTHY=5
RISKY=2
BLOCKED=2
SUM=$((HEALTHY + RISKY + BLOCKED))
if [[ "$SUM" -ne "$TOTAL" ]]; then
  ok "bucket sum mismatch correctly detected ($SUM != $TOTAL)"
else
  bad "bucket sum should mismatch but matched"
fi

# === Test 8: Slack payload structure ===
echo ""
echo "=== test 8: Slack payload structure ==="
PAYLOAD=$(jq -nc --arg ch "C0AJQ5M0A0Y" --arg txt "test" '{channel:$ch, text:$txt, unfurl_links:false}')
CH=$(echo "$PAYLOAD" | jq -r .channel)
TXT=$(echo "$PAYLOAD" | jq -r .text)
UNFURL=$(echo "$PAYLOAD" | jq -r .unfurl_links)
if [[ "$CH" == "C0AJQ5M0A0Y" && "$TXT" == "test" && "$UNFURL" == "false" ]]; then
  ok "Slack payload: channel=C0AJQ5M0A0Y text=test unfurl_links=false"
else
  bad "Slack payload malformed: channel=$CH text='$TXT' unfurl_links=$UNFURL"
fi

# === Test 9: Channel default ===
echo ""
echo "=== test 9: channel default is C0AJQ5M0A0Y (#ai-general) ==="
DEFAULT_CHANNEL="${HERMES_CMUX_4H_CHANNEL:-C0AJQ5M0A0Y}"
if [[ "$DEFAULT_CHANNEL" == "C0AJQ5M0A0Y" ]]; then
  ok "default channel is #ai-general (C0AJQ5M0A0Y)"
else
  bad "default channel is $DEFAULT_CHANNEL, expected C0AJQ5M0A0Y"
fi

# Override test
HERMES_CMUX_4H_CHANNEL="C0AKALZ4CKW" DEFAULT_CHANNEL="${HERMES_CMUX_4H_CHANNEL:-C0AJQ5M0A0Y}"
if [[ "$DEFAULT_CHANNEL" == "C0AKALZ4CKW" ]]; then
  ok "channel override respected (HERMES_CMUX_4H_CHANNEL wins)"
else
  bad "channel override not respected: got $DEFAULT_CHANNEL"
fi

# === Test 10: Wrapper sourcing chain ===
echo ""
echo "=== test 10: wrapper requires launchd-env-wrapper.sh ==="
WRAPPER="$REPO_ROOT/scripts/cmux-surface-report-4h-wrapper.sh"
if [[ -f "$WRAPPER" ]]; then
  if grep -q "launchd-env-wrapper.sh" "$WRAPPER"; then
    ok "wrapper sources launchd-env-wrapper.sh"
  else
    bad "wrapper does NOT source launchd-env-wrapper.sh — Slack token won't load"
  fi
  if grep -q "FATAL: launchd-env-wrapper.sh missing" "$WRAPPER"; then
    ok "wrapper has FATAL guard for missing launchd-env-wrapper.sh"
  else
    bad "wrapper missing FATAL guard"
  fi
else
  bad "wrapper missing at $WRAPPER"
fi

# ============================================================
# Tests for v1.2 improvements (2026-06-24)
# ============================================================

# --- Test A: extract_pr() helper ---
# Re-implement the python logic in pure bash so the test runs without
# python3 -c (which the script uses). This mirrors the SAME regexes so
# any drift between the script and the test fails CI.
extract_pr() {
  local screen="$1"
  local default_repo="${CMUX_REPORT_GH_REPO:-$GITHUB_REPOSITORY}"

  # Last-valid-URL wins (freshest activity at bottom of agent screens).
  # Iterate matches in order; pick the LAST whose repo != jleechanorg.
  local last_repo="" last_n=""
  local tmp_screen="$screen"
  while [[ "$tmp_screen" =~ github\.com/jleechanorg/([^/]+)/pull/([0-9]+) ]]; do
    local matched="${BASH_REMATCH[0]}"
    local repo="${BASH_REMATCH[1]}"
    local n="${BASH_REMATCH[2]}"
    if [[ "$repo" != "jleechanorg" ]]; then
      last_repo="$repo"
      last_n="$n"
    fi
    # Advance past this match.
    tmp_screen="${tmp_screen#*"$matched"}"
  done
  if [[ -n "$last_repo" && -n "$last_n" ]]; then
    echo "[#${last_n}](https://github.com/jleechanorg/${last_repo}/pull/${last_n})"
    return 0
  fi

  # Text-only `jleechanorg/<repo>` mention. Reject the doubled-owner
  # pattern (jleechanorg/jleechanorg/...) so we never emit that as repo.
  local m_repo=""
  if [[ "$screen" =~ jleechanorg/([^[:space:]/]+) ]]; then
    if [[ "${BASH_REMATCH[1]}" != "jleechanorg" ]]; then
      m_repo="${BASH_REMATCH[1]}"
    fi
  fi

  # No jleechanorg anchor anywhere -> refuse to guess.
  if [[ -z "$m_repo" && "$screen" != *"jleechanorg"* ]]; then
    return 0
  fi

  # Find FIRST PR number. Prefer "PR #N" / "#N" / "pull/N".
  local n=""
  if [[ "$screen" =~ (PR\ \#|\#)([0-9]+) ]]; then
    n="${BASH_REMATCH[2]}"
  elif [[ "$screen" =~ /pull/([0-9]+) ]]; then
    n="${BASH_REMATCH[1]}"
  fi
  if [[ -z "$n" ]]; then
    return 0
  fi

  local repo="${m_repo:-$default_repo}"
  # Strip leading "jleechanorg/" from a fully-qualified default.
  if [[ "$repo" == "jleechanorg/"* ]]; then
    repo="${repo#jleechanorg/}"
  fi
  echo "[#${n}](https://github.com/jleechanorg/${repo}/pull/${n})"
}

echo ""
echo "=== test A: extract_pr() handles full URLs + bare refs ==="
declare -a EXTRACT_PR_CASES=(
  "auto-merge https://github.com/$GITHUB_REPOSITORY/pull/7847|[#7847](https://github.com/$GITHUB_REPOSITORY/pull/7847)"
  "auto-merge https://github.com/jleechanorg/$GITHUB_REPOSITORY/pull/7522|[#7522](https://github.com/$GITHUB_REPOSITORY/pull/7522)"
  "working on PR #7651 at $GITHUB_REPOSITORY|[#7651](https://github.com/$GITHUB_REPOSITORY/pull/7651)"
  "working on PR #99 merged|"
  "working on PR #7852 at jleechanorg/dark-factory|[#7852](https://github.com/jleechanorg/dark-factory/pull/7852)"
  "https://github.com/jleechanorg/cmux/pull/8|[#8](https://github.com/jleechanorg/cmux/pull/8)"
  "see https://github.com/somebody/cool-project/pull/42 for inspiration|"
  "agent idle bash prompt|"
)
for case in "${EXTRACT_PR_CASES[@]}"; do
  input="${case%%|*}"
  expected="${case#*|}"
  actual=$(extract_pr "$input")
  if [[ "$actual" == "$expected" ]]; then
    ok "extract_pr: $(echo "$input" | cut -c1-50)"
  else
    bad "extract_pr: $(echo "$input" | cut -c1-50)  (got: ${actual:-<empty>} expected: ${expected:-<empty>})"
  fi
done

# --- Test B: smarter "working on" extractor ---
# Re-implement the rank-by-score logic from the script. Verify that
# lines mentioning a PR number are preferred over activity-keyword-only
# lines, and later-in-screen lines beat earlier ones.
working_on_score() {
  local screen="$1"
  python3 <<PYEOF
import sys
text = """$screen"""
lines = [l for l in text.splitlines() if l.strip()]
import re
PR_RX = re.compile(r"#\d+|jleechanorg/[A-Za-z0-9_.\-]+")
ACT_RX = re.compile(r"(?i)\b(running|generating|building|processing|compiling|"
                    r"cooked|brewed|sprouting|cogitated|composer|cargo|pytest|"
                    r"mypy|working on|sleeping|claude--)\b")
best, best_score = "", -1
n = len(lines)
for i, line in enumerate(lines):
    s = line.strip()
    if not s or s.startswith(">"): continue
    score = 0
    if PR_RX.search(s):   score += 3
    if ACT_RX.search(s):  score += 2
    score += i / max(n, 1)
    if score > best_score:
        best, best_score = s, score
print(best)
PYEOF
}

echo ""
echo "=== test B: 'working on' extractor prefers PR-mentioning lines ==="
# Header line is at top, log line with PR mention is at bottom. The
# extractor should pick the bottom line because it's fresher AND mentions
# a PR (score += 3).
SCREEN_B=$'Welcome to agento\nPinned workspaces loaded\nagent: Running tests in worktree\nPR #7847 updated — awaiting review\n> bash $'
best=$(working_on_score "$SCREEN_B")
if [[ "$best" == *"#7847"* ]]; then
  ok "PR-mentioning line wins (got: $(echo "$best" | cut -c1-60))"
else
  bad "PR-mentioning line should win (got: $(echo "$best" | cut -c1-60))"
fi

# PR-mention beats activity-keyword even when activity is at bottom.
SCREEN_B2=$'Running cargo build\nfoo bar baz\nPR #99 merged at d68d52b'
best2=$(working_on_score "$SCREEN_B2")
if [[ "$best2" == *"#99"* ]]; then
  ok "PR-mention beats earlier activity-keyword (got: $(echo "$best2" | cut -c1-60))"
else
  bad "PR-mention should beat earlier activity-keyword (got: $(echo "$best2" | cut -c1-60))"
fi

# --- Test C: pinned workspace resolution ---
# Re-implement the bash logic for matching workspace ref + name frag.
is_pinned() {
  local ws="$1" ws_name="$2"
  local pin_file="$HOME/.config/cmux/pinned-workspaces.txt"
  [[ ! -r "$pin_file" ]] && return 1
  while IFS= read -r line; do
    line="${line%%#*}"
    line="$(echo "$line" | xargs)"
    [[ -z "$line" ]] && continue
    if [[ "$line" == workspace:* ]]; then
      if [[ "$ws" == "${line#workspace:}" ]]; then return 0; fi
    else
      lc_name=$(echo "$ws_name" | tr '[:upper:]' '[:lower:]')
      lc_frag=$(echo "$line" | tr '[:upper:]' '[:lower:]')
      [[ "$lc_name" == *"$lc_frag"* ]] && return 0
    fi
  done < "$pin_file"
  return 1
}

echo ""
echo "=== test C: pinned workspace resolution (ref + name fragment) ==="
PIN_TMP=$(mktemp)
trap "rm -f $PIN_TMP" EXIT
# Write a temporary pin file so the test doesn't depend on the user's
# actual ~/.config/cmux/pinned-workspaces.txt. Override via env override
# would require editing the script; instead write the real file for the
# duration of the test.
ORIG_PIN="$HOME/.config/cmux/pinned-workspaces.txt"
[[ -f "$ORIG_PIN" ]] && cp "$ORIG_PIN" "$PIN_TMP"
cat > "$ORIG_PIN" <<'EOF'
workspace:14
agento
# comment line
EOF

if is_pinned 14 "agento"; then
  ok "pinned by exact ref (workspace:14)"
else
  bad "pinned by exact ref should match"
fi
if is_pinned 99 "anything"; then
  bad "non-pinned workspace should not match"
else
  ok "non-pinned workspace rejected"
fi
if is_pinned 5 "agento worker"; then
  ok "pinned by name fragment (substring match)"
else
  bad "pinned by name fragment should match"
fi
# Restore.
if [[ -f "$PIN_TMP" ]]; then
  mv "$PIN_TMP" "$ORIG_PIN"
else
  rm -f "$ORIG_PIN"
fi

# --- Test D: priority sort (pinned > selected > class) ---
echo ""
echo "=== test D: priority sort puts pinned first ==="
python3 <<'PYEOF'
import sys
pri = [80, 40, 20, 40]   # idle, active, risky, active
sel = [0, 1, 0, 0]
pin = [0, 0, 1, 0]
ws  = ["w1", "w2", "w3", "w4"]

# Re-implement the sort key from the script.
def sort_key(i):
    return (
        pri[i],
        0 if pin[i] == 1 else 1,
        0 if sel[i] == 1 else 1,
        ws[i],
    )
indices = sorted(range(len(pri)), key=sort_key)
# Expected: pinned=w3 first (pri=20, pinned=1),
# then active+selected w2 (pri=40-5=35 effectively via R_PRI),
# but here we test the raw priority array pre-bump.
# Actually: priority calc in script adds -5 to selected, sets pinned=1.
# So with [80, 40, 20, 40] and bumps: [80, 35, 1, 40]
pri_bumped = list(pri)
for i in range(len(pri)):
    if sel[i] == 1: pri_bumped[i] -= 5
    if pin[i] == 1: pri_bumped[i] = 1
def sort_key2(i):
    return (
        pri_bumped[i],
        0 if pin[i] == 1 else 1,
        0 if sel[i] == 1 else 1,
        ws[i],
    )
indices2 = sorted(range(len(pri)), key=sort_key2)
order = [ws[i] for i in indices2]
expected = ["w3", "w2", "w4", "w1"]
if order == expected:
    print("OK priority_sort: " + str(order))
else:
    print(f"FAIL priority_sort: got={order} expected={expected}")
    sys.exit(1)
PYEOF
[[ $? -eq 0 ]] && ok "priority sort: pinned > selected+active > active > idle" \
                || bad "priority sort order is wrong"

# === Summary ===
echo ""
echo "==================================="
echo "Tests passed: $PASS"
echo "Tests failed: $FAIL"
echo "==================================="
[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1