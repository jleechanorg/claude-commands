---
name: llm-narration-format-clarifier
description: |
  Fix LLM narration drift (LLM improvises formatting because a prompt line is
  too vague) by adding a worked example in the prompt, NOT by adding backend
  enforcement. Use when the user reports the LLM is dropping fields, abbreviating
  formats, or substituting its own template for an underspecified one.

  Triggers: "the LLM dropped X", "show both/all Y", "the narrative is missing Z",
  "prompt is too vague", "LLM invents the format", "add a worked example",
  "make the LLM consistently format X", "narration drift", "format hint needed",
  "the LLM cited D&D 3.5e/Pathfinder/<external system> when it shouldn't have",
  "we shouldn't reference <external system>", "build our own framework",
  "the LLM inherited math from <X> without us defining it".

  Does NOT apply to: LLM judgment errors that need richer prompt context (use
  llm-prompt-engineering / root-cause-first), backend state bugs (use root-cause-first),
  or LLM compliance with explicit instructions it already has (use systematic-debugging).
version: 1.1.0
allowed-tools:
  - read_file
  - search_files
  - patch
  - write_file
  - terminal
  - send_message
context: |
  Repos where the LLM is the formatter of player-facing narrative text:
  your-project.com, $GITHUB_REPOSITORY, any RPG / game / story engine
  that surfaces dice rolls / currency / status lines to the user.
---

# llm-narration-format-clarifier

## The class of bug

The prompt has a one-line instruction like `**Advantage/Disadvantage:** Show both dice, indicate which was used.` The LLM reads it, decides "show both dice" is a soft hint, and narrates the roll with only the kept die. The user complains: "the LLM is dropping the second die."

The same shape recurs for currency, status lines, time deltas, name rendering, etc. The temptation is to add a backend formatter / regex / post-processor that scrubs the LLM output. **That is the wrong move** for two reasons:

1. **It violates root-cause-first.** The LLM is the canonical author of the narrative. A backend post-processor silently rewrites it; the user sees "corrected" prose with no signal that something was overridden.
2. **It drifts.** The post-processor handles the specific case the user complained about; the next case is a new post-processor; six months later the codebase has a forest of regex scrubbers, each handling a slightly different pattern, none of them tested together.

The correct fix is a **worked example** in the prompt — the same pattern the LLM already imitates successfully for the canonical case. Worked examples are what the LLM was trained on; they are the highest-fidelity format hint you can give it.

## The 4-step recipe (verified 2026-06-13, dice adv/disadv PR #7539)

### Step 1 — Confirm the LLM controls the formatting, not the server

Grep the prompt file for the format-relevant rule. Grep the server code for any
post-processing that scrubs the LLM output for this format. If the server does
post-process, you have a different bug (and a different skill).

For dice in your-project.com:
- Prompt: `$PROJECT_ROOT/prompts/dice_system_instruction.md:44` — single ambiguous line.
- Server: `$PROJECT_ROOT/dice.py` returns the raw server-rolled values via `tool_requests`; no post-processor scrubs the narrative.
- **Verdict: LLM is the formatter. Prompt is the right surface.**

### Step 2 — Find an existing worked example in the same prompt to mirror

The LLM reliably imitates the existing normal-roll format on line 42:
```
`Action: Stealth Check | Roll: 1d20+5 = [12]+5 = 17 | Result: Success`
```
The adv/disadv lines below it lacked a worked example — that's the gap. Find
the canonical line in your own prompt and mirror its structure. **Do not invent
a new format style**; the LLM imitates the dominant pattern, so the worked
example should be byte-similar to the line above it.

### Step 3 — Replace the vague line with the worked example(s)

Before:
```
**Advantage/Disadvantage:** Show both dice, indicate which was used.
```

