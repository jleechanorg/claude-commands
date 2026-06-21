---
description: Review evidence artifacts for a claim, then check evidence-standards compliance. Dispatches to codex via orchestration library and hard-aborts if required skills fail to load (no inline fallback).
aliases: [er]
type: orchestration
execution_mode: immediate
last_updated: 2026-05-20
---

# /evidence_review — Evidence Review + Evidence Standards

**Usage**: `/evidence_review [subject or path]`

**Purpose**: Run an independent evidence review on the current conversation's claims,
a specific file/directory, or a described subject, THEN check evidence-standards
compliance via `/es`. Combines both results into a single verdict.

Uses the orchestration library to dispatch to codex first; falls back to the
evidence-reviewer subagent (claude) if codex is unavailable.

## Execution Instructions

When this command is invoked with `$ARGUMENTS`:

### Step 1: Collect Context

Determine what to review from `$ARGUMENTS`:
- If a file/directory path: read those artifacts
- If a description: extract relevant claims and artifacts from the recent conversation
- If empty: review the most recent work described in the conversation (e.g., last fix, test run, deployment)

### Step 2: Load Evidence-Review Skill

Load the evidence-review skill file that contains the enforcement rules, verdict rubric, mandatory pre-PASS checks, and anti-patterns:

```bash
# User-scope takes priority over repo-scope (user customizations override repo defaults)
if [ -f "$HOME/.claude/skills/evidence-review/SKILL.md" ]; then
  SKILL_PATH="$HOME/.claude/skills/evidence-review/SKILL.md"
elif [ -f "$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.claude/skills/evidence-review.md" ]; then
  SKILL_PATH="$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.claude/skills/evidence-review.md"
elif [ -f ".claude/skills/evidence-review.md" ]; then
  SKILL_PATH=".claude/skills/evidence-review.md"
else
  echo "WARNING: evidence-review skill not found — cannot proceed"
  SKILL_PATH=""
fi
```

If `$SKILL_PATH` is empty, **abort command execution immediately and report the error — do not proceed to Steps 3–6**.
Do not fall back to inline methodology; the canonical skill is the single source of truth and must be present.

### Step 3: Evidence Review (Codex Dispatch)

Run this Bash command to attempt codex dispatch:

```bash
# _dispatch_via_subprocess is a TaskPoller method — call ai_orch directly
if [ -z "$ARGUMENTS" ]; then
  PROMPT="Review evidence for the most recent work described in this conversation (e.g., last fix, test run, deployment). Map claims to artifacts, rate quality (STRONG/WEAK/MISSING), output PASS/PARTIAL/FAIL/INCONCLUSIVE verdict."
else
  PROMPT="Review evidence for: $ARGUMENTS. Map claims to artifacts, rate quality (STRONG/WEAK/MISSING), output PASS/PARTIAL/FAIL/INCONCLUSIVE verdict."
fi
ai_orch run --agent-cli codex "$PROMPT"
CODEX_EXIT=$?
echo "Codex dispatch exit: $CODEX_EXIT"
```

- If exit 0: read the most recent log from `/tmp/ralph/jobs/` matching `er-review*` and store findings for Step 6 synthesis
- If exit non-zero: proceed to Step 4

### Step 4: Fallback — Evidence-Reviewer Subagent (Claude)

If codex dispatch failed or produced no log, use the Agent tool to launch the evidence-reviewer subagent.

**CRITICAL**: If `$SKILL_PATH` is empty, **abort command execution immediately and report the error — do not proceed to Steps 3–6**. The subagent must read the evidence-review skill file from Step 2 itself — do not inline the methodology.

```
Use the Agent tool with:
  subagent_type: "evidence-reviewer"
  prompt: "Review evidence for: ${ARGUMENTS:-the most recent work described in this conversation}

  (Guard check: verify ${SKILL_PATH} is non-empty; if empty, abort command execution immediately and report the error — do not proceed to Steps 3–6.)
  Load the evidence-review skill at ${SKILL_PATH} and apply its methodology:
  verdict rubric, 6 mandatory pre-PASS checks, 4-phase review procedure, and anti-patterns.

  Focus on: [insert specific claims from conversation context here]"
```

**Regardless of whether Step 3 (codex) or Step 4 (fallback) produced the evidence review result**, continue to Step 5. The evidence-standards check always runs.

### Step 5: Evidence Standards (/es)

`/es` is a **reference/display command** — it reads and displays the evidence-standards skill layers. It does **not** accept `$ARGUMENTS` or perform automated evaluation. Instead, the reviewer performs manual evaluation using the referenced standards:

1. Read `~/.claude/skills/evidence-standards/SKILL.md` — general cross-project standards.
2. Read `.claude/skills/evidence-standards.md` — WorldArchitect-specific standards.
3. **Manually** evaluate the evidence collected in Steps 3-4 against both standards layers, using the same `$ARGUMENTS` context to identify which evidence class and media requirements apply. The reviewer applies the standards judgment — there is no automated /es subprocess.
4. Record findings separately for Step 6 synthesis.

### Step 6: Synthesize and Report

Combine both results into a single verdict:

1. **Evidence Review findings** (bundle integrity, test coverage, claim-to-artifact mapping)
2. **Evidence Standards findings** (class compliance, media requirements, claim floor, authenticity)
3. **Overall verdict**: This command returns the **raw overall verdict** (PASS only if both steps pass; WARN if minor issues exist but core claims are proven; PARTIAL if one has gaps; FAIL if either fails; INCONCLUSIVE if evidence is missing or cannot be verified). Harnesses (e.g., `/goal_harness`) are responsible for final verdict normalization.
4. For each claim, explicitly state what the evidence **proves** and what it **does NOT prove**.
5. **Note**: When called from a harness (e.g., `/goal_harness`), verdict normalization is the harness's responsibility. This command returns the raw verdict for the harness to process according to its own convergence rules.

**Hard rule — Unit-only evidence is NOT ALLOWED.** If the only proof for a claim is unit tests (Layer 1, mocked/isolated functions), the verdict must be INSUFFICIENT regardless of other factors; warn the user explicitly. Minimum acceptable proof: Layer 2 end-to-end integration tests (real callstack, mocks only at external API boundaries). Production-behavior claims involving LLMs or external services additionally require real-service evidence. **Exception:** unit-only proof IS acceptable for non-production changes (docs, tests, tooling/scripts) or for production changes under 100 delta lines of non-test code.

**Caveats**: The "proves vs does NOT prove" reconfirmation is mandatory — do not skip it even if both steps individually pass.

### Verdict Synthesis Decision Table

| ER verdict | ES verdict | Raw overall verdict | Harness-normalized |
|-----------|-----------|---------------------|--------------------|
| PASS | PASS | PASS | PASS |
| PASS | WARN | WARN | PASS |
| PASS | FAIL | FAIL | FAIL |
| PASS | PARTIAL | PARTIAL | FAIL |
| WARN | PASS | WARN | PASS |
| WARN | WARN | WARN | PASS |
| WARN | FAIL | FAIL | FAIL |
| PARTIAL | any | PARTIAL | FAIL |
| FAIL | any | FAIL | FAIL |
| INCONCLUSIVE | any | INCONCLUSIVE | FAIL |

Key rule: `/evidence_review` returns the **raw overall verdict**. Harnesses may normalize PARTIAL/INCONCLUSIVE/FAIL to FAIL and WARN to PASS per their convergence policy.
