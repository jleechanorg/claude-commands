---
name: cli-usage-audit
description: Daily request/token/cost breakdown across every AI CLI installed on this Mac (Claude Code, Codex, Hermes, OpenCode, Gemini, Kimi, Qwen, Copilot, Goose, Kilo, Droid, OpenClaw, Amp, Codebuff, Pi). Trigger when the user says "how many requests do I do daily", "what am I spending on AI", "AI usage report", "daily AI cost", "token breakdown per day", "show me my per-day usage", "ai-usage-tracker", or any natural-language request for a daily AI-tool activity report. Encodes the three-source recipe (ccusage hermes + direct JSONL parsing of ~/.claude/projects and ~/.codex/sessions) that survives the schema-mismatch bug in the `ai-usage-tracker-js` npm wrapper, the 180s `ccusage daily --json` timeout trap, the executable-bit permission-denied trap on the wrapper shim, and the Claude `source` filter that separates real REPL prompts from agent-internal tool-loop rows. Verified 2026-07-21 against 7,558 Codex sessions, 6,348 Claude JSONLs, 30-day Hermes window.
---

# CLI Daily Usage Audit (per-CLI, per-day)

A reproducible recipe for "how many requests / how much $$ / how many tokens do I generate per day across all my AI CLIs". The `ai-usage-tracker-js` npm wrapper does *not* work end-to-end on this machine as of v0.1.5 — its output is empty/zeros for Claude and Codex (schema-mismatch bug, see Pitfall 1). The recipe below is the verified replacement.

## TL;DR

```bash
# Three independent commands, all under ~60s when run in parallel:
SINCE=$(date -v-30d +%Y-%m-%d)

# A) Hermes — fastest, cleanest, has request count per day
ccusage hermes daily --since "$SINCE" --order desc --json

# B) Claude Code REPL prompts — direct JSONL parse (filter agent-internal rows!)
#    see scripts/daily_usage_audit.py for the full extractor

# C) Codex CLI — also direct JSONL parse (different schema from ccusage-codex)
#    see scripts/daily_usage_audit.py
```

Run **all three in parallel via `terminal(background=true, notify_on_complete=true)`**, then pipe the outputs into the canonical formatter in `scripts/daily_usage_audit.py`. That script returns one combined Markdown table with daily Hermes/Claude/Codex rows + 30-day totals + peak day.

## What the user actually wants

The user almost always asks for **"requests per day"**, not tokens. They tolerate tokens/cost as context. Distinguish:
- **Hermes** request count = `messageCount` field from `ccusage hermes daily --json` (clean, direct).
- **Claude Code** request count = number of `type=user && source in (None,"repl_main") && has_text` rows in `~/.claude/projects/**/<session>.jsonl`, bucketed by the row's `timestamp` field. **Do NOT use the total row count** — it inflates 10–100× because agent-internal tool-loop rows are also `type=user` but with `source="agent_progress"|"compact"|...` and no human text content. Use the `source` filter; the `has_text` check on the `message.content` (str or list-of-text-blocks) is the tie-breaker. Pitfall 2.
- **Codex CLI** request count = number of `type=event_msg && payload.type=="user_message"` rows in `~/.codex/sessions/**/rollout-*.jsonl`, bucketed by the inner `timestamp` field. The top-level Codex schema is `{"timestamp","type","payload":{...}}` — different from ccusage's. Pitfall 3. Use **inner timestamp** not file mtime; sessions that ran across midnight (or got rotated to an archive dir) bucket wrong by hours/days if you key off mtime.

The three counts are not directly comparable (one Hermes call ≠ one Claude prompt ≠ one Codex user-message turn) but together they describe the user's daily AI tool activity.

## Pitfall 1 — `ai-usage-tracker-js` v0.1.5 is broken on this machine

**Symptom:** the wrapper prints an empty table / 0/0/0 rows when invoked with `--days 30`. It also has TWO permission traps:

```bash
$ ai-usage-tracker-js --help
bash: $HOME/.nvm/versions/node/v22.22.0/bin/ai-usage-tracker-js: Permission denied

$ ls -la $HOME/.nvm/versions/node/v22.22.0/bin/ai-usage-tracker-js
lrwxr-xr-x@ 1 $USER  staff  48 Mar  6 01:49 ... -> ../lib/node_modules/ai-usage-tracker/dist/cli.js
# ^ symlink missing +x bit; chmod +x fixes the symlink target only if run via the
# wrapper path; cleanest is `node <abs path>/dist/cli.js`

$ ccusage daily --since 2026-06-21 --json
# 180s tool timeout, exits 124, empty output — full log scan, not the data shape
```

