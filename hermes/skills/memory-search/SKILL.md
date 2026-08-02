---
name: memory-search
description: "Search across all memory systems — ~/roadmap, beads, claude memories, hermes sqlite, hermes briefings, hermes index, wiki, history, and slack. Use whenever the user asks to search memories, find something in memories, or looks for anything that might have been captured in any memory store. Trigger on: 'search memories', 'find in my memories', '/ms', '/memory_search', 'search across all memories', 'look up in memory', 'did I save this somewhere', 'do I have anything about X in memory'."
---

# Memory Search (Hermes-side overlay)

**This file is the Hermes-side resolver entry for the `memory-search` skill.**
The canonical implementation lives at `~/.claude/skills/memory-search/SKILL.md` (Claude Code user-scope).
Hermes's `skill_view(name='memory-search')` resolves this overlay directly; if your runtime cannot find this overlay, fall back to the Claude-side file.

## Why this overlay exists (added 2026-07-02)

Before 2026-07-02, `~/.hermes/skills/memory-search/SKILL.md` did NOT exist. SOUL.md's `## COMMIT: ms-on-new-task` told Hermes agents to call `skill_view(name='memory-search')` but the resolver could not find it from `~/.hermes/skills/` — only from `~/.claude/skills/`. Telemetry from `~/.hermes/state.db` showed 0 of the 1,951 tool-using sessions in 7 days called `memory-search` via `skill_view`; only the slash-command surface (`/ms`) worked, and only from Claude Code / Codex runtimes. This overlay closes the resolver gap so `skill_view(name='memory-search')` works from any runtime (Slack, CLI, cron, terminal).

## How to execute the 9-store fan-out

Read the canonical implementation at `~/.claude/skills/memory-search/SKILL.md` and execute its `Execution` section. The 9 sources are:

1. `~/roadmap` — Project roadmaps and planning docs (`~/roadmap/`)
2. `beads` — Issue/bead tracking (`br search "$QUERY" --json | head -40`)
3. `claude memories` — Session memories (`~/.claude/projects/*/memory/`)
4. `hermes sqlite` — `~/.hermes/state.db` (`messages` table + FTS5 trigram index). NOTE: `~/.hermes/memory.db` is 0 bytes — DO NOT use it
5. `hermes briefings` — `~/.hermes/memory/briefing-*.md`, `mcp-mail-ack-log.md`
6. `hermes index` — `~/.hermes/MEMORY.md`
7. `wiki` — `~/llm_wiki/`
8. `history` — `~/.claude/projects/*/*.jsonl` (use 2-phase grep with -m flag, never read raw)
9. `slack` — `mcp__slack__conversations_search_messages` (skip if MCP unavailable)

Run all 9 searches in parallel via `delegate_task` (or `/e` subagents in Claude Code). Cache TTL = 1 hour, cache dir = `~/llm_wiki/.cache/memory-search/`.

## Parallel fan-out via `delegate_task` (when in-line fan-out isn't viable)

When the agent runtime cannot run all 9 searches in a single in-line turn (e.g. Slack-routed session with no `mcp__slack__conversations_search_messages`, or a research task that needs to ingest a multi-MB Google Doc corpus + a 9-store memory search + a file-audit in the same turn), use **3 parallel `delegate_task` calls** instead of one in-line fan-out:

