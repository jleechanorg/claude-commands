---
name: cmux-resume-watchdog
description: Use when idle cmux Claude Code / Codex CLI sessions stall on quota exhaustion or network/API failures and need a daemon to auto-resume them. Bundles the watchdog Python script, run wrapper, launchd plist template, and test suite in a sibling directory.
---

# cmux-resume-watchdog — auto-resume stalled cmux sessions

A single launchd daemon (`com.$USER.cmux-resume-watchdog`) that watches
**all cmux terminal surfaces** every 120 s and un-stalls idle Claude Code /
Codex CLI sessions that died from one of two failure modes:

1. **Quota stalls** — usage/session-limit banner ("You've hit your session limit",
   "individual quota reached", etc.). Banner's reset time is parsed; surface is
   parked until that time passes.
2. **Network/API stalls** — last turn died from connectivity or API failure
   (`ENOTFOUND`, `connection lost`, `API Error`, `Request rejected`).

It inspects every terminal surface via `cmux tree --all --json`, classifies the
visible tail using a two-stage pipeline (fastembed + LLM fallback), then
applies the matching resume path with exponential backoff (15 m → 30 m → 1 h
→ 1 h, capped).

## Files (in this skill's sibling directory)

| File | Role |
|---|---|
| `cmux_resume_watchdog.py` | The daemon — discovers cmux sockets, enumerates terminal surfaces, classifies screen tail, sends resume prompt + Enter with debounce. |
| `run-cmux-resume-watchdog.sh` | launchd wrapper: sources `~/.bash_profile`, unsets `OPENAI_API_KEY` + `CMUX_SOCKET*`, execs the script with `--daemon --interval 120` via the `~/.local/orch-venv/bin/python3` that has fastembed/numpy/onnxruntime. |
| `com.$USER.cmux-resume-watchdog.plist.template` | launchd job template with `@HOME@` placeholder. |
| `install_cmux_resume_watchdog.sh` | Renderer + installer: copies the script to `~/.local/libexec/cmux-resume-watchdog/`, renders + loads the plist. Re-run after editing the Python script. |
| `semantic_classifier.py` | FastEmbed anchor-phrase classifier (imported by the watchdog for screen-tail classification). |
| `test_cmux_resume_watchdog.py` | Regression tests (44 tests; covers classification, debounce, list_terminal_surfaces, send_resume ordering). |
| `SKILL.md` | This file (single-file mirror for the cmux-steer.md convention). |

## Install (macOS only)

```bash
cd "$(dirname "$0")/cmux-resume-watchdog"
./install_cmux_resume_watchdog.sh
launchctl print "gui/$(id -u)/com.$USER.cmux-resume-watchdog" | head -20
~/.local/libexec/cmux-resume-watchdog/cmux_resume_watchdog.py --scan-only
```

## Live smoke / triage

```bash
tail -f ~/Library/Logs/cmux-resume-watchdog.launchd.log
python3 -m json.tool < ~/.local/state/cmux-resume-watchdog/state.json | less
```

## Source of truth

Canonical: `$GITHUB_REPOSITORY` `scripts/cmux_resume_watchdog.py`. This skill
is the vendored snapshot that `/exportcommands` ships to
`$GITHUB_REPOSITORY`.

See the sibling directory's `SKILL.md` for the full design notes + provenance.
