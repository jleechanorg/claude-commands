# Design: consolidate skill-distribution mechanisms (reconciliation-first)

Date: 2026-10-13 · Repo: jleechanorg/jleechan-skills · Status: corrected after review

## Context (verified 2026-10-13, reproduced by `scripts/report_skill_inventory_divergence.py`)
| Mechanism | Payload |
|---|---|
| `.claude/skills/` | 239 skills (README: source of truth) |
| `shared-skills.json` (`jleechan-shared-skills-v1`) | 4 reconciled skills, sha256-pinned; the flow `SHARED-SKILLS.md` names current |
| `portable/manifest.json` (`jleechan-portable-skills-v1`) | 29 skills / 32 files + `portable/skills/**` |
| marketplace manifests | `.claude-plugin/marketplace.json` **and** `.agents/plugins/marketplace.json` |
| `install-claude-commands.sh` | whole-home installer (docs say do not use) |
| live trees | `~/.claude/skills` 643 · `~/.agents/skills` 645 · `~/.codex/skills` 469 |

### Corrected finding 1 - the portable tree is NOT a duplicate
Verified comparison of the 29 portable skills against `.claude/skills/**`:
- **7 portable-only** (no `.claude/skills` counterpart): `cmux-restore, diagnosing-bugs, er, es, harness, p, sq`
- **19 divergent bodies**: `advice, cmux-backup, cmux-goal, cmux-steer, conversation-history-sparse, evidence-review, evidence-standards, harness-engineering, history, memory-search, ms, nextsteps, parallel, parallelize-to-ceiling, ready, redgreen, research, superpowers-quick, web-advice`
- **3 byte-identical**: `backend-first, llm-first, root-cause-first`

Therefore any plan that deletes `portable/**` as "duplicates" would **destroy 7 unique skills and choose 19 bodies arbitrarily**. Deletion is blocked until per-skill reconciliation decides which body wins.

### Corrected finding 2 - the marketplace manifests are not interchangeable
They differ materially: `.agents/plugins/marketplace.json` uses name `jleechan-skills-marketplace` and source `{"source":"github","repo":"jleechanorg/jleechan-skills"}`; `.claude-plugin/marketplace.json` uses name `jleechan-skills`, source `"./"`, version `1.0.1`, plus a description/author. A symlink is a **semantic change** for whichever consumer reads the `.agents` file, so single-sourcing requires consumer validation and a format mapping, not a blind symlink.

## Problem
Five distribution channels, two bundle formats/verifiers, two marketplaces with different schemas, three live discovery trees, and four sync/verify checkers. The genuine defect is **ambiguity + hidden divergence**, not simple duplication.

## Assumptions and Recommended Defaults (auto-picked; /sq invocation authorizes)
| Question | Auto-picked answer | Rationale |
|---|---|---|
| Is `portable/**` duplicate content? | **No** - divergent variant set (7 unique, 19 differing, 3 identical) | measured; `scripts/report_skill_inventory_divergence.py` |
| Which manifest should survive? | `shared-skills.json` **for the reconciled bundle**, with `.claude/skills/**` remaining the content source; the portable set must be reconciled INTO it, never deleted wholesale | SHARED-SKILLS.md names it current; the portable set holds unreconciled variants |
| Delete or regenerate portable now? | **Neither yet** - first add the divergence tool + contract test; reconcile per skill; then collapse | deletion is irreversibly destructive of unique bodies |
| Marketplace single-sourcing | Deferred behind consumer validation + format mapping (no symlink) | the two files encode different source formats |
| Live trees | Target: `~/.claude/skills` canonical, other runtimes as generated links | `/up` skill: "Do not add .codex user projections" |
| Sequencing | S1 inventory+contract+decision (this PR, non-destructive) → S2 per-skill reconciliation → S3 collapse bundle/verifier → S4 marketplace single-source after validation → S5 retire dead installer | each stage independently testable and reversible |

## Alternatives rejected
1. **Delete `portable/**` as duplicates** - rejected: destroys 7 unique skills, picks 19 bodies arbitrarily (verified numbers above).
2. **Symlink the marketplace manifests** - rejected: different name/source schema; silent semantic change for the `.agents` consumer.
3. **Adopt the 29-skill portable set as the single bundle** - rejected: `shared-skills.json` is the flow the repo's docs/installer designate current, and the portable bodies are stale variants of most overlaps.

## Chosen design (reconciliation-first)
- **S1 (this PR)**: ship `scripts/report_skill_inventory_divergence.py` + `tests/test_skill_inventory_divergence_contract.py` (pins 7/19/3), correct this spec/plan, and record the target architecture. **No deletions, no symlinks.**
- **S2**: per-skill reconciliation of the 7 portable-only and 19 divergent entries with an explicit decision record (which body wins and why); add reconciled skills to `shared-skills.json`.
- **S3**: after S2, collapse to the single manifest + one verifier; delete `portable/**` only when its content is fully represented.
- **S4**: validate each marketplace consumer, then single-source with a mapping that preserves both schemas.
- **S5**: retire `install-claude-commands.sh` (precondition: no launchd/cron invocation).

## Implementation Preconditions
- S2 requires semantic review of each divergent skill (not mechanical).
- S4 requires identifying the consumer of `.agents/plugins/marketplace.json` and its expected schema.
- S5 requires confirming no live invocation of the whole-home installer.

## Out of scope
Changing which skills exist; reconciling the remaining 210 `.claude/skills/**` entries.
