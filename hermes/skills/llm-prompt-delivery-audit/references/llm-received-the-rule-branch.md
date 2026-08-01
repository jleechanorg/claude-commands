# Step 6 — The LLM-received-the-rule branch (worked example PR #8498)

**Status:** NEW (2026-07-21, verified on campaign `q04GfOEl4SWnEQrFUVST` turn 31 + PR [#8498](https://github.com/$GITHUB_REPOSITORY/pull/8498))

This file documents the **decision branch** that fires when the canonical `llm-prompt-delivery-audit` 5-step wire diagnostic confirms the rule IS reaching the LLM but the LLM still drifts. The wrong reflex is "add the rule to the prompt file" — the right reflex is to reclassify and route to a different fix shape.

## Origin incident — Sanguine Architecture "Slayer Form" drift (2026-07-21)

User report (campaign `q04GfOEl4SWnEQrFUVST`, scene 77, turn 31): *"the llm forgot I asked it to always use the nice looking slayer form."* User follow-up after my first misdiagnosis: *"are you stupid? ... The fucking fix isn't to hardcode slayer form into the prompt it's to fucking investigate the BQ LLM raw requests like I asked and see if the llm even received the instruction."*

The campaign is the Sanguine Architecture / "God of Murder BG3" module from PR [#8483](https://github.com/$GITHUB_REPOSITORY/pull/8483). The mechanic: Mantle of the Radiant Slayer with two aspects — Aspect I (Sanguine Sovereign / nice-looking divine visage) and Aspect II (Chitinous Ruin / monstrous obsidian form). User wanted Aspect I as default.

The user had already manually god-mode-reinforced earlier in the turn with *"you forgot I always wanna use the nice looking slayer form"*. LLM responded by writing `directives.add = ["Default all divine/slayer manifestations to 'Aspect I: The Sanguine Sovereign' (The Divine Visage) unless otherwise specified by the player."]`. Next turn (turn 32) honored the directive. So the **directive machinery works** going forward — the bug was the moment the LLM produced the bad output, before the correction could land.

## Step 6 diagnostic — verify the LLM actually received the rule

BQ query (per `llm-prompt-delivery-audit` Step 3):

```sql
SELECT turn_index, agent, ingested_at, request_json, response_text
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE campaign_id = 'q04GfOEl4SWnEQrFUVST'
  AND ingested_at BETWEEN TIMESTAMP('2026-07-21 05:53:09') AND TIMESTAMP('2026-07-21 05:53:12')
ORDER BY ingested_at ASC
LIMIT 1
```

Save the 350KB `request_json`. Strip BQ truncation suffix. Grep:

| Pattern | Hits | Where |
|---|---|---|
| `Mantle of the Radiant Slayer` | 2 | offsets 25249, 26681 — §5 mechanic + diagram |
| `Sanguine Sovereign` | 9 | campaign description §5 + prior narrative |
| `Chitinous Ruin` | 1 | Aspect II definition offset 28450 |
| `Radiant Slayer` | 3 | §5 + phase 4 references |
| `Transcendent Beauty confirmed` | 2 | prior god-mode turn offsets 139038, 140785 |
| `Aspect I:` / `Aspect II:` | 1 / 1 | §5 explicit aspect text |
| `Visual Preference Set` | **0** | user's god-mode directive NOT yet in this request |
| `Default all divine/slayer` | **0** | same — directive was added after this turn |

**Verdict:** the LLM received the Mantle of the Radiant Slayer §5 mechanic + the prior god-mode "Transcendent Beauty confirmed" directive. The bug is **NOT missing-delivery**.

Timeline reconstruction:
- `05:53:11` HeavyDialogAgent turn 31 → produces obsidian-wing bug (the moment the user saw in browser)
- `05:54:02` GodModeAgent turn 31 → user correction → LLM emits `directives.add`
- `05:55:57+` subsequent turns → directive propagates (turn 32 verified)

The bug fired at the moment the LLM produced the bad output, BEFORE the correction could land. The LLM had the mechanic in context but defaulted to Aspect II.

## Reclassification — the wrong reflex vs the right reflex

**Wrong reflex (the one I almost shipped):** add a §"Default Aspect Classifier" to `$PROJECT_ROOT/prompts/divine/divine_leverage_system.md` saying *"When the player invokes their Slayer Form, default to Aspect I: The Sanguine Sovereign."*

**Why this is wrong:**

1. **Wrong root cause** — the LLM already received the rule. Adding another copy of the rule at the prompt layer doesn't address why the LLM defaulted to Aspect II (it's buried 100+ KB deep in `story_history[0].text` and competing with thousands of other tokens).
2. **Same anti-pattern at a different layer** — a hardcoded "Slayer Form default to Sanguine Sovereign" rule couples every future campaign to one specific mechanic. The original bug was "the mechanic lives deep in RAG and the LLM ignores it sometimes." The fix-shape mistake would be "the mechanic lives deep in RAG AND also in the prompt, and the LLM still ignores it sometimes" — same problem, no improvement.

**Right reflex (PR [#8498](https://github.com/$GITHUB_REPOSITORY/pull/8498)):** acknowledge that campaign-specific rules should NOT live in the prompt layer at all. Make the prompt layer campaign-AGNOSTIC so no future prompt addition can re-introduce the coupling. Campaign-specific content stays in `world_reference/` and loads via RAG / `story_history[0].description` / `custom_campaign_state.directives` (existing mechanism — the directive DID propagate to turn 32).

## Shipped fix — policy + lint + tests

PR [#8498](https://github.com/$GITHUB_REPOSITORY/pull/8498), branch `docs/campaign-agnostic-prompts-clause`, HEAD `abef75a278` (+492/-0 across 4 files):

| File | Change |
|---|---|
| `CLAUDE.md` | New BANNED anti-pattern: **Campaign-agnostic prompts** (inserted adjacent to existing "Class-specific hardcoding in code or prompts" rule) |
| `$PROJECT_ROOT/prompts/CLAUDE.md` | NEW 260-line rule file with banned-name list, allowed generics, PASS/FAIL examples, `CAMPAIGN-SPECIFIC PROMPT EXCEPTION APPROVED` exception process |
| `scripts/check_prompt_agnosticism.py` | NEW 200-line CI lint — exit 1 on banned terms outside `e.g.` blocks |
| `$PROJECT_ROOT/tests/test_prompt_agnosticism_8497.py` | NEW 8 contract tests pinning the rule + lint + detection logic |

### What is banned

- **Named characters** from any `world_reference/campaign_module_*.md`: Nocturne, Karlach, Astarion, Shadowheart, Gale, Lae'zel, Minthara, Wyll, Halsin, Jaheira, Minsc, Sarevok, Viconia, Orin, Bhaal, Bane, Myrkul, Kelemvor, Vlaakith, Elminster, Cyric, the Dark Urge, etc.
- **Named campaign-specific mechanics**: Slayer Form, Mantle of the Radiant Slayer, Sanguine Sovereign, Chitinous Ruin, Tragic Betrayal doctrine, 5-Pillar Dread Court, 3-Generation Power Lineage, 3e God Combat, Sanguine Pulse, Murderous Manifestation, Murderous Mask, Transcendent Beauty, etc.
- **Setting-specific names** beyond D&D 5e baseline canon: Faerûn, Baldur's Gate, Elturel, Waterdeep, Neverwinter, Avernus, the Fugue Plane, the Sword Coast, etc.
- **Specific numerical thresholds** tied to a single campaign's design.

### What IS allowed

Generic D&D 5e vocabulary (deity, divine rank, portfolio, domain, aspect, exalted stance, manifestation, divine spark, worship, follower, proficiency bonus, spell slot, advantage, disadvantage, conditions, CR, XP, AC, HP) PLUS the structural concepts "multi-aspect deity", "default aspect", "opt-in aspect", "persistent campaign directive".

### Exception process

Explicit per-PR `CAMPAIGN-SPECIFIC PROMPT EXCEPTION APPROVED` from the operator in the originating chat thread. Scoped to a named, reviewed, narrowly-bounded prompt fragment.

### Follow-up

6 existing prompt files (`master_directive.md`, `planning_protocol.md`, `living_world_instruction.md`, `god_mode_instruction.md`, `narrative_system_instruction.md`, `game_state_instruction.md`) still contain banned terms. Cleanup tracked separately under issue #8497 followup. Contract test `test_lint_script_exits_zero_on_clean_repo` is intentionally permissive until cleanup lands via follow-up PRs — the lint itself flags them as `error`.

## The decision matrix (use this when Step 5 ends with "rule IS in request")

| Symptom | The rule is in the request? | Fix shape | Skill routing |
|---|---|---|---|
| LLM ignores rule, rule NOT in request | No | **Prompt-delivery fix** — restore file to dispatcher; wire `PROMPT_TYPE_<NAME>` into missing agents | `llm-prompt-delivery-audit` Steps 1-5 |
| LLM ignores rule, rule IS in request (campaign-specific mechanic) | Yes | **Policy + lint fix** (PR #8498 shape) — `$PROJECT_ROOT/prompts/CLAUDE.md` + lint + tests; do NOT add a hardcoded prompt rule | This reference file (Step 6) |
| LLM ignores rule, rule IS in request (generic 5e mechanic like a stat-block rule) | Yes | **Prompt-content fix** — add a compact worked example in the relevant prompt file | `llm-narration-format-clarifier` |
| LLM drifts on multi-aspect mechanic, rule IS in request, prior god-mode correction worked for one turn | Yes | **Schema/loader alignment** — fix the campaign description loader; ensure §5 mechanic is loaded before first character-mode turn | `repro` skill §"Factor G" |
| LLM ignores rule across multiple unrelated campaigns | Yes (multiple campaigns) | **Prompt-engineering fix** — the rule is wrong / ambiguous / underspecified in the prompt layer | `llm-prompt-engineering` |

## Pitfalls

1. **Don't trust the user's first message framing.** The user said "LLM forgot I asked it to always use the nice looking slayer form." That sounds like missing-instruction. It's NOT — the LLM received the instruction. Always run the BQ raw-request diagnostic before forming the root-cause hypothesis.

2. **Don't propose "add a prompt rule" reflexively.** Even when the rule IS missing from the prompt layer, adding a hardcoded rule isn't always the right fix. Consider whether the rule belongs at the prompt layer at all. For campaign-specific mechanics, the rule belongs in the campaign module, NOT in `$PROJECT_ROOT/prompts/`.

3. **The Step 5 cross-check is the smoking gun, not Step 4.** Step 4 (extract block from request) tells you what reached the LLM. Step 5 (count `complaint_in_resp`) tells you how often the LLM ignored the rule. When Step 5 shows 90%+ drift AND Step 4 shows the rule is in the request, you have the architectural-coupling signature — not a delivery bug.

4. **Don't confuse scene numbers with turn_index.** In this case, the user said "scene 77" but the campaign's `MAX(turn_index) = 32`. The scene number comes from `user_scene_number` in the story entries, which is a different counter. Always confirm with `SELECT MAX(turn_index)` before assuming the user's scene ref (see `repro` skill `references/bq-llm-payload-truncation-pitfall.md` §"scene-number-vs-turn_index mismatch").

5. **The 350KB BQ payload truncation is significant.** The on-disk `request_json` is capped at 350KB regardless of actual size (verified 914KB sha256 `857372994f95848ea9d98e349d7f23bfb0be66cd1075aa42e46e16228f4afd12`). The Mantle of the Radiant Slayer §5 + the "Transcendent Beauty confirmed" block were both within the truncated portion, but a future investigation might hit a mechanic that lives past the truncation boundary. Plan B: use `bq query` with `EXPORT DATA` to GCS for full payloads, or expand `llm_payloads.request_json` column size limit.

6. **The user-explicit pushback is a class-level signal.** Jeffrey's *"are you stupid? ... investigate the BQ LLM raw requests ... and see if the llm even received the instruction"* is the operational form of the missing-diagnostic discipline. This is not a one-off complaint — it's a workflow rule that should be encoded in EVERY prompt-related skill. Future agents who skip the BQ diagnostic when investigating an LLM behavior complaint will hit the same pushback.

## Cross-references

- `llm-prompt-delivery-audit` SKILL.md §"Step 6" — the umbrella skill's diagnostic recipe
- `repro` skill `references/god-mode-directive-factor-g-prompt-default-missing.md` — Factor G diagnostic (does the prompt layer have the mechanic's vocabulary at all?). The Factor G recipe was originally "add a §Default Aspect Classifier" — that recipe is superseded by the PR #8498 fix shape; see the rewritten Factor G file's §"Fix shape — REVISED 2026-07-21"
- `repro` skill `references/bq-llm-payload-truncation-pitfall.md` — BQ query patterns for verifying persistence + propagation; also covers the `turn` vs `turn_index` column pitfall and the scene-number-vs-turn_index mismatch
- PR [#8498](https://github.com/$GITHUB_REPOSITORY/pull/8498) — the actual shipped fix
- PR [#8491](https://github.com/$GITHUB_REPOSITORY/pull/8491) — sibling fix shape (combat-scope classifier — campaign-AGNOSTIC, lives in a prompt file because the rule is generic 5e mechanics, not a specific campaign's mechanic)
- Issue [#8497](https://github.com/$GITHUB_REPOSITORY/issues/8497) — origin incident