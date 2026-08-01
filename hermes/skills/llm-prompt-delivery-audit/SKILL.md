---
name: llm-prompt-delivery-audit
version: 1.0.0
description: "Diagnose whether the prompt content on disk actually reaches the LLM on the wire. The class-level umbrella for any case where the user complaint looks like a prompt-content problem (rule is wrong, format is off, instruction is missing) but the real root cause is that the LLM never sees the prompt file at all — the dispatcher returns a stub, the agent loader skips the file, the dynamic_instructions tail replaced the static section, or the cache-key split put the policy on the wrong channel. Verified 2026-07-20 on $GITHUB_REPOSITORY — PR #8005 (Jun 29) moved living_world_instruction.md to dynamic_instructions for cache stability but kept only a 7-line stub, so the 1,080-line Major Event Rarity Budget + Trigger Whitelist + Lore-Appropriate Enemy Detection guardrails never reached the LLM for 6 weeks. The user reported stop the scrying/auditors, only one antagonistic event weekly — the rules existed in the prompt file, but the LLM had no idea."
tags: ["llm", "prompts", "prompt-delivery", "bq", "forensics", "worldarchitect", "agent_prompts", "cache", "dynamic_instructions"]
category: devops
triggers:
  - llm ignores my prompt rule
  - the prompt says X but the LLM does Y
  - is my prompt reaching the LLM
  - the instructions aren't working
  - the LLM keeps violating rule
  - why does the LLM keep doing X when the prompt forbids it
  - prompt not being followed
  - are my instructions reaching the model
  - the rule exists but the LLM ignores it
  - verify the prompt is in the request
  - audit prompt delivery
  - check what the LLM actually receives
  - rule not working
  - living world not working
  - antagonistic events not working
related_skills:
  - repro
  - wa-campaign-content-analysis
  - wa-prod-data-query
  - finish-the-job
changelog:
  - "1.0.0 (2026-07-20): Initial umbrella. Three concrete techniques from the your-project.com living_world_instruction.md audit: (1) BQ forensic against llm_forensics.llm_payloads.request_json — grep for stable prompt-section anchors (file header, key section names) to confirm the file content reached the LLM. (2) Per-agent column breakdown — group by (agent, event_type) and compute has_section_pct per agent. The smoking gun is when one agent shows 95%+ and others show 0% — the file exists, the dispatcher is selective. (3) Dynamic vs static split detection — when a prompt file is moved to dynamic_instructions for cache stability, the static file content is often replaced by a small activation tail. Verify on the wire by extracting REGEXP_EXTRACT(request_json, anchor-50chars) from a real call and checking if the matched text is the file body or a stub."
  - "1.1.0 (2026-07-21): NEW BRANCH — 'LLM received the rule, but ignored it.' The 5-step wire diagnostic now has an explicit Step 6 for when the rule IS reaching the LLM but the LLM still drifts (verified on campaign `q04GfOEl4SWnEQrFUVST` turn 31 — Sanguine Architecture Mantle of the Radiant Slayer; user said 'are you stupid? ... The fucking fix isn't to hardcode slayer form into the prompt it's to fucking investigate the BQ LLM raw requests ... and see if the llm even received the instruction'). When Steps 1-5 confirm the rule IS in the request_json (Mantle of the Radiant Slayer §5 at offsets 25249-33400 + prior god-mode 'Transcendent Beauty confirmed' block at offsets 139038-140903), the bug is NOT missing-delivery — reclassify as 'instruction drift / architectural coupling.' The fix is NOT another hardcoded prompt rule (that would be the same anti-pattern at a different layer, coupling every campaign to one mechanic). The fix is **policy + lint**: add a BANNED anti-pattern in repo-root CLAUDE.md (campaign-agnostic prompts) + a new `$PROJECT_ROOT/prompts/CLAUDE.md` rule file with banned-name list + `scripts/check_prompt_agnosticism.py` CI lint + 8 contract tests in `$PROJECT_ROOT/tests/test_prompt_agnosticism_8497.py`. Verified on PR [#8498](https://github.com/$GITHUB_REPOSITORY/pull/8498), branch `docs/campaign-agnostic-prompts-clause`, HEAD `abef75a278` (+492/-0 across 4 files). Companion file: `references/llm-received-the-rule-branch.md` documents the Step 6 diagnostic + the campaign-agnosticism policy fix shape with worked example + the 'prompt rule vs policy + lint' decision matrix."
