---
tags: [repro, worldarchitect, planning-block, canonical-state-anchor, npc-peer-autonomy, dispatch-framing, independent-ally, bg3, campaign-q04GfOEl4SWnEQrFUVST, issue-8499, pr-8500]
---

# NPC Peer-Autonomy — 4th canonical-state-anchor sub-class (issue #8499, PR #8500)

## Bug phenotype

User reports: *"the planning block is still acting like Astarion just travels with me like a minion I order around when I've said a million times he's doing f his own thing"*.

Trigger choice emitted by `planning_block`:

> **Frame the Return:** Send Astarion ahead to prepare the city for your 'heroic' return with 'liberated' Elturgard veterans.
> Pros: Maximizes 'Hero' mask impact, Increases public F growth, Lowers suspicion regarding the decimation
> Cons: Requires high-tier Deception/Persuasion, Risk of a survivor leaking the truth

The imperative premise *"Send <NPC> ahead"* presupposes dispatch authority. For an `independent_ally` NPC the player does not have that authority.

## Source campaign

- `q04GfOEl4SWnEQrFUVST` — "bg3 nocturne murder god" (BG3 Nocturne — Sanguine Architecture)
- Owner UID `vnLp2G3m21PJL6kxcuAqmWSOtm73`, $USER@gmail.com
- Test copy `bOexQX3yrrQzaA8KOG3D` under `0wf6sCREyLcgynidU5LjyZEfm7D2` (<your-email@gmail.com>)

## Why the narrative mirror already had the rule

The export at `/tmp/your-project.com/repro-exports/bg3-nocturne-dup-content-42/bg3 nocturne murder god _dupe content_ _copy__MK2ON2vc.txt` shows the narrative layer correctly establishing Astarion as Independent Ally in **8+ places** (lines 2178, 2452, 2498, 2523, 2652, 2932 etc.). The doctrine "Astarion, Minthara, Gale, Lae'zel, Sarevok, Araj are confirmed as independent allies. You cannot order them" was present in the god-mode directives and the narrative re-derived it correctly.

But the planning layer (`planning_protocol.md` §"Canonical-State Anchor") covered only:
- §4 NPC Co-Presence
- §5 God-Mode Directive Compliance
- §6 NPC Reachability
- §7 NPC Status Alignment

**§8 NPC Peer-Autonomy was missing.** The planning layer was re-deriving NPC agency on every turn and defaulting to a party-of-travelling-companions frame, producing imperative "Send / Dispatch / Order / Have" choices that presuppose a subordination the canonical state does not grant.

## Static-evidence grep signals (phenotype-lock)

```bash
# Code-symbol grep — should be ZERO in $PROJECT_ROOT/ before the fix:
grep -rn "Astarion" $PROJECT_ROOT/prompts/ --include="*.md"   # → 0 hits pre-fix
grep -rn "co-presence\|companion\|travels with" $PROJECT_ROOT/prompts/planning_protocol.md  # → 0 hits pre-fix

# Prior-export grep — confirms narrative mirror has the doctrine:
grep -n "Independent Allies\|Peer Autonomy\|Allied Peerage\|doing his own thing" \
  /tmp/your-project.com/repro-exports/bg3-nocturne-dup-content-42/*.txt  # → 8+ hits

# Sibling-issue scan — confirms 3rd-sibling cluster trigger:
gh issue list --repo $GITHUB_REPOSITORY --state all --search "q04GfOEl4SWnEQrFUVST"
# → #8490 (Factor F, 2026-07-20), #8497 (Factor G, 2026-07-21), #8499 (this issue, 2026-07-21)
```

## Fix shape (4-component, verified on PR #8500)

| # | File | Change |
|---|------|--------|
| 1 | `$PROJECT_ROOT/prompts/planning_protocol.md` | New `### 8. NPC Peer-Autonomy (No "Send" / "Dispatch" / "Order" Framing for Independent Allies)` subsection. 3-class relationship table (Direct / Independent Ally / Antagonist) with forbidden premise forms (Send / Dispatch / Order / Have / Command) and valid rewrites (Negotiate with / Coax / Concede to / Offer). Detection recipe reads `npc_data.<name>.relationship` first, falls back to scanning `god_mode_directives[]` for trigger phrases (Independent Allies / Peer Autonomy / Allied Peerage / own agenda / his own thing / doing his own thing / you cannot order them). Worked example using the Astarion case from the source campaign. |
| 2 | `$PROJECT_ROOT/prompts/planning_protocol.md` | Quick Self-Audit §7 added: relationship-class / premise-form consistency check. |
| 3 | `$PROJECT_ROOT/prompts/narrative_system_instruction.md` | New `### 9. NPC Peer-Autonomy (No "Following" / "Traveling With" Framing for Independent Allies)` mirror. Forbids the narrative-side "follows you" / "travels with you" / "at your side" framing for `independent_ally` NPCs. Promotes the doctrine from example prose (only emitted when the LLM happened to recall it) to a canonical-state invariant with the same authority as §6 NPC Co-Presence and §7 God-Mode Directive Compliance. |
| 4 | `$PROJECT_ROOT/tests/test_planning_block_npc_peer_autonomy_anchor_8499.py` | 6-test contract pinning the §8 / §9 structural changes. |

