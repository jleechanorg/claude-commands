#!/usr/bin/env bash
# block-tmux-sidekick.sh — PreToolUse hook (DRAFT)
#
# PURPOSE
#   Enforce the 2026-07-11 user directive: "i dont wanna use separate tmux
#   sessions i wanna use a real /team-claude and the sidekick is a teammate
#   i can see here." Intercepts Bash invocations that would spawn Claude
#   Code (or a long-running Codex under a "sidekick-..." tmux session) via
#   an external tmux session, and either:
#     - blocks the call (default), logging a clear remediation message
#     - allows it only when ALLOW_TMUX_SIDEKICK=1 AND
#       ALLOW_TMUX_SIDEKICK_REASON=<non-empty> are BOTH set in env
#
# RATIONALE
#   2026-07-11 diagnostic reproduced 4 failure classes around external tmux
#   sidekicks (mailbox never polled, lead stalls, routing broken, silent
#   fallback). The four corresponding upstream Anthropic issues are all
#   CLOSED (#24108, #24771, #24292 = closed/duplicate; #46691 =
#   closed/not_planned — verified 2026-07-11 via gh api), so the
#   user-mandated default is the in-process Agent Teams path. This hook
#   keeps that default enforced.
#
# STATUS
#   DRAFT — not registered in ~/.claude/settings.json. To activate:
#     1. Move this file to ~/.claude/hooks/block-tmux-sidekick.sh
#     2. Add to settings.json PreToolUse with matcher "Bash"
#     3. chmod +x the script
#   All three steps require explicit user approval per
#   ~/.claude/CLAUDE.md "Harness fix durability must match violation severity".
#
# BYPASS (ha3z fix)
#   Both ALLOW_TMUX_SIDEKICK=1 AND a non-empty ALLOW_TMUX_SIDEKICK_REASON must
#   be set in the parent shell BEFORE running the command. Missing reason =
#   still deny. Documented use case: must-survive-this-session-exit sidekick.
#
# DRY RUN (vyor fix)
#   BLOCK_TMUX_DRY_RUN=1 logs a would-block entry and allows. Use to verify
#   the rule fires without interrupting work.
#
# BUG CLASS REFERENCE (verified 2026-07-11 — all upstream issues CLOSED)
#   anthropics/claude-code#24108  mailbox never polled          (closed/duplicate)
#   anthropics/claude-code#24771  teammate routing broken      (closed/duplicate)
#   anthropics/claude-code#24292  tmux silent fallback         (closed/duplicate)
#   anthropics/claude-code#46691  lead stalls                  (closed/not_planned)
#   anthropics/claude-code#23513  tmux send-keys race with shell init
#                                 (still reproduced; no upstream issue yet)
#   Beads tracking the repro: $USER-09v2 (mailbox), $USER-63vk
#     (lead stalls), $USER-p0pm (phantom lane), $USER-b0g0 (silent
#     fallback + config drift).

set -euo pipefail

# Stable log path (yqdb fix) — independent of where this script lives,
# so moving the draft to ~/.claude/hooks/ later does not break audit trail.
LOG_FILE="${HOME}/.claude/hooks/block-tmux-sidekick.log"
mkdir -p "$(dirname "$LOG_FILE")"
TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# Read stdin. PreToolUse hooks receive the Bash tool call JSON on stdin.
# Empty/malformed stdin is allowed: the script must never crash under
# set -euo pipefail — that locks the user out of the session.
INPUT="$(cat 2>/dev/null || true)"

# Extract command from tool_input. Bash hook shape:
#   {"tool_name":"Bash","tool_input":{"command":"..."}}
# Any failure path (empty stdin, JSON parse error, missing keys) → empty
# COMMAND → the script falls through to exit 0 (allow).
COMMAND=""
if [ -n "$INPUT" ]; then
    COMMAND="$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    cmd = d.get("tool_input", {}).get("command", "")
    if cmd:
        sys.stdout.write(cmd)
except Exception:
    pass
' 2>/dev/null || true)"
fi

if [ -z "$COMMAND" ]; then
    exit 0
fi

