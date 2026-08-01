---
name: references-p36-stable-universe-contract
description: Companion to Pitfall P36 in campaign-design-iteration. Spells under the default D&D 5e ruleset that anchor the Information Provenance Gate, the canonical detection-range table, the synthesized contract clauses, and the SRD 5.1 fact pack verified on 2026-07-29.
---

# P36 — Stable-Universe Mechanics Contract (companion)

This file is the detailed companion for Pitfall P36 in the umbrella skill. It contains:

1. The D&D 5e spell-range table the user expects the LLM to honor when stating what magic "knows" or "detects."
2. The verbatim user-correction catalog mined from 230 LLM-wiki transcripts (12,498 God Mode messages).
3. The synthesis contract for `/superpowers brainstorm`-driven prompt-only spec work.
4. The SRD 5.1 fact pack (Detect Magic / Detect Thoughts / Locate Creature / Clairvoyance / Scrying / Nondetection) with exact range, target, duration, save, and components, sourced from the official WotC PDF on 2026-07-29.

For the umbrella summary, the `### Pitfalls` section in `SKILL.md` retains the canonical P36 introduction + visible failure-pattern list. This companion carries the table, contract clauses, and SRD fact pack.

## D&D 5e bounded detection/divination spell table

| Spell (level, school) | Range / Limit | Target / Output | Save / Counter |
|---|---|---|---|
| `Detect Magic` (1st-level divination, ritual) | Active concentration; senses magic within **30 feet** of caster | Visible creature/object in the 30-ft radius; learns magic school | Blocked by 1 ft stone / 1 in common metal / thin sheet of lead / 3 ft wood or dirt |
| `Detect Thoughts` (2nd-level divination) | Self; creature within **30 feet** | Surface thoughts of one creature at a time | Deeper probing requires Wisdom save; on save, spell ends |
| `Clairvoyance` (3rd-level divination) | **1 mile** | Invisible sensor at familiar or obvious location; one sense at a time | Sensor can be seen by `See Invisibility` / Truesight |
| `Scrying` (5th-level divination) | Self; **same plane** | Sensor within 10 ft of target | Wisdom save; modifiers by familiarity (secondhand +5, firsthand +0, familiar -5) and connection (likeness -2, possession -4, body part/lock of hair/bit of nail -10). Blocked by `Mind Blank` / `Nondetection` |
| `Locate Creature` (4th-level divination) | Self; **1,000-foot** direction-only | Description or name of familiar creature | Blocked by running water ≥10 ft wide |
| `Locate Object` (2nd-level divination) | Self; 1,000 ft | Known object / latest-known location | Blocked by lead shielding |
| `Nondetection` (3rd-level abjuration) | Touch | Target cannot be targeted by divination magic or perceived through magical scrying sensors | — |
| `Mind Blank` (8th-level abjuration) | Touch | Target immune to psychic detection, divination, and target-by-effect | — |

## Verbatim user-correction catalog

Repeated corrections across unrelated campaigns (verbatim wording where reused, otherwise near-exact):

- "**Signatures are forbidden**" — Bumpkin Swordsman GM #33.
- "**The inquisition shouldn't know about my magic**" — Alexiel V2 GM #63.
- "**What magic residue would Vael see? I didn't use any magic and why is he even concerned about abyssal magic?**" — Alexiel V2 GM #15.
- "**The planar auditor is from the Absolute? You're making it sound like it's from the Absolute**" — Nocturne BG3 v5 fixed GM #50-52.
- "**Investigations are random events**" / "**this is some random investigation made up by you**" — appears in mid-campaign corrections tied to RP drift.
- "**invent a fall back for me isn't the same as using written spell text**" — directive that any default-detection contract should reference SRD text, not improvisation.

