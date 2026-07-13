---
description: Analyze failures and fix the harness (instructions, skills, tests, CI) rather than just the symptom
type: quality
execution_mode: deferred
scope: user
---
# /harness — Fix the harness, not just the symptom

**Scope:** **User-level (general).** This file lives at `~/.claude/commands/harness.md` and applies to **any** repository unless a project overrides it. **Collision rule:** if a workspace contains **`.claude/commands/harness.md`**, read repo-local content **after** this file — it adds project-specific harness rules (for example OpenClaw gateway). **Canonical copy in git:** [jleechanclaw `docs/harness/user-command-harness.md`](https://github.com/jleechanorg/jleechanclaw/blob/main/docs/harness/user-command-harness.md) (sync with `scripts/sync-harness-user-scope.sh` in that repo).

Read `~/.claude/skills/harness-engineering/SKILL.md` and execute the full
workflow with the provided input — it defines the failure-class taxonomy, the
mandatory 5-Whys protocol (technical + agent path), the harness-layer gap
analysis, the audit-mode sweep, worked examples, and decision rules for
picking the right fix.

## Usage

| Invocation | Behavior |
|---|---|
| `/harness` | Analyze the most recent mistake/correction in this conversation, propose fixes, wait for approval |
| `/harness <description>` | Analyze a specific failure pattern, propose fixes, wait for approval |
| `/harness --fix` | Analyze AND implement fixes without waiting for approval |
| `/harness --audit` | Scan all instruction files for staleness, contradictions, gaps, duplication |

## Input

$ARGUMENTS