After (one worked example per branch, plus a "never abbreviate" guard):
```
**Advantage/Disadvantage:** The server rolls 2d20 (one kept, one dropped). Display BOTH raw d20 values, label which die was kept, then apply the modifier once. Format examples:

- `Action: Stealth Check (Advantage) | Roll: 2d20+5 keep high = [8, 17]+5 = 22 | Kept: 17 | Result: Success`
- `Action: Perception Check (Disadvantage) | Roll: 2d20+3 keep low = [4, 11]+3 = 14 | Kept: 4 | Result: Fail`

The "kept" die is the one that determined the total; always show the dropped one too for transparency. Never abbreviate to a single d20.
```

Three structural pieces, all required:
1. The instruction (what to do).
2. A worked example per branch (concrete template).
3. A negative guard ("never abbreviate to X") — the LLM will paraphrase on edge cases; the durable rule is the negative guard.

### Step 4 — Add a string-presence unit test

The test guards the worked example so a future prompt revision cannot silently
regress to the vague line. Use string-presence assertions on the prompt file:

```python
PROMPT_PATH = "$PROJECT_ROOT/prompts/dice_system_instruction.md"

def _load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as fh:
        return fh.read()


class TestDicePromptAdvantageDisadvantage(unittest.TestCase):
    def test_prompt_has_advantage_keep_high_example(self):
        prompt = _load_prompt()
        self.assertIn("2d20+5 keep high", prompt)
        self.assertIn("[8, 17]", prompt)
        self.assertIn("Kept: 17", prompt)
        self.assertIn("Advantage", prompt)

    def test_prompt_has_disadvantage_keep_low_example(self):
        prompt = _load_prompt()
        self.assertIn("2d20+3 keep low", prompt)
        self.assertIn("[4, 11]", prompt)
        self.assertIn("Kept: 4", prompt)
        self.assertIn("Disadvantage", prompt)

    def test_prompt_drops_old_vague_line(self):
        prompt = _load_prompt()
        self.assertNotIn("Show both dice, indicate which was used.", prompt)

    def test_prompt_explicitly_forbids_single_d20_abbreviation(self):
        prompt = _load_prompt()
        self.assertIn("Never abbreviate to a single d20", prompt)
```

Three assertions per branch + one for the dropped-old-line + one for the
negative guard. The test file should live in `$PROJECT_ROOT/tests/` per AGENTS.md
"Test File Placement" rule (for your-project.com; adapt to your repo's test
dir convention).

## Sub-class: External-system heritage citation (verified 2026-07-21)

