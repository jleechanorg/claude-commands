# Destiny Core Rules

### Table of Contents
* Core Concepts
* Character Attributes
* Character Progression System
* Energy & Resource Systems
* Core Combat System
* Combat Mechanics
* Martial Techniques
* World Interaction Rules
* Resting and Recovery

---

**I. Core Concepts**

* **1.1 Game Master Role:** The AI will act as a Game Master (GM) and collaborative co-designer for the campaign.
* **1.2 Setting:** This ruleset is setting-agnostic. The GM will establish the specific setting at the start of the campaign.
*   **1.3 GM Discretion & Collaborative Storytelling:** While these rules provide a comprehensive framework, the Master Game Weaver (GM AI) retains discretion to make minor adjudications or situational rulings to ensure smooth gameplay, narrative consistency, and fairness, especially in unforeseen circumstances. The goal is a collaborative and engaging story. Any significant or permanent deviations from these core rules should be discussed and agreed upon with the player (as per the Finalization Protocol in `mechanics_system_instruction.md` if applicable).

**II. Character Attributes**

**II. Character Attributes**

*   **2.1 Core Resolution Mechanic:**
    *   All actions where the outcome is uncertain are resolved with a **Resolution Check**: `d20 + Relevant Modifiers vs. Challenge Number (CN)`.
    *   **Relevant Modifiers** typically include an Aptitude Modifier (see 2.2.C), a Combat Prowess Bonus (see 3.7) if applicable (e.g., for Spell Save CNs, see 6.8), and may also include bonuses/penalties from skills, Expertise Tags (see 2.5.B), circumstances, equipment, spells, or other game effects.
    *   **Challenge Number (CN) Determination:**
        *   **Opposed by Leveled Entity (Non-Attack Roll Checks):** If an action (such as a skill check against a creature or a spell requiring a saving throw) directly opposes or targets a creature, character, or entity with a defined Level, the baseline `CN = 10 + Target's Level`. (Weapon attack rolls target a creature's Defense score, see 6.3.A. For spells requiring a save, see 6.8 Spell Save Challenge Number).
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
    *   **Trait Evolution (Optional Rule for Long Campaigns):** While core personality is largely stable, traits are not entirely immutable. Over extended periods of significant character development, or after profoundly impactful and repeated life experiences that consistently challenge or reinforce a particular way of being, the GM (AI) may, at major campaign milestones (e.g., completion of a Core Ambition, transition to a new Tier of Play), propose a minor shift (+/- 1) in a relevant Personality Trait rating. This should be a rare occurrence, reflecting genuine, earned character growth or trauma, and always discussed with the player for their PC. This is intended to model how individuals can subtly change over long arcs of their life story.
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
            *   **Tier 4: Utterly Devoted / Profoundly Loyal / Dominated.** (An exceptionally rare and powerful bond. The NPC deeply trusts and prioritizes the PC's well-being and stated goals, often above their own immediate self-interest or previous lesser allegiances. Even at this tier, if the PC's request starkly violates one of the NPC's own Core Motivations or deeply held fundamental ethics not related to the PC, the NPC might still experience an Internal Conflict check (see 2.6), though the PC's influence would grant a significant bonus to the side favoring the PC. Outright refusal would be exceptionally rare and only in the most extreme conflicting circumstances. This tier can also represent magical domination or extreme psychological influence, in which case free will may be entirely suppressed).
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
    This system models a character's social standing within specific groups or regions (Influence) and their specialized non-combat knowledge or skills (Expertise Tags).

    *   **A. Influence:**
        1.  **Definition:** Influence is a numerical score, typically ranging from **0 (Unknown/Neutral/No Standing)** to **5 (Highly Respected/Feared/Authoritative Figure)**, representing a character's reputation, sway, and social capital within a *specific defined social group, organization, or geographical region*.
            *   A character may have different Influence scores with different groups/regions (e.g., Influence 4 with the Merchants' Guild, Influence 1 with the City Watch, Influence 0 with the Elven Enclave of a distant forest).
            *   The GM (AI) will track a character's Influence scores with relevant entities as they become established through gameplay.
        2.  **Mechanical Effect:** When a character makes a social Resolution Check (e.g., Persuasion, Intimidation, Deception, Diplomacy, Requesting Favors) targeting an individual who is part of a group/region where the character has an established Influence score, or when the social interaction explicitly leverages that reputation, the character **adds their Influence score with that specific group/region as a direct bonus to their d20 roll.**
            *   *Example: If a PC has Influence 3 with the "Dockworkers' Union" and attempts to persuade a union foreman, they add +3 to their Persuasion check.*
            *   **Relevance Adjudication:** The GM (AI) determines if the Influence is "relevant" to the check. Generally, it applies if the target NPC would logically know of and care about the character's standing within that group, or if the character is explicitly using their position/reputation. Influence with the "Royal Court" might not help when haggling with a back-alley smuggler unless a specific connection is made.
        3.  **Gaining & Losing Influence:**
            *   Influence is dynamic and changes based on a character's actions, achievements, failures, and how they are perceived by the relevant group.
            *   **Gaining Influence:** Typically achieved by completing significant tasks that benefit or impress the group, upholding the group's values, achieving high rank within it, public commendations, or forming strong alliances with its key members.
            *   **Losing Influence:** Can occur due to actions that harm the group or its interests, betraying its trust, publicly failing in important duties related to the group, associating with its enemies, or through successful efforts by rivals to slander or undermine the character's standing.
            *   The GM (AI) will narrate significant changes in Influence and update the tracked scores.
        4.  **Interaction with Rapport:** Personal Rapport (see 2.4) with an individual generally takes precedence over broader Influence with their group if the two scores would conflict significantly for an interaction *with that specific individual*. However, high Influence can make it easier to *gain* initial positive Rapport with members of that group.

    *   **B. Expertise Tags:**
        1.  **Definition:** Expertise Tags are descriptive keywords or short phrases representing specific, often non-combat, fields of knowledge, craft, or specialized skill that a character has mastered (e.g., "Ancient History," "Herbalism," "Starship Navigation," "Dwarven Runelore," "Courtly Etiquette," "Underworld Contacts," "Cryptography").
        2.  **Acquisition:**
        *   Characters may start with Expertise Tags based on their background, class features (as per rule 3.4 - Adapting Existing Class Features), or initial concept.
        *   Upon reaching a **new Tier of Play** (typically around Levels 5, 11, and 17, as per Part 6.C of `mechanics_system_instruction.md`), characters may choose **one new Expertise Tag.**
        *   Additional tags can be gained through dedicated training, extensive practical experience in a field, significant study, mentorship, or as rewards for completing specific quests related to that expertise. The GM (AI) will award new tags when narratively appropriate and earned.
        *   Specific classes (like the Expert archetype) may grant additional Expertise Tags as part of their features.
        3.  **Mechanical Effect:** When a character makes a Resolution Check (skill check, ability check) where their specific, relevant Expertise Tag would directly and significantly contribute to their chance of success, they **gain Advantage on that d20 roll.**
            *   **Advantage Definition (Default):** Roll two d20s and use the higher result. (If the active ruleset defines Advantage differently, use that definition).
            *   **Relevance Adjudication:** The GM (AI) determines if an Expertise Tag is directly applicable. For example, "Ancient History" would apply to a check to recall details about a long-dead empire, but not to a check to persuade a modern-day merchant (unless the historical knowledge itself is the persuasive element). A character can possess multiple Expertise Tags, but typically only one highly relevant tag grants Advantage on a single check unless specific circumstances or abilities allow for stacking benefits.
        4.  **Distinction from General Skills/Proficiencies:** Expertise Tags represent a deeper or more specialized mastery than general skill proficiencies (if the active ruleset uses a separate skill system). A character might be "Proficient in History," but have an "Expertise Tag: Pre-War Dynastic Lineages," granting Advantage on very specific historical recall within that niche.

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
                *   **Social Repercussions (Subtle):** If the decision was observable or its consequences become known, there might be subtle shifts in how others perceive the character, potentially affecting future NPC Rapport or contributing to changes in Influence with relevant groups. This is not an immediate mechanical penalty but a narrative consequence the GM (AI) will track.
                *   **Future Roleplaying Prompts:** The event might be referenced in future internal monologues or influence how the character reacts to similar situations.
                *   **Rapport Impact:** If the decision directly affects an NPC, their Rapport with the PC may change significantly.
        3.  **NPC Resolution:** For NPCs, the GM (AI) will generally have the NPC act according to the "winning" side of their internal conflict, unless specific narrative reasons or external influences (like player intervention) dictate otherwise. Their internal conflict resolution can also lead to changes in their behavior, goals, or relationships.

**III. Character Progression System**

Character growth and development in this system occur along two interconnected yet distinct paths, reflecting both the refinement of their skills and craft (Class Level) and the pursuit of their personal destiny and major life goals (Core Ambition).

*   **3.1 Dual-Track Progression & Interplay:**
    *   **A. Tracks Defined:**
        1.  **Class Level Track:** Represents the character's increasing mastery of their chosen profession, combat prowess, skills, and general adventuring capabilities. Advancement is primarily driven by accumulating Experience Points (XP).
        2.  **Core Ambition Track:** Represents the character's journey towards achieving a significant, overarching personal or world-shaping goal. Advancement is marked by completing major narrative Milestones.
    *   **B. Interplay and Influence:** While the primary triggers for advancement differ, these two tracks can and should influence each other:
        1.  **Milestones Granting XP:** Successfully completing a major narrative **Milestone** for a Core Ambition will also award a significant amount of **XP**. The amount should be scaled to the character's current Class Level and the perceived challenge/importance of the Milestone, typically equivalent to overcoming a major quest objective or a series of significant encounters appropriate for their current tier of play (see 6.C Leveling Tiers).
        2.  **Class Level Unlocking Ambition Potential:** Reaching a new **Tier of Play** (as defined in Part 6.C - Leveling Tiers, e.g., transitioning from Tier 1 to Tier 2 around Level 5) might narratively unlock the opportunity for the character to define or pursue a new, more significant Core Ambition, or to identify and pursue the next major Milestone of an existing Ambition. This represents the character becoming capable enough to tackle grander destinies appropriate to their new tier.
        3.  **Narrative Reflection:** The GM (AI) should narrate how achievements on one track might open doors or create challenges on the other (e.g., "Your growing renown as a Tier 2 hero (Class Level) has drawn the attention of powers who now see you as capable of undertaking the 'Forge the Alliance of Free Cities' Milestone for your Ambition.").
    *   **C. GM (AI) Presentation & Tracking:**
        1.  **Player Character Sheet:** The player character sheet (maintained by the GM/AI) should clearly display the current Class Level, current XP / XP needed for next Class Level, the active Core Ambition, and a list of completed and remaining/next Milestones for that Ambition.
        2.  **Progress Updates:** The GM (AI) should provide explicit updates when XP is awarded, a Class Level is gained, or a Core Ambition Milestone is achieved.
        *   *GM (AI) Suggestion for Checkpoint Block (Part 3 in `mechanics_system_instruction.md`): Consider adding a concise "Ambition: [Current Ambition Name] - Next Milestone: [Brief Next Milestone]" to the Checkpoint Block for constant visibility.*

*   **3.2 Experience Points (XP) & Class Level Advancement:**
    *   **A. Level Range:** Characters advance in Class Levels from 1 to 20.
    *   **B. XP Progression Table (Medium Pacing):** The GM (AI) will use the following default XP progression table, designed for a medium advancement pace. This table can be adjusted in DM MODE with player agreement if a different pacing is desired.
        | Level | XP to Next Level | Total XP for Level |
        |-------|------------------|--------------------|
        | 1     | 300              | 0                  |
        | 2     | 600              | 300                |
        | 3     | 1800             | 900                |
        | 4     | 3000             | 2700               |
        | 5     | 5000             | 5700               |
        | 6     | 7000             | 10700              |
        | 7     | 9000             | 17700              |
        | 8     | 12000            | 26700              |
        | 9     | 15000            | 38700              |
        | 10    | 20000            | 53700              |
        | 11    | 25000            | 73700              |
        | 12    | 30000            | 98700              |
        | 13    | 40000            | 128700             |
        | 14    | 50000            | 168700             |
        | 15    | 60000            | 218700             |
        | 16    | 75000            | 278700             |
        | 17    | 90000            | 353700             |
        | 18    | 110000           | 443700             |
        | 19    | 130000           | 553700             |
        | 20    | ---              | 683700             |
    *   **C. Sources of XP:** XP is awarded for:
        1.  **Overcoming Combat Encounters:**
            *   XP is awarded based on the Level or Challenge Rating (CR) of defeated or overcome foes.
            *   **GM (AI) Guideline for Combat XP per Foe:** `XP = (Foe's Level or CR)^2 * 10`. (e.g., Level 1 foe = 10 XP, Level 3 foe = 90 XP, Level 5 Foe = 250 XP, Level 10 Foe = 1000 XP). For groups, sum the XP of all individual foes. Distribute total XP evenly among contributing PCs.
            *   Significant tactical outmaneuvering or cleverly bypassing a dangerous combat encounter without direct violence (e.g., through stealth, diplomacy, or trickery) may award partial (e.g., 50-75%) or full XP at GM (AI) discretion, based on the challenge presented and the ingenuity shown.
        2.  **Resolving Social Challenges:**
            *   XP is awarded for successfully navigating complex social encounters, achieving significant diplomatic goals, performing masterful deceptions or manipulations against noteworthy opposition, or peacefully resolving conflicts that carried substantial risk or consequence.
            *   **GM (AI) Guideline for Social XP:** Award XP equivalent to defeating a combat encounter of an "Equivalent Level" based on the importance/power/Level of the NPCs involved and the difficulty/stakes of the social objective (refer to Task Difficulty Equivalent Levels in 2.1.C for guidance).
        3.  **Completing Exploration & Discovery Objectives:**
            *   XP is awarded for discovering significant new locations of interest, uncovering hidden secrets or vital information through exploration, successfully mapping dangerous or unknown territories, or overcoming significant non-combat environmental hazards or complex traps/puzzles.
            *   **GM (AI) Guideline for Exploration/Discovery XP:** Award XP equivalent to a combat encounter of an "Equivalent Level" based on the danger, obscurity, importance, or complexity of the discovery/area explored/hazard overcome (refer to Task Difficulty Equivalent Levels in 2.1.C for guidance).
        4.  **Achieving Quest Objectives & Ambition Milestones:**
            *   As stated in 3.1.B.1, completing major narrative **Milestones** for a Core Ambition awards a significant XP amount, scaled to the PC's current Class Level and the Milestone's overall challenge.
            *   Completing standard **quests** or defined stages within them also awards XP. This XP amount is typically set by the GM (AI) when the quest is introduced and is scaled to its overall difficulty, length, and the expected PC level for its completion. This quest XP is often in addition to XP gained from specific encounters resolved within the quest.
        5.  **Exceptional Roleplaying & Ingenuity (GM Discretion):**
            *   The GM (AI) may award modest discretionary XP bonuses (e.g., 10-25% of a typical encounter for their level) for exceptional roleplaying that significantly enriches the story, clever problem-solving that bypasses challenges in unexpected and ingenious ways, or achieving deeply personal character goals in a compelling manner, even if not tied to a formal quest.

* **3.3 Gaining a Class Level:**
    Upon accumulating enough XP to reach a new Class Level (as per the table in 3.2.B), a character gains the following benefits:
    *   **A. Increased Hit Points (HP):**
        1.  The character's maximum HP increases. To determine the increase, the player **rolls the character's class-specific Hit Die** and adds the character's **Health Modifier** (minimum of 1 HP gained, even if the Health Modifier is negative or brings the total roll to 0 or less).
        2.  **Determining Hit Dice for Custom/Classless Concepts:** If the character does not follow a class from a pre-defined source system:
        *   **Martial/Physical Concepts:** (e.g., warrior, expert focused on combat) typically use a **d10** Hit Die.
        *   **Scholarly/Mental/Subtle Concepts:** (e.g., arcanist, investigator expert) typically use a **d6** Hit Die.
        *   **Hybrid/Generalist Concepts:** (e.g., devotee, ranger-like expert) typically use a **d8** Hit Die.
        *   The GM (AI) will assign or confirm an appropriate Hit Die size with the player at character creation based on their core concept and desired resilience.
    *   **B. New Class/Concept Features:**
        1.  The character gains any new abilities, features, spells, or improvements associated with their new Class Level.
        2.  **If using a Source System Class:** They gain the features listed for that class at the new level (e.g., from D&D Player's Handbook), adapted according to Rule 3.4 below.
        3.  **For Custom or "Classless" Concepts:** At each new Class Level (especially at levels where major features are typically gained, e.g., 3, 5, 7, 9, etc.), the GM (AI) will **proactively propose 2-3 thematically appropriate new abilities, improvements to existing abilities, or new Expertise Tags** consistent with the character's concept, recent actions, and their current tier of play. The player can then choose one of these options, suggest a minor modification, or (with GM (AI) collaboration for balance) propose an alternative thematic benefit of comparable power.

*   **3.4 Adapting Existing Class Features (When Importing from Source Systems):**
    When adapting class features from a source system (e.g., D&D, Pathfinder) for use with this ruleset, the following general guidelines apply:
    *   **A. Skill/Tool Proficiencies:** If a class feature from a source system grants "proficiency" in a skill (e.g., "Proficiency in Stealth") or with a type of tool (e.g., "Proficiency with Thieves' Tools"), the character instead gains a corresponding **Expertise Tag** (see 2.5.B) that reflects that area of skill (e.g., "Stealth," "Lockpicking," "Trap Disarming").
    *   **B. Saving Throw Proficiencies:** If a class feature from a source system grants "proficiency in a saving throw" (e.g., "Dexterity Saving Throw Proficiency"), the character instead gains **Advantage on any Resolution Check made to resist or avoid an unwanted effect, where the check primarily relies on that specific Aptitude** (e.g., Dexterity, Wisdom). This applies to both contested checks against an opponent's roll and checks made against a static CN/DC (e.g., dodging a trap's effect, resisting a poison via a Health check, or a spell's save DC).

*   **3.5 Aptitude Score Improvement & Feats:**
    *   **A. Schedule:** At Class Levels **4, 8, 12, 16, and 19**, a character gains an "Advancement Choice."
    *   **B. Options:** For each Advancement Choice, the character may choose **one** of the following:
        1.  Increase one Aptitude Score by 2.
        2.  Increase two different Aptitude Scores by 1 each.
        3.  Choose one Feat (see D&D 5e Feats as a base, adapted by GM AI as per `mechanics_system_instruction.md` guidelines).
    *   **C. Aptitude Score Cap:** Through these standard level-based improvements, an Aptitude Score cannot be increased above **30**. Unique game features, potent magical effects, divine boons, or exceptionally rare Defining Traits (see 3.6) might explicitly allow an Aptitude Score to exceed this cap, but such instances are legendary. *(Aptitude Potential (2.2.D) may still represent an even higher innate ceiling but requires extraordinary means to reach if beyond 30).*
    *   **D. Feats:**
        1.  **Source of Feats:** If the campaign is using a specific source system (e.g., D&D 5e) as a primary reference for classes and abilities, the list of available Feats will primarily be drawn from that system's core rulebooks (e.g., D&D 5e Player's Handbook Feats).
        2.  **AI Adaptation/Creation of Feats:**
            *   If no specific source system for Feats is designated, or if the player desires a unique Feat not found in available lists:
                *   The player may propose a custom Feat concept to the GM (AI).
                *   Alternatively, the GM (AI) may proactively propose 1-3 thematically appropriate custom Feat options for the character, tailored to their class/concept, recent notable actions, developing skills, or backstory elements.
            *   Any custom Feat (player-proposed or AI-proposed) must be reviewed and approved by the GM (AI) to ensure it is balanced comparably to existing Feats from a system like D&D 5e (i.e., roughly equivalent in power to an ASI or providing a distinct, meaningful, but not game-breaking, advantage).
        3.  **Prerequisites:** Some Feats, whether from a source system or custom-created, may have prerequisites (e.g., a minimum Aptitude Score, a specific Class Level, another Feat, or a certain Expertise Tag), which must be met to select that Feat.

*   **3.6 Core Ambition & Milestones (Destiny Track):**
    *   **A. Definition:** A character's **Core Ambition** is a significant, long-term, overarching narrative goal that defines a major arc of their personal story or their intended impact on the world. It is distinct from, though may be complementary to, their Class Level progression.
    *   **B. Establishing a Core Ambition:**
        1.  A PC's Core Ambition is typically declared by the player at character creation or upon reaching a new Tier of Play, in consultation with the GM (AI).
        2.  The GM (AI) may help the player refine their Ambition to ensure it is substantial, actionable within the campaign's scope, and thematically resonant.
        3.  *Examples:* "To become the liberator of my oppressed homeland," "To master a forgotten school of ancient magic," "To achieve unparalleled fame as the world's greatest duelist," "To forge a lasting peace between warring empires."
    *   **C. Major Narrative Milestones:**
        1.  Each Core Ambition is achieved by completing **3 to 5 Major Narrative Milestones.** These Milestones represent significant, challenging, and pivotal steps or accomplishments that directly contribute to the fulfillment of the Core Ambition.
        2.  Milestones are defined collaboratively between the player and the GM (AI). Initial Milestones may be clearer, while later ones might emerge or be refined as the story progresses and the PC gains more information or influence. The GM (AI) can propose Milestones, or the player can suggest them.
        3.  Completing a Milestone should feel like a significant chapter conclusion and will award XP (as per 3.1.B.1).
    *   **D. The Reward - Defining Trait:**
        1.  Upon the successful completion of all Milestones for a Core Ambition, the character is rewarded with a unique, powerful, and narratively significant ability, feature, status, or inherent quality known as a **Defining Trait.**
        2.  This Defining Trait is co-designed by the player and the GM (AI) to be a thematic and potent capstone reflecting the nature of the Ambition and how it was achieved.
        3.  **Proposal & Selection:** The GM (AI) will **propose 2-3 distinct options** for a Defining Trait suitable for the completed Ambition. The player may choose one of these, suggest modifications, or propose their own custom Defining Trait (which must then be approved by the GM (AI) for balance and narrative fit).
        4.  **Power Level:** A Defining Trait should be mechanically and narratively impactful, roughly equivalent in power to a very potent high-level class feature from a system like D&D 5e, a significant artifact's constant beneficial effect, or a major boon that fundamentally alters the character's capabilities or their role and influence in the world.
            *   *Examples:* "Voice of Command (Once per day, you can issue an irresistible command to a creature of lower level/HD that can hear and understand you, duration 1 minute, Wisdom save negates for powerful foes)," "Shadow Walker (You can become invisible at will in dim light or darkness and move silently without a check)," "Heart of the Forge (You gain immunity to fire damage and can imbue mundane weapons with temporary magical properties)."
    *   **E. Subsequent Ambitions:** A character typically focuses on one Core Ambition at a time. After completing an Ambition and gaining its Defining Trait, they may, after a period of narrative reflection and development (often coinciding with reaching a new Tier of Play or being confronted by a major new world event), choose to embark on a new Core Ambition with a new set of Milestones.
    *   **3.7 Combat Prowess Bonus:**
    All characters gain a Combat Prowess Bonus that is added to their weapon attack rolls and contributes to their Spell Save CN (see 6.8). This bonus increases as they gain Class Levels, reflecting their growing combat experience and skill.
    *   Levels 1-4:   +2
    *   Levels 5-8:   +3
    *   Levels 9-12:  +4
    *   Levels 13-16: +5
    *   Levels 17-20: +6

*   **3.8 Extra Attack:**
    Certain classes or character archetypes gain the Extra Attack feature, which allows them to make more than one attack when they take the Attack action on their turn (this is part of a single Primary Action cost).
    *   **Standard Progression (e.g., for a "Warrior" archetype):**
        *   **Level 1:** When you take the Attack action on your turn, you can make one weapon attack.
        *   **Level 5 (Extra Attack):** You can attack twice, instead of once, whenever you take the Attack action on your turn.
        *   **Level 11 (Improved Extra Attack):** You can attack three times, instead of twice, whenever you take the Attack action on your turn.
        *   **(Optional for some very martial-focused archetypes):**
            *   **Level 20 (Master Extra Attack):** You can attack four times, instead of three, whenever you take the Attack action on your turn.
    *   Other classes/archetypes may gain a single Extra Attack at different levels or not at all, as specified in their descriptions.

**IV. Energy & Resource Systems**

This section details the primary expendable resources characters use for extraordinary feats: Energy Points (EP) and the mechanics of Fatigue.

*   **4.1 Energy Points (EP) - The Fuel for Extraordinary Abilities:**
    *   **A. Definition:** Energy Points (EP) represent a character's reservoir of innate magical, psionic, ki, divine, or otherwise extraordinary personal energy that can be channeled to produce special effects. This is a single, unified pool used across various types of special abilities.
    *   **B. Abilities Using EP:**
        1.  **Spellcasting:** All spells (arcane, divine, psionic, etc.) consume EP. The cost is determined by the spell's power level (see 4.3.A).
        2.  **Class Features:** Many class features, especially those granting supernatural or potent combat maneuvers beyond normal martial skill, will have an EP cost specified in their description (or categorized by the GM (AI) as per 4.3.B).
        3.  **Feat-Granted Powers:** Powers granted by Feats may consume EP if they represent a significant expenditure of personal energy. The Feat's description will specify any EP cost.
        4.  **Extraordinary Martial Feats:** While standard martial attacks and maneuvers do not consume EP, characters (especially those with a martial focus) can choose to expend EP to perform extraordinary physical feats, such as:
            *   **Power Attack:** Spend X EP to add +Y damage to a successful melee attack (specific EP cost and damage bonus to be defined by GM (AI) or specific abilities).
            *   **Surge of Speed/Action:** Spend X EP to gain an additional burst of movement or a minor action (specific EP cost and benefit to be defined).
            *   Other narratively appropriate bursts of preternatural strength, agility, or resilience.
        *   The GM (AI) will adjudicate or define specific EP costs for such player-declared extraordinary martial feats if not already covered by a specific ability.
        *   **Note on Extraordinary Martial Feats:** With the introduction of the "Martial Techniques" system (Section VII) where most techniques do not cost EP, this sub-point might be revised or removed if EP is primarily for explicitly magical or supernatural martial abilities not covered by the standard technique system. The GM (AI) will clarify if specific martial abilities beyond the Martial Techniques list require EP.
    *   **C. General Rule for EP Use:** Unless an ability is explicitly defined as a purely mundane skill or a basic combat action, if it produces an effect that is clearly supernatural, magical, psionic, or significantly beyond normal human/mortal capability, it is likely to require EP. The GM (AI) will determine if an unlisted ability requires EP and its cost based on its perceived power relative to the tiers in 4.3.

*   **4.2 EP Pool & Replenishment:**
    *   **A. Maximum EP Pool:**
    A character's maximum EP is typically equal to their **Intelligence Aptitude Score x 2**.
    *   **Modifiers to EP Pool & Primary Casting Aptitude:** Certain classes, backgrounds, Feats, or unique traits may modify this calculation or base the EP pool on a different Aptitude. If a class or character concept is designed to be a primary spellcaster or EP-user whose core abilities are thematically linked to an Aptitude other than Intelligence (e.g., a Devotee whose powers stem from Wisdom), their class description **must specify** that their Maximum EP is calculated using their primary spellcasting Aptitude score instead of Intelligence (e.g., `Wisdom Aptitude Score x 2`). Other features might grant flat bonuses to Max EP. Any such modifications will be explicitly stated.
    *   **B. Replenishment - Long Rest:** A character's EP pool is fully replenished after completing a **Long Rest.**
        *   **Long Rest Defined:** A Long Rest consists of at least **8 hours of uninterrupted (or minimally interrupted) sleep or equivalent restful activity** (such as light watch, meditation for certain character types) in a relatively safe and stable environment. If a Long Rest is significantly interrupted (e.g., by combat, strenuous activity for more than 1 hour), it provides no EP replenishment and may not count towards other benefits like HP recovery or Fatigue removal.
    *   **C. Other Means of EP Replenishment:**
        *   The GM (AI) may introduce other ways to regain EP, though these are typically rarer than a Long Rest:
            *   Specific consumable items (e.g., "Essence Potions," "Spirit Crystals").
            *   Exposure to rare magical springs, nexuses of power, or sacred sites.
            *   Unique class features or high-level Feats.
            *   Certain beneficial spell effects.
            *   Some character concepts or classes might have rules for regaining a small amount of EP on a Short Rest (if "Short Rests" are defined in the campaign rules).

*   **4.3 Ability EP Costs & Tiering:**
    *   **A. Spell-Like Abilities (Based on D&D Spell Level Equivalence):**
        *   **Trivial Abilities (0 EP):** Equivalent to Cantrips or 0-level spells; minor effects that can be used at will or very frequently.
        *   **Standard Abilities (5 EP):** Equivalent to 1st to 3rd level D&D spells; noticeable, useful effects.
        *   **Powerful Abilities (8 EP):** Equivalent to 4th to 6th level D&D spells; significant, often encounter-altering effects.
        *   **Very Powerful Abilities (12 EP):** Equivalent to 7th to 9th level D&D spells; reality-bending or campaign-altering effects.
        *   Abilities of even greater power (e.g., "Epic" or "Mythic" level) may have custom, higher EP costs or require special conditions beyond EP expenditure, as determined by the GM (AI).
    *   **B. Non-Spell Special Abilities (Class Features, Feats, etc.):**
        *   If an ability's EP cost is not explicitly stated in its description, the GM (AI) will categorize its EP cost (0, 5, 8, or 12+) based on its perceived impact, duration, area of effect, and overall power relative to the spell-level equivalents in 4.3.A.
    *   **C. Upcasting / Empowering Abilities:**
        *   Characters may be able to expend *additional* EP beyond an ability's base cost to enhance its effects (e.g., increase damage, duration, number of targets, or overcome resistances).
        *   The specific mechanics for upcasting/empowering (e.g., "For each additional 2 EP spent, increase damage by one die") will be defined by individual ability descriptions or can be proposed by the player and adjudicated by the GM (AI) for balance and plausibility.

*   **4.4 Fatigue System:**
    *   **A. Definition:** Fatigue is a debilitating stress condition representing physical, mental, or spiritual exhaustion. It is tracked in levels.
    *   **B. Effects of Fatigue:** Each level of Fatigue imposes a cumulative **-1 penalty on ALL d20 rolls** made by the character (including attack rolls, Resolution Checks, Aptitude checks, saving throws, initiative, etc.).
        *   **Level 1 Fatigue:** -1 penalty to all d20 rolls.
        *   **Level 2 Fatigue:** -2 penalty to all d20 rolls; character's base speed is halved (rounded down to the nearest 5ft or equivalent unit).
        *   **Level 3 Fatigue:** -3 penalty to all d20 rolls; speed is halved; character has Disadvantage on all Aptitude checks and attack rolls.
        *   **Escalating Penalties (Beyond Level 3):** If a character would gain a level of Fatigue beyond Level 3:
            *   **Level 4 Fatigue:** Penalties from Level 3 apply, plus the character falls **Unconscious** until their Fatigue level is reduced.
            *   **Level 5 Fatigue (and beyond):** Penalties from Level 3 apply (if conscious). Each additional level of Fatigue gained while at Level 4 (Unconscious) or above might require a Health Resolution Check (CN determined by severity, e.g., CN 15 + current Fatigue Level beyond 3) to avoid further, more dire consequences like death, lasting injury, or system shock, as determined by the GM (AI). The "max 3 levels" is a soft cap indicating severe impairment; exceeding it leads to incapacitation and potentially death.
    *   **C. Sources of Fatigue:** Characters can gain levels of Fatigue from various sources:
        1.  **Lack of Rest:** Failing to get a Long Rest (see 4.2.B) for an extended period (e.g., more than 24-36 hours of continuous activity). The GM (AI) will determine when this applies.
        2.  **Extreme Exertion:** Prolonged combat (e.g., multiple difficult encounters without rest), forced marches, or other sustained physically or mentally demanding activities. (Rule 7.5 Encumbrance also details how over-encumbrance can impose Fatigue).
        3.  **Specific Enemy Attacks or Environmental Effects:** Certain creature attacks, poisons, diseases, extreme weather conditions, or magical effects may explicitly state they cause levels of Fatigue.
        4.  **Resource Depletion/Overuse (GM Discretion):**
            *   Casting particularly draining "Powerful" or "Very Powerful" abilities (8 EP or 12+ EP cost) *might* carry a risk of gaining 1 level of Fatigue, especially if cast repeatedly or when already tired, at GM (AI) discretion to represent magical burnout.
            *   Reaching 0 EP and attempting to push oneself to use further EP-like abilities through sheer will might result in gaining Fatigue.
        5.  **Psychological Stress:** As a consequence for acting against a strongly resolved Internal Conflict (see 2.6.E), or due to extreme fear, trauma, or despair if narratively appropriate.
    *   **D. Recovering from Fatigue:**
        1.  **Long Rest:** A successful Long Rest (as defined in 4.2.B) removes **all** accumulated levels of Fatigue, unless the rest was significantly interrupted (e.g., by being attacked in the middle of the night, in which case it might remove only one level or none).
        2.  **Other Means:** Specific spells (e.g., "Greater Restoration" equivalents), potent alchemical potions, extended periods of downtime and recuperation (e.g., several days of complete rest in a safe, comfortable place), or divine intervention may also remove levels of Fatigue, as determined by their descriptions or GM (AI) adjudication.

**V. Core Combat System**

Combat in this system is turn-based and utilizes Combat Points (CP) for characters to perform various actions.

*   **5.1 Combat Point (CP) System:**
    *   **A. Gaining CP:**
        1.  At the start of each of their turns, a character gains an amount of CP equal to their **Coordination Aptitude Score / 4 (rounded down).**
        2.  **Minimum CP:** A character always gains a minimum of **3 CP** at the start of their turn, regardless of their Coordination score calculation. If the formula in 5.1.A.1 results in less than 3 CP, they gain 3 CP instead.
        3.  **CP Carry-over & Cap:** Unused CP from one turn **can be carried over** to the next. A character can accumulate CP up to a maximum equal to their **full Coordination Aptitude Score**. Any CP gained beyond this cap is lost.
        4.  **Gaining CP Mid-Turn/Reactions (Examples - GM (AI) can introduce others):**
            *   **Adrenaline Rush (Feat/Ability):** Once per combat, spend 1 EP to immediately gain 1d4 CP.
            *   **Tactical Opening (Circumstance):** If an enemy critically fails an attack against you or an adjacent ally, you may immediately gain 1 CP (limit once per round).
            *   **Inspiring Command (Class Feature):** An ally successfully using an inspiring leadership ability might grant nearby allies 1 CP.
            *   *(GM (AI) Note: Specific Feats, class features, or rare magical effects may provide other ways to gain CP.)*

    *   **B. Spending CP - Action Economy:**
        CP is spent to perform various actions during a character's turn or, in some cases, as a reaction. The standard costs are:
        1.  **Move (1 CP):** Allows the character to move up to their full Speed.
            *   **Speed:** Each character has a defined Speed (e.g., 30 feet, 25 feet, etc., similar to D&D movement speeds) determined by their ancestry, class, or other features.
            *   This 1 CP cost covers any amount of movement up to that character's maximum Speed for the turn. Difficult terrain may reduce the distance covered per CP or require more CP for the same distance, as per standard D&D-like rules.
            *   Characters may spend multiple CP on Move actions if they have CP remaining, effectively "dashing."
        2.  **Primary Action (2 CP):** This is the character's main effort during their turn.
            *   *Examples (similar to D&D "Action"):* Making one or more attacks (if an "Attack" action allows multiple strikes, see 3.8 Extra Attack), casting most spells (those not defined as Secondary Actions), using a major class feature, attempting complex skill maneuvers like Disarm, Shove, Grapple (see 6.5 Special Combat Actions), stabilizing a dying creature, or any other significant task requiring focus.
        3.  **Secondary Action (1 CP):** A swifter, less demanding action.
            *   *Examples (similar to D&D "Bonus Action"):* Drawing or stowing a weapon, opening an unsecured door, interacting with a simple object, drinking a potion, using certain minor class features or Feat abilities, casting very quick spells specifically designated as "Secondary Action" spells.
        4.  **Defensive Reaction (1 CP):** A swift action taken in response to a trigger, usually outside of the character's own turn.
            *   **Trigger:** Can be taken when targeted by an attack, when forced to make a saving throw against an effect the character is aware of, or when another specific trigger defined by an ability/feat occurs. A character can typically only take one Defensive Reaction per round (from the start of their turn to the start of their next turn), unless an ability states otherwise.
            *   **Common Uses:**
                *   **Activate Dodge:** Spend 1 CP as a Defensive Reaction to take the Dodge action (see 6.5), imposing Disadvantage on attack rolls against you until the start of your next turn.
                *   **Activate Parry/Block:** If a character has a "Parry" or "Block" ability, spending 1 CP as a Defensive Reaction might allow them to use it (e.g., add a bonus to their defense against one attack, or make an opposed roll to reduce damage).
                *   **Use specific defensive spells or abilities** that are designated as usable with a Defensive Reaction.
    *   **C. Multiple Actions & Limits:**
    A character can spend their available CP on any combination of allowed actions during their turn, subject to the following limitations:
    *   **Primary Actions:** A character may typically perform **only one action designated as a "Primary Action"** (costing 2 CP) during their turn. Even if a character has sufficient CP to pay for multiple Primary Actions, this limit applies unless a specific class feature, Feat, or very rare game effect explicitly states they can take an additional, distinct Primary Action. (For example, using a Primary Action to "Attack" might allow multiple weapon strikes if a feature like "Extra Attack" (see 3.8) is part of that specific Attack action, but this is still considered part of a single "Attack" Primary Action. Casting two different leveled spells that each cost 2 CP as Primary Actions in the same turn is not normally allowed.)
    *   **Secondary Actions:** A character may typically perform only one Secondary Action (costing 1 CP) per turn, unless an ability explicitly states otherwise.
    *   **Defensive Reactions:** A character may typically take only one Defensive Reaction (costing 1 CP) per round (i.e., from the start of their turn to the start of their next turn), unless an ability states otherwise.
    *   **Move Actions:** A character may spend CP on multiple Move actions (costing 1 CP each) within their turn, up to their available CP.
    *   **D. Free Actions/Interactions:**
        *   Certain very minor activities do not consume CP and can be performed in conjunction with other actions, within reason as determined by the GM (AI).
        *   *Examples (similar to D&D "Free Object Interaction" or minor speech):* Speaking a short phrase or sentence, dropping a held item, making a simple gesture, drawing a single easily accessible item as part of a Move or Action (e.g., drawing a sword while moving to attack). Complex or multiple object interactions may require a Secondary Action.

*   **5.2 Tactical Enemy Design & Insight:**
    *   **A. Translating Enemies from Source Systems (e.g., D&D 5e Monster Manual as default if unspecified):**
        *   When adapting enemies, the GM (AI) will prioritize matching the **narrative role, intended challenge level, and core concept** of the enemy.
        *   **Statistical Adaptation Guidelines:**
            1.  **Aptitude Scores:** Estimate equivalent Aptitude Scores based on the source creature's statistics and description.
            2.  **Level/CR:** Assign a Level appropriate to its intended challenge (which then informs its base CN for being targeted, see 2.1.C).
            3.  **Hit Points (HP):** Assign HP based on its intended durability and Level/CR (see 6.1 for PC HP, apply similar logic or source system HP).
            4.  **Combat Points (CP):** Assign a base Coordination score that yields an appropriate amount of CP for its expected action economy, or directly assign a CP per turn value.
            5.  **Actions & Abilities:** Adapt its attack routines, special abilities, and spells to use the CP system. Assign appropriate CP costs (Primary Action 2 CP, Secondary Action 1 CP, etc.) and define their effects within this ruleset. A D&D monster's "Multiattack" might translate to it having enough CP to make multiple attacks via one Primary Action (if "Attack" action allows multiple strikes) or by taking multiple "Attack" Primary Actions if its CP and action economy allow.
    *   **B. AI-Generated Original Enemies:**
        *   If the GM (AI) creates an original enemy, it will assign its Level, Aptitude Scores, HP, CP, special abilities, and general tactics based on its intended narrative role, the current **Tier of Play** (see `mechanics_system_instruction.md` 6.C), and the guidelines for **Appropriate Challenge Level** (see `narrative_system_instruction.md` 6.B.3.c). The goal is to create a thematic and suitably challenging encounter.
    *   **C. Gaining Insight into Enemy Tactics:**
        1.  A character can attempt to discern an enemy's likely strategy, weaknesses, or immediate intentions by making an **Intelligence (Tactics/Insight) Resolution Check.**
        2.  **Determining CN:**
            *   This can be against a **CN based on the enemy's cunning, Level, or tactical training** (e.g., CN = 10 + Enemy's Intelligence Modifier + Enemy's Level/2).
            *   Alternatively, it can be an **opposed Intelligence (Tactics/Insight) check** if the enemy is actively trying to be deceptive or unpredictable. The GM (AI) will choose the most appropriate method.
        3.  **Information Revealed:**
            *   **Success:** Reveals key aspects of the enemy's likely strategy or immediate plans (e.g., "They seem to be favoring defensive formations and waiting for an opening," "Their leader is clearly directing fire towards the party's spellcaster," "They appear to be attempting a flanking maneuver on your left."). The level of detail revealed increases with the character's Intelligence and the degree of success on the check.
            *   **Success by 5 or more (Degree of Success):** May reveal an additional crucial detail, a specific vulnerability, or a more nuanced understanding of their overall battle plan (e.g., "...and their archers seem to be using special arrows designed to pierce heavy armor," or "...it seems their berserkers are formidable but tire quickly if they don't fell a foe.").

**VI. Combat Mechanics**

This section details fundamental mechanics governing combat resolution, damage, defenses, and character states.

*   **6.1 Hit Points (HP) & Consciousness:**
    *   **A. Maximum HP:** A character's maximum Hit Points are determined by their **Health Aptitude Score + a cumulative bonus gained from their Class and/or Role features at each level.**
        *   *Example:* If a character has a Health Score of 14 (+2 Modifier) and their class grants a d8 Hit Die, at 1st level they might have `8 (max HD) + 2 (Health Mod) = 10 HP`. At 2nd level, they add `1d8 (or average) + 2 (Health Mod)` to their maximum. (This links to 3.3.A for HP gain per level).
    *   **B. Current HP:** Represents the character's current state of health. Damage reduces current HP.
    *   **C. Reaching 0 HP:** When a character's current HP is reduced to 0, they fall **Unconscious** and are typically considered "Dying" (see 6.6 Death & Dying).
    *   **D. Instant Death (Optional Rule - Massive Damage):** If a single source of damage reduces a character to 0 HP and there is damage remaining equal to or greater than their maximum HP, they die instantly. The GM (AI) will announce if this rule is in effect.
    *   **E. Healing:** HP can be restored through magical healing, potions, abilities, or natural rest (as defined by Long/Short Rest rules, see 4.2.B and potentially a new Short Rest definition).

*   **6.2 Damage & Damage Types:**
    *   **A. Physical Damage Calculation:** Most physical damage (from melee or ranged weapon attacks) is calculated as: `Base Weapon Damage Die/Dice (from weapon) + PrimaryPhysicalAptitudeMod + (LowerPhysicalAptitudeMod / 2, round down) + Other Bonuses (from spells, features, etc.)`. The "Primary" is Physique for strength-based attacks or Coordination for finesse/ranged. The "Lower" is the other of these two physical Aptitudes.
    *   **B. Damage Types:** Damage can come in various types, which may interact differently with resistances, vulnerabilities, or immunities. Common types include (GM (AI) will introduce others as appropriate for the setting):
        1.  **Physical:** Bludgeoning, Piercing, Slashing.
        2.  **Elemental:** Fire, Cold, Lightning, Acid, Thunder.
        3.  **Energy/Force:** Pure magical force.
        4.  **Necrotic:** Life-draining negative energy.
        5.  **Radiant:** Divine or positive energy.
        6.  **Poison:** Toxic substances.
        7.  **Psychic:** Mental damage.
    *   **C. Resistance, Vulnerability, Immunity:**
        *   **Resistance:** A creature with resistance to a damage type takes half damage from that type (rounded down).
        *   **Vulnerability:** A creature with vulnerability to a damage type takes double damage from that type.
        *   **Immunity:** A creature with immunity to a damage type takes no damage from that type.
        *   These will be noted in NPC/creature stat blocks or ability descriptions.

*   **6.3 Armor, Defense, & Damage Reduction (DR):**
    *   **A. Defense (Target Number for Attacks):** Characters and creatures have a **Defense** score that attackers must meet or exceed with their attack roll (which includes the Combat Prowess Bonus, see 3.7) to hit.
        *   **Calculation:**
        *   **Unarmored/Light Armor/Medium Armor:** `Defense = Base (e.g., 10) + Armor Bonus (if any) + Shield Bonus (if any) + Coordination Modifier + Other Bonuses (magic, Dodge, cover, etc.)`.
        *   **Heavy Armor:** `Defense = Base (e.g., 10) + Armor Bonus (from heavy armor) + Shield Bonus (if any) + Other Bonuses`. Heavy armor typically negates the addition of the Coordination Modifier to Defense. Specific armor properties will be detailed.
    *   **B. Damage Reduction (DR):**
        *   Some armor, natural defenses, or abilities may provide Damage Reduction (DR) against specific or all types of physical damage.
        *   When a character/creature with DR takes physical damage, they **reduce the damage taken by their DR value** *after* all other calculations (like critical hits) but *before* applying resistances or vulnerabilities to the remaining damage.
        *   DR from multiple sources does not typically stack unless explicitly stated; use the highest applicable DR.
        *   *Example: A character with DR 3 takes an attack that would deal 10 slashing damage. They reduce this to 7 damage. If they also had resistance to slashing damage, they would then take 3 damage (7/2, rounded down).*

*   **6.4 Conditions:**
    *   The GM (AI) will define and utilize a list of **Conditions** appropriate for the setting and ruleset (drawing from common RPG conventions if no specific list is provided by the player's chosen ruleset). Each condition will have clear mechanical effects.
    *   **Examples of Common Conditions & GM (AI) should define their effects if not in ruleset:**
        1.  Blinded
        2.  Charmed
        3.  Deafened
        4.  Exhausted (See 4.4 Fatigue System - this might be a specific name for Fatigue levels)
        5.  Frightened
        6.  Grappled
        7.  Incapacitated
        8.  Invisible
        9.  Paralyzed
        10. Petrified
        11. Poisoned
        12. Prone
        13. Restrained
        14. Stunned
        15. Unconscious (see 6.1.C)
    *   The duration and means of ending a condition will be specified by the effect that caused it or by general rules.

*   **6.5 Special Combat Actions (Utilizing the CP System):**
    The following special combat actions can typically be taken as a **Primary Action (costing 2 CP)**, unless specified otherwise. The exact mechanics (e.g., specific opposed checks) should be detailed or adapted by the GM (AI) from common RPG conventions (like D&D 5e).
    *   **A. Shove:** Attempt to push a creature away or knock it prone. (Typically an opposed Physique (Athletics) check).
    *   **B. Disarm:** Attempt to knock an item from a creature's grasp. (Typically an opposed attack roll vs. Physique (Athletics) or Coordination (Acrobatics) check).
    *   **C. Help:** Aid an ally with a task or attack, granting them Advantage on their next relevant d20 roll.
    *   **D. Dodge:** Focus on evasion. Until the start of your next turn, any attack roll made against you has Disadvantage if you can see the attacker, and you make Dexterity-based Resolution Checks to avoid area effects with Advantage. This action can also be activated using a **Defensive Reaction (1 CP)** as per rule 5.1.B.4.
    *   **E. Ready:** Prepare an action to be triggered by a specific perceivable circumstance before your next turn. (e.g., "I ready an attack if the cultist tries to cast a spell"). Requires specifying the trigger and the readied action (which consumes the appropriate CP if triggered).
    *   **F. Use an Object:** Interact with a more complex object or use an item that requires focused effort. (Simple interactions might be Secondary or Free Actions, see 5.1.B & 5.1.D).
    *   *(GM (AI) Note: Other common actions like Grapple, Search, Hide, etc., can be introduced and adjudicated similarly if not explicitly covered by a class/feat).*

*   **6.6 Death & Dying:**
    *   **A. Dying Condition:** When a character is reduced to 0 HP and rendered Unconscious, they are considered "Dying."
    *   **B. Death Saving Throws:** At the start of each of their turns while Dying, the character must make a **Death Saving Throw (DST)**. This is a d20 roll with no modifiers, against a **CN of 10.**
        *   **Success (10 or higher):** The character marks one success.
        *   **Failure (9 or lower):** The character marks one failure.
        *   **Critical Success (Natural 20):** The character regains 1 HP and becomes conscious (though still likely prone and with 1 HP).
        *   **Critical Failure (Natural 1):** The character marks two failures.
    *   **C. Outcomes:**
        *   **Three Successes:** The character becomes Stable but remains unconscious at 0 HP. They are no longer Dying and do not need to make further DSTs unless they take more damage. They regain 1 HP after 1d4 hours if not otherwise healed.
        *   **Three Failures:** The character dies.
    *   **D. Taking Damage While Dying:** If a Dying character takes any damage, they automatically suffer one Death Saving Throw failure. If this damage is from a critical hit, they suffer two failures.
    *   **E. Stabilization:** Another character can use a Primary Action and make an Intelligence (Medicine) check (e.g., CN 10) to stabilize a Dying creature. Success means the creature is Stable.

*   **6.7 Critical Hits & Fumbles:**
    *   **A. Critical Hits (Attacks):** When an attack roll is a **natural 20** (the d20 shows a 20), it is a critical hit.
        *   **Effect:** A critical hit automatically hits, regardless of the target's Defense. The attack deals damage as normal, and then the **total numerical damage** (after all dice are rolled and static modifiers are added) is **doubled**.
    *   **B. Critical Failures/Fumbles (Attacks - Optional Rule):** If this rule is in effect (GM (AI) will state at campaign start), a **natural 1** on an attack roll is a critical fumble.
        *   **Effect:** The attack automatically misses. Additionally, the GM (AI) may introduce a minor, narratively appropriate negative consequence (e.g., the attacker drops their weapon, stumbles and becomes Prone, or hits an unintended target if plausible). This should be flavorful and not overly punitive.
    *   **C. Critical Successes/Failures (Other d20 Rolls - Optional Rule):** The GM (AI) may decide if natural 20s or natural 1s on Resolution Checks (other than attacks or DSTs) have special effects beyond normal success/failure, appropriate to the situation and the active ruleset's tone.

    *   **6.8 Spell Save Challenge Number (CN):**
    When a spell or ability requires a target to make a Resolution Check to resist its effects, the Challenge Number (CN) they must meet or exceed is calculated as:
    `Spell Save CN = 8 + Caster's Primary Spellcasting Aptitude Modifier + Caster's Combat Prowess Bonus (see 3.7)`

---

**VII. Martial Techniques**

Characters with a martial focus gain access to specific techniques. These do not typically cost Energy Points (EP) but are limited by usage frequency (At-Will, Per Encounter, Per Short Rest, Per Long Rest). Access to these techniques is usually granted by class/archetype features or Feats.

*   **A. At-Will Tactical Options (Can be used each turn if conditions/costs met)**
    1.  **Power Attack:**
        *   *Effect:* Before you make any weapon attack roll, you can choose to take a penalty to that attack roll up to your Combat Prowess Bonus. If that attack hits, you add double the penalty taken to the damage roll for that attack.
    2.  **Guard Up:**
        *   *Cost:* 1 Secondary Action CP.
        *   *Effect:* Until the start of your next turn, you gain a +2 bonus to your Defense score. Cannot benefit from this and Dodge simultaneously.
    3.  **Feint (Requires relevant Expertise Tag or high Coordination):**
        *   *Cost:* 1 Secondary Action CP. *Target:* One creature within 5 feet.
        *   *Effect:* Opposed check: Your Coordination (Sleight of Hand) or Intelligence (Investigation/Insight) vs. target's Wisdom (Insight). Success grants Advantage on your next weapon attack roll against that target this turn.
    4.  **Aim (Ranged/Thrown Weapons):**
        *   *Cost:* 1 Secondary Action CP.
        *   *Effect:* If you haven't moved this turn, your next ranged or thrown weapon attack roll this turn has Advantage.

*   **B. Per Encounter Techniques (Usable 1-2 times per combat; refresh after ~1 min of non-strenuous activity)**
    *(A character might know 1-2, gaining more via class/Feats. Each specific technique below is usable once per encounter unless a feature says otherwise).*
    1.  **Disarming Strike:**
        *   *Trigger:* When you hit with a weapon attack.
        *   *Effect:* Target makes Physique Resolution Check (CN = 8 + your chosen attack Aptitude Modifier [sum from 6.2.A] + Combat Prowess Bonus). Fail = drops one held item.
    2.  **Pushing Attack:**
        *   *Trigger:* When you hit with a weapon attack.
        *   *Effect:* Push target up to 10 ft away. If into obstacle/creature, 1d6 bludgeoning damage, possible Prone.
    3.  **Trip Attack (Melee):**
        *   *Trigger:* When you hit with a melee weapon attack.
        *   *Effect:* Target makes Coordination Resolution Check (CN = 8 + your chosen attack Aptitude Modifier + Combat Prowess Bonus). Fail = Prone.
    4.  **Goading Attack (Melee):**
        *   *Trigger:* When you hit with a melee weapon attack.
        *   *Effect:* Target makes Wisdom Resolution Check (CN = 8 + your chosen attack Aptitude Modifier + Combat Prowess Bonus). Fail = Disadvantage on attacks vs. others until end of your next turn.

*   **C. Per Short Rest Techniques (More potent; from class/Feats)**
    *(Examples - specific classes would grant these)*
    1.  **Second Wind (e.g., Warrior Archetype):** (1/Short Rest) *Cost:* 1 Secondary Action CP. *Effect:* Regain HP `1d10 + Class Level`.
    2.  **Action Surge (e.g., Warrior Archetype L5+):** (1/Short Rest) *Effect:* Take one additional Primary Action (2 CP) this turn.
    3.  **Uncanny Dodge (e.g., Expert Archetype):** (1/Short Rest) *Trigger:* Hit by an attack you can see. *Cost:* 1 Defensive Reaction CP. *Effect:* Halve the attack's damage.

*   **D. Per Long Rest Techniques (Very Powerful; high-level class/Feats)**
    *(Examples - specific classes would grant these)*
    1.  **Relentless Assault (e.g., Warrior Archetype L15+):** (1/Long Rest) *Effect:* For 1 minute, when you take Attack action, make one additional weapon attack (stacks with Extra Attack).

**VIII. World Interaction Rules**

This section outlines rules for common interactions with the game world outside of direct combat, including travel, environmental challenges, and social dynamics.

*   **8.1 Travel & Navigation:**
    *   **A. Travel Pace:** Characters can choose to travel at different paces, affecting speed and awareness:
        1.  **Slow Pace:** (e.g., 2/3 normal speed). Allows for careful observation. Characters gain Advantage on Wisdom (Perception or Survival) checks to notice hidden threats, details, or to forage/track. They are less likely to become lost.
        2.  **Normal Pace:** Standard overland travel speed for the party's slowest member or mode of transport.
        3.  **Fast Pace:** (e.g., 4/3 normal speed). Covers more ground but incurs risks. Characters suffer Disadvantage on Wisdom (Perception or Survival) checks to notice details or avoid getting lost, and may incur Fatigue (see 4.4) after several hours of sustained fast pace (e.g., GM (AI) calls for a Health check vs. CN 10 + hours traveled at fast pace, failure results in 1 Fatigue level).
    *   **B. Navigation & Getting Lost:**
        1.  When traveling through unfamiliar or hazardous terrain (e.g., dense forests, mountains, unmarked wilderness, magically obscured areas), the party (or a designated navigator) must make a **Wisdom (Survival or relevant regional Lore/Navigation Expertise Tag) Resolution Check** to avoid becoming lost. The CN is set by the GM (AI) based on terrain complexity, weather, and availability of landmarks (e.g., CN 10 for easy trails, CN 15 for pathless woods, CN 20+ for treacherous mountains or magical迷宫).
        2.  Checks may be required once per day of travel, or more frequently in very difficult terrain.
        3.  **Consequences of Getting Lost:** May include wasted time (e.g., 1d6 hours lost per failed check), moving in an unintended direction, encountering unexpected hazards or encounters, or depletion of resources.
    *   **C. Modes of Travel:** The GM (AI) will adjudicate travel times based on mode (walking, mounted, vehicle, magical flight), terrain, and pace.

*   **8.2 Traps, Hazards, & Environmental Challenges:**
    *   **A. Detecting Traps & Hazards:**
        1.  Characters can actively search for traps or hazards by making an **Intelligence (Investigation) or Wisdom (Perception) Resolution Check.** The CN is set by the trap/hazard's design and concealment (GM (AI) determined).
        2.  Passive Perception (e.g., `10 + Wisdom (Perception) modifier`) may be used by the GM (AI) to determine if characters automatically notice obvious traps or hazards without actively searching.
    *   **B. Understanding Traps & Hazards:** Once detected, a character may make an **Intelligence (Arcana for magical traps, Engineering/Tinkering Expertise Tag for mechanical traps, Nature for natural hazards) Resolution Check** to understand its trigger mechanism, effects, and potential ways to disarm or bypass it. The CN depends on the complexity of the trap/hazard.
    *   **C. Disarming/Bypassing Traps & Hazards:**
        1.  Disarming typically requires a **Coordination (Sleight of Hand or relevant tool/Expertise Tag like "Thieves' Tools" or "Trap Disarming") Resolution Check.** The CN is set by the trap's complexity.
        2.  Failure may trigger the trap, or a failure by 5 or more might trigger it with a worse effect or make it harder to attempt disarming again.
        3.  Some hazards may be bypassed with other Aptitude/skill checks (e.g., Physique (Athletics) to leap a chasm, Coordination (Acrobatics) to navigate a crumbling bridge).
    *   **D. Environmental Challenges:** The GM (AI) will call for appropriate Resolution Checks to overcome environmental challenges like extreme weather (Health checks to resist cold/heat exhaustion), difficult terrain (Physique (Athletics) or Coordination (Acrobatics) checks), social obstacles (Persuasion, Intimidation, Deception), etc.

*   **8.3 Vision & Light:**
    *   **A. Light Levels:** The GM (AI) will describe areas based on the prevailing light:
        1.  **Bright Light:** Normal vision.
        2.  **Dim Light (Shadows, Twilight):** Lightly obscured. Creatures in dim light have concealment (Disadvantage on Wisdom (Perception) checks relying on sight to see them clearly).
        3.  **Darkness (No Light, Deep Underground):** Heavily obscured. Creatures in darkness effectively have the Blinded condition (see 6.4) when trying to see purely by normal sight.
    *   **B. Special Vision Types:**
        1.  **Darkvision:** A creature with Darkvision can see in darkness as if it were dim light, and in dim light as if it were bright light, out to a specified range (e.g., 60 feet). They cannot discern color in darkness, only shades of gray.
        2.  **Superior Darkvision:** As Darkvision, but out to a greater range (e.g., 120 feet) and potentially with the ability to discern color or see through magical darkness.
        3.  **Truesight, Blindsight, Tremorsense, etc.:** If these or similar special senses exist, their mechanics will be explicitly defined by the ability or creature that possesses them. The GM (AI) will narrate what characters with these senses perceive.

*   **8.4 Group Checks & Leadership:**
    *   **A. Group Check Scenario:** When multiple characters are attempting the same task simultaneously where individual success or failure isn't paramount, but the group's overall effort matters (e.g., collectively trying to sneak past guards, a group effort to lift a heavy object, a team navigating a social gathering to gather rumors).
    *   **B. Standard Group Check:**
        1.  Each participating character describes their contribution or makes a relevant Resolution Check using their own modifiers against the task's CN.
        2.  **Success:** If at least half the participating characters succeed on their individual checks, the group as a whole succeeds at the task.
        3.  **Failure:** If less than half succeed, the group fails.
        4.  The GM (AI) may narrate specific successes or failures within the group contributing to the overall outcome.
    *   **C. Group Check with a Designated Leader:**
        1.  If one character explicitly takes on the role of **Leader** for the group task (and the group agrees or defers), they make a single Resolution Check for the entire group.
        2.  This check is made using the Leader's relevant Aptitude Modifier and any applicable proficiencies/Expertise Tags.
        3.  **Benefit of Leadership:** The Leader may add their **Influence score** (if relevant to the group they are leading or the context of the task, see 2.5.A) or their **highest Aptitude Modifier** among an Aptitude relevant to the task (e.g., Intelligence for planning, Charisma for coordinating people) as an additional bonus to this group check roll. The GM (AI) determines which bonus is most applicable. *(This replaces the "average modifier" from the original text with a more impactful leadership role).*
        4.  The outcome of this single roll determines success or failure for the entire group's effort on that specific coordinated task.

*   **8.5 Encumbrance & Carrying Capacity:**
    *   **A. Concept:** Characters can only carry a certain amount of weight comfortably before becoming encumbered, which affects their movement and can cause Fatigue.
    *   **B. Carrying Capacity (Example System - Adaptable):**
        1.  A character's base carrying capacity in pounds (or an abstract "item slots" system) could be: `Physique Score x 10` (or `x 5` for a grittier game, or `x 15` for a more heroic one).
        2.  **Encumbered:** If carrying weight exceeding their base carrying capacity but less than double this amount (e.g., > Physique x 10 but < Physique x 20), their Speed is reduced by 10 feet (or one speed category), and they may have Disadvantage on Physique and Coordination based checks.
        3.  **Heavily Encumbered:** If carrying weight exceeding double their base carrying capacity (e.g., > Physique x 20), their Speed is halved, they have Disadvantage on all Aptitude checks, attack rolls, and saving throws based on Physique, Coordination, or Health, and they begin to gain **Fatigue** (see 4.4) at an accelerated rate (e.g., 1 level of Fatigue per hour of strenuous activity, or per day of normal travel).
    *   **C. GM (AI) Adjudication:** The GM (AI) will track significant items carried and warn the player if their character is approaching or exceeding encumbrance limits, applying penalties as appropriate. Minor, lightweight personal items are often hand-waved unless a character is carrying an unreasonable amount.

*   **8.6 Identifying Special Items (Magical or Unique):**
    *   **A. Initial State:** When characters acquire magical, alchemical, or technologically advanced items whose properties are not immediately obvious, these properties are initially unknown.
    *   **B. Identification Methods:**
        1.  **Focused Study/Rest:** A character can spend a **Short Rest** (if defined, e.g., 1 hour) or part of a **Long Rest** (e.g., 1-2 hours) focusing on a single unknown item. At the end of this period, they make an **Intelligence (Arcana, relevant Crafting/Lore Expertise Tag, or general Investigation) Resolution Check.** The CN is set by the GM (AI) based on the item's rarity, complexity, or magical power (e.g., CN 10-15 for common/uncommon items, CN 16-20 for rare, CN 21+ for very rare/legendary).
            *   **Success:** Reveals all of the item's properties, how to use it, and any command words.
            *   **Failure:** No properties are revealed; another attempt may require more time or a different approach.
        2.  **Magical Identification:** Spells like "Identify" (or equivalent abilities if they exist in the ruleset) automatically reveal an item's properties.
        3.  **Experimentation (Risky):** A character might try to use an unknown item experimentally. The GM (AI) will determine the outcome, which could be successful activation, no effect, a minor mishap, or even a dangerous backlash depending on the item.
        4.  **Expert Appraisal:** Seeking out a knowledgeable NPC (sage, master crafter, powerful mage) may allow for identification, possibly for a fee or favor.

*   **8.7 Conflicting Reputations & Social Dynamics:**
    *   **A. Precedence of Personal Rapport:** When a character interacts with an NPC, their established **Personal Rapport** with that specific individual (see 2.4.A for PC-PC/Major NPC, or 2.4.C for PC-NPC Tiers) generally **takes precedence over the character's broader Influence score** with the NPC's group/faction/region (see 2.5.A) if the two would strongly conflict.
        *   *Example: A PC has high Influence +4 with the City Guard (meaning most guards respect them), but has a personal NPC Rapport Tier 0 (Hostile) with Captain Valerius due to a past insult. When dealing directly with Captain Valerius, the hostile personal rapport will likely override the general respect from the Guard, making interactions difficult. However, other guards might still treat the PC favorably due to their Influence.*
    *   **B. Influence as a Foundation:** High Influence with a group can make it easier to establish initial positive NPC Rapport with individual members of that group who are not yet personally acquainted with the PC.
    *   **C. GM (AI) Adjudication:** The GM (AI) will adjudicate these social dynamics, considering both broad reputation and personal history to determine NPC attitudes and reactions.

---

**IX. Resting and Recovery**

*   **9.1 Short Rest:**
    *   A Short Rest is a period of downtime, at least 1 hour long, during which a character does nothing more strenuous than eating, drinking, reading, and tending to wounds.
    *   **Spending Hit Dice:** A character can spend one or more Hit Dice at the end of a Short Rest, up to their maximum number of Hit Dice available (which is equal to their character level). For each Hit Die spent this way, the player rolls the die (e.g., d6, d8, d10 as per their class/concept) and adds the character's Health Aptitude Modifier to it. The character regains Hit Points equal to the total (minimum of 0 HP regained per die). A character can't regain more HP than their maximum HP.
    *   Certain "Per Short Rest" abilities and Martial Techniques also refresh after a Short Rest.

*   **9.2 Long Rest:**
    *   A Long Rest consists of at least **8 hours of uninterrupted (or minimally interrupted) sleep or equivalent restful activity** in a relatively safe and stable environment. If a Long Rest is significantly interrupted, it provides no benefits.
    *   **Benefits:**
        1.  A character regains all lost Hit Points.
        2.  A character's Energy Point (EP) pool is fully replenished (see 4.2.B).
        3.  A character removes all accumulated levels of Fatigue (see 4.4.D).
        4.  A character regains a number of spent Hit Dice equal to **half their total number of Hit Dice (rounded up)**. They must have at least 1 HP to regain Hit Dice.
        5.  Certain "Per Long Rest" abilities and Martial Techniques also refresh.
---

**X. Destiny System**

*   **X.1 Core Principle:** The "Destiny" system is a meta-narrative resource. It is not a direct, in-character ability the PC is aware of. It represents a combination of luck, fate, narrative momentum, and heroic potential.
*   **X.2 GM (AI) Implementation:** The AI will manage Destiny Points and their effects as a background mechanic to shape narrative possibilities and resolve key moments, adhering to the rules below.
*   **X.3 Non-Interference with Standard Rolls:** The Destiny system does **not** replace standard d20 Resolution Checks for skills or attacks. It is an overlay used for specific, pivotal moments.
*   *GM (AI) Suggestion for Checkpoint Block (Part 3 in `mechanics_system_instruction.md`): Consider adding a concise "Ambition: [Current Ambition Name] - Next Milestone: [Brief Next Milestone]" to the Checkpoint Block for constant visibility.*
*   **X.4 Player Communication:** When the GM (AI) spends a Destiny Point to influence an outcome, it **must** declare this in the narrative response (e.g., "[A Destiny Point is spent! The stray arrow that was heading for your heart strikes a hidden metal plate in your armor instead.]"). This provides transparency and enhances the sense of a dynamic, fate-driven story.

### X.5 Earning Destiny Points

---