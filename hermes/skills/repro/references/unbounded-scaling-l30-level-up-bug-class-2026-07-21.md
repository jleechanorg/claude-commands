# Unbounded-scaling L30+ level-up bug class (2026-07-21, issue #8508 → PR #8509)

## TL;DR

A **deterministic-canonical reducer** whose stale-clear predicates assume a **finite XP progression table** will silently miss the unbounded-scaling regime (level 30+, where `xp_needed_for_level(N)` falls through to a +X/level formula). The reducer returns "not stale" indefinitely, the rewards box keeps emitting `level_up_available=true`, and the modal stays open forever. Cross-campaign reproducible.

When you see "stuck level-up modal at L30+", do NOT file a one-off bug — the cluster trigger has likely already fired (≥3 cross-campaign siblings within 24h). Branch a fresh worktree, add an **explicit unbounded-scaling clause** to the deterministic reducer, **expose the XP progression formula via a god-mode-writable seam**, and ship **one PR** covering both the backend gating and the prompt-layer rule.

## The class

The D&D 5e XP table has 30 rows (`XP_THRESHOLDS[0..29]`). Beyond Level 30 the your-project.com project falls through to `+50,000 XP/level` — `xp_needed_for_level(N) = 855000 + (N-30)*50000` for N>30. This is the "unbounded-scaling regime."

The deterministic-canonical reducer `ensure_level_up_rewards_pending` (`$PROJECT_ROOT/game_state.py:2094-2128`) clears stale `rewards_pending.level_up_available=True` only when ONE of:

1. `level_up_complete=True` or `level_up_cancelled=True` (modal was committed)
2. `stored_level >= existing_new_level` (already at/past target)
3. `current_xp < xp_threshold_for_pending` (XP is BELOW the next threshold)

**At L50 with target 51 and `current_xp=1,905,000`:**
- Branch 1: false (modal not committed)
- Branch 2: `50 >= 51` → false
- Branch 3: `1,905,000 < 1,905,000` → false

No branch fires. The rewards box stays stale. **`rewards_box_has_future_level_transition` keeps returning True** (`rewards_engine.py:413-433`) because `target (51) > current (50)` regardless of the XP regime.

**God mode can't clear it either.** The GodModeAgent final-output contract (`$PROJECT_ROOT/agents.py:1142-1158`) forbids admin-commit from writing `rewards_pending` — the contract is *"write `state_updates.player_character_data.level`, NOT `level_up_signal` / `rewards_box.level_up_available`"*. So even after `GOD MODE: set level = 51`, the persistent `rewards_pending` field is untouched.

## Cross-campaign trigger (NOT per-scene invention)

