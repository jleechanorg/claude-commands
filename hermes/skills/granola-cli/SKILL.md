---
name: granola-cli
description: Query and fetch Granola meeting notes from the terminal. Wraps the Granola MCP server via `mcporter` (joelhooks/granola-mcp-plus). Use when Jeffrey asks about "my meetings", "meeting notes", "what did we discuss in <meeting>", action items from a call, or wants a transcript.
tags: []
---

# Granola CLI

Agent-first wrapper over the Granola MCP server. Two layers:

1. **High-level CLI** — `~/.local/bin/granola` (joelhooks/granola-cli, Bun-compiled) — user-friendly commands returning JSON envelopes
2. **Low-level MCP** — `/opt/homebrew/bin/mcporter` driving `granola-mcp-plus` (npx) — direct tool calls when the CLI's wrapper breaks

The CLI is convenient but it sometimes hides failure modes (returns empty payloads when the underlying MCP returns 401). **When the CLI returns empty results, go around it via `mcporter call granola <tool>` directly.**

## Binary

- `~/.local/bin/granola` — built from `joelhooks/granola-cli` (Bun)
- `/opt/homebrew/bin/mcporter` — MCP CLI (0.7.3 as of 2026-07-13)
- Config: `~/.config/granola-cli/mcporter.json` (granola-cli) OR `~/.mcporter/mcporter.json` (mcporter — same OAuth credentials)
- Credentials: `~/.mcporter/credentials.json` (OAuth, browser flow on first use)
- MCP transport: `STDIO $HOME/.nvm/versions/node/v22.22.0/bin/npx -y granola-mcp-plus`

## Setup (one-time)

```bash
curl -fsSL https://raw.githubusercontent.com/joelhooks/granola-cli/main/install.sh | sh
# Fallback when no GitHub release exists (build from source):
git clone https://github.com/joelhooks/granola-cli.git /tmp/granola-cli
cd /tmp/granola-cli
bun build src/cli.ts --compile --outfile ~/.local/bin/granola
```

```bash
export PATH="$HOME/.local/bin:$PATH"
granola auth   # opens browser for OAuth approval
```

## Commands (CLI)

| Command | Purpose |
|---|---|
| `granola` | Self-documenting command tree + health check |
| `granola meetings [--range this_week\|last_week\|last_30_days\|custom] [--start YYYY-MM-DD] [--end YYYY-MM-DD]` | List meetings by time range |
| `granola meeting <id> [--transcript]` | Full details, summary, attendees (and transcript if flagged) |
| `granola search "query"` | Natural-language search — **wraps `search_granola_notes`** (notes) + `search_granola_transcripts` (transcripts) under the hood |

**Time-range defaults:** if you pass no `--range` to `meetings`, it falls back to `this_week`. For "today's meetings" use `--range custom --start YYYY-MM-DD --end YYYY-MM-DD`.

## ⚠️ MEETING ID FORMAT — PATCH (added 2026-07-13)

The `granola meetings` list returns IDs as **8-character hex prefixes** (e.g. `0332337e`, `b07e705d`). But the `granola meeting <id>` command and the underlying `get_meetings` MCP tool require **full UUIDs** (e.g. `0332337e-0000-0000-0000-000000000000`).

