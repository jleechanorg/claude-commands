---
name: campaign-bible-design
description: Design a tabletop campaign bible (D&D 5e, Pathfinder, custom system) for a specific character + setting by running the superpowers brainstorming protocol — multiple-choice questions one at a time, hard-gate no-implementation-before-design-approval — and write the result to a Google Doc + llm-wiki source page. Use when the user asks "design a campaign for X" or "make a campaign bible" or extends an existing campaign (vN+1). Triggers on "Visenya", "campaign v9", "design campaign", "campaign bible", "god campaign", "ascension track". v1.0.0 fires when the campaign must be designed as a *system* (one machine, multiple emergent endings) rather than as a *story* (single plot) — and the user pushes back if you propose a canonical ending.
version: 1.0.0
author: hermes (learned from Visenya v9 campaign brainstorm, 2026-07-20, Slack C0AH3RY3DK6/p1784584425.185909)
triggers:
  - "design a campaign for"
  - "campaign bible"
  - "Visenya vN"
  - "god campaign"
  - "ascension track"
  - "gloomstalker assassin"
  - "campaign system not story"
  - "emergent endings"
  - "campaign module for"
  - "make a campaign"
---

# Campaign bible design — brainstorming protocol with system-not-story rule

## The principle

**A campaign is a *system*, not a *story*.** The bible describes the machine that produces stories; the *player* picks the story at the table. This rule is **non-negotiable** for Jeffrey — he will explicitly call it out ("Don't make me pick an ending, just save possibilities") if you propose a canonical resolution mid-brainstorm. The bible must:

1. Ship with **multiple documented endings** (≥2; ideally 3-4)
2. Mark the endings as **mechanically distinct** (each reachable through different mechanical conditions)
3. Explicitly state **"no canonical ending"** in the design
4. Reserve a **player-defined** slot for off-rail resolutions

Anti-pattern: pre-writing the campaign arc with a single fixed resolution, then asking "what do you want the ending to be?" That's a *story* proposal. The user wants a *system* proposal.

## The brainstorming protocol (8-question structure)

Jeffrey has confirmed multiple-choice questions, one at a time, are the right shape for campaign design (verified Visenya v9 brainstorm, 2026-07-20). The question *types* that work:

| Q# | Question type | Example (Visenya v9) |
|---|---|---|
| Q1 | Open framing | "Adversarial match + worldbuilding aftermath, single mortal anchor, or something else?" |
| Q2 | Specific constraint | "First Song adversary? Eastern framing? Doom as apotheosis or extinction?" |
| Q3 | Setting geography | "Yi Ti Golden Empire, Asshai, Shadow Lands, or Doom's basalt?" |
| Q4 | Choice shape | "Joining, Replacement, Refusal, or open-ended?" |
| Q5 | Engagement type | "Three canonical branches + freeform, or one system with multiple emergent endings?" |
| Q6 | Mechanic candidate | "Sanguine Thread as book of names, as lineage, as reputation, or as perception?" |
| Q7 | First quest-shape question | "God-campaign tier mechanic — Archon ranks, Divine Rank table, or custom progression?" |
| Q8 | Final identity pick | "First Song = V6-Visenya / V8-Visenya / V2-Visenya / blend?" |

**Hard rules from the brainstorming skill:**

- **One question per message** — never stack 2-3 questions in a single reply
- **Multiple choice preferred** — present 3-4 options + a freeform option, not open-ended prompts
- **Don't propose the design until Q8** — questions are the deliverable, not previews
- **Lock the previous answer before asking the next** — restate what was just decided, then ask

## Class-level brainstorm patterns (reusable across campaigns)

These four patterns appear across campaign designs and should be unlocked early:

1. **The Blood/Name/Bloodline mechanic** — an object that *transforms* at each tier (book, weapon, title, reputation). The same object, different function per tier. The system tracks the *change*, not the count.

2. **The mirror/ancestor/exile adversary** — the Big Bad is a *future version* of the PC, or an *ancestor*, or a *parallel-world version*. The campaign is the PC confronting what they *could become*. Sadism comes from *loneliness without mortal anchors*, not from generic evil.

