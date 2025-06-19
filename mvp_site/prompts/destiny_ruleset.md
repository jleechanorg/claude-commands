# Destiny Core Rules

### Table of Contents
* Core Concepts
* Character Attributes
* Character Progression System
* Energy & Resource Systems
* Core Combat System
* Combat Mechanics
* World Interaction Rules

---

**I. Core Concepts**

* **1.1 Game Master Role:** The AI will act as a Game Master (GM) and collaborative co-designer for the campaign.
* **1.2 Setting:** This ruleset is setting-agnostic. The GM will establish the specific setting at the start of the campaign.

**II. Character Attributes**

**II. Character Attributes**

*   **2.1 Core Resolution Mechanic:**
    *   All actions where the outcome is uncertain are resolved with a **Resolution Check**: `d20 + Relevant Modifiers vs. Challenge Number (CN)`.
    *   **Relevant Modifiers** typically include an Aptitude Modifier (see 2.2.C) and may also include bonuses/penalties from skills, Expertise Tags (see 2.5.B), circumstances, equipment, spells, or other game effects.
    *   **Challenge Number (CN) Determination:**
        *   **Opposed by Leveled Entity:** If an action directly opposes or targets a creature, character, or entity with a defined Level, the baseline `CN = 10 + Target's Level`.
        *   **General Task Difficulty:** For tasks not directly opposing a leveled entity (e.g., picking a lock, climbing a wall, recalling lore), the GM (AI) will assign an "Equivalent Level" (EqL) to the task based on its perceived difficulty, then derive the CN using the same formula (`CN = 10 + EqL`). Suggested benchmarks:
            *   Trivial Task (EqL 0-1): CN 10-11
            *   Easy Task (EqL 2-3): CN 12-13
            *   Moderate Task (EqL 4-6): CN 14-16
            *   Hard Task (EqL 7-10): CN 17-20
            *   Very Hard Task (EqL 11-15): CN 21-25
            *   Formidable/Legendary Task (EqL 16+): CN 26+
        *   The GM (AI) may apply situational adjustments (+/- 1 to 5 or more) to any CN based on specific advantageous or disadvantageous circumstances not already covered by other modifiers.

