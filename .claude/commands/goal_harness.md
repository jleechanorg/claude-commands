---
description: "Goal Harness — work on a goal until /es, /er, /code_standards, and Independent Agent Review all pass via adversarial subagents"
type: quality
execution_mode: immediate
aliases: [h]
---

# /goal_harness — Goal-Driven Harness Loop

Define a goal (via builtin `/goal`), then iterate until **4 adversarial gates** all pass:

1. **`/es`** — Evidence Standards (both layers: user-scope + project-scope)
2. **`/er`** — Evidence Review (adversarial, independent reviewer)
3. **`/code_standards`** — ZFC + ZFC-leveling + root-cause-first (3 adversarial lanes)
4. **Independent Agent Review** — Independent Agent-run review of the full diff

All four gates use **adversarial subagents** — each gate runs in an isolated context
that receives **only the diff and its evaluation standard**, never the primary agent's
reasoning or optimism.

## Usage

```
/goal_harness <goal description>
/h <goal description>               # alias
```

## Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│ Step 1: Define Goal (/goal)                         │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│ Step 2: Implement                                   │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│ Step 3: Run 4 Gates (adversarial subagents)          │
│  ├─ /es (evidence standards)                        │
│  ├─ /er (evidence review)                           │
│  ├─ /code_standards (3 parallel lanes)              │
│  └─ Independent Agent Review                        │
└─────────────────────┬───────────────────────────────┘
                      ▼
                  4/4 PASS?
                   ▼     ▼
                 YES    NO
                  ▼      ▼
              DONE    FIX & LOOP ──┐
                         ▲         │
                         └─────────┘
                      (max 10 iter, stall at 2× same)
```

## Steps

### Step 1 — Define the Goal

Invoke builtin `/goal` with `$ARGUMENTS` to establish the goal and success criteria.
The goal file is written to `.converge/goal.md` (or `.goalexec/goal.md` for legacy state).

### Step 2 — Execute Toward Goal

Implement the goal. After each implementation iteration, run the 4-gate harness.

### Step 3 — Run the Harness (4 adversarial gates)

Each gate dispatches a **subagent** with:
- **Context rules**:
  - **Gates 1-2 (Evidence Gates)**: Full access to the current diff and the evidence bundle/artifacts as context.
  - **Gates 3-4 (Code Gates)**: Only the current diff or changed files as context.
- **Only** the relevant standard/skill as its evaluation criteria
- **No** access to the primary agent's context, reasoning, or optimism
- **Verdict rules**: Gates must ultimately produce a normalized verdict (PASS / WARN / FAIL) with file:line evidence; implementations (such as Gate 2) may emit raw outcomes (e.g., PARTIAL, INCONCLUSIVE) which are mapped to normalized verdicts during the subsequent normalization stage.

#### Gate 1: /es (Evidence Standards)

Evaluate evidence standards via adversarial subagent — spawns the `evidence-reviewer` subagent to apply both evidence-standards skill layers:

```
Use the Agent tool with:
  subagent_type: "evidence-reviewer"
  prompt: "Evaluate the current diff against evidence-standards. Read both skill layers:
  (1) ~/.claude/skills/evidence-standards/SKILL.md (user-scope) and
  (2) .claude/skills/evidence-standards.md (project-scope).
  Apply their rules to the diff and return PASS, WARN, or FAIL with file:line evidence.

  Diff and artifacts:
  <full diff + evidence artifacts>"
```

#### Gate 2: /er (Evidence Review)

Evaluate evidence review via adversarial subagent — spawns the `evidence-reviewer` subagent to run evidence-review and evidence-standards synthesis. Note that Gate 2 emits raw overall verdicts (PASS, WARN, PARTIAL, FAIL, or INCONCLUSIVE) which are normalized by the harness in the subsequent normalization stage:

```
Use the Agent tool with:
  subagent_type: "evidence-reviewer"
  prompt: "Run evidence review against the current diff and its evidence artifacts.
  Load and apply:
  (1) The evidence-review skill from the repo-root required SKILL_PATH (located at `.claude/skills/evidence-review.md` relative to the repository root).
      If the repo-root SKILL_PATH is not present, immediately abort Gate 2 and emit a missing-skill error (do not continue synthesis).
  (2) The evidence-standards skills from ~/.claude/skills/evidence-standards/SKILL.md (user-scope) and .claude/skills/evidence-standards.md (project-scope).
  Return overall verdict: PASS, WARN, PARTIAL, FAIL, or INCONCLUSIVE with file:line evidence.

  Diff and artifacts:
  <full diff + evidence artifacts>"
