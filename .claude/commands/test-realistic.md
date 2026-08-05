---
description: /test-realistic - Run the realistic-user-testing skill (60+ unit tests + acceptance test on the PR #8489 banner/status bug + dynamic Layer 1/3)
type: testing
execution_mode: immediate
---

## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**

**PRIMARY REFERENCE**: The skill lives at `testing_ui/realistic/`. The skill is now **dynamic** — it grows via:
- **Layer 1**: `docs_to_invariants.py` — auto-derives predicates from `docs/user-stories-ui/`
- **Layer 2**: `persona_pool.py` — 5 personas (power-gamer, story, completionist, casual, new) that pretend to be real users
- **Layer 3**: `swarm_runner.py` — dispatches the swarm, judges captures, writes new predicates, appends to `library.yaml`

The 8 baseline predicates are **EXAMPLES, not the full coverage**. The library grows as the swarm finds new bug classes. New invariants are written to `predicates/swarm_discovered/<name>.py` and registered in `library.yaml`.

## 🚨 EXECUTION WORKFLOW

### Step 1: Run the unit tests (always-run gate)

```bash
cd "$PROJECT_ROOT"
pytest testing_ui/realistic/ -q
```

**Expected**: `60+ passed` in <1s. The number grows as new swarm-discovered predicates are added. If this fails, the skill is broken — STOP and file a `br create` bead before continuing.

### Step 2: Run the defining acceptance test (PR #8489 banner/status bug)

The acceptance test replays the verbatim PR #8489 capture (status L3, rewards banner "Now level 3", narrative "level-up to 4 sealed", target_level 4) through the skill's `invariant_check` and **expects it to FAIL with both required named invariants**:

```bash
cd "$PROJECT_ROOT"
python -m testing_ui.realistic.invariant_library.invariant_check \
  --captures testing_ui/realistic/tests/fixtures/pr8489_capture.jsonl
```

**Expected output**:
```
verdict: FAIL
failures: N (real: 4, stubs: M)
failed_invariants: ['choice_menu_has_four_options', 'narrative_mentions_new_level', 'rewards_banner_uses_target_level', 'status_level_matches_target']
stub_invariants: ['us_001_contract'] (synthesized; Layer 3 will fill in)
```
**Exit code**: 1 (FAIL is the EXPECTED outcome for the bug capture).

**Required**: both `status_level_matches_target` AND `rewards_banner_uses_target_level` MUST be in `failed_invariants`. The `stub_invariants` line shows which doc-derived stubs are still RED by design (Layer 3 fills them in).

### Step 3: Run the inverse (healthy post-fix capture should PASS the two defining invariants)

```bash
# Build a minimal healthy post-fix capture (status L4, banner "Now level 4", target 4)
cat > /tmp/test-realistic-healthy.jsonl << 'EOF'
{"turn": 12, "rendered": {"session_header": {"level": 4, "hp": "40/40", "xp": "0/4900"}, "rewards_banner": "🎉 LEVEL UP! Now level 4.", "narrative": "The level-up to 4 is now fully sealed. You stand at level 4."}, "parsed": {"level_up_signal": {"current_level": 3, "target_level": 4}}, "state": {"hp_before": 36, "hp_after": 36, "spell_slots": {"L1": {"used": 0, "total": 4}}}}
EOF

python -m testing_ui.realistic.invariant_library.invariant_check \
  --captures /tmp/test-realistic-healthy.jsonl
```

**Expected**: `status_level_matches_target` and `rewards_banner_uses_target_level` MUST NOT be in `failed_invariants` (other invariants may fail because the capture is minimal — that's OK; what matters is the two defining invariants are silent).

This step proves the predicates are not overfit to the bug capture. If both invariants FAIL on a healthy capture, the predicates are broken — STOP and file a bead.

### Step 4 (NEW): Layer 1 — discover user stories covered by the skill

```bash
cd "$PROJECT_ROOT"
PYTHONPATH=. python -m testing_ui.realistic.docs_to_invariants --discover
```

**Expected**: List of `US-###.md` and `NEW-*.md` from `docs/user-stories-ui/`. Each line is `STORY_ID  TITLE  (N terms, M assertions)`. This shows the "what the user expects" corpus the skill is mining. ~111 user stories today.

### Step 5 (NEW): Layer 3 — swarm dispatch, discover new invariants

```bash
cd "$PROJECT_ROOT"
PYTHONPATH=. python -m testing_ui.realistic.swarm_runner --run
```

**Expected**: For each of the 5 personas, list the findings (mismatches between the persona's `cares_about` and what the synthetic capture shows). The swarm appends new invariants to `library.yaml` automatically. New invariants include a real predicate file at `predicates/swarm_discovered/<name>.py`.

The swarm catches bug classes a standard structural test would miss — by simulating how a real human persona (power-gamer, story-focused, etc.) would observe the rendered turn. Example: an `aggressive_power_gamer` notices immediately when XP doesn't increase after a combat action (`xp_after_combat_matches_diff`).

### Step 6: Report

Print a one-line summary:
```
/test-realistic: <N tests pass|FAIL>, PR #8489 capture: <CAUGHT (both named invariants FAIL)|MISSED>, healthy capture: <NOT OVERFIT (both named invariants PASS)|OVERFIT>, dynamic: <K user stories discovered | M new invariants this run>
```

## 📋 REFERENCE DOCUMENTATION

# /test-realistic - Realistic-User-Testing Skill Local Run

## Purpose

Run the realistic-user-testing skill (`testing_ui/realistic/`) locally to verify it still catches the PR #8489 banner/status bug class AND that the dynamic skill (Layers 1-3) is finding new invariants. This is a fast (under 5 seconds) sanity check.

The skill is the merged-into-main `testing_ui/realistic/` from PR #8680. It now has 4 dynamic layers:
1. **Baseline**: 8 hand-coded predicates seeded from `TEST-FAILURE-PATTERNS.md` and the PR #8489 bug class
2. **Layer 1 (docs_to_invariants)**: auto-discovers ~111 user stories from `docs/user-stories-ui/`, generates stub predicates for each
3. **Layer 2 (persona_pool)**: 5 personas (power-gamer, story, completionist, casual, new) with different playstyles
4. **Layer 3 (swarm_runner)**: dispatches personas, judges captures, writes real predicate code, appends to `library.yaml`

## Usage

```bash
/test-realistic
```

No arguments. The command runs end-to-end in seconds.

## What it tells you

- **N tests pass**: the skill's structural integrity is intact (grows over time)
- **PR #8489 capture → both named invariants FAIL**: the skill catches the bug class
- **Healthy post-fix capture → both named invariants PASS**: the skill is not overfit; it discriminates correctly
- **Layer 1 discovers N user stories**: shows the corpus the skill is mining
- **Layer 3 (swarm) → M new invariants this run**: the skill grew; new predicates are now in the library

## CI integration

The workflow `.github/workflows/realistic-test.yml` is **manual-only** (`workflow_dispatch` only) — operator-runnable from the Actions tab. It runs all 6 steps plus uploads a `verdict.yaml` artifact and prints a library.yaml summary.

## When to run

- Before/after any change to `testing_ui/realistic/` predicates
- Before/after any change to `$PROJECT_ROOT/prompts/` that touches the level-up / rewards / status-bar surface
- When a new operator-reported bug class emerges (e.g. the XP-not-gained bug from /game/JTuldmrV1UWC7UfsSJLp)
- As the humanlike-testing gate when an operator wants to spot-check a release
- After any change to `docs/user-stories-ui/` (Layer 1 auto-rediscovers)

## When NOT to use

- This is NOT a substitute for full real-LLM end-to-end testing (use `/llm-testing` for that)
- This is NOT a substitute for unit tests in `$PROJECT_ROOT/tests/`
- The stubbed `runner.py` does NOT execute real AGY; the skill is observation-only
