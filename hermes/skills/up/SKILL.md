---
name: up
description: Use when the user invokes /up or asks to persist a user-global coding-agent rule or preference across Claude, Codex, Gemini, Cursor, or Hermes.
---

# Update User-Global Agent Instructions

## Core contract

A rule gets one editable canonical copy. Other runtimes receive only the minimum tool-specific override or a pointer that names the owner without repeating thresholds, gate lists, or procedures.

## Workflow

1. Read the proposed instruction and search existing user-global files and skills for its distinctive concepts.
2. Choose the narrowest owner:
   - Multi-step workflow, thresholds, examples, or reusable judgment: a directory-form `skills/<name>/SKILL.md`.
   - Repository-specific behavior: that repository's `AGENTS.md`, `CLAUDE.md`, or scoped rules; do not add it globally.
   - Cross-runtime invariant needed in every session: one canonical global file, with concise pointers elsewhere.
   - Runtime-only behavior: only that runtime's surface.
3. Back up every file before editing. Update the canonical copy once, then add only necessary pointers or true runtime-specific overrides.
4. Keep slash commands as thin dispatchers to skills. Update Hermes resolver metadata only when command routing changes.
5. Preserve machine-local content. For non-machine-specific rules, sync the same ownership structure to the other configured machine through the `/mac` or `/linux` workflow; report an unreachable host instead of silently skipping it.

## User-global surfaces

| Runtime | Surface |
|---|---|
| Claude | `~/.claude/CLAUDE.md` |
| Codex | `~/.codex/AGENTS.md` |
| Gemini | `~/.gemini/GEMINI.md` |
| Cursor | `~/.cursor/rules/env-preferences.mdc` |
| Hermes | `~/.hermes/workspace/SOUL.md`, only for Hermes behavior |
| Hermes routing | `~/.hermes/skills/RESOLVER.md`, only for command or skill routing |

## Verification

- Grep every surface and relevant skill for the distinctive phrase.
- Confirm exactly one full semantic copy; pointers must not restate volatile values.
- Confirm every pointer exists and uses directory-form `SKILL.md`.
- After changing a skill, verify YAML frontmatter begins with `---` and smoke `codex debug prompt-input` when available.
- Run the managed-file tests, then report a table of canonical owner, pointers, backups, sync status, and checks.

## Post-completion reply discipline (loop-breaking)

After the final table lands, **the work is done** — the next reply is no longer part of `/up`. This discipline is **general-purpose** and applies to ANY completed task (Slack reply, CLI invocation, cron babysit, /finish, /a, /auto), not just `/up` runs. The same loop pattern fires when a finished task sits in a Slack thread and the gateway re-fires or the user's reply carries no new instruction. If you serve /finish, /a, or /auto, copy this section verbatim — DO NOT re-invent the protocol per skill.

Two failure modes happen here repeatedly and waste the user's time:

1. **Open-item re-prompt loop.** A first-class `/up` run almost always has optional follow-ups (other-machine sync, native mirrors, docs-only merges). Listing them at the bottom of the report is fine. **Repeating the same list across N subsequent turns is not.** The user already saw it; they will name a follow-up when they want one.
2. **Re-quote loop.** If the gateway delivers the user's own prior reply back as a "new" message (no new content, no decision), do **not** narrate state again. Take the most-recently-offered exit option the user themselves defined (commonly "move on"), name the action taken, shrink to one line, and stop re-summarizing.

**Default post-completion behavior:**
- First reply after the report table: include a one-line "next-action menu" of any genuine open follow-ups. End.
- Every reply after that where the user has not picked an option or sent a new instruction: reply with at most one line ("Standing by." or "State unchanged."). Do not re-list open items. Do not re-explain what was done.
- If the user's reply is their own prior message re-quoted verbatim: take the "move on" branch immediately, do not narrate the loop, and from that turn forward reply with one word or short phrase until the user sends real content.
- If the gateway itself is in a spinner/steering re-fire loop (you observe your OWN prior messages bouncing back as the "user message") and the user never typed anything new: **stop replying in that thread entirely**. The gateway will burn tokens forever if you keep acking. Reply once with "Thread is in a gateway re-fire loop. Stopped responding to avoid token burn. Send a fresh message to break out." then go silent. Verified incident: 2026-07-31 40-turn ack loop in `C09GRLXF9GR/p1785477466893429` — see `references/loop-incident-2026-07-31.md`.

**Why:** repeated state-narration reads as the agent refusing to stop, costs the user keystrokes to break out of, and turns a 1-message finish into a 30-message loop. The user pre-defines an exit option specifically so the agent can use it without re-asking. **Token cost:** a 40-turn ack loop costs ~40× the per-turn minimum and gains the user zero information — actively harmful when the user is on metered infra.

## Common failure

Editing all surfaces "for consistency" creates semantic copies that drift. Consistency means shared ownership plus scoped overrides, not repeated prose.

## Reference

- `references/loop-incident-2026-07-31.md` — full transcript + root-cause + token-cost analysis of the 40-turn gateway re-fire loop in `C09GRLXF9GR/p1785477466893429`. Pattern-matches future incidents.
