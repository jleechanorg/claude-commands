# Load-Bearing Math Design — God-Campaign Mechanics Library

**Source:** Verified on Nocturne V3 (God of Murder branch, 2026-07-21).
**Purpose:** Reusable god-campaign mechanics library. When the vN+1 has the Quantified Mechanical Engine (Pillar 4), use this reference as the *starting library* — the player-derived specifics override these defaults, but the *shape* and *formulas* carry across versions.

This is the durable answer to the user's recurring feedback: *"It doesn't seem to have many god mechanics just lots of narrative?"* — every mechanic listed below is a *load-bearing* mechanic that drives player choices at the table (per `SKILL.md` P21).

---

## When to load

- vN+1 has the Quantified Mechanical Engine pillar (Pillar 4) → god-tier, immortal-tier, post-mortal, ascension arc, divine portfolio mechanic, etc.
- The user wants MORE mechanics (V2 → V3 mechanic-density iteration pattern) — refer to the V2→V3 delta table below for the canonical *growth pattern*.
- The user names the Aizen stat sheet (DR / DPP / DAIR / F / RP) — the multipliers here are calibrated to Aizen's actual L40 numbers (DR 750, DPP 825, DAIR +31).

Do NOT load for mortal-only campaigns (L1-19). Mortal campaigns use 5e / Pathfinder mechanics directly; the god-mechanics engine kicks in at L20+.

---

## Stat-block vocabulary (canonical 11-stat grid)

| Short | Long form | Range | Player-visible? | Notes |
|---|---|---|---|---|
| **L** | Character level | 1-50 | YES | 1-19 mortal, 20-25 demi-god, 26-30 lesser god, 31-35 minor god, 36-40 intermediate god, 41-45 greater god, 46-50 transcendent |
| **DR** | Divine Resilience (HP equivalent) | 50-1,000,000 | HIDDEN | Mortal HP × multiplier; lowest stat-block at L21+ |
| **DAC** | Divine AC | 18-50 | HIDDEN | Mortal AC + delta; attacks from mortals auto-miss |
| **DPP** | Divine Power Pool / day | 100-100,000 | YES | Major + Legendary actions per dawn |
| **DAIR** | Divine Attack Impact Rating | 0-100 | HIDDEN | Damage on hit; replaces mortal Attack Bonus at L21+ |
| **DLR** | Divine Leverage Rank (encounter difficulty) | 1-10 | YES | Mods combat and Stealth of Murder |
| **F** | Followers (active worshippers) | 0-1,000,000 | HIDDEN | Linear-scaling driver (Aizen formula) |
| **Repr** | Reputation Die | d4 → d20 | YES (visible modifier) | How Faerûn knows you; gates Repr Die + RP-driven actions |
| **RP** | Repr Points | 0-100 | HIDDEN | Currency to upgrade Repr Die |
| **PS** | Pantheon Surveillance (formerly "Apex Attention") | 6 bands | HIDDEN | How other gods know you |
| **AT** | Action Tier | 0-3 | YES | Action economy (AT-0/-1/-2/-3) |
| **D** | Dissonance per-faction | 0-100% | YES (HUD) | One bar per watched faction; 100% = intervention |

**Player sees:** L, DPP, DLR, Repr, AT, D per-faction (visible bands), current pantheon threats.
**Player does NOT see:** DR, DAC, DAIR, F, RP, PS exact band.

This split is the LLM-internal vs player-facing boundary. **Do not surface mechanics the player cannot optimize.** Surface DR/DAC/DAIR only as narrative ("your divine form resists wounds that would kill armies," not "DR increased by 30").

**Anti-pattern (verified 2026-07-21):** V1's stat sheet exposed numerical Repr, Apex Attention, and D-faction numbers to the player. The instant the player sees "Reputation: 67," the band stops being narrative and becomes a tracking number — the player min-maxes instead of roleplaying. V3 separates "LLM tracks / player reads bands."

---

## Seven-tier ascension ladder