**Root cause:** the wrapper expects `ccusage daily` to emit per-day `totalTokens` / `totalCost` AND assume each entry has a request count. But `ccusage daily` (v0.x) has schema `[{date, totalTokens, totalCost, modelBreakdowns:[...], metadata:{agents:[...]}}]` — the `metadata.agents` field is now `["claude","codex","gemini","hermes"]` (aggregated!) AND there's no `messageCount`/`requests` field on the day row. Worse, `ccusage-codex daily` returns a *different* schema (`{date, inputTokens, outputTokens, totalTokens, costUSD, models:{...}}`) — also no request count. The wrapper's combined output ends up zero for Claude and zero for Codex because the schema keys it reads (`entry.totalCost` for codex) are wrong.

**Workaround (preferred): bypass the wrapper entirely and use `ccusage hermes daily --json` for the Hermes column (clean request counts) + direct JSONL parsing for Claude + Codex. The wrapper cannot be salvaged by patching alone; it needs a v0.2 that pulls per-day request counts from each tool's native log format.**

**Workaround (less preferred):** `chmod +x $HOME/.nvm/versions/node/v22.22.0/bin/ai-usage-tracker-js` first (resolves the Permission denied trap), then run `ccusage daily` / `ccusage-codex daily` in `terminal(background=true, notify_on_complete=true)` with a 300s timeout — they will finish in ~8–9 minutes each on a 30-day window with this machine's log volume. Output still has zero request counts; only useful for tokens/$.

## Pitfall 2 — Claude JSONL `source` filter is the only thing separating "user prompts" from "agent internals"

The Claude Code session JSONL files (`~/.claude/projects/<cwd-hash>/<session-id>.jsonl`) write a row for every agent turn, not just yours. The rows look like:

```json
{"type":"user","isMeta":true, ...}                  // ignore (hook/meta rows)
{"type":"user","source":"repl_main","message":{"content":"Fix the bug"}}  // COUNT
{"type":"user","source":"agent_progress","message":{"content":[{"type":"text","text":"..."}]}}  // skip
{"type":"user","source":"compact","message":{"content":"Compaction summary..."}}  // skip
{"type":"user","source":null,"message":{"content":"..."}}  // COUNT (newer SDK convention)
```

**Counterexample if you ignore the filter:** a single day with a busy Opus session can produce 10,000+ `type=user` rows, of which 200–1,500 are real REPL prompts. Reporting the unfiltered count (e.g. "24,111 prompts/day") is misleading by an order of magnitude.

**Verified filter (2026-07-21, 6,348 JSONL files, 30 days):**
- Keep iff `type == "user" and isMeta != true and source in (None, "repl_main") and message.content has text`.
- Counts: 22,491 REPL prompts across 30 days → avg **726 prompts/day**, in 6,519 distinct sessions.
- Skipping the `source` filter inflates to ~240,000 rows over the same window — >10× too high.

Distinct sessions per day is a useful second axis: `obj["sessionId"]` is populated on every row. Today (2026-07-21) showed 299 distinct sessions for 542 prompts — high concurrency (multiple parallel agent invocations).

## Pitfall 3 — Codex JSONL schema is `event_msg` + inner `payload.type`, not what ccusage-codex says

`~/.codex/sessions/**/rollout-<timestamp>-<uuid>.jsonl` looks like:

```json
{"timestamp":"2026-06-03T19:19:05.123Z","type":"session_meta","payload":{"id":"..."}}
{"timestamp":"...","type":"event_msg","payload":{"type":"task_started"}}      // 1 per Codex CLI invocation
{"timestamp":"...","type":"event_msg","payload":{"type":"user_message"}}       // 1 per user prompt
{"timestamp":"...","type":"event_msg","payload":{"type":"agent_message"}}     // 1 per assistant turn
{"timestamp":"...","type":"response_item","payload":{"type":"message"}}        // not a turn event
{"timestamp":"...","type":"response_item","payload":{"type":"function_call"}}
{"timestamp":"...","type":"event_msg","payload":{"type":"token_count"}}
```

