---
description: ZFC Level-Up Architecture — M0 cleanup, compliance probe, legacy deletion, and enforcement
scope: worldarchitect.ai/mvp_site
---

# Level-Up ZFC Skill

## Purpose

Execute the ZFC Level-Up migration (model computes level-up facts; backend formats).
This skill governs **M0 through M3** on the `feat/zfc-level-up-model-computes` branch.

**Companion docs:**
- `roadmap/zfc-level-up-model-computes-2026-04-19.md` — architecture contract
- `~/.claude/skills/deletion-milestone.md` — **generic deletion milestone discipline** (net LOC protocol, PR lifecycle time budget, anti-substitution rules, CI gate requirements). This skill provides ZFC-specific content only; the generic skill covers the repeatable patterns.

**Companion wiki concepts:**
- [[ZFC-Level-Up-Architecture]] — north-star
- [[Net-Negative-Deletion-Is-Ok]] — net-negative deletion is always acceptable
- [[ScopeDrift]] — PR drift mechanics
- [[PragmaticLayerAntiPattern]] — mislabeled milestone response table

---

## Activation Cues

- Any work on `feat/zfc-level-up-model-computes` branch
- Any PR with title containing "level up" or "zfc" or "model computes"
- Tasks from beads tagged `LEVEL-UP`, `ZFC`, `M0`, `M1`, `M2`
- Comments from CodeRabbit or Bugbot on level-up PRs

---

## Phase Gate Protocol

**Before starting any work on this branch, run this check:**

```
git fetch origin
git log --oneline origin/main..HEAD   # List your commits
git diff --stat origin/main          # Net additions vs deletions for $PROJECT_ROOT/*.py
```

Compare against the M0/M1/M2/M3 checklist below.
If the planned work is "add behavior" on a deletion milestone → **STOP and re-assert scope.**

**For net LOC computation, see `deletion-milestone.md` — generic skill.**

---

## M0: Delete First, Add Nothing

**Goal:** Reduce live legacy paths. Production LOC must be **net ≤ 0**.

### M0 Checklist (all must be true before claiming M0 complete)

- [ ] Duplicate `project_level_up_ui()` streaming call deleted (`llm_parser.py:381`)
- [ ] `project_level_up_ui()` marked transitional with deletion trigger in docstring
- [ ] `resolve_level_up_signal()` in `world_logic.py` — keep/replace/delete classification documented
- [ ] `resolve_level_up_signal()` in `game_state.py` — keep/replace/delete classification documented
- [ ] `_canonicalize_core()` legacy fallback branches — each branch has a characterization test
- [ ] `rewards_engine.py` header updated to ZFC responsibility format
- [ ] Typed atomicity regression test added (`rewards_box.level_up_available` ↔ `planning_block.block_type`)
- [ ] **Net production LOC change ≤ 0** (verified by `git diff --stat origin/main -- $PROJECT_ROOT/*.py | grep -v test`)

### M0 Commit Order

1. **Test commit first** — characterize legacy behavior
2. **Deletion commit second** — remove only what tests prove
3. **Header/docstring commit** — update responsibility docs

### M0 Anti-Pattern — DO NOT

- Do NOT add new formatter logic while legacy paths still exist
- Do NOT claim "M0 complete" if net production LOC increased
- Do NOT merge M0 PR if legacy branches are still reachable without tests
- Do NOT let PR lifecycle (conflict resolution, CR responses) consume time that should be deletion work

---

## M1: Model Compliance Probe

**Goal:** Measure whether the LLM reliably emits canonical `level_up_signal`.

### M1 Checklist

- [ ] Prompt contract updated for `previous_turn_exp` / `current_turn_exp`
- [ ] Real streaming evidence captured for XP-only and level-up cases
- [ ] Compliance failures classified: model vs schema vs formatter
- [ ] `caveats` field deferred or promoted (see roadmap line 462-482)

### M1 Rule

Do NOT start M2 (formatter narrowing) until M1 compliance evidence exists.
Do NOT use compliance evidence as deletion proof unless evidence is reproducible.

---

## M2: Formatter Narrowing

**Goal:** `canonicalize_rewards()` is the only public rewards formatter.

- [ ] `format_model_level_up_signal()` made private (`_format_model_level_up_signal`)
- [ ] All callers migrated to `canonicalize_rewards()`
- [ ] `project_level_up_ui()` deleted (precondition: no remaining callers)
- [ ] Canonical XP field names enforced: `previous_turn_exp`, `current_turn_exp`, `total_exp_for_next_level`
- [ ] Deprecated aliases (`xp_to_next_level`, `xp_total`) accepted as input only

---

## M3: Enforcement

**Goal:** Prevent future drift.

- [ ] Net LOC gate in CI for M0/M2 PRs
- [ ] Centralization ratchet: no new `def` in `world_logic.py` whose name exists in `rewards_engine.py`
- [ ] Architecture test: `level_up_signal` formatting stays in `rewards_engine.py`

---

## Key Beads for This Work

| Bead | Purpose |
|------|---------|
| `rev-7vyc` | Level-up centralization tracker |
| `rev-pkjh` | Typed atomicity regression |
| `rev-lmdo` | ZFC roadmap realignment (2026-04-20) |
| `rev-k36z` | ZFC current status snapshot |

Always anchor spawn prompts to a bead, not a PR number.

---

## Related Skills

- `~/.claude/skills/deletion-milestone.md` — **generic** deletion/quarantine milestone discipline (intentionally outside repo; generic skill survives any project clone)
- `skills/code-centralization.md` — general duplicate-code consolidation
- `skills/pr-workflow-manager.md` — PR lifecycle (conflict handling, CR responses)
- `skills/evidence-standards.md` — real-model evidence requirements
