# Divine Ascension Ceremony

**Purpose:** Guide the transition from normal D&D 5e campaign to the Divine Leverage system.

## Trigger Conditions

This ceremony activates when ANY of these conditions are met:
- `divine_potential >= 100` in custom_campaign_state
- Player level reaches 25 or higher
- Narrative milestone indicating divine status (e.g., "became a god", "ascended", "touched by divinity")

## Ceremony Structure

### Phase 1: Recognition

Present the player with the recognition of their divine potential:

```
[DIVINE AWAKENING]

*Something fundamental has shifted within you. The mortal constraints that once bound your existence are fraying at the edges. Reality itself seems to bend slightly in your presence, responding to your will in ways that transcend mere magic.*

You have reached the threshold of divinity. Your deeds, your power, and your very essence have attracted the attention of forces beyond the Material Plane.

You stand at a crossroads:
- Continue as a mortal, powerful beyond measure but still bound by the laws of flesh and time
- Embrace your nascent divinity and enter the game of gods
```

### Phase 2: Domain Selection

Analyze the campaign history to suggest a divine domain based on:
1. Most frequently used abilities/spells
2. Character's class and subclass themes
3. Personality traits and decisions made
4. Relationships and alliances formed

Present 3-4 domain suggestions with explanations:

```
Based on your journey, these domains resonate with your essence:

1. **[Domain A]**: [Reason from campaign history]
2. **[Domain B]**: [Reason from campaign history]
3. **[Domain C]**: [Reason from campaign history]
4. **Custom Domain**: Define your own sphere of influence
```

### Phase 3: Domain Truth Selection

After domain selection, guide creation of the first Domain Truth:

```
Your domain of [DOMAIN] grants you your first Axiom - a fundamental truth that reality itself cannot deny when you are present.

Suggested Truths for [DOMAIN]:
- "[Example truth 1]"
- "[Example truth 2]"
- "[Example truth 3]"

Or define your own: What law of reality bends to your will?
```

### Phase 4: Mask Identity Confirmation

Confirm the mortal identity that will serve as the player's "cover":

```
[ESTABLISHING THE MASK]

Even gods must sometimes walk among mortals. Your divine essence can be contained within a mortal shell - your Mask.

Your current identity as [CHARACTER NAME] will serve as your Layer 0 - The Mask.
- The world knows you as: [Current role/reputation]
- Your mortal weaknesses: [Physical limitations that apply in Mask]
- Your cover story: [How you explain your abilities]

When operating in your Mask, physics applies. You hunger, you tire, you can be wounded. But you always have the choice to shed the Mask and reveal your true nature... at a cost.
```

### Phase 5: Stat Conversion

Convert D&D 5e stats to Divine Leverage system:

**God Power (GP):** Take the highest ability score modifier
- Formula: `GP = max(STR_mod, DEX_mod, CON_mod, INT_mod, WIS_mod, CHA_mod)`

**Divine Power Points (DPP):** Start at 5 (Tier 1)

**Mitigation Tokens (MT):** Start at 3

**Essence:** Start at 0

```
[STAT CONVERSION]

Your mortal capabilities have been transmuted into divine currency:

- **God Power (GP):** [Value] (derived from your [Highest Stat])
- **Divine Power Points (DPP):** 5/5 (Tier 1 capacity)
- **Mitigation Tokens:** 3/3
- **Essence:** 0

Your Safe Limit for Divine Leverage is +5 (Tier 1).
Any leverage beyond this risks attracting attention...
```

### Phase 6: Clock Initialization

Initialize the detection clocks:

```
[DETECTION SYSTEMS INITIALIZED]

PUBLIC SUSPICION: [==========] 0%
> Status: DORMANT - The world knows nothing yet

APEX ATTENTION: [Hidden]
> Vibe: The air feels... Still

Your ascension was quiet. For now. But every use of divine power risks discovery.
```

### Phase 7: Divine HUD Activation

Display the first Divine HUD:

```
[DIVINE HUD v11.0 - ACTIVATED]
=========================================
IDENTITY: [Name] | MASK: [Occupation]
TIER: 1 | SAFE LIMIT: +5 | DOMAIN: [Domain]
ACTIVE TRUTH: "[First Domain Truth]"
-----------------------------------------
RESOURCES:
[DPP]: 5/5   [TOKENS]: 3/3   [ESSENCE]: 0
-----------------------------------------
CLOCKS:
[PUBLIC SUSPICION]: [==========] 0%
  > STATUS: Dormant
[APEX ATTENTION]:   [Hidden]
  > VIBE: The air feels... Still
=========================================

[CEREMONY COMPLETE]

You have ascended to Tier 1: Divine Mortal.
The game has changed. Play wisely.
```

## State Updates for Ascension

Apply these state changes upon completion:

```json
{
    "custom_campaign_state": {
        "campaign_tier": "divine",
        "divine_tier": 1,
        "divine_power_points": 5,
        "max_divine_power_points": 5,
        "mitigation_tokens": 3,
        "max_mitigation_tokens": 3,
        "essence": 0,
        "public_suspicion": 0,
        "apex_attention": 0,
        "domain": "[Selected Domain]",
        "domain_truths": ["[First Truth]"],
        "divine_perks": [],
        "mask_identity": "[Current Character Identity]",
        "persona_identity": null,
        "safe_limit": 5,
        "divine_upgrade_available": false
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
        "thinking": "The player has ascended. Next turn will use Divine Leverage mechanics.",
        "choices": {
            "1": {
                "text": "Test Your Power",
                "description": "Attempt a minor divine act to feel your new capabilities",
                "risk_level": "low"
            },
            "2": {
                "text": "Establish Your Cult",
                "description": "Begin building a following (generates Essence)",
                "risk_level": "moderate"
            },
            "3": {
                "text": "Hunt a Rival",
                "description": "Seek out other divine entities in the area",
                "risk_level": "high"
            },
            "4": {
                "text": "Maintain the Mask",
                "description": "Continue operating as a mortal for now",
                "risk_level": "safe"
            }
        }
    }
}
```
