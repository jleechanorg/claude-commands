---
name: campaign-creation
version: 1.2.1
description: |
  Publication-ready solo campaign bible from canonical templates
  (Campaign 9-section bible + Sub-Templates A/B/C; Personality 6-tier
  dossier + d20). v1.2.0: NPCs evolve via Want/Fear/Boundary state;
  AI mysteries (3 clues, 3 suspects) target each NPC; plot arcs must
  advance growth, confront insecurity, or reframe a Want. MBTI codes
  are LLM-internal only.

  Triggers: campaign creation/bible, template follow, "design mysteries",
  "AI-generated mysteries", "mystery-driven", "internal-drive plot",
  "character-evolution arc", "personal-growth campaign", and the Campaign
  Template (1kWl5zkpxMFO7tQb7C9NRuyhmgRKYmBIdHoNuWF9Q1fI) or Character
  Personality Template (1hYzTmydm1qE6o4Ipk8ChOlsF4PIy2BaF7PVW-coup68).

  Authoritative source: the two templates (cached locally at
  `~/.hermes/skills/campaign-creation/references/`). The templates are the
  spec; this skill enforces the spec.
allowed-tools:
  - Read
  - Write
  - Bash
context: inline
---

# Campaign Creation — Build a Solo Campaign Bible From Scratch

## Contract

This skill enforces a **deterministic 11-step workflow** with the following guarantees:

| # | Item | Enforced by |
|---|------|-------------|
| 1 | Source templates are the canonical spec (Campaign Template + Character Personality Template) | `references/campaign_template.txt`, `references/personality_template.txt` (cached Google Docs) |
| 2 | All 9 Campaign-Template sections must appear | `scripts/template_validator.py` |
| 3 | Sub-Template A applied in full to Section 2 + every family member + every retinue member | `scripts/template_validator.py` (6-tier keyword check) |
| 4 | Sub-Template B applied to ruling factions | `scripts/template_validator.py` (5-section keyword check) |
| 5 | Sub-Template C applied to every panoply item | `scripts/template_validator.py` (panoply item count = 3-5) |
| 6 | Exactly 2 parents, 2 brothers, 2 sisters | `scripts/template_validator.py` (count check) |
| 7 | Exactly 10 ruling factions, 10 friendly, 10 antagonistic | `scripts/template_validator.py` (count check) |
| 8 | Exactly 3 retinue NPCs | `scripts/template_validator.py` (count check) |
| 9 | 8-12 unique non-standard loot items in Section 8 | `scripts/template_validator.py` |
| 10 | Personality Template Part 1 (I-VI) + Part 2 (I-V) + 9-sub-section deep dive | `scripts/template_validator.py` |
| 11 | Every ability has a quantified mechanic (action economy / DC / daily limit) | `scripts/section_completeness.py` |

**Outputs:** a campaign bible Markdown file + a verifier report (PASS/FAIL per item) + a save receipt (Google Doc ID + URL, or local path).

**Failure modes:** any ERROR-level verifier finding is a blocker; WARN-level findings are advisory.

---

This skill turns a blank page into a publication-ready campaign bible by enforcing the structure of the two canonical Google Doc templates. Both templates are cached locally at `references/` so the skill works offline.

## Phases

The skill runs as 11 deterministic phases. Each phase has a verifier that fails the pipeline if its output is missing.

| Phase | Output | Verifier |
|-------|--------|----------|
| 1. Read cached templates | Confirmation that both reference files exist | `check_resolvable.py --self` |
| 2. Locate authoritative source IDs | Two Google Doc IDs (Campaign Template `1kWl5zk…`, Personality Template `1hYzTm…`) logged in provenance | `references/god_mechanics_general.md` reference loaded if god-tier campaign |
| 3. Lock setting + system | Setting name, system name, branch, level, power tier recorded | Manual checkpoint |
| 4. Compose Section 1 (Campaign Intro) | Title, concept, hook, tone | `scripts/template_validator.py` (Section 1 check) |
| 5. Compose Section 2 (Character Personality — Section heading) | Core Identity, Psychology, Behavior and Speech, Backstory, Persona vs Repressed Interior, Unconscious Beliefs | `scripts/template_validator.py` (Sub-Template A check) |
| 6. Compose Section 3 (Character Class) | Class name, unique mechanic, 5-tier progression | `scripts/section_completeness.py` (abilities quantified) |
| 7. Compose Section 4 (Assets and Retinue) | Panoply (3-5 items, Sub-Template C), Retinue (3 NPCs, Sub-Template A) | `scripts/template_validator.py` (Panoply + Retinue count) |
| 8. Compose Section 5 (Family) | 2 parents + 2 brothers + 2 sisters, each with full Sub-Template A | `scripts/template_validator.py` (count check) |
| 9. Compose Section 6 (Factions) | 10 ruling (Sub-Template B) + 10 friendly + 10 antagonistic | `scripts/template_validator.py` (faction counts) |
| 10. Compose Section 7 (World Lore) + Section 8 (Gazetteer) + Section 9 (Starting Scene) | Timeline + 4 locations + loot table (8-12 items) + scene | `scripts/template_validator.py` (Loot Table check) |
| 11. Append Personality Template | Part 1 (I-VI + 9-section deep dive) + Part 2 (I-V d20 sheet) | `scripts/template_validator.py` (Personality Template checks) |

---

## Output Format

A successful run produces:

1. **A campaign bible Markdown file** at `world_reference/campaign_module_<name>.md` (or `~/path/of/choice.md`)
2. **A verifier report** (stdout from `template_validator.py --json`)
3. **A save receipt** — for Google Doc output: Doc ID + URL. For local: absolute path + byte size + SHA256.

Optional outputs:
- **A wiki entry** in `~/llm_wiki/wiki/sources/<campaign-name>.md` (call `llm_wiki` skill)
- **A character dossier** in `~/llm_wiki/wiki/characters/` (for the protagonist + each NPC)

## Character Evolution & Mystery Architecture (v1.2.0)

This section is the **internal-drive engine** for v1.2.0+. It tells the LLM
how to write NPCs that change over the course of play, how to weave mysteries
that target their vulnerabilities, and how to build plot arcs that earn their
narrative weight. None of this content is player-visible — the *effects* are
(player sees a character who breaks down, a clue that lands, a choice that
hits), but the *machinery* (MBTI codes, stress arcs, want/fear/boundary state,
suspect branches) is LLM-internal state held in DM notes.

### The MBTI internal-only contract

The 16 MBTI type pages at `~/llm_wiki/wiki/concepts/mbti/` (one page per type
code — INTJ, INFJ, INTP, INFP, ISTJ, ISFJ, ISTP, ISFP, ENTJ, ENFJ, ENTP,
ENFP, ESTJ, ESFJ, ESTP, ESFP) are **LLM-input only**. They are background
reading that informs how a character behaves, what stresses them, what they
reach for under pressure, and what personal growth looks like for them.

