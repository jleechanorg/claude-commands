# Monitored Channel Registry — Jeffrey / $USER

Verified live 2026-07-05 via `mcp_slack__channels_list`. Use these IDs directly in `mcp__slack__conversations_history(channel_id=<id>, limit=N)` calls.

## Tier 1 — Always scan (Jeffrey-direct + active work)

| Channel | ID | Why |
|---|---|---|
| Jeffrey's DM (brief thread anchor) | `D0AFTLEJGJU` | All sweep briefs live here, threaded together |
| #worldai | `C0AH3RY3DK6` | Product PRs + directed asks; jleechanbrain slack |
| #all-$USER-ai | `C09GRLXF9GR` | Operator-Hermes direct line, roadmap posts |
| #worldai-bugs | `C0BDEAJH8PK` | Open bug threads + cost-job investigations |
| #worldai-alerts | `C0BCVG4F560` | BQ coverage / recurring warnings |
| #ai-slack-test | `C0AKALZ4CKW` | agento respawn-cap escalations (single source of truth for stuck-PR backlog) |
| #life | `C0AMM2B4319` | Personal reminders |
| #hermes-pc | `C0BDAMWQQJK` | Hermes-PC takeover / runner health |

## Tier 2 — Scan on alert signal (deploy / health)

| Channel | ID | Trigger |
|---|---|---|
| #disk-usage-alerts | `C0AKNDEARS5` | Only include if last message <12h AND mentions Jeffrey |
| #openclaw-health | `C0AKYEY48GM` | Only include if process state changed since last brief |
| #ralph-status | `C0AGX2Q0EA3` | ralph PR backlog overflow |

## Tier 3 — Read-only context (most sweeps skip)

| Channel | ID | When |
|---|---|---|
| #jleechanclaw | `C0AJ3SD5C79` | Harness PRs |
| #agent-orchestrator | `C0ALSKLU9KM` | AO worker PRs |
| #mcp-mail | `C0A0AG6EELB` | MCP mail ack thread |
| #promotion | `C0AJTVB80TZ` | Domain promo tracker |
| #bug-hunt | `C0ALM55GQCT` | Dogfood bug reports |

## Don't read

| Channel | ID | Why |
|---|---|---|
| #ai-general | `C0AJQ5M0A0Y` | Home channel for system-generated output — sweep is targeted, not ambient |
| #openclaw-chatter | `C0ANK6HFW66` | Openclaw chatter, retired 2026-07-04 |
| #openclaw-canary | `C0AP8LRKM9N` | Disabled per `no-slack-canary-tests` |
| #social | `C09FXQ4U6ET` | Off-topic |

## Sort order for the brief

When the same item shows up in multiple channels, surface it once under the channel where Jeffrey asked. Example: PR 8139 lives in #worldai but is referenced in #all-$USER-ai — lead with #worldai.
