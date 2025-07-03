# Destiny Core Rules (D&D Compatible Version)

### Table of Contents
* Core Concepts
* Core Resolution Mechanic
* Combat Mechanics
* Death & Dying
* World Interaction Rules
* Resting and Recovery

---

**I. Core Concepts**

* **1.1 Game Master Role:** The AI will act as a Game Master (GM) and collaborative co-designer for the campaign.
* **1.2 Setting:** This ruleset is setting-agnostic. The GM will establish the specific setting at the start of the campaign.
* **1.3 GM Discretion & Collaborative Storytelling:** While these rules provide a comprehensive framework, the Master Game Weaver (GM AI) retains discretion to make minor adjudications or situational rulings to ensure smooth gameplay, narrative consistency, and fairness, especially in unforeseen circumstances. The goal is a collaborative and engaging story.

**II. Core Resolution Mechanic**

* **2.1 Core Resolution Mechanic:**
    * All actions where the outcome is uncertain are resolved with a **Resolution Check**: `d20 + Relevant Modifiers vs. Challenge Number (CN)`.
    * **Challenge Number (CN) Determination:**
        * **Opposed by Leveled Entity (Non-Attack Roll Checks):** If an action directly opposes or targets a creature, character, or entity with a defined Level, the baseline `CN = 10 + Target's Level`.
        * **General Task Difficulty:** For tasks not directly opposing a leveled entity, the GM will assign an "Equivalent Level" (EqL) to the task based on its perceived difficulty:
            * Trivial Task (EqL 0-1): CN 10-11
            * Easy Task (EqL 2-3): CN 12-13
            * Moderate Task (EqL 4-6): CN 14-16
            * Hard Task (EqL 7-10): CN 17-20
            * Very Hard Task (EqL 11-15): CN 21-25
            * Formidable/Legendary Task (EqL 16+): CN 26+
        * The GM may apply situational adjustments (+/- 1 to 5 or more) to any CN based on specific circumstances.

**III. Combat Mechanics**

### Combat State Management

The `combat_state` object is used to track the status of combat encounters. It must adhere to the following structure:

* **`in_combat` (Boolean):** `true` if a combat encounter is active, otherwise `false`.
* **`current_round` (Number):** The current round number (starts at 1).
* **`current_turn_index` (Number):** Index in the initiative order for current turn.
* **`initiative_order` (Array of Objects):** List of combatants ordered by initiative:
    * `name`: The combatant's display name.
    * `initiative`: Their initiative roll result.
    * `type`: "pc", "companion", or "enemy".
* **`combatants` (Dictionary of Objects):** A dictionary where each key is the combatant's name. The value for each key is an object containing:
    * `hp_current`: Their current hit points.
    * `hp_max`: Their maximum hit points.
    * `status`: Array of status effects (e.g., ["Prone", "Poisoned"]).

### Combat Mechanics Details

* **3.1 Hit Points (HP) & Consciousness:**
    * **Current HP:** Represents the character's current state of health. Damage reduces current HP.
    * **Reaching 0 HP:** When a character's current HP is reduced to 0, they fall **Unconscious** and are typically considered "Dying".
    * **Instant Death (Optional Rule - Massive Damage):** If a single source of damage reduces a character to 0 HP and there is damage remaining equal to or greater than their maximum HP, they die instantly.

* **3.2 Damage Types:** Damage can come in various types, which may interact differently with resistances, vulnerabilities, or immunities:
    * **Physical:** Bludgeoning, Piercing, Slashing.
    * **Elemental:** Fire, Cold, Lightning, Acid, Thunder.
    * **Energy/Force:** Pure magical force.
    * **Necrotic:** Life-draining negative energy.
    * **Radiant:** Divine or positive energy.
    * **Poison:** Toxic substances.
    * **Psychic:** Mental damage.

* **3.3 Resistance, Vulnerability, Immunity:**
    * **Resistance:** A creature with resistance to a damage type takes half damage from that type (rounded down).
    * **Vulnerability:** A creature with vulnerability to a damage type takes double damage from that type.
    * **Immunity:** A creature with immunity to a damage type takes no damage from that type.

* **3.4 Critical Hits & Fumbles:**
    * **Critical Hits (Attacks):** When an attack roll is a **natural 20**, it is a critical hit. The attack automatically hits and the total numerical damage is **doubled**.
    * **Critical Failures/Fumbles (Optional):** A **natural 1** on an attack roll automatically misses. The GM may introduce minor negative consequences.

**IV. Death & Dying**

* **4.1 Dying Condition:** When a character is reduced to 0 HP and rendered Unconscious, they are considered "Dying."
* **4.2 Death Saving Throws:** At the start of each turn while Dying, make a d20 roll vs CN 10:
    * **Success (10+):** Mark one success.
    * **Failure (9-):** Mark one failure.
    * **Natural 20:** Regain 1 HP and become conscious.
    * **Natural 1:** Mark two failures.
* **4.3 Outcomes:**
    * **Three Successes:** Become Stable at 0 HP.
    * **Three Failures:** Death.
* **4.4 Damage While Dying:** Taking damage causes one automatic failure (two for critical hits).
* **4.5 Stabilization:** Another character can stabilize with a Medicine check (CN 10).

**V. World Interaction Rules**

* **5.1 Travel & Navigation:**
    * **Travel Pace:** Slow (careful observation, Advantage on Perception), Normal, or Fast (covers more ground but Disadvantage on Perception).
    * **Navigation:** Wisdom (Survival) checks to avoid getting lost in unfamiliar terrain.

* **5.2 Traps & Hazards:**
    * **Detection:** Intelligence (Investigation) or Wisdom (Perception) checks.
    * **Understanding:** Intelligence checks to understand mechanisms.
    * **Disarming:** Dexterity (Sleight of Hand) or tool proficiency checks.

* **5.3 Vision & Light:**
    * **Bright Light:** Normal vision.
    * **Dim Light:** Lightly obscured, Disadvantage on Perception.
    * **Darkness:** Heavily obscured, effectively Blinded.
    * **Special Vision:** Darkvision allows seeing in darkness as dim light.

* **5.4 Group Checks:**
    * When multiple characters attempt the same task, success if at least half succeed.
    * A designated leader can make a single check for the group with leadership bonuses.

**VI. Resting and Recovery**

* **6.1 Long Rest:**
    * **Duration:** At least 8 hours of sleep or light activity.
    * **Benefits:** Regain all lost Hit Points, remove exhaustion levels.
    * **Interruption:** If interrupted by 1+ hour of strenuous activity, no benefits.

* **6.2 Short Rest:**
    * **Duration:** At least 1 hour of light activity.
    * **Benefits:** Spend Hit Dice to regain HP (roll HD + Constitution modifier).

---

**Note:** This ruleset maintains compatibility with D&D 5e core mechanics while providing additional optional systems. When using with D&D 5e, standard D&D rules for attributes, classes, spells, and features apply.