3. **The Magic Barrier System** — the antagonist's full power is *gated* by world-level containment; the PC's growth *weakens* the barrier as a *side effect*. The price of becoming a god in this world is the antagonist's return. L20+ stakes are not just "PC vs BBEG" but "PC's growth is the mechanism by which BBEG returns".

4. **Multiple emergent endings** — Joining (apotheosis-as-homecoming), Replacement (the kill), Refusal (the unprecedented choice), Player-defined (off-rail). Each is mechanically distinct, each is a real choice at the table, no canonical resolution.

## Working with "campaign = system, not story"

The user pushback pattern (verified Visenya v9): when you propose canonical endings, the user says *"don't make me pick an ending, just save possibilities — we are designing the campaign not a fully decided story."*

**Right response:** acknowledge, drop the canonical-resolution framing, re-shape to system-not-story.

**Right mechanic structure:**

- **Mechanic definition** — what the mechanic *is* (e.g., "the Sanguine Thread is a lineage mechanic that strengthens with each kill")
- **Mechanic tiers** — what it does at each level (Cub → Stalker → Apex Predator → Sovereign → Demi-God → God)
- **Multiple emergent endings** — 3-4 documented + 1 player-defined
- **No "the story ends with X"** language — instead: "the campaign supports Joining/Replacement/Refusal/Player-defined as mechanical resolutions; the player picks at the table"

## Working with the "take inspiration, don't copy" rule

The user has explicitly stated (Visenya v9): *"i said to take inspiration from that bhaal campaign and dont directly copy."* This applies to *any* prior open PR / module / campaign they reference.

**Copy-vs-inspire test for each mechanic you propose:**

