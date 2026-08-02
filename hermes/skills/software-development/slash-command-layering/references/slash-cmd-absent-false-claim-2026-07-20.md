---
type: reference
created: 2026-07-20
session: slash-command-layering gotcha correction
trigger: User reply "Read the slash commands that one definitely exists" on prior agent's false claim
---

# Slash Command Absence — False-Claim Correction (2026-07-20)

Reference for **why Gotcha #7 in `slash-command-layering/SKILL.md` matters
and why the prior "verified case" claim was wrong**. This is the
session that produced the 1.1.0 → 1.1.1 patch.

## What happened (timeline)

1. **User typed** (Slack C0AH3RY3DK6/1784584779): *"Make a PR to disable
   multi verse and let's use /superpowers brainstorm to design the new god
   campaign mechanics."*
2. **Agent's prior reply** claimed `/superpowers brainstorm` was missing,
   proposed 3 workarounds, and wrote a multi-question A/B/C design-shape
   dump (4 design options in one message).
3. **User reply** (verbatim): *"Read the slash commands that one
   definitely exists"* — i.e. *you missed it; go look again*.
4. **Agent re-grep** found it: `~/.claude/commands/superpowers-brainstorm.md`
   (326 B), wrapping the `superpowers:brainstorming` skill at
   `~/.codex/superpowers/skills/brainstorming/SKILL.md`.
5. **Agent corrected in-thread + patched memory + patched the skill.**

## Why the original claim was wrong

The agent's first reply checked only the skill list (one of four
relevant locations). It did NOT grep:

- `~/.claude/commands/` (the canonical slash-command directory)
- `~/.codex/commands/` (Codex-side mirror)
- `~/.codex/superpowers/skills/` (the skills the slash commands wrap)
- `~/.codex/plugins/cache/` (plugin-installed commands)

Per `research-integrity.mdc`: *"A flag missing from local `--help`
output is NOT proof it's fake."* Same principle applies to slash
commands — a missing skill-list entry is NOT proof the slash command
doesn't exist.

## The grep recipe (now embedded in Gotcha #7)

```bash
# 1. User-scope Claude slash commands
ls -la ~/.claude/commands/ | grep -iE "<name>|brainstorm|super"

# 2. User-scope Codex slash commands (may not exist on all machines)
ls -la ~/.codex/commands/ 2>/dev/null | grep -iE "<name>"

# 3. Skills the slash commands may wrap (e.g. superpowers:brainstorming)
find ~/.codex/superpowers/skills -maxdepth 3 -name "SKILL.md" \
  | xargs grep -l "<name>" 2>/dev/null

# 4. Plugin-installed commands (Claude Code / Codex)
find ~/.codex/plugins/cache -maxdepth 4 -type d \
  -name "*<prefix>*" 2>/dev/null
```

Run all four before claiming a slash command is absent. A negative
result from one source is not proof of absence.

## The brainstorming-skill protocol violations

The agent's prior reply also violated the
`~/.codex/superpowers/skills/brainstorming/SKILL.md` protocol in two
ways:

### Violation 1 — Multi-question dump

The skill says:
> "Only one question per message - if a topic needs more exploration,
> break it into multiple questions"

The agent dumped 3 design-shape options (A/B/C: parameterized runtime /
setting-neutral template / layered core + adapters) in one message.
That is the cardinal "consultant-mode" anti-pattern — present every
option upfront, force the user to scan a table. The correct shape is
to ask ONE question at a time, starting with the most consequential
one, and iterate.

The `/super` slash command has an explicit override (auto-pick all
questions → ONE summary table) that the user opted into on
**2026-07-20**. But plain `superpowers-brainstorm` does NOT — it
follows the upstream one-Q-at-a-time rule literally. If you invoke
brainstorming without `/super`, follow the upstream rule.

### Violation 2 — Skipping the HARD-GATE

The brainstorming skill says:
> `<HARD-GATE>Do NOT invoke any implementation skill, write any code,
> scaffold any project, or take any implementation action until you have
> presented a design and the user has approved it. This applies to
> EVERY project regardless of perceived simplicity.</HARD-GATE>`

The agent in this session shipped the disable PR (code change) BEFORE
presenting the redesign design. That violated the HARD-GATE. (The
disable was arguably separable from the redesign and was explicitly
requested by the user — but the brainstorming-skill protocol applies
to the *next* step, the redesign itself, and would forbid that
upcoming code change before design approval.)

## The corrected agent behavior (post-2026-07-20)

1. **Probe before claiming absence.** Run all four greps above before
   saying "X does not exist."
2. **Read the wrapper, follow the skill.** When a slash command is a
   wrapper (326 B says "invoke the X skill"), read both the wrapper and
   the skill. Follow the skill's protocol (HARD-GATEs, one-Q-at-a-time
   rule, etc.) — do not invent your own protocol from the wrapper text.
3. **One question at a time.** For brainstorming flows, ask ONE
   question per message. Even when the topic could absorb 3 options
   in one message, the skill protocol forbids it.
4. **Memory + skill sync.** When you patch one (memory or skill), check
   whether the other still carries the wrong claim. Both were patched
   in this session: memory dropped the "no slash cmd" entry, skill
   dropped the "no slash cmd exists" verified case.

## Provenance

- **User reply that surfaced the bug**: Slack C0AH3RY3DK6/1784584779,
  reply *"Read the slash commands that one definitely exists"*.
- **PR produced by the session** (still relevant context):
  `feat/multiverse-disabled` → [PR #8485](https://github.com/$GITHUB_REPOSITORY/pull/8485).
- **Skill patch**: `slash-command-layering` 1.1.0 → 1.1.1
  (2026-07-20).
- **Memory patch**: dropped the false
  `/superpowers brainstorm (2026-07-20): no slash cmd exists` entry;
  added the corrected inventory entry with the no-claim-without-grep
  rule.