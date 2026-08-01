# Mythic Tier / 3.5e Epic Levels Anti-pattern — Reference

> Companion file to `llm-narration-format-clarifier` (v1.1.0+). Documents the full diagnostic trail for the L21+ "LLM invents XP math from D&D 3.5e Epic Levels heritage" bug class, verified on $GITHUB_REPOSITORY:
> - Issue #8510 ("prompt: WorldAI Mythic Tier custom leveling framework...")
> - PR #8511 (open, DRAFT pending /es)
> - Campaign `wc2BBcSgOljiU3vJ160A` ("bg3 nocturne murder god")

## The bug class

A prompt cites an external system's heritage as a **literature pointer** without anchoring the specific math the LLM needs. The LLM, which has the cited external system's rules in its prior-knowledge weights, fills in the values itself — confidently, incorrectly, and reproducibly across every relevant campaign.

The shape is:
```markdown
... inspired by <EXTERNAL SYSTEM> <SUBSECTION>. No <specific value>
explicitly defined.
```

The user sees an LLM narration that **sounds plausible** and **cites the heritage authority**, but is **sourced from somewhere other than the prompt file the user is editing**.

## The exact wrong prompt

`$PROJECT_ROOT/prompts/divine/divine_leverage_system.md:42` (before PR #8511):

```markdown
## Level-Based Divine Rank System

Divine power scales automatically with character level, inspired by D&D 3.5e
Epic Levels and Deities & Demigods. No separate resource tracking — bonuses
are derived from level.
```

**The single sentence that broke the world for L21+ characters.** No formula. No per-level cost. Just "inspired by D&D 3.5e Epic Levels" — and the LLM invented 50,000 XP/level from its own training memory.

## The exact LLM improvisation

Campaign `wc2BBcSgOljiU3vJ160A` (UID `vnLp2G3m21PJL6kxcuAqmWSOtm73`, $USER@gmail.com). Latest entries at `/tmp/your-project.com/repro-exports/8508-bg3-nocturne-murder-god/`:

**User turn 1, line 9227:**
> "How does the exp progression work and why do you think I should be level 77?"

**User turn 2, line 9272:**
> "What's the standard mortal epic scaling is that from 3e? Our system prompts don't have that?"

**LLM response, line 9288:**
> "You are correct that the **50,000 XP per level** linear scaling is not explicitly written in the system prompts provided. Here is the technical explanation of where that logic originated and why it triggered the Level 77 projection... Our current `divine_leverage_system.md` defines two *other* formulas: Epic Mortal (21-25): Linear growth with deltas of ~25,000 to 31,050 XP. Divine (26+): Exponential growth (15% increase per level)."

The LLM self-confirmed three things:
1. **It invented the 50,000 XP/level value** from its prior-knowledge weights.
2. **It cited only the heritage source**, not the prompt file.
3. **The prompt did contain other formulas** that the LLM ignored in favor of the heritage pointer.

**Net effect:** the LLM projected L77 for a character whose actual level is L50, computed from `3,249,500 / 50,000 ≈ 65 + 12 = 77`. Same prompt, same agent, same campaign — three sibling campaigns reproduced the bug:

| Campaign | Level | Symptom |
|---|---|---|
| `q04GfOEl4SWnEQrFUVST` | L50 → L51 | god mode stuck on pending level-up |
| `wSm8Z8McTLJ8oQjqlTyJ` | L77 | god mode stuck on pending level-up |
| `wc2BBcSgOljiU3vJ160A` | L77 | LLM invented the L77 number and couldn't self-explain it |

This is a **fleet-wide prompt gap**, not a per-campaign issue. Per `convergent-bug-triage`, the trigger fires when 3+ campaigns reproduce the same LLM improvisation pattern. Here, the trigger fired on 3 of 3 L20+ campaigns reviewed.

## The user mid-thread steer

User pushback (verbatim, 2026-07-21):
> "i think we shouldnt even reference 3e epic levels, just have our own custom leveling system/framework after level 20"

The user's preference is the canonical answer:
1. **Drop the heritage citation entirely** — do not cite any external system.
2. **Build a custom framework** that the codebase owns.
3. The framework has formula, worked-examples table, and operational rules.

## The exact right prompt (PR #8511, post-fix)

`$PROJECT_ROOT/prompts/divine/divine_leverage_system.md` (after PR #8511):

```markdown
## Level-Based Divine Rank System

Divine power scales automatically with character level. WorldAI uses its
**own XP progression framework** for levels beyond the D&D 5e SRD table —
see the **WorldAI Mythic Tier XP Framework** section below for the
canonical math. Do NOT substitute external-system rules (3.5e Epic
Levels, Pathfinder Mythic, 5e epic house-rules, etc.) when narrating
L21+ advancement; only the values in this prompt apply, and only
`custom_campaign_state.progression_overrides` (god mode) may rewrite
them per-campaign.

### WorldAI Mythic Tier XP Framework (canonical, custom)

Beyond the D&D 5e SRD table (Level 20), all character advancement in
WorldAI follows **the WorldAI Mythic Tier progression** — a flat,
explicit per-level XP cost the LLM MUST use as-written. The framework
uses a single flat rate with **tier names** providing narrative flavor
(no tier-specific math branches; the per-level cost is the same across
all tiers):

| Tier | Level range | Cumulative XP | Per-level cost (flat) |
|------|-------------|--------------:|----------------------:|
| **Mythic Mortal** | 21–25 | 405,000 → 605,000 | **+50,000 XP** per level |
| **Ascendant** | 26–40 | 655,000 → 1,355,000 | **+50,000 XP** per level |
| **Divine Apex** | 41–100 | 1,405,000 → 4,355,000 | **+50,000 XP** per level |

**Cumulative threshold formula (single source of truth — use this everywhere):**

```
xp_needed_for_level(L) =
  SRD_table[L - 1]                                  if 1 ≤ L ≤ 20
  355_000 + (L − 20) × 50_000                       if L ≥ 21
```

Worked examples (canonical, pinned in the test contract):

| Level | Cumulative XP required |
|-------|------------------------:|
| 21    | 405,000  |
| 25    | 605,000  |
| 26    | 655,000  |
| 40    | 1,355,000 |
| 41    | 1,405,000 |
| 50    | 1,855,000 |
| 51    | 1,905,000 |
| 77    | 3,205,000 |
| 100   | 4,355,000 |

**Operational rules the LLM MUST follow when narrating L21+ advancement:**

1. **Never re-derive the per-level cost.** Do NOT compute it from any
   other RPG system's heritage (3.5e, Pathfinder, etc.). The numbers
   above are the ONLY correct values.
2. **Use the cumulative XP formula directly** when calculating current
   level from XP, or when narrating how much XP remains to the next
   level. Worked examples are pinned in the test contract.
3. **Per-campaign overrides** via `custom_campaign_state.progression_overrides`
   replace the formula on a per-campaign basis. The default IS the
   WorldAI Mythic Tier +50,000 XP/level flat rate shown here.
4. **Narrative consequence:** Worlds that grant L21+ levels mechanically
   treat those levels as **earned, not auto-awarded**. Awards are paced
   by `$PROJECT_ROOT/prompts/leveling_pace_contract.md` (target ~one level per
   extended arc of play).
5. **Cross-prompt anchor:** `$PROJECT_ROOT/prompts/leveling_pace_contract.md`
   defines a band-based XP-award fraction system for *awards*; the
   WorldAI Mythic Tier Framework here defines cumulative-threshold math
   for level *transitions*. They are independent; do not mix them up.
```

Five structural pieces:
1. **Self-description as owned** (`canonical, custom`).
2. **Single flat rate** with tier labels as **narrative flavor only** (no tier-specific math branches).
3. **Closed-form formula** (`xp_needed_for_level(L) = ...`) explicitly stated in the prompt.
4. **Worked-examples table** with explicit `× 50,000` arithmetic (so the LLM can verify its own computation rather than improvising).
5. **Operational rules** including the never-re-derive guard (banning 3.5e / Pathfinder / 5e house-rules as authority sources).

## The test contract (PR #8511, 27 cases)

`$PROJECT_ROOT/tests/test_mythic_tier_prompt_anchor.py`:

```python
class TestMythicTierPromptContract(unittest.TestCase):
    """Pin the prompt-layer rule so future edits don't silently drop it."""

    def test_worldai_mythic_tier_section_header_present(self):
        self.assertIn("WorldAI Mythic Tier XP Framework", self.content)

    def test_worldai_mythic_tier_is_canonical(self):
        needle = "single source of truth"
        self.assertIn(needle, self.content.lower())
        for marker in ("canonical, custom", "flat, explicit per-level XP cost"):
            self.assertIn(marker, self.content)

    def test_3e_3_5e_heritage_removed(self):
        # Absence assertion — catches half-fixes that keep the heritage
        # citation alongside the new framework.
        forbidden_phrases = (
            "inspired by D&D 3.5e",
            "Inspired by D&D 3.5e",
            "inspired by 3.5e Epic Levels",
            "inspired by D&D 3.5e Epic Levels and",
        )
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, self.content)

    def test_never_re_derive_rule_present(self):
        # At least one of these markers must be in the prompt.
        canonical_markers = (
            "Do NOT compute it from any other RPG",
            "any other RPG system's heritage",
        )
        for marker in canonical_markers:
            if marker in self.content:
                return
        self.fail("Prompt must include the never-re-derive rule.")


class TestMythicTierNumericalContract(unittest.TestCase):
    """Pin the worked-example XP values to the canonical formula."""

    def _expected_xp(self, level: int) -> int:
        if level <= 20:
            SRD = [0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000,
                   85000, 100000, 120000, 140000, 165000, 195000, 225000, 265000,
                   305000, 355000]
            return SRD[level - 1]
        return 355_000 + (level - 20) * 50_000

    def _check_row(self, level: int):
        expected = self._expected_xp(level)
        formatted = f"{expected:,}"
        bare = f"{expected}"
        candidates = (formatted, bare)
        for candidate in candidates:
            if candidate in self.content:
                return
        self.fail(
            f"Worked-example for level {level} (expected ~{formatted}) "
            f"not found verbatim in prompt."
        )

    def test_l21_405_000(self): self._check_row(21)
    def test_l25_605_000(self): self._check_row(25)
    def test_l26_655_000(self): self._check_row(26)
    def test_l40_1_355_000(self): self._check_row(40)
    def test_l41_1_405_000(self): self._check_row(41)
    def test_l50_1_855_000(self): self._check_row(50)
    def test_l51_1_905_000(self): self._check_row(51)
    def test_l77_3_205_000_canonical(self): self._check_row(77)
    def test_l100_4_355_000(self): self._check_row(100)
```

The test guards **both** the prompt content **and** the arithmetic consistency. A future prompt rewrite cannot regress without the test failing — and the absence-assertion on `3.5e` phrases catches half-fixes where the heritage citation survives alongside the new framework.

## Mirror in the companion prompt

`$PROJECT_ROOT/prompts/leveling_pace_contract.md` (after PR #8511) gains a "**Beyond Level 9 (10+ epic / mythic tier)**" section that anchors the L21 / L41 / L51 bands at 50,000 XP each:

```
- **Level 21 band = 405,000 − 355,000 = 50,000** (Mythic Mortal tier opens)
- **Level 41 band = 1,405,000 − 1,355,000 = 50,000** (Divine Apex tier)
- **Level 51 band = 1,905,000 − 1,855,000 = 50,000** (Greater Apex)
```

And a closing **Cross-Prompt Anchor — WorldAI Mythic Tier** section that points back to the framework, with the cross-anchor at the end of the file.

Cross-prompt anchors keep the cumulative-threshold layer (the formula in `divine_leverage_system.md`) and the award-rate layer (the band-fractions in `leveling_pace_contract.md`) synchronized. Without the mirror, the companion prompt can drift independently and re-introduce the bug class from a different angle.

## The PR shape that worked

PR #8511 was opened as **DRAFT** with:

- **`## Tenets` section** (required by `gh-actions/Design Doc Grep Gates` Gate 0).
- **Linkage to issue #8510** (the companion issue) and PR #8509 (the backend sibling, still open).
- **Self-incriminating numerical repro** — the worked-example table shows L77 = 3,205,000, exactly the level the user was stuck at.
- **`## Evidence` section** stating N/A + reason for prompt-only change, plus the BQ payload cross-check for on-wire delivery.

**Note on DRAFT status:** Per AGENTS.md `## Evidence for mvp_site Production Changes`, prompt changes that touch user-visible behavior require real gunicorn + real LLM evidence at /es time before merge. The string-presence test guards the prompt; BQ payload check guards the delivery; the `/es` evidence sweep guards the user-visible behavior. All three are required. PR #8511 is DRAFT until the `/es` sweep runs against `wc2BBcSgOljiU3vJ160A`.

## Reusable recipe — applying the same fix to a new prompt

When the next "LLM cites D&D 3.5e/Pathfinder/5e-house-rules and improvises the specific value" symptom appears, the recipe is:

1. **Find the heritage citation** (`grep -rn "inspired by <EXTERNAL>" $PROJECT_ROOT/prompts/`).
2. **Read the latest affected campaign** (`scripts/download_campaign.py --uid <uid> --campaign-id <cid> --output-dir /tmp/.../`) and find the LLM's improvisation product in the response_text.
3. **Replace the citation with a custom framework** using the 5-piece structure (self-description + flat rate + closed-form formula + worked-examples table with arithmetic + operational rules with never-re-derive guard).
4. **Mirror in any companion prompt** that touches the same domain.
5. **Test contract** with both string-presence assertions AND worked-example numerical pins AND absence-assertions on the heritage citation.

The shape generalizes — anywhere the prompt cites an external system's heritage as authority, the LLM will improvise the values. Replace the citation with an owned framework. The user's stated preference ("we shouldnt even reference 3e epic levels") establishes the canonical answer: **custom frameworks, not heritage citations**.

## Pitfalls specific to this sub-class

(Pitfalls E and F in the parent skill are the canonical ones for the owned-framework branch. Below are the workflow-level pitfalls surfaced during this session.)

**Pitfall G — Letting the cluster signal slip past without triage.** The external-system-heritage bug class is reproducible across every L20+ campaign. Per `convergent-bug-triage`, when 3+ campaigns reproduce the same LLM improvisation pattern, fix the prompt at the source — not the per-campaign dispatch. **Diagnostic trigger:** `session_search` on the campaign identifier returns 2+ sibling issues on the same bug class within 9 days. Test on this case: searches for `level 77` and `level 50 stuck` and `3e` all return hits that trace to the same `divine_leverage_system.md:42` failure.

**Pitfall H — Stripping the citation while keeping the math.** A common half-fix: drop "inspired by D&D 3.5e" but leave the existing `Linear`/`Exponential` formulas that the LLM already had. The LLM will fall back to those and the bug persists. The fix shape requires ALL FIVE pieces (self-description, flat rate, formula, worked-examples table with arithmetic, operational rules with never-re-derive guard).

**Pitfall I — Branching off `fix/unbounded-scaling-stale-clear-8508` instead of `origin/main`.** The first fix (PR #8509) was already opened when this prompt-layer fix landed. A naive branch from PR #8509's branch would carry its 6-file / +486-line commit history into the new PR — the "never push onto someone else's PR head" antipattern, verified multiple times in the SOUL.md / `.cursor/rules/pr-branch-from-main.mdc` enforcement. Branch from `origin/main` always; the per-PR commits stay narrow and reviewable.

## Cross-references

- `llm-narration-format-clarifier` — the parent skill (this file is its companion).
- `convergent-bug-triage` — for the cluster-signal detection that triggers the external-system-heritage sub-class.
- `llm-prompt-delivery-audit` Step 7 — the BQ payload cross-check on whether the new framework section actually reaches the LLM on the wire.
- PR #8511 — the canonical example of this fix shape on $GITHUB_REPOSITORY.
- Issue #8510 — the canonical example of the bug class with full reproduction.