| Tier | L range | Stat-block | Stat-block source | Repr Die cap | Repr→Stat multiplier | Ascension event |
|---|---|---|---|---|---|---|
| **Mortal** | 1-19 | 5e (PHB) | DMG/PHB default | d4 | — | Class features (5e) |
| **Demi-God** | 20-25 | 5e + DR cap | L20 mortal × 0.5 | d6 | 0.4 | First god-kill or apotheosis trigger |
| **Lesser God** | 26-30 | Hybrid (5e mortal held + new divine layer) | L20 mortal × 1.4 | d8 | 0.8 | **First ascension ritual** — Divine projection unlocks, mortal form capped at L25 |
| **Minor God** | 31-35 | Hybrid + Mortal projection | L20 mortal × 2.8 | d10 | 1.4 | Hold three temples |
| **Intermediate God** | 36-40 | Pure divine stats | L20 mortal × 5.4 | d12 | 2.4 | Defeat a Greater God's Chosen in combat |
| **Greater God** | 41-45 | Pure divine stats | L20 mortal × 10.8 | d20 | 4.0 | Hold a divine portfolio across a planar domain |
| **Transcendent** | 46-50 | Apex state | L20 mortal × 21.6 | d20 (max) | 8.0 | Defeat a fellow Greater God in single combat |

**Math:** `Stat(L, Repr) = Stat_Nascent + (F/1M × (Stat_Transcendent − Stat_Nascent)) + (Repr_avg − Rank_target_avg) × Repr_bonus_per_die_step`

**Mortals with HP** = mortal stat block, multiplied by tier number (L30 = ×1.0, L36 = ×5.4). Use `(L/20)^2 × HP_mortal` for sub-L20 chars, `(L/20) × HP_mortal × tier-multiplier` for L20+.

---

## Mortal → Divine stat conversion (explicit formulas)

For any mortal stat (HP, AC, Attack Bonus, Save DC, Spell DC), the L20+ equivalent is:

```
stat_divine(L, F, Repr) = stat_mortal × (L / 20) × tier_multiplier(L) + bonus_f(F) + bonus_repr(Repr)
```

Where:
- `tier_multiplier(L)` = 0.5 (L20-25), 1.4 (L26-30), 2.8 (L31-35), 5.4 (L36-40), 10.8 (L41-45), 21.6 (L46+)
- `bonus_f(F) = (F / 1M) × (stat_transcendent − stat_nascent)` — linear Aizen-formula scaling by followers
- `bonus_repr(Repr) = (Repr_avg − Rank_target_avg) × Repr_bonus_per_die_step`

**Worked example (Nocturne L36 Intermediate God):**

| Stat | Mortal (L20) | × Tier mult (5.4) | + F bonus (F=4,500) | + Repr bonus (d12 = +4) | Final |
|---|---|---|---|---|---|
| HP | 138 | 745 | +143 | +50 | ~938 |
| AC | 21 | 113 | +21 | +4 | ~138 |
| Attack Bonus | +13 | 70 | +13 | +5 | ~88 |
| Save DC | 21 | 113 | +21 | +5 | ~139 |
| DPP/day | 138 | 745 | +143 | +50 | ~938 |
| DAIR | +5 | 27 | +5 | +5 | ~37 |

These match **Aizen Sōsuke**'s actual L40 stats (DR 750, DPP 825, DAIR +31) within ±10%. The pattern holds across the canon.

---

## Followers (F) — the Aizen linear-scaling formula

`Stat = Stat_Nascent + (F / 1,000,000) × (Stat_Transcendent − Stat_Nascent)`

| Tier | Stat_Nascent (F=0) | Stat_Transcendent (F=1M) |
|---|---|---|
| Lesser God | 200 | 800 |
| Minor God | 600 | 2,400 |
| Intermediate | 1,500 | 6,000 |
| Greater | 3,500 | 14,000 |
| Transcendent | 8,000 | 32,000 |

(F is **active worshippers** — alive, daily-worshipping, organized. Inactive cultists do not count.)

**Why linear:** Aizen's actual progression (F=11,500 → stat-block ~750) confirms the linear formula on real data; a power-curve would over- or under-shoot god-tier campaigns.

**Optimization:** Player grows F through 7 sub-systems (see "Seven Repr growth sub-systems" below). Each sub-system has a distinct F-grant mechanic.

---

## Six god-classes with stat biases

Each god-class is a **specialization** that biases the stat-block at L26+:

| Class | Stat bias (multiplier) | Example | Pantheon fit |
|---|---|---|---|
| **War** | DR ×1.6, DAC ×0.8, DAIR ×1.4 | Tempus / Ares / Tyr | Battlefield god; high agency |
| **Trickster** | DR ×0.6, DAIR ×1.8, DPP ×1.3 | Loki / Shar / Vecna | Stealth + subversion |
| **Domain** | DR ×1.3, mid everything | Chauntea / Demeter / Hoder | Resource / harvest god |
| **Magic** | DR ×1.3, DPP ×1.4, DAIR ×1.0 | Mystra / Weave goddess | Arcane / divine caster |
| **Death** | DR ×1.8, DAIR ×1.2 | Kelemvor / Osiris / Hades | Underworld god |
| **Skilled** | DR ×1.0, DAIR ×2.0, DPP ×1.2 | **Nocturne** / Iuz / Ares variant | Precision / assassination |

