# Live CLI payload capture — 2026-07-30

This file is the source of truth for the cross-cli Stop hook's
unit-test fixtures in
`tests/test_cross_cli_status.py::CLAUDE_LIVE_PAYLOAD` and
`CODEX_LIVE_PAYLOAD`. Re-run the captures below if Claude or Codex
ships a new schema; update the fixtures + the extractor in
lockstep.

## Claude v2.1.220 — `claude --print 'Reply with one word: ping'`

Verified against `$HOME/.local/bin/claude 2.1.220`.

Raw JSON keys observed (Stop hook payload):

```
background_tasks
cwd
effort
hook_event_name          # value: "Stop" (capital S)
last_assistant_message
permission_mode
prompt_id
session_crons           # Claude-only — disambiguator from Codex
session_id
stop_hook_active
transcript_path
```

Important: the Stop hook payload in v2.1.220 does **NOT** carry
`model`, `context_window`, `cost`, or `rate_limits`. Those appear only
in the **statusline** payload. The hook must not require them.

Detector field: `stop_hook_active` + `hook_event_name == "Stop"`
(case-sensitive — Codex uses lowercase `"stop"`).

## Codex 0.144.5 — `codex exec --dangerously-bypass-approvals-and-sandbox 'Reply with one word: pong'`

Verified against `/opt/homebrew/bin/codex codex-cli 0.144.5`.

Raw JSON keys observed (Stop hook payload):

```
cwd
hook_event_name          # value: "stop" (lowercase)
last_assistant_message
model                    # value: STRING (e.g. "gpt-5.6-sol")
permission_mode
session_id
stop_hook_active         # also a Claude field; the casing of hook_event_name disambiguates
transcript_path
turn_id                  # Codex-only — disambiguator from Claude
```

Important: Codex's Stop payload also lacks `usage` (tokens + cost).
The "tokens used 36,000" line in Codex's CLI output is rendered from
a separate, non-hook channel — the hook must not require it.

Detector field: `last_assistant_message` + `turn_id` (the only
field Claude never publishes).

## Hook invocation verification

```
$ cat ~/.claude/var/cross_cli_status/last.json | jq '.cli,.model,.session_id'
"claude"
"claude-opus-5"           ← statusline payload (different channel)
"c726962e-3185-4681-aec2-313689a33360"

$ cat ~/.claude/var/cross_cli_status/last.json | jq '.cli,.model,.session_id'
"codex"
"gpt-5.6-sol"
"019fb560-de6b-7320-a070-5642753ded3d"
```

## Repro

```bash
# Claude
claude --print --dangerously-skip-permissions 'Reply with one word: ping' >/dev/null
jq '.cli,.model,.session_id,.hook_event_name' \
  "$HOME/.claude/var/cross_cli_status/last.json"

# Codex
codex exec --dangerously-bypass-approvals-and-sandbox 'Reply with one word: pong' >/dev/null
jq '.cli,.model,.session_id,.hook_event_name' \
  "$HOME/.claude/var/cross_cli_status/last.json"
```

## Discovery-indirection debug transcript (the hour lost to the
"`codex_hooks.json` is right there, why doesn't Codex read it?" trap)

Codex loads Stop hooks through a TWO-LAYER indirection that vendor
docs do not document:

1. `~/.codex/hooks.json` `Stop[]` does NOT execute the inner commands
   directly. It dispatches to `~/.codex/stop-hook-dispatch.sh`
   (49-line bash script on this machine).
2. The dispatch script reads the cwd from the payload, then checks
   `<cwd>/.codex/hooks.json` for a `Stop[]` config. If found, it
   sets `local_stop_configured=true` and **does not actually run any
   project-local Stop hooks** — the project's Stop entry just
   suppresses the legacy fallback.
3. The actual hook that fires is whatever
   `stop-hook-dispatch.sh` decides to invoke (in this case, the
   legacy `codex-notify-git-header.sh` chain).

The transcript from `/tmp/codex_hooks_run.log` showed the dispatch
running but my new `cross_cli_status.py` was never invoked — because
the project's `<repo>/.codex/hooks.json` Stop entry existed and the
dispatch suppressed everything else.

**Fix**: replace `~/.codex/stop-hook-dispatch.sh` entirely (not just
the project's Stop entries). The new dispatch script shape that
works is documented in the umbrella SKILL.md §1.2.

`codex_hooks.json` (no dot prefix) is also a trap — Codex never reads
that filename. Only `<cwd>/.codex/hooks.json` and
`~/.codex/hooks.json` are honored.

## Cursor + Antigravity + agy payload captures

Not yet captured for this session (no live Cursor / Antigravity / agy
sessions were run during the 2026-07-30 cross-cli work). When those
sessions happen, capture + bake fixtures here in the same shape.

For Cursor, the documented schema is in
`references/live-payload-capture-cursor.md` (TODO). For Antigravity,
the Gemini CLI variant is undocumented for hooks — fall back to the
Gemini-shape fields actually present in the payload.

## Schema drift log

| Date | CLI | Field | Was | Became | Source |
|---|---|---|---|---|---|
| 2026-07-30 | Claude | `hook_event_name` | unknown | `"Stop"` (capital S) | live `claude --print` |
| 2026-07-30 | Codex | `hook_event_name` | unknown | `"stop"` (lowercase) | live `codex exec` |
| 2026-07-30 | Codex | `model` | unknown | top-level STRING (not dict) | live `codex exec` |
| 2026-07-30 | Claude | `model` in Stop | assumed-present | absent (statusline-only) | live `claude --print` |
| 2026-07-30 | Codex | `usage` in Stop | assumed-present | absent (rendered outside hook channel) | live `codex exec` |
