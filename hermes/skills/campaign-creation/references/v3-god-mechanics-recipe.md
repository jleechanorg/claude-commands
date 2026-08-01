# V3 God-Mechanics Recipe — Canonical Pattern for L20+ God-Campaigns

Source: PR $GITHUB_REPOSITORY#8488, commits `1968a9b58e` (V2→V3) → `d6e1da7bc5` (V3.1 Chosen/Avatar) → `02d4167a9f` (agy evidence) → `9b8d09ccb8` (V3.20 cleanup).

## When to use this recipe

The user's complaint verbatim (Slack C0AH3RY3DK6/p1784585087.439909, 2026-07-20):
> "keep iterating on this campaign. It doesnt seem to have many god mechanics just lots of narrative?"

Use this recipe whenever a god-campaign (protagonist reaches L20+ or has god-tier stats) feels "all narrative, no math." The recipe produces a 22-sub-mechanics overlay that grounds every scene in quantified mechanics.

## The 22 sub-mechanics (canonical V3 inventory)

Apply ALL of these. Each is a named section (`V3.N`) in the prompt overlay, not a paragraph of prose.

| Section | Name | Type | Notes |
|---|---|---|---|
| V3.0 | Stat-block vocabulary | Reference | 11 stats with player-visible vs LLM-internal split |
| V3.1 | Seven-tier ascension ladder | Table | Mortal → Transcendent with explicit multipliers per tier |
| V3.2 | Mortal → Divine stat conversion | Formulas | Per-stat explicit formulas (HP/AC/AB/DC/Spell DC/DPP/DAIR) |
| V3.3 | Followers (F) Aizen-formula | Formula | `Stat = Nascent + (F/1M) × (Transcendent − Nascent)` |
| V3.4 | Six god-classes | Table | War / Trickster / Domain / Magic / Death / Skilled with stat biases |
| V3.5 | Seven Repr growth sub-systems | List | Major Miracle / Sermon / Holy Day / Oracle / Spend / Patron / Stealth of Murder |
| V3.6 | Action Tier economy | Caps | AT-0/-1/-2/-3 with DPP costs + per-dawn caps |
| V3.7 | Per-dawn menu | Template | 4-6 options with explicit DPP/AT costs |
| V3.8 | Dawn classification | Logic | Routine / Triggered / Quiet (not every dawn has a menu) |
| V3.9 | Pantheon Surveillance bands | Table | Unseen / Whispered / Noticed / Marked / Hunted / Apotheosis-imminent with detection % |
| V3.10 | Roll = variance within bracket | Pattern | 6-phase math-then-roll, 4-roll cap per scene |
| V3.11 | Combat ladder | Table | Auto-win on mortals / named mortals / rolls vs Chosen / Avatars / lesser+ gods |
| V3.12 | Deicide = Clean Kill | Rules | No Wounds / Publicity Tax / Empty Throne |
| V3.13 | AT-3 Legendary Actions menu | List | War March / Divine Duello / Celestial Coup / Reformation / Cleansing Strike / Deicide |
| V3.13.1 | **Chosen Creation** | Mech | 250 DPP / 50 DHP / floor(L/5)-4 cap / DC 25 absorption / loyalty ±5 |
| V3.13.2 | **Avatar Creation** | Mech | 500 DPP / 100 DHP / floor(L/10)-1 cap / 100% DHP reclaimed / no resistance |
| V3.14 | D-faction tracking | System | Per-god D bars + god-class response matrix |
| V3.15 | Per-temple ledger | Bookkeeping | F bookkeeping + tithe income |
| V3.16 | Cooldowns + dawn economics | Reference | Per-dawn reset cadence per resource |
| V3.17 | OPTIMIZE → ROLL → NARRATE | Pattern | Player decides first, math resolves, roll adds variance |
| V3.18 | 5 dawn-action archetypes | List | Sovereign / Diplomat / Tyrant / Seducer / Hermit |
| V3.19 | 8 verification standards | Checklist | Self-audit before merge |
| V3.20 | 2 worked examples | Worked-out | L36 routine dawn + L42 triggered dawn |