---

# llm-prompt-delivery-audit

**The class-level umbrella for "is the prompt actually reaching the LLM?"** Use this whenever the user reports an LLM behavior that contradicts a prompt rule — before assuming the prompt content is wrong, verify the prompt content actually reaches the model. The most common root cause is a prompt-**delivery** failure, not a prompt-content failure.

## When this skill fires

Trigger on any of:
- User: "the LLM ignores rule X / keeps violating Y / isn't following the prompt"
- User: "stop the [behavior]" — and grepping the prompt file finds a rule forbidding the behavior
- A prompt file was recently edited (or moved to dynamic_instructions for cache stability) and now user reports drift
- A repro shows a behavior pattern that exists as a forbidden clause in the relevant prompt file
- A new repro pattern shows the same anti-pattern across N campaigns / N agents — likely a structural prompt-delivery issue

**Anti-trigger:** If the LLM is failing to follow a rule that the prompt file explicitly contains AND that file's content is verifiably reaching the LLM, this is a prompt-content / prompt-engineering issue. **BUT** it is NOT necessarily a "add another prompt rule" issue — see **Step 6 — The LLM-received-the-rule branch** below for the reclassification decision tree (verified on campaign `q04GfOEl4SWnEQrFUVST`, PR [#8498](https://github.com/$GITHUB_REPOSITORY/pull/8498)). Route to `repro` skill's `references/god-mode-directive-factor-g-prompt-default-missing.md` if the symptom is "LLM keeps picking the wrong aspect/variant."

## The 5-step wire diagnostic

### Step 1 — Confirm the rule exists in the prompt file on disk

```bash
# Find the prompt file
grep -rn "<rule_text_or_keyword>" $PROJECT_ROOT/prompts/ --include="*.md"

# Confirm the file exists in the canonical location
ls -la $PROJECT_ROOT/prompts/<prompt_file>.md
```

If the file doesn't exist or the rule isn't in it → that's a content gap, not a delivery gap. Use `repro` skill's prompt-fix-deliverable-shape pattern.

If the file exists AND the rule is in it → continue to Step 2.

### Step 2 — Find where the prompt file is loaded into the dispatcher

```bash
grep -rn "<prompt_file>" $PROJECT_ROOT/ --include="*.py" | head -20
```

You're looking for the call site that loads the file content and emits it into the LLM payload. Common patterns:
- `parts.append(_load_instruction_file(constants.PROMPT_TYPE_<NAME>))` → loads whole file
- `pb.build_<name>_instruction(turn_number)` → returns a string (might be a stub!)
- `dynamic_instructions=...` argument → dynamic channel, may be a small tail

For each call site, read the function body. **If it returns a hardcoded string instead of loading the file content, that's a delivery bug — the function has been refactored to emit a stub.**

**Pitfall (verified 2026-07-20):** A function named `build_<prompt>_instruction()` may have been "moved to dynamic path" for cache stability, and the body may have been reduced to a 7-line activation tail. The on-disk file is intact, but only the tail reaches the LLM. The `del advances_time  # Unused after <prompt> moved to dynamic path` comment in `$PROJECT_ROOT/agent_prompts.py:1469` is the marker for this pattern.

### Step 3 — BQ forensic: what does the LLM actually receive?

The single source of truth is `request_json` in BQ. For your-project.com the table is `worldarchitecture-ai:llm_forensics.llm_payloads`; for other products, find the equivalent LLM payload log table.