# --------------------------------------------------------------------
# a9mm fix: dynamic wrapper detection with static fallback.
# Grep ~/.bashrc for alias / function bodies whose definition contains
# "--teammate-mode=tmux". If the grep yields nothing (sandbox / fresh
# install), use the 2026-07-11 static fallback list. Order doesn't matter;
# the matcher is an alternation.
# --------------------------------------------------------------------
WRAPPER_NAMES=()
if [ -r "${HOME}/.bashrc" ]; then
    while IFS= read -r name; do
        if [ -n "$name" ]; then
            WRAPPER_NAMES+=("$name")
        fi
    done < <(
        awk '
            # alias <name>=...   (single-line definition; check whole line)
            /^alias [A-Za-z_][A-Za-z0-9_]*=/ {
                line=$0; sub(/^alias /, "", line); sub(/=.*/, "", line);
                if (index($0, "--teammate-mode=tmux") > 0) print line
                next
            }
            # function opener on its own line:  name() {
            /^[A-Za-z_][A-Za-z0-9_]*\(\) \{/ {
                name=$1; sub(/\(\).*/, "", name); fname=name
                in_block=1; block=$0 ORS; next
            }
            # some bashrcs split the brace:  name()
            #                                    { ... }
            /^[A-Za-z_][A-Za-z0-9_]*\(\)$/ {
                name=$1; sub(/\(\)$/, "", name); fname=name
                in_block=1; block=$0 ORS; next
            }
            in_block && /^\}/ {
                block = block $0 ORS
                if (index(block, "--teammate-mode=tmux") > 0) print fname
                in_block=0; fname=""; block=""
                next
            }
            in_block { block = block $0 ORS }
        ' "${HOME}/.bashrc" 2>/dev/null
    )
fi
# 2026-07-11 ground-truth floor (see STATE.md). claudet is a script-launcher
# alias (`~/.claude/scripts/split-pane-launch.sh`) that ultimately spawns a
# tmux+Claude pane, so it belongs here too. These 24 names are ALWAYS in the
# block list — the dynamic grep may miss wrappers that delegate (claudedsc ->
# claudeds, claudeafc -> claudeaf) without containing the literal flag, so
# we union the two sets instead of using one or the other.
STATIC_WRAPPER_NAMES=(
    clauded claudedc claudedo claudedco claudeo claudeoc
    claudewa claudewac claude2 claude2c claudeaf claudeafc
    claudeds claudedsp claudedsc claudedspc claudelocal claudelocalc
    claudem claudeme claudemc claudeg claudegc claudet
)
# Dedup-union: associative array keyed on name.
declare -A _seen=()
for n in "${STATIC_WRAPPER_NAMES[@]}"; do _seen["$n"]=1; done
for n in "${WRAPPER_NAMES[@]}";    do _seen["$n"]=1; done
WRAPPER_NAMES=("${!_seen[@]}")
unset _seen

# Patterns are grep -E (POSIX-ERE) regexes. ANY match blocks.
PATTERNS=(
    # tmux new-session invoking the claude binary
    'tmux[[:space:]]+new-session.*claude'
    # 41ed fix: tmux+codex only blocks when the session name passed with
    # `-s` starts with "sidekick-". AO's tmux+codex workers (e.g.
    # ao-worker-1) must NOT trigger the rule. The old broad codex pattern
    # was overblocking any tmux+codex invocation. We allow arbitrary chars
    # between the -s arg and the "codex exec" payload (flags, quoting).
    'tmux[[:space:]]+new-session.*-s[[:space:]]+"?sidekick-[A-Za-z0-9_.-]+"?.*codex[[:space:]]+exec'
    # bare --teammate-mode tmux / --teammate-mode=tmux
    '--teammate-mode[[:space:]]+(=|[[:space:]]+)?tmux'
)
# Append one alternation regex covering all detected wrapper names. We
# require whitespace (or start/end-of-line) on BOTH sides of the name.
# This catches `clauded -p hi`, `sudo clauded`, and `clauded` alone while
# avoiding common false positives like `not-clauded` (where `-` is a
# non-whitespace boundary) and `my-clauded-mock.sh`. POSIX-ERE has no
# lookbehind, so the boundaries are part of the captured group; the
# followup loop only checks BOOLEAN match, not capture content, so this
# is safe.
WRAPPER_ALT="$(IFS='|'; printf '%s' "${WRAPPER_NAMES[*]+"${WRAPPER_NAMES[*]}"}")"
# If WRAPPER_ALT came back empty for any reason, refuse to build a pattern
# that matches everything, so fall back to a guaranteed-non-match anchor.
if [ -z "$WRAPPER_ALT" ]; then
    # Guaranteed-never-match, valid POSIX-ERE ('$' before '^' cannot match).
    WRAPPER_PATTERN='$^'
else
    # Match wrapper only when BOTH sides are bounded by a shell token
    # separator (whitespace, ; | & ( ) ) or start/end-of-line. This catches
    # `clauded -p hi`, `(clauded)`, `ls; clauded; ls`, `sudo clauded`,
    # `clauded` alone, etc. — but skips hyphenated suffixes like
    # `not-clauded` and `my-clauded-mock.sh` because '-' is NOT in our
    # boundary set.
    WRAPPER_PATTERN="(^|[[:space:];|&(])(${WRAPPER_ALT})([[:space:];|&)]|$)"