1. Is the mechanic's *name* unique to this campaign? (If it's the same name as a prior module, that's a copy.)
2. Is the mechanic's *function* different? (If it's the same function with renamed elements, that's a copy.)
3. Does the mechanic have a *campaign-specific rationale*? (If the only reason it exists is "the other campaign had it", that's a copy.)
4. Does removing the mechanic break the *system*? (If it's decorative, cut it.)

When in doubt: cite the inspiration source explicitly ("Inspired by [PR / module] — used as a *shape* for X, not as content") and explain the campaign-specific redesign.

## Status checks (use these, the user expects them)

The user accepts a periodic "Status Visenya v9"-style recap. The right shape:

- **What's locked in** (your decisions so far — short table)
- **What's shipped** (already pushed to wiki + Google Doc — file URLs + status)
- **What's in /tmp** (NOT yet uploaded)
- **What's blocked** (one question awaiting user pick)
- **Bottom line** (one sentence: "system well-designed, holding on one question per protocol")

Format the table with `| Decision | Your pick | Notes |` headers. Keep status checks ≤200 words. The user uses them to confirm progress mid-session.

## Output destination (Visenya v9 pattern, generalize to other campaigns)

For Visenya specifically (and likely future Visenya v10+):

- **Spec + Plan:** `~/llm_wiki/docs/superpowers/specs/YYYY-MM-DD-<campaign>.md` + `~/llm_wiki/docs/superpowers/plans/YYYY-MM-DD-<campaign>.md` (force-add with `git add -f`, the docs/ dir is gitignored in llm-wiki)
- **Source page:** `~/llm_wiki/wiki/sources/<campaign>.md` (a wiki source = a structured summary of the design)
- **Concept pages:** one per major mechanic (e.g., `SanguineThread.md`, `MagicBarrierSystem.md`, `FirstSong.md`, `BloodDragonReputationDie.md`) — each a self-contained concept reference
- **Entity pages:** one per setting element (e.g., `RooksRest.md`)
- **index.md:** Concepts section + Sources section + Entities section, all updated
- **log.md:** ingest + finalize + ship entries with timestamps
- **Google Doc:** full spec content, replace-with-`--markdown` flag, smoke-test by exporting to /tmp

## world_reference/ PR to $GITHUB_REPOSITORY (final ship step)

After llm-wiki is on origin/main, mirror the spec to WA's `world_reference/` directory:

1. Fresh worktree from `origin/main` of `$GITHUB_REPOSITORY`
2. File: `world_reference/campaign_module_<short>.md` — naming convention matches existing modules (campaign_module_daenerys.md, campaign_module_luke.md, campaign_module_dragon_knight.md, etc.)
3. Structure: italic preamble + Shared World Background + Hidden Truth + 3-Generation Power Lineage table + Module 0 (Campaign Summary + World History + Campaign Details) + mechanic tables + provenance
4. Single-scope commit, push, open PR
5. Drive through Green Gate (GATE-1 self-referential FAIL + GATE-3 CodeRabbit rate-limit are non-blocking on `world_reference/` content PRs — branch protection on main has no required checks; mergeable=true; `gh pr merge --merge --delete-branch` works directly)

## Anti-patterns to avoid

- **Don't ask "what do you want the ending to be?"** — the player picks at the table; document multiple + player-defined
- **Don't copy a prior campaign module's name** — find a campaign-specific name for the central mechanic
- **Don't propose a single fixed plot arc** — the bible is the *machine*, the player writes the *story*
- **Don't skip the status check** — the user uses them to confirm mid-session progress
- **Don't pre-write the design before Q8** — questions are the deliverable; proposal comes after
- **Don't stack multiple questions in one reply** — one Q per message, multiple choice preferred

## Pitfalls

1. **The "mechanic is the engine" trap.** A mechanic that *only* exists to drive the story (e.g., "the Book of Names fills up to mark story beats") is decorative. The mechanic must *change the player's options* at each tier, not just record progress.

2. **The "ending is canon" trap.** If your design document has a single "Story" section that walks through the canonical arc, you've written a story, not a campaign. The Player's Book should read like a *rulebook*, not a *novel*.

3. **The "first adversary is just an enemy" trap.** The mirror/ancestor/exile adversary pattern is *stronger* than a generic big bad — it makes the campaign about *the PC's own choices*, not about defeating an external threat. If your Big Bad has no personal relationship to the PC, reconsider.

4. **The "ascension is just stat bumps" trap.** L20+ god-campaign arcs that are just "you get bigger numbers" are not engaging. The interesting shape is *what changes about the world as you ascend* — who can manifest where, what NPCs can perceive about you, what moral choices become available or unavailable. For quantified-stat-table inspiration, see `worldarchitect-campaign-tier-redesign` skill — the Aizen-pattern (DR/DAC/DPP/DAIR/DLR/Primary Damage table) is the LLM-grounded template.

5. **The "copying PR #XXXX" trap.** When the user says "take inspiration from PR #XXXX", they mean the *shape* (tier mechanic, magic system, mirror adversary), not the *content* (specific names, specific resolution, specific stat blocks). Audit each mechanic against the copy-vs-inspire test before shipping.

## Related skills

- `worldarchitect-campaign-tier-redesign` — for *redesigning existing tier mechanics in WA production code* (L0/L1/L2 framing, DPP-overload, quantified-stat-table patterns from the Aizen god-campaign). Use this skill for tabletop campaign *content* design; use the other for *production-code* tier redesign.
- `wa-green-gate-pr-shape` — for driving WA PRs through the Green Gate. Includes the `world_reference/` content-only path (GATE-6 / GATE-6b auto-bypass, GATE-1 self-referential + GATE-3 CodeRabbit rate-limit are non-blocking on content PRs).
- `finish-the-job` — for end-to-end execution discipline (don't pause for confirmation; drive to mergeable state; ship).
- `workflow/always-pr-never-local-edit` — for the never-just-local-edit discipline that the worldai PR workflow requires.

## Reference files

- `references/visenya-v9-brainstorm-flow.md` — full Q1-Q8 transcript from the 2026-07-20 Visenya v9 brainstorm session (the canonical example of this protocol applied end-to-end). Includes the user's "campaign ≠ story" correction, the "take inspiration, don't copy" correction, the OOB First Song backstory, and the full ship sequence.
- `templates/campaign-module-bible.md` — template for the `world_reference/campaign_module_<short>.md` final document (the shape that mirrors existing WA campaign modules like `campaign_module_daenerys.md` and `campaign_module_dragon_knight.md`).
- `templates/concept-page.md` — template for the `~/llm_wiki/wiki/concepts/<concept>.md` wiki concept page (one per major mechanic).