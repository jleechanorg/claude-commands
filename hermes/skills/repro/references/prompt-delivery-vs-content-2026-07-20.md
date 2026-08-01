# Prompt-delivery vs prompt-content bug class — case study 2026-07-20

**TL;DR:** When the LLM violates a rule and the rule is in the prompt file on disk, the bug class is **delivery** (the file doesn't reach the LLM), not **content** (the rule is wrong). This is a separate bug class from the existing `god-mode-directive-missing` family. Use the new umbrella skill **`llm-prompt-delivery-audit`** for the 5-step wire diagnostic.

## The class distinction

| Bug class | Symptom | Where the rule lives | Where the failure is |
|---|---|---|---|
| **god-mode-directive-missing** (existing family, PR #7162/#8012/etc.) | LLM ignores a god-mode directive the user typed into the session | In a directive string the user emits via god-mode UI | Directive gets dropped between session storage and LLM payload (4-factor matrix) |
| **prompt-delivery** (new, 2026-07-20, PR #8005) | LLM ignores rules in a canonical prompt file the project owns | In a `$PROJECT_ROOT/prompts/*.md` file (e.g. `living_world_instruction.md`) | The whole file content is replaced by a stub at the dispatcher seam — the file exists on disk, the LLM never sees it |

The two share an observable signature ("LLM violates a rule that the source code says is forbidden") but the diagnostic surface and the fix are completely different. god-mode-directive-missing is a runtime delivery path bug (4 storage/routing factors); prompt-delivery is a build-time dispatcher bug.

## The case study: living_world_instruction.md stub regression

**Originating PR:** [$GITHUB_REPOSITORY#8005](https://github.com/$GITHUB_REPOSITORY/pull/8005) (merged 2026-06-29) — "Fix cache prefix MCP drop bug for living world".

**Commit message excerpt:**
> Implicit Caching: Relocate metadata fields and use RealisticFakeLLMResponse pattern

**What PR #8005 actually did:** moved `living_world_instruction.md` from the cached system prefix into the dynamic_instructions channel for cache-stability. Kept a 7-line activation tail in `build_living_world_instruction()`. The on-disk file content was lost in the move.

**Marker in source code (verified 2026-07-20):**

```python
# $PROJECT_ROOT/agent_prompts.py:1469
del advances_time  # Unused after living_world_instruction moved to dynamic path
```

This `del advances_time` comment is the diagnostic marker for the pattern. If you see it in `agent_prompts.py`, the named prompt was moved to dynamic_instructions and the function body may now return a stub.

**Stub body (`$PROJECT_ROOT/agent_prompts.py:2625-2635`):**

```python
turn_header = (
    "\n**🌍 LIVING WORLD POLICY**\n"
    "Evaluate the full state and decide whether the living world should "
    "advance this turn.\n"
    "You MUST always emit `state_updates.world_events` as a dict. "
    "When advancing, include `background_events`. "
    "When quiet recovery or no meaningful off-screen motion is right, "
    "emit `world_events.background_events` as an empty array.\n"
)
return turn_header + arc_context
```

7 lines. The on-disk file is 1,080 lines with the Major Event Rarity Budget, Trigger Whitelist, Lore-Appropriate Enemy Detection, escalation ladder, momentum counterpressure, complication probability formula. None of it reaches the LLM.

## Why the move was tempting (and why it broke)

The legitimate engineering goal of PR #8005 was cache stability — Gemini's implicit cache requires a stable prefix, and any field that changes per-turn (companion arc summary, current location, etc.) invalidates the cache key. Moving per-turn state to dynamic_instructions preserves the cache hit rate.

The mistake: the move treated the WHOLE prompt file as per-turn state. The Major Event Rarity Budget, Trigger Whitelist, etc. don't change per-turn — they're cacheable. Only the activation tail and per-turn state should be in dynamic_instructions.

The correct split:
- **Stable section** (system prefix, cacheable): Major Event Rarity Budget, Trigger Whitelist, Lore-Appropriate Enemy Detection, escalation ladder, anti-patterns, momentum counterpressure, complication probability formula, schema contract — everything the LLM needs every turn.
- **Dynamic section** (dynamic_instructions): per-turn activation tail + cadence check + companion arc summary.

## The 5-step wire diagnostic (full recipe in `llm-prompt-delivery-audit` SKILL.md)

For the your-project.com case:

**Step 1 — Confirm the rule is in the file on disk:**
```bash
grep -rn "Major Event Rarity Budget\|scrying\|auditor" $PROJECT_ROOT/prompts/living_world_instruction.md
# → 12 hits in the file. Rules present.
```

**Step 2 — Find the dispatcher call site:**
```bash
grep -rn "living_world_instruction" $PROJECT_ROOT/ --include="*.py"
# → $PROJECT_ROOT/agent_prompts.py:2576 build_living_world_instruction()
```

Read the function body — confirms it returns a 7-line stub.

**Step 3 — BQ forensic against `worldarchitecture-ai:llm_forensics.llm_payloads`:**
```sql
SELECT
  agent, event_type,
  COUNT(*) AS calls,
  COUNTIF(REGEXP_CONTAINS(CAST(request_json AS STRING), r'Living World Advancement Protocol')) AS has_lw_header,
  COUNTIF(REGEXP_CONTAINS(CAST(request_json AS STRING), r'Major Event Rarity Budget')) AS has_budget
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND is_test = false
GROUP BY agent, event_type
ORDER BY calls DESC
```

Result: 34/2279 = 1.5% of real-user calls contain the LW header. Major Event Budget = 0% for non-stream agents.

**Step 4 — Extract the actual block:**
```sql
SELECT
  REGEXP_EXTRACT(CAST(request_json AS STRING), r'LIVING WORLD POLICY[^$]{0,500}') AS block_in_request
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE REGEXP_CONTAINS(CAST(request_json AS STRING), r'LIVING WORLD POLICY')
LIMIT 1
```

Result: 7-line stub. File body is NOT in the request.

**Step 5 — Cross-check response side:**
```sql
SELECT
  agent, event_type,
  COUNT(*) AS calls,
  COUNTIF(REGEXP_CONTAINS(response_text, r'scrying|scent|inquisitor|auditor|detect magic|tracking focus|Blood-Scent|ward|sensor')) AS complaint_in_resp,
  ROUND(100*COUNTIF(REGEXP_CONTAINS(response_text, r'scrying|scent|...')
                     AND NOT REGEXP_CONTAINS(CAST(request_json AS STRING), r'Major Event Rarity Budget'))
        / COUNT(*), 1) AS pct_lm_invented
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND is_test = false
GROUP BY agent, event_type
ORDER BY calls DESC
```

Result: 90-100% `pct_lm_invented` on non-stream agents. The LLM has zero prompt guardrails for these tropes.

## Why the existing god-mode-directive-missing skill would miss this

The `references/god-mode-directive-missing-subclasses.md` skill encodes a 5-factor matrix for directives the USER emits at runtime. Its BQ forensic recipe (`## active god mode directives` header check) is the right shape but the wrong axis. It looks at directive headers in the request, not at prompt-file body content. A session where the user never invokes god-mode would have zero `## active god mode directives` headers — the matrix would say "factor E: no god mode in session" and the diagnostic would conclude "no directive bug, must be content." But the real issue is upstream — the prompt file content was lost in a cache-stability refactor.

The right diagnostic surface for prompt-delivery is:
1. Confirm the rule is in the prompt file on disk (Step 1)
2. Find the dispatcher call site and read the function body (Step 2)
3. BQ-grep the request_json for stable prompt-section anchors, not for directive headers (Step 3-4)
4. Cross-check response_text for the user's complaint tokens (Step 5)

That's the umbrella `llm-prompt-delivery-audit`.

## Recommended durable fix shape

1. **Split the file** into stable-section (system prefix, cacheable) and dynamic-section (dynamic_instructions).
2. **Wire `PROMPT_TYPE_LIVING_WORLD`** into the 7 missing agents: HeavyDialogAgent, GodModeAgent, DialogAgent, StoryModeAgent, LevelUpAgent, FactionManagementAgent, PlanningAgent, RewardsAgent, CharacterCreationAgent, CombatAgent.
3. **Add a contract test** in `$PROJECT_ROOT/tests/test_living_world_delivery.py`:
   - Load each agent's system instruction
   - Assert "Major Event Rarity Budget" is present (not just the stub "Living World Advancement Protocol" header)
   - Assert file body content > 5,000 tokens (catches the stub regression)
4. **Add a BQ regression check** (cron or pre-merge):
   - Per-agent `has_lw_header_pct` and `has_major_event_budget_pct`
   - Alert if any agent drops below 90%

## Cross-references

- **`llm-prompt-delivery-audit` umbrella skill** — the 5-step wire diagnostic, the 5 root-cause patterns, and the durable-fix shape. Load this first.
- **`references/god-mode-directive-missing-subclasses.md`** — the sibling class for runtime user-emitted directives. Load this if the suspect rule comes from god-mode, not from a prompt file.
- **`references/repro-llm-invented-lore-artifacts-2026-07-18.md`** (Bug Class 4) — the prompt-**content** sibling fix shipped in PR #8443. Different bug class (rule is wrong in the prompt file, fix the prompt content); the prompt-delivery class is rule is missing from the request entirely, fix the dispatcher.
- **`references/phenotype-lock-static-evidence.md`** — the 3 static-evidence greps that should run BEFORE deciding which class. The "code-symbol grep" in `$PROJECT_ROOT/prompts/` is the gate that catches the delivery-vs-content fork early.

## Pitfalls

**Pitfall 1 — Treating this as a content bug.** The instinct when the user reports "LLM keeps doing X" is to grep the prompt file, find X is forbidden there, and conclude "must be LLM compliance issue" — then go fix the prompt content. But if Step 3 shows the file body isn't in the request, no amount of prompt-content engineering will help. **Always check the wire first.**

**Pitfall 6 — Concluding "prompt delivery works" because the file is loaded into the served prompt.** A subtle extension of Pitfall 5: Step 3 may show the on-disk file body is present in the request (full content, not a stub) AND `has_<rule_header>` is 100%, yet the operational rule can still be functionally buried. Verified case study: campaign `wc2BBcSgOljiU3vJ160A` (PR #8527 / issue #8526, 2026-07-23) — `living_world_instruction.md` was loaded as part of `StoryModeAgent.REQUIRED_PROMPT_ORDER` (so the file body was in the served prompt at full 60K length, confirmed via `PromptBuilder.build_from_order` output), but the `Turn 3: MANDATORY - Initialize first companion quest arc` rule lived at offset 59,642 / 60,375 (98.8%) of the living-world part and 291,436 / 292,169 (99.7%) of the full served prompt. The LLM tuned the rule out across 169+ trigger turns and never wrote `state_updates.custom_campaign_state.next_companion_arc_turn` or `state_updates.companion_arcs`. Empirical proof: 0/219 character-mode turns wrote either field. The dynamic-injection channel (`build_living_world_instruction`) emitted only a 5-line stub with no companion-quest content, so the recency window carried zero mirror of the rule.

**Fix shape for this sub-class:** mirror the operational obligation into the dynamic-injection channel so it lands in the LLM's recency window on every trigger turn, NOT just rely on the static cached prefix. The static file keeps the high-cadence policy context; the dynamic block carries the per-turn obligation echo.

**Diagnostic that catches it:** Step 3 should report not just `has_<rule_header>` but also `<rule_position_in_request_pct>`. Diagnostic Python recipe (verified):
```python
from mvp_site.agent_prompts import PromptBuilder
from mvp_site.agents import StoryModeAgent
parts = PromptBuilder(game_state=None).build_from_order(StoryModeAgent.REQUIRED_PROMPT_ORDER, turn_number=1)
full = ''.join(parts)
offset = full.find('<canonical-rule-substring>')
pct = 100 * offset / len(full)
print(f'rule at {offset}/{len(full)} = {pct:.1f}% through prompt')
# RULE: if pct > 90, the rule is buried regardless of has_<rule> being true
```
If the rule is past the 90% mark of the served prompt, it's buried. **Do NOT conclude "prompt works" based on `has_<rule>` alone.**

**Cross-skill rule:** when verifying the fix, also assert in the contract test that the rule appears in the dynamic-injection block at offset `< 2K` (recency window), not just that the dynamic block contains the string somewhere. Position matters as much as presence.

**Sibling pattern:** the same lost-in-the-middle failure mode produced this issue as the 3rd sibling on `wc2BBcSgOljiU3vJ160A` (#8508 / #8509 backend, #8510 prompt anchor, #8526 companion-quest cadence). The campaign itself has a structural prompt-bloat / buried-rule class that surfaces different symptoms. Per `references/repro-planning-block-and-campaign-cluster-2026-07-18.md` cluster-signal trigger (≥3 siblings → root-cause-first prompt fix addressing the common anchor layer), the 3rd sibling triggers a fix addressing buried-rule / lost-in-the-middle.

**Pitfall 2 — Believing the `del advances_time  # Unused after <prompt> moved to dynamic path` comment is harmless.** It's the smoking gun. Search for that exact comment in `$PROJECT_ROOT/agent_prompts.py` to find every prompt file that was moved to dynamic_instructions and may have lost content in the move.

**Pitfall 3 — Per-agent column breakdown is essential.** Aggregating `has_lw_header` across all agents hides the bug (overall could be 50%+, masking the 0% agents). The smoking gun is the agent-level column where one row is 95%+ and adjacent rows are 0%. Always `GROUP BY agent, event_type`.

**Pitfall 4 — `is_test = false` filter is mandatory.** The `llm_payloads` table contains thousands of test fixtures (verified 2026-07-20 — the 1.5% rate includes test rows). Without the filter, the percentages are misleadingly high because tests often include the full prompt.

**Pitfall 5 — The 7-line stub IS in the request.** `has_lw_header` will be true on stubbed requests because the stub starts with `🌍 LIVING WORLD POLICY`. The discriminator is `has_major_event_budget` (0% on stubs) or `LENGTH(request_json)` (stubs are much smaller than full-payload requests). Use both, not just the header.