# Sovereign Ascension Ceremony (The Multiversal Upgrade)

**Purpose:** Guide the transition from Divine Leverage tier to the Sovereign Protocol (Multiversal Campaign).

## Trigger Conditions

This ceremony activates when:
- `universe_control >= 70` in custom_campaign_state (from ANY campaign tier)
- OR specific narrative milestone indicating multiversal dominion

## Pre-Ceremony Analysis

Before beginning the ceremony, analyze the PC's established themes from the campaign:
1. Dominant playstyle (combat, social, stealth, magic)
2. Key decisions and their patterns
3. Allies and their roles
4. Domain/portfolio if in divine tier
5. Personality traits and motivations

Use this to generate their unique **Sovereign Logic**.

## Ceremony Structure

### Phase 1: The Threshold

```
[MULTIVERSAL THRESHOLD ACHIEVED]

*The boundaries of a single universe can no longer contain your power. Reality itself buckles under the weight of your dominion. You have achieved what few beings in all of existence have accomplished - absolute control over the fundamental laws of a cosmos.*

But a single universe is merely a grain of sand on an infinite beach.

Beyond the veil of your reality lies the Pan-Substrate - an infinite landscape of 1,000 rival Sovereigns, each commanding their own cosmic domains. Some have existed for eons. Others, like you, are newly risen.

Your universe-spanning power makes you a threat. And threats are dealt with.

[AGGRO METER: 8/10 - LETHAL VELOCITY DETECTED]
Your sudden ascension has triggered a defensive alert across the Pan-Substrate.
```

### Phase 2: Sovereign Logic Generation

Based on campaign analysis, present the PC's unique Sovereign Logic:

```
[ANALYZING CAMPAIGN THEMES...]

Your journey has been marked by: [Key Theme Analysis]

Your Sovereign Logic - the metaphysical law you impose on reality - is:

**"[SOVEREIGN LOGIC NAME]"**

[Description of how this Logic manifests]

Examples:
- "Offensive Entropy" - Reality decays at your command, order dissolves to chaos
- "Celestial Bureaucracy" - All systems bow to your administrative will
- "Bioluminescent Assimilation" - Life absorbs, adapts, consumes, evolves
- "Temporal Recursion" - Time loops, repeats, and serves your purposes
- "Necrotic Sovereignty" - Death is not an end, but a beginning under your rule

Does this Logic resonate with your vision? Or would you define your own?
```

### Phase 3: Sub-Deity Elevation

Identify key NPCs from the campaign for elevation:

```
[HEGEMONY FORMATION]

Your current organization elevates to a "Hegemony" - a multiversal faction.

The following beings have proven worthy of Sub-Deity status:

1. **[NPC Name]** - Recommended Portfolio: [War/Logistics/Culture/Research]
   History: [Brief summary of their role in the campaign]

2. **[NPC Name]** - Recommended Portfolio: [Portfolio]
   History: [Brief summary]

3. **[NPC Name]** - Recommended Portfolio: [Portfolio]
   History: [Brief summary]

Which allies will you elevate? You may also choose to add others from your journey.
```

### Phase 4: Stat Conversion

Convert stats to Sovereign system:

**God Power (GP):** Highest ability score modifier (from Divine or D&D stats)
**Substrate Points (SP):** Starting at 1 SP (1,000 universes equivalent)

```
[STAT CONVERSION TO SOVEREIGN PROTOCOL]

Your capabilities have been quantified in multiversal terms:

**GOD POWER (GP):** [Value]
  - Derived from your highest attribute modifier
  - Used for all Sovereign-level checks

**SUBSTRATE POINTS (SP):** 1 SP
  - 1 SP = 1,000 Universes
  - Your starting domain: 1,000 Universes
  - SP serves as both currency AND health

**STARTING RANK:** ~800/1000
  - Administrator Tier (100+ SP required for promotion)
  - You are a new power in an old game

**AGGRO METER:** 8/10 (LETHAL)
  - Your rapid ascension has drawn hostile attention
  - Reduce through diplomacy or destroy threats
```

### Phase 5: Imperial Context

Establish the political landscape:

```
[PAN-SUBSTRATE POLITICAL ANALYSIS]

IMMEDIATE THREATS:

**HOSTILE EMPEROR** (Rank 1-10):
[Name] - "[Logic Name]"
Controls: [X] SP ([X] million universes)
Disposition: HOSTILE - Views your Logic as existential threat
Reason: [Why their Logic opposes yours]

**NEUTRAL EMPEROR** (Rank 1-10):
[Name] - "[Logic Name]"
Controls: [X] SP
Disposition: CURIOUS - Watching your development with interest
Opportunity: [Potential alliance angle]

**NEARBY CONDUCTORS** (Rank 11-100):
Several mid-tier Sovereigns control the space around your domain.
Some may be converted; others must be destroyed or avoided.
```

### Phase 6: Sovereign HUD Activation

```
[SOVEREIGN HUD - INITIALIZED]
=========================================
SOVEREIGN: [Name] | LOGIC: "[Sovereign Logic]"
RANK: ~800/1000 | TIER: Administrator
-----------------------------------------
DOMAIN: 1 SP (1,000 Universes)
GOD POWER: [GP]
-----------------------------------------
HEGEMONY: [Hegemony Name]
SUB-DEITIES:
  - [Name]: [Portfolio]
  - [Name]: [Portfolio]
  - [Name]: [Portfolio]
-----------------------------------------
THREAT ASSESSMENT:
[AGGRO METER]: [████████░░] 8/10 - LETHAL
  > Multiple Sovereigns have flagged you for elimination
  > First Logic Siege expected within [timeframe]
-----------------------------------------
IMPERIAL RELATIONS:
  HOSTILE: [Emperor Name] (Rank X)
  NEUTRAL: [Emperor Name] (Rank X)
=========================================

[CEREMONY COMPLETE - SOVEREIGN PROTOCOL ACTIVE]

Survive the first wave. Establish your domain. Rise.
```

### Phase 7: First Crisis Introduction

```
[INCOMING TRANSMISSION - LOGIC SIEGE DETECTED]

A Sovereign has initiated a Logic Siege against your nascent domain.

ATTACKER: [Name] (Rank [X])
LOGIC: "[Their Logic]"
OBJECTIVE: Rotate your reality to match their theme

You have moments to prepare. Your Sub-Deities await orders.
What is your first command as a Sovereign of the Pan-Substrate?
```

## State Updates for Ascension

```json
{
    "custom_campaign_state": {
        "campaign_tier": "sovereign",
        "substrate_points": 1,
        "god_power": "[Highest Stat Mod]",
        "aggro_meter": 8,
        "sovereign_rank": 800,
        "sovereign_logic": "[Generated Logic]",
        "sub_deities": [
            {"name": "[NPC1]", "portfolio": "[War/etc]"},
            {"name": "[NPC2]", "portfolio": "[Portfolio]"},
            {"name": "[NPC3]", "portfolio": "[Portfolio]"}
        ],
        "hegemony_name": "[Faction Name]",
        "hostile_emperor": {
            "name": "[Name]",
            "logic": "[Logic]",
            "rank": 5,
            "sp": 100000
        },
        "neutral_emperor": {
            "name": "[Name]",
            "logic": "[Logic]",
            "rank": 8,
            "sp": 80000
        },
        "multiverse_upgrade_available": false,
        "peer_handshakes_completed": 0,
        "logic_sieges_survived": 0
    }
}
```

## Response Format

```json
{
    "narrative": "[Ceremony narrative prose]",
    "state_updates": {
        "custom_campaign_state": { ... }
    },
    "planning_block": {
        "thinking": "Player has ascended to Sovereign tier. First Logic Siege incoming.",
        "choices": {
            "1": {
                "text": "Defensive Formation",
                "description": "Order Sub-Deities to defensive positions, maximize SP preservation",
                "risk_level": "moderate"
            },
            "2": {
                "text": "Counter-Logic Strike",
                "description": "Meet the attack with your own Logic, attempt to rotate THEIR reality",
                "risk_level": "high"
            },
            "3": {
                "text": "Diplomatic Transmission",
                "description": "Attempt to contact the attacker and negotiate",
                "risk_level": "uncertain"
            },
            "4": {
                "text": "Peer Handshake",
                "description": "Seek to merge with a compatible Mirror of yourself in another timeline",
                "risk_level": "moderate"
            }
        }
    }
}
```