Passing the short prefix returns: `MCP error -32602: Input validation error: Invalid arguments for tool get_meetings: Invalid uuid`. Passing the short prefix with the dash-padded suffix above returns: `{"meetings": [], "not_found": ["0332337e-0000-0000-0000-000000000000"]}` (the padded UUID doesn't match the real one).

**The `0332337e` you saw in `meetings` list is just a display prefix.** The real UUID is elsewhere — currently no CLI path I know surfaces it. Workarounds:

1. Use `granola search "..."` (natural-language) — doesn't need the UUID
2. Use `mcporter call granola get_meetings` with NO arguments (the MCP server may return recent meetings with full UUIDs) — **does not currently work either**, the tool requires the ID
3. Best workaround today: synthesize from the meeting list (titles + dates) and acknowledge the transcript is unavailable

This is a known gap — flag for upstream if it bites another session.

## Direct MCP tools (via mcporter) — for when the CLI breaks

List actual tools:

```bash
mcporter list granola --schema
mcporter list granola --json  # full schema
```

**The actual MCP tool names (verified 2026-07-13 via `mcporter list granola --schema`):**

| MCP tool name | Purpose |
|---|---|
| `search_granola_notes(query, limit=10)` | Search notes/documents by query string. Returns matching documents with their content. |
| `search_granola_transcripts(query, limit=10)` | Search transcripts by query string. Returns matching transcripts with their content. |
| `search_granola_events(query, ...)` | Search calendar events by query. |

**Wrong tool names from prior versions of this skill** (don't try these — they don't exist):
- ~~`get_meetings`~~ — exists but requires UUID IDs (see above)
- ~~`get_meeting_transcript`~~ — not exposed by current MCP server
- ~~`query_granola_meetings`~~ — old name; current server uses `search_granola_notes`

## Common recipes

**List today's meetings:**

```bash
TODAY=$(date +%Y-%m-%d)
granola meetings --range custom --start "$TODAY" --end "$TODAY"
```

**Pull this week's meeting titles only (jq):**

```bash
granola meetings | jq -r '.result.meetings[]? | "\(.date)  \(.title)"'
```

**Search for content across notes (preferred over per-meeting fetch):**

```bash
granola search "action items about billing"
```

**When the CLI returns empty: bypass with mcporter:**

```bash
mcporter call granola search_granola_notes query="verification gap" limit=10
mcporter call granola search_granola_transcripts query="software factory" limit=10
```

## Output shape

Every `granola` command returns a JSON envelope:

```json
{ "ok": true, "command": "granola meetings", "result": { ... }, "next_actions": [...] }
```

On failure: `{ "ok": false, "command": "...", "error": { "message": "...", "code": "AUTH_EXPIRED", "fix": "..." } }`

`AUTH_EXPIRED` and `MCP_DISABLED` are the two codes you'll see most. Both recoverable:
- `AUTH_EXPIRED` → `granola auth` (or `mcporter auth granola --reset`)
- `MCP_DISABLED` → enable MCP in Granola Settings → Integrations → MCP

**`mcporter call granola search_granola_notes ...` returns a raw error envelope, NOT the CLI envelope:**

```json
{ "error": "Granola API error: 401 Unauthorized" }
```

This is the canonical "Granola OAuth is dead" signal — same fix as `AUTH_EXPIRED`.

## Pitfalls

- **OAuth must complete in browser.** If you SSH in, tunnel port 61200 first: `ssh -L 61200:127.0.0.1:61200 <host> -N`
- **No GitHub release yet** (as of 2026-06-11) — `install.sh` 404s on `releases/latest`. Use the build-from-source fallback above.
- **PATH:** `~/.local/bin` is not in the default macOS PATH. Either export it per shell or add to `~/.zshrc` / `~/.bashrc`.
- **Empty list is not always "no meetings".** It can mean the OAuth scope is wrong, or the date range straddles weeks, OR the underlying MCP returned 401. Check `connected: true` via bare `granola` first. If `granola` says connected but `granola meeting <id>` returns empty bodies, run `mcporter call granola search_granola_notes` to disambiguate.
- **Meeting IDs from `meetings` list are 8-char hex prefixes, not full UUIDs.** `granola meeting <short-id>` returns `Invalid uuid`. See "MEETING ID FORMAT" patch above.
- **Transcripts are large.** A 60-min meeting transcript can be 20-50KB. Don't dump it into Slack — summarize with the LLM first.
- **`mcporter` is at `/opt/homebrew/bin/mcporter`, not `/usr/bin/mcporter`.** Calling `/usr/bin/mcporter` returns `No such file or directory` even though it's installed. PATH should already cover this; if not, use the full path.
- **`mcporter call granola list_meetings` returns an error envelope `{ "error": "Unknown tool: list_meetings" }`** — that tool name doesn't exist in current server. Use `search_granola_events` or fall back to `granola meetings` CLI.

## When to use

✅ "What were my meetings today?" / "Pull my action items from this morning's call"
✅ "What did we decide about <topic> last week?"
✅ "Get the transcript of the <X> sync"
❌ Live calendar / scheduling — Granola is read-only. Use Google Calendar MCP or `gog` for that.
❌ Recording new meetings — that happens inside the Granola Mac app, not via CLI.

## Related skills

- `granola-email-only-pipeline` (devops category) — the `jleechanorg/granola-exporter` cron that emails consolidated notes; uses the same `mcporter` MCP layer.