Verified 2026-07-21 on TWO distinct campaigns in the same hour:
- `q04GfOEl4SWnEQrFUVST` L50 → L51 (4th sibling in cluster #8490/#8497/#8499)
- `wSm8Z8McTLJ8oQjqlTyJ` L77 → L78 (5th campaign; new)

`session_search "level 77 stuck unbounded scaling pending"` returns 0 prior hits on `wSm8Z8McTLJ8oQjqlTyJ` — distinct from the cluster. The bug is structural, not campaign-specific.

## The 3-component fix shape (verified PR #8509, 2026-07-21)

The fix is ONE PR with three load-bearing components — NOT three PRs, NOT backend-only, NOT prompt-only. The user typically issues all three directives in the same `/repro` flow ("all fields writable from god mode", "progression shouldn't be hardcoded", "fix the stuck level-up"). Shipping them separately creates merge-train risk; shipping them together ships a coherent solution.

### Component 1 — Backend gating (`$PROJECT_ROOT/game_state.py:2150+`)

Add an **explicit unbounded-scaling clause** to the deterministic reducer. The clause fires when:

```python
# Stored at MAX_LEVEL (30+) AND target is one ahead AND XP threshold has been
# crossed AND modal is not actively in progress.
in_unbounded_regime = stored_level >= MAX_LEVEL
xp_already_crossed_pending = (
    in_unbounded_regime
    and existing_new_level > stored_level
    and current_xp >= xp_needed_for_level(existing_new_level, state_dict=state_dict)
)
```

When all four conditions hold AND `level_up_in_progress` is NOT True, clear `rewards_pending`. This is the **asymmetric sibling** of the pre-existing deterministic-stale-evidence check at `world_logic.py:2055-2079` — that one fires only when `target <= current`; the new clause also catches `target == current+1` at L30+ when XP is at/past the threshold.

### Component 2 — Prompt-layer god-mode universal override (`$PROJECT_ROOT/agents.py:1151+` + `$PROJECT_ROOT/prompts/level_up_modal_override_instruction.md`)

Per operator directive ("all fields and flags must be viable to god mode"), extend the GodModeAgent final-output contract with the **universal-override rule**:

> *"GOD MODE IS THE UNIVERSAL OVERRIDE: every persistent field and modal flag the runtime maintains is FAIR GAME for god-mode writes — `rewards_pending`, `rewards_box`, `custom_campaign_state.{level_up_pending,level_up_in_progress,level_up_complete,level_up_cancelled}` etc. MUST be writable in a god-mode admin-commit response when the player explicitly asks. The `directives.add` mechanism is the canonical way to write those flags from god mode. Admin-commit does not forbid touching modal-side flags — only the modal-handoff path does."*

Mirror in `$PROJECT_ROOT/prompts/level_up_modal_override_instruction.md` with a new `## UNBOUNDED-SCALING LEVEL-UP (L30+)` section + worked example pinning the L51 threshold value (`1,905,000`) and the `directives.add` payload shape.

### Component 3 — XP progression parameterizable (`$PROJECT_ROOT/game_state.py:1622+`)

Per operator directive ("level up progression shouldn't be hard coded and should be in game state for the formula"), expose the XP threshold formula via a god-mode-writable seam:

```python
DEFAULT_XP_PROGRESSION: dict[str, Any] = {
    "explicit_thresholds": None,   # Replace the SRD table entirely
    "epic_step_xp": 50000,         # +X per level beyond the table
    "epic_start_level": None,      # Default MAX_LEVEL = 30
    "class_multipliers": {},       # {"rogue": 1.1} per-campaign
}

def xp_needed_for_level(level, state_dict=None) -> int:
    # ...honors custom_campaign_state.progression_overrides
```

**Do NOT migrate** the embedded `XP_THRESHOLDS` constant — preserve D&D 5e SRD defaults + epic/divine tiers. The seam is purely additive: god mode can override per-campaign via `directives.add { progression_overrides: {...} }` and the runtime picks it up on the next `xp_needed_for_level` call.

## Contract tests (15 cases, all green in `tests/test_unbounded_scaling_stale_pending_clears_8508.py`)

- **Basic regression** (L50→L51, L77→L78): the modal-clearing path fires.
- **Boundary preservation** (L29→L30 with sub-threshold XP, active modal with `level_up_in_progress=True`): pre-existing behavior unchanged.
- **Idempotency** (double-call safe): clearing is safe to call repeatedly.
- **Surface sanity** (`MAX_LEVEL == 30`, `xp_needed_for_level(31) == 855000 + 50000`): the embedded fallback still works.
- **Prompt contract**: `level_up_modal_override_instruction.md` contains the unbounded-scaling section, `#8508` reference, L51 threshold value (`1,905,000`), and `directives.add` keyword.
- **God-mode universal-override contract**: `agents.py` contains the universal-override section, `#8508` reference, and all six flag names.
- **Progression overridability** (4 cases): default config returns baseline; per-campaign override takes effect (state_dict threaded); `explicit_thresholds` replaces the table; default constant is NOT mutated by overrides.

## Cross-campaign cluster signal recipe

For any "stuck level-up modal" symptom reported on a L30+ character:

1. **Confirm cross-campaign**: `session_search "<level> stuck unbounded scaling pending"` for the user's exact level. 0 prior hits on distinct campaigns = new cross-campaign sibling, the cluster trigger has fired.
2. **Check the deterministic reducer**: read `ensure_level_up_rewards_pending` in `$PROJECT_ROOT/game_state.py`. If it has the explicit unbounded-scaling clause, the user is on a campaign that already shipped the fix; if not, file a new issue + branch a fresh worktree.
3. **Check the prompt layer**: read `$PROJECT_ROOT/prompts/level_up_modal_override_instruction.md`. If it has the `## UNBOUNDED-SCALING LEVEL-UP (L30+)` section, you're covered; if not, the prompt-side fix is missing.
4. **Check the agents contract**: read `$PROJECT_ROOT/agents.py` for the universal-override section. If missing, god mode can't clear future flag-class bugs either.

## Related references

- `references/god-mode-directive-missing-subclasses.md` — the 6-factor matrix (A-F) for directive-persistence bugs. **This bug class is NOT in that matrix** — it's a reducer-predicate miss, not a directive-persistence bug.
- `references/prompt-delivery-vs-content-2026-07-20.md` — the prompt-delivery vs prompt-content diagnostic. **Don't apply it here** — the unbounded-scaling rule IS being delivered to the LLM (per the worked-example prompt file); the bug is that the deterministic reducer doesn't have the matching backend gate.
- `references/phenotype-lock-static-evidence.md` — the 3 static-evidence greps. Particularly the "code-symbol grep" + "sibling-issue scan" — these are the gates that catch the cross-campaign signal before opening a per-scene issue.

## Pitfall: don't ship backend-only or prompt-only

The temptation is to ship just the backend gating ("the bug is fixed by the reducer") or just the prompt rule ("the LLM just needs to clear the flag"). **Both fail without the other:**

- Backend-only fix: the LLM keeps emitting `rewards_pending.level_up_available=True` every turn because it doesn't know the campaign is in the unbounded regime. The modal stays "fresh" in the LLM payload and the deterministic reducer's clauses only fire on the persisted state.
- Prompt-only fix: the LLM clears `rewards_pending` once via `directives.add` but the next god-mode admin-commit that bypasses the modal contract (per the old forbidden wording) restores the bug.

**The 3-component shape is the minimum coherent fix.** Component 1 closes the reducer gap; Component 2 lets god mode clear the persistent flag; Component 3 lets god mode rewrite the formula so the same bug class can't re-emerge at L100, L200, etc.

## Cluster trigger extension

Per `references/repro-planning-block-and-campaign-cluster-2026-07-18.md` §3, the campaign-cluster trigger fires at **≥3 open repros on the same `campaign_id`**. This bug class has a **parallel cross-campaign trigger** at **≥2 distinct campaigns within 24h reporting the same root-cause class** — at that point, the bug is structural (in the prompt layer / reducer), not per-scene.

When the cross-campaign trigger fires:
1. **STOP filing per-scene issues.** One issue per campaign_id is enough.
2. **Branch a fresh worktree from `origin/main`.** Do NOT stack onto an existing PR head (per `## COMMIT: never-push-onto-someone-elses-pr-head`).
3. **Ship ONE PR** covering all three components.
4. **Update the existing per-campaign issue bodies** with a comment linking the new PR.
5. **Do NOT auto-merge.** Per operator conditional-approval pattern, production-code PRs are excluded from auto-merge even when CI is green.

## Verified worked example

PR #8509 ([$GITHUB_REPOSITORY](https://github.com/$GITHUB_REPOSITORY/pull/8509)) — HEAD `778e705b8439f469734279358ae8129eda9db667`. Branch `fix/unbounded-scaling-stale-clear-8508` from `origin/main@664cf2fa0f`. Files changed: 4 (3 modified + 1 new test file). Lines: +486/-12. Tests: 15 cases green + 317/7/1 (passed/skipped/xfailed) regression sweep on the level-up cluster.

The PR landed DRAFT per AGENTS.md `/es` evidence gate (production-path edits require real-server + real-LLM evidence before merge). Draft-to-non-draft transition required adding `## Tenets` section + linked artifact to the PR body (Gate-0 Design Doc Grep requirement); the empty-commit retrigger pattern was needed because body-only PATCH does NOT re-fire Gate-0 (see `wa-green-gate-pr-shape/SKILL.md` for the full chicken-and-egg recipe).