---
name: cmux-resume-watchdog
description: Operate, install, or debug the cmux session resume watchdog — a launchd daemon that polls cmux terminal surfaces, classifies each surface as idle/busy/stuck via fastembed + LLM fallback, and sends a one-token resume action (Esc + paste "Continue...") when a surface is dead. Use when the watchdog isn't running, surfaces stay dead after a CLI/API hang, the daily-cap or attempt-cap fires, the user complains "why did claude/codex stop?", or when migrating the watchdog between machines.
user-invocable: true
---

# cmux Resume Watchdog

Canonical files (this skill is the exportable source of truth):

- Skill root: `$HOME/.claude/skills/cmux-resume-watchdog/`
- Daemon: `scripts/cmux_resume_watchdog.py` (model-backed, provider-neutral)
- Wrapper: `scripts/run-cmux-resume-watchdog.sh` (sources `~/.bash_profile`, picks a Python runtime with `fastembed`/`numpy`/`onnxruntime`)
- Shared helpers (vendored from `~/projects/user_scope/scripts/`): `scripts/cmux_surface_utils.py`, `scripts/semantic_classifier.py`
- Plist template: `com.$USER.cmux-resume-watchdog.plist` (`@HOME@`-templated)
- Rendered plist: `com.$USER.cmux-resume-watchdog.plist.rendered` (with `$HOME` substituted, ready to `cp` into `~/Library/LaunchAgents/`)
- Tests: `tests/test_cmux_resume_watchdog.py` (234 tests; vendored from `~/projects/user_scope/tests/`)

## Install / Restore (one-shot)

```bash
# 1. Copy the rendered plist into ~/Library/LaunchAgents/
cp ~/.claude/skills/cmux-resume-watchdog/com.$USER.cmux-resume-watchdog.plist.rendered \
   ~/Library/LaunchAgents/com.$USER.cmux-resume-watchdog.plist

# 2. (Re)load it
launchctl bootout gui/$(id -u)/com.$USER.cmux-resume-watchdog 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.$USER.cmux-resume-watchdog.plist

# 3. Verify
launchctl print gui/$(id -u)/com.$USER.cmux-resume-watchdog | grep -E 'state|runs|last exit code'
tail -n 20 ~/Library/Logs/cmux-resume-watchdog.launchd.log
```

## Canonical Pair: cmux Surface Utils

This daemon and `cmux-codex-autoapprove` share `cmux_surface_utils.py` (single-RPC `cmux tree` parsing) and `semantic_classifier.py` (fastembed ONNX predictor with retry/backoff). Both are vendored into each skill's `scripts/` dir so they can be exported via `/exportcommands` independently. When you change one, mirror to the other.

## Purpose

Poll every cmux terminal surface every 120 s. For each surface:
1. Read the visible screen + title (cheap RPC).
2. Classify state via fastembed cosine-similarity to anchor phrases (`ambiguous`, `awaiting_input`, `error`, `idle`). Falls back to a 12 s LLM probe only when fastembed is `ambiguous`.
3. If dead and within the 15-min debounce window, send `Esc` then type a resume prompt containing the `[cmux-resume-watchdog]` marker so downstream surfaces know it was the watchdog that resumed them.
4. Track per-surface `attempt_count` (cap: 24 → action `PAUSE_24H`) and a process-wide `DAILY_RESUME_CAP` (50; resets on UTC date rollover) so a classifier misfire can't cascade.

## Tunables (env vars, exported by `run-cmux-resume-watchdog.sh`)

- `DEBOUNCE_SECONDS` (default 900) — minimum gap between resumes on the same surface.
- `MAX_RESUME_BACKOFF_SECONDS` (default 3600) — exponential backoff ceiling.
- `FASTEMBED_ACTION_THRESHOLD` (0.68) / `FASTEMBED_CLEAR_THRESHOLD` (0.58) — similarity cutoffs.
- `LLM_TIMEOUT_SECONDS` (12) — model probe budget.

## When To Edit

- A real "dead" surface is missed → tighten BUSY/RETRY/TITLE regexes or lower the action threshold.
- A live surface is being resumed → raise the action threshold, fix the anchor phrases.
- `MAX_ATTEMPT_COUNT` / `DAILY_RESUME_CAP` need adjustment → edit the script and re-vendor to both `cmux-codex-autoapprove` and `cmux-resume-watchdog`.

## Debugging

- Logs: `~/Library/Logs/cmux-resume-watchdog.launchd.log`
- Per-surface state: `~/.local/state/cmux-resume-watchdog/state.json`
- Live probe: `python3 ~/.claude/skills/cmux-resume-watchdog/scripts/cmux_resume_watchdog.py --probe-host localhost`
- Tests: `python3 -m pytest ~/.claude/skills/cmux-resume-watchdog/tests/test_cmux_resume_watchdog.py -q`

## Compatibility paths

- Legacy source-of-truth (still editable): `$HOME/projects/user_scope/scripts/cmux_resume_watchdog.py`
- Legacy launchd plist (still installed): `~/Library/LaunchAgents/com.$USER.cmux-resume-watchdog.plist`
- This skill is the exportable copy that ships via `/exportcommands`.