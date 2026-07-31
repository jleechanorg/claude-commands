---
name: cross-cli-status-hook
description: Unified Stop hook for claude, codex, cursor, antigravity, and agy. Normalizes model / token / cost / rate-limit fields across all four CLIs into a single JSON record at ~/.claude/var/cross_cli_status/last.json.
triggers:
  - "cross cli ratelimit hook"
  - "cross-cli stop hook"
  - "rate limit hook for claude codex cursor antigravity"
  - "unified stop hook"
  - "agy hook"
version: 1.0.0
---

# cross-cli-status-hook

A single Python Stop hook that reads the JSON payload on stdin from **any
of**: `claude` (Code CLI), `codex` (Codex CLI), `agy` (the agy wrapper),
`cursor` (Cursor agent), `antigravity` (Gemini CLI's `antigravity` flavor),
and writes one normalized record to
`~/.claude/var/cross_cli_status/last.json` (plus an append-only
`history.jsonl`).

## Why it exists

The legacy `stop-git-header-json.sh` only read the Codex Stop payload
(`rate_limits.block_reset_seconds`, `usage.cost_usd`). It silently dropped
Claude's `rate_limits.five_hour.used_percentage`, Cursor's
`status/loop_count`, and Antigravity's `decision` field. Verified
regression on 2026-07-17: a fixture-tested Codex hook failed to read the
real Codex `tool_input.cwd` field because Codex 0.144+ nests it
differently than the docs claimed.

The cross-CLI hook:

1. detects which CLI fired the hook from `HERMES_HOOK_CLI` env with
   payload-shape fallbacks (`stop_hook_active` + `session_crons` =>
   claude; `last_assistant_message` + `turn_id` => codex;
   `conversation_id` + `generation_id` => cursor; Gemini-style decision
   block => antigravity; else unknown);
2. normalizes into a single schema: `cli`, `model`, `context_pct`,
   `tokens_in`, `tokens_out`, `cost_usd`, `rate_limit_pct`,
   `rate_limit_window`, `rate_limit_reset_at`, `cwd`, `pr_url`,
   `header_status`, `received_at`, `event`, `raw_keys`;
3. merges the legacy `git-header.sh --status-only` first line + first PR
   URL so callers downstream do not lose them;
4. is **fail-closed by default**: if no recognized CLI is detected and
   no recognizable payload shape matches, it writes a record with
   `cli="unknown"` + the full raw key set so a future regression does
   not silently swallow the payload. Use `--strict` to also exit
   non-zero (only recommended for `Stop` hooks that should not block the
   turn).

## File layout

| File | Purpose |
| --- | --- |
| `.claude/hooks/cross_cli_status.py` | The hook itself (executable Python). |
| `codex_hooks/cross_cli_status.sh` | Codex-only launcher that resolves repo-local vs home-scope install. |
| `.codex/stop-hook-dispatch.sh` | Replaces the legacy dispatcher; runs the cross-CLI hook + mem0_save. |
| `codex_hooks.json` | Codex `hooks.json` registration (Stop event). |
| `claude-settings.json` | Claude `settings.json` registration (Stop event). |
| `cursor_hooks.json.template` | Cursor agent-hooks overlay (`stop` event). |
| `antigravity_hooks.toml.template` | Antigravity `hooks.toml` overlay (`AfterAgent` event). |
| `.agy/cross_cli_status.md` | agy install instructions. |
| `tests/test_cross_cli_status.py` | 20 unit tests (fixtures + live payload shapes). |
| `tests/integration/test_cross_cli_live_tmux.py` | Live tmux integration (run with `CROSS_CLI_LIVE=1`). |

## Verified against real CLI payloads (2026-07-30)

| CLI | Version | Real payload keys | Detector field |
| --- | --- | --- | --- |
| `claude` | 2.1.220 | `cwd, session_id, prompt_id, transcript_path, last_assistant_message, stop_hook_active, session_crons, effort, background_tasks, permission_mode, hook_event_name` | `stop_hook_active` + `hook_event_name == "Stop"` |
| `codex` | 0.144.5 | `cwd, hook_event_name, last_assistant_message, model, permission_mode, session_id, stop_hook_active, transcript_path, turn_id` | `last_assistant_message` + `turn_id` |
| `agy` | 1.1.8 | Inherits the Codex envelope (OpenAI-compatible). | `HERMES_HOOK_CLI=agy` env override |
| `cursor` | 3.11.13 (cursor agent) | `conversation_id, generation_id, model, model_id, status, loop_count` | `conversation_id` + `generation_id` |
| `antigravity` | Gemini CLI variant | `cwd, session_id, model, decision` | (best-effort; only Gemini-style fields are public) |

The detector and the extractors are **fail-soft**: missing fields are
recorded as `null` and the file is still written. The detector and the
extractors were updated **after running real `claude --print` and
`codex exec` sessions** to capture the actual payload keys (not the
docs-promised ones); see `tests/test_cross_cli_status.py` for the
captured fixtures.

## Quick install

```bash
# 1. Symlink the hook into both codex + claude home hooks dirs:
ln -sf "$(git rev-parse --show-toplevel)/.claude/hooks/cross_cli_status.py" \
       "$HOME/.claude/hooks/cross_cli_status.py"
ln -sf "$(git rev-parse --show-toplevel)/.claude/hooks/cross_cli_status.py" \
       "$HOME/.codex/hooks/cross_cli_status.py"

# 2. Replace the Codex Stop dispatcher with the cross-cli version:
cp "$(git rev-parse --show-toplevel)/.codex/stop-hook-dispatch.sh" \
   "$HOME/.codex/stop-hook-dispatch.sh"

# 3. Add the Claude Stop hook to ~/.claude/settings.json (snippet below).

# 4. Cursor: copy cursor_hooks.json.template to <repo>/.cursor/hooks.json
#    and Cursor auto-discovers it.

# 5. Antigravity: copy antigravity_hooks.toml.template to
#    <repo>/.gemini/hooks.toml (or merge into ~/.gemini/settings.toml).
```

`~/.claude/settings.json` Stop snippet:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'HERMES_HOOK_CLI=claude HERMES_HOOK_EVENT=Stop python3 $HOME/.claude/hooks/cross_cli_status.py; exit 0'",
            "description": "Cross-CLI Stop status (claude/codex/cursor/antigravity/agy)"
          }
        ]
      }
    ]
  }
}
```

## Inspecting the output

```bash
# Most recent payload
jq '{cli, model, rate_limit_pct, rate_limit_window, rate_limit_reset_at, pr_url}' \
  "$HOME/.claude/var/cross_cli_status/last.json"

