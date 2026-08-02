# Factor G — Prompt-side default missing (worked example #8497)

**Status:** NEW (2026-07-21, issue [#8497](https://github.com/$GITHUB_REPOSITORY/issues/8497), campaign `q04GfOEl4SWnEQrFUVST`)

This file documents the **7th sibling** of the directive-pairing-invariant bug family
(see `references/god-mode-directive-missing-subclasses.md` for the full A-F history).

## What Factor G is

The LLM **correctly writes** `directives.add` AND the directive **propagates** to subsequent turns — but the underlying prompt layer has **no compact default-classifier rule** stating which side of a multi-aspect mechanic is canonical. The user is forced to god-mode-reinforce on every fresh campaign that imports the mechanic.

Factor G is the **prompt-anchor half** of the same problem Factor F exposes. F is the LLM not writing at all; G is the LLM writing correctly but the underlying prompt having no anchor for the rule.

## Why it's distinct from F

| Factor | LLM writes `directives.add`? | Prompt has default-classifier? | Symptom |
|---|---|---|---|
| F (narrative-ack-as-write) | **No** | Doesn't matter | User's directive forgotten next turn |
| **G (prompt-default-missing)** | **Yes** | **No** | User's directive works for one turn, but every fresh campaign needs manual god-mode reinforcement |

## Pattern (verified campaign `q04GfOEl4SWnEQrFUVST` turn 31, 2026-07-21 05:53:11 UTC)

1. Campaign uses a multi-aspect mechanic (Mantle of the Radiant Slayer — Sanguine Sovereign Aspect I vs Chitinous Ruin Aspect II), imported from a `world_reference/campaign_module_*.md` file.
2. The `$PROJECT_ROOT/prompts/` layer has **zero references** to the mechanic's vocabulary:
   ```bash
   rg -i 'slayer|sanguine sovereign|chitinous ruin|mantle of the radiant' $PROJECT_ROOT/prompts/
   # → 0 hits in divine_leverage_system.md, narrative_system_instruction.md, etc.
   ```
3. User narrates: *"assassinate Karlach if surprise works with my full abilities and slayer form for bonuses..."*
4. LLM responds with **the wrong aspect** (Aspect II Chitinous Ruin / obsidian wings) because there's no system-level default rule — the LLM has to re-derive from 350KB of RAG context every turn.
5. User corrects in god mode: *"You forgot I always wanna use the nice looking slayer form"*
6. LLM **correctly** emits `directives.add = ["Default all divine/slayer manifestations to 'Aspect I: The Sanguine Sovereign' (The Divine Visage) unless otherwise specified by the player."]`
7. Next turn (turn 32 at 06:01:44 UTC) — the directive **works**: response opens with Aspect I (liquid-ruby wings, High Elf visage).

So the directive machinery works. The gap is purely **prompt-side**: the campaign module defines the mechanic but no system prompt says "default to Aspect I." Every fresh campaign using this module will hit the same drift.

## ⚠️ CRITICAL PITFALL — Verify the LLM actually received the rule before classifying as Factor G

**The single most common mistake on Factor G is to skip the BQ raw-request inspection and jump straight to "add a default-classifier § to the prompt file." This is WRONG.**

The canonical Factor G anti-pattern (user pushback 2026-07-21):

> *"are you stupid? ... The fucking fix isn't to hardcode slayer form into the prompt it's to fucking investigate the BQ LLM raw requests like I asked and see if the llm even received the instruction"*

The "obvious" fix — adding `divine_leverage_system.md` §"Default Aspect Classifier: When the player invokes their Slayer Form, default to Aspect I: The Sanguine Sovereign..." — would have been:

1. **Wrong root cause** — the LLM already received the rule (Mantle of the Radiant Slayer §5 at offsets 25249–33400 of the request, plus the prior god-mode "Transcendent Beauty confirmed" block at offsets 139038–140903). The drift was architectural, not instructional.
2. **Same anti-pattern at a different layer** — a hardcoded "Slayer Form default to Sanguine Sovereign" rule in the prompt layer couples every future campaign to one specific mechanic. The right fix is a policy that forbids this kind of coupling, not another instance of it.

**Mandatory diagnostic — BEFORE proposing any prompt-layer fix for Factor G:**

1. Pull the LLM request for the buggy turn from BQ:
   ```sql
   SELECT turn_index, agent, ingested_at, request_json, response_text
   FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
   WHERE campaign_id = '<CID>'
     AND ingested_at BETWEEN TIMESTAMP('<buggy_turn_ts - 1s>') AND TIMESTAMP('<buggy_turn_ts + 1s>')
   ORDER BY ingested_at ASC
   LIMIT 1
   ```
2. Save the `request_json` to disk. Strip the BQ truncation suffix (`...[TRUNCATED request_json original_bytes=... sha256=...]`) if present.
3. Grep the saved request for the mechanic's vocabulary AND the user's directive text. If both appear in the request — the LLM DID receive the rule. **Factor G is NOT missing-instruction; reclassify to "instruction drift / architectural coupling" and the fix is NOT a prompt rule.**
4. Only if the rule is missing from the request do you have a true Factor G (prompt not delivered to LLM) — and even then, the fix should be **schema/loader alignment** (ensure the campaign description is loaded before character-mode turns), NOT a hardcoded prompt rule.

If the rule IS in the request but the LLM ignored it — that's bucket 7.7 in the /repro classification, which this whole skill is built on. The fix path is "policy + lint + tests" (PR #8498, see below), NOT "more prompt text."

## Diagnostic

When a user reports "LLM keeps picking the wrong aspect/variant/stance/alignment" on a mechanic that has multiple canonical variants:

1. **Phenotype-lock code-symbol grep** across `$PROJECT_ROOT/prompts/`:
   ```bash
   rg -i '<mechanic_keyword>|<aspect_1_name>|<aspect_2_name>' $PROJECT_ROOT/prompts/ --type=md
   ```
   If 0 hits AND the LLM DID receive the rule via RAG/story-history — **this is NOT missing-instruction**. Reclassify as "instruction drift / architectural coupling." Fix is policy + lint, not prompt text. (See the corrected fix shape below.)
   If 0 hits AND the rule is also missing from the LLM's request — true Factor G. Fix is schema/loader alignment.
2. **BQ check** for the directive's persistence and propagation:
   ```sql
   SELECT turn_index, agent, request_json, response_text
   FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
   WHERE campaign_id = '<CID>' AND turn_index BETWEEN <user_turn-1> AND <user_turn+1>
   ORDER BY ingested_at ASC
   ```
   If the LLM **did** emit `directives.add` AND the next-turn response honored it: persistence works, the gap is either prompt-anchor-missing (rare) or instruction-drift (common — rule was in RAG but LLM didn't re-derive it this turn).
3. **Compare against the canonical sibling** (Factor F via `references/god-mode-directive-missing-subclasses.md` §"Factor F"). If the LLM **did** emit `directives.add`, this is **G, not F** — but ALSO not "missing instruction."

## Fix shape — REVISED 2026-07-21 (PR #8498)

**Do NOT add a hardcoded prompt rule.** The earlier fix shape documented below (adding a §"Default Aspect Classifier" to the relevant prompt file) was a candidate but was REJECTED by the user. The shipped fix is a policy + automation pattern that:

1. **Forbids campaign-specific terms in `$PROJECT_ROOT/prompts/`** — the rule file `$PROJECT_ROOT/prompts/CLAUDE.md` defines a banned-name list (named characters from any `world_reference/campaign_module_*.md`, named mechanics, setting-specific names) plus an exception process: explicit per-PR `CAMPAIGN-SPECIFIC PROMPT EXCEPTION APPROVED` from the operator.
2. **Adds the same rule to repo-root `CLAUDE.md`** as a BANNED anti-pattern (inserted adjacent to the existing "Class-specific hardcoding in code or prompts" rule).
3. **Ships a CI lint** `scripts/check_prompt_agnosticism.py` — exit 1 on banned terms outside `e.g.` blocks.
4. **Pins with 8 contract tests** in `$PROJECT_ROOT/tests/test_prompt_agnosticism_8497.py`.

Verified on 2026-07-21: PR [#8498](https://github.com/$GITHUB_REPOSITORY/pull/8498), branch `docs/campaign-agnostic-prompts-clause`, HEAD `abef75a278`. +492/-0 across 4 files.

**Why this fix shape is correct:** the Sanguine Architecture "Aspect I default" rule ALREADY lives in the campaign module (`world_reference/campaign_module_god_of_murder.md` §5 Mantle of the Radiant Slayer). The LLM received it (verified via BQ). The drift is that the LLM is free to ignore it on any given turn because it competes against 350KB of other context. The right fix is NOT to add another layer of the same anti-pattern (a hardcoded prompt rule), it's to:

- Acknowledge that campaign-specific rules should NOT live in the prompt layer at all
- Make the prompt layer campaign-AGNOSTIC so no future prompt addition can re-introduce the coupling
- Ensure campaign-specific content loads correctly via RAG / `story_history[0].description` / `custom_campaign_state.directives` (existing mechanism — the directive DID propagate to turn 32)
- Use the policy + lint to enforce the architectural boundary

## Anti-pattern — adding a hardcoded prompt rule

**The earlier candidate fix shape (rejected 2026-07-21):**

> Three files, ~+140 lines total:
> 1. **Relevant prompt file** (e.g. `$PROJECT_ROOT/prompts/divine/divine_leverage_system.md` for the Mantle of the Radiant Slayer) — add a §"Default Aspect Classifier" section with default aspect / alternate aspects / Persistent Override clauses.
> 2. **`$PROJECT_ROOT/prompts/god_mode_instruction.md`** — add the exact rule as a worked example.
> 3. **`$PROJECT_ROOT/tests/test_<classifier>_*.py`** — 6 tests pinning the classifier.

**Why this was rejected:** the user said *"The fucking fix isn't to hardcode slayer form into the prompt."* The campaign-specific "Sanguine Sovereign default" rule would couple every future campaign to one mechanic. The same anti-pattern at the prompt layer as the original bug was at the RAG-context layer.

**The lesson generalizes:** for ANY mechanic that lives in `world_reference/campaign_module_*.md`, the rule belongs in the campaign module, NOT in `$PROJECT_ROOT/prompts/`. The prompt layer should describe generic structural concepts ("multi-aspect deity", "default aspect", "opt-in aspect", "persistent campaign directive") without naming a specific mechanic.

## Worked example — the BQ raw-request inspection that exposed the misclassification

PR #8498's body and PR description include the full BQ evidence chain. The shortest reproduction:

```sql
SELECT turn_index, agent, ingested_at, SUBSTR(request_json, 1, 200) as req_head, request_json
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE campaign_id = 'q04GfOEl4SWnEQrFUVST'
  AND ingested_at BETWEEN TIMESTAMP('2026-07-21 05:53:09') AND TIMESTAMP('2026-07-21 05:53:12')
ORDER BY ingested_at ASC LIMIT 1
```

The `request_json` (350KB, truncated) contains:
- `Mantle of the Radiant Slayer` (2 matches at offsets 25249, 26681)
- `Sanguine Sovereign` (9 matches)
- `Chitinous Ruin` (1 match at offset 28450)
- `Transcendent Beauty confirmed` (2 matches at offsets 139038, 140785)
- `Aspect I:` (1 match at offset 27554)
- `Aspect II:` (1 match at offset 28435)
- `Visual Preference Set` (0 matches — the user's directive hadn't been added yet)
- `Default all divine/slayer` (0 matches — same reason)

**Verdict:** the LLM received every mechanic and the prior god-mode "Transcendent Beauty confirmed" directive. It chose Aspect II anyway. The drift is NOT missing-instruction.

## Cross-references

- `references/god-mode-directive-missing-subclasses.md` — full 7-factor matrix (A–G)
- `references/bq-llm-payload-truncation-pitfall.md` — BQ query patterns for verifying persistence + propagation
- `references/phenotype-lock-static-evidence.md` — the code-symbol grep recipe that flags Factor G (0 hits for the mechanic's vocabulary in `$PROJECT_ROOT/prompts/`)
- PR [#8498](https://github.com/$GITHUB_REPOSITORY/pull/8498) — the actual shipped fix: campaign-agnostic prompts policy + lint + tests (NOT a hardcoded prompt rule)
- PR [#8491](https://github.com/$GITHUB_REPOSITORY/pull/8491) — sibling fix pattern that DOES belong in a prompt file (combat-scope classifier — campaign-AGNOSTIC; uses generic CR / combatant thresholds)
- **Diagnostic discipline rule (NEW 2026-07-21):** ALWAYS pull the BQ raw-request before proposing a prompt-layer fix. If the LLM already received the rule, the bug is NOT missing-instruction and the fix is NOT a prompt rule.