```sql
WITH recent AS (
  SELECT
    ingested_at,
    campaign_id,
    agent,
    event_type,
    REGEXP_CONTAINS(CAST(request_json AS STRING), r'<prompt-file-header>') AS has_file_header,
    REGEXP_CONTAINS(CAST(request_json AS STRING), r'<key-section-name>') AS has_key_section,
    REGEXP_CONTAINS(CAST(request_json AS STRING), r'<specific-rule-text>') AS has_specific_rule
  FROM `<project>.llm_forensics.llm_payloads`
  WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    AND is_test = false
)
SELECT
  agent,
  event_type,
  COUNT(*) AS calls,
  COUNTIF(has_file_header) AS has_header,
  COUNTIF(has_key_section) AS has_key_section,
  COUNTIF(has_specific_rule) AS has_rule
FROM recent
GROUP BY agent, event_type
ORDER BY calls DESC
```

**Smoking gun signature:** One agent (typically `gemini_provider.stream` for gameplay_streaming) shows >95% `has_*` while every other agent shows 0%. This means: (a) the file IS loaded for the streaming path, (b) the file is NOT loaded for the dialog/levelup/etc. agents. Two fixes needed: (1) wire `PROMPT_TYPE_<NAME>` into the missing agents, (2) verify the file body is actually in the request (not a stub).

### Step 4 — Extract the actual block from a real call

```sql
SELECT
  campaign_id,
  agent,
  event_type,
  ingested_at,
  REGEXP_EXTRACT(CAST(request_json AS STRING), r'<prompt-anchor-regex>[^$]{0,500}') AS block_in_request,
  LENGTH(request_json) AS req_size
FROM `<project>.llm_forensics.llm_payloads`
WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND is_test = false
  AND REGEXP_CONTAINS(CAST(request_json AS STRING), r'<prompt-anchor>')
ORDER BY ingested_at DESC
LIMIT 5
```

If the extracted block is the full file content (1,000+ chars), the file IS reaching the LLM. If it's a 7-line stub (the "moved to dynamic_instructions" pattern), the delivery is broken.

### Step 5 — Cross-check the response side

Verify the LLM actually applied (or ignored) the rule by grepping `response_text` for the user's complaint tokens:

```sql
SELECT
  agent,
  event_type,
  COUNT(*) AS calls,
  COUNTIF(REGEXP_CONTAINS(CAST(request_json AS STRING), r'<rule-keyword>')) AS rule_in_req,
  COUNTIF(REGEXP_CONTAINS(response_text, r'<user-complaint-token>')) AS complaint_in_resp,
  ROUND(100*COUNTIF(REGEXP_CONTAINS(response_text, r'<user-complaint-token>')
                     AND NOT REGEXP_CONTAINS(CAST(request_json AS STRING), r'<rule-keyword>'))
        / COUNT(*), 1) AS pct_lm_invented
FROM `<project>.llm_forensics.llm_payloads`
WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND is_test = false
GROUP BY agent, event_type
ORDER BY calls DESC
```

**High `pct_lm_invented` (>50%) = strong signal that the missing prompt section is the cause.** If a specific anti-pattern shows up in 90-100% of agent outputs and that agent has 0% of the prompt rule, you have the smoking gun.

## The 5 common root causes

