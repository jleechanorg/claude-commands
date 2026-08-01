---
name: disk-root-cause
description: Run the disk-root-cause forensic skill to explain disk growth — min/floor deltas, attributable buckets, safe cleanup recommendations (no destructive commands without explicit OK).
metadata:
  type: command
  runtime: claude
---

# /disk-root-cause

Thin slash command that delegates to the `disk-root-cause` skill. Same effects as invoking the skill directly; this command exists so users get a single namespace entry point.

## Behavior

When the user types `/disk-root-cause <optional question>`, this command:

1. Loads the skill at `skills/disk-root-cause/SKILL.md`.
2. Falls back to the canonical skill invocation if the local copy is missing.
3. Returns whatever the skill returns.

## Examples

```text
/disk-root-cause
/disk-root-cause why is my disk filling up
/disk-root-cause what grew in the last week
/disk-root-cause find the min disk used last month and show delta vs now
/disk-root-cause how much can I safely reclaim
```

## Notes

- This command is intentionally read-only. Safe cleanup commands appear in the skill's readout as recommendations, not auto-ran.
- Whenever the skill needs real-time evidence, the skill points the operator at `./disk_magician.sh snapshot` (which is itself safe and idempotent).
- See `skills/disk-root-cause/SKILL.md` for the full procedure.