# Last 20 events (one JSON per line)
tail -20 "$HOME/.claude/var/cross_cli_status/history.jsonl" | \
  jq -c '{ts: .received_at, cli, model, rl: .rate_limit_pct, win: .rate_limit_window}'

# Watch a live session
watch -n 2 'jq -C "{cli, model, rate_limit_pct, rate_limit_window, header_status, pr_url}" \
  "$HOME/.claude/var/cross_cli_status/last.json"'
```

## Known limitations

1. **Cursor's `stop` payload does not expose rate-limit % fields.** The
   Cursor app surfaces rate limits in the UI badge, not in the hook
   payload. The hook reports `rate_limit_pct=100` with
   `rate_limit_window="loop_storm"` as a heuristic when `status="error"`
   + `loop_count >= 4` so callers can still alert.
2. **Antigravity's `AfterAgent` schema is not officially documented.** The
   hook surfaces whatever Gemini-shaped fields are present; the
   `decision` field is the only one we can rely on. Coverage will expand
   once antigravity publishes a hook schema.
3. **The Claude Stop payload in v2.1.220 does NOT carry `model`,
   `context_window`, or `cost` fields** — those only appear in the
   statusline payload. The hook records `null` for those keys when the
   Stop event fires; downstream callers that need them should subscribe
   to a statusline hook instead.
4. **Codex Stop payload also lacks `usage` (tokens + cost).** The
   `tokens used 36,000` line in Codex's CLI output is rendered from a
   separate, non-hook channel.

## Cross-references

- Companion skill: `~/.claude/skills/advice/SKILL.md` (the
  cross-CLI review used to verify this hook).
- Hook tests: `tests/test_cross_cli_status.py` (20 unit tests) +
  `tests/integration/test_cross_cli_live_tmux.py` (live tmux, gated on
  `CROSS_CLI_LIVE=1`).
- Live fixture capture log: `references/live_payloads_2026-07-30.md`
  (raw transcript of the two real `claude --print` + `codex exec` runs
  whose payloads are baked into the unit tests).