| Pattern | Symptom | Where to look |
|---|---|---|
| **A. Prompt moved to dynamic_instructions, body replaced by stub** (verified 2026-07-20, PR #8005) | File on disk is full; `build_<x>_instruction()` body returns 7-line string | `$PROJECT_ROOT/agent_prompts.py` — search for `del advances_time  # Unused after <prompt> moved to dynamic path` |
| **B. PROMPT_TYPE not wired into the agent's prompt_order** | One agent has the prompt, others don't | `$PROJECT_ROOT/agent_prompts.py` — search for `_load_instruction_file(constants.PROMPT_TYPE_<NAME>)`; check each agent's `build_from_order` call |
| **C. Per-agent dispatcher filters out the prompt** | Agent uses a mode-specific builder that excludes the prompt type | `$PROJECT_ROOT/agent_prompts.py` — search for `build_<mode>_system_instructions` and the prompt_order tuple per agent |
| **D. Cache-stable split: static section moved, dynamic tail missing** | `request_json` has partial file but missing key sections | `_load_for_build` and `_append_game_state_with_planning` in agent_prompts.py — the static-vs-dynamic seam |
| **E. RAG-retrieved version omits the rule** | `rag_query` was set and the rule didn't match the query terms | `prompt_rag.RAG_CONFIG` + the `_load_for_build` RAG path; check `rag_query` against the rule's keywords |

## The 3-step durable fix shape

When the diagnostic confirms a prompt-delivery bug:

1. **Restore the policy to the right channel.** Split the prompt file into:
   - **Stable section** (system prefix, cacheable): the rules, guardrails, schema, anti-patterns — what the LLM needs every turn.
   - **Dynamic section** (dynamic_instructions): per-turn activation tail + cadence check + per-turn state.

2. **Wire `PROMPT_TYPE_<NAME>` into the missing agents.** Update each agent's prompt_order tuple in `build_<mode>_system_instructions` to include the missing prompt type.

3. **Add a contract test that fails on regression.** Add a test in `$PROJECT_ROOT/tests/test_<prompt>_delivery.py` that:
   - Loads each agent's system instruction
   - Asserts the rule keyword is present
   - Asserts the file header is present (not a stub)
   - Asserts the file size > N tokens (catches the "stub regression" pattern)

## Verification gate (before claiming fix)

```bash
# Re-run Step 3 BQ query after deploy — every agent should now show >90%
bq query ... <re-run-with-same-query>

# Re-run Step 4 — extracted block should now be full file content, not stub
bq query ... <re-run-extract-block>

# Live LLM call with /es evidence — record request_json + response_text
# Confirm response respects the rule
```

If the BQ query post-deploy still shows 0% for some agent, the wiring is incomplete — repeat Step 2 for that agent.

## Step 6 — The LLM-received-the-rule branch (NEW 2026-07-21)

When Steps 1-5 confirm **the rule IS in the request_json** but the LLM still drifts, do NOT propose "add the rule to the prompt file" — that's the same anti-pattern at a different layer. Instead, run the **reclassification diagnostic**:

```sql
-- Find the buggy turn + the most recent request before it
SELECT ingested_at, agent, event_type, turn_index,
       SUBSTR(request_json, 1, 200) AS req_head,
       SUBSTR(response_text, 1, 300) AS resp_head
FROM `<project>.llm_forensics.llm_payloads`
WHERE campaign_id = '<CID>'
  AND turn_index BETWEEN <user_turn - 1> AND <user_turn + 1>
ORDER BY ingested_at ASC
```

Save the 350KB `request_json` to disk. Strip the BQ truncation suffix (`...[TRUNCATED request_json original_bytes=... sha256=...]`). Grep the saved request for **the mechanic's vocabulary AND the user's directive text**:

- `Mantle of the Radiant Slayer` — does it appear in the request? At what offsets?
- `Sanguine Sovereign` / `Chitinous Ruin` — do both appear?
- `Default all divine/slayer` — does the god-mode directive appear in this turn's request?
- `Transcendent Beauty confirmed` — does the prior god-mode turn's directive appear?

**If both the mechanic AND the user's directive appear in the request:** the LLM received the rule. The bug is **NOT** missing-delivery and the fix is **NOT** a hardcoded prompt rule. Reclassify per the `repro` skill bucket 7.7 ("Unknown / under-instrumented") OR as **architectural coupling / instruction drift**. The fix shape is policy + lint, not prompt text.

**If the rule is genuinely missing from the request** (e.g., the campaign module was pruned from the worktree by `git archive`, or the campaign description loader dropped the §5 block): that's a **true** delivery bug — fix the loader/schema, not the prompt layer.

### Why "add a prompt rule" is the wrong fix when the LLM received it

The user's pushback (2026-07-21, campaign `q04GfOEl4SWnEQrFUVST` turn 31):

> *"are you stupid? ... The fucking fix isn't to hardcode slayer form into the prompt it's to fucking investigate the BQ LLM raw requests like I asked and see if the llm even received the instruction"*

A "Default Aspect Classifier: When the player invokes their Slayer Form, default to Aspect I: The Sanguine Sovereign..." rule in `divine_leverage_system.md` would:

1. Be wrong root-cause — the LLM already received the mechanic via `story_history[0].text`.
2. Couple every future campaign to one specific mechanic — the same anti-pattern at the prompt layer as the original bug was at the RAG-context layer.

The correct fix is a **policy that forbids campaign-specific terms from entering `$PROJECT_ROOT/prompts/`**:

- `CLAUDE.md` — add a BANNED anti-pattern: Campaign-agnostic prompts (inserted adjacent to the existing "Class-specific hardcoding in code or prompts" rule).
- `$PROJECT_ROOT/prompts/CLAUDE.md` — new rule file with banned-name list (named characters from any `world_reference/campaign_module_*.md`, named mechanics, setting-specific names), allowed generics, PASS/FAIL examples, and `CAMPAIGN-SPECIFIC PROMPT EXCEPTION APPROVED` exception process.
- `scripts/check_prompt_agnosticism.py` — CI lint, exit 1 on banned terms outside `e.g.` blocks.
- `$PROJECT_ROOT/tests/test_prompt_agnosticism_8497.py` — 8 contract tests pinning the rule + lint + detection logic.

Verified on PR [#8498](https://github.com/$GITHUB_REPOSITORY/pull/8498), branch `docs/campaign-agnostic-prompts-clause`, HEAD `abef75a278` (+492/-0 across 4 files).

### The prompt-rule vs policy+lint decision matrix

| Symptom | The rule is in the request? | Fix shape |
|---|---|---|
| LLM ignores rule, rule NOT in request | No | **Prompt-delivery fix** — restore file to dispatcher (this skill's main path) |
| LLM ignores rule, rule IS in request (campaign-specific mechanic) | Yes | **Policy + lint fix** (PR #8498 shape) — add `$PROJECT_ROOT/prompts/CLAUDE.md` rule + lint; do NOT add a hardcoded prompt rule |
| LLM ignores rule, rule IS in request (generic 5e mechanic) | Yes | **Prompt-content fix** — add a compact worked example in the relevant prompt; use `llm-narration-format-clarifier` skill |
| LLM drifts on multi-aspect mechanic, rule IS in request, prior god-mode correction worked for one turn | Yes | **Schema/loader alignment** — fix the campaign description loader; ensure §5 mechanic is loaded before first character-mode turn (see `repro` skill §"Factor G") |

## Cross-references

- **`repro` skill** — owns the prompt-**content** bug class (PR #8443, PR #8446) and the directive-pairing-invariant family (#7162/#8012/#8080/#8103/#8065/#8275/#8283/#8390/#8490; Factor G added 2026-07-21). This skill owns prompt-**delivery** for cases where the file exists but the LLM never sees it. **CRITICAL:** when repro's Factor G reclassification lands here (LLM received the rule, drift is architectural), the fix routes back through this skill's Step 6 + PR #8498 shape — NOT through repro's prompt-fix-deliverable-shape.
- **`wa-campaign-content-analysis`** — diagnose prompt/agent issues from campaign content. Use BEFORE this skill if the user reports a per-campaign pattern (vs a fleet-wide pattern).
- **`wa-prod-data-query`** — analyze real-user activity. Different signal (turn_timestamps vs request_json).
- **`finish-the-job`** — drive the fix to a green PR with evidence. This skill tells you WHAT the bug is; finish-the-job drives the PR-merged end-state.
- **`llm-narration-format-clarifier`** — the **generic 5e** row of the Step 6 decision matrix (worked example in the prompt). Different from PR #8498 — narration drift is fixed by adding an example, not by a policy + lint.
- **`references/llm-received-the-rule-branch.md`** — companion file with the full Step 6 diagnostic recipe + the campaign-agnosticism policy fix shape + the worked example from PR #8498.

## Worked example — the 2026-07-20 living world audit

User reported (Slack C0AH3RY3DK6): "modify these antagonists living world events and stop all magical detection scrying and auditors it seems too out of nowhere modify prompts. Let's also only do one antagonistic event weekly max and otherwise make them neutral or beneficial events or new quests or companion story development. One antagonistic event weekly and one neutral or positive event daily and stop these back to back antagonistic events and read LLM raw requests from BQ to see if the proper living world instructions are even making it to the ll[m]"

Step 1: `grep -rn "Major Event Rarity Budget\|scrying\|auditor" $PROJECT_ROOT/prompts/living_world_instruction.md` — found all the rules in lines 268-291 (Lore-Appropriate Enemy Detection), lines 60-86 (Major Event Rarity Budget). File is 1,080 lines / 58.9K / has the rules.

Step 2: `grep -rn "living_world_instruction" $PROJECT_ROOT/ --include="*.py"` — found `agent_prompts.py:2576 build_living_world_instruction()`. Read the body (lines 2625-2635):

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

The function returns a 7-line stub. The on-disk file content never reaches the LLM. Marker confirmed: `agent_prompts.py:1469 del advances_time  # Unused after living_world_instruction moved to dynamic path`.

Step 3 (BQ forensic, `worldarchitecture-ai:llm_forensics.llm_payloads`):

| Agent | Calls | LW header | Major Event Budget | Trigger Whitelist | detection in resp |
|---|---:|---:|---:|---:|---:|
| gemini_provider.stream | 1084 | 8 | 8 | 8 | 776 |
| HeavyDialogAgent | 291 | **0** | **0** | **0** | 257 |
| GodModeAgent | 272 | **0** | **0** | **0** | 76 |
| DialogAgent | 170 | **0** | **0** | **0** | 153 |
| StoryModeAgent | 142 | **0** | **0** | **0** | 132 |
| LevelUpAgent | 78 | **0** | **0** | **0** | 58 |

LW header = "Living World Advancement Protocol". Only 34/2279 = 1.5% of real-user calls contain the LW header. Major Event Budget = 0% for non-stream agents.

Step 4 (extract block from real call):

```
LIVING WORLD POLICY**\\nEvaluate the full state and decide whether the living world should advance this turn.\\nYou MUST always emit `state_updates.world_events` as a dict. When advancing, include `background_events`. When quiet recovery or no meaningful off-screen motion is right, emit `world_events.background_events` as an empty array.\\n
```

7 lines. That's the stub. The 1,080-line file content is not in the request.

Step 5 (response-side cross-check):

| Agent | calls | complaint_in_resp | pct_lm_invented |
|---|---:|---:|---:|
| HeavyDialogAgent | 257 | 257 | **96.5%** |
| DialogAgent | 153 | 153 | **92.8%** |
| StoryModeAgent | 132 | 132 | **94.7%** |
| GodModeAgent | 76 | 76 | **89.5%** |
| LevelUpAgent | 58 | 58 | **100%** |

100% LLM-invented on LevelUpAgent; 90-96% on dialog/level/story agents. The LLM has zero prompt guardrails for these tropes and is inventing them 9-10 times out of 10.

**Diagnosis:** Pattern A (prompt moved to dynamic_instructions, body replaced by stub) + Pattern B (PROMPT_TYPE_LIVING_WORLD not wired into the 7 non-stream agents). The user's "stop scrying/auditors" rule exists on disk but is unreachable.

**Posted to Slack thread C0AH3RY3DK6/1784511909.604309 with three-option design call for the cache-stable placement (Option A/B/C) before touching code.**