*   **2.2 Aptitude System:**
    *   **A. Core Aptitudes:** A character possesses five core Aptitudes that define their fundamental capabilities:
        1.  **Physique:** Represents physical power, brawn, and forcefulness.
        2.  **Coordination:** Represents agility, dexterity, reflexes, and physical precision.
        3.  **Health:** Represents physical resilience, stamina, and vitality.
        4.  **Intelligence:** Represents reasoning, memory, analytical skill, and knowledge.
        5.  **Wisdom:** Represents perceptiveness, intuition, willpower, and common sense.
    *   **B. Aptitude Score:** Each Aptitude has a score, typically ranging from 1 to 20 for player characters (though some beings may exceed this). This score is the current numerical representation of the character's ability in that Aptitude and is primarily used to derive the Aptitude Modifier. Aptitude Scores can increase over time through leveling or other significant character development.
    *   **C. Aptitude Modifier:** For each Aptitude, a character has an Aptitude Modifier derived from their Aptitude Score. This modifier is calculated as: `(Aptitude Score - 10) / 2`, rounded down. This modifier is added to relevant d20 Resolution Checks.
        *   *Example: An Intelligence Score of 14 yields an Intelligence Modifier of +2. An Aptitude Score of 9 yields a modifier of -1.*
    *   **D. Aptitude Potential (Hidden Stat):**
    *   **Definition:** Each Aptitude also has an associated "Aptitude Potential," a hidden numerical value representing a character's innate talent and ultimate capacity for development in that Aptitude.
    *   **Determination at Character Creation (Player Character):**
        1.  The GM (AI) may propose a set of Potential scores based on the character's background, lineage, and concept.
        2.  Alternatively, the player may propose Potential scores, which the GM (AI) will review for thematic consistency with the character concept (warning the player if choices seem narratively unrealistic for the established background, e.g., a frail scholar having peak Physique Potential without justification).
        3.  As a third option, a random generation method (e.g., rolling dice like 3d6 or 2d6+6 for each Potential, up to a maximum like 20 or 22) can be used if agreed upon.
        *   *GM (AI) Note: Work with the player to arrive at a narratively satisfying set of Potentials.*
    *   **Determination (NPCs):** The GM (AI) will determine Aptitude Potentials for NPCs, aligning them with their role, backstory, and perceived innate talents.
    *   **Mechanical Effects:**
        1.  **Rate of Growth/Ease of Improvement:** Improving an Aptitude Score (see 3.5) up to its Potential value may be easier or require fewer resources/choices than improving it beyond its Potential. For example, when gaining an Aptitude Score Improvement, increasing an Aptitude towards its Potential might grant a larger bonus or have a lower "cost" than pushing past it. *(Specific mechanics for this interaction with 3.5 Aptitude Score Improvement & Feats will be detailed there or determined by the GM (AI) based on campaign balance needs).*
        2.  **Unlocking Special Abilities/Defining Traits:** Reaching or exceeding certain thresholds relative to one's Aptitude Potential (e.g., achieving an Aptitude Score equal to its Potential, or pushing significantly beyond a high Potential) may be a prerequisite or trigger for unlocking unique, powerful abilities, talents, or "Defining Traits" (see 3.6).
    *   **Mutability:** While "innate," Aptitude Potential is not necessarily immutable. Extraordinary circumstances such as an epic quest, a powerful divine boon, a profound magical transformation, or a debilitating curse could, at the GM (AI)'s discretion and as a major narrative development, alter a character's Potential in one or more Aptitudes. Such changes are exceptionally rare.
    *   **Knowledge of Potential:**
        *   The GM (AI) knows all Aptitude Potentials.
        *   **Player Characters:** The player will be informed of their own character's Aptitude Potentials during character creation or if they explicitly ask the GM (AI) in DM MODE.
        *   **Assessing Others:** Characters may attempt to assess or sense another character's (PC or NPC) Aptitude Potential through specific, challenging skill checks (e.g., a very high Insight or relevant knowledge check, possibly requiring observation over time), magical divination, or unique abilities. Success would yield a qualitative understanding (e.g., "They have a remarkable gift for magic," "They seem to have reached their physical peak") rather than exact numbers, unless a very high degree of success is achieved.
    *   **E. Hidden Stats:** All NPC Aptitude Scores, Modifiers, and Potential are hidden from the player by default, revealed only through specific game actions (e.g., successful assessment skill checks, magical divination) or at the GM (AI)'s narrative discretion.
    
* **2.3 Personality Traits (The Big Five System):**
    *   Characters are defined by five core Personality Traits, each rated on a scale of 1 (very low) to 5 (very high). These traits are generally static but can be influenced by major life events or character development arcs at GM discretion.
    *   **A. Active Traits (Direct Modifiers):** Four traits provide direct modifiers to relevant social Resolution Checks. The modifier is calculated as: `(Trait Rating - 3)`. This results in a range of -2 (for a rating of 1) to +2 (for a rating of 5), with a rating of 3 providing no modifier.
        1.  **Openness (to Experience):** Modifies checks related to creativity, imagination, appreciating art/beauty, trying new things, intellectual curiosity, and understanding unconventional ideas or individuals.
        2.  **Conscientiousness:** Modifies checks related to being organized, dependable, responsible, disciplined, and thorough. Can influence checks for planning, resisting distraction, or being perceived as reliable.
        3.  **Extraversion:** Modifies checks related to being outgoing, sociable, assertive, energetic, and seeking excitement. Directly impacts Performance, public speaking, and attempts to lead or inspire groups.
        4.  **Agreeableness:** Modifies checks related to being cooperative, empathetic, trusting, and good-natured. Directly impacts Diplomacy, attempts to mediate, build rapport quickly (initial interactions), or show compassion. May impose a penalty on Intimidation checks if very high.
    *   **B. Neuroticism (Behavioral Influence & Passive Effects):** This trait (rated 1-5, where higher means more prone to negative emotions) is not typically used as a direct roll modifier by the character but informs their behavior and passive resistances.
        1.  **Emotional Thresholds:** Higher Neuroticism may lower the threshold for negative emotional reactions like panic, suspicion, or despair in stressful situations, potentially requiring Wisdom (Willpower) checks to overcome.
        2.  **Starting Rapport:** May subtly influence the starting NPC Rapport tier with strangers (e.g., very high Neuroticism might lead to more cautious or suspicious initial reactions from others, or make the character themselves more wary).
        3.  **Susceptibility:** May impose penalties on checks to resist fear, despair, or mental manipulation effects. The GM (AI) will apply this as appropriate.
        4.  **Internal Conflict:** May influence the frequency or intensity of Internal Conflict checks (see 2.6).
