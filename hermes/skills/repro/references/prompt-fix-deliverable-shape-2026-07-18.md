# Prompt-fix deliverable shape for planning_block canonical-state-anchor violations

**Verified 2026-07-18 on $GITHUB_REPOSITORY PR [#8446](https://github.com/$GITHUB_REPOSITORY/pull/8446).** Shipped the actual prompt-side fix for the 5-anchor canonical-state-anchor taxonomy (the 5× sibling cluster on campaign `D3iZvnGiBl9wyveQBFj9`: [#8438](https://github.com/$GITHUB_REPOSITORY/issues/8438), [#8440](https://github.com/$GITHUB_REPOSITORY/issues/8440), [#8442](https://github.com/$GITHUB_REPOSITORY/issues/8442), [#8444](https://github.com/$GITHUB_REPOSITORY/issues/8444), plus the pre-existing structural-issue bead).

This is the **durable-fix recipe** for the planning_block canonical-state-anchor sub-class. Load it before writing the prompt fix PR for any sibling in this class. The 5-anchor taxonomy and the §"Future Event & Milestone Consistency" precedent live in `references/repro-planning-block-and-campaign-cluster-2026-07-18.md`; this reference is the **implementation recipe** that picks up after the bug-class diagnosis.

## Why a prompt-side fix, not backend enforcement

Per `AGENTS.md` §"Root-cause-first prompt discipline":

> *"Fix missing or contradictory prompt/schema/agent instructions before adding server-side protection."*

The canonical-state-anchor violation is a **missing rule**, not a contradictory one. The LLM is reasoning from narrative memory without re-checking canonical state — adding a backend Layer C guard before the prompt is corrected would be guarding against a behavior the prompt doesn't even forbid. Ship the prompt fix first; revisit backend enforcement only if the prompt correction proves insufficient (and only with explicit human approval per AGENTS.md "For level-up work, do not add backend enforcement unless the human explicitly approves enforcement in-thread").

## The deliverable shape (4 components)

A complete prompt-fix PR for the canonical-state-anchor class has **exactly 4 components** — no more, no fewer:

### Component 1 — `$PROJECT_ROOT/prompts/planning_protocol.md` — new §"Canonical-State Anchor" section

Insert a new top-level section AFTER the existing §"Future Event & Milestone Consistency" section (so the existing rule stays intact and the new rule is purely additive — minimizes diff and protects the implicit-cache-hot zone near the top of the file). Shape:

```markdown
## Canonical-State Anchor (NPC Co-Presence, Location, Directives, Reachability)

**Scope**: applies to every emit of `planning_block` (all agents, all modes). Extends the §"Future Event & Milestone Consistency" section above — same canonical-state-anchor principle, additional anchor types. Mirrored by `narrative_system_instruction.md` §"Narrative Consistency Anchors" for narrative-prose side.

Before emitting `planning_block.choices[N].description`, `text`, `pros`, `cons`, `id`, or `thinking`, validate every spatial/actor premise against canonical state. **DROP or rewrite any choice whose premise contradicts canonical state.**

### 4. NPC Co-Presence (No "Depart to Find Someone Already Present")
   For every NPC explicitly named in a choice's `text`, `description`, or `pros`/`cons`:
   - Locate that NPC in `entity_tracking.active_entities[]` (ACTIVE tier) OR `npc_data.<name>` (canonical record).
   - Read their canonical `location` snapshot (from `entity_tracking.active_entities[].status.location` for ACTIVE tier) and any `co_presence` flag (if present).
   - Compare against the player's canonical location from `player_character_data.world_data.location` and `entity_tracking.present_entities[]`.
   - If the choice's premise is *"depart to rejoin/visit/give-to/find them at location X"* AND the NPC is already co-present at the player's current location (or will be — see §6 reachability), DROP that choice or rewrite to a premise that observes co-presence.
   - Conversely, if the choice is *"stay and continue working with them"* AND the NPC is NOT actually co-present, DROP or rewrite.

   **Why**: prevents the canonical-state-anchor violation pattern documented across [sibling issue links].

### 5. God-Mode Directive Compliance (No Choosing Against an Active Rule)
   Before emitting any choice, scan `custom_campaign_state.god_mode_directives[]` for active directives...

### 6. NPC Reachability (No "Travel to Where They Aren't")
   ...

### 7. NPC Status Alignment (No "Trade with a Dead Enemy" / "Negotiate with a Captured Foe")
   ...

### Quick Self-Audit Before Emit (Mandatory)
   1. For every NPC named: is their canonical `location` consistent?
   2. For every directive: is the choice compliant?
   3. For every destination: is it reachable in this turn's time budget?
   4. For every NPC named: is their `status` consistent with being treated as present or interactive?
   5. For every future event mentioned: is `revealed_at` set?
   6. For every milestone / inventory item / reward: is the canonical state still showing it as available?

   **Reference sibling issue cluster**: [all 5 sibling issue links]. **This rule prevents recurrence across all campaigns**, not just the source.
```

**Key design choices:**

1. **Numbered sub-rules §4-§7**: continue the §1, §2, §3 numbering from the existing §"Future Event & Milestone Consistency" section so the Quick Self-Audit's "1-6" list maps to existing rules 1-3 + new rules 4-7.
2. **"Why" lines**: every sub-rule cites the sibling cluster. This prevents future maintainers from deleting the rule thinking "we don't have Aegon anymore" — the rule is general, not campaign-specific.
3. **"Drop or rewrite" verb**: matches the existing §"Future Event & Milestone Consistency" verb ("DROP or rewrite") so the LLM recognizes a familiar instruction pattern.
4. **Quick Self-Audit at the end**: the LLM's pre-emit checklist. Mandatory. Reinforces the rules.
5. **Reference sibling cluster**: hard-links the 5 sibling issues. The link list is the durable evidence that this isn't a one-off.

### Component 2 — `$PROJECT_ROOT/prompts/narrative_system_instruction.md` — mirror §"Narrative Consistency Anchors" section

The narrative-prose side needs a parallel rule. Insert AFTER the existing §5 "🚫 NO LEAKING UNREVEALED FUTURE EVENTS" rule (numbered §6, §7, §8 to continue). Same shape as Component 1 but adapted to prose emit:

```markdown
## Narrative Consistency Anchors (Canonical-State Rules)

**Scope**: applies to every narrative emit (all agents, all modes). Mirrors `planning_protocol.md` §"Canonical-State Anchor" for the planning_block side.

Before writing `narrative` prose or NPC dialogue, validate every spatial/actor premise against canonical state.

### 6. NPC Co-Presence
   ...

### 7. God-Mode Directive Compliance
   ...

### 8. NPC Status Alignment
   ...
```

**Why mirror, not just add to one side**: the same canonical-state-anchor violation manifests differently in prose ("You travel to find Aegon at Mander mouth") vs in planning_block ("Depart ... to rejoin Aegon's main vanguard at Mander mouth"). Both need the rule. Without both, the LLM could satisfy the planning_block rule and emit narrative prose that violates it (or vice versa).

### Component 3 — `$PROJECT_ROOT/tests/test_<descriptive>_<issue-number>.py` — new test file pinning the prompt contract

Create a parallel test file that pins the new prompt sections. The pattern follows `test_planning_block_future_leak_7763.py` (the existing sibling-class test). Shape:

```python
"""Unit tests for the canonical-state-anchor rule class (sibling issue cluster).

Pin the prompt contract from `$PROJECT_ROOT/prompts/planning_protocol.md`
§"Canonical-State Anchor (NPC Co-Presence, Location, Directives, Reachability)"
and the matching narrative side in `$PROJECT_ROOT/prompts/narrative_system_instruction.md`
§"Narrative Consistency Anchors".

Sibling cluster: [list all 5 sibling issues].

These tests run as fast unit tests (no LLM, no network). They pin the prompt
contract — i.e. the rules the LLM is supposed to follow at emit time.

Per AGENTS.md "Root-cause-first prompt discipline", backend enforcement
(server-side Layer C guard) requires explicit human approval before being added.
For now this is the prompt-side rule, which the LLM must follow at emit time.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_PLANNING_PROTOCOL = _PROMPTS_DIR / "planning_protocol.md"
_NARRATIVE_INSTRUCTION = _PROMPTS_DIR / "narrative_system_instruction.md"


def _load(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


class PlanningProtocolCanonicalStateAnchor(unittest.TestCase):
    """Pin the planning_protocol.md canonical-state-anchor rule contract."""

    def setUp(self) -> None:
        self.text = _load("planning_protocol.md")

    def test_canonical_state_anchor_section_present(self) -> None:
        self.assertIn("Canonical-State Anchor", self.text, "...")

    def test_npc_co_presence_rule_present(self) -> None:
        self.assertIn("NPC Co-Presence", self.text)
        self.assertIn("entity_tracking.active_entities", self.text)
        self.assertIn("present_entities", self.text)
        self.assertIn("player_character_data.world_data.location", self.text)

    # ... one test per sub-rule ...

    def test_quick_self_audit_present(self) -> None:
        self.assertIn("Quick Self-Audit", self.text)
        self.assertIn("Before returning the response", self.text)

    def test_sibling_issue_links_present(self) -> None:
        for issue in ("#8438", "#8440", "#8442", "#8444"):
            self.assertIn(issue, self.text, "...")

    def test_general_fix_not_campaign_specific(self) -> None:
        # The new section must be generic-language + no hard-coded lore tokens.
        anchor_section = self.text.split("## Canonical-State Anchor")[1]
        section_lower = anchor_section.lower()
        for marker in ("for every npc", "every directive", "every destination"):
            self.assertIn(marker, section_lower, "...")
        self.assertIn("all campaigns", section_lower)
        # Confirm no campaign-specific hard-coding to lore tokens.
        for lore_token in ("Aegon", "Highgarden", "Sariel"):
            self.assertNotIn(lore_token, anchor_section,
                f"Canonical-State Anchor section must not hard-code lore token "
                f"{lore_token!r} — the fix must be general, not campaign-specific.")


class NarrativeInstructionCanonicalStateAnchor(unittest.TestCase):
    """Pin the narrative_system_instruction.md canonical-state-anchor rule contract."""
    # ... parallel tests for §6, §7, §8 ...


class CrossReference(unittest.TestCase):
    """Both files must reference the sibling cluster and each other."""

    def test_planning_protocol_references_narrative_section(self) -> None:
        self.assertIn("narrative_system_instruction.md", _load("planning_protocol.md"))

    def test_narrative_instruction_references_planning_section(self) -> None:
        self.assertIn("planning_protocol.md", _load("narrative_system_instruction.md"))


class FutureEventRuleStillPresent(unittest.TestCase):
    """Regression check: existing §Future Event & Milestone Consistency rule
    must NOT be broken by the new section's insertion."""

    def test_future_event_rule_still_present_in_planning_protocol(self) -> None:
        text = _load("planning_protocol.md")
        self.assertIn("Future Event & Milestone Consistency", text)
        self.assertIn("Unrevealed Future Events", text)
        self.assertIn("revealed_at", text)
        self.assertIn("Completed Milestones", text)


if __name__ == "__main__":
    unittest.main()
```

**Key test design choices** (each is a pitfall I hit and corrected while writing the test):

1. **`test_general_fix_not_campaign_specific` MUST scope to the new section**: use `text.split("## Canonical-State Anchor")[1]` to isolate just the new section, then check both:
   - **Generic-language markers present** (`for every npc`, `every directive`, `every destination`, `all campaigns`) — case-fold the substring before asserting
   - **No lore-token hard-coding**: `assertNotIn(lore_token, anchor_section)` for each major token from the source campaign. Without the section-scope, the file-wide assertion would false-positive on legitimate lore references elsewhere in the prompt.

2. **`assertIn("NPC Co-Presence", self.text)` is case-sensitive** — the prompt uses `NPC Co-Presence` (capital N). Don't case-fold the assertion; case-fold the input only. If the prompt uses `npc co-presence` (lowercase), update the test to match.

3. **Cross-reference tests** ensure the two prompt files reference each other (so future maintainers don't delete one side without the other).

4. **Regression test for the existing rule** (`test_future_event_rule_still_present_in_planning_protocol`) — protects against accidental removal of the §"Future Event & Milestone Consistency" section during the patch.

5. **No LLM in tests** — these are pure prompt-file grep tests. Run with `TESTING_AUTH_BYPASS=true ./venv/bin/python -m pytest <test_file> -v` from the project root (the worktree has no `./venv/` — see pitfall below).

### Component 4 — PR body documenting coverage + cluster signal

The PR body MUST include:

1. **Sub-class coverage map**: a table mapping each sibling issue to its anchor sub-class and which new sub-rule fixes it. Proves the fix is general, not campaign-specific.
2. **Sibling cluster signal**: the 5-sibling count + the campaign ID + the bead ID (if any) for the structural-issue follow-up.
3. **Token-cost impact**: line counts added to each prompt file. Per AGENTS.md "Prompt Duplication & Compression", the new section should sit at the END of each file, outside the implicit-cache-hot zone at the top.
4. **Why prompt-side, not backend**: cite AGENTS.md "Root-cause-first prompt discipline" verbatim.
5. **Behavior change scope**: explicitly state "prompt-side only, no backend / server-side enforcement added".
6. **Verification**: list every test that ran (new + regression). Include the actual green counts (e.g. "15 tests, all green").

## Pitfalls I hit while writing this PR (so future fixes avoid them)

### Pitfall 1 — Edits landed in the wrong checkout (silent failure)

The worktree at `$HOME/projects/wt-aegon-rejoin-repro/` had no `./venv/`. When I ran `pytest` to verify the prompt edits, the venv resolved to a different directory — and the `patch` tool wrote to the **main checkout** `$HOME/projects/your-project.com/` (which was on a different branch, `docs/bq-cost-spike-2026-07-08-findings`), not to the worktree. There was NO error message — `patch` succeeded, `pytest` ran, the tests passed. The trap: the edits looked correct in the test run, but they were on the wrong branch.

**Detection heuristic:** after `patch` succeeds on a file in a worktree, run `git -C <worktree> status --short` AND `git -C <main-checkout> status --short`. If the main checkout shows the file as modified, the patch landed in the wrong place.

**Recipe for the next session:**

```bash
# 1. Verify worktree has venv (or use main checkout's venv explicitly)
ls -la $HOME/projects/wt-<topic>/venv 2>&1 | head -2
# If no venv: run pytest with main-checkout's venv, but commit/push in the worktree.
# Crucially: ALWAYS run git status on BOTH directories to confirm edits land in the right branch.

# 2. After every patch, run BOTH status commands:
cd $HOME/projects/wt-<topic>
git status --short
git rev-parse --abbrev-ref HEAD   # confirm branch is what you think

cd $HOME/projects/<main>
git status --short                # MUST be empty after a worktree-local edit
```

**Verified case 2026-07-18, $GITHUB_REPOSITORY PR #8446:** the prompt edits + test file landed in the main checkout first (no error). I caught it via `git status --short` on both directories, then copied the files to the worktree and reverted the main checkout. ~3 tool calls wasted. Without the dual-status check, the PR would have shipped on the wrong branch (the main checkout's branch `docs/bq-cost-spike-2026-07-08-findings`, NOT the worktree's `fix/aegon-rejoin-co-presence-8444`).

### Pitfall 2 — `assertIn("Every NPC", self.text)` failed because the prompt uses lowercase

Initial test assertion `self.assertIn("Every NPC", self.text)` failed because the prompt's Quick Self-Audit checklist uses lowercase (`for every npc named`). The assertion was on the wrong case.

**Recipe:** case-fold the substring before asserting, NOT the text. `self.assertIn("for every npc", section.lower())`. Then if the prompt uppercases it later, the test still passes (false-positive protection).

### Pitfall 3 — File-wide `assertNotIn(lore_token)` false-positives on legitimate lore references

Initial test `assertNotIn("Aegon", self.text)` would fail because the prompt legitimately references "Aegon" in other contexts (the lore-level example, the §"Example with Parallel Execution" block, etc.).

**Recipe:** scope the assertion to the new section only via `text.split("## Canonical-State Anchor")[1]` (or `text.split("## Future Event & Milestone Consistency")[0]` for the OLD section). File-wide assertions for campaign-specific lore tokens always false-positive.

### Pitfall 4 — Git `git status` from the wrong CWD gave misleading output

After `cp`ing files from `/tmp/` to the worktree, I ran `git status --short` from `$HOME/projects/your-project.com/` (main checkout). The status showed the files as `??` (untracked) — but those untracked files were in the WORKTREE, not the main checkout. CWD is the source of truth for `git status`.

**Recipe:** always `cd <worktree>` first, then `git status --short`. If running from main checkout, pass the worktree path explicitly: `git -C $HOME/projects/wt-<topic> status --short`.

### Pitfall 5 — VICTORY RIPPLE PROTOCOL pre-existing test failure (out of scope)

`$PROJECT_ROOT/tests/test_prompts.py::TestVictoryRippleProtocol::test_victory_ripple_protocol_present_in_narrative` failed BOTH before and after my edits — it's looking for a section added by an unrelated fix (#8388) that lives on a different branch. Not my fix's regression. Verify by running the test against `git stash`'d main first; if it fails there too, it's pre-existing and out of scope.

**Recipe:** before claiming "my fix introduced a regression", always run the failing test against the pre-fix state. If it failed before, document it as pre-existing and link the fix that needs to land first.

## Where this PR lands in the cluster-signal-driven decision tree

Per `references/repro-planning-block-and-campaign-cluster-2026-07-18.md` §3 (campaign-cluster pre-threshold warning):

| Sibling count on same campaign | Action |
|---|---|
| 1 | File per-scene repro. Single-instance. |
| 2 | File per-scene repro. Flag campaign as potentially structural. |
| **≥3** | **STOP per-scene filing. Branch a root-cause-first prompt fix that addresses the common anchor layer.** |

Verified case 2026-07-18, campaign `D3iZvnGiBl9wyveQBFj9`: 5 siblings accumulated on the same campaign in <24h. The PR landed BEFORE the 5th repro was filed — i.e. the structural-bead trigger fired at #8440 (3rd sibling) and the prompt-fix PR (#8446) was opened after the 5th (#8444). This is the canonical sequence: 3rd sibling triggers the bead, 5th sibling triggers the prompt-fix PR.

## Token-cost impact

The PR adds:
- ~140 lines to `planning_protocol.md` (the §"Canonical-State Anchor" section)
- ~26 lines to `narrative_system_instruction.md` (the §"Narrative Consistency Anchors" section)
- 220 lines for the test file

Both new sections sit at the END of their respective files, outside the implicit-cache-hot zone. Per AGENTS.md "Prompt Duplication & Compression", this is the correct placement — keeps the cache hit rate high for the existing rules.

## Cross-references

- `references/repro-planning-block-and-campaign-cluster-2026-07-18.md` — the 5-anchor taxonomy and the §"Future Event & Milestone Consistency" precedent
- `references/phenotype-lock-static-evidence.md` — the 3 static-evidence greps that run BEFORE this recipe (code-symbol, prior-export, sibling-issue)
- `references/static-evidence-sufficient-no-live-turn.md` — when HISTORICAL RED ARTIFACT is acceptable (no live LLM replay needed)
- `references/gh-rate-limit-rest-fallback.md` — when GraphQL budget is 0, REST fallback preserves the hard-gate contract (verified on issue #8444 in this session)
- `references/find-new-campaign-id-after-copy.md` — `copy_campaign.py` returns only `{dest_uid, dest_email}`; Firestore REST is the canonical lookup. The `--allow-same-user` flag is mandatory for cross-UID copies
- AGENTS.md §"Root-cause-first prompt discipline" — why prompt-side fix, not backend enforcement
- AGENTS.md §"Evidence for mvp_site Production Changes (Mandatory)" — `/es` requirement for any non-test change under `$PROJECT_ROOT/` (the test file in Component 3 satisfies the "tests + non-LLM evidence" carve-out, but production changes still need real server proof)

## Worked example — $GITHUB_REPOSITORY PR #8446 (2026-07-18)

The 5-sibling cluster on campaign `D3iZvnGiBl9wyveQBFj9`:

| # | Sub-class | Fix coverage in PR #8446 |
|---|---|---|
| [#8438](https://github.com/$GITHUB_REPOSITORY/issues/8438) | LLM-prose invention (Blood-Scent silver vial) | NOT covered by #8446 — covered by PR #8439 (LLM-prose side of canonical-state validation) |
| [#8440](https://github.com/$GITHUB_REPOSITORY/issues/8440) | Directive retcon violation | §5 (God-Mode Directive Compliance) covers the planning_block side; §7 covers the narrative-prose side. Pairs with PR #8441's directive-specific fix. |
| [#8442](https://github.com/$GITHUB_REPOSITORY/issues/8442) | MBTI / Alignment leak | §7 (narrative side directive compliance) + the internal-contract rule from PR #8439 |
| **#8444 (this)** | NPC co-presence violation | §4 (NPC Co-Presence) + §6 (NPC Reachability) + Quick Self-Audit items 1, 3, 4 |
| Pre-existing structural-issue bead | NPC status canonical-state | §7 (NPC Status Alignment) covers the planning_block side; §8 covers the narrative-prose side. Pairs with PR #8352's existing `master_directive.md` §"Canonical NPC Status" rule. |

PR #8446 closes 4 of 5 anchor sub-classes (NPC co-presence + directive compliance + NPC reachability + NPC status alignment). The 5th (LLM-prose invention) is PR #8439's territory. Together they cover the full cluster.

**Verification (test run, from the actual session):**

```
$ TESTING_AUTH_BYPASS=true ./venv/bin/python -m pytest \
    $PROJECT_ROOT/tests/test_planning_block_canonical_state_anchor_8444.py -v
...
============================== 15 passed in 0.08s ==============================

$ TESTING_AUTH_BYPASS=true ./venv/bin/python -m pytest \
    $PROJECT_ROOT/tests/test_planning_block_future_leak_7763.py -v
...
========================= 3 passed, 1 skipped in 0.05s =========================

$ TESTING_AUTH_BYPASS=true ./venv/bin/python -m pytest \
    $PROJECT_ROOT/tests/test_dialog_prompt_loading.py -v
...
============================== 1 passed in 0.27s ==============================
```

PR: https://github.com/$GITHUB_REPOSITORY/pull/8446
SHA: `4524525569692db3e5a5b36a818a7248b65fae09`
Worktree: `$HOME/projects/wt-aegon-rejoin-repro`
Branch: `fix/aegon-rejoin-co-presence-8444` (off `origin/main` @ `65dd85b651`)

## Worked example — $GITHUB_REPOSITORY PR #8469 / issue #8468 (2026-07-20)

**Bug class C: NPC knowledge-of-PC violation.** Different sub-class from PR #8446 (co-presence / reachability) and PR #8439 (LLM-prose invention) — but the same 4-component deliverable shape applies. Proves the recipe generalizes across bug classes.

**Source:**
- Campaign: `EROaUnSbmDhqBedTbJMg` (Sariel Valyria), scene 454 (`RewardsAgent`, gemini-3-flash-preview)
- Issue: [#8468](https://github.com/$GITHUB_REPOSITORY/issues/8468)
- PR: [#8469](https://github.com/$GITHUB_REPOSITORY/pull/8469) (draft)
- Branch: `fix/eroa-targaryen-identity-knew-me` HEAD `6dfdd5bf2702aa24857d583615d3912776b6b3a2`
- Worktree: `$HOME/projects/wt-eroa-targaryen-identity`

**The bug** (verbatim prose from scene 454):

> "The romantic tensions are a secondary pincer. You can feel the heat of Aegon's gaze as he watches you — a mixture of **protective reverence** and a deep, **existential dread** that he is losing the **woman he believes he 'saved.'** Visenya's hand rests on *Dark Sister*, her tactical suspicion flaring as she observes your un-aging beauty. **She remembers the Sea Cliffs twenty years ago; she remembers a girl who looked exactly as you do now**, and the realization that you have **bypassed the decay of the Fourteen Flames** is a **splinter in her mind** that no mask can fully heal."

Two co-occurring root causes (NOT one):
1. **NPC-knowledge-of-PC violation** — Aegon / Visenya are described with internal-monologue claims that depend on knowing Sariel's hidden Consul-of-Valyria / divine identity, but the Lady Daena mask layer forbids that knowledge.
2. **LLM-prose invention** — "Sea Cliffs twenty years ago" and "Fourteen Flames decay" are invented lore tokens that do not exist anywhere in prompts or code (grep clean in both `$PROJECT_ROOT/` and `$PROJECT_ROOT/prompts/`).

**Sub-class coverage map** (Component 4 of the recipe):

| Sibling issue | Sub-class | Fix coverage in PR #8469 |
|---|---|---|
| [#8463](https://github.com/$GITHUB_REPOSITORY/issues/8463) / PR #8464 | NPC-knowledge-of-PC OMITTED (Argella suspicion dropped) | §NPC Knowledge of Player-Character Identity forbids BOTH "include knowledge the NPC lacks" AND "omit knowledge the NPC has" by anchoring the rule to canonical state |
| #8468 (this) | NPC-knowledge-of-PC VIOLATED + LLM-prose invention | §NPC Knowledge of Player-Character Identity + §Choice Premise Validation mirror. The "forbidden-pattern examples" inside the prompt section serve the same anti-invention function as PR #8443's NPC Development section. |
| [#8444](https://github.com/$GITHUB_REPOSITORY/issues/8444) / PR #8445 | NPC co-presence (anchor b) | NOT covered by #8469 — covered by PR #8446. Different sub-class. |
| [#8451](https://github.com/$GITHUB_REPOSITORY/issues/8451) / PR #8452 | Vaelaros-tuned Blood-Scent lore invention | NOT covered by #8469 — covered by PR #8443's NPC Development section. Different sub-class. |

**The 4-component shape** (verbatim from PR #8469):

| # | Component | File | Lines | Notes |
|---|---|---|---|---|
| 1 | §NPC Knowledge of Player-Character Identity | `$PROJECT_ROOT/prompts/narrative_system_instruction.md` | +28 | Inserted after §NPC Development (Character & World Protocol section). Names canonical sources (`active_constraints`, `god_mode_directives`, `core_memories`). Enumerates forbidden NPC-inference patterns with bug-origin examples. Bug-class label `NPC-knowledge-of-PC violation`. |
| 2 | §NPC Knowledge of Player-Character Identity (Choice Premise Validation) | `$PROJECT_ROOT/prompts/planning_protocol.md` | +44 | Inserted after §Future Event & Milestone Consistency. DROP/rewrite directive (matches existing §Future Event verb). Cross-references Component 1 explicitly so a fix-author cannot land one half without the other. |
| 3 | `$PROJECT_ROOT/tests/test_npc_knowledge_of_pc_constraint_8468.py` | new file | +172 | Follows `test_planning_block_future_leak_7763.py` shape. 12 prompt-contract pins + 1 properly-skipped server-side Layer-C placeholder. Includes **section-scoped** `assertNotIn(lore_token, anchor_section)` to prevent campaign-specific hard-coding. Includes **"no long banned patterns only in prompt"** test that asserts the bug-origin phrase appears ≤1 time across both files AND only inside the new section. |
| 4 | PR body | n/a | n/a | Sub-class coverage map (above) + sibling cluster signal + token-cost impact + verification output + "out of scope" notes (Factor A directive-race controller, full campaign export, server-side Layer-C enforcement). |

**Verification (verbatim from the actual session):**

```
$ TESTING_AUTH_BYPASS=true vpython -m unittest mvp_site.tests.test_npc_knowledge_of_pc_constraint_8468 -v
...
Ran 12 tests in 0.002s
OK (skipped=1)
```

The 1 skipped test is `test_layer_c_pending_human_approval` — the server-side post-LLM guard. Per AGENTS.md "Root-cause-first prompt discipline", server-side enforcement requires explicit human approval before being added. Tracking it separately is correct; it's NOT blocked on this PR.

**What this example proves** — the 4-component shape is bug-class-agnostic:
- PR #8446 used it for **anchor (b) NPC co-presence / reachability** (planning_block-only originally; narrative mirror added in same PR).
- PR #8443 used it for **class 4 LLM-prose invention** (narrative-only; no planning_block mirror because the bug class doesn't touch choice premises).
- PR #8469 used it for **bug class C NPC-knowledge-of-PC** (both narrative + planning_block mirrors needed because the bug class touches both).

The discriminator for whether to include a planning_block mirror is: **does the bug class touch `planning_block.choices[N]` premises?** If yes, mirror needed (PRs #8446, #8469). If no, narrative-only is fine (PRs #8439, #8443, #8452). This is the only decision point that varies across the 4-component recipe.

**Lesson for future prompt-fix PRs:** when designing the test file, include the **"no long banned patterns only in prompt"** assertion. This catches the failure mode where a fix-author puts the bug-origin phrase in the prompt as a forbidden example but the LLM later regresses to using it. The test asserts the phrase appears ≤N times AND only in the new section, which forces the fix-author to scope examples to the new section.