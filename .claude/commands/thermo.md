---
description: Run a strict, high-conviction maintainability and structural code quality review on files, PRs, or branches using the thermo-nuclear rubric.
aliases: [thermo-nuclear-review, thermonuclear]
type: slash
execution_mode: immediate
---

# /thermo — Thermo-Nuclear Code Quality Review

Run an extremely strict maintainability and structural review for abstraction quality, giant files, and spaghetti-condition growth using the thermo-nuclear rubric.

**Usage**: 
- `/thermo <path-to-file>` — review specific file
- `/thermo <branch-or-pr>` — review changes in a branch or PR
- `/thermo .` — review current directory/workspace changes

**Rubric Highlights**:
1. **Be ambitious about structural simplification ("Code Judo")**: Prefer solutions that make the code dramatically simpler, deleting whole branches, helpers, or layers.
2. **Decompose files over 1k lines**: Do not let a PR push a file from under 1k lines to over 1k lines without a compelling structural reason.
3. **No random spaghetti growth**: Reject ad-hoc conditionals, nullable flags, special cases, or one-off branches inserted into unrelated flows.
4. **Boundary and type cleanliness**: Flag casts, `any`, `unknown`, and ad-hoc object shapes that obscure real invariants.
5. **Canonical layers and modularity**: Ensure feature logic doesn't leak into shared paths and details don't leak through APIs.

**Action**:
To perform the review, the agent MUST immediately open, read, and apply the strict rules defined in:
- Personal skill: [~/.claude/skills/thermo-nuclear-code-quality-review/SKILL.md](file://$HOME/.claude/skills/thermo-nuclear-code-quality-review/SKILL.md)

Provide direct, serious, and demanding feedback on structural quality, ordering findings strictly as specified in the rubric.
