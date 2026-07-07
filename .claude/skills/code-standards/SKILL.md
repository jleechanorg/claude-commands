---
name: code-standards
description: Dispatch independent adversarial reviews for ZFC, ZFC leveling, root-cause-first, and thermo without duplicating their standards.
---

# Code Standards

Use this skill to dispatch code, diff, PR, or proposed-implementation review
against the repo's core standards. This is a pointer/dispatch skill: reference
the source skills below instead of duplicating their standards.

## Iron Law

> **NO REVIEW LANE PASSES WITHOUT VERIFICATION EVIDENCE**
> A lane returning PASS must include the specific file/line evidence that proves
> compliance. A lane returning FAIL must include the exact location and required fix.
> **Rationalizations are not evidence.**

This Iron Law mirrors the superpowers systematic-debugging principle: if you
can't point to the exact line, the lane hasn't completed its work.

## Source Skills

Load the relevant source skills by path and treat them as authoritative.

**Path resolution:** Prefer personal overrides from `~/.claude/skills/`
when they exist, then fall back to the repo-local project skills listed below.
The repo-local `.claude/skills/` paths are authoritative for a normal checkout
because they are versioned with this repository. The `.codex/skills/` directory
contains pointer/mirror files for Codex-based agents and is not the primary
lookup path.

|- `.claude/skills/zero-framework-cognition/SKILL.md` (`/zfc`)
|- `.claude/skills/zfc-leveling-roadmap/SKILL.md` (`/zfclevel`)
|- `.claude/skills/root-cause-first/SKILL.md` (`/root-cause-first`)
|- `.claude/skills/code-quality/SKILL.md` (`/code-quality`, alias `/cq`) — metric-driven complexity / duplication / coupling / AI-import verification. **Out of scope: syntax, naming, formatting, lint rules** (those are linter territory, see "Lane ownership" below).
|- Thermo-nuclear: invoke via `Agent` tool with `subagent_type: thermo-nuclear-code-quality-review` (`/thermo`). This is an Agent tool subagent type, not a bash command or external process.

## Lane ownership (no overlap)

Each lane has a defined scope. A lane must hand off — not duplicate — work that
belongs to a sibling lane.

| Concern | Owner | Why |
|---|---|---|
| Syntax, formatting, import order, lint rules | ESLint / Ruff / mypy / prettier / pre-commit hooks | Mechanical, deterministic, already enforced in CI |
| Naming conventions, file layout | `/code-standards` style lane + linters | Project conventions, not metric-driven |
| Logic, architecture, complexity, duplication, AI-import verification | `/code-quality` | Metric + pattern reasoning |
| ZFC contract, agent routing, structured fields | `/zfc` | Domain semantics |
| Level-up / XP / reward semantics | `/zfclevel` | Game-loop semantics |
| Root-cause-first methodology for fix proposals | `/root-cause-first` | Debugging discipline |
| Holistic adversarial review | `/thermo` | Independent subagent model |

If a finding would belong to another lane, the current lane must name the
correct lane and stop rather than produce feedback that conflicts with it.

**SUPERPOWERS INTEGRATION** (from obra superpowers framework):

- **systematic-debugging iron law**: Find root cause before proposing fixes.
  Applied here: a FAIL without file/line evidence is incomplete work.
- **verification-before-completion**: Before claiming PASS, verify with grep/read.
  Applied here: lanes must cite specific evidence, not assume compliance.
- **finishing-a-development-branch verification**: Tests → verify → present options.
  Applied here: each lane must run verification commands and report actual output.

## Workflow

1. **Define the scope** from the command argument. If no argument is provided,
   review the current diff or active PR context.
2. **Dispatch five adversarial, independent review lanes** every time:
   `/zfc`, `/zfclevel`, `/root-cause-first`, `/code-quality`, and `/thermo`.
   Each lane has a defined scope — see "Lane ownership" below.
