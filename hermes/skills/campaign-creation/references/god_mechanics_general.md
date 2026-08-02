# God Mechanics — General (System-Agnostic) Specification

*A canonical, setting-agnostic framework for "you are a god" solo campaigns. Works for Forgotten Realms deicide, Wuxia cultivation transcendence, cyberpunk ascended-AI divinity, Naruto tailed-beast sovereign, Marvel cosmic-tier hero, or anime god-of-tyranny arcs. Quantified enough to be mechanically useful, abstract enough to drop into any pantheon.*

---

## Why this exists

Every god-tier campaign Jeffrey has loved (Aizen Godhood Continued, the original Aizen-as-god series, the dark-godtyranny arcs in llm_wiki) shared three structural ingredients that the narrative-heavy successors (e.g. the current God of Murder doc) lost:

1. **Quantified stat blocks** — explicit DHP / DPP / DAIR-style numbers, not vibes
2. **Linear scaling formulas** — "at F followers, my divine AC = base + (F/target × delta)" — math the LLM can compute every scene
3. **Hard bookkeeping layers** — sequence IDs, checkpoint blocks, named subsystems with costs & cooldowns

This file is the **general** version: it has no Faerûn lore, no Forgotten Realms deities, no D&D dice math. Drop it into any setting. Translate DPR/DHP into the setting's idiom ("Dread Tides," "Cult Resonance," "Quantum Influence Pool") but keep the structure.

---

## I. Tiers of Divinity (the 7-Rank Ladder)

A god is not a binary. There are **seven canonical ranks**, each with an explicit numerical budget. Promotion requires both a mechanical trigger AND a narrative milestone (the LLM never promotes based on vibes alone).