This is a **second class** of LLM improvisation bug, distinct from format drift
but sharing the same fix shape: the prompt cites an external system's heritage
("inspired by D&D 3.5e Epic Levels", "per Pathfinder Mythic", "as in standard
5e house-rules") without anchoring the specific math, so the LLM fills in the
specific values from its prior-knowledge weights. The user sees improvisation;
the LLM sees a "literature pointer."

### Why this is a different sub-class

Format-drift (the original class) is the LLM *making up a presentation*. The
external-system-heritage sub-class is the LLM *making up values from a citation*.

**Example (verified 2026-07-21, $GITHUB_REPOSITORY issue #8510,
campaign `wc2BBcSgOljiU3vJ160A` "bg3 nocturne murder god"):**

**Wrong prompt** (the bug):
```markdown
Divine power scales automatically with character level, inspired by D&D 3.5e
Epic Levels and Deities & Demigods. No separate resource tracking — bonuses
are derived from level.
```

**What the LLM did:** with no per-level cost anchored, the LLM invented a
50,000 XP/level flat rate from its 3.5e heritage memory, computed
`3,249,500 / 50,000 ≈ 65` levels beyond L20 → projected L77 for a character
that should be L50. When the user asked the LLM to explain, it self-confirmed:
*"You are correct that the 50,000 XP per level linear scaling is not
explicitly written in the system prompts provided."*

User mid-thread steer: *"we shouldnt even reference 3e epic levels, just have
our own custom leveling system/framework after level 20"*. The citation was
the bug, the heritage was the bug, the improvisation was downstream.

### Cluster trigger (when this is fleet-wide, not per-scene)

The external-system-heritage bug class is **fleet-wide by construction** —
every L21+ campaign the LLM has ever narrated will hit it, because the vague
heritage citation is in `divine_leverage_system.md:42` (or wherever the cite
lives). Per `convergent-bug-triage`, treat 3+ sibling reproductions across
campaigns as a fleet-wide prompt gap, not a per-campaign invention bug.

Diagnostic heuristic:
1. `grep -rn "inspired by <external system>\|per Pathfinder\|as in <system>" $PROJECT_ROOT/prompts/`
2. For each hit, look at the surrounding context — does the prompt anchor a
   specific value, or just cite the heritage?
3. If cite-without-anchor, the LLM will improvise.

### The recipe — owning the framework

When a prompt cites an external-system heritage without anchored math, the fix
is to **own the framework**, not to add a more specific citation. The fix shape
mirrors the 4-step recipe above, but the worked example becomes a **canonical
formula + authoritative table**:

1. **Replace the citation with a self-description.** Drop "inspired by D&D
   3.5e Epic Levels" entirely. Replace with "WorldAI uses its own progression
   framework for levels beyond the SRD table — see the *<WorldAI Own Framework>*
   section below for the canonical math." The single-source-of-truth marker
   `### <Framework Name> (canonical, custom)` self-identifies the math as
   owned by the codebase, not a heritage pointer.

2. **Anchor the formula.** Write a single `xp_needed_for_level(L)` (or equivalent)
   formula with a closed-form expression. Worked example:
   ```
   xp_needed_for_level(L) =
     SRD_table[L - 1]                       if 1 ≤ L ≤ 20
     355_000 + (L − 20) × 50_000            if L ≥ 21
   ```
   The formula is the canonical source. The tier labels (`Mythic Mortal`,
   `Ascendant`, `Divine Apex`) are **narrative flavor only** — math is
   identical across all tiers, even when the table has multiple bands.

3. **Provide a worked-examples table with explicit `× 50,000` math.** Not just
   "L77 = 3,205,000" — show the arithmetic step `355,000 + 57 × 50,000 =
   3,205,000`. This makes the formula visible in the prompt itself, so the LLM
   can verify its own computation rather than improvising.

4. **Add operational rules** with the never-re-derive guard:
   ```
   **Operational rules the LLM MUST follow when narrating L21+ advancement:**

   1. Never re-derive the per-level cost. Do NOT compute it from any other
      RPG system's heritage (3.5e, Pathfinder, etc.). The numbers above are
      the ONLY correct values.
   2. Use the cumulative XP formula directly when calculating current level
      from XP, or when narrating how much XP remains to the next level.
   3. Per-campaign overrides via custom_campaign_state.progression_overrides
      replace the formula on a per-campaign basis.
   ```

5. **Mirror in any companion prompt** that touches the same domain. If
   `divine_leverage_system.md` has a pacing-fractions system, mirror the
   band anchors in that companion (`leveling_pace_contract.md` in this case):
   `**Level 21 band = 405,000 − 355,000 = 50,000** (Mythic Mortal tier opens)`.
   Keeps the cumulative-threshold and award-rate layers synchronized.

6. **Add a test contract with the never-re-derive guard.** The test asserts:
   - The framework section header is present (anchored by string match).
   - The forbidden heritage citation (`inspired by D&D 3.5e`, `Inspired by D&D
     3.5e`, etc.) is NOT present anywhere in the prompt.
   - At least one of `Do NOT compute it from any other RPG` / `any other RPG
     system's heritage` / similar never-re-derive markers is present.
   - Worked-example numerical values are pinned (e.g. L21=405,000; L77=3,205,000)
     so any drift becomes a CI failure.

7. **Mirror in BQ check:** if there is an existing BQ payload log table
   (`llm_forensics.llm_payloads` or equivalent), verify after merge that the
   new framework section reaches the LLM for every agent that calls the
   dispatcher:
   ```sql
   SELECT
     agent,
     COUNTIF(REGEXP_CONTAINS(CAST(request_json AS STRING), r'<Framework Name>')) AS has_framework,
     COUNTIF(REGEXP_CONTAINS(CAST(request_json AS STRING), r'<key formula anchor>')) AS has_formula,
     COUNT(*) AS calls
   FROM `<project>.llm_forensics.llm_payloads`
   WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     AND is_test = false
   GROUP BY agent
   ```

### Pitfall for the owned-framework branch

**Pitfall E — Hiding the math in the formula.** If your worked-examples table
says L77 = 3,205,000 but never mentions "× 50,000" or "+ (L-20) × 50_000"
in the prompt itself, the LLM cannot verify its computation against the
canonical formula. Either show the arithmetic in the worked-examples column
(`L77: 355,000 + 57 × 50,000 = 3,205,000`) or restate the formula immediately
above the table.

Verified failure case (2026-07-21, PR #8511 first draft): the table said
`L77 = 3,705,000` while the formula gave `3,205,000` — a `355,000` vs
`705,000` ancestor-of-the-formula difference. A contract test
(`test_l77_3_205_000_canonical`) would have caught this pre-merge if the
formula had been stated above the table; as written, the test had to be
added separately and the prompt patched mid-review. **Mitigation:** always
write the formula → worked-examples table → test contract in that order;
**the test contract references the formula, never the table alone.**

**Pitfall F — Pinning arithmetic in the test, not the prompt.** A test like
`assertIn("3,205,000", prompt)` allows a prompt rewrite to say "L77 = 3,205,000"
with no formula and the test still passes. Stronger contract: assert the
formula string is present, plus the worked example, plus a marker that the
framework section is the single source of truth. All three checks together.

## Evidence policy (what counts as proof the worked example works)

| Change scope | Evidence required | Why |
|---|---|---|
| `$PROJECT_ROOT/prompts/**` only, no LLM call site change, no schema change, no server change | **String-presence unit test is sufficient** | The prompt is a static string; the test guards that string. A real-LLM replay does not test the prompt — it tests the LLM, which is non-deterministic and not the unit under test. |
| Prompt change that coincides with a schema/tool/agent change | Real LLM full HTTP raw response evidence (`## Real LLM Evidence` section) | The change is no longer prompt-only; the schema is also a unit under test. |
| Prompt change that claims to fix a specific user-visible failure | Replay the original failure scenario (existing test, real LLM, real campaign) | The test must be RED before the prompt fix, GREEN after. The "Was the bug actually fixed?" question is the test's question. |

For the dice adv/disadv case (PR #7539), the change is prompt-only — string-presence test is the right evidence shape. The PR's `## Real LLM Evidence` is N/A + explains why, not skipped.

For the external-system-heritage case (PR #8511), the change is also prompt-only — same string-presence evidence shape applies, but **plus** the BQ payload check from Step 7 above to confirm the framework reaches the LLM. The test asserts the prompt content; BQ asserts the on-wire delivery.

## Pitfalls

### Pitfall 1 — Stopping at "PR open" instead of driving to green

The prompt-only change takes 3 minutes to land. Watching the checks turn green
takes 15-30 minutes. The temptation is to declare done at PR-open. **Don't.**
Re-trigger failed checks, fix anything fixable in the PR, post the in-thread
update with the final state. PR-open is the *minimum* unit of done-ness; green
CI is the *complete* unit.

If a CI failure is **infra-class** (runner stale refs, missing env var, OOM),
ship the infra fix in the same turn — the work for the user is "PR is green",
not "PR exists with a known transient failure that I'll get to later." Verified
2026-06-13: a self-hosted runner had 6 stale broken local refs (deleted
branches); the same runner failed every job in 6 seconds with
`fatal: bad object refs/remotes/origin/<branch>`. Pruning the local refs
restored green. The PR diff was 0; the CI state went red→green.

### Pitfall 2 — Marking the change N/A on `## Real LLM Evidence` for a prompt-only change that touches user-visible behavior

The your-project.com PR template hard-requires `## Real LLM Evidence` whenever
`$PROJECT_ROOT/prompts/**` changed. For a pure prompt-text change with no schema /
agent / call-site change, N/A is correct — but the explanation must say *why*
N/A is correct ("the prompt is a static string; the test guards that string;
a real-LLM replay tests the LLM, not the unit under test"). N/A + reason
passes the gate; bare N/A does not.

For the external-system-heritage branch, N/A is also correct in shape — the
prompt is a static string and the BQ payload check (Step 7 in the recipe)
covers the on-wire delivery question. State both in `## Real LLM Evidence`:
"N/A on real LLM replay (prompt is the unit under test); BQ payload check
covers delivery; Postman `/api/campaigns/<CID>/interaction/stream` evidence
sweep is required at /es time per AGENTS.md `## Evidence for mvp_site Production
Changes`."

### Pitfall 3 — Skipping the "test the test" step

The unit test guards the prompt. Run the test green in the worktree *before*
pushing the branch. A test that always passes is worse than no test — it
silences regressions.

```bash
cd <worktree>
$HOME/your-project.com/venv/bin/python3 -m unittest \
  mvp_site.tests.test_dice_prompt_advantage_disadvantage -v
# Expect: Ran 5 tests in 0.000s / OK
```

For the Mythic Tier case, the test guards both the **prompt content** (string
presence) AND the **arithmetic consistency** (worked-example values match the
formula). Run both before pushing.

### Pitfall 4 — Inventing a new format style instead of mirroring the existing one

The LLM imitates the dominant pattern. If your worked example uses
`[d20_high, d20_low]+mod` but the surrounding prompt uses
`1d20+5 = [12]+5 = 17`, the LLM will produce inconsistent output. **Mirror the
existing line byte-similar.** Same delimiters, same modifier-once math, same
"Result: X" suffix.

### Pitfall 5 — Keeping the heritage citation AND adding the framework

A common half-fix: add a canonical section but leave "inspired by 3.5e" in
place for historical flavor. The LLM reads both — the framework AND the
heritage — and improvises by averaging, by anchoring on whichever reads
first, or by silently preferring the heritage. Strip the heritage
citation entirely; the framework's self-description
("canonical, custom") is the only anchor the LLM should see.

Verified failure case (2026-07-21, PR #8511 first draft): the test file's
`test_3e_3_5e_heritage_removed` correctly asserted the absence of
`inspired by D&D 3.5e` (and 3 similar phrases) and would have caught a
half-fix where the citation survived. **Mitigation:** the contract test
MUST include an absence-assertion for the heritage. Without it, a
half-fix slips through review.

### Pitfall 6 — Editing the user's prompt without first reading their campaign state

The external-system-heritage bug class is reproducible on the campaign that
prompted it (`wc2BBcSgOljiU3vJ160A` for the Mythic Tier case). Reading the
*latest* entries from that campaign via `scripts/download_campaign.py`
before editing the prompt surfaces:

- What the LLM said (the improvisation product, useful as a "negative example").
- What the user pushed back with ("we shouldnt even reference 3e epic levels").
- The campaign's specific level/XP state (to write a worked-examples table
  that matches the user's actual data, not fabricated levels).

For $GITHUB_REPOSITORY specifically, the canonical recipe is
`scripts/download_campaign.py --uid <uid> --campaign-id <cid> --output-dir /tmp/.../`.
Skip the browser path entirely — Firebase auth blocks it.

## Cross-references

- `worldarchitect` skill — 7-green gate, evidence rules, design-decision heading requirement.
- `root-cause-first` skill — when the LLM is the wrong layer to fix (rare for narration drift; common for state bugs).
- `always-pr-never-local-edit` skill — worktree + GH issue + branch + PR + push, every time.
- `drive-pr-to-green` skill — full bring-to-green workflow for the next session.
- `convergent-bug-triage` skill — fleet-wide vs per-scene triage when a single campaign hits 3+ sibling bugs; triggers when the same LLM improvisation pattern crosses 3+ campaigns (this is the canonical signal for the external-system-heritage sub-class).
- `llm-prompt-delivery-audit` — for the cross-check on whether the new framework section actually reaches the LLM on the wire (Step 7 in the recipe). When the prompt-edit PR claims "fixed," BQ payload table is the verification.
- `references/mythic-tier-3e-antipattern.md` — full diagnostic trail (issue #8510) showing the wrong prompt, the LLM's improvisation, the worked-examples table, and the test contract.
