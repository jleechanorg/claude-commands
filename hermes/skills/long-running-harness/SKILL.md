---
name: long-running-harness
version: 1.0.0
description: "Run multi-hour autonomous coding tasks using a 5-agent harness: Researcher, Planner, Executor (with Opus advisor), Evaluator, and Orchestrator. Combines Anthropic's advisor strategy, GAN-inspired generator/evaluator design, and Boris Tane's annotation-cycle workflow."
when_to_use: "When $USER asks to build a complex feature, refactor a system, or tackle any multi-step coding task that will take >30 min of autonomous agent time. Also when he says 'long running', 'harness', 'multi-agent', or references the advisor-strategy/harness-design/annotation-cycle posts."
---

# Long-Running Harness

A structured multi-agent architecture for autonomous coding tasks that would overwhelm a single agent session. Combines three proven approaches:

1. **Advisor Strategy** (Anthropic Apr 2026) — Opus-on-demand, cheap executor always
2. **Harness Design** (Anthropic Mar 2026) — GAN-inspired generator + evaluator, context resets, structured handoffs
3. **Annotation Cycle** (Boris Tane Feb 2026) — Research → Plan → Annotate → Implement → Feedback

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                         │
│  (human-in-loop + Opus advisor, gatekeeps transitions) │
└──────────┬──────────┬──────────┬──────────┬────────────┘
           │          │          │          │
     ┌─────▼──┐ ┌────▼───┐ ┌───▼────┐ ┌──▼──────┐
     │RESEARCH│ │ PLANNER│ │EXECUTOR│ │EVALUATOR │
     │(Haiku)│ │(Sonnet)│ │(Sonnet)│ │(Opus)    │
     └────────┘ └────────┘ └────────┘ └──────────┘
```

### Agent Roles

| Agent | Model | Job | Output |
|-------|-------|-----|--------|
| **Researcher** | Haiku (cheap, broad) | Deep-read codebase, understand system | `research.md` |
| **Planner** | Sonnet (balanced) | Write implementation plan with code snippets | `plan.md` + `todo.md` |
| **Executor** | Sonnet + Opus advisor (main workhorse) | Implement one todo at a time, context reset on fill | code changes + `handoff.md` |
| **Evaluator** | Opus (skeptical judge) | Grade output against rubric, never self-grade | `eval_report.md` |
| **Orchestrator** | Human + Opus | Phase transitions, annotation cycles, ship gate | approval / rejection |

## The Loop

```
1. Researcher → research.md
2. [ANNOTATION CYCLE] Human reviews, adds inline notes → Researcher revises (1-3x)
3. Planner → plan.md + todo.md
4. [ANNOTATION CYCLE] Human reviews plan, adds notes → Planner revises (1-3x)
5. [GATE] Plan approved?
   NO → back to step 3 or 1
   YES → proceed
6. For each todo item:
   a. Executor implements (with Opus advisor on-call)
   b. Context reset if anxiety/fill detected → handoff.md → fresh session
   c. Evaluator grades output against plan spec
   d. Eval PASS → next todo
      Eval FAIL → specific feedback → Executor retries (max 2x, then escalate)
7. All todos done → Final evaluation (full Evaluator pass)
8. [SHIP GATE] Human approves merge
```

## Quick Start

```bash
# Run the full harness from CLI
python3 ~/.hermes/skills/long-running-harness/scripts/harness.py \
  --task "Add cursor-based pagination to the list endpoint" \
  --repo /path/to/repo \
  --project-id agent-orchestrator

# Or step-by-step (more control):
# 1. Research
python3 ~/.hermes/skills/long-running-harness/scripts/harness.py \
  research --task "..." --repo /path/to/repo

# 2. Plan (after reviewing research.md)
python3 ~/.hermes/skills/long-running-harness/scripts/harness.py \
  plan --task "..." --repo /path/to/repo

# 3. Implement (after approving plan.md)
python3 ~/.hermes/skills/long-running-harness/scripts/harness.py \
  implement --repo /path/to/repo --todo-file .hermes/plans/todo.md

