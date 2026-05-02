# /nextsteps

Situational assessment and roadmap sync after a work block.

**Skill:** `~/.claude/skills/nextsteps/SKILL.md`

## Usage
```
/nextsteps [optional: brief description of what just happened]
```

## EXECUTION INSTRUCTIONS

When this command is invoked:

### Step 1 — Load skill
Read `~/.claude/skills/nextsteps.md` for full execution protocol.

### Step 2 — Gather context in parallel
Run simultaneously:
- `git log --oneline -10` for recent commits
- `br list --status open` for open issues
- `ls roadmap/` for available docs
- Use any input provided after `/nextsteps` as additional context

### Step 3 — Assess and plan updates
Identify which beads issues and roadmap docs need updating based on recent activity. For new work not yet tracked, plan new issues/docs.

### Step 4 — Execute in parallel with subagents
Dispatch one subagent per major update task:
- Subagent A: Update/close beads issues matching recent commits
- Subagent B: Create new beads issues for untracked gaps
- Subagent C: Update relevant roadmap docs
- Subagent D: Create new roadmap docs for new initiatives (if any)

### Step 5 — Report summary
List everything updated/created with IDs, paths, and recommended next actions.
