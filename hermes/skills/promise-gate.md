# Promise Gate — Durable Policy Commitment Skill

## Purpose

When making a forward commitment ("I will always X", "from now on Y"), you MUST write the policy to a location that hermes actually loads. This prevents orphaned policy files that feel durable but have no runtime effect.

## Rule: only these locations count

| What you're committing to | Write it here |
|---|---|
| Behavioral policy (how agent acts, reports, dispatches) | Add a section to `~/.hermes/SOUL.md` |
| Tool allow/deny changes | Edit `~/.hermes/TOOLS.md` |
| Heartbeat behavior | Edit `~/.hermes/HEARTBEAT.md` |
| Short checklist for a recurring task | Add a section to `~/.hermes/SOUL.md` |

## NOT valid locations

- `workspace/policies/` — hermes never reads this directory
- `workspace/memory/` — memory, not policy; won't enforce behavior
- Any new ad-hoc `.md` file outside the list above
- Claude Code memory files — those are for Claude sessions, not hermes

## Commitment format (required)

All commitments in `~/.hermes/SOUL.md` MUST use this format:

```markdown
## COMMIT: <short-name>
Trigger: When <event X> occurs
Action: <exact action Y to take>
Added: <YYYY-MM-DD>
```

The `## COMMIT:` prefix is scannable — the session-init protocol and heartbeat audit both grep for it. A vague `## My Policy` section without this format will be invisible to those checks.

## How to use

When about to make a commitment:

1. **Identify the correct file** from the table above.
2. **If the file is `~/.hermes/SOUL.md`** — add a `## COMMIT: <name>` section using the format above.
3. **If the file is `~/.hermes/TOOLS.md` or `~/.hermes/HEARTBEAT.md`** — add a named `##` section in that file's native format (no `## COMMIT:` prefix needed; those files are not scanned by the session-init protocol and enforce commitments through their own mechanisms).
4. **The rule must be trigger-based** — "when X, do Y". Not "I'll try to Y".
5. **In your reply**, reference the exact file path AND section heading.
6. **Commit + push** if the file is in a git-tracked location (`~/.hermes/`).

### Example — correct

> "I updated `~/.hermes/SOUL.md` § `## COMMIT: mcp-mail-ack`. Trigger: when an MCP Agent Mail session-complete update arrives in `#mcp-mail`; Action: ack in-thread with `Ack: <session/task id> — <state> — action needed: yes/no`."

Then in `~/.hermes/SOUL.md`:
```markdown
## COMMIT: mcp-mail-ack
Trigger: When an MCP Agent Mail session-complete update arrives in `#mcp-mail`
Action: Acknowledge in-thread with format: `Ack: <session/task id> — <state> — action needed: yes/no`. If action needed, add one-line escalation.
Added: <YYYY-MM-DD>
```

### Example — WRONG (do not do this)

> "I created `workspace/policies/mcp-mail-ack-tracking.md`."

That file is never loaded. The commitment is theater.

## Cleanup rule

If you discover a file in `workspace/policies/` or another unloaded location:
1. Move the content into the appropriate section of `SOUL.md` or `TOOLS.md`
2. Delete the orphan file
3. Commit both changes together
