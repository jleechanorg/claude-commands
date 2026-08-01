# Resolver recovery for executive-assistant — worked example (2026-07-22/23)

This file documents a real resolver-recovery path for a scheduled `ea-sweep-hourly` cron where the canonical skill is locally duplicated under `hermes-imports/executive-assistant`. The duplication is intentional (compatibility overlay for older Claude/Codex sessions that pre-date the canonical name) but causes a name collision on bare `skill_view(name='executive-assistant')` in current Hermes sessions.

## Failure mode

```
[IMPORTANT: The following skill(s) were listed for this job but could not be found and were skipped: executive-assistant]
```

This appears at the top of the cron preamble. It is a **resolver error, not a missing-skill error** — the canonical SKILL.md is on disk at `~/.hermes/skills/executive-assistant/SKILL.md`. Don't conclude the workflow is unavailable.

## Three-step fallback chain (in priority order)

### 1. `skill_view(name='hermes-imports/executive-assistant')`

```bash
skill_view(name="hermes-imports/executive-assistant")
```

Picks the named overlay directly. No name collision. Returns the compatibility overlay's SKILL.md body, which is functionally complete for a basic sweep (calendar + gmail + slack, with default DM destination).

### 2. `read_file ~/.hermes/skills/executive-assistant/SKILL.md`

```bash
read_file(path="$HOME/.hermes/skills/executive-assistant/SKILL.md")
```

Bypasses the resolver entirely. Returns the canonical body — the most up-to-date version with all P86–P96 pitfalls, the full reference index, and the resolver-recovery recipe you are reading now. **Use this when the resolver itself is wedged** or when you need the canonical recipe (e.g. the per-sweep destination override logic, the bot-locked-out xoxp fallback, or the `compact-gmail-calendar-digest.md` rendering format).

> **Do NOT rely on** `skill_view(name='executive-assistant/')` as an escape hatch. The trailing-slash form is **not** a documented bypass; in the 2026-07-23 sweep it returned the same ambiguous-name error. If the resolver wants a name, give it a unique one.

### 3. Inspect the overlay as compatibility only

The `hermes-imports/executive-assistant` overlay is intentionally thinner than the canonical (fewer pitfalls, fewer references). Treat it as a stable compatibility shim, not as the source of truth. If the overlay and the canonical disagree (e.g. on the destination override recipe), the canonical wins.

## Worked example — 2026-07-23 08:00 PDT sweep

1. Cron preamble: `[IMPORTANT: The following skill(s) were listed for this job but could not be found and were skipped: executive-assistant]`
2. First response: surfaced the warning to the operator (per the recipe).
3. Tried `skill_view(name='executive-assistant')` → `Ambiguous skill name 'executive-assistant': 2 skills match…`.
4. Tried `skill_view(name='executive-assistant/SKILL.md')` → also ambiguous.
5. Fell back to `read_file` on the canonical path → got the body and proceeded.
6. Posted the brief to `#ai-general` via `HERMES_SLACK_BOT_TOKEN` (resolved to `mcp_agent_mail` / `U0A4G7LDJ4R`; `chat.postMessage` returned `ok=true` with `ts=1784819159.529229`).
7. Returned the same brief as the cron scheduler's final response so the scheduler's auto-delivery channel agrees with the post destination.

The two test `__ping__` messages sent during the post-path probe were cleaned up (`chat.delete`), with one tombstone visible to `USLACKBOT` (the xoxp user-token ping could not be deleted by the bot but the next read showed only the Slackbot-deleted placeholder).

## Why the overlay exists (don't delete it)

Older Claude/Codex sessions that pre-date the `skills/` rename still call `executive-assistant` from the `hermes-imports/` discovery path. Removing the overlay would break those callers' sweep hooks. The overlay is a frozen compatibility shim; only the canonical under `skills/` should receive content updates.

## When NOT to invoke resolver recovery

If the cron preamble says `Skill(s) not found and skipped: some-other-skill`, that's a real missing skill (or one removed by curator), not a resolver collision. In that case, follow the standard missing-skill playbook: load via `read_file` on the path the preamble named, or skip the work and report a clear blocker.