fi
PATTERNS+=("$WRAPPER_PATTERN")

BLOCKED=0
MATCHED_PATTERN=""
for pat in "${PATTERNS[@]}"; do
    # Wrap in if/|| to keep set -e from killing us on grep errors.
    if printf '%s' "$COMMAND" | grep -E -q -- "$pat" 2>/dev/null; then
        BLOCKED=1
        MATCHED_PATTERN="$pat"
        break
    fi
done

if [ "$BLOCKED" -eq 0 ]; then
    exit 0
fi

# --------------------------------------------------------------------
# vyor fix: DRY RUN — log would-block and allow.
# --------------------------------------------------------------------
if [ "${BLOCK_TMUX_DRY_RUN:-0}" = "1" ]; then
    printf '[%s] DRY-RUN would-block: pattern=%s cmd=%s\n' \
        "$TS" "$MATCHED_PATTERN" "$COMMAND" >> "$LOG_FILE"
    exit 0
fi

# --------------------------------------------------------------------
# ha3z fix: bypass requires BOTH the flag AND a non-empty reason.
# --------------------------------------------------------------------
if [ "${ALLOW_TMUX_SIDEKICK:-0}" = "1" ]; then
    REASON="${ALLOW_TMUX_SIDEKICK_REASON:-}"
    if [ -n "$REASON" ]; then
        printf '[%s] ALLOWED: ALLOW_TMUX_SIDEKICK=1 reason=%s pattern=%s cmd=%s\n' \
            "$TS" "$REASON" "$MATCHED_PATTERN" "$COMMAND" >> "$LOG_FILE"
        exit 0
    fi
    # Flag set, reason missing — log and fall through to deny so the user
    # gets a clear signal that the override is incomplete.
    printf '[%s] BLOCKED (override incomplete): ALLOW_TMUX_SIDEKICK=1 but ALLOW_TMUX_SIDEKICK_REASON is empty: pattern=%s cmd=%s\n' \
        "$TS" "$MATCHED_PATTERN" "$COMMAND" >> "$LOG_FILE"
fi

# --------------------------------------------------------------------
# pa54 fix: deny path. PreToolUse requires stdout JSON in the
# hookSpecificOutput shape with permissionDecision="deny" + exit 0.
# Build the JSON via python3 json.dumps because MATCHED_PATTERN and
# COMMAND can contain regex backslashes (the patterns themselves are
# regex literals — heredoc double-escaping is unsafe).
# 96k0 / e2kg fix: reason cites the four beads and describes the
# upstream issues as CLOSED (not "open").
# --------------------------------------------------------------------
# `-` after python3 makes argparse read COMMAND from sys.argv cleanly.
python3 - "$MATCHED_PATTERN" "$COMMAND" <<'PYEOF'
import json, sys
matched_pattern, command = sys.argv[1], sys.argv[2]
reason = (
    "Blocked: tmux-wrapped Claude/Codex spawn detected (pattern: "
    + matched_pattern
    + ").\n\n"
    + "Per the 2026-07-11 user directive, the default for /sidekick and "
    + "/team-claude is in-process Agent Teams teammates (Agent tool with "
    + "name:), not external tmux sessions.\n\n"
    + "Reproduced failure classes (all 4 upstream Anthropic issues are "
    + "CLOSED per 2026-07-11 gh api check — "
    + "#24108/#24771/#24292 closed/duplicate; #46691 closed/not_planned):\n"
    + "  - mailbox never polled\n"
    + "  - teammate routing broken\n"
    + "  - tmux silent fallback to in-process\n"
    + "  - lead stalls (not-planned upstream)\n"
    + "Beads tracking the local repro: $USER-09v2 (mailbox), "
    + "$USER-63vk (lead stalls), $USER-p0pm (phantom lane), "
    + "$USER-b0g0 (silent fallback + config drift).\n\n"
    + "Remediation — replace this command with the in-process path:\n"
    + "  Agent({name: \"<lane-name>\", model: \"sonnet\", "
    + "run_in_background: true, prompt: \"<mission>\"})\n\n"
    + "Override (must-survive-this-session missions only): set BOTH "
    + "ALLOW_TMUX_SIDEKICK=1 AND a non-empty ALLOW_TMUX_SIDEKICK_REASON "
    + "before running this command. Document the override in STATE.md. "
    + "Blocked command: " + command
)
out = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }
}
sys.stdout.write(json.dumps(out, ensure_ascii=False))
PYEOF

# Audit-trail log (do NOT swallow the JSON; log to file in the background).
printf '[%s] BLOCKED: pattern=%s cmd=%s\n' \
    "$TS" "$MATCHED_PATTERN" "$COMMAND" >> "$LOG_FILE"

exit 0
