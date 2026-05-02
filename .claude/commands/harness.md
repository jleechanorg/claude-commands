---
description: Analyze failures and fix the harness (instructions, skills, tests, CI) rather than just the symptom
type: quality
execution_mode: deferred
scope: user
---
# /harness — Fix the harness, not just the symptom

**Scope:** **User-level (general).** This file lives at `~/.claude/commands/harness.md` and applies to **any** repository unless a project overrides it. **Collision rule:** if a workspace contains **`.claude/commands/harness.md`**, read repo-local content **after** this file — it adds project-specific harness rules (for example OpenClaw gateway). **Canonical copy in git:** [jleechanclaw `docs/harness/user-command-harness.md`](https://github.com/jleechanorg/jleechanclaw/blob/main/docs/harness/user-command-harness.md) (sync with `scripts/sync-harness-user-scope.sh` in that repo).

## Instructions for Claude

When this command is invoked, analyze the current situation for harness-level gaps and propose/implement fixes that prevent the same class of mistake from recurring.

**Skill reference**: `~/.claude/skills/harness-engineering/SKILL.md`

## Usage

- `/harness` — Analyze the most recent mistake or user correction in this conversation and propose harness fixes
- `/harness <description>` — Analyze a specific failure pattern and propose harness fixes
- `/harness --fix` — Analyze AND implement fixes without waiting for approval
- `/harness --audit` — Scan all instruction files for staleness, contradictions, or gaps

## Execution

### Default mode (`/harness` or `/harness <description>`)

1. **Identify the trigger**: Look at the most recent user correction, failed test, or explicit description
2. **Classify the failure**: Use the failure classes from the harness engineering skill
3. **Check existing harness**: Read these files to see what's already covered:
   - `~/.claude/CLAUDE.md` (global instructions)
   - Repo-local `CLAUDE.md` (project instructions)
   - Workspace **`.claude/commands/harness.md`** and **`.claude/skills/*/`** when present (repository overlay)
   - `~/.codex/AGENTS.md` (Codex instructions)
   - `~/.claude/skills/harness-engineering/SKILL.md` (the skill itself)
   - `~/.claude/projects/*/memory/` (relevant memories)
4. **Run 5 Whys — Technical**: Ask "Why?" five times about the technical failure. Drill to root cause. **This is mandatory.**
5. **Run 5 Whys — Agent path**: Ask "Why?" five times about why the agent (Claude Code or any coding LLM) went down the wrong path. **This is mandatory.** Focus on: Did the agent trust without verifying? Did it analyze at the wrong abstraction level? Was there no skill/instruction to redirect it?
6. **Identify the gap**: What's missing or insufficient in the harness?
7. **Propose fixes**: Output the structured plan from the skill protocol
8. **Wait for approval** before implementing (unless `--fix` flag)

### Fix mode (`/harness --fix`)

Same as default but implement immediately after analysis. Still report what was changed.

### Audit mode (`/harness --audit`)

Scan all harness files for:
- **Stale rules**: Instructions that reference files/tools/patterns that no longer exist
- **Contradictions**: Rules in different files that conflict
- **Gaps**: Known failure patterns (from memory) without corresponding instructions
- **Duplication**: Same rule in multiple places (consolidate to most durable layer)

Report findings as a table:

```
| Issue | File | Line | Recommendation |
|-------|------|------|----------------|
| Stale | ~/.claude/CLAUDE.md | 42 | Remove reference to deprecated tool X |
| Gap | repo CLAUDE.md | - | Add rule about Y (corrected 3x in memory) |
```

## Output Format

```
## Harness Analysis

**Trigger**: <what happened — user correction, failed test, or description>
**Failure class**: <mislabeled artifact | wrong approach | missing validation | repeated manual fix | silent degradation | knowledge gap | LLM path error>

### 5 Whys — Technical failure
1. Why: <answer>
2. Why: <answer>
3. Why: <answer>
4. Why: <answer>
5. Why: <answer>
→ Root cause: <single sentence>

### 5 Whys — Agent path
1. Why did the agent not catch/prevent this?
2. Why did the agent reason or act that way?
3. Why didn't the agent's instructions prevent that reasoning?
4. Why wasn't there a skill, memory, or rule that redirected the agent?
5. Why was the harness incomplete for this class of agent behavior?
→ Agent root cause: <single sentence>

### Existing coverage
- [x] ~/.claude/CLAUDE.md — <relevant rule if exists>
- [ ] repo CLAUDE.md — <gap identified>
- [ ] ~/.claude/skills/ — <no skill covers this>
- [x] memory — <relevant memory if exists>

### Proposed fixes
1. **[Instructions]** `<file>` — <what to add/change>
2. **[Skill]** `<file>` — <what to create/update>
3. **[Test]** `<file>` — <what test to add>

### Verification
<How to confirm the fix works>
```

## Examples

**User says "don't mock the database in these tests"**:
→ Failure class: wrong approach
→ 5 Whys technical: mock used → no instructions prohibiting it → testing philosophy not documented → ...
→ 5 Whys agent: agent defaulted to mock → common pattern in training data → no skill redirecting to real tests → ...
→ Add instruction to CLAUDE.md, save feedback memory

**Test labeled "e2e" but only does unit-level work**:
→ Failure class: mislabeled artifact
→ 5 Whys technical: E2E criteria not met → criteria not checked → no checklist for E2E → ...
→ 5 Whys agent: agent named it e2e without verifying → no skill mandating verification → ...
→ Add/update test classification rules in CLAUDE.md + AGENTS.md, update /validate-e2e skill

**Same code review comment given 3 conversations in a row**:
→ Failure class: repeated manual fix → mandatory harness fix, no exceptions
→ Add instruction to CLAUDE.md, save memory, consider lint rule

**Automation cleanup silently fails every cycle**:
→ Failure class: silent degradation (harness layer present but broken)
→ 5 Whys technical: cleanup fn uses wrong grep key → porcelain format not verified → no test for cleanup path → ...
→ 5 Whys agent: agent said "cleanup present" without running it → assumed present = working → skill doesn't mandate verifying harness script correctness → ...
→ Fix script, add verification step to skill, add integration test for cleanup path

**AO worker spawned on original PR branch instead of isolated clone**:
→ Failure class: LLM path error — wrong abstraction level (agent acted at "spawn worker" level without verifying branch isolation)
→ 5 Whys technical: `ao spawn` reuses existing worktrees → `--claim-pr` only adds dashboard tracking → no clone created → worker lands on original branch → pushes commits directly to live PR
→ 5 Whys agent: request said "spawn for PR 6198" → agent assumed `ao spawn` would create isolation → flag name implies PR association but not branch isolation → no skill/instruction to redirect to clone-before-spawn → harness had no rule for this failure class
→ Fix: add clone-before-spawn rule to jleechanclaw CLAUDE.md, add verification to team-mini.md, add failure class to harness.md, save feedback memory

**General principle — tool semantic mismatch**:
Many tools have names that imply capabilities they don't actually provide. When a tool name suggests isolation, atomicity, or safety guarantees that the implementation doesn't enforce, agents will trust the name and skip verification. This is a recurring failure class: LLM path error driven by misleading tool semantics.

Common examples:
- `ao spawn --claim-pr` implies PR isolation — it provides only dashboard tracking
- `git checkout -b` implies a new branch — but it can be from HEAD, not an isolated PR clone
- `gh pr checkout` checks out the PR branch directly — not a clone

Rule: When a tool's name semantically promises isolation or safety guarantees, verify those guarantees exist in the implementation before relying on them. If the tool's name over-promises relative to its behavior, the harness gap is the misleading name — fix in docs/skill rather than expecting agents to discover the gap.

## Input

$ARGUMENTS
