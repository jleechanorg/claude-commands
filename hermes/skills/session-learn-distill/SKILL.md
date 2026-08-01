---
name: session-learn-distill
description: After a complex / multi-turn session (>5 tool calls, multiple spawns, multiple commits, or user corrections), use this skill to extract /learn artifacts (memory + skills) BEFORE ending the session. Triggers on "/learn", "/learn from this session", "anything to learn", "what did we learn", "skillify from this", "save this for next time", or any post-session reflection ask.
---

# Session Learn Distill — /learn workflow

## When to use

After any session that meets ANY of these:
- Spawned >=3 AO workers (multi-PR coordination)
- Made >=3 commits
- User corrected you at least once
- Discovered a new file path / config value / pitfall that future sessions will hit
- Used a workaround or recovery pattern that wasn't documented
- Hit a three-home artifact drift (staging vs prod vs origin/main)
- Ran the cmux codex advisor pattern OR needed to fall back because cmux was wedged

The cost of skipping this is high — every "wtf is this?" Slack thread becomes a 30-min investigation instead of a 30-second skill load.

## Pipeline (in order, every /learn)

### 1. Extract the raw material

Before /learn artifacts, gather:
- The user's original asks (in this conversation)
- The corrections / pushbacks the user gave (those are the highest-value signals)
- The commands that failed and how you recovered
- The files you wrote that contain reusable knowledge
- The mem0 entries you saved (if any)

A quick self-scan: re-read the last 5-10 user messages. For each correction, ask: "would future-me hit this same trap?" If yes, /learn it.

### 2. Decide the destination

For each piece of knowledge, pick the right bucket:

| Type of knowledge | Destination | Why |
|-------------------|-------------|-----|
| User preferences, personal facts | `mem0_conclude` (persistent across all sessions) | Survives even when skills aren't loaded |
| Stable environment facts (paths, configs, ports) | `memory` action='add' (in-session memory) | Available immediately in current session |
| Durable workflows (5+ steps, multiple commands) | `skill_manage` action='create' (new SKILL.md) | Loaded on-demand by future sessions |
| Specific pitfalls / gotchas | Patch an EXISTING skill with `skill_manage` action='patch' | Lives where future lookups will find it |
| Three-home artifact contract | Patch `~/.hermes_prod/SOUL.md` `## COMMIT:` sections | Enforced by session-init scan |
| User explicitly asked for a report in `~/roadmap` (verified 2026-07-20, Slack `C09GRLXF9GR/p1784573431`) | Also write a dedicated `~/roadmap/<topic>-YYYY-MM-DD.md` | Short-form audit trail lives in the monthly log; the dedicated report is the referenceable artifact |

**Anti-pattern:** Don't put environment facts in skills (they go in memory). Don't put preferences in memory if they're session-specific.

### 3. Apply the 5-rail closure contract (per three-home artifact rule)

For any new skill or SOUL.md patch:
1. Write to `~/.hermes_prod/` (runtime, prod)
2. Copy to `~/.hermes/` (staging)
3. `git add` + `git commit` + `git push origin main` (origin)
4. Verify: `git ls-files`, `git show origin/main:<path>`, count lines
5. Log SHA in report / Slack reply

If any of the 5 rails is missing, the skill is not durable.

### 4. Test the trigger

After writing the skill, write 2-3 realistic trigger queries ("show me the iteration budget skill when I ask...") and verify it triggers. The `skill-creator` skill has the full eval pattern.

### 5. Tell the user what was learned

End with a 1-line per artifact summary:
- `mem0: <entry name>` (saves to long-term memory)
- `~/.hermes/skills/<name>/SKILL.md` (new skill, 5-rail closed)
- `~/.hermes/skills/<existing>/SKILL.md` patched (pitfall added)
- `~/.hermes_prod/SOUL.md` patched (COMMIT: added)

This lets the user audit what's in their harness.

## Common mistakes

- **Stopping at the report push.** The /roadmap skill has a documented bug-ref where the agent stopped at "report pushed, here are the issues" — same pattern. /learn must include the COMMIT-PUSH step.
- **Putting static config in skills.** If a value is a single number (e.g. "Hermes is at 1000 turns"), it goes in memory, not a 200-line skill. Skills are for workflows.
- **Not testing the trigger.** A skill that exists but never loads is worse than no skill (false confidence). Use the eval pattern.
- **Three-home drift.** A skill only in `~/.hermes_prod/` is gone on next `~/.hermes` reset. Always commit.

## This-session worked example (2026-06-27)

In the /roadmap session that triggered this skill:
- **L1 (new skill):** `hermes-budget-fields` — documents the 3 distinct iteration fields. Created this turn.
- **L2 (patch existing skill):** `agento` SKILL.md — added `--claim-pr auto` pitfall. Pushed to origin/main commit `0efe263bdd`.
- **L3 (patch existing skill):** `roadmap` SKILL.md — added Step 8.5 /a fullrun drive phase. Pushed to origin/main commit `8d6e888a4a`.
- **L4 (mem0):** `hermes-budget-fields-three`, `ao-no-iteration-concept`, `auto-cron-clarification`.
- **L5 (commit + push):** 4 commits on `jleechanorg/jleechanclaw`, 4 commits on `jleechanorg/roadmap`, all on origin/main.

Total artifacts produced in 1 turn: 1 new skill + 2 skill patches + 3 mem0 entries + 8 commits.

## Related

- `skillify` — class-level skill with the full skill creation pattern
- `skill-creator` — eval-driven skill improvement loop
- `hermes-deploy-pipeline` — staging/prod/origin sync contract
- `mem0_search` / `mem0_conclude` — memory tool reference
- `~/.hermes_prod/SOUL.md` `## COMMIT: three-home-artifact-closure-contract`

## Hermes-side `wiki-ingest` resolver gap (added 2026-07-20)

The Claude-side `/wiki-ingest` skill lives at `~/.claude/skills/wiki-ingest/SKILL.md` and is **not** in the Hermes resolver (`skill_view(name='wiki-ingest')` returns "Skill not found" from Hermes sessions). When running /learn closure from a Hermes session, this skill's "Always wiki-ingest (call the skill, do not write files manually)" rule cannot be honored.

**Fallback when wiki-ingest is unreachable from the runtime:**
1. Write `~/llm_wiki/wiki/sources/<slug>.md` directly via `write_file` with full YAML frontmatter (title, type, tags, sources, created, updated) — match the format used by existing source pages in the wiki
2. Write/update `~/llm_wiki/wiki/entities/<name>.md` for every named entity (orgs, hosts, tools) — same frontmatter shape
3. Prepend a Sources entry at the top of `~/llm_wiki/wiki/index.md` `## Sources` section (after the `## Sources` heading, before the first existing entry) via `patch` mode=replace targeting the heading + first-row anchor
4. Append `## [YYYY-MM-DD] ingest | <title>` to `~/llm_wiki/wiki/log.md` listing every file created/updated
5. Use `[[wikilinks]]` in source pages linking to entity pages (e.g. `[[Prime Radiant]]`, `[[Cloud-Superpowers-Build]]`)

This deviation from the Claude-side `/learn` skill's "do not write files into `~/llm_wiki/wiki/` directly" rule is acceptable because the rule's purpose (forcing the skill to do entity/concept extraction) cannot be honored when the skill is unreachable. **Long-term fix**: ship a Hermes-side overlay at `~/.hermes/skills/wiki-ingest/SKILL.md` so `skill_view(name='wiki-ingest')` resolves from any runtime — separate bead.
