---
name: skillify
description: "Turn any feature, script, or workflow into a properly-skilled, tested, auditable Hermes skill. Use when the user says skillify, is this a skill, make this proper, or add tests and evals. Runs the 10-item skillify checklist against the target and creates all missing artifacts."
when_to_use: "Use when the user says: skillify this, is this a skill?, make this proper, add tests and evals for this, check skill completeness, turn this into a skill, capture this workflow. Also use proactively after building any new feature without the full skill infrastructure."
arguments:
  - target_path
  - description
argument-hint: "[target_path] [description of what to skillify]"
context: inline
---

# Skillify — The 10-Item Skill Completeness Checklist

## The 10-Item Contract

A feature is "properly skilled" when all 10 items are present:

1. **SKILL.md** — skill file with YAML frontmatter, name, description, when_to_use, triggers, allowed-tools, context
2. **Code** — deterministic script if applicable (shell, Python, TypeScript)
3. **Unit tests** — cover every branch of deterministic logic
4. **Integration tests** — exercise live endpoints, not just in-memory shape
5. **LLM evals** — quality/correctness cases if the feature includes any LLM call
6. **Resolver trigger** — entry in the skills resolver with trigger patterns the user actually types
7. **Resolver trigger eval** — test that feeds trigger phrases to the resolver and asserts they route to this skill
8. **check-resolvable** — the resolver passes: skill is reachable, MECE against siblings, no DRY violations
9. **E2E test** — exercises the full pipeline from user turn to side effect
10. **Brain filing** — if the feature writes to memory/brain, the brain RESOLVER has an entry so pages aren't orphaned

## Phases

### Phase 1: Audit

For the target, answer:
- What is this feature? (one line)
- Where does it live? (file path)
- Run the 10-item checklist manually:
  ```
  1. SKILL.md — exists? valid frontmatter?
  2. Code — script or is it pure LLM?
  3. Unit tests — in tests/?
  4. Integration tests — E2E?
  5. LLM evals — eval files?
  6. Resolver trigger — in RESOLVER.md?
  7. Resolver trigger eval — test for the trigger?
  8. check-resolvable — passes?
  9. E2E test — full pipeline test?
  10. Brain filing — brain/RESOLVER entry?
  ```
- Print audit: mark each item ✓ (present) or ✗ (missing)

### Phase 2: Create Missing Pieces

Work top-down. Earlier items constrain later ones.

**1. Write SKILL.md** — frontmatter must include: `name`, `description`, `when_to_use`, `allowed-tools`, `context`. Body must have: Contract, Phases, Steps, Output Format.

**2. Extract deterministic code** — if any logic can be deterministic (file I/O, API calls, parsing), extract it to a script so it can be tested independently.

**3. Write unit tests** — mock external calls (LLM, DB, network). Tests must be fast and deterministic.

**4. Add integration tests** — hit real endpoints. These catch bugs that mocks hide.

**5. Add LLM evals** — if the feature calls an LLM, add 3-case eval (happy / edge / adversarial).

**6. Add resolver trigger to RESOLVER.md** — use trigger patterns the user ACTUALLY types, not internal jargon.

**7. Add resolver trigger eval** — feed trigger patterns in, assert they route to this skill.

**8. Run check-resolvable** — `gbrain check-resolvable` or the Hermes equivalent. Fix reachability, MECE, DRY issues.

**9. Add E2E smoke test** — submit a real job or run CLI invocation end-to-end, assert side effects.

**10. Brain filing** — if writing brain pages, add entry to brain RESOLVER so pages aren't orphaned.

### Phase 3: Verify

Run and confirm green:
```bash
# Unit tests
pytest tests/   # or bun test, etc.

# Integration / E2E
pytest tests/   # or the project's test runner

# Resolver + MECE + DRY
gbrain check-resolvable
```

## Quality Gates

NOT skilled until:
- All 10 items present
- Resolver entry has real user trigger phrases
- Trigger eval confirms routing
- check-resolvable passes
- If brain pages written: brain RESOLVER entry exists

## Anti-Patterns

- ❌ Code with no SKILL.md — invisible to the resolver
- ❌ SKILL.md with no tests — contract regresses silently
- ❌ Tests that reimplement production — reimplementation bugs hide production bugs
- ❌ Resolver entry with internal jargon users never type
- ❌ Feature writes brain pages with no brain RESOLVER entry
- ❌ Deterministic logic in LLM space — should be a script
- ❌ LLM judgment in deterministic space — should be an eval

## Critical Scope Limitation (2026-04-22)

**gbrain check-resolvable and skillify-check.ts only scan ~/projects/gbrain/skills/, NOT ~/.hermes/skills/.**

When auditing a Hermes skill, gbrain's automated tools report the skill as missing even when properly wired in Hermes's own `RESOLVER.md`.

To audit a Hermes skill manually, run the 10-item checklist yourself:
1. `ls ~/.hermes/skills/<name>/` — confirm SKILL.md exists
2. `grep <name> ~/.hermes/skills/RESOLVER.md` — confirm resolver entry exists
3. Run the actual test suite for the target
4. Run `scripts/skillify-check.ts` if available

**Actual test count for gbrain's skillify skill:** 11 pass, 0 fail:
- `test/skills-conformance/skillify-resolver-trigger-eval.test.ts` — 8/8
- `test/e2e/skillify-e2e.test.ts` — 3/3

## Known Bugs in skillify Test Suite (2026-04-22)

### Bug 1: skillify-check.ts subdirectory test discovery is broken
**File:** `~/projects/gbrain/scripts/skillify-check.ts`
**Problem:** Only checks top-level `test/` files. Tests in subdirectories like `test/skills-conformance/` are missed, causing false negatives. Reports 6/10 for skillify even though actual bun test suite proves 11/10.
**Fix:** Patched in `~/projects/gbrain/scripts/skillify-check.ts` (commit fbb4936). Without patch, use bun test directly instead of skillify-check to verify coverage.

### Bug 2: `test_resolver_trigger` regex only captures heading line
**File:** `tests/test_skillify_resolver_trigger.py`
**Problem:** The non-greedy regex `(skillify.*?)(?=\n\n|\n##)` only captures the `## heading` line, so trigger words in `**Triggers:**` sub-lines below the heading are **not found**.
**Fix:** Put all trigger words directly on the heading line:
```markdown
## skillify — skillify this, make this proper, add tests and evals
```
NOT:
```markdown
## skillify
**Triggers:** skillify this, make this proper, ...
```

### Bug 3: `test_skill_tree_resolvable` calls `read_text()` on a directory
**File:** `tests/test_skillify.py`, line ~169
**Problem:** `skill_dir.read_text()` raises `IsADirectoryError` because `skill_dir` is a directory, not a file.
**Fix:** Always append `SKILL.md`:
```python
(skill_dir / "SKILL.md").read_text()
```

## Output Format

A skillify run produces:

1. **Audit printout** — which of 10 items exist vs missing
2. **Files created** — SKILL.md, test files, resolver entries
3. **Verification output** — check-resolvable confirming reachability
4. **Score** — N/10 skill completeness
