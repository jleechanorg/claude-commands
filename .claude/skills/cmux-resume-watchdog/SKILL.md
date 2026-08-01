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

## Install (macOS only)

```bash
cd $(dirname "$0")  # this skill's sibling directory
./install_cmux_resume_watchdog.sh
launchctl print "gui/$(id -u)/com.$USER.cmux-resume-watchdog" | head -20
~/.local/libexec/cmux-resume-watchdog/cmux_resume_watchdog.py --scan-only
```

The install script:
1. Copies `cmux_resume_watchdog.py` to the checkout-independent
   `~/.local/libexec/cmux-resume-watchdog/` (so editing the skill does not
   require re-running the installer — edits to the script file are the
   deployed file because the plist points at the live skill path).
2. Renders the plist template with `$HOME` substituted in.
3. Boots out any pre-existing job + bootstraps the new one.

## Live smoke / triage

```bash
# watch live tick activity
tail -f ~/Library/Logs/cmux-resume-watchdog.launchd.log

# one-shot classification on a specific surface
~/.local/libexec/cmux-resume-watchdog/cmux_resume_watchdog.py --scan-only \
  --workspace workspace:5 --surface surface:75

# per-surface debounce / reset state
python3 -m json.tool < ~/.local/state/cmux-resume-watchdog/state.json | less
```

## What it does NOT do (deliberate non-features)

- **No network/DNS probe** of `api.anthropic.com` / `api.openai.com`. The
  resume decision is purely screen-content-driven. Provider-aware gating was
  deliberately omitted — see PR #38 for the design discussion.
- **No provider-aware gating** — it can resume a Claude surface while OpenAI
  is down and vice-versa. The provider field (`codex` / `claude`) is logged
  but does not affect the resume path.
- **No external LLM call by default.** The 2nd-stage LLM uses
  `$CMUX_RESUME_LLM_MODEL` (default `gpt-5.3-codex-spark`); if it fails,
  fastembed's ambiguous label returns `NOT_ELIGIBLE` and the surface stays
  parked until the next eligible tick.

## Source of truth

The canonical version lives in `$GITHUB_REPOSITORY` `scripts/cmux_resume_watchdog.py`.
This skill is a vendored snapshot that the `/exportcommands` pipeline ships to
`$GITHUB_REPOSITORY`. When the user_scope source changes, re-export
the skill from the your-project.com worktree (the export's Source Surface 2
is `your-project.com/.claude/`).

Re-export flow:
1. Update `$GITHUB_REPOSITORY` first.
2. From `your-project.com` (or its export worktree), copy the new
   `scripts/cmux_resume_watchdog.py` + `tests/test_cmux_resume_watchdog.py`
   into `your-project.com/.claude/skills/cmux-resume-watchdog/`.
3. Run `/exportcommands` → opens a PR against `$GITHUB_REPOSITORY`.

## Provenance

- `$GITHUB_REPOSITORY` PR #38 — dead `cmux list_surfaces` fallback removed
  (no-op call to a subcommand that never existed in cmux).
- Verified live against cmux 0.64.16 (2026-08-01).
