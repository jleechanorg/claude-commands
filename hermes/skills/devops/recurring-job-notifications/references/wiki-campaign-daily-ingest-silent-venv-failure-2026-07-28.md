# wiki-campaign-daily-ingest silent venv failure + Gmail-only alert (2026-07-28)

Session-specific detail for the `scripts/wiki-campaign-daily-ingest.sh`
fix that landed as PR
[#807](https://github.com/jleechanorg/jleechanclaw/pull/807). Read this
together with `recurring-job-notifications/SKILL.md` (the umbrella) and
`references/wiki-campaign-daily-notifications-2026-07-20.md` (the
original wiring reference).

## Original Gmail alert

From `$USER@gmail.com`, 2026-07-24 09:02 PT (4 days after the failure):

```
:red_circle: *wiki-campaign-daily-ingest — FAILED*
batch ingest exited with status 127

*Last log tail:* (see `$HOME/Library/Logs/wiki-campaign-daily-ingest.log` for full)
  [2026-07-24 09:00:24] Bootstrap: installing WA .venv dependencies (one-time)
  [2026-07-24 09:00:24] Bootstrap: installing WA .venv dependencies (one-time)
  $HOME/.hermes/scripts/wiki-campaign-daily-ingest.sh: line 283: $HOME/your-project.com/.venv/bin/python: No such file or directory
  [2026-07-24 09:00:31] Running all-users batch ingest (min-entries=50, --skip-existing)...
  [2026-07-24 09:00:31] Running all-users batch ingest (min-entries=50, --skip-existing)...
  $HOME/.hermes/scripts/wiki-campaign-daily-ingest.sh: line 302: $HOME/your-project.com/.venv/bin/python: No such file or directory
  [2026-07-24 09:00:39] ERROR: batch ingest exited with status 127
  [2026-07-24 09:00:39] ERROR: batch ingest exited with status 127
```

Two failures of the same script in one minute (lines 283 and 302) — both
exit 127 from bash trying to exec a missing binary. The Slack notify path
DID fire (the body shows up in the Gmail recap), but it went to
`#life` (C0AMM2B4319), NOT `#ai-general`, AND it did not tag
`<@U09GH5BR3QU>` or `<@U0AEZC7RX1Q>`.

## Three contract violations reproduced

1. **`SLACK_CHANNEL` defaulted to `#life`** (`C0AMM2B4319`). Per SOUL.md
   `slack-channel-routing-policy`, system-generated cron output belongs in
   the home channel `#ai-general` (`C0AJQ5M0A0Y`). The script's own
   source-comment claimed "bot is not in #ai-general" — but that comment
   was stale. The bot was re-invited to `#ai-general` on 2026-07-14 (per
   `slack-mcp-mail-bot-reinstall` skill §6); the script never got the
   memo.

2. **`notify_error()` did not tag `<@U09GH5BR3QU>` or `<@U0AEZC7RX1Q>`**.
   USER_PROFILE rule: tag on failure paths ONLY (probe/OK/digest must
   stay silent). The script's failure body had no `<@...>` tokens — the
   alert landed in `#life` without waking anyone. Gmail was the only
   signal that the cron had broken.

3. **`trap ERR` did not catch exit 127 from a missing `$PYTHON`**. The
   shell's `execve()` aborts the entire script BEFORE bash consults the
   trap. The script DID log `ERROR: batch ingest exited with status 127`
   — but only because of a separate explicit `if [ $INGEST_EXIT -ne 0 ]`
   guard on the `--skip-existing` pipeline. The FIRST failure (line 283,
   the venv dep check) had no such guard and died silently.

## TDD trail (RED proof captured)

Three contract tests, each reproducing one violation:

```bash
bash scripts/tests/test_wiki_campaign_daily_ingest_notifications.sh
```

### RED proof (pre-fix)

```
Test 1: notify_error() targets #ai-general (C0AJQ5M0A0Y)
  FAIL: SLACK_CHANNEL default = 'C0AMM2B4319' (want 'C0AJQ5M0A0Y' for #ai-general)
Test 2: notify_error() tags <@U09GH5BR3QU> <@U0AEZC7RX1Q> on failure
  FAIL: notify_error slack_text missing tag(s) — operator=0 hermes=0 (need both >=1)
Test 3: broken venv python triggers notify_error() with actionable error (not silent 'No such file or directory')
  FAIL: no notify_error() call was made before script aborted -- venv check did not intercept the broken PYTHON

===============================================
PASS: 0    FAIL: 3
===============================================
```

Each FAIL was driven by a single contract violation; the test was wired
in a way that could not be satisfied without changing the source.

### GREEN proof (post-fix)

```
PASS: SLACK_CHANNEL default = C0AJQ5M0A0Y (#ai-general)
PASS: script declares SLACK_OPERATOR_ID + SLACK_HERMES_BOT_ID with correct literal IDs
PASS: notify_error heredoc interpolates BOTH <@...> tags
PASS: build_success_summary does NOT tag operator or Hermes (success path stays silent)
PASS: venv precheck fired with actionable diagnostic: '[...] ERROR: venv python missing or not executable: ...'
PASS: venv precheck log includes remediation hint

===============================================
PASS: 6    FAIL: 0
===============================================
```

Deterministic across 3 reruns. No flake. No regressions in adjacent
tests (`test_slack_anchor_chunking.sh` 9/9 + `test_slack_anchor_pinning.sh`
8/8 still pass).

## Three targeted fixes

Each is a minimal patch to `scripts/wiki-campaign-daily-ingest.sh`:

1. **`SLACK_CHANNEL` default → `C0AJQ5M0A0Y`**, plus declarations of
   `SLACK_OPERATOR_ID="U09GH5BR3QU"` and `SLACK_HERMES_BOT_ID="U0AEZC7RX1Q"`
   so the variables can be referenced symbolically in heredocs.

2. **`notify_error()` heredoc prepends** `<@${SLACK_OPERATOR_ID}>
   <@${SLACK_HERMES_BOT_ID}>` after the `:red_circle:` header line.
   `build_success_summary()` is NOT touched (USER_PROFILE rule:
   tag-only-on-failure-paths).

3. **Venv preflight block** inserted before the dep check. Detects
   dangling symlinks (Homebrew python moved), attempts auto-recovery via
   `command -v python3.12 || command -v python3`, and if no candidate
   exists, fires `notify_error()` directly (NOT via ERR trap, which
   wouldn't have fired) and exits 127 cleanly.

The preflight code (excerpted from the PR):

```bash
log "Venv preflight: $PYTHON"
if [[ -L "$PYTHON" ]]; then
    py_target=$(readlink "$PYTHON" 2>/dev/null || echo "")
    if [[ -z "$py_target" ]] || [[ ! -e "$py_target" ]]; then
        log "WARN: venv python symlink target '$py_target' is missing — attempting repair"
        py_basename=$(basename "$py_target")
        candidate=$(command -v "$py_basename" 2>/dev/null || command -v python3 2>/dev/null || echo "")
        if [[ -n "$candidate" ]] && [[ -e "$candidate" ]]; then
            ln -sf "$candidate" "$PYTHON" && log "Relinked $PYTHON -> $candidate"
        else
            LAST_ERROR="venv python symlink broken: $PYTHON -> '$py_target' (target missing and no candidate python found)"
            RUN_STATUS="error"
            log "ERROR: $LAST_ERROR"
            notify_error "$LAST_ERROR" 2>&1 | tee -a "$LOG" || true
            exit 127
        fi
    fi
elif [[ ! -x "$PYTHON" ]]; then
    if [[ ! -d "$WORLDAI_REPO/.venv" ]] && command -v python3 >/dev/null 2>&1; then
        log "WARN: no venv at $WORLDAI_REPO/.venv — bootstrapping (one-time)"
        if command -v uv >/dev/null 2>&1; then
            (cd "$WORLDAI_REPO" && uv venv --python 3.12 .venv 2>&1 | tail -3) | tee -a "$LOG" || true
        else
            (cd "$WORLDAI_REPO" && python3 -m venv .venv 2>&1 | tail -3) | tee -a "$LOG" || true
        fi
    fi
    if [[ ! -x "$PYTHON" ]]; then
        LAST_ERROR="venv python missing or not executable: $PYTHON — recreate with 'python3 -m venv $WORLDAI_REPO/.venv' or relink to a system python"
        RUN_STATUS="error"
        log "ERROR: $LAST_ERROR"
        notify_error "$LAST_ERROR" 2>&1 | tee -a "$LOG" || true
        exit 127
    fi
fi
```

## What I learned about test harnesses for cron scripts

Three subtle bugs that bit me while building the TDD harness:

### 1. `bash` env overrides do NOT propagate into `function` definitions

When I tried `export -f notify` inside a subshell then ran
`bash <script>`, the script's own `notify()` definition won (functions
defined in the script can't be overridden from the outside). I lost an
hour on this. The fix is to NOT stub `notify()` — let the real `notify()`
run with stubbed upstream calls (`slack_post_message` returns 0,
`command -v gog` returns 1, `lib-slack-post.sh` "not found" fallback).
Then assert against the SCRIPT'S LOG FILE, not against captured function
arguments.

### 2. `log()` writes to stdout via `tee -a`, not stderr

The script's `log()` is `echo "..." | tee -a "$LOG"`. `tee` writes to
BOTH stdout and the log file. So:

- Redirecting stdout (`>/dev/null`) eats the log lines that `tee` was
  forwarding — they never reach the log file.
- Redirecting stderr only (`2>"$TMPLOG"`) misses the log entirely (tee
  writes to stdout).

The correct pattern when capturing for test assertions: let stdout flow
to /dev/null, but ALSO override `LOG` to a tmpfile path so `tee` writes
there. Or, more pragmatically: don't override `LOG` (the script
hardcodes it as `LOG="$HOME/Library/Logs/..."`, not `${LOG:-...}`) — set
`HOME` to a tmpdir and assert against `$TMPD/Library/Logs/<job>.log`.

### 3. `awk` heredoc extraction needs the right stop-marker

I first wrote `capture && /^notify "[$]/` thinking the heredoc ended at
`notify "$subject" "$slack_text" "$gmail_body"`. The `$` was wrong —
bash doesn't anchor strings to end-of-line. The fix: `capture && /^notify /`
(stop on any line starting with `notify `, which is the call site). The
heredoc content lives between the `notify_error()` opener and the call
site, with no other `notify` calls in between.

## Diagnostic recipe for "my cron failed and I only got a Gmail recap"

When you receive a Gmail alert like the one above and want to know if
the Slack alert fired correctly:

1. **Look for the channel ID** in the Gmail body. `C0AMM2B4319` = #life,
   `C0AJQ5M0A0Y` = #ai-general, `C09GRLXF9GR` = #all-$USER-ai. If the
   ID is one of these, the Slack alert fired somewhere.

2. **Look for `<@U...>` tokens** in the alert body. If absent, the alert
   did not wake anyone on Slack — only Gmail saw it.

3. **Look for "No such file or directory" lines** under the script's
   expected `$BIN` paths. If present, the preflight is missing — the
   trap can't catch exit 127 from `execve()` failures.

4. **Look for "Trap:" lines** in the script's log. If absent, the ERR
   trap didn't fire — either `set -e` was used (skips the trap on some
   commands) or the script aborted before reaching the trap (binary
   preflight missing).

If all three checks fail, the cron is producing Gmail-only failure
alerts and the operator has no Slack-side visibility. That's the
wiki-campaign-daily-ingest 2026-07-24 situation; the fix is PR #807.