These map to repeated corrections in:
- **campaign-design-iteration** P9 (guard rails against scrying detection anti-pattern).
- **campaign-design-iteration** P11 / P15 (don't import mechanic shapes; take inspiration).
- **campaign-design-iteration** P33 / P34 (named in-system consequences; no ruler-of-realm auto-promotion).

## Synthesis contract for the prompt-only spec

When the user says "I want stable universe mechanics / no more magical signatures / default D&D 5e":

1. **Brainstorm first.** Run the brainstorming skill (164-line skill at `~/.codex/superpowers/skills/brainstorming/SKILL.md`) for 5+ rounds of Q&A + three proposal trades. Do **not** ship a prompt patch before spec approval. Per `references/brainstorming-handoff.md`.
2. **Spec at `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`** with these required sections:
   (a) D&D 5e edition decision (2014/SRD 5.1 vs 2024 revised; lock per-campaign at creation).
   (b) Default vs exception mechanics list, each with one-line trigger.
   (c) **Information Provenance Gate** wording: "Before any NPC knows/detects/investigates a fact, identify the exact channel: perception / witness / physical evidence / written spell or feature / established surveillance asset / explicit lore capability."
   (d) **Causal Consequence Gate** wording: "Consequences require both a cause and a delivery path. Severity cannot exceed what the evidence supports."
   (e) Per-campaign Mechanics Manifest contract fields: id, source, scope, users, trigger, range, cost, limits, counters, observability.
   (f) Failed-pattern clause set: ≥10 SHALL/SHALL NOT lines, derived from the user-correction catalog.
3. **Self-contained** per P30: Slack-thread context may disappear, so embed every rationale inline.
4. **Dual-location delivery** per P28: Slack thread + `~/roadmap/docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`.
5. **Sub-task** per Phase 7: open WA prompt-layer PRs/issues so the spec references real PR surface that the WA team can grep (`G1`, `G2`, …).

## Synthesized SHALl-not clauses (load-bearing, ~10 lines for the prompt layer)

1. **SHALL NOT** treat any cast spell as auto-leaving a remotely detectable signature. Spell text governs.
2. **SHALL NOT** invent a "planar auditor / inquisition / world-rule god" without a manifest-defined trigger, range, jurisdiction.
3. **SHALL NOT** rename forbidden mechanics ("resonance," "aura sense," "magical taint," "world-rule judge," "spiritual audit") to bypass the gate. Names are not the gate; channels are the gate.
4. **SHALL** apply the **Information Provenance Gate** before every NPC knowledge claim: perception / witness / physical evidence / written spell or feature / named lore capability. Otherwise the NPC does not know.
5. **SHALL** treat `Scrying` (5th) and `Detect Thoughts` (2nd) as spells, not as world rules. Saves, range, target, duration bind.
6. **SHALL** honor `Nondetection` (3rd) and `Mind Blank` (8th). The player has an opt-out; invoking it ends detection from those channels.
7. **SHALL** admit campaign-specific mechanics (Force push, Dune prescience, Nocturne auditor consumption, Vespera mask ladder, Alexiel Nullification Field) only when listed in the per-campaign Mechanics Manifest. Nothing leaks across campaigns.
8. **SHALL NOT** smear hidden mechanics into other campaigns (Nocturne's Soul Thief / Hogyoku / Malcanthet's Favor / Mora-Karrigan, Vespera's 4-layer mask, Alexiel's Assiah cosmology).
9. **SHALL** keep canonical NPCs / factions / units / planes named in the manifest; do not introduce new "auditor" factions mid-campaign (unless the user typed in `GOD MODE:`).
10. **SHALL NOT** narrate NPC knowledge of player-only state (secret identity, hidden lineage, mortal-mask level, future plot points) when the NPC lacks a written channel.

## SRD 5.1 fact pack (verified 2026-07-29, fetched from `https://media.wizards.com/2023/downloads/dnd/SRD_CC_v5.1.pdf`, extracted at `/tmp/SRD_CC_v5.1.txt`)

- **Detect Magic** — 1st-level divination (ritual). Casting time 1 action, range Self, V S components, duration Concentration up to 10 minutes. "For the duration, you sense the presence of magic within 30 feet of you. If you sense magic in this way, you can use your action to see a faint aura around any visible creature or object in the area that bears magic, and you learn its school of magic, if any." Blocked by 1 ft stone / 1 in common metal / a thin sheet of lead / 3 ft wood or dirt. At Higher Levels: casting with a spell slot of 8th level or higher reveals auras within 30 ft as if you were *always* seeing them, but no further reach.
- **Detect Thoughts** — 2nd-level divination. Casting 1 action, range Self, V S M (a copper piece), duration Concentration up to 1 minute. "For the duration, you can read the thoughts of certain creatures. When you cast the spell and as your action on each turn until the spell ends, you can focus your mind on any one creature that you can see within 30 feet of you." Initially surface thoughts only — *what is most on its mind in that moment*; deeper probing triggers a Wisdom save; on success, the spell ends.
- **Locate Creature** — 4th-level divination. Casting 1 action, range Self, V S M (a bit of fur from a bloodhound), duration Concentration up to 1 hour. "Describe or name a creature that is familiar to you. You sense the direction to the creature's location, as long as that creature is within 1,000 feet of you." Blocked by running water at least 10 feet wide; cannot locate polymorphed/disguised creatures.
- **Clairvoyance** — 3rd-level divination. Casting 10 minutes, range 1 mile, V S M (focus worth at least 100 gp, or a jeweled horn for hearing or a glass eye for seeing), duration Concentration up to 10 minutes. Creates an invisible sensor in a location familiar or in an obvious location that is unfamiliar (e.g. behind a door, around a corner); one sense at a time. Visible as a luminous orb about the size of a fist to creatures with `See Invisibility` or truesight. Upcast: target one additional creature per slot level above 1st.
- **Scrying** — 5th-level divination. Casting 10 minutes, range Self, V S M (focus worth at least 1,000 gp, such as a crystal ball, a silver mirror, or a font filled with holy water), duration Concentration up to 10 minutes. Same-plane target. Wisdom save modified by knowledge (secondhand +5, firsthand +0, familiar -5) and physical connection (likeness/picture -2, possession/garment -4, body part/lock of hair/bit of nail -10). On a successful save the target isn't affected and can't be targeted by this spell again for 24 hours.
- **Nondetection** — 3rd-level abjuration. Casting 1 action, range Touch, V S M (pinch of diamond dust worth 25 gp sprinkled over the target, which the spell consumes), duration 8 hours. The target can be a willing creature or a place or an object no larger than 10 feet in any dimension. "For the duration, you hide a target that you touch from divination magic. The target can't be targeted by any divination magic or perceived through magical scrying sensors."

## Anti-pattern: 200-line "stable universe" prompt essay

The user has rejected repeated "more lore" patch attempts. The Information Provenance Gate is single-gate: cite the channel (one of six) before claiming an NPC knows something. The other clauses are the support layer. Do not bloat the system prompt into a rule-book; the gate is the gate; the manifest binds lore-specific exceptions per campaign.

## Cross-reference

- `campaign-design-iteration` SKILL.md P36 (umbrella summary + visible failure-pattern list).
- `references/load-bearing-math-design.md` (god-mechanics library — reuse when god-tier designs need mechanical density).
- `references/brainstorming-handoff.md` (the brainstorming → spec → writing-plans handoff contract).
- Open WA prompt-layer PRs surface as candidates for the spec's Phase 7 guardrail mapping; grep $GITHUB_REPOSITORY for `magic signature`, `auditor`, `inquisition`, `planar` issues.