**Hard rules:**

- The 4-letter type code (e.g. `INFJ`) **never appears** in any player-facing
  prose — not in Section 2, not in d20 stat blocks, not in scene narration,
  not in the Starting Scene, not in dialogue tags.
- The type *category labels* ("Analyst", "Diplomat", "Sentinel", "Explorer")
  also never appear in player-facing prose.
- Personal growth may be referenced as a narrative theme ("they must learn
  to let go of control," "she has to face her fear of being seen"), but the
  underlying typology stays in DM notes.
- This contract mirrors the canonical one in `narrative_system_instruction.md`
  (PR #8539); if that file is updated, defer to it.

The 16 type pages are linked via wikilinks (`[[concepts/mbti/INFJ]]`) so
LLM context retrieval can surface them on demand. Keep them in mind but never
quote them to the player.

### Character evolution rule — Want / Fear / Boundary state

Every NPC that appears in the campaign bible (protagonist, family, retinue,
faction leaders, named antagonists) carries a tracked internal state with
three fields:

| Field | What it tracks | Example |
|---|---|---|
| **Want** | The deep motivational drive — what they believe will finally make them whole / safe / powerful / loved | "To be the only one her father ever trusted" |
| **Fear** | The thing they will go furthest to avoid | "Being abandoned by the people she chose" |
| **Boundary** | The line they will not cross, even at cost to themselves | "She will never lie to a child" |

**Mutation rule:** When an in-game event plausibly *fulfills*, *negates*, or
*mutates* any of these three fields, the LLM **must** update the state and
document the trigger in DM notes:

- **Fulfilled** — the event delivered what the Want/Fear/Boundary pointed to.
  The field is satisfied; downstream behavior shifts (relief, grief,
  re-orientation).
- **Negated** — the event proved the Want/Fear/Boundary false or unattainable.
  The character grieves the loss and reorients.
- **Mutated** — the event reframed the Want/Fear/Boundary without satisfying
  or negating it. The new form is logged; old form is archived.

Trigger documentation format (LLM-internal, appears in DM notes — never in
the bible body):

```
[character_state_update]
  npc: <name>
  field: Want | Fear | Boundary
  transition: fulfilled | negated | mutated
  trigger_event: <scene or event reference>
  new_value: <post-transition value>
  evidence: <1-2 sentences justifying the transition>
```

### MBTI stress arc

Under sustained pressure (3+ consecutive high-stress scenes, a critical
failure, or a betrayal by a trusted ally), an NPC's behavior drifts toward
their type's **stress pattern**. Examples (not exhaustive — consult the
type page for the canonical pattern):

- **INFJ** → withdrawn, hyper-critical of self and others, door-slam cuts
- **ENTJ** → micromanagement, command-by-fiat, contempt for slower allies
- **ISFP** → emotional flooding, retreat into silence, sudden exit
- **ESTP** → risk escalation, mocking humor as armor, provocation-seeking
- **ENFP** → scattered focus, broken promises, people-pleasing collapse

The stress arc is **not a permanent shift** — it is a 1-3 scene window of
disrupted behavior. After the trigger resolves (peace, confession, ally
return, time skip), the character either returns to baseline or grows into
a new baseline if the growth direction was advanced.

### Mystery template (AI-generated)

For each major mystery the LLM proactively designs during campaign
construction, document:

```
mystery_state:
  id: <slug>
  active:
    - id: <sub-mystery-slug>
      hidden_fact: <the truth the players must uncover>
      clue_trail:
        - clue_1: <discovery>
        - clue_2: <discovery>
        - clue_3: <discovery>
      suspect_branches:
        red_herring:
          suspect: <name>
          motive_frame: <how this branch looks true>
          falsifying_evidence: <clue that disproves it>
        partial_truth:
          suspect: <name>
          motive_frame: <how this branch is half-right>
          what_it_misses: <the missing half>
        real_answer:
          suspect: <name>
          motive_frame: <the actual answer>
      hits_vulnerability: <which NPC's Want/Fear/Boundary this mystery attacks>
  resolved:
    - id: <sub-mystery-slug>
      real_answer: <confirmed truth>
      cost_to_npc: <how the resolution mutated the NPC's state>
```

The mystery **must hit a vulnerability** — a Want the player is positioned
to threaten, a Fear the player can trigger, or a Boundary the player can
force the NPC to cross. Mystery design that does not attack an internal
state is decorative; cut it.

### Internal-drive plot arc

Each of the campaign's 3 acts (Early / Mid / Late) **must** do at least one
of:

1. **Advance the personal-growth direction** — move the protagonist (or
   a key NPC) toward the lesson/healing/confrontation their
   Personal-Growth Direction specifies (see Personality Template Part 1.VI
   below).
2. **Confront an insecurity** — force the character to face the
   insecurity catalogued in their Stress Arc & Insecurity Map (same
   section).
3. **Reframe a long-held Want** — present evidence that the Want is
   either unattainable, insufficient, or pointing at the wrong target;
   the character must integrate the new information.

If an act does none of the three, it is filler — rewrite the act.

The Starting Scene (Section 9) is required to surface the first clue of
at least one active mystery (see Step 10 below).

### Where this machinery lives in the bible

| Bible location | State field / pattern |
|---|---|
| Section 2 Character Personality, Tier II Psychology | Want / Fear / Boundary triple (each NPC) |
| Section 4 Retinue | Personal-Growth Direction + Stress Arc per retinue NPC |
| Section 8 Gazetteer & Mechanics | Custom Mechanics → **Mystery Tracker** (structured `mystery_state` block) |
| Section 9 Starting Scene | First clue of an active mystery surfaces here |
| Personality Template Part 1.VI Psychological Deep Dive | **Personal-Growth Direction** + **Stress Arc & Insecurity Map** (2 new sub-sections) |
| DM notes (LLM-internal, not in bible) | `[character_state_update]` log + stress-arc windows |

This state is what makes a campaign feel like a *world that responds* rather
than a script. It is the single biggest v1.2.0 differentiator over v1.1.0.

**Full schemas and copy-paste templates** for the `mystery_state` block, the
Want/Fear/Boundary triple, the `[character_state_update]` log format, the
Personal-Growth Direction + Stress Arc & Insecurity Map YAML, the per-act
internal-drive checklist, and the Panoply–Retinue binding example live at
`references/character-evolution-and-mystery-architecture.md` in this skill.
Load it whenever you are composing a new v1.2.0 bible or auditing an existing
one for completeness on the internal-drive engine.

## When to load

Load this skill when ANY of the following signals fire:

| Signal | Example |
|---|---|
| User says "create a campaign," "design a new campaign," "make a campaign" | "design me a campaign from scratch" |
| User says "follow the template," "use the template" | "follow the campaign template for a Wuxia cultivation arc" |
| User references the Campaign Template doc ID | `1kWl5zkpxMFO7tQb7C9NRuyhmgRKYmBIdHoNuWF9Q1fI` |
| User references the Character Personality Template doc ID | `1hYzTmydm1qE6o4Ipk8ChOlsF4PIy2BaF7PVW-coup68` |
| User wants the 9-section bible + Sub-Templates A/B/C | "use Sub-Template A for every character" |
| User wants the 6-tier psychological dossier + d20 sheet | "go deep on the personality profile" |
| User wants a "main character energy" god-tier / sovereign / high-fantasy campaign | "design a high-stakes campaign with a level-20 god-tier protagonist" |
| User wants explicit numerical stat blocks instead of narrative ("more god mechanics, less narrative") | Mandatory Quantified Mechanical Engine from `references/god_mechanics_general.md` — 6-tier divinity ladder, follower-scaling formulas, per-faction portfolio tension, system-agnostic so it works for any setting (D&D, Wuxia, Naruto, Marvel, Cyberpunk) |
| User asks for a non-BG3 system (Wuxia, Naruto, Cyberpunk, Marvel) | Same Quantified Engine — the math is setting-agnostic; only the *naming* and flavor shift |

## Distinct from adjacent skills

- **`campaign-design-iteration`** — iterates an *existing* campaign across versions (vN → vN+1). This skill is for *new* campaigns.
- **`download-campaign`** — exports an existing Firestore campaign to wiki. This skill generates from prompts, not Firestore.
- **`wa-campaign-content-analysis`** — audits an existing campaign. This skill creates.

## The 11-Step Workflow

### Step 1 — Confirm scope up-front (one question max)

The skill needs ONE clarifying input from the user:

**Required question (mandatory):** "What is the *Tone + Setting Concept + Protagonist Archetype*?" (Format: free text or use the Campaign Template's three placeholders — `Tone:`, `Setting Concept:`, `Protagonist Archetype:`.)

That's it. **Pick defaults for everything else.** Specifically:

- Default to **9-section bible + Sub-Templates A/B/C** unless user says "personality only" or "campaign only."
- Default to **level 1-30 + Tier 5 Epic Boons** unless user names a specific tier ceiling.
- Default to **10 friendly factions + 10 antagonistic factions** unless user names a different count.
- Default to **2 parents + 2 brothers + 2 sisters** unless user names different family shape.
- Default to **3 retinue NPCs + 3-5 panoply items** unless user names different counts.

Do NOT ask multi-part questions. Do NOT ask about formatting, length, or style. The templates are the spec.

### Step 2 — Section 1: Campaign Intro (Title + Concept + Hook)

Per the Campaign Template's Section 1:

- **Title** — thematic, evocative. NOT generic ("The Dark Campaign" ✗). Use the protagonist's name or a defining artifact ("The Sanguine Architecture" ✓).
- **Concept** — the world's unique twist + the protagonist's ultimate goal. 3-5 sentences. Names at least one specific antagonist system and one specific protagonist-tool.
- **Hook** — why is this fun? Focus on the **power fantasy**: "You are not saving the world; you are conquering it." Lead with what the player can *do* right now that they could not do in a normal campaign.

### Step 3 — Section 2: Character Personality (Sub-Template A in full)

Apply the **Standard Character Architecture** in full:

| Tier | Field | Required? |
|------|-------|-----------|
| I | Core Identity (Name, Archetype, Social Standing, Alignment, MBTI) | ✓ |
| II | Psychology (Core Motivation, Greatest Fear, 3-5 Temperament Traits) | ✓ |
| III | Behavior and Speech (stress ticks, speech patterns, reputation) | ✓ |
| IV | Backstory (Defining Moment + Relevant History + Deep Secrets) | ✓ |
| V | Persona vs Repressed Interior (outward mask + inner critique) | ✓ |
| VI | Unconscious Beliefs (2-4 absolute statements) | ✓ |

Then append the campaign-specific extensions:
- **Core Compulsion** (specific psychological hunger — "Breaking Authority," "Hoarding Secrets," etc.)
- **Mechanic — The Urge** (Failure Penalty + Success Bonus — *must be quantified*)
- **Interaction Shorthand** (explicit dialogue styles for Rivals vs Subordinates)
- **Inner Monologue** (3-5 raw sample thoughts)

### Step 4 — Section 3: Character Class (Tiered 1-30 progression)

Per the Campaign Template's Section 3:

- **Class Name + Flavor** — rename or gestalt a base class; explain the *source* of power (Bloodline, Pact, Tech, Mutation, Divine spark)
- **Unique Mechanic** — one game-breaking "Main Character" ability, complete with action economy, limitations, and resource costs
- **Progression (Levels 1-30)** in 5 tiers:
  - **Tier 1 (Lvl 1-5):** Renamed core features + 1 Custom Ability
  - **Tier 2 (Lvl 6-10):** Renamed core features + 1 Custom Aura or Passive
  - **Tier 3 (Lvl 11-16):** Renamed core features + 1 High-Impact Offensive Capstone
  - **Tier 4 (Lvl 17-20):** Transformation / Avatar State (trigger actions + duration)
  - **Tier 5 (Lvl 21-30):** Named Epic Boons + Attribute cap increases (max 30) + reality-bending capabilities

**Mechanical specificity rule:** Every ability MUST have at least one of:
- An action economy cost ("bonus action," "1/round," "reaction")
- A scaling rule ("+1 per level," "1d8 + INT mod")
- A save DC formula
- A daily/long-rest resource cost

If you write an ability with none of the above, it is a *flavor* ability and the LLM will forget it. Quantify or remove.

### Step 5 — Section 4: Assets & Retinue

Per the Campaign Template's Section 4:

- **Starting Status** — Rank/Title matching their high station
- **Resources** — broad starting wealth + 1-2 named safehouses + political leverage / blackmail
- **The Panoply** — 3-5 Masterwork or Magical items. **Each item MUST be built with Sub-Template C** (the Tactical Masterwork / Relic Framework):
  - I. Item Name + Classification (true name + legendary titles + base item type)
  - II. Aesthetic + Material (exact physical description, weight, age, tactile feel)
  - III. Mythic Origin (lore, history, acquisition)
  - IV. System Metrics — Passive Property + Active Tactical Feature (action economy + daily uses + DC) + Narrative Side Effect
- **The Retinue** — exactly **3 distinct NPC subordinates**. Each retinue member MUST:
  - Be built with Sub-Template A in full
  - Have an explicit **Loyalty Profile** (psychological, financial, or transactional reason they serve)
  - Have a **Personal-Growth Direction** (lesson / healing / confrontation) — see Personality Template Part 1.VI sub-section 10. This is LLM-internal data the LLM uses to design plot arcs that challenge the retinue NPC on these axes.
  - Have a **Stress Arc & Insecurity Map** (stress pattern + 3-5 insecurities + surface patterns + mystery targeting) — see Personality Template Part 1.VI sub-section 11.
  - Have a documented **Want / Fear / Boundary** triple in their psychology tier (see "Character evolution rule" in the Character Evolution & Mystery Architecture section above).

- **Panoply–Retinue binding (v1.2.0)** — at least **1 of the 3-5 panoply items** MUST connect to a retinue NPC's personal-growth direction. Examples: an item the retinue NPC gave the protagonist as proof of loyalty; an item whose history forces the retinue NPC to confront an insecurity; an item whose mythic origin intersects the retinue NPC's secret backstory. Document the binding inline in the panoply item's Mythic Origin field (Sub-Template C tier III) so the LLM can use the item as a plot lever during the campaign.

### Step 6 — Section 5: Family Dynamics

Per the Campaign Template's Section 5:

- **The Parents** — 2 living parents (typically Lvl 12-20+). Apply Sub-Template A in full to each. State their stance toward the protagonist (Protective Guide / Demanding Superior / Covert Adversary) + how this dynamically impacts faction access.
- **The Siblings** — **exactly 2 older brothers + 2 older sisters**. Apply Sub-Template A in full to each. Map each to one of:
  1. **Direct Ally** (loyal confidant)
  2. **Overprotective Guardian** (loyal but restrictive)
  3. **Indifferent Bystander** (own agenda)
  4. **Unwitting Pawn** (easily drained)
  5. **Hostile Rival** (active threat)

### Step 7 — Section 6: Factions (The Game Board)

Per the Campaign Template's Section 6:

- **Ruling Factions** — **exactly 10** Major Houses / Corporations / Clans. Each MUST be built with Sub-Template B (Faction Structural Profile):
  - I. Nomenclature + Heraldry (official name, alias, visual signature)
  - II. Infrastructure + Domain (HQ + asset/manpower bracket + resource engine)
  - III. Leadership Dossier (apply Sub-Template A in full to the leader)
  - IV. Internal Operational Culture (unwritten codes, internal struggles, failure consequences)
  - V. The Hook (precise structural vulnerability the PC can exploit)
- **Friendly Factions** — **exactly 10** leverageable groups (Armies, Cults, Guilds). For each: Name + Operational Function + Leader's Identity + Leverage Point that keeps them aligned.
- **Antagonistic Factions** — **exactly 10** threats. **Humanoid / structural only** (Assassins, Rival Empires, Inquisitions, Corporate Strike Teams) — NOT mindless monsters. For each: Primary Objective + Escalation Method.

**Historical campaigns exception:** If setting is historical, use actual historical factions appropriate to the era.

### Step 8 — Section 7: World Lore

Per the Campaign Template's Section 7:

- **Timeline** — major historical events leading up to campaign start. Identify the **Divergence Point** (the unique ancient occurrence that shapes the current era).
- **Mythos** — metaphysical reality: pantheon of Gods + true nature of magic/tech systems + active Ancient Pacts.
- **Current Situation** — the immediate crisis (War / Succession Crisis / Plague / Looming Collapse) + the active conflict vector forcing immediate action.
- **Story Arcs** — 3 sequential phases (Early / Mid / Late Game) with escalating stakes + regional milestones + potential systemic endings. **Preserve player choice** — these are *suggested* arcs, not mandatory.

### Step 9 — Section 8: Gazetteer & Mechanics

Per the Campaign Template's Section 8:

- **Locations** — 4-6 Key Stages (e.g., The Palace, The War Camp, The Slums, The Spire). For each:
  - The Vibe (sensory + atmospheric)
  - 3-5 Key Sub-locations within
  - 1 concrete Physical or Social Hazard with variable 5e mechanical DC brackets + consequences
- **Custom Mechanics** — **exactly 2** unique gameplay sub-systems. Choose from:
  - **Mass Combat / Unit Rules** — how the PC commands armies using modified 5e metrics
  - **Social Reputation Tracker** — systemic tracker (Dignitas / Infamy / Leverage Bars) shifting faction behaviors based on public deeds
  - **Resource Management Ledger** — tracking structural wealth, supply lines, institutional influence
  - **Mystery Tracker** *(new in v1.2.0)* — a structured state field the LLM uses to drive AI-generated mysteries through the campaign. Document the full `mystery_state` block in Section 8 per the schema below. The tracker is a bible-resident artifact (not LLM-internal-only) because the *existence* of mysteries is player-discoverable; only the *machinery* (suspect branches, vulnerability targeting, MBTI cross-references) is held in DM notes alongside the tracker.
- **Loot Table** — 8-12 unique non-standard "Relics" or "Favors." **No generic +1 items.** Focus on systemic / narrative / mechanical power shifts.

### Step 10 — Section 9: Starting Scene

Per the Campaign Template's Section 9:

- **Setting** — atmospheric description with sensory details (sights, sounds, smells, ambient lighting).
- **The Hook** — immediate context, crisis, or operational opportunity framing the protagonist right now.
- **The Action** — the first decision point. **Provide an A/B/C choice that bypasses tests of authority** and lets the player act / dominate / build / demonstrate power right away. Establishes their high position from turn 1. **(v1.2.0)** The scene **must also surface the first clue of an active mystery** (one of the entries from the Section 8 Mystery Tracker) — embed it in the sensory detail, in an overheard line, in a delivered letter, or in a visible anomaly the player can choose to investigate (A), table for later (B), or dismiss (C). The clue is the campaign's first emotional lever; do not let the Starting Scene end without one.

### Step 11 — Append the Character Personality Template (6-tier dossier)

After Sections 1-9, append the **Character Personality Template** content for the protagonist. This is the deep psychological profile (separate from Section 2's Standard Character Architecture). Structure:

| Part | Section | Required? |
|------|---------|-----------|
| 1 | Part 1.I Core Identity | ✓ |
| 2 | Part 1.II Psychology & Personality (motivation, fear, 4-6 traits, 3+ quirks) | ✓ |
| 3 | Part 1.III Behavior & Speech (demeanor under stress, speech patterns, reputation) | ✓ |
| 4 | Part 1.IV Backstory (Defining Moment + Relevant History + Secrets) | ✓ |
| 5 | Part 1.V System Mechanics (feats/perks + special abilities/powers) | ✓ |
| 6 | Part 1.VI Psychological Deep Dive (9 sub-sections — see below) | ✓ |
| 7 | Part 2.I Core Attributes & Scaling (full d20 stat block) | ✓ |
| 8 | Part 2.II Combat & Tactical Vitality | ✓ |
| 9 | Part 2.III Proficiencies & Expertise | ✓ |
| 10 | Part 2.IV Features, Traits & Flaws (heritage + class + feats) | ✓ |
| 11 | Part 2.V Inventory & Equipment | ✓ |

The **Part 1.VI Psychological Deep Dive** has 11 sub-sections — all required
(9 canonical + 2 new in v1.2.0 for the internal-drive engine):

1. Portrait Summary
2. Composite Psychological Sketch (Big Five + Dominant Defenses + Attachment Style)
3. Social Persona vs Repressed Interior
4. Defense-Mechanism Diagnostics (3 specific mechanisms + triggers)
5. Relational Decoding (Attachment Script + Distance Mechanics + Interpretation Bias)
6. Core Unconscious Beliefs (3 absolute statements)
7. Personal Myth Narrative (Role + Story Told + Comfort/Safe Haven + Toxicity)
8. Break-Point Scenario (Catalyst + What Fractures + Immediate Cost + Liberation)
9. Closing Pulse
10. **Personal-Growth Direction** *(new in v1.2.0)* — what the character
    needs to **learn**, **heal**, or **confront** over the course of the
    campaign. This is LLM-internal data; the LLM uses it to design plot
    arcs that challenge the character on these axes (see "Internal-drive
    plot arc" above). Format:
    - **Lesson** — the cognitive/emotional insight the character must
      integrate ("letting go of control is not the same as losing love").
    - **Healing** — the wound or pattern that must be addressed ("the
      abandonment they keep re-enacting with every trusted ally").
    - **Confrontation** — the truth they refuse to face ("their mentor
      was wrong about what makes a person worthy").
    - The Growth Direction is referenced by every act's internal-drive
      check (see Phase 2 above). Acts that fail to advance it are filler.
11. **Stress Arc & Insecurity Map** *(new in v1.2.0)* — what the character
    does **under sustained pressure**, what insecurities get triggered,
    and how those moments surface in narrative. Format:
    - **Stress pattern** — the behavior drift the character exhibits
      during a 1-3 scene stress window (e.g. INFJ under stress →
      withdrawal + hyper-critical door-slam). Cross-reference the
      corresponding MBTI type page at `~/llm_wiki/wiki/concepts/mbti/`
      for the canonical pattern; do not paste the type code into the
      bible.
    - **Insecurities (3-5)** — each named with a trigger cue ("if the
      PC praises a rival publicly, the character spirals into
      self-doubt about being replaceable") and a narrative tell
      ("stops eating, voice flattens, retreats to their study").
    - **Surface patterns** — the visible behavior the player sees when
      an insecurity fires (deflection, escalation, withdrawal,
      appeasement, confession, etc.).
    - **Mystery targeting** — note which active mystery (see Mystery
      Template above) is positioned to hit each insecurity. Mysteries
      without a targeting linkage are decorative.

These two sub-sections are the load-bearing structure of v1.2.0's
character evolution. Without them, the campaign cannot honor the
internal-drive plot arc rule, and mysteries become plot devices rather
than emotional weapons.

## Pitfalls

**P1 — Skipping the Sub-Templates.** Section 2 *must* use the 6-tier Standard Character Architecture. Section 5 (family) must use Sub-Template A. Section 6 (factions) must use Sub-Template B. Section 4 items must use Sub-Template C. If you write Section 2 as a single paragraph, you skipped the contract.

**P2 — Vague mechanics.** An ability without an action economy cost, save DC, or daily limit is a flavor ability. The LLM will forget it next scene. Quantify or remove.

**P3 — Missing the 9-section structure.** Sections 1-9 are required. If you write Sections 1, 2, 3, then "Narrative" then jump to Starting Scene, you skipped the contract.

**P4 — Wrong counts.** Family = 2 + 2 + 2. Ruling factions = 10. Friendly = 10. Antagonistic = 10. Panoply = 3-5. Retinue = 3. If you have 7 ruling factions or 5 retinue members, the structure is wrong.

**P5 — Generic loot.** Loot table = 8-12 systemic / narrative items. NO +1 swords. The LLM needs loot that opens a *new capability*, not a stat bump.

**P6 — Skipping the psychological deep dive.** Part 1.VI of the Personality Template is the densest section. If you skip it, the character will feel like a stat block, not a person. The 9 sub-sections are required.

**P7 — Output limit truncation.** The Campaign Template explicitly says: "Do not summarize, abbreviate, or truncate any responses. Every section must be written out completely." If you hit token limits, **HALT at the end of a section** and ask the user for permission to continue. Do NOT collapse two sections.

**P8 — All narrative, no mechanics.** Every scene-level mechanic MUST be quantified. Use the **god-mechanics framework** at `~/.hermes/skills/campaign-creation/references/god_mechanics_general.md` (or its your-project.com mirror at `world_reference/god_mechanics_general.md`) for any campaign where the protagonist ascends to divine tier.

**P11 — L20+ is the sharp god-campaign quality filter.** Across the 19+ god-tier wikis (Aizen Godhood, Sariel Valyria, Visenya V6, Nocturne BG3 v6, Alexiel SWToR, Astarion Ascended, Witcher Strat, Rome Pax Julia, Dragon Knight, etc.), the campaigns that survived and graduated share four properties:

1. **Stat block in every scene header** (Aizen pattern: DHP/DPP/DAIR/DLR/F at the top of every entry). The player reads the math at every dawn.
2. **Custom class that projects god-tier from L1** (Apex Weaver gestalt, Abyssal Sovereign, Sovereign class) — the L1 build already feels divine.
3. **Reached L20+ by scene 30-50 of a 100-scene arc** (slow-burn pattern; Alexiel SWToR 33%, Nocturne BG3 v6 67%). Instant-L20 (Aizen Godhood, scene 4 of 78) is also valid if the mortal-graduation arc is skipped.
4. **Repr / Infamy / Pantheon Temperature economy** — quantitative tracking, not just bigger numbers.

Campaigns that stayed sub-L20 (Witcher Strat capped L4, Rome Pax Julia capped L10, Astarion Ascended capped L13) are burnout candidates regardless of premise quality. **The L20+ check is a sharper quality filter than "did the user keep iterating."** Use it to decide between god-campaign and mortal-campaign framing at Step 1.

**P12 — D&D 5e player loop is OPTIMIZE → ROLL, not "no rolls at climax."** A player first optimizes build / stats / items / strategy. *Then* the roll is the last thing — adds excitement and variance on top of an already-optimized setup. The roll is the cherry on top of an already-built sundae. **The user's complaint about god-campaigns was not "too many rolls." It was "no choices before the roll."** A campaign without a per-dawn choice menu has no OPTIMIZE step, so the roll ends up being the whole answer.

**Mechanic rule (P12 corollary):** Every central decision must present 4-6 named options with distinct mechanical consequences BEFORE the math runs. The math then resolves the consequence. The roll adds variance within the math-determined bracket — never decides the outcome.

**Per-dawn choice menu template:**
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
Player picks → math runs deterministically → roll variance within bracket.

**P13 — Calculations without choices are dead math.** When the user reads an LLM-generated god-campaign and "just sees calculations which don't mean much," the failure mode is: math exists but no decision tree points to the math. A DC has no mechanical meaning if the player's previous choice did not raise or lower it. **Every calculation in the stat block must be addressable from at least one per-dawn choice option.** If a stat (e.g. DPP cost, Repr threshold, Wound penalty) appears in the stat sheet but no choice option references it, the stat is decoration — remove it or wire it into a choice.

**P14 — Hybrid stats (5e L1-19 → divine L20+) is the right default for god-tier campaigns.** Two systems is the worry, but in sequence (not parallel) it's the Aizen pattern and the user's pattern:
- **L1-19:** standard 5e. Player optimizes the mortal build they already know. HP/AC/Save DC/Attack Bonus/Spell Slots. Familiar.
- **L20 transition:** mortal form caps. Divine projection unlocks. **The transition IS the campaign arc** — Nocturne's mortal form (Bard X / Rogue Y) hits the 5e cap, divine projection unlocks with a new stat block. The ascension is the campaign moment, not the campaign pre-req.
- **L20+:** divine stats. DHP/DAC/DPP/DAIR/DLR/F/Repr Die/Infamy/Pantheon Temperature. NEW optimization target (DPP economy, Repr Die growth, Infamy management).

Aizen did exactly this — Aizen's L20 mortal form (HP 138, AC 21, Save DC 21, Attack +13) + divine projection (DHP 750, DAC 25, DPP 825, DAIR +31, DLR 4). Two layers, one character. Two optimization targets in sequence, not parallel — no cognitive overload.

**P15 — Three-Layer Deception (Aizen pattern) is the canonical Repr mechanic.** Visible stat block / projected stat block / cover-story stat block — three layers of public-facing reality that differ from the player's true state. Adopt this for the Repr Die, do not invent a fresh mechanic.

**P16 — Publicity Tax > Wound Ledger for deicide-cost.** The user did not ask for a "killed god embeds in you as a saboteur" mechanic in Aizen (clean consumption of Bane was the precedent). Wound Ledger was invented to fill a need that did not exist. Use **Publicity Tax** (Repr decays 2× for 1d4 days, +1 Infamy) or **Clean Kill** (no deicide cost at all — match Aizen's pattern exactly). Empty Throne is valid but more-complex.

**P17 — Resource overhead ceiling: 5 trackers max.** Approved god-campaign resource set:
- Repr Die (d4→d20) + RP — how Faerûn perceives you; gates actions AND grants attributes
- DPP/day — divine power budget; 1 Major + 3 Legendary per dawn
- Follower count (F) — powers Aizen-style linear scaling (`Stat = Nascent + (F/1M × (Transcendent − Nascent))`)
- Infamy — 1 entry per god-kill with timestamp; gates Rank-up (max 2-in-60-days)
- Pantheon Temperature (0-5) — one dial for political heat; affects tithe income

Five trackers. Anything beyond gets cut. Resource sprawl is itself a design failure mode.

**P18 — Strategy archetypes at L20+.** Sovereign / Diplomat / Tyrant / Seducer (or domain-specific equivalents) change the math profile and present different choice options per dawn. The archetype choice is itself the player's first OPTIMIZE decision.

**P19 — Hybrid stats solve "no OPTIMIZE step" complaint.** See P14. The mortal grind (L1-19) IS the OPTIMIZE step the user wanted; the divine projection (L20+) IS the new optimization target. Two phases, both with named optimization targets.

**P9 — Skipping the confirmation question.** Ask the ONE clarifying question (Tone + Setting + Archetype) at the start. Do NOT ask 4+ questions. The skill's defaults cover everything else.

**P10 — Skipping the persistence step.** When the campaign bible is complete, you MUST save it. Default paths:
- **Google Doc** — `gog docs create "<title>"` + `gog docs write <DOC_ID> < /tmp/<bible>.md`
- **Local Markdown** — `~/your-project.com/world_reference/campaign_module_<slug>.md` (only for your-project.com campaigns)
- **Wiki source** — `~/llm_wiki/wiki/sources/<slug>.md` (only for personal wiki ingestion)

If you do not save it, you have not completed the deliverable.

**P20 — Double-placeholder artifact pitfall in setting-agnostic writing.** Verified 2026-07-21 on V3 god-mechanics overlay. When you replace setting-specific entity names with generic placeholders (e.g., `Mystra` → `the Weave-archon (replace per setting)`), do NOT apply the replacement to text that already contains a substring of the canonical name from a different context. The result is `the Source-Fabric (replace per setting)-archon (replace per setting)` — multiple `(replace per setting)` tags in one phrase. **Setting-agnostic tests only catch the underlying entity matches (e.g., test_no_dnd_default_entities checks for `Mystra` literally), not the artifact class.** The artifact will pass automated tests but reads horribly to humans and confuses the LLM. **Fix:** pick a clean single-token placeholder name with zero collision risk. Rename `the Source-Fabric-archon` → `the Arcanelord`, `the Shadow-Queen` → `the Shadowlord`, etc. **Run an aggressive verifier pass** (`grep -n '(replace per setting)'` after replacement) to catch any phrase with >1 placeholder marker.

**P21 — V3 mechanic density floor: 20+ sub-mechanics for L20+ god-campaigns.** Verified 2026-07-21 on PR $GITHUB_REPOSITORY#8488. V1 had 1 mechanic, V2 had 8, V3 has 22. The user's complaint was "doesn't seem to have many god mechanics, just lots of narrative." The V3 floor:
- **Stat-block vocabulary** (split between player-visible + LLM-internal)
- **Per-tier explicit multipliers** (no "approximately" in stat tables)
- **7 Repr growth sub-systems** (not just 1 generic "Repr+")
- **Action Tier economy** (AT-0/-1/-2/-3 with explicit DPP costs + caps)
- **AT-3 Legendary Actions menu** (6 named actions: War March / Divine Duello / Celestial Coup / Reformation / Cleansing Strike / Deicide)
- **5 dawn-action archetypes** (Sovereign / Diplomat / Tyrant / Seducer / Hermit)
- **D-faction tracking** per-god (not 1 global counter; god-class response matrix)
- **Per-temple ledger** (F bookkeeping)
- **OPTIMIZE→ROLL pattern** (player decides first, then math runs, then roll variance within bracket)
- **Chosen + Avatar creation** (vessels + manifestations: V3.13.1 Chosen at 250 DPP/50 DHP/DC 25; V3.13.2 Avatar at 500 DPP/100 DHP/no resistance)
- **2 worked examples** (one Routine dawn + one Triggered dawn)

If your overlay has fewer than 20 sub-mechanics, you are still in V2 territory and the user will say so. See `references/v3-god-mechanics-recipe.md` for the canonical V3 pattern.

**P22 — Real-LLM evidence with agy CLI is the verification path.** Verified 2026-07-21 on PR #8488. After writing god-mechanics content, you CANNOT claim "the LLM will probably handle this" — you must actually run a real LLM and observe the output. Recipe in `references/agy-cli-real-llm-verification.md`:
1. Build a test prompt that includes the V3 spec + a concrete scenario (e.g., L36 Intermediate god vs Bane's Avatar, triggered dawn)
2. Run `agy --print --dangerously-skip-permissions --add-dir <prompts_dir> --model "Claude Sonnet 4.6 (Thinking)" --prompt "$(cat test.txt)" > output.txt`
3. Verify the output honored: stat-block split (visible vs hidden), AT caps, DC 25 check, god-class response matrix, OPTIMIZE → ROLL, math-failure recognition
4. Save outputs at `<repo>/world_reference/agy-evidence/` with a README.md explaining what each test exercises
5. Reference the bundle in the PR `## Evidence` section

This is the proof that V3 mechanics actually work, not just that they read well. Critical: `agy --model` accepts a specific model string (e.g., `"Claude Sonnet 4.6 (Thinking)"`, not `claude-sonnet-4` which fails with "model not recognized").

**P23 — Never expose MBTI codes or category labels to the player (v1.2.0 internal-drive contract).** The 16 MBTI type pages at `~/llm_wiki/wiki/concepts/mbti/` are LLM-input only. Their purpose is to inform NPC behavior, stress patterns, and personal-growth direction — not to label the player or break the fourth wall. Hard rules:

- **Never** write the 4-letter type code (`INFJ`, `ENTP`, `ISTP`, etc.) into any player-facing text — not in Section 2, not in the Personality Template d20 sheet, not in scene narration, not in dialogue tags, not in NPC introductions, not in the Starting Scene.
- **Never** write the type *category label* (`Analyst`, `Diplomat`, `Sentinel`, `Explorer`) into any player-facing text for the same reason — even a "soft mention" ("she's clearly a Sentinel") breaks the contract.
- **Personal growth** is allowed as a narrative theme: "she must learn to trust the people she leads," "he has to face his fear of being ordinary." These are character arcs, not typology disclosures.
- The `[character_state_update]` log, the `mystery_state` block's `hits_vulnerability` field, the Stress Arc & Insecurity Map, and any cross-reference to a type page (`~/llm_wiki/wiki/concepts/mbti/INFJ`) all belong in **DM notes**, not in the bible body.
- **Verification:** a post-write grep across the bible for the 16 type codes and 4 category labels must return zero player-facing hits. (`grep -nE '\b(INTJ|INFJ|INTP|INFP|ISTJ|ISFJ|ISTP|ISFP|ENTJ|ENFJ|ENTP|ENFP|ESTJ|ESFJ|ESTP|ESFP|Analyst|Diplomat|Sentinel|Explorer)\b' <bible>.md` should match only inside explicit DM-notes fenced blocks, never in the main body.)

This contract mirrors the canonical one in `narrative_system_instruction.md` (PR #8539); if that file is updated, defer to it. The rule is the **load-bearing wall** of v1.2.0's internal-drive engine — without it, the typology leaks into the fiction and the player starts reading NPCs as labels rather than people.

**P24 — The user's design philosophy (verified across multiple campaigns as of 2026-07-28).** When the user (Jeffrey) reviews a campaign, the design-heuristics that consistently keep campaigns fun are the same ones that read as "feels like a real person is DMing." These are class-level rules, not Spellblade-specific:

- **Keep the power fantasy, challenge with stronger opponents, not arbitrary nerfs.** Dual-class / gestalt / hidden-apex protagonists stay powerful. The challenge comes from specialized opponents (counter-prep, terrain, hostages, roleplay cost, time pressure), not from inflating opponent stats or secretly capping the PC. Inflating stats and "you auto-win because you're stronger" scenes are both forbidden.
- **Hidden apex → surprise → intimidation (or its inverse).** The PC looks ordinary; an opponent makes assumptions; the PC chooses whether to reveal. A witnessed reveal creates a reputation change. The reputation is **per-NPC** (witness set persistence), never a global "the realm suspects" meter. Each observer's tier is its own datum.
- **No global aggregate trackers.** Aggregate suspicion / aggregate alignment / aggregate "the court knows" are forbidden. Each NPC tracks their own knowledge independently. Apply this to ALL state that could be aggregated: hidden-identity knowledge, alignment shifts, reputation, restraint-vs-violence, faction standing.
- **No forced ruler-progression arc.** The PC's arc toward or away from rulership is a player choice. NPCs do not volunteer "you must become the leader because no one else can." Refuse-the-call is a valid ending. Warrior-queen / bureaucrat / permanent peace-warden role is something the player *can* choose, never something the model steers them into.
- **Custody / confinement is a playable consequence, not a global flag.** Arrest, detention, interrogation, escape — these happen to specific people with specific evidence and authorize specific consequences. They are *played through* (hearings, planning, escape, ally vouching, slow time), not auto-resolved by the PC's power. The cell is a narrative challenge, not a stat block.
- **Exhaustion / responsibility cost is conditional, not a hidden ledger.** The PC gains a cost only when ALL of: (a) the PC explicitly accepted the responsibility, (b) the PC had a plausible opportunity to prevent the harm, (c) the PC knowingly failed or abandoned it, (d) the harm was serious. Good-faith attempts, unavoidable losses, reasonable tactical tradeoffs, and harms the PC never learned of do not trigger the cost. No silent accumulator the player can't see.
- **Anime / manga / franchise inspirations are flavor-only.** Use anime character archetypes (reserved prodigy, hot-blooded rival, weary mentor, cheerful chaos agent) as personality flavor. Never copy storylines, reveals, named techniques, transformation sequences, signature moves, character arcs, or future plot points from the source material. The campaign has its own story. This is non-negotiable when the user has stated they plan to read the source material.
- **Trust per-NPC autonomy over aggregate state.** Whenever the campaign mechanic surface tempts "the realm knows" / "the court has grown suspicious" / "all nearby NPCs feel X" — split the state into per-NPC fields tracked in `custom_campaign_state.npcs[<id>].*`, with witness-set persistence for events. This is the same pattern the user kept asking for: witness-based reveal, hidden-identity knowledge tiers, surprise-strike charges per PC. When in doubt, smaller per-NPC fields beat larger aggregate counters.
- **Bigger worlds beat bigger obstacles.** Top-tier campaigns (Visenya, Aizen, Dragon Knight, Nocturne) graduated by adding *cultures, factions, era, and player-driven consequences*, not by adding more global meters. Default to world-build depth over state-sprawl when scaling challenge.

When auditing a campaign against this pitfall, the grep test is: "Would the world survive losing the global meter?" If yes, the meter is load-bearing; if no, split it into per-NPC state. The two best implementations of this pattern are `references/character-evolution-and-mystery-architecture.md` (NPC evolution and mystery targeting) and the witness-set pattern in `$PROJECT_ROOT/prompts/shared/witness_based_reveal_continuity.md` (PR-A SHARED-CONTRACTS). Cargo-cult them when implementing new mechanics.

## Verification

After the campaign bible is generated, verify:

```bash
python3 ~/.hermes/skills/campaign-creation/scripts/template_validator.py \
  /tmp/<bible>.md \
  --campaign-template ~/.hermes/skills/campaign-creation/references/campaign_template.txt \
  --personality-template ~/.hermes/skills/campaign-creation/references/personality_template.txt
```

Output: a pass/fail per item, with severity (ERROR / WARN / INFO) and a concrete fix instruction for each FAIL.

Then:

```bash
python3 ~/.hermes/skills/campaign-creation/scripts/section_completeness.py \
  /tmp/<bible>.md
```

Output: per-section character count + per-mechanic quantification check.

Both scripts run with no LLM. They are deterministic and exit non-zero on any ERROR.

## Output Format

A campaign-creation run produces:

- **The campaign bible** (Markdown or Google Doc, with all 9 sections + Personality Template Part 1 + Part 2)
- **A verification report** from `template_validator.py` showing all required sub-templates are present
- **A completeness report** from `section_completeness.py` showing every section is written out fully (no truncations)
- **A save receipt** (Google Doc ID + URL, or local file path)

If any report fails on ERROR, the run is NOT complete. Iterate until both reports pass.

## Cross-references

- **Authoritative source 1:** Google Doc ID `1kWl5zkpxMFO7tQb7C9NRuyhmgRKYmBIdHoNuWF9Q1fI` (Campaign Template). Local cache at `references/campaign_template.txt`.
- **Authoritative source 2:** Google Doc ID `1hYzTmydm1qE6o4Ipk8ChOlsF4PIy2BaF7PVW-coup68` (Character Personality Template). Local cache at `references/personality_template.txt`.
- **God-mechanics framework** (when protagonist ascends to divine tier): `references/god_mechanics_general.md` (local mirror of `world_reference/god_mechanics_general.md`).
- **Verified god-campaign design lessons** (Nocturne V2 redesign, 2026-07-21): `references/god-campaign-design-lessons.md` — the L20+ filter, OPTIMIZE→ROLL pattern, hybrid stats rationale, 5-resource cap, per-dawn choice menu template.
- **V3 god-mechanics recipe** (canonical 22-sub-mechanic pattern, 2026-07-21): `references/v3-god-mechanics-recipe.md` — load when asked for L20+ god-mechanics; applies P21 floor (20+ sub-mechanics) + V3.13.1 Chosen + V3.13.2 Avatar.
- **Real-LLM verification via agy CLI** (mandatory end-to-end test, 2026-07-21): `references/agy-cli-real-llm-verification.md` — load when you need to verify a mechanic overlay works on a real LLM (PR #8488 evidence bundle uses this recipe).
- **Iterating an existing campaign:** `~/.hermes/skills/campaign-design-iteration/SKILL.md`.
- **Auditing an existing campaign:** `~/.hermes/skills/worldarchitect/wa-campaign-content-analysis/SKILL.md`.
- **Downloading an existing Firestore campaign:** `~/.hermes/skills/download-campaign/SKILL.md`.

## Provenance

- v1.2.1 (2026-07-28): P24 codifies the user's recurring design philosophy (hidden apex → surprise → intimidation, no global aggregate trackers, no forced ruler-progression, custody as playable consequence, conditional exhaustion, anime flavor-only, per-NPC state). Verified `references/character-evolution-and-mystery-architecture.md` already carries the full v1.2.0 schemas (Want/Fear/Boundary, `[character_state_update]`, 16-type stress catalog, `mystery_state`, Personal-Growth Direction, Stress Arc & Insecurity Map, internal-drive plot arc check, Panoply–Retinue binding, verification recipes) — no rewrite needed; v1.2.0 set up the reference, v1.2.1 just closes the design-philosophy pitfall gap.
- v1.2.0 (2026-07-28): Character Evolution & Mystery Architecture. Added the "Character Evolution & Mystery Architecture" section before "When to load" covering the MBTI internal-only contract, the Want/Fear/Boundary state mutation rule, the MBTI stress arc, the AI-generated mystery template (hidden fact → 3-clue trail → 3 suspect branches), and the internal-drive plot arc rule (each act must advance growth direction, confront insecurity, or reframe a Want). Extended Personality Template Part 1.VI from 9 to 11 sub-sections with **Personal-Growth Direction** (lesson/healing/confrontation) and **Stress Arc & Insecurity Map** (stress pattern + 3-5 insecurities + surface patterns + mystery targeting). Step 5 (Retinue) now requires personal-growth direction + stress-arc + Want/Fear/Boundary for each retinue NPC, plus a panoply–retinue binding for at least 1 of the 3-5 panoply items. Step 9 (Section 8 Mechanics) gains the **Mystery Tracker** custom-mechanic option with the full `mystery_state` schema. Step 10 (Starting Scene) extended to require the first clue of an active mystery to surface. Added Pitfall P23 codifying the no-MBTI-in-player-facing-prose contract with a grep verification recipe. YAML frontmatter bumped to 1.2.0; description rewritten to reflect the new internal-drive engine. No external API dependencies added; remains deterministic + offline-friendly. The 11-step workflow, the two Google Doc template IDs (Campaign Template `1kWl5zk…`, Personality Template `1hYzTm…`), and the existing verifier scripts (`template_validator.py`, `section_completeness.py`) are unchanged.
- v1.1.0 (2026-07-21): V3 god-mechanics lessons encoded. Added Pitfalls P20 (double-placeholder artifact class — verified by Reviewer C on PR #8488 commit `9b8d09ccb8`), P21 (V3 mechanic density floor: 20+ sub-mechanics for L20+ god-campaigns), P22 (real-LLM evidence with `agy` CLI is the verification path). Added 2 references: `v3-god-mechanics-recipe.md` (canonical V3 sub-mechanics inventory) and `agy-cli-real-llm-verification.md` (recipe for end-to-end LLM testing).
- v1.0.0 (2026-07-20): Created per Jeffrey's request in Slack C0AH3RY3DK6/p1784585087.439909 ("I also want to follow these templates lets /skillify a campaign creation skill too"). Source templates were both fetched via `gog docs export` and cached locally. The skill encodes their structure verbatim into a deterministic 11-step workflow with two scripts (`template_validator.py`, `section_completeness.py`) and one test suite (`tests/test_campaign_creation_skill.py`).
