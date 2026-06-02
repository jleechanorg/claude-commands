---
description: ZFC level-up flow review — judge clean architecture, file ownership, and model-owned cognition for level-up work
type: quality
execution_mode: immediate
---

# /zfclevel

## Purpose

Review level-up, rewards, XP, and modal-flow work for clean architecture and
ZFC compliance. This is a judgment-first review command, not a grep gate.

Primary standards:
- Clean code: small coherent changes, clear ownership, minimal coupling, no
  duplicated decision logic, and no unrelated scope in a level-up PR.
- ZFC: model decides, server executes. Application code must not add semantic
  routing, keyword/prefix classification, heuristic scoring, or backend
  recomputation of model-owned level-up decisions.
- Level-up architecture: follow `.claude/skills/zfc-leveling-roadmap/SKILL.md`
  and its file responsibility table.
- Root-cause-first: before accepting backend guards, fallbacks, suppressions,
  retries, or server-synthesized choices, require prompt/schema/agent evidence
  from the real path.

Automated grep gates, line counts, CI labels, PR body claims, and previous bot
comments are supporting evidence only. They never determine the verdict.

## Required Context

Load these repo-local skills before judging:
- `.claude/skills/zero-framework-cognition/SKILL.md`
- `.claude/skills/zfc-leveling-roadmap/SKILL.md`
- `.claude/skills/root-cause-first/SKILL.md`
- `.claude/skills/code-standards/SKILL.md`

If a command argument is provided, review that scope. Otherwise review the
current diff or active PR. For PR work, prefer changed lines from
`origin/main...HEAD`; do not block on pre-existing debt unless this PR newly
uses, expands, or relies on it.

## Review Workflow

1. Identify changed files and classify each change by responsibility:
   - Does the added behavior belong in the file's OWNS column?
   - Does it cross into a MUST NOT DO column?
   - Does it duplicate or scatter a level-up decision already owned elsewhere?
2. Review level-up flow cleanliness:
   - Is the flow understandable as model output -> canonical rewards/level-up
     formatting -> modal/session execution?
   - Are modal locks, prompt contracts, parser behavior, routing, and UI
     submission separated cleanly?
   - Are tests proving the contract rather than pinning workaround behavior?
3. Review ZFC risks:
   - New semantic routing by choice ID, prefix, label, text, or CSS class.
   - Backend level, XP, target-level, or eligibility computation as a primary
     path.
   - Backend suppression, choice synthesis, parser mutation, or fallback that
     changes model-owned output without root-cause-first proof.
   - New public APIs that let callers second-guess canonical level-up helpers.
4. Review root-cause-first evidence:
   - selected agent and prompt/schema provenance
   - raw request/response
   - state before/after
   - prompt/schema/agent fix attempted first
   - why a backend invariant remains necessary
5. Review scope:
   - Separate in-PR blockers from follow-up debt.
   - Do not demand a redesign when a small PR-tightening is enough.
   - Do not excuse new architecture debt merely because it is central to the PR;
     label it honestly as accepted debt if the human chooses to ship it.

## Verdict Rules

Use `FAIL` when current changed lines introduce or expand:
- backend semantic classification/routing
- backend primary XP/level/eligibility computation
- broad suppression or fallback over model-owned state
- file-role violations in the level-up responsibility table
- undocumented server-synthesized choices or parser mutation of planning choices

Use `WARN` when the issue is real but can be safely deferred because it is
display-only, documentation-only, or pre-existing debt not expanded by this PR.

Use `PASS` only when the changed lines preserve clean ownership and ZFC
principles, with any backend correction narrow, logged, and justified.

## Report Format

```markdown
## /zfclevel Report

Scope: <diff, PR, file, or task>

### Verdict
PASS/WARN/FAIL - <one sentence>

### Changed-File Ownership
| File | Added behavior | Owner verdict | Evidence |
|---|---|---|---|

### ZFC / Clean-Code Findings
- <severity>: <file:line> <issue> -> <required action>

### Backend Adjustment Proof
| Component | Non-prompt behavior | Proof state | Verdict |
|---|---|---|---|

### In This PR
- <small, scope-tight fixes required before merge>

### Later
- <tracked follow-up debt with bead/design reference>

### Supporting Checks
- <grep gates, tests, CI, evidence status; supporting only>
```

End with `PASS`, `WARN`, or `FAIL`; do not report a grep-gate pass as ZFC
alignment.