| Rank | Title | Mechanical Trigger | Narrative Milestone | Example Archetype |
|------|-------|-------------------|---------------------|-------------------|
| **0** | Quasi-Deity | Consumed a divine spark / merged with an elder entity / ascended an AI core above god-tier threshold | A city or region kneels | Brand-new god (Dark Urge post-Bhaal, Aizen post-Bane) |
| **1** | Minor Ascendant | Held territory for 1 year; built a functioning church with ≥ 100 active worshippers | Your faith has a name, vestments, a calendar | First saint appears |
| **2** | Ascendant | ≥ 1,000 worshippers; survived at least one planar incursion attempt by an intermediate deity | Other gods put you on their meeting agenda | Recognized factional power |
| **3** | Nascent Greater Deity | ≥ 10,000 worshippers; one full god-portfolio absorbed; one full planar realm claimed | The first crusade against you assembles | The gods take you seriously |
| **4** | Lesser Deity | ≥ 50,000 worshippers; survived a coalition assault; an avatar has killed or absorbed an intermediate deity | An avatar of yours holds a planar throne | You are a name in the cosmology book |
| **5** | Intermediate Deity | ≥ 250,000 worshippers; one full pantheon wing (≥ 3 portfolios) under your dominion; a permanent planar fortress | Your avatar stands in council with established gods | Peer of Torm / Mystra / Bane |
| **6** | Greater Deity | ≥ 1,000,000 worshippers; multiple pantheons converted or absorbed; permanent multiversal reach | The gods form a coalition against you personally | You are a tier-1 cosmological actor |
| **7** | Transcendent | ≥ 10,000,000 worshippers AND consensus-driven narrative escalation (you've become a *theme*, not a *being*) | Reality rewrites around your portfolio | Final-form god |

**The formula** (compute current stat at F followers, target 1,000,000):
```
Current_Stat = Base_Rank3_Stat + ((F / 1,000,000) × (Rank6_Stat - Rank3_Stat))
```
Use this for every divine stat below. The LLM computes it explicitly each scene.

---

## II. The Divine Stat Block (system-agnostic)

Translate the names to whatever fits the setting. The numbers stay.

| Stat | Abbreviation | What it Measures | Scaling Rule |
|------|--------------|------------------|--------------|
| **Divine HP** | DHP | HP equivalent for god combat. Total damage the god can absorb before avatar-discorporation | 150 → 300 → 750 → 1,000+ → 1,750 |
| **Divine Armor Class** | DAC | Defense vs divine attacks. Base + DEX + flat deflection bonus | 20 → 22 → 25 → 25+ → 25 |
| **Divine Power Pool** | DPP | Daily resource pool for major divine actions. Regenerates each dawn | 50 → 200 → 825 → 1,000+ → 1,825 |
| **Divine Attack / Influence Roll** | DAIR Mod | Attack bonus + influence DC mod vs other deities | +15 → +20 → +31 → +25+ → +56 |
| **Divine Legendary Resistances** | DLR | Per-day auto-pass on save-or-die effects | 1 → 3 → 4 → 5 → 9 |
| **Primary Divine Damage** | PDD | Base damage die + multiplier when DAIR hits another god | 10+(1d20×2) → 20+(1d20×3) → 80+(1d20×5) → 30+(1d20×5)+ → 110+(1d20×10) |

**Per-tier table** (use exactly this; no rounding, no reinterpretation):

| Rank | DHP | DAC | DPP/day | DAIR Mod | DLR | PDD |
|------|----|----|---------|----------|-----|-----|
| 0 Quasi | 75 | 18 | 25 | +10 | 0 | 5+(1d20×1) |
| 1 Minor Ascendant | 150 | 20 | 50 | +15 | 1 | 10+(1d20×2) |
| 2 Ascendant | 225 | 21 | 125 | +18 | 2 | 15+(1d20×2) |
| **3 Nascent Greater** | **750** | **25** | **825** | **+31** | **4** | **80+(1d20×5)** |
| 4 Lesser | 300 | 22 | 200 | +20 | 3 | 20+(1d20×3) |
| 5 Intermediate | 500 | 23 | 400 | +23 | 3 | 30+(1d20×4) |
| 6 Greater | 1,000+ | 25+ | 1,000+ | +25+ | 5+ | 30+(1d20×5)+ |
| 7 Transcendent | 1,750 | 25 | 1,825 | +56 | 9 | 110+(1d20×10) |

> **Note on the table:** Rank 3 (Nascent Greater) outscales Rank 4 (Lesser) and Rank 5 (Intermediate) intentionally. A *nascent* greater deity holds raw power well above its rank position because it just absorbed a major god's essence. As followers grow, the power spreads out — Rank 6 / 7 are stronger, but Rank 3 is the most *concentrated* form.

---

## III. Portfolio — the Conceptual Domain

Every god owns one or more **portfolios** — abstract concepts whose authority the god holds. A god without a portfolio is a blank power battery; a god with a clear portfolio is a **functional cosmological actor**.

**Portfolio expansion rules:**

- **Starting portfolio** (at ascension): 1 concept (e.g. Murder, Tyranny, Magic, the Moon)
- **Rank 3 (Nascent Greater):** 2 concepts (your starting + one absorbed from a defeated god)
- **Rank 5 (Intermediate):** 3 concepts
- **Rank 6 (Greater):** 5 concepts
- **Rank 7 (Transcendent):** Unlimited (you are a theme, not a being)

**Portfolio mechanics in play:**

1. **Portfolio Influence Roll:** Any action that lies *within* your portfolio automatically counts as if rolled with a **+10 bonus** (on top of DAIR Mod). You bend the concept to your will.
2. **Portfolio vs Portfolio:** When two deities contest on overlapping portfolios, the higher-ranked deity wins *by default* (DC = 100 auto-save for the loser, but the winner must spend 150 DPP to assert it — this is the cosmic "no, this is MY domain" assertion).
3. **Hidden Dissonance:** *Per-faction.* Each worshipper faction experiences your portfolio slightly differently. This is the setting-agnostic version of the **dissonance hidden, per god faction versus overall** rule you asked for in 1784507599 — the LLM must not collapse all factions into one shared reading.
4. **Portfolio Decay:** A portfolio you do not actively assert for 1 in-game year *shrinks*. Lose 1 portfolio slot per year of neglect. The LLM tracks this.

**Example portfolio sets** (for reference):

- Aizen: Tyranny · Control · Order through Absolute Will · Absolute Codification
- Dark Urge (God of Murder): Murder · Submissive Death · Intimate Betrayal · Total Suppression of Will
- Shinto Sun Goddess: Sun · Imperial Order · Crops
- Marvel Infinity-tier: Time · Space · Power · Mind · Soul · Reality

---

## IV. Follower-Scaling (the math)

A god's power scales linearly with active worshippers (F). The formula:

```
Stat(F) = Stat_Rank3 + (F / 1,000,000) × (Stat_Rank6 - Stat_Rank3)
```

**Per-stat scaling** (verify against II's table):

| Stat | Δ per 1M followers |
|------|--------------------|
| DHP | +250 (from 750 → 1,000) |
| DPP/day | +175 (from 825 → 1,000) |
| DAIR Mod | (capped, only changes at rank promotion) |
| DLR | +1 (from 4 → 5) |
| PDD base | +5 (from 80 → 85; multiplier unchanged at 5) |

**Active worshipper count (F)** is the LLM-tracked value. Update rules:

- +1 per soul that consciously and voluntarily invokes your name with intent
- +0 for involuntary fear-based worship (counts as a *tithe*, not worship; see V)
- -1 per soul that consciously renounces your name in a sacred space
- F is audited at every long rest / dawn transition

**Target milestones** (the LLM narrates when these flip):

| F threshold | Trigger |
|-------------|---------|
| 100 | First saint / first mortal bound to your faith |
| 1,000 | Your faith has vestments, a calendar, a hierarchy |
| 10,000 | First heretical schism within your church |
| 100,000 | Other gods hold formal council about you |
| 1,000,000 | Rank 6 promotion fires; you become a Greater Deity |
| 10,000,000 | Rank 7 promotion fires; you become a Transcendent theme |

---

## V. Tithes — the Sacrifice Engine

Worship scales you slowly. **Tithes** are the burst-scale engine: a one-time surge of divine essence in exchange for an immediate mechanical effect.

**Tithe sources:**

1. **Voluntary death** (a follower gives their life in your name): +1 Tithe per soul, scales by rank of follower (commoner = 1, hero = 5, high priest = 25, avatar of another god = 100)
2. **Terror harvest** (submissive death, fear-extraction, life-force drained by your avatar): +1 Tithe per mortal whose death was *entirely* in your direct causal chain
3. **Tragic betrayal** (the bond severed was profound — lover, child, lifelong companion): ×3 Tithe multiplier on top of base
4. **Planar conquest** (slay an avatar of another god on their home plane): +100 Tithe
5. **Pantheon absorption** (consume the divine spark of a defeated god): +1,000 Tithe, +1 portfolio slot, immediate Rank promotion check

**Tithe maximum pool:** equal to current DPP/day. Regenerates fully at dawn.

**Tithe expenditure** (sample effects; the LLM may add new ones but must cite this baseline):

| Effect | Cost | What it does |
|--------|------|--------------|
| **Martyr's Substitution** | 1 | When your avatar drops to 0 HP, a distant cultist takes the death instead. Your avatar drops to 1 HP and vanishes into the nearest shadow. |
| **Dread Proclamation** | 2 | All non-allies within 30 ft must save vs DC = 100 or fall prone in submission. (The Aizen baseline.) |
| **Portfolio Override** | 5 | For 1 minute, any action within your portfolio auto-succeeds. The universe does not resist you. |
| **Planar Transit** | 25 | Teleport self + retinue to any location in any plane you have a worshipper in. |
| **Avatar Conjunction** | 100 | Two avatars of yours act in perfect synchronization for 1 round (effectively 2 turns of action). |
| **Divine Resurrection** | 500 | A deceased mortal returns to life as your Chosen — bound to your portfolio, immune to resurrection by any god of lower rank. |
| **Pantheon Absorption Attempt** | 1,000 | Attempt to consume the divine spark of a present deity. Target must be ≤ your rank. On success, +1 portfolio, +1,000 DHP cap, immediate rank check. |
| **Cosmic Rewrite** | 5,000 | One rule of reality within your portfolio changes for 24 hours. The LLM must enforce the change in all subsequent scenes. |

---

## VI. Avatar Mechanics — The Mortal Shell

Gods can manifest in the mortal plane through an **avatar**: a discrete physical body operating under a specific subset of your divine power. Avatars are how every campaign actually *plays*.

**Avatar properties:**

| Property | Rule |
|----------|------|
| **HP cap** | Avatar HP = (1,000 × Rank) + mortal-level-based bonus. Discorporation at 0; reform in 1d10 days at your primary altar. |
| **Carries mortal sheet** | The avatar inherits all your character-class features, levels, gear, spells. They layer ON TOP of the divine stat block, not replace it. |
| **DAC** | max(mortal AC + DEX, DAC) + (Rank as flat deflection bonus) |
| **Action economy** | 1 Major Divine Action (cost DPP) + 3 Legendary Actions (10-25 DPP each) per round |
| **Switching modes** | You can swap between inhabiting the avatar (full consciousness) and remote-commanding it (autonomous with daily check-ins) at will. Bonus action. |

**Why avatars matter:**

- Most mortal-class threats are below the avatar's notice. The avatar *chooses* to engage them.
- Avatar death is *not* god death. Discorporation = 1d10 days reformation + reputation hit among worshippers.
- Avatar encounters vs other god avatars: full God Combat (see VII).

---

## VII. God Combat — Turn Economy

When two divine beings clash directly, **mortal combat rules do not apply.** Use this engine.

**Per round, a god has:**

- **1 Major Divine Action** (costs DPP; 100-150 for nascent greater, scales by rank)
- **3 Legendary Actions** (each costs 10-25 DPP; can be used at any point in the round, including reactively)

**Action costs** (per rank):

| Rank | Major Action | Legendary Action |
|------|--------------|------------------|
| 0 Quasi | 10-25 DPP | 5-10 |
| 1-2 Ascendant | 25-75 | 5-15 |
| 3 Nascent Greater | 100-150 | 10-25 |
| 5 Intermediate | 50-100 | 10-20 |
| 6 Greater | 150-250 | 25-50 |
| 7 Transcendent | 300+ | 50-100 |

**Combat math:**

- **To-hit:** 1d20 + DAIR Mod
- **Damage on hit:** PDD (base + 1d20 × multiplier)
- **Defense:** Opponent's DAC (flat deflection + DEX + any cover)
- **Save DC for divine influence:** 8 + Rank × 10 + WIS or CHA mod (whichever is lower for the target)
- **HP regeneration:** Gods do not regenerate HP in combat. They spend DPP to heal (1 HP per 1 DPP, capped at 100 HP/round).

**Special rules:**

- **No crits in god combat.** Variance is already in PDD's 1d20 multiplier.
- **Discorporation at 0 DHP.** Avatar shatters; divine essence reforms at altar in 1d10 days.
- **True death requires** consuming the divine spark (V.5, 1,000 Tithe) *and* the target being at a planar location they do not control.

---

## VIII. Worship, Propaganda & Cult Mechanics

The LLM tracks cult operations as a discrete sub-system, not narrative fluff.

**Cult Operations Table** (sample actions; LLM may extend):

| Action | Cost | Time | Effect |
|--------|------|------|--------|
| **Establish shrine** | 50 gold + 1 named NPC | 1 week | +10 to local F growth |
| **Convert noble house** | 1 intrigue roll + 500 gold | 1 month | +50 to F, +1 political lever |
| **Run martyrdom ritual** | 1 willing follower | 1 day | +5 Tithe, -1 F, reputation spike |
| **Planar embassy** | 1,000 gold + Rank ≥ 3 | 3 months | Opens diplomacy with 1 planar faction |
| **Inquisition / purging rival cult** | 1 elite squad + 200 gold | 1 month | -50 to rival F in target region, +25 to your F |
| **Saint canonization** | 1 dead hero + 5,000 gold | 1 year | +500 to F, grants 1 named Saint ability |

**Reputation Axes** (track separately):

1. **Fear** (0-100) — how terrified mortals are of you. High fear = fast F growth, low quality of worship.
2. **Love** (0-100) — how devoted your followers are. High love = resilient F, slower growth.
3. **Awe** (0-100) — how the gods themselves regard you. High awe = diplomacy leverage, low awe = ignored.

---

## IX. Per-Faction Dissonance (the rule Jeffrey asked for in 1784507599)

**Dissonance is hidden, per god faction versus overall.**

Each worshipper faction — defined by region, social class, race, or philosophical sub-school — has its own private reading of your portfolio. The LLM maintains:

- **One global reputation** (what other gods + general public see)
- **Per-faction reputations** (what each sub-group experiences)
- **Faction-specific events** (one faction may receive a unique vision, revelation, or scandal that no other faction knows about)

**Mechanical effect:**

- +1 portfolio slot at Rank 5 if you can keep ≥ 3 major factions in alignment
- -1 portfolio slot at Rank 5 if your factions' dissonance exceeds threshold
- Per-faction plot arcs may *contradict* the global narrative; the LLM is forbidden from collapsing them into a single read

This is the **anti-anti-invention guardrail** for divine campaigns — it ensures each faction feels lived-in and independent.

---

## X. Ascension — How a Mortal Becomes a God

The mechanical ladder mortals climb. Different settings call this "cultivation breakthrough," "tailed-beast merger," "divine spark ignition," or "Omega-level event."

**5-stage ascension template:**

| Stage | Trigger | Mechanic |
|-------|---------|----------|
| **Mortal Apex** | Reached max mortal level / cultivation peak / Omega threshold | Character sheet is at maximum mortal potential |
| **Spark Ignition** | Encountered / absorbed a divine spark, elder entity, or Omega-tier power source | Unlock Rank 0 quasi-deity stats |
| **First Worship** | First 100 mortal worshippers voluntarily invoke your name | Promote to Rank 1, unlock cult mechanics |
| **Pantheon Notice** | A god of higher rank attempts to interact with you (negotiation, assault, or absorption attempt) | Unlock Rank 3 stats; full portfolio mechanics online |
| **Transcendence** | Hit F = 1M OR consumed a god of equal rank | Promote to Rank 6 / 7; rewriting-reality privileges unlocked |

**The campaign is the gap between stages.** Each gap is a sandbox arc:

- Mortal Apex → Spark Ignition: classic mortal-tier power fantasy
- Spark Ignition → First Worship: god-mechanics discovery, building the cult
- First Worship → Pantheon Notice: small-scale cult operations, regional warfare
- Pantheon Notice → Transcendence: full divine warfare, planar conquest

---

## XI. Anti-Pattern: When God Mechanics Go Wrong

The user has flagged these in past campaigns. The LLM must NOT do them.

| Anti-pattern | Why it's bad | Replacement |
|--------------|--------------|-------------|
| **All narrative, no math** | The user can't feel progression; the LLM vibes the difficulty curve | Explicit stat block per scene; compute DHP/DPP at start of each divine encounter |
| **Gods win every fight** | Removes challenge; the user quits in 5 sessions | Divine enemies use the same God Combat engine, with their own stats. They can win. |
| **Worship is automatic** | No cult operations, no per-faction dissonance | Track F explicitly; require cult actions for F growth above natural baseline |
| **Avatars are invincible** | Avatar vs mortal threats is boring | Avatars operate under the mortal sheet + divine overlay; can be challenged by high-tier mortals |
| **Portfolio never changes** | Static god = static campaign | Portfolio expansion at rank promotion; portfolio decay on neglect |
| **Portfolios collapse across factions** | "Everyone sees you the same way" | Per-faction dissonance rule (IX) — keep them independent |
| **Random antagonist events** | Cosmic-level threat with no LLM-narrated setup | Antagonist actions cost the antagonist Tithe/DPP; track and disclose |
| **Magic-detection / scrying spam** | The LLM invents "you've been seen by an oracle" tropes | Detection = a divine-tier action that costs the watching god DPP; default = NOT watched |

---

## XII. Game Master Operational Rules (general)

The LLM running a god campaign must:

1. **Print the divine stat block** at the start of every scene in which the avatar is active. One line: `DHP X / DAC Y / DPP Z/day / DAIR +A / DLR B / PDD C+d20×D / F=current`.
2. **Print the F tracker** at dawn transitions and after any cult operation. `F = 12,450 (+0 natural / +0 operations today)`.
3. **Print the Tithe pool** at every divine action. `Tithes spent: 2 (Dread Proclamation). Pool: 5/7 remaining.`
4. **Compute formulas in-line** when scaling changes. "Your DHP has scaled with F: was 750 at F=0, now 762 at F=50,000." No hiding the math.
5. **Use sequence IDs / checkpoint blocks** to anchor scene continuity. (Format: `SeqID N | Timestamp | Location | [HASH]`.) Borrowed from the Aizen Godhood Continued model.
6. **Apply per-faction dissonance.** Two factions receiving the same vision differently is a feature, not a bug. The LLM is forbidden from averaging their reactions.
7. **No silent antagonist events.** Every antagonist action has a Tithe/DPP cost the LLM discloses. If an NPC acts against the god, the LLM narrates the *cost they paid*.
8. **No magical scrying without divine-tier action.** Mortals cannot scry a god-tier avatar without spending divine-tier resources. If a mortal "somehow detects" you, the LLM must explain the chain.

---

## XIII. Worked Example: Aizen, the God-King (setting-agnostic)

Translating the aizen_god_mechanics.md doc into this framework:

- **Rank:** 3 Nascent Greater
- **F:** Started at 0 (post-Bane consumption); scale to 1M for Rank 6
- **DHP:** 750 (matches Rank 3)
- **DAC:** 25 + DEX = 26
- **DPP/day:** 825 (matches Rank 3)
- **DAIR Mod:** +31 (matches Rank 3)
- **DLR:** 4
- **PDD:** 80 + (1d20×5)
- **Portfolios:** Tyranny, Control, Order through Absolute Will, Absolute Codification
- **Cult mechanics:** Aizen's avatar in BG3 is mid-ascension, building toward F=100k
- **Avatar:** Mortal-class Paladin 2 / Bard 10, inherits gestalt sheet
- **Anti-pattern check:** The 3-layer deception (Kyōka Suigetsu, false stat block to Mystra) IS the right kind of god-mechanic — system-agnostic illusion as divine action, costs DPP.

This general spec explains *why* the Aizen god-mechanics doc worked: it had explicit numbers, a scaling formula, and a coherent engine.

---

## Cross-references

- **Existing setting-specific module:** `world_reference/campaign_module_god_of_murder.md` — apply this general spec to the BG3 module's Sanguine Architecture to get explicit Tier-3 god stats.
- **Aizen reference (Faerûn-specific):** `world_reference/aizen_god_mechanics.md` — the canonical setting-specific instantiation this general spec was extracted from.
- **3e God Combat baseline:** The mechanical baseline used in the BG3 God of Murder doc; reused here with system-agnostic numbers.
- **Campaign bible templates:** `~/.hermes/skills/campaign-creation/` (skillified this turn) — uses this god-mechanic framework for the "if your protagonist ascends, here's the engine" section.

---

## Provenance

- **Drafted:** 2026-07-20, in response to Jeffrey's "keep iterating on this campaign. It doesnt seem to have many god mechanics just lots of narrative?" (Slack C0AH3RY3DK6/p1784585087.439909).
- **Extracted from:** `world_reference/aizen_god_mechanics.md` (verified 2026-07-20) + the Sanguine Architecture module's Section 6 (Level 12→30 ledger) + Section 7 (Mechanical Subsystems).
- **Constraint applied:** "The god mechanics should be general though and not specific to faerun or D&D" (Slack C0AH3RY3DK6/p1784584779.096719).
- **Voice constraint applied:** "Lets make dissonance hidden and remove apex attention and make it dissonance per god faction versus overall" (Slack C0AH3RY3DK6/p1784507599.182939) — codified as §IX.
