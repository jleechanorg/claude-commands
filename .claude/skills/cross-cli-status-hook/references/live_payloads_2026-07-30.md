# Live CLI payload capture — 2026-07-30

This file is the source of truth for the unit-test fixtures in
`tests/test_cross_cli_status.py::CLAUDE_LIVE_PAYLOAD` and
`tests/test_cross_cli_status.py::CODEX_LIVE_PAYLOAD`. Re-run the captures
below if Claude or Codex ships a new schema; update the fixtures + the
extractor in lockstep.

## Claude v2.1.220 — `claude --print 'Reply with one word: ping'`

Verified against `/Users/jleechan/.local/bin/claude 2.1.220`.

Raw JSON keys observed (Stop hook payload):

```
background_tasks
cwd
effort
hook_event_name
last_assistant_message
permission_mode
prompt_id
session_crons
session_id
stop_hook_active
transcript_path
```

Important: the Stop hook payload in v2.1.220 does **NOT** carry
`model`, `context_window`, `cost`, or `rate_limits`. Those appear only
in the **statusline** payload. The hook must not require them.

Detector field: `stop_hook_active` + `hook_event_name == "Stop"` (Codex
uses lowercase `"stop"`).

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
turn_id
```

Important: Codex's Stop payload also lacks `usage` (tokens + cost). The
"tokens used 36,000" line in Codex's CLI output is rendered from a
separate, non-hook channel — the hook must not require it.

Detector field: `last_assistant_message` + `turn_id`.

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
jq '.cli,.model,.session_id' "$HOME/.claude/var/cross_cli_status/last.json"

# Codex
codex exec --dangerously-bypass-approvals-and-sandbox 'Reply with one word: pong' >/dev/null
jq '.cli,.model,.session_id' "$HOME/.claude/var/cross_cli_status/last.json"
```