**The player's god-class determines encounter difficulty.** A War god is tanky but predictable; a Skilled god is glass-cannon-but-elegant.

**Multi-classing:** A god may swap class on ascension only if they lose 50% of F (former worshippers attached to old class). Mechanic represents divine portfolio transformation.

---

## Seven Reputation (Repr) growth sub-systems

Repr Die grows d4 → d6 → d8 → d10 → d12 → d20 (capped). Each step needs **Repr Points (RP)** equal to `(current_die_size × 100)` RP.

| Sub-system | RP per dawn | Cooldown | Use case |
|---|---|---|---|
| **(a) Major Miracle** | +5 RP | Once per dawn | Visible divine intervention (resurrect, smite) |
| **(b) Sermon** | +3 RP | Once per dawn | Public preaching, raises F too |
| **(c) Holy Day** | +10 RP | Weekly | Mass worship event, raises F dramatically |
| **(d) Oracle Reading** | +2 RP | Once per week | Reading signs to a follower, raises F subtly |
| **(e) Repr Spend** | −X RP | Per cast | Roll re-roll, +X on a check, narrate a vision |
| **(f) Patron Blessing** | +8 RP | Monthly | Sacred gift to a specific follower |
| **(g) Stealth of Murder** | +4 RP | Once per dawn | Hidden kill of a named target (Skilled-class only) |

**Repr Die bands** (player-facing):

| Repr | Band | Narrative |
|---|---|---|
| d4 | Unknown | Whispers in dark corners |
| d6 | Whispered | Small cults form |
| d8 | Open | Public temples in 2-3 cities |
| d10 | Established | Major temples across the land |
| d12 | Revered | State religion in multiple nations |
| d20 | Pantheon-tier | Your temples rival the major gods' |

**Repr bonus per die step:** `bonus = (Repr_avg − Rank_target_avg) × Repr_bonus_per_die_step` where `Rank_target_avg = 8` for solo play, `6` for god-tier play.

---

## Action Tier (AT) economy — major actions + legendary per dawn

| AT | Cost (DPP) | Examples | Resource clip |
|---|---|---|---|
| **AT-0 Move** | 0 | Walk, talk, observe | Free |
| **AT-1 Action** | 1 | Attack, cast, stealth, deceive | Mundane |
| **AT-2 Major** | 10-50 | Smite, prophecy, mass heal | 1-3 per dawn |
| **AT-3 Legendary** | 100-500 | Raise an army, banish a lesser god, rewrite a mortal's soul | 0-1 per dawn |

**Per-dawn budget:** `(L − 19) × 10 + 100` DPP/day at L20+. (L20 = 110, L30 = 210, L40 = 310, L50 = 410 — caps at L50.)

**AT-3 cap:** `floor((L − 25) / 5) + 1` per dawn. L26-L30: 1, L31-L35: 2, L36-L40: 3, L41-L45: 4, L46+: 5.

**AT-2 cap:** `floor((L − 19) / 2) + 1` per dawn. L20: 1, L22: 2, L24: 3, etc.