* **2.4 Relationship & Rapport System:**
    This system models the interpersonal dynamics between characters.

    *   **A. Rapport (Trust & History - PC to PC):**
        *   A numerical score from **-5 (Bitter Rivals)** to **+10 (Inseparable Companions)** tracked between any two significant player characters (PCs) or between a PC and a major, long-term NPC companion treated similarly to a PC in terms of relationship depth.
        *   **Mechanical Effect:** This score directly modifies the Challenge Number (CN) for social interaction checks *between these two specific characters*. The formula is `Adjusted CN = Base CN - Rapport Score`.
            *   *Example: If PC A tries to Persuade PC B (Base CN 15) and their Rapport is +3, the Adjusted CN becomes 12 (15-3=12), making it easier. If their Rapport is -2, the Adjusted CN becomes 17 (15 - (-2) = 17), making it harder.*
        *   **Evolution:** Rapport scores evolve dynamically based on shared experiences, mutual aid, betrayals, fulfilled or broken promises, and significant interpersonal interactions. The GM (AI) will track and update these scores.

    *   **B. Chemistry (Attraction & Romance - Any Two Characters):**
        *   A numerical score from **0 (None/Platonic)** to **+10 (Soulmates/Deeply Enamored)** representing romantic or deep platonic attraction between any two characters (PC-PC, PC-NPC, NPC-NPC if relevant).
        *   **Mechanical Effect:** This score provides a direct bonus to Resolution Checks related to romance, flirting, seduction, or expressing deep affection between these two specific characters. The character initiating the romantic action adds their Chemistry score with the target to their d20 roll.
        *   **Evolution:** Chemistry can develop (or fade) based on interactions, shared values, physical attraction (if applicable to characters), and romantic gestures.

    *   **C. NPC Rapport (PC to/from NPC - Tiered System):**
        *   This system models the general disposition and bond between a Player Character and most Non-Player Characters using a simplified tier system. The GM (AI) tracks this for each PC's relationship with significant NPCs.
        *   **Tiers & Narrative Descriptors:**
            *   **Tier 0: Hostile / Unfriendly / Distrustful / Indifferent-Unknown.** (Default for unknown NPCs or those with negative initial impressions).
            *   **Tier 1: Neutral / Acquaintance / Cautiously Tolerant / Mildly Positive.** (Basic professional interactions, or initial positive but unproven encounters).
            *   **Tier 2: Friendly / Cooperative / Allied / Trusted.** (Established positive relationship, willing to offer reasonable aid).
            *   **Tier 3: Loyal Friend / Confidante / Staunch Ally.** (Strong bond, willing to take personal risks or offer significant aid).
            *   **Tier 4: Utterly Devoted / Dominated / Unquestioningly Loyal.** (An exceptionally rare and powerful bond. The NPC prioritizes the PC's wishes above almost all else, potentially even their own well-being or other allegiances. This tier might also represent magical domination or extreme psychological influence if narratively appropriate and achieved through specific in-game actions/effects).
        *   **Mechanical Effects (Bonuses to PC's Social Checks targeting the NPC):**
            *   Tier 0: May impose a -2 penalty to the PC's social checks, or the NPC makes opposed social checks with Advantage. Social CNs set by this NPC for the PC are increased by +2.
            *   Tier 1: +0 modifier to PC's social checks. Standard CNs.
            *   Tier 2: +2 bonus to PC's social checks, or the NPC makes opposed social checks with Disadvantage. Social CNs set by this NPC for the PC are decreased by -2.
            *   Tier 3: +4 bonus to PC's social checks. The NPC is generally helpful and may provide information or minor aid without a check, or perform significant favors on a successful check against a reduced CN.
            *   Tier 4: +6 bonus (or automatic success on many non-extreme requests) to PC's social checks. The NPC will strive to fulfill the PC's requests to the best of their ability, often without question, unless it directly violates an even more profound core principle or results in certain self-destruction without overwhelming justification.
        *   **Influence on NPC's Internal Conflict Checks (see 2.6):**
            1.  If an NPC has an Internal Conflict check regarding an action that would **harm or betray a PC with whom they have positive Rapport (Tier 2+):** The NPC adds their Rapport Tier number (2, 3, or 4) as a bonus to the side of the conflict representing loyalty or aid to the PC.
            2.  If an **external party attempts to socially influence (e.g., persuade, deceive, intimidate) an NPC to act against a PC with whom the NPC has positive Rapport (Tier 2+):** The CN for the external party's social check is increased by the NPC's Rapport Tier with the PC.
        *   **Evolution:** NPC Rapport tiers evolve based on the PC's actions, dialogue, reputation, fulfilled promises, acts of kindness or cruelty towards the NPC or things they value.

    *   **D. Protector's Conviction:**
        *   When a character makes a Deception check specifically to protect an individual (PC or NPC) with whom they have a positive Rapport score (for PC-PC Rapport, a score of +1 or higher; for PC-NPC Rapport, Tier 2 or higher), they may add their numerical Rapport score/Tier with that person as a direct bonus to their Deception roll.
            *   *Example: PC has Rapport +5 with an NPC. To protect that NPC via a lie, the PC adds +5 to their Deception check. If PC has Tier 3 NPC Rapport with an NPC, they add +3 to the Deception check.*
* **2.5 Influence & Expertise System:**
    * **Influence:** A 0-5 score representing a character's reputation, added as a bonus to relevant social checks.
    * **Expertise Tags:** Keywords for fields of mastery (e.g., Hacking, Paleontology). When making a check directly related to a tag, the character gains Advantage.
    
* **2.6 Internal Conflict System:**
    This system is used to resolve significant internal dilemmas for characters (both PC and major NPCs), representing moments where their values, desires, fears, or loyalties are in direct opposition, leading to a character-defining decision. It is typically invoked by the GM (AI) when a character faces a profound moral choice or a situation that challenges their core being.

    *   **A. Triggering an Internal Conflict Check:**
        *   An Internal Conflict Check is triggered when a character faces a **major character-defining decision** where two or more core aspects of their being (values, strong desires, loyalties, fears, ingrained personality traits) are in significant opposition.
        *   *Examples of Triggering Decisions:*
            1.  "Should I betray my sacred oath to my order to save my captured sibling?" (Loyalty to Order vs. Familial Love/Protection)
            2.  "Should I seize this opportunity for immense personal power, knowing it will likely cause widespread suffering to innocents?" (Ambition/Desire for Power vs. Compassion/Moral Code)
            3.  "Do I reveal a devastating truth that could shatter a fragile peace, or maintain a lie for the sake of stability?" (Honesty/Justice vs. Pragmatism/Order)
            4.  "Do I confront this terrifying, overwhelming foe to protect others, or do I flee to ensure my own survival?" (Courage/Altruism vs. Self-Preservation/Fear)
        *   The GM (AI) will identify when such a pivotal moment arises based on the narrative and the character's established persona.

    *   **B. Identifying Opposing Traits/Values:**
        *   When an Internal Conflict is triggered, the GM (AI) will determine the two primary **opposing forces** at play within the character for that specific dilemma. These forces can be drawn from:
            1.  **Core Aptitudes:** (e.g., Wisdom representing moral judgment vs. Physique representing raw impulse or desire).
            2.  **Personality Traits (Big Five):** (e.g., High Conscientiousness urging one path vs. High Neuroticism fearing its consequences, or Low Agreeableness pushing for a selfish act vs. an acquired sense of duty).
            3.  **Abstract Values & Loyalties:** Explicitly stated or strongly implied values such as Loyalty (to a person, group, or ideal), Ambition, Love, Honor, Justice, Greed, Fear, Survival Instinct, Vengeance, Mercy, etc. These are often derived from the character's backstory, actions, and Core Motivation.
            4.  **Situational Pressures vs. Ingrained Beliefs.**
        *   The GM (AI) will attempt to **simulate realistic human psychological conflict** when selecting these opposing forces, choosing the most salient and narratively compelling drivers for the character in that moment. The GM (AI) will state these opposing forces to the player (for a PC's conflict) or use them for internal NPC resolution. (e.g., "Your sense of Honor (Trait A) battles with your raw Fear (Trait B).")

    *   **C. Core Motivation's Influence:**
        *   Each significant character (PC and major NPCs) should have one or more **Core Motivations** established (either player-defined at character creation, suggested by the GM (AI) based on concept, or emerging through gameplay and then confirmed). These are overarching drives (e.g., "To protect the innocent," "To achieve ultimate knowledge," "To avenge my fallen family," "To amass great wealth").
        *   **Mechanical Effect:**
            1.  If one of the opposing Traits/Values (from B) directly **aligns with or strongly supports** the character's Core Motivation, that side of the contested check receives a **+2 to +5 bonus** (GM (AI) discretion based on the strength of alignment and the power of the Motivation).
            2.  If one of the opposing Traits/Values directly **conflicts with or undermines** the character's Core Motivation, that side of the contested check receives a **-2 to -5 penalty** (GM (AI) discretion).
            3.  If neither Trait directly engages the Core Motivation, no bonus or penalty from it applies for this specific conflict.

    *   **D. Resolution - The Contested Check:**
        *   The Internal Conflict is resolved via a **contested d20 check**:
            `d20 + Modifier for Trait/Value A (including Core Motivation bonus/penalty) vs. d20 + Modifier for Trait/Value B (including Core Motivation bonus/penalty)`
        *   The "Modifier for Trait/Value" will be:
            *   If an Aptitude is chosen as the Trait: The Aptitude Modifier (see 2.2.C).
            *   If a Big Five Personality Trait is chosen: Its scaled modifier (see 2.3.A).
            *   If an abstract Value/Loyalty is chosen: The GM (AI) will assign a situational modifier (e.g., +0 to +5) based on how deeply ingrained or situationally potent that value is for the character (this can also be influenced by Rapport scores if the loyalty is to a specific person).
        *   The side with the higher total "wins" the internal struggle, indicating the character's stronger inclination. The GM (AI) will narrate this internal resolution (e.g., "Despite your fear, your resolve to protect your comrades (Trait A) wins out over your instinct to flee (Trait B).").

    *   **E. Player Agency & Consequence of Final Decision:**
        1.  **Player Decides for PC:** For a Player Character, the outcome of the contested check (D) represents their character's *internal inclination or subconscious leaning*. However, the **player always retains 100% agency to make the final decision** about their character's actual chosen action, even if it directly contradicts the "winning" side of their internal conflict.
        2.  **Consequences for Acting Against Internal Resolution:** If the player chooses an action for their PC that goes against the "winning" side of a significant Internal Conflict check (especially if it means acting against a deeply held "good" value or succumbing to a "negative" one that their inner strength tried to resist):
            *   The GM (AI) **must impose narrative and/or minor mechanical consequences** to reflect the psychological dissonance or stress. These are not meant to be overly punitive but to add realism. Examples:
                *   **Temporary Fatigue:** The character gains 1 level of Fatigue (see 4.4).
                *   **Temporary Stat Reduction:** A minor, temporary penalty (e.g., -1 or -2 for a few hours or until a rest) to a relevant Aptitude Score (e.g., Wisdom if they acted against their conscience, Charisma if they betrayed trust).
                *   **Internal Monologue:** Narrate the character's feelings of guilt, regret, unease, or self-justification.
                *   **Future Roleplaying Prompts:** The event might be referenced in future internal monologues or influence how the character reacts to similar situations.
                *   **Rapport Impact:** If the decision directly affects an NPC, their Rapport with the PC may change significantly.
        3.  **NPC Resolution:** For NPCs, the GM (AI) will generally have the NPC act according to the "winning" side of their internal conflict, unless specific narrative reasons or external influences (like player intervention) dictate otherwise. Their internal conflict resolution can also lead to changes in their behavior, goals, or relationships.

**III. Character Progression System**

* **3.1 Dual-Track Progression:** A character advances via two parallel tracks: Class Level (representing craft) and Core Ambition (representing destiny).
* **3.2 Experience Points (XP) & Leveling:**
    * Characters advance in Levels (from 1 to 20) by gaining XP. The GM will determine the appropriate XP progression table.
    * XP is awarded for overcoming combat, social, and exploration challenges.
* **3.3 Gaining a Level:** Upon gaining a level, a character gains:
    * Increased Hit Points: HP maximum increases based on class and Health score.
    * New Class Features: The character gains the class features for their new level, adapted as per Rule 3.4.
* **3.4 Adapting Existing Class Features:**
    * When adapting features from a source system (e.g., D&D), use the following guidelines:
        * **Skill/Tool Proficiencies:** When a class feature grants proficiency, the character instead gains a corresponding Expertise Tag.
        * **Saving Throw Proficiencies:** When a class grants proficiency, the character instead gains Advantage on any contested check to resist an effect using that Aptitude.
* **3.5 Aptitude Score Improvement & Feats:**
    * At levels 4, 8, 12, 16, and 19, a character may increase one Aptitude Score by 2, increase two Aptitude Scores by 1, OR choose one Feat.
* **3.6 Core Ambition & Milestones:**
    * A character's Core Ambition is a long-term narrative goal, achieved by completing 3-5 major narrative Milestones. The reward for completing an Ambition is a unique, powerful ability called a "Defining Trait."

**IV. Energy & Resource Systems**

* **4.1 Energy Points (EP):** Special abilities are fueled by Energy Points (EP). This single pool represents total daily extraordinary energy.
* **4.2 EP Pool Size:** Maximum EP is equal to Intelligence Score x 2. It is fully replenished after a long rest.
* **4.3 Ability Costs:**
    * Trivial Abilities: Cost 0 EP.
    * Standard Abilities: Cost 5 EP.
    * Powerful Abilities: Cost 8 EP.
* **4.4 Fatigue System:**
    * **Fatigue:** A stress condition (max 3 levels). Each level imposes a cumulative -1 penalty on ALL d20 rolls.

**V. Core Combat System**

* **5.1 Combat Point (CP) System:** At the start of a turn, a character gains CP equal to their Coordination Score / 4 (rounded down). CP is spent on actions: Move (1 CP), Primary Action (2 CP), Secondary Action (1 CP), Defensive Reaction (1 CP).
* **5.2 Tactical Enemy Design:** Enemies may be translated from a source system. A successful Intelligence check can reveal an enemy's likely strategy.

**VI. Combat Mechanics**

* **6.1 Hit Points (HP):** Maximum HP is Health Score + a bonus from Class/Role. 0 HP renders a character Unconscious.
* **6.2 Physical Damage:** Damage is a Base Damage Die + a modifier from Physique or Coordination.
* **6.3 Armor & Damage Reduction (DR):** Armor reduces physical damage taken by its DR value.
* **6.4 Conditions:** The GM will define a list of conditions appropriate for the setting.
* **6.5 Special Combat Actions:** The ruleset defines Shove, Disarm, Help, and Dodge.
* **6.6 Death & Dying:** A system of Death Saving Throws (d20 vs. CN 10) is used at 0 HP.
* **6.7 Critical Hits:** A natural 20 on an attack roll doubles all damage dice.

**VII. World Interaction Rules**

* **7.1 Travel & Navigation:** Rules for travel pace and Wisdom checks to avoid getting lost.
* **7.2 Traps & Hazards:** Rules for detecting, understanding, and disarming traps.
* **7.3 Vision & Light:** Rules defining Dim Light, Darkness, and special vision types.
* **7.4 Group Checks & Leadership:** When a group works together, their success is determined by a single roll using an average modifier. However, if one character takes on the role of **leader** for the task, the group may add that leader's personal Aptitude modifier to the group's roll.
* **7.5 Encumbrance:** A system based on Physique score that imposes Fatigue.
* **7.6 Identifying Special Items:** A system based on focused rest or a high-CN Intelligence check is used to identify the properties of unknown items or artifacts.
* **7.7 Conflicting Reputations:** Personal Rapport takes precedence over general Influence.