3. **Give each lane only its scope**, the relevant source skill path, and the
   instruction to look for blockers with file/line evidence. Do not paste or
   restate the full standard into the prompt.
4. **For Claude callers**, use a Codex subagent or Codex reviewer plugin for at
   least one independent lane when available, so one reviewer is not relying on
   the same model/context as the caller.
5. **The `/thermo` lane** uses `subagent_type: thermo-nuclear-code-quality-review`
   (NOT a bash command). Pass: diff summary, file list, working dir.
6. **Require every lane to report PASS/WARN/FAIL**, evidence, required fixes, and
   any N/A caveats. A lane may return N/A for a subsection only if the source
   skill permits that; the lane itself still runs.
7. **Reconcile the lane results** into one practical report. Do not dilute a FAIL
   from any required lane into a PASS.

## Systematic Debugging Integration

Each lane follows the four-phase process from systematic-debugging:

1. **Root Cause Investigation**: Read errors, check recent changes, trace data flow
2. **Pattern Analysis**: Find working examples, compare against references
3. **Hypothesis and Testing**: Form theory, test minimally
4. **Verification**: Verify fix works before claiming success

Applied to code review:
- Lane sees a symptom → investigates to find root cause (not just flags symptom)
- Lane proposes fix → traces to exact file/line that needs change
- Lane returns PASS → cites grep/read evidence proving compliance

## Test Coverage Gate

For any PR touching production code (non-test files):

- **Enforce**: New production code requires corresponding tests
- **Verification**: The reviewer runs test commands when execution access is
  available; otherwise, the reviewer must cite CI run output or require the
  PR author to provide test execution evidence.
- **TDD integration** (from superpowers TDD skill):
  - If tests don't exist, FAIL with "No tests for changed production code"
  - If test coverage dropped, FAIL with specific uncovered areas
  - Note: TDD write-first compliance is a development-time practice and
    cannot be verified post-facto from PR state alone. Do not WARN or FAIL
    based on assumed write order without CI evidence of the sequence.

## Prompt Placement Gate

Behavioral prompt prose belongs in `your_app/prompts/` markdown files, not in
Python string literals. Python may assemble deterministic structured context,
load prompt files, and substitute explicit placeholders such as current time or
location, but it must not embed new model instructions, behavioral rules, or
audit criteria inline. If a review finds inline prompt prose added or expanded
in Python, mark `/code-standards` FAIL unless the PR moves that prose into a
prompt file or documents why the text is purely deterministic formatting.

## Report Format

Return a concise report:

```markdown
## Code Standards Report

Scope: <file, diff, PR, or task>

- ZFC: PASS/WARN/FAIL - <evidence>
- ZFC leveling: PASS/WARN/FAIL - <evidence or permitted N/A caveat>
- Root-cause-first: PASS/WARN/FAIL - <evidence or permitted N/A caveat>
- Code-quality: PASS/WARN/FAIL - <evidence or permitted N/A caveat (see "Short-circuit clauses" in code-quality/SKILL.md)>
- Thermo: PASS/WARN/FAIL - <evidence or structural blockers>

Blockers:
- <line-level issue and required fix>

Test Coverage:
- <test command run and output, or CI evidence reference>
- PASS/FAIL for test coverage gate

Next checks:
- <tests, evidence, or review steps needed>
```

**Iron Law Enforcement:**
- If there are no blockers, say so explicitly and list any residual risks
- Do not mark any of the five lanes as skipped
- A PASS without file/line evidence is treated as INCOMPLETE (continue investigation)

## Anti-Rationalization Checks

From systematic-debugging rationalization tables:

| Rationalization | Reality |
|----------------|---------|
| "Tests are obvious, no need to verify" | Test existence ≠ test correctness |
| "Code is simple, review is optional" | Simple code has simple bugs with simple root causes |
| "I'll verify later" | Later = never; verification must be in this session |
| "Close enough to pass" | A FAIL is a FAIL; reconcile by fixing, not diluting |

If you catch yourself thinking any of these, stop and complete the verification step.
