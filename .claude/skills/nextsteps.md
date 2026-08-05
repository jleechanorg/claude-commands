---
name: nextsteps
description: "Default: update beads and ~/roadmap (parallel). Use --full for full situational assessment with memory sync, learnings, nextsteps doc, and GitHub issues."
---

# /nextsteps — Beads & Roadmap Update

## Default mode (no flags)

Gather context, then **write updates** — beads and `~/roadmap`. Run in parallel; agent/subagent tool use is explicitly allowed and encouraged.

### Step 1 — Gather context (parallel)

Run all of these concurrently:

- `git log --oneline -10` — recent commits
- `br list --status open --limit 0` — open beads
- `ls ~/roadmap/` — roadmap files
- Read `~/roadmap/README.md` recent activity section (if it exists)
- Use any user-provided text after `/nextsteps` as extra context.

### Step 2 — Update beads (parallel, use Agent tool)

Match recent commits to open beads:

- **Close or update** resolved beads: `br update <id> --status done`
- **Create** new beads for gaps not yet tracked: `br create "<title>" --type task --priority 2`

Run bead updates in parallel via subagents when multiple updates are needed.

### Step 3 — Update `~/roadmap` (parallel with beads)

Run concurrently with Step 2:

- `mkdir -p "$HOME/roadmap"` first
- Append a dated session bullet to **`~/roadmap/README.md`** under `## Recent activity` (create file/section if absent).
- Format: `- YYYY-MM-DD: <one-line summary of what was done>`

### Step 4 — Report

- Beads updated/created (IDs and titles)
- `~/roadmap/README.md` path and line appended
- Recommended next actions

---

## `--full` mode

When invoked as `/nextsteps --full`, run the complete pipeline:

→ Follow `~/.claude/skills/nextsteps/SKILL.md` exactly (nextsteps doc, learnings, Claude auto-memory, mem0, GitHub issues).