**Bucketing rule:** use the inner `obj["timestamp"]` (ISO 8601 with `Z` suffix) and convert to local date. **Do NOT use file mtime** — sessions get archived/rotated, so the mtime reflects when the file was last touched, not when the events occurred. Observed drift: a session that ran 2026-07-19 had its JSONL mtime 2026-07-20 because the file was finalized the next day.

**Request count definitions:**
- `event_msg.payload.type == "user_message"` = 1 user prompt (analog to Claude REPL prompt) — **30-day total 11,476** for this user, avg **370/day**.
- `event_msg.payload.type == "agent_message"` = 1 assistant turn. Inflated by tool-call round-trips: 30-day total **125,940** — ~11× user-prompt count.
- `event_msg.payload.type == "task_started"` = 1 Codex CLI invocation (analog to Claude `sessionId`): **30-day total 12,145**.

Pick `user_message` for the "requests per day" column; it's the closest analog to "I typed a thing into a CLI today".

## The script (canonical, run this — don't hand-type the JSONL parsing)

`scripts/daily_usage_audit.py` does all three pulls, joins by local-date, prints a single Markdown table plus 30-day totals. It runs in ~70 seconds on this machine with the typical log volume. Re-run it on any ask of the form "daily AI usage" — no human retyping required.

```bash
python3 ~/.hermes/skills/devops/cli-usage-audit/scripts/daily_usage_audit.py --days 14
```

Output shape:
```
DATE        HERMES     HERMES $   CLAUDE PROMPTS   CLAUDE SESSIONS   CODEX PROMPTS   CODEX AGENT-MSG
2026-07-21   2,887    $  25.52            542              299             283             990
...

=== 30-day totals ===
  Hermes            : 181,212 requests   $597.67   -> 5,846/day
  Claude Code REPL  :  22,491 prompts         $0   ->   726/day  (in 6,519 distinct sessions)
  Codex session entr.: 11,476 user_prompts   $0   ->   370/day
```

## When the user asks a narrower question

| User asks for | Recipe | Notes |
|---|---|---|
| "how many requests do I do daily" | full 3-column audit | this skill |
| "Hermes-only" / "gateway only" | `ccusage hermes daily --since SINCE --json` | 5–10s, reliable, has both msg + cost |
| "Claude Code tokens" | `ccusage claude daily --since SINCE --json` | slow (~8min for 30d, 180s timeout hits often); schema is tokens/$ aggregated across all agents under `metadata.agents` |
| "Codex tokens" | `ccusage-codex daily --since SINCE --json` | slow, schema `{date, totalTokens, costUSD, models:{...}}` |
| "what models did I use" | `ccusage hermes daily --json` → `modelsUsed` field | gives the model roster |
| "am I over my rate limit" | out of scope — use `verify-telemetry-alert` skill |

If the user wants **just Hermes** or **just one CLI**, skip the JSONL parses and run only the `ccusage <agent>` subcommand. Hermes comes back in ~5s.

## Companion skills

- `context-token-audit` — single-session context composition (different concern: how big is THIS conversation, not how much did I send across all sessions).
- `gcp-cost-diagnosis-bq-billing-export` — same shape for cloud bills (BQ billing export vs local JSONLs). Parallel class.
- `mac-disk-pressure-triage` — parallel class for filesystem usage.
- `swap-hermes-provider` — when a daily-usage report reveals the user is overspending on a specific model tier.

## Support files

- `scripts/daily_usage_audit.py` — the canonical 3-source extractor. Run this; don't re-derive.
- `references/2026-07-21-ai-usage-tracker-js-schema-bug.md` — first documented instance of the wrapper's empty-output bug + the JSONL `source` filter discovery.
- `references/codex-session-schema.md` — full Codex rollout JSONL schema reference + per-event-type meanings.

## Reporting findings (template)

```
🟢 **AI CLI daily usage — last 14 days**
DATE        HERMES     HERMES $   CLAUDE   CODEX   | daily notes
2026-07-21   2,887    $25.52      542     283    | <-- today
...

📊 30-day totals:
• Hermes:       181,212 requests, $597.67, avg 5,846/day
• Claude Code:   22,491 REPL prompts, 6,519 sessions, avg 726/day
• Codex:         11,476 user prompts, avg 370/day (avg ~11× tool-call round-trips)

Peak: 2026-06-23 — 15,298 Hermes requests, $44.32
```

Always include the raw JSON paths (`/tmp/ccusage_*.json` if you generated them) so the user can re-run / cross-check.