# 4. Evaluate
python3 ~/.hermes/skills/long-running-harness/scripts/harness.py \
  evaluate --repo /path/to/repo --plan-file .hermes/plans/plan.md
```

## Key Design Decisions

### Why context resets over compaction

Anthropic's finding: Sonnet 4.5's context anxiety persisted even with compaction. A reset + structured handoff gives a clean slate. Trade-off: orchestration complexity + token overhead for handoff artifacts. In our stack, `ao-babysit` detects context fill and triggers resets.

### Why separate evaluator

Agents grade their own work too generously (Anthropic's GAN insight). Tuning a standalone evaluator for skepticism is tractable; making a generator self-critical is not. The evaluator runs Opus because judgment quality matters more than speed here.

### Why advisor tool (not sub-agent orchestration)

The `advisor_20260301` tool is a one-line API change. No worker pool, no decomposition. Sonnet drives, Opus only on hard calls. Cost stays near Sonnet levels.

### Why annotation cycles

Boris Tane's insight: the plan document is a shared working surface. Inline notes in the artifact beat chat-message steering every time. Domain knowledge injection happens before code, not after.

## Artifact Chain

| Phase | Input | Output | Location |
|-------|-------|--------|----------|
| Research | prompt + codebase | `research.md` | `.hermes/plans/research.md` |
| Planning | `research.md` + human notes | `plan.md` + `todo.md` | `.hermes/plans/` |
| Execution | `plan.md` + `todo.md` | code changes + `handoff.md` | worktree + `.hermes/plans/handoff.md` |
| Evaluation | plan spec + code diff | `eval_report.md` | `.hermes/plans/eval_report.md` |
| Ship | all artifacts | final commit | worktree |

## Model + Cost Profile

| Component | Model | % of tokens |
|-----------|-------|-------------|
| Research | Haiku | ~15% |
| Planning | Sonnet | ~10% |
| Execution | Sonnet + Opus advisor (3x/request max) | ~60% (mostly Sonnet) |
| Evaluation | Opus | ~15% |
| **Total** | | **~Sonnet-equivalent cost, Opus-level quality** |

## Integration with Existing Stack

| Harness Component | Hermes Equivalent |
|-------------------|-------------------|
| Research Agent | `ao spawn` with Haiku, writes to worktree |
| Planner Agent | `ao spawn` with Sonnet, outputs `plan.md` |
| Executor Agent | `ao spawn` with Sonnet + advisor tool, `ao-babysit` for context monitoring |
| Evaluator Agent | `ao spawn` with Opus, skeptic-evidence-capture skill |
| Orchestrator | Hermes gateway session + `bidi-cmux-alignment` for steering |
| Context resets | `ao-babysit` detects context fill → kills session → fresh spawn reads `handoff.md` |
| Annotation cycle | Human in Slack thread + `dispatch-task` for sending agent back to artifact |

## Anti-Patterns

1. **Don't let the agent self-evaluate** — always use separate evaluator
2. **Don't skip research** — garbage in, garbage out
3. **Don't implement before plan approved** — wasted tokens on wrong approach
4. **Don't rely on compaction alone** — context resets + handoffs for long tasks
5. **Don't use Opus end-to-end** — advisor tool for on-demand intelligence
6. **Don't steer via chat messages** — annotate the artifact, send agent back to it
7. **Don't let the executor write more than one todo without evaluation** — drift compounds fast

## Template Files

Read these when building agent prompts:

- `templates/researcher-prompt.md` — Research agent system prompt
- `templates/planner-prompt.md` — Planner agent system prompt
- `templates/executor-prompt.md` — Executor agent system prompt (includes advisor tool wiring)
- `templates/evaluator-prompt.md` — Evaluator agent system prompt (skeptical rubric)
- `templates/handoff-schema.md` — Structured handoff artifact schema

## Script

- `scripts/harness.py` — CLI orchestrator that runs phases, manages artifacts, triggers context resets

## References

- `references/advisor-strategy-summary.md` — Key points from Anthropic's advisor strategy post
- `references/harness-design-summary.md` — Key points from Anthropic's harness design post
- `references/annotation-cycle-summary.md` — Key points from Boris Tane's workflow
