---
description: Alias for /advice — token-efficient second opinion (Hermes-side overlay)
aliases: [advice, smart-advisor]
type: orchestration
execution_mode: immediate
---

# /ad — Hermes-side Alias for /advice

**This file is the Hermes-side resolver entry for the `/ad` slash command.**
The canonical Claude-side file lives at `~/.claude/commands/advice.md` (283 B, `aliases: [smart-advisor]`).
Hermes runtimes resolve THIS file when the user types `/ad` outside Claude Code.

**Aliases**: `/ad`, `/advice`, `/smart-advisor` — all dispatch to the same skill.

## Why this alias exists (added 2026-07-02)

The user typed `/ad` in Slack thread `C0AJ3SD5C79/p1783036536.864119` and expected it to resolve to `/advice`. Before this commit, only the Claude-side `~/.claude/commands/advice.md` existed, so Hermes Slack/CLI/cron sessions could not invoke `/ad` (the slash-command resolver is runtime-specific). The canonical advice skill itself (`~/.claude/skills/advice/SKILL.md`) is reachable from any runtime via `skill_view(name='advice')`, but the slash-command surface was missing on the Hermes side.

This overlay closes that gap. `/ad` is the shortest unambiguous alias and is what the user types most often — `advice` and `smart-advisor` are listed as additional `aliases:` for backward compatibility.

## Action

When invoked, dispatch to the canonical advice skill:

1. Read `~/.hermes/skills/advice/SKILL.md` (Hermes-side overlay) — falls back to `~/.claude/skills/advice/SKILL.md` if missing.
2. Execute the protocol: extract decision + artifact (≤150 lines), fan out 3 reviewers in parallel (Opus subagent → codex → agy fallback chain + `/research` + `/secondo`), synthesize.

## Per-runtime dispatch

| Runtime | Slash-command resolution |
|---|---|
| Claude Code / Codex | `~/.claude/commands/advice.md` (canonical, identical action) |
| Hermes (Slack / CLI / cron) | `~/.hermes/skills/advice/SKILL.md` (this overlay) |

Both runtimes land at the same 3-reviewer fan-out + synthesis table.

## Usage

```
/ad [optional question]
/ad "should we ship X or Y?"
/ad --decision "the rule fires too rarely" --artifact "workspace/SOUL.md:363-369"
```

## Cross-references

- Canonical slash command: `~/.claude/commands/advice.md`
- Canonical skill: `~/.claude/skills/advice/SKILL.md`
- Hermes overlay skill: `~/.hermes/skills/advice/SKILL.md`
- Hermes ROLES.md entry: `~/.hermes/skills/RESOLVER.md` (auto-discovers via the `skills/` tree)
- Bug-ref: 2026-07-02 Slack C0AJ3SD5C79 ts 1783036536.864119 — user asked to "make an alias /ad point to /advice"