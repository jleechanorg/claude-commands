---
name: granola-cli
description: Query and fetch Granola meeting notes from the terminal. Wraps the official Granola MCP server via joelhooks/granola-cli (HATEOAS JSON). Use when Jeffrey asks about "my meetings", "meeting notes", "what did we discuss in <meeting>", action items from a call, or wants a transcript.
---

# Granola CLI

Agent-first wrapper over the Granola MCP server (`https://mcp.granola.ai/mcp`). Every command returns a JSON envelope, no plain text — designed to be parsed by an LLM agent.

## Binary

- Built from source: `joelhooks/granola-cli` (Bun)
- Compiled to: `~/.local/bin/granola`
- Depends on `mcporter` (`/opt/homebrew/bin/mcporter`)
- Config: `~/.config/granola-cli/mcporter.json`
- Credentials: `~/.mcporter/credentials.json` (OAuth, browser flow on first use)

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

## Commands

| Command | Purpose | MCP tool |
|---|---|---|
| `granola` | Self-documenting command tree + health check | `list_meetings` |
| `granola meetings [--range this_week\|last_week\|last_30_days\|custom] [--start YYYY-MM-DD] [--end YYYY-MM-DD]` | List meetings by time range | `list_meetings` |
| `granola meeting <id> [--transcript]` | Full details, summary, attendees (and transcript if flagged) | `get_meetings` / `get_meeting_transcript` |
| `granola search "query"` | Natural-language search with citations | `query_granola_meetings` |

**Time-range defaults:** if you pass no `--range` to `meetings`, it falls back to `this_week`. For "today's meetings" use `--range custom --start YYYY-MM-DD --end YYYY-MM-DD`.

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

**Get a specific meeting's summary + action items:**
```bash
granola meeting <id>
```

**Get the full transcript:**
```bash
granola meeting <id> --transcript
```

**Search across all notes:**
```bash
granola search "action items about billing"
```

## Output shape

Every command returns a JSON envelope:
```json
{ "ok": true, "command": "granola meetings", "result": { ... }, "next_actions": [...] }
```
On failure: `{ "ok": false, "command": "...", "error": { "message": "...", "code": "AUTH_EXPIRED", "fix": "..." } }`

`AUTH_EXPIRED` and `MCP_DISABLED` are the two codes you'll see most. Both are recoverable:
- `AUTH_EXPIRED` → `granola auth`
- `MCP_DISABLED` → enable MCP in Granola Settings → Integrations → MCP

## Pitfalls

- **OAuth must complete in browser.** If you SSH in, tunnel port 61200 first: `ssh -L 61200:127.0.0.1:61200 <host> -N`
- **No GitHub release yet** (as of 2026-06-11) — `install.sh` 404s on `releases/latest`. Use the build-from-source fallback above.
- **PATH:** `~/.local/bin` is not in the default macOS PATH. Either export it per shell or add to `~/.zshrc` / `~/.bashrc`.
- **Empty list is not always "no meetings".** It can mean the OAuth scope is wrong, or the date range straddles weeks. Check `connected: true` via bare `granola` first.
- **Transcripts are large.** A 60-min meeting transcript can be 20-50KB. Don't dump it into Slack — summarize with the LLM first.

## When to use

✅ "What were my meetings today?" / "Pull my action items from this morning's call"
✅ "What did we decide about <topic> last week?"
✅ "Get the transcript of the <X> sync"
❌ Live calendar / scheduling — Granola is read-only. Use Google Calendar MCP or `gog` for that.
❌ Recording new meetings — that happens inside the Granola Mac app, not via CLI.