**22 sub-mechanics total.** If your overlay has fewer, you are below the V3 floor.

## Stat-block vocabulary (V3.0 — the canonical split)

| Short | Long | Range | Player-visible? |
|---|---|---|---|
| L | Character level | 1-50 | YES |
| DHP | Divine HP | 50-1M | NO |
| DAC | Divine AC | 18-50 | NO |
| DPP | Divine Power Pool/day | 100-100k | YES |
| DAIR | Divine Attack Impact Rating | 0-100 | NO |
| DLR | Divine Leverage Rank (DC) | 1-10 | YES |
| F | Followers | 0-1M | NO |
| Repr | Reputation Die | d4→d20 | YES (modifier only) |
| RP | Repr Points | 0-100 | NO |
| PS | Pantheon Surveillance | 6 bands | NO |
| D | Dissonance per-faction | 0-100% | YES (HUD bars) |
| AT | Action Tier | 0-3 | YES |

**Rule:** if the player cannot optimize it, do not surface it as a number. Surface as narrative only ("your divine form resists wounds that would kill armies").

## The OPTIMIZE → ROLL pattern (V3.17 — non-negotiable)

For every god-tier campaign turn:

1. **OPTIMIZE phase** — Player uses the Per-dawn menu to pick AT action. Math runs deterministically.
2. **ROLL phase** — Math resolves most of the chain (V3.10). Roll only at the boundary.

The player NEVER rolls first then chooses. That breaks the meta-game.

## Chosen + Avatar (V3.13.1 + V3.13.2)

**Chosen Creation:**
- 250 DPP (one-time, AT-3 Legendary Action)
- 50 DHP minimum binding (drawn from god's pool)
- Cap: floor(L/5) - 4 (L26: 1, L36: 3, L46: 5)
- Death/resignation: binding snaps; DHP lost permanently
- Absorption: AT-3 Major Divine Action; up to 50% DHP reclaimed
- DC 25 Divine Influence check (d20 + DAC vs DC 25)
- Loyalty ±5 modifier on contested roll

**Avatar Creation:**
- 500 DPP (one-time, AT-3 Legendary Action)
- 100 DHP minimum binding
- Cap: floor(L/10) - 1 (L26: 1, L36: 2, L46: 3)
- Discorporation (HP=0): binding snaps; DHP lost permanently
- Absorption: 100% DHP reclaimed, no resistance (extension of will)

## Setting-agnostic naming (P20 from SKILL.md)

When you replace setting-specific entity names with generic placeholders, use clean single-token names that do NOT contain the original entity as a substring:
- `the Weave-archon (replace per setting)` → becomes `the Arcanelord`
- `the Shadow-Queen (replace per setting)` → becomes `the Shadowlord`
- `the Vigilant (replace per setting)` → becomes `the Sentinel`
- `the Justiciar (replace per setting)` → becomes `the Lawbringer`
- `the Spider-Queen (replace per setting)` → becomes `the Arachne`

Always run `grep -n '(replace per setting)'` after replacement to catch artifact phrases with >1 placeholder marker.

## Worked example structure (V3.20)

Each worked example MUST include:
- Trigger description (what's happening in the scene)
- Player-visible stat sheet (L, DPP, DLR, Repr, AT remaining, D-faction bars, Chosen/Avatar held)
- Per-dawn menu (4-6 options with explicit DPP/AT costs and consequences)
- OPTIMIZE phase (player picks one; math runs)
- ROLL phase (d20 rolls + bracket math)
- NARRATE phase (third-person narrative; no "you feel X" tells)
- Post-resolution state update

## What V3 explicitly DOES NOT include

- Mortal-level (L1-19) mechanics — 5e default is sufficient
- Multiverse / sovereign-tier mechanics — disabled separately
- D&D-specific entity names in default text — Appendix A only
- Backend code (per /zfc) — prompt-only
- Real-LLM evidence (separate from the spec) — verified via agy CLI per P22