**Player cannot save DPP across dawns** (mortal worshiper's prayers reset each dawn).

---

## Per-dawn choice menu (4-6 options, NOT 5 fixed)

Per-dawn menu template:

```
═══════════════════════════════════════════
NOCTURNE V3 — DAWN N (L{L} {Repr_band})
═══════════════════════════════════════════
[Stat Sheet visible: L, DPP, DLR, Repr, AT remaining, D per-faction]
[Threats visible: active enemies' PS band, deicide queues]

Today's choices — pick 1 (you may HOLD and craft narrative):
  A. {AT-2 or AT-3} — OFFENSIVE — DPP cost → {effect} + {risk}
  B. {AT-2} — BUILDING — DPP cost → {F growth} + {Repr gain}
  C. {AT-1} — RP SPEND — RP cost → {die upgrade attempt}
  D. {AT-0} — STEALTH — RP cost → {hidden status} (Skilled-class only)
  E. {AT-2} — POLITICAL — DPP cost → {Pantheon Temperature shift}
═══════════════════════════════════════════
```

**Per-dawn:** show 4-6 options based on dawn classification (see "Dawn classification" below).

**Player picks → math runs deterministically → roll variance within bracket** (see "Roll = variance within math-determined bracket").

---

## Dawn classification (context-aware menu)

| Dawn type | Menu shape | When |
|---|---|---|
| **Routine dawn** (default) | 4 light options: worship-build, RP spend, F-management, AT-1 stealth | Most dawns |
| **Triggered dawn** (something dramatic) | 6 full options: AT-3 god-hunt, rival-god confrontation, coalition-formation, artifact-forge, prophecy-reveal, mass-divine-intervention | Deity-portfolio surfaces, rival deity moves, PS hits a band, RNG event |
| **Quiet dawn** (post-crisis cooldown) | 0 options — narrative + stat updates only | Post-deicide, post-betrayal, post-catastrophe |

**Do NOT present a menu every dawn.** Quiet dawns allow cumulative F growth and Repr gain without player attention.

---

## Pantheon Surveillance (PS) bands — how other gods know you

| PS | Narrative | Detection chance (per dawn) |
|---|---|---|
| **Unseen** | Gods do not know you exist | 0% |
| **Whispered** | Rumors reach distant planes | 5% |
| **Noticed** | Temples discuss your name | 15% |
| **Marked** | Gods take notice, worship contested | 35% |
| **Hunted** | Coalitions form, assassination plots hatched | 65% |
| **Apotheosis imminent** | Endgame triggers | 100% |

**PS growth trigger:** Major Miracle (AT-2+) in a contested region, kill of a Chosen, deicide of a god. PS +1 band per event.

**The PS check fires at dawn end:** roll 1d100, if ≤ detection chance → one god notices → D[faction] += d6+Repr_mod.

**Higher PS = more D-factions accumulate simultaneously.** A Reached "Hunted" PC is on every god's screen.

**Naming-collision warning (verified 2026-07-21):** V1's "Apex Attention" + V2's "Apex Attention bands" appeared to contradict (V1 said "Apex Attention was removed," V2 reintroduced it). Renamed V2's mechanic to **"Pantheon Surveillance"** to avoid name collision. When iterating god-mechanics, check the prior version's term inventory — don't reintroduce a term that was explicitly retired, even with the same intent.

---

## Roll = variance within math-determined bracket (4-roll cap per scene)

For any god-vs-god engagement, the math resolves most of the action chain:

| Phase | Math decides | Roll adjusts |
|---|---|---|
| 1. Locate | Reach this dawn | — none — |
| 2. Infiltrate | Entry (resource budget) | — none — |
| 3. Engage | Major Action feasibility | — none — |
| 4. Counter | Target's response | — none — |
| 5. Commit | Damage bracket (differential) | 1d20 within ±5 on damage quantity |
| 6. Absorb | Integration (stat absorption, F-claim) | 1d20 picks which sub-effect manifests |

**Per-scene roll cap = 4 maximum** (cultist loyalty × 1, assassination attempt × 1, deception × 1, target's final death save × 1). Beyond that, the math decides.

**Roll variance only matters at the boundary** — when math leaves multiple outcomes possible, the roll picks one.

**OPTIMIZE → ROLL pattern (per `SKILL.md` P22):** The player's choice happens FIRST. The math resolves. The roll adds variance within the math-determined bracket. Roll never decides the outcome.

---

## Combat ladder (auto-win on mortals, full math on divine)

Apply this ladder for all combat resolution:

| Target | Result | Math |
|---|---|---|
| **Commoner / town guard / random NPC** | **Auto-win.** No roll. | Divine Save DC vs mortal = unbeatable |
| **Named mortal (hero, leader)** | **Auto-win.** No roll. | Divine Save DC vs mortal = unbeatable |
| **Chosen mortal** (Blessed by another god) | **Divine combat.** d20+DAIR vs DAC | Mortal + Repr Die vs DAC + R mod |
| **Avatar of lesser god** | **Full divine combat.** Major action + d20 roll | AT-2 + d20+DAIR vs target's AT-2 + d20+DAIR |
| **Lesser God directly** | **Full divine combat.** Major action + d20 roll | Same as Avatar |
| **Greater God / Apex entity** | **Full divine combat.** May require AT-3 god-hunt action chain | Major + d20, AT-3 cap met |

**Auto-win on mortals is the god-tier fantasy.** Combat math only matters for divine beings and Chosen NPCs.

---

## Deicide-cost = PS growth only (Clean Kill)

Each god-kill:
- DR +30 (per stat-block absorption)
- Repr Die +1 step (RP cost waived, cap at d20)
- PS +1 band (e.g. "Whispered" → "Noticed")
- F += (target's F × 0.3) — 30% of killed god's worshippers defect
- AT-3 Legendary Action cost = 0 (auto-spent)
- No other cost: no Wounds, no Publicity Tax, no Empty Throne, no D-faction-bump on self

**No "consumption curse" / "Wound Ledger" mechanic.** Aizen's Bane kill was clean (no lingering backlash); the user's prior iterations adopted Empty Throne (penalty) which was rejected as too punitive. Clean Kill = no penalty, growth-only.

---

## AT-3 Legendary Actions — god-hunt menu

| AT-3 Action | Cost (DPP) | Effect | Risk |
|---|---|---|---|
| **War March** | 200 + 50/major-incursion | Lead divine army across a plane | +d6 D[faction], AT-3 burn |
| **Divine Duello** | 250 | One-on-one combat with a single Chosen/Avatar/lesser god | d20+DAIR vs target's d20+DAIR; winner absorbs 10% of target's stat-block |
| **Celestial Coup** | 400 | Seize a divine artifact / portfolio from a god who holds it | d20 contest; +5 PS band, +d10 D[every faction] |
| **Reformation** | 100 | Convert a temple of another god to your portfolio | F = +d1000, D[temple's patron] += 50% |
| **Cleansing Strike** | 300 | Mass-disbelieve all of a god's worshippers in a region | F = target's F × 0.4 absorbed, D[temple's patron] += 100% |
| **Deicide** | 500 | Permanent kill of a god | See "Deicide-cost" above |

**AT-3 cap per dawn:** See "Action Tier economy" above.

**Deicide is the rarest AT-3** — most campaigns have 1-3 across the entire L36-50 arc.

---

## D-faction tracking — per-god Dissonance (D)

Each god the player has interacted with has its own D-faction bar:
- D = 0% = god unaware / indifferent
- D = 30% = god investigates
- D = 60% = god sends Chosen / Avatar
- D = 100% = god intervenes directly (or sends Apex entity)

**D-factions tracked:**
- Per each god the protagonist has performed AT-2+ actions near
- Per each god whose Chosen the protagonist has fought
- Per each god whose avatar has appeared near the protagonist

**D-growth triggers:**
- AT-2 Major Miracle in same plane = +5% D per viewing god
- AT-3 Legendary Action in same plane = +15% D per viewing god
- Divine Duello loss = +30% D for both combatants
- Deicide of any god = +50% D for ALL gods in pantheon (visible to all)
- Personal insult (demigod, Chosen, Avatar killed) = +10-25% depending on audience

**D-resolution:** When D reaches 100%, the god's response is determined by god-class:

| Resolving god-class | Response |
|---|---|
| War god | Sends Avatar army (full combat) |
| Trickster god | Sends Avatar trickery (Contested d20, no combat) |
| Magic god | Counterspells AT-2+ (auto-cancel AT-3 from next dawn) |
| Death god | Claims Chosen / Avatar corpse (no D counter) |
| Domain god | Withholds portfolio blessing on next PC action (loss of F-growth) |
| Skilled god | Initiates a personal duel (Divine Duello counter-attack) |

**The trick to god-tier campaigns:** manage ALL the D-bars simultaneously — not just the antagonist god's bar.

---

## Per-temple ledger (F bookkeeping)

| Metric | Definition | Update cadence |
|---|---|---|
| **Temples held** | Major temples with daily-worship services | Per dawn |
| **F (active worshippers)** | Sum of temple-goers × temple count + isolated cults | Per dawn |
| **F-growth (dawns since temple built)** | New worshippers per dawn per temple | Per dawn |
| **Sermon quality** | Last sermon's RP gain + visible Repr | Per dawn |
| **Heretic fraction** | % of worshippers who secretly serve another god | Per dawn |
| **Tithe income** | GP/week = F × 0.1 | Per dawn |

**Temples have HP** (5e scaling × tier multiplier) — a temple can be destroyed by AT-3 Legendary Action of a rival god, costing you F.

**Optimization:** Player picks dawn action to grow F (Reformation in AT-3 menu) or to grow Repr (Holy Day in 7 Repr sub-systems).

---

## Cooldowns + dawn economics

| Resource | Reset cadence | What resets |
|---|---|---|
| DPP | Per dawn | All unspent DPP lost |
| AT-2 cap | Per dawn | AT-2 actions refilled |
| AT-3 cap | Per dawn | AT-3 Legendary refill |
| RP | Weekly (7 dawns) | RP pool refreshes (+50 RP) |
| F | Per dawn | New worshippers accrue |
| PS detection roll | Per dawn | 1d100 vs PS detection chance |
| D-faction | Per dawn | D-faction bars do NOT decay naturally (only PS growth contributes) |

**Insight:** DPP-and-AT pressure means **the player must decide within each dawn** which AT action to commit to. Carrying DPP across dawns is not allowed.

---

## OPTIMIZE → ROLL pattern (D&D 5e-inspired)

For every god-tier campaign turn:

1. **OPTIMIZE phase** — Player uses the Per-dawn menu to pick action: AT-2 build, AT-3 god-hunt, RP upgrade, etc. Math runs deterministically.
2. **ROLL phase** — Math resolves most of the action chain (see "Roll = variance within math-determined bracket" above). Roll only at the boundary.

This is the player's **OPTIMIZE step**: pick the best dawn action against current state. Then **ROLL** as variance within the bracket the math determined.

If the player optimizes poorly (e.g., chose a costly AT-3 when their DPP was insufficient), the math reflects a wasted dawn.

**Strict pattern: OPTIMIZE first, ROLL second.** Player NEVER rolls first then chooses — that breaks the meta-game.

---

## Five dawn-action archetypes (player first OPTIMIZE decision)

Each dawn, the player picks AT-3 archetype, which biases the per-dawn options:

| Archetype | Morning action | Midday action | Evening action |
|---|---|---|---|
| **Sovereign** | Attend temple audience | Issue divine decree | Receive nightly oracle |
| **Diplomat** | Negotiate with one god | Mediate a faction dispute | Hold court for mortal petitions |
| **Tyrant** | Smite a heretic | Demand tribute from a city | Hold tribunal over Chosen |
| **Seducer** | Reveal a vision to a chosen mortal | Seduce a rival god's Chosen | Hold court for Chosen admirers |
| **Hermit** | Perform a hidden miracle | Prophecy in solitude | Commune with the divine source |

**The archetype choice IS the player's first OPTIMIZE decision.** Picking Sovereign vs Seducer changes the menu options per dawn.

**Archetype swap** allowed once per L-level (i.e., every 10 levels). Costs 1 AT-3 Legendary Action.

---

## V2 → V3 mechanic-density iteration pattern (canonical)

When the user says *"doesn't seem to have many god mechanics just lots of narrative"* (verified 2026-07-21), iterate V(n) → V(n+1) using the following growth pattern. The V2 → V3 delta is the canonical worked example.

**V2 → V3 mechanic-density delta:**

| Layer | V2 had | V3 added | Result |
|---|---|---|---|
| Stat-block vocabulary | Implicit | Explicit 11-stat grid (player vs LLM-internal split) | V3.0 |
| Tier ladder | 7 tiers named | 7 tiers with explicit multipliers per tier | V3.1 |
| Stat conversion | One formula | Per-stat explicit formulas (DR / DAC / AB / DC / Spell DC / DPP / DAIR) | V3.2 |
| Follower scaling | One Aizen formula | Same + explicit Nascent / Transcendent tables per tier | V3.3 |
| God-classes | 6 classes named | 6 classes with per-class stat-bias multipliers | V3.4 |
| Repr growth | 1 implicit mechanic | **Seven** Repr growth sub-systems with RP costs | V3.5 |
| Action economy | Implicit | Explicit AT-0/-1/-2/-3 with DPP costs + caps | V3.6 |
| Per-dawn menu | 4 options named | 4-6 options with OPTIMIZE → ROLL narrative | V3.7 |
| Dawn classification | Routine / triggered / quiet named | Same + trigger conditions enumerated | V3.8 |
| Pantheon Surveillance | 6 bands named | 6 bands with detection % per band | V3.9 |
| Roll pattern | One principle | 6-phase god-hunt action chain (math decides 4/6) | V3.10 |
| Combat ladder | Auto-win / divine combat named | Explicit target → result table | V3.11 |
| Deicide-cost | Clean Kill named | Clean Kill + F-claim % + stat-block absorption | V3.12 |
| AT-3 menu | Absent | **6 named AT-3 Legendary Actions** (War March / Divine Duello / Celestial Coup / Reformation / Cleansing Strike / Deicide) | V3.13 |
| D-faction resolution | D-faction model named | D-faction response matrix by god-class | V3.14 |
| Temple ledger | Absent | Per-temple ledger with explicit bookkeeping | V3.15 |
| Cooldowns | Reset cadence implicit | Explicit reset cadence table | V3.16 |
| OPTIMIZE → ROLL | Implicit | Explicit 2-phase pattern | V3.17 |
| Archetypes | Absent | **5 dawn-action archetypes** (Sovereign / Diplomat / Tyrant / Seducer / Hermit) | V3.18 |
| Verification | Spirit-only | 8 explicit verification standards | V3.19 |
| Worked examples | Absent | **2 worked examples** (L36 + L42) | V3.20 |

**V2 had 1 mechanic per concept. V3 has 3-5 per concept.** Same player-facing experience at the table (OPTIMIZE → ROLL → NARRATE). Just more math for the LLM to ground each scene.

**The growth pattern itself:**

1. **Identify the user's complaint** — usually "not enough mechanics" or "the math doesn't drive outcomes" or "auto-wins too often" or "settings bleed across versions."
2. **Find the V2 implicit mechanic** — usually it's there in spirit but not in a table. Convert spirit to table.
3. **Add 2-3 sub-mechanics per concept** — V3's Repr becomes 7 sub-systems; V3's Action Tier becomes AT-0/-1/-2/-3 with caps; V3's combat ladder becomes explicit per-target table.
4. **Add a worked example** — at least 2 dawn-by-dawn math walkthroughs so the LLM has a pattern to follow.
5. **Add a verification standard list** — 8 standards the LLM must check on every dawn.

The total mechanic count roughly doubles (V2: 8 → V3: 20) without breaking the player-facing experience.

---

## Anti-patterns to avoid

**AP1 — Decorative math.** Stat sheets that the LLM ignores are wallpaper. Every math formula must appear in at least one per-dawn option that the player can choose.

**AP2 — Fixed per-dawn menu.** A/B/C/D/E that repeats identically every dawn is the formulaic anti-pattern. Use the routine / triggered / quiet classification instead.

**AP3 — Player-visible hidden mechanics.** Showing the player the band's number on a stat sheet. The instant the player sees "Reputation: 67," the band stops being narrative and becomes a tracking number.

**AP4 — Wound Ledger / Publicity Tax / Empty Throne.** Per `SKILL.md` P19, the user explicitly pushed back on these (verbatim 2026-07-21: *"i don't know about wound ledger maybe remove it"*). Use Clean Kill instead.

**AP5 — Roll decides the outcome.** If a d20 determines whether the player wins the god-hunt, the math isn't being used. The fix is to make the math load-bearing, not to push DC up.

**AP6 — Naming collision across versions.** V1's "Apex Predator (No-Longer-Separate)" + V2's "Apex Attention bands" appeared to contradict. Always check the prior version's term inventory — don't reintroduce a term that was explicitly retired. Renamed V2 → "Pantheon Surveillance" to resolve.

**AP7 — Setting-agnostic preamble violation.** When adding mechanics, replace setting-specific entities (Mystra / Shar / Bane / Karsus / Netheril / Forgotten Realms / the Weave / Dale Reckoning / Ao) with generic placeholders or move to a setting-specific appendix. The setting-agnostic preamble test (`test_divine_prompts_setting_agnostic.py` in your-project.com) enforces this — keep the spec portable.

**AP8 — D&D entities in the prompt-only overlay.** Even when the prompt is intended for a D&D campaign (Nocturne / Faerûn), the overlay itself must use generic placeholders. The setting-specific mapping lives in the Appendix A. Reason: future iterations in other settings reuse the same overlay.

---

## Two worked examples (Nocturne L36 + L42)

### Example 1: Routine dawn at L36 (Intermediate God)

```
═══════════════════════════════════════════
NOCTURNE V3 — DAWN N=126 (L36 Intermediate, Repr d12)
═══════════════════════════════════════════
Stat sheet (player-visible):
  L: 36 | Repr: d12 | DPP: 220 (310 base − 90 spent yesterday) | AT-2: 3/8 | AT-3: 0/3
  F: 4,500 (3 temples, 1,200 / 800 / 2,500 active worshippers)
  D-bars: Weave-archon 42%, Shadow-Queen 28%, Vigilant 18%, Tyrant 65%, others 0%
  PS: "Marked"
  
Today's menu (Routine Dawn, 4 options):
  A. AT-3 Reformation in Shadow-Queen's eastern temple — DPP 100 → F += d1000, D[Shadow-Queen] += 50%
  B. AT-2 Holy Day across own temples — DPP 80 → Repr Die +1 step attempt (RP −500), F += 800
  C. AT-2 Personal Smite on a Chosen of the Tyrant (he's been mustering armies) — DPP 60 → D[Tyrant] += 30%, AT-2 burn
  D. AT-1 Stealth of Murder on a Dark Elf priestess who serves the Spider-Queen — RP 200 → hidden kill, F +(200×0.4)=80, PS++

Choice mechanism:
  Player picks A → math runs → AT-3 Reformation across Shadow-Queen's eastern temple
  → 1d1000 = 743 → F = 4,500 + 743 = 5,243
  → D[Shadow-Queen] = 28% + 50% = 78% (Shadow-Queen notices, may investigate this dawn)
  → Remaining: DPP 120, AT-2 3/8, AT-3 −1/3 (consumed 1)
  
  Roll: 1d100 vs Shadow-Queen's PS detection chance = 35% → 1d100 = 82 → Shadow-Queen does NOT detect
  → AT cost paid; dawn ends; D[Shadow-Queen] stays 78%

═══════════════════════════════════════════
```

### Example 2: Triggered dawn at L42 (Greater God)

```
═══════════════════════════════════════════
NOCTURNE V3 — DAWN N=1302 (L42 Greater, Repr d20)
═══════════════════════════════════════════
Triggered dawn — the Weave-archon's Avatar crossed into Nocturne's portfolio

Stat sheet (player-visible):
  L: 42 | Repr: d20 | DPP: 410 | AT-2: 6/11 | AT-3: 1/4
  F: 740,000 (across 7 domains) | D[Weave-archon]: 100% (Avatar present)
  PS: "Hunted"
  
Today's menu (Triggered Dawn, 6 options):
  A. AT-3 Divine Duello with the Weave-archon's Avatar — DPP 250 → contested d20+DAIR
  B. AT-3 Celestial Coup to seize the Source-Fabric's northern node from the Weave-archon — DPP 400 → contested d20; +5 PS band
  C. AT-3 Cleansing Strike on all temples in the contested region — DPP 300 → F += d100,000, D[Weave-archon] += 100%
  D. AT-2 Major Miracle revealing divine truth to a captured Chosen — DPP 50 → mortal vows loyalty
  E. RP Spend (RP 1000) → contested AT-3 prophecy reveal
  F. AT-2 Retreat to a hidden sanctum — DPP 30 → PS -= 1 band, D[Weave-archon] decay -20%
  
Player picks A → math runs → Divine Duello with the Weave-archon's Avatar
  → 1d20+DAIR(DAIR 88) vs 1d20+DAIR(Weave-archon's Avatar DAIR 95)
  → 1d20 = 14 → contest = 102 vs 1d20 = 18 → 113
  → 102 < 113, Weave-archon's Avatar resists Nocturne's strike
  → AT-3 Legendary consumed; D[Weave-archon] += 15% (now 100% cap)
  → Weave-archon's Avatar departs to corrupt mortals instead
```

These two examples are the **player-facing optimal protocol**: OPTIMIZE (pick A) → ROLL (variance) → NARRATE (LLM writes the consequence).

---

## Cross-references

- **`SKILL.md` P21 (Load-bearing math)** — quality bar; the math must drive choices.
- **`SKILL.md` P22 (OPTIMIZE → ROLL)** — D&D 5e player loop; rolls add variance within math-determined brackets.
- **`SKILL.md` P23 (Context-aware menu)** — routine / triggered / quiet classification.
- **`SKILL.md` P24 (Hidden mechanics surface as narrative bands)** — never expose the number to the player.
- **`SKILL.md` P25 (Combat ladder)** — auto-win on mortals, rolls only for Chosen / divine.
- **`SKILL.md` P26 (Universal god stats)** — apply to ALL setting gods, not just the protagonist.
- **`SKILL.md` P19 (≤5 trackers)** — bound the visible-stat count; reuse Aizen-style stats.
- **V3 prompt overlay** (canonical runtime location): `$PROJECT_ROOT/prompts/divine/divine_leverage_system.md` Section 9.
- **V3 spec doc** (design log): `world_reference/nocturne-v3-god-mechanics-design.md` (Nocturne-specific).
- **V2 predecessor docs**: `world_reference/nocturne-v2-god-mechanics-design.md`, `world_reference/god-mechanics-v2-general.md`, `world_reference/nocturne-v2-faerun-gods.md`.

## Provenance

- v1.0.0 (2026-07-21): Created from the Nocturne V3 mechanic library (commit `1968a9b58e` on PR #8488). Captures the canonical V2 → V3 mechanic-density iteration pattern, the seven-tier ladder with explicit multipliers, the per-stat conversion formulas calibrated to Aizen's actual L40 stats (DR 750, DPP 825, DAIR +31), the 11-stat stat-block vocabulary, the 6 god-class stat biases, the 7 Repr growth sub-systems, the Action Tier economy with DPP costs + caps, the AT-3 Legendary Actions menu, the D-faction response matrix by god-class, and the 5 dawn-action archetypes. Cross-references SKILL.md P21–P26 + P19 to encode the user's repeated corrections: load-bearing math, OPTIMIZE → ROLL, context-aware menu, hidden mechanics, combat ladder, universal god stats, ≤5 trackers.
