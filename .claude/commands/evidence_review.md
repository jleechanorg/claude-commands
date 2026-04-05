---
description: Review evidence artifacts for a claim using the evidence-reviewer agent. Dispatches to codex via orchestration library, falls back to inline claude analysis.
aliases: [er]
type: orchestration
execution_mode: immediate
---

# /evidence_review — Evidence Review Command

**Usage**: `/evidence_review [subject or path]`

**Purpose**: Run an independent evidence review on the current conversation's claims,
a specific file/directory, or a described subject. Uses the orchestration library to
dispatch to codex first; falls back to the evidence-reviewer subagent (claude) if codex
is unavailable.

**Guard**: If invoked with no arguments (empty `$ARGUMENTS`), exit immediately with a
message asking the user to specify a PR, file, or subject to review.

## Execution Instructions

When this command is invoked with `$ARGUMENTS`:

### Step 0: Guard — Require Arguments

If `$ARGUMENTS` is empty or whitespace-only, respond:
> "Usage: `/evidence_review [subject or path]` — please specify a PR (e.g., `$GITHUB_REPOSITORY PR 6048`), file path, or description of what to review."

Then stop. Do not attempt to run Codex or spawn an agent with no context.

### Step 1: Collect Context

**Prerequisite:** Step 0 has already passed — `$ARGUMENTS` is non-empty. Do not fall back to “review the last thing we did” when arguments were empty; that case is handled only by Step 0.

Determine what to review from `$ARGUMENTS`:
- If a file/directory path: read those artifacts
- If a description: extract relevant claims and artifacts from the recent conversation

### Step 2: Try Codex Dispatch via Orchestration Library

Run this Bash command to attempt codex dispatch:

```bash
# _dispatch_via_subprocess is a TaskPoller method — call ai_orch directly
PROMPT="Review evidence for: $ARGUMENTS. Map claims to artifacts, rate quality (STRONG/WEAK/MISSING), output PASS/PARTIAL/FAIL/INCONCLUSIVE verdict."
ai_orch run --agent-cli codex "$PROMPT"
CODEX_EXIT=$?
echo "Codex dispatch exit: $CODEX_EXIT"
```

- If exit 0: read the most recent log from `/tmp/ralph/jobs/` matching `er-review*` and summarize findings to the user
- If exit non-zero: proceed to Step 3

### Step 3: Fallback — Evidence-Reviewer Subagent (Claude)

If codex dispatch failed or produced no log, use the Agent tool to launch the evidence-reviewer subagent:

```
Use the Agent tool with:
  subagent_type: "evidence-reviewer"
  prompt: "Review evidence for: $ARGUMENTS

  Apply the full evidence-reviewer methodology:
  1. Inventory all artifacts mentioned in this conversation or at the provided path
  2. Map each claim to its supporting artifact
  3. Rate artifact quality: STRONG / WEAK / MISSING / INVALID
  4. Output a verdict table and overall PASS/PARTIAL/FAIL/INCONCLUSIVE with confidence level

  Focus on: [insert specific claims from conversation context here]"
```

### Step 4: Report to User

Present the verdict clearly:
- Overall verdict (PASS / PARTIAL / FAIL / INCONCLUSIVE)
- Confidence level
- Which claims passed, which failed, which are missing evidence
- Specific artifact names that supported or undermined each claim
- Note whether the review was done by codex or claude fallback