1. **Task A — `file-audit`**: read every file in a known directory tree relevant to the query, capture verbatim content + cross-references + mechanical rules. Returns a structured audit document.
2. **Task B — `memory-search`**: run the 9-store fan-out with **multiple fused queries** (don't run one search per store per query — fuse 3-5 related queries and accept partial overlap).
3. **Task C — `domain-corpus`**: any third storage class the task needs (Google Drive via `gog drive search`, Beads, local repo greps). Returns an inventory table.

This is the pattern that worked for "redesign all god/multiverse mechanics" on 2026-07-20: 3 parallel subagent tasks → 3 ~20-50K-char structured audits → single human-readable synthesis in the parent session. Cache the 3 task outputs as `/tmp/redesign_task{0,1,2}.md` so they can be re-read in chunks (read_file truncates at ~50K chars inline).

**Don't** delegate the synthesis step itself. The parent session must own the cross-referencing and the user-facing summary — subagent summaries are self-reports, not verified findings.

**Don't** mix `delegate_task` with `web_extract` / `web_search` in the same batch — different tool availability profiles, and Tavily is disabled in this runtime per env-preferences.

## Delivery contract — receipts before questions

When the user asks "find + read X" (a multi-source research task), **deliver the receipts first**, then ask the next-step question. The 2026-07-20 "redesign god/multiverse mechanics" session was corrected by the user mid-flight with "Status on this and did you truly find and read aizen campaign and all the others I asked?" because the agent had moved to a `clarify` tool call without first posting the inventory table. Pitfall pattern:

- WRONG: read sources → draft `clarify` choice list → post "Pick: A/B/C"
- RIGHT: read sources → post inventory table (file ID, size, mod date, 1-sentence "why this matters") → THEN ask single-scope question

The inventory table IS the deliverable for any "find and read X" task. The next-step question (if any) goes AFTER it.

## Per-runtime invocation

| Runtime | How to invoke |
|---|---|
| Claude Code / Codex | Type `/ms <query>` (slash command resolves to `~/.claude/commands/ms.md`) |
| Hermes (any runtime) | `skill_view(name='memory-search')` reads THIS overlay, then execute the 9-store fan-out |
- Cron / launchd / cmux | `skill_view(name='memory-search')` + execute fan-out via `delegate_task` |

**Pitfall — `web_extract` is broken on plain-text endpoints in this runtime (confirmed 2026-07-10):** Calls to `web_extract(urls=["https://...github.../raw/..."])` fail with `"DuckDuckGo (ddgs) is a search-only backend and cannot extract URL content. Set web.extract_backend to firecrawl, tavily, exa, or parallel."` DDGS is the configured `web.extract_backend` and is search-only. **Fallback: use `terminal(curl)` for any plain-text endpoint** (`.md`, `.txt`, `.json`, `.yaml`, `raw.githubusercontent.com`, documented API endpoints). For JS-rendered or interactive pages, use the Aside browser (`mcp__aside-mcp__*`) or Playwright headless (`mcp__playwright-mcp`). Never retry `web_extract` expecting a different result on the same URL — it fails identically. The env-preferences rule already says "prefer curl via terminal for plain-text endpoints" but the overlay didn't enforce it; this pitfall codifies it as a known failure mode to skip past on the first try.

**Pitfall — WorldArchitect campaign search by premise lives in TWO stores (Firestore AND wiki raw transcripts):**

WA campaign premises are duplicated across Firestore (live data) and the LLM wiki (ingested snapshots from `download-campaign`). A premise-only search that hits Firestore alone will return false positives and miss the wiki-ingested original where the user's own words live.

| Store | Path | Holds |
|---|---|---|
| Firestore (live) | `users/{uid}/campaigns/{campaign_id}/story/{entry_id}` | LLM-generated description blocks for the first ~5 entries; premise paraphrased |
| Wiki raw transcripts | `~/llm_wiki/raw/campaigns/<campaign_id>/<Title>_<id>.md` / `.txt` / `_game_state.json` | Full session transcripts — premise is in the player's opening "God Mode:" prompt and first 1-3 scenes |
| Wiki source summaries | `~/llm_wiki/wiki/sources/<slug>.md` | Curated one-paragraph summary per ingested campaign |
| Wiki catalog index | `~/llm_wiki/wiki/index.md` | One-line entry per campaign — fastest signal for "do we have anything on this trope?" |

**When to fire this pitfall:** User asks "find my WA campaign where [premise]" AND the Firestore scan returns matches that don't describe the user's premise AND the user hints "the wiki" / "I think the campaign might be in the LLM wiki." Switch immediately to wiki fan-out — do not re-scan Firestore with broader keywords.

**Recipe when user names a trope ("demon lord reincarnation," "investigate daughter from past life," "Isekai"):**

```bash
# 1. Wiki catalog index — fastest (curated one-liners)
grep -i -E "<trope-keywords>" ~/llm_wiki/wiki/index.md

# 2. Wiki source summaries — paraphrased premise per campaign
grep -lir -E "<trope-keywords>" ~/llm_wiki/wiki/sources/

# 3. Wiki raw transcripts — full text (premise in opening God Mode prompt)
grep -lir -E "<trope-keywords>" ~/llm_wiki/raw/campaigns/

# 4. Wiki concepts/entities — cross-refs (faction, character, setting pages)
grep -lir -E "<trope-keywords>" ~/llm_wiki/wiki/concepts/ ~/llm_wiki/wiki/entities/
```

**Worked example (2026-07-28):** user asked "find the campaign where I was reincarnated and investigating my daughter from a past life." Firestore scan returned 14 false positives (`Aristocrat reborn V2` Sylphina being reincarnated as a seventh daughter; `Gaia Julia` Caesarion "thinks he is the reincarnation of Horus"; `Alexiel` absorbing a demon king's heart — not reincarnation as one). User follow-up: "I was a demon lord or demon king reincarnation I think the campaign might be in the LLM wiki." Wiki grep on `reincarnat|reborn|iseki` immediately surfaced `~/llm_wiki/raw/campaigns/dUfl4Adb3oH6foczNFSZ/Iseki v1_dUfl4Adb.txt`. Opening God Mode prompt: "Let's make me a reincarnation of a great demon lord… I killed half the worlds population but I had a good reason and I was level 25 but a band of heroes finally defeated me but I only lost because my child's life was in danger during battle." Scene 19 confirmed the daughter from a past life: "Future plot arc where I meet my child again from when I was a demon lord. She's now level 20 and will be primary antagonist for an arc." Both descriptions the user gave across two turns landed on this single campaign — `Iseki v1` / character `Renjiro` / Firestore campaign ID `dUfl4Adb3oH6foczNFSZ` / 112 story entries / created 2026-06-19 / last played 2026-06-27. **Lesson:** the user's own words live in the God Mode opening of the raw transcript, NOT in the Firestore description block which the LLM rewrites. Always include `~/llm_wiki/raw/campaigns/` in the search path when premise-only Firestore search returns false positives.

## Aggregation output format

```
# Memory Search: "<query>"

## ~/roadmap
[results]

## Beads
[results]

## Claude Memories
[results]

## Hermes SQLite
[results]

## Hermes Briefings
[results]

## Hermes Index
[results]

## Wiki
[results]

## History
[results]

## Slack
[results]
```

## Cross-references

- Canonical implementation: `~/.claude/skills/memory-search/SKILL.md` (Claude Code user-scope)
- Trigger rule: `~/.hermes/workspace/SOUL.md` `## COMMIT: ms-on-new-task`
- Per-session fan-out: `~/.hermes/workspace/AGENTS.md` `Session-Start Recall Routine`
- Audit detector: `~/.hermes/scripts/audit_ms_proactive_firing.sh` (verifies firing rate after each deploy)
- Mirror: `~/.codex/skills/memory-search/SKILL.md` (Codex-readable, kept in sync)
- Bug-ref: 2026-07-02 Slack C0AJ3SD5C79 ts 1783036536.864119 — user asked to root-cause + fix `/ms` not firing proactively