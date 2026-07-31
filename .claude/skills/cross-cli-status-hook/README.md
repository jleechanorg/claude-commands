# cross-cli status hook (2026-07-30)

Unified Stop hook for **claude / codex / cursor / antigravity / agy**.
Reads the JSON payload each CLI writes to stdin on Stop, normalizes
model / token / cost / rate-limit fields across all four shapes, and
emits a single record to `~/.claude/var/cross_cli_status/last.json`.

## TL;DR

- One Python hook handles every CLI's Stop payload.
- Auto-detects the CLI from payload shape; `HERMES_HOOK_CLI` env
  overrides if you want to force a particular branch.
- Captures rate-limit state for Claude (5h + 7d), Codex (block-reset
  seconds), Cursor (loop-storm heuristic), Antigravity (decision
  field), agy (Codex envelope).
- Fail-closed: unknown payloads are recorded with `cli="unknown"` and
  the full raw key set so a future regression never silently drops data.
- 20 unit tests + a live-tmux integration suite (run with
  `CROSS_CLI_LIVE=1`).

## Files

| File | Purpose |
| --- | --- |
| `.claude/hooks/cross_cli_status.py` | The hook (executable). |
| `.codex/hooks/cross_cli_status.py` | Repo-local mirror (Codex 0.144+ resolves this). |
| `codex_hooks/cross_cli_status.sh` | Codex-only launcher (repo vs home scope). |
| `.codex/stop-hook-dispatch.sh` | Replaces the legacy Codex Stop dispatcher. |
| `codex_hooks.json` | Codex `hooks.json` registration (Stop event). |
| `claude-settings.json` | Claude `settings.json` registration (Stop event). |
| `cursor_hooks.json.template` | Cursor `hooks.json` overlay. |
| `antigravity_hooks.toml.template` | Antigravity `hooks.toml` overlay. |
| `.agy/cross_cli_status.md` | agy install instructions. |
| `tests/test_cross_cli_status.py` | Unit tests (20 cases; fixtures + live shapes). |
| `tests/integration/test_cross_cli_live_tmux.py` | Live tmux integration. |
| `.claude/skills/cross-cli-status-hook/SKILL.md` | Skill entry. |

## Install

```bash
git clone https://github.com/jleechanorg/claude-commands
cd claude-commands

# 1. Symlink the hook into both home hooks dirs:
ln -sf "$(git rev-parse --show-toplevel)/.claude/hooks/cross_cli_status.py" \
       "$HOME/.claude/hooks/cross_cli_status.py"
ln -sf "$(git rev-parse --show-toplevel)/.claude/hooks/cross_cli_status.py" \
       "$HOME/.codex/hooks/cross_cli_status.py"

# 2. Replace the Codex Stop dispatcher:
cp "$(git rev-parse --show-toplevel)/.codex/stop-hook-dispatch.sh" \
   "$HOME/.codex/stop-hook-dispatch.sh"
chmod +x "$HOME/.codex/stop-hook-dispatch.sh"

# 3. Add the Claude Stop hook to ~/.claude/settings.json (see SKILL.md
#    for the JSON snippet).

# 4. Cursor: copy cursor_hooks.json.template to <repo>/.cursor/hooks.json
# 5. Antigravity: copy antigravity_hooks.toml.template to ~/.gemini/
```

## Run the tests

```bash
python3 -m unittest discover -s tests -p 'test_cross_cli_status.py' -v

# Live tmux (requires real claude / codex on PATH and CROSS_CLI_LIVE=1):
CROSS_CLI_LIVE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## What the hook writes

`~/.claude/var/cross_cli_status/last.json`:

```json
{
  "cli": "claude",
  "received_at": "2026-07-30T23:34:54+00:00",
  "event": "Stop",
  "model": null,
  "context_pct": null,
  "tokens_in": null,
  "tokens_out": null,
  "cost_usd": null,
  "rate_limit_pct": 12,
  "rate_limit_window": "5h",
  "rate_limit_reset_at": 1785398400,
  "session_id": "c726962e-3185-4681-aec2-313689a33360",
  "version": null,
  "cwd": "/private/tmp/cc-hooks-ratelimit",
  "header_status": "...",
  "pr_url": "https://github.com/jleechanorg/claude-commands/pull/338",
  "raw_keys": ["background_tasks", "cwd", "effort", "..."],
  "error": null
}
```

`~/.claude/var/cross_cli_status/history.jsonl`: one JSON object per
event, trimmed to the most recent 500 (override via
`CROSS_CLI_STATUS_HISTORY_MAX`).

## Why the old hook failed

The legacy `codex_hooks/stop-git-header-json.sh` only knew Codex's
payload shape. Claude's `rate_limits.five_hour.used_percentage`,
Cursor's `status/loop_count`, and Antigravity's `decision` were all
silently dropped. The fix: a single Python module that knows the
field-name table for all four CLIs and emits a normalized record.
