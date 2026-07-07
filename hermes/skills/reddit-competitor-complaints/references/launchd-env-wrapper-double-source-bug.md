# Bug: launchd-env-wrapper.sh double-source kills cron jobs with rc=1

## Symptom

`launchctl print gui/$UID/<label>` shows the job loaded, the wrapper
script runs, and the outer log shows:

```
[2026-06-24T00:15:36Z] [reddit-competitor] === launchd tick ===
[2026-06-24T00:15:36Z] [reddit-competitor] === tick done (rc=1) ===
```

The inner log (the one the target script writes to via
`exec >> log 2>&1`) shows:

```
=== launchd tick 2026-06-24T00:15:36Z ===
Target: slack:C0AUXSVFSA2:1782239564.437219 (fallback: slack:C0AJQ5M0A0Y)
+ '[' -x $HOME/.hermes/scripts/launchd-env-wrapper.sh ']'
+ source $HOME/.hermes/scripts/launchd-env-wrapper.sh
```

…and then nothing. No `RAW_OUT=`, no Slack post, no exit summary.

## Root cause

`launchd-env-wrapper.sh` ends with `exec "$@"` (line 119). This is by
design: the wrapper is meant to be **called as a command** with the
target command as its arguments, e.g.:

```bash
# Standard usage — what the cmux-surface-report-4h-wrapper does:
bash -c "source '$HOME/.hermes/scripts/launchd-env-wrapper.sh' >/dev/null 2>&1; exec '$HOME/.hermes/scripts/cmux-surface-report-4h.sh'"
```

The pattern: `bash -c "source env-wrapper; exec target"` —
- `source env-wrapper` loads the env vars into the current shell.
- `exec target` replaces the current shell with the target script.

The env-wrapper's own terminal `exec "$@"` (when sourced, not called)
fires in the current shell and replaces it with `$@` — the **parent
shell's** positional args. When the parent shell is the wrapper
`bash -c "source env-wrapper; exec target-script"`, the positional
args are the bash command string itself (or empty, depending on how
the shell parses it).

**But if the target script ALSO sources the env-wrapper**, the
env-wrapper's `exec "$@"` runs in the target script's context, with
the target's positional args. If the target has no args (typical
for cron), `$@` is empty, `exec` with no args is a no-op or errors.
Either way, the target script's shell is replaced (or the command
after the source is replaced with the wrong thing). The script
silently dies.

## The fix

**Do NOT source `launchd-env-wrapper.sh` from inside the target
script.** The cron wrapper already loads the env. The target
script reads `HERMES_SLACK_BOT_TOKEN` from the inherited env and
trusts that the wrapper handled it.

In `reddit-competitor-complaints.sh`:

```bash
# REMOVED (was the bug):
# if [ -x "$SCRIPT_DIR/launchd-env-wrapper.sh" ]; then
#   source "$SCRIPT_DIR/launchd-env-wrapper.sh" 2>/dev/null
# fi

# NEW (the comment documents the gotcha for future maintainers):
# NOTE on env loading: do NOT source launchd-env-wrapper.sh here. The wrapper
# script (reddit-competitor-complaints-wrapper.sh) already runs the right chain:
#     bash -c "source launchd-env-wrapper.sh >/dev/null 2>&1; exec $0"
# If we source it again, the env-wrapper's terminal `exec "$@"` runs in our
# current shell with our (empty) positional args and replaces this script with
# `exec` (no-op or 127) — verified bug 2026-06-23 against this very script.
# HERMES_SLACK_BOT_TOKEN is therefore already in env by the time we run.
```

## How to diagnose this in another launchd job

1. Check the inner log: `tail -50 ~/.hermes/logs/scheduled-jobs/<label>.*.log`.
2. If the last line is `+ source $HOME/.hermes/scripts/launchd-env-wrapper.sh`
   and nothing after, this is your bug.
3. Grep the target script for the env-wrapper source:
   ```bash
   grep -n "launchd-env-wrapper" ~/.hermes/scripts/<target>.sh
   ```
4. If the target script sources the env wrapper, delete that block.

## Related: `set -o pipefail` + `head` in `$()`

This is a different rc=1 bug, often in the same code path:

```bash
# BAD — SIGPIPE when head closes early → rc=141
DIGEST=$(echo "$RAW_OUT" | awk '/marker/{flag=1; next} flag' | head -60)

# GOOD — let awk own the truncation
DIGEST=$(echo "$RAW_OUT" | awk '/marker/{flag=1; next} flag && NR<=200 {print}')
```

Symptom: the inner log shows the digest extraction succeeded but the
script exits 1 with `bash: echo: write error: Broken pipe` (or just
silent). Fix: use awk's own NR exit instead of `head -N` in the
pipeline.

## Verified fix

After applying both fixes (no inner source, no `head` in pipe),
`reddit-competitor-complaints-wrapper.sh` returns rc=0 and the inner
log shows:

```
=== launchd tick 2026-06-24T00:22:18Z ===
Target: slack:C0AUXSVFSA2:1782239564.437219 (fallback: slack:C0AJQ5M0A0Y)
[2026-06-23 17:22:18 PDT] [reddit-competitor] === start (PullPush.io backend) ===
[2026-06-23 17:22:18 PDT] [reddit-competitor]   source[0] AI Dungeon  ...
[2026-06-23 17:22:18 PDT] [reddit-competitor]   source[0] AI Dungeon: 1 hits
...
[2026-06-23 17:22:27 PDT] [reddit-competitor] === end (10 threads emitted) ===
Posted to C0AUXSVFSA2 (thread=1782239564.437219)
=== tick done (delivered to primary) ===
```

## Related skills

- `launchd-job-authoring` — canonical pattern for new launchd jobs
  (this skill is the right home for new installs; `references/launchd-env-wrapper-double-source-bug.md`
  is the post-mortem for the specific failure mode)
- `hermes-deploy-pipeline` — `~/.hermes/` (staging) → `~/.hermes_prod/` (prod) sync
