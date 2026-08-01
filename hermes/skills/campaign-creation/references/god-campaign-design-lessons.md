# God-Campaign Design Lessons — Verified 2026-07-21

Source: Slack thread C0AH3RY3DK6/p1784585087.439909 (Nocturne V2 redesign with the user).

## Lesson 1: The L20+ filter is the sharp quality test

Across 19 god-tier campaigns (wikis):

| Campaign | Total scenes | First L20+ scene | % to L20 | Verdict |
|---|---|---|---|---|
| aizen-godhood-continued | 78 | 4 | 5% | ⭐⭐⭐ instant god-mode |
| alexiel-swtor | 822 | 271 | 33% | ⭐⭐ slow-burn graduation |
| noctune-bg3-v6 | 519 | 349 | 67% | ⭐⭐ late-game graduation |
| visenya-v6 | 153 | 74 | 48% | ⭐ Apex Weaver graduation |
| alexiel-assiah-v2 | 363 | 244 | 67% | ⭐⭐ late-game graduation |
| visenya-v1 | 1065 | 886 | 83% | 🟡 L20 very late, kept on momentum |
| dragon-knight | 730 | 334 (claims) | 46% | 🟡 via class-projection |
| witcher-strat | 128 | NEVER | — | ❌ capped L4 |
| rome-pax-julia | 474 | NEVER | — | ❌ capped L10 |
| astarion-ascended | 151 | NEVER | — | ❌ capped L13 (misleading title) |
| aizen-bg3-v2 | 468 | NEVER | — | ❌ capped L18 (god-mechanics doc is the math) |

**Filter rule:** "Did this campaign reach L20+ in entries?" is a sharper quality test than "did the user keep iterating." Mortal-capped campaigns are burnout candidates regardless of premise.

## Lesson 2: D&D 5e player loop is OPTIMIZE → ROLL

The user's exact framing: "A player will optimize the build/stats/items/strategy and then the roll is the last thing to add excitement and variance."

**Wrong design (the failure mode I produced first):**
- Math computes outcome
- No choice before the math runs
- DC has no mechanical meaning
- Roll ends up being the whole answer

**Correct design (the OPTIMIZE→ROLL pattern):**
- Per-dawn choice menu (4-6 named options with distinct mechanical consequences)
- Player picks ONE option
- Math resolves the consequence deterministically
- Roll adds variance within the math-determined bracket
- The roll is the cherry on top of an already-built sundae

## Lesson 3: Hybrid stats (5e L1-19, divine L20+) is the right default

**Three options considered:**
- A. Pure 5e — gods are high-CR stat blocks (Asmodeus = CR 26). Familiar but gods feel like big monsters.
- B. Pure divine — DHP/DAC/DPP/DAIR/DLR/F from L1. Gods feel like gods but player learns new system.
- C. Hybrid — 5e L1-19, divine at L20+. **Recommended.** The L20 transition IS the campaign arc.

Aizen pattern (precedent): Mortal form HP 138 / AC 21 / Save DC 21 / Attack +13 (capped at L20) + Divine projection DHP 750 / DAC 25 / DPP 825 / DAIR +31 / DLR 4 (unlocked at L20).

## Lesson 4: Resource overhead ceiling = 5 trackers

User's quote: "lets avoid defining too many new resources though, might be annoying to manage."

Approved god-campaign resource set:
1. **Repr Die (d4→d20) + RP** — gates actions AND grants attributes
2. **DPP/day** — divine power budget; 1 Major + 3 Legendary per dawn
3. **Follower count (F)** — powers Aizen-style linear scaling
4. **Infamy** — 1 entry per god-kill with timestamp; gates Rank-up
5. **Pantheon Temperature (0-5)** — political heat; affects tithe income

Anything beyond gets cut. Resource sprawl is a failure mode.

## Lesson 5: Three-Layer Deception is the canonical Repr mechanic

Visible stat block / projected stat block / cover-story stat block. Three layers of public-facing reality. Don't invent a fresh mechanic — adopt this pattern from Aizen.

## Lesson 6: Per-dawn choice menu structure