```

#### Gate 3: /code_standards (3 adversarial lanes)

Delegate to `/code_standards` — 3 parallel subagents:

```
Use the Agent tool with:
  subagent_type: "code-review"
  prompt: "Review diff against ZFC (zero-framework cognition). Read ~/.claude/skills/zero-framework-cognition/SKILL.md (user scope; fall back to .claude/skills/zero-framework-cognition/SKILL.md if absent). Check for keyword routing, heuristic scoring, regex intent detection, banned if/else intent chains. Return PASS or FAIL with file:line evidence.

  Diff: <full diff only>"

Use the Agent tool with:
  subagent_type: "code-review"
  prompt: "Review diff against ZFC-leveling. Read .claude/skills/zfc-leveling-roadmap/SKILL.md (project scope; fall back to ~/.claude/skills/zfc-leveling-roadmap/SKILL.md if absent). Check for level-up fields, modal scoping, stale flag guards. Return PASS or FAIL with file:line evidence.

  Diff: <full diff only>"

Use the Agent tool with:
  subagent_type: "code-review"
  prompt: "Review diff against root-cause-first. Read ~/.claude/skills/root-cause-first/SKILL.md (user scope; fall back to .claude/skills/root-cause-first/SKILL.md if absent). Check that prompt/schema/instruction fixes are documented before backend protection, fallback, or retry is added. Return PASS or FAIL with file:line evidence.

  Diff: <full diff only>"
```

Reconcile: if ANY lane returns FAIL → overall /code_standards is FAIL.
WARN is acceptable but must be documented.

#### Verdict normalization

Harnesses are responsible for normalizing raw verdicts emitted by gates (such as `/er` in Gate 2) into final PASS/WARN/FAIL statuses for the convergence loop:

| Raw verdict | Normalized | Harness treatment |
|-------------|------------|-------------------|
| PASS        | PASS       | Gate passes |
| WARN        | PASS       | Gate passes (document warnings) |
| PARTIAL     | FAIL       | Gate fails — evidence gaps remain |
| INCONCLUSIVE| FAIL       | Gate fails — cannot confirm correctness |
| FAIL        | FAIL       | Gate fails |

Non-PASS raw verdicts (PARTIAL, INCONCLUSIVE, FAIL) are treated as FAIL in the convergence loop because the harness requires definitive proof.

#### Gate 4: Independent Agent Review

```
Use the Agent tool with:
  subagent_type: "code-review"
  prompt: "Review the full diff as a code reviewer. Look for: bugs, anti-patterns, missing tests, security issues, dead code. Return PASS or FAIL with file:line evidence.

  Diff:
  <full diff only>"
```

### Step 4 — Gate Matrix Report

After all 4 gates complete, produce a matrix:

```
| Gate                     | Verdict | Notes                       |
|--------------------------|---------|-----------------------------|
| /es                      | PASS    | Both layers satisfied       |
| /er                      | FAIL    | Missing media for claim 2   |
| /code_standards          | PASS    | ZFC clean, root-cause OK    |
| Independent Agent Review | PASS    | No blockers found           |
```

Convergence requires **4/4 PASS** (after normalization).

### Step 5 — Convergence or Iterate

- **4/4 PASS (after normalization)** = goal complete. Report results.
- **Any normalized-FAIL** = fix blockers, increment iteration counter, loop back to Step 2.
- **Same score 2 iterations in a row** = STALLED. Stop and report to human.
- **Max iterations (10)** = stop with partial report.

### Step 6 — Scheduled Mode (optional)

For long-running harness loops (cmux / background):

```bash
# Start harness loop via converge command
/converge <goal>

# Or use loop scripts (goalexec-* are canonical; goal-* are legacy aliases)
bash scripts/goalexec-loop.sh <goal>
bash scripts/goalexec-loop-cmux.sh --install --goal "<goal>" --interval 300  # cmux-aware variant
```

State persists in `~/.goal-loop/` between iterations.

## Safety Rules

- **Never skip a gate.** All 4 must run every iteration.
- **Never weaken a verdict.** If an adversarial subagent returns FAIL, it's FAIL.
- **Subagents must be adversarial.** Each subagent gets only its standard + the diff.
  It must NOT see the primary agent's reasoning or conclusions.
- **Parallel dispatch.** The 3 /code_standards lanes run in parallel when possible.
- **Agent review independence.** The independent review must not share context with the
  primary agent's own review of the same code.

## Related Commands

- `/goal` — builtin Claude Code goal command (sets success criteria)
- `/es` — Evidence Standards (reference/display)
- `/er` — Evidence Review (adversarial synthesis)
- `/code_standards` — Coding standards dispatch (ZFC + ZFC-leveling + root-cause-first)
- `/converge` — Iterative goal achievement loop (formerly `/goalexec`)
- `/converge_define` — Define-only variant (sets goal without execution)