## Worked example embedded in the prompt

**Forbidden (DO NOT emit):**
> *"Send Astarion ahead to prepare the city for your 'heroic' return with 'liberated' Elturgard veterans."*
> — `npc_data["Astarion"].relationship == "independent_ally"` (confirmed by `god_mode_directives[]` rule). "Send <NPC> ahead" presupposes dispatch authority the player does not have.

**Compliant rewrite:**
> *"Negotiate with Astarion to convince him to use his spawn network to prepare the city's patriar houses — but be prepared to concede a share of the Soul Ledger, since Astarion will not move his own network for free."*
> — same strategic outcome, premise correctly presupposes a negotiation where the player pays a price.

## Detection recipe (for the LLM)

1. For each NPC named in `choices[N].text|description|pros|cons|id`, read `npc_data.<name>.relationship` (default `"unknown"`).
2. If `relationship` unset, scan `custom_campaign_state.god_mode_directives[]` for any directive whose `rule` text names the NPC AND uses one of the trigger phrases: "Independent Allies", "Peer Autonomy", "Allied Peerage", "own agenda", "his own thing", "doing his own thing", "you cannot order them". If matched → treat as `independent_ally`.
3. If the choice's `text` begins with "Send <NPC>", "Dispatch <NPC>", "Order <NPC>", "Tell <NPC> to", "Have <NPC>", "Command <NPC>" AND the NPC's effective relationship is `independent_ally`, **rewrite or DROP**. Rewrite MUST replace the imperative premise with a negotiation/coax/concede premise that names the player-side cost the NPC would demand.

## Pitfall: contract-test resolver pointing to the wrong repo (see SKILL.md §"Contract-test resolver pitfall, 2026-07-21")

The first run of the 6-test contract had REPO_ROOT hard-coded as `"$HOME/projects/your-project.com"` (the main checkout). The worktree at `$HOME/projects/wt-astarion-anchor-8501/` had the patched prompt files but the test was reading from the main checkout (which had the un-patched files). All 6 tests failed with extraction errors — not assertion errors.

**Fix:** the test file now resolves REPO_ROOT by walking up from `__file__` until it finds the marker file (`$PROJECT_ROOT/prompts/planning_protocol.md`), with an `HERMES_REPO_ROOT` env var override for CI. See the pitfall section in the parent SKILL.md for the full recipe.

## Sibling cluster context (canonical-state-anchor class)

| # | Issue | Sub-class | Layer fixed |
|---|---|---|---|
| [#8438](https://github.com/$GITHUB_REPOSITORY/issues/8438) | blood-scent invention | LLM-prose invention (Bug Class 4) | narrative |
| [#8440](https://github.com/$GITHUB_REPOSITORY/issues/8440) | Inquisition / Blood-Scent confrontation | directive retcon | narrative |
| [#8442](https://github.com/$GITHUB_REPOSITORY/issues/8442) | MBTI / ISTJ letters in player prose | LLM-prose invention | narrative |
| [#8444](https://github.com/$GITHUB_REPOSITORY/issues/8444) | Aegon co-presence | NPC co-presence (planning sub-class) | planning §4 |
| [#8490](https://github.com/$GITHUB_REPOSITORY/issues/8490) | Combat Scope Classifier | Factor F — narrative-ack-as-write | god-mode + combat prompt |
| [#8497](https://github.com/$GITHUB_REPOSITORY/issues/8497) | Mantle of Radiant Slayer default aspect | Factor G — prompt-side default missing | god-mode prompt |
| [#8499](https://github.com/$GITHUB_REPOSITORY/issues/8499) (this issue) | Astarion / NPC independent-agenda | NPC peer-autonomy | **planning §8 + narrative §9** |

Cluster trigger: 3rd repro on `q04GfOEl4SWnEQrFUVST` (#8490, #8497, #8499). Per `references/repro-planning-block-and-campaign-cluster-2026-07-18.md` §"When the 3rd sibling fires", this is the threshold for stopping per-scene issues and branching a fresh worktree for a root-cause-first prompt fix.

## Branch / PR

- Branch: `fix/astarion-independent-ally-planning-anchor-8499`
- HEAD: `b859ac121a2961621ccdf414d5b242d2a637c618`
- PR: [#8500](https://github.com/$GITHUB_REPOSITORY/pull/8500) (draft)
- 6/6 contract tests green on the worktree
- Total: 3 files changed, 186 insertions(+), 1 deletion(-)

## Open follow-up

Live LLM replay against test copy `bOexQX3yrrQzaA8KOG3D` to verify the planning block no longer emits the forbidden premise form. Flagged in the PR body under "Pre-state / post-state evidence" — not blocking this PR (the fix is prompt-layer only, no `$PROJECT_ROOT/` runtime code path touched).