```
═══════════════════════════════════════════
NOCTURNE V2 — DAWN N
═══════════════════════════════════════════
[Stat Sheet: Rank, DHP, DPP, DAIR, DLR, F, Repr Die, RP, Infamy, Pantheon Temp, Wounds]

Today's Choices — pick 1:
  A. [HIGH-STAKES OPTION] (DPP cost) → reward + risk
  B. [BUILDING OPTION] (DPP cost) → reward + nothing-lost
  C. [WOUND-RESOLUTION OPTION] (DPP cost) → reward + Repr-stays-same
  D. [REPR UPGRADE OPTION] (RP cost) → die-size growth
  E. [TEMPERATURE PLAY OPTION] (DPP cost) → political-state shift
═══════════════════════════════════════════
```

Player picks → math resolves → roll variance within bracket.

## Lesson 7: Strategy archetypes at L20+

Sovereign / Diplomat / Tyrant / Seducer (or domain-specific equivalents). The archetype choice is the player's first OPTIMIZE decision. Each archetype changes the math profile and presents different choice options per dawn.

## Lesson 8: Roll role is texture-only, never outcome-determining

Every roll must answer "which flavor" not "did you win."

| Phase | Math decides | Roll adjusts |
|---|---|---|
| Locate | Findability (DPP budget) | — none — |
| Infiltrate | Plane entry | — none — |
| Engage | Major Action feasibility | — none — |
| Counter | God's response | — none — |
| Commit | Damage bracket | 1d20 within ±5 modifier on damage quantity |
| Absorb | Portfolio integration | 1d20 picks which sub-effect manifests |

## Lesson 9: Publicity Tax > Wound Ledger for deicide-cost

Three options considered:
- **Publicity Tax** (Repr decays 2× for 1d4 days, +1 Infamy)
- **Empty Throne** (dead god's portfolio doubles a rival's power unless absorbed same action)
- **Clean Kill** (no cost — match Aizen's pattern)

The user did not ask for a "killed god embeds in you" mechanic in Aizen (clean consumption of Bane was the precedent). Wound Ledger was invented to fill a need that did not exist.

## Lesson 10: Stat block in scene header is the Aizen pattern

10197 endgame-keyword hits across 78 scenes of aizen-godhood-continued = stat block in every scene header. Player reads math at every dawn. This is what makes a god-campaign feel like a god-campaign, not a narrative.

## Anti-pattern: All narrative, no mechanics

User's actual complaint (verbatim from Slack): "It doesnt seem to have many god mechanics just lots of narrative."

**Fix:** Every section must include quantified mechanics. The god-mechanics framework at `references/god_mechanics_general.md` is the canonical system-agnostic source for these.

## How this maps to V2 Nocturne specifically

| V2 Nocturne decision | Source lesson |
|---|---|
| Portfolio = Murder | user-specified |
| Setting = BG3 / Faerûn, post-game | user-specified |
| Protagonist = Nocturne | user-specified |
| Enemies = other gods (not future-self) | user-specified |
| Approach = Three-Engine Mechanic Stack | proposed, locked |
| Hybrid stats (5e L1-19 → divine L20+) | Lesson 3 |
| Per-dawn choice menu (4-6 options) | Lesson 2, 6 |
| Repr Die = visible/projected/cover (Three-Layer) | Lesson 5 |
| Publicity Tax replaces Wound Ledger | Lesson 9 |
| 5-resource cap (Repr Die / DPP / F / Infamy / Temp) | Lesson 4 |
| Roll = texture-only, never outcome | Lesson 8 |
| Strategy archetypes (Sovereign / Diplomat / Tyrant / Seducer) | Lesson 7 |
| Stat block in scene header | Lesson 10 |

## Pre-spec open questions (carried forward from session)

- Q1. Scaling curve: linear / log / step
- Q2. Publicity Tax vs Empty Throne vs Clean Kill for deicide-cost
- Q3. Stat-block-in-header trigger frequency (every scene? every dawn? only at major transitions?)

These were awaiting user response when context compacted; re-raise them at the start of the next session if work resumes.
