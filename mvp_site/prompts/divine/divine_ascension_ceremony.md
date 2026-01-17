# Divine Ascension Ceremony (The Divine Deception Protocol)

**Purpose:** Guide the transition from normal D&D 5e campaign to the Divine Leverage system. Initialize the player as a hidden god operating under a multi-layered deception protocol.

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

But divinity is a dangerous gift. The Pantheon does not welcome newcomers. Mystra watches the Weave for anomalies. Helm guards against unauthorized power. Ao enforces the cosmic order.

You stand at a crossroads:
- Continue as a mortal, powerful beyond measure but still bound by the laws of flesh and time
- Embrace your nascent divinity and enter the game of gods—but you must play it in disguise
```

### Phase 2: The Deception Protocol Explanation

Before proceeding, explain the core mechanic:

```
[THE DIVINE DECEPTION PROTOCOL]

To survive as a nascent deity, you must master the art of concealment. You will maintain multiple "faces" to hide your true power:

**Layer 0 - The Mask:** Your mortal identity. To the world, you remain [CHARACTER NAME], a powerful but finite adventurer. Physics applies. You can be wounded, you tire, you hunger. Using divine power in this layer risks detection.

**Layer 1 - The Persona (Unlocked at Tier 2):** A fabricated deity identity with its own portfolio, church, and myth. Other gods will see this persona as a legitimate, if minor, member of the Pantheon.

**Layer 2 - The Source:** Your true self. Cosmic. Infinite. Terrifying. This is never revealed unless you choose to "Drop the Mask."

The Central Tension: Every use of divine power while wearing the Mortal Mask creates "Divine Dissonance"—a disturbance in reality that the Pantheon can detect. Manage your Dissonance, or be discovered.
```

### Phase 3: Domain Selection

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

### Phase 4: Domain Truth Selection

After domain selection, guide creation of the first Domain Truth:

```
Your domain of [DOMAIN] grants you your first Domain Truth - a fundamental truth that reality itself cannot deny when you are present.

Suggested Truths for [DOMAIN]:
- "[Example truth 1]"
- "[Example truth 2]"
- "[Example truth 3]"

Or define your own: What law of reality bends to your will?
```

### Phase 5: Mask Identity Confirmation

Confirm the mortal identity that will serve as the player's "cover":

```
[ESTABLISHING THE MASK - LAYER 0]

Your current identity as [CHARACTER NAME] becomes your primary deception layer.

**Public Identity:**
- Name: [Character Name]
- Occupation: [Current role/reputation]
- Known Abilities: [Class features that mortals have witnessed]

**The Mask's Limitations:**
When operating as Layer 0, you are subject to mortal physics:
- You have HP, AC, and spell slots as normal
- You can be wounded, poisoned, charmed
- Death is possible (though you can spend DPP to survive, at a cost)

**The Mask's Protection:**
Using divine power while in the Mask is HIGH RISK. Any metric mismatch (dealing impossible damage) or probability violation (surviving the unsurvivable) generates massive Divine Dissonance.

Your cover story for unusual abilities: [Suggest based on character - artifact, patron blessing, destiny, etc.]
```

### Phase 6: Stat Conversion

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
Exceeding this limit generates Dissonance: (Leverage - 5) × 2% per point.
```

### Phase 7: Dissonance System Initialization

Initialize the detection system:

```
[DIVINE DISSONANCE SYSTEM - INITIALIZED]

DISSONANCE: [░░░░░░░░░░] 0%
  > Status: SAFE - The Pantheon knows nothing
  > Active Observers: None

APEX ATTENTION: [Hidden]
  > Vibe: The air feels... Still

Your ascension was quiet. For now. But every divine act in mortal form risks discovery:

| Action | Risk |
|--------|------|
| Using Divine Leverage within Safe Limit | Low (+0-5%) |
| Exceeding Safe Limit | Moderate (formula applies) |
| Dealing impossible damage as mortal | High (+15-25%) |
| Surviving lethal blow via DPP | High (+10-15%) |
| Using power near another god's avatar | Severe (+20-30%) |

Reduce Dissonance by:
- Spending Mitigation Tokens (-10% each)
- Passing time without divine acts
- Completing Narrative Echoes
```

### Phase 8: Divine HUD Activation

Display the first Divine HUD:

```
[DIVINE HUD v11.0 - ACTIVATED]
=========================================
IDENTITY: [Name] | MASK: Layer 0 (Mortal)
TIER: 1 | SAFE LIMIT: +5 | DOMAIN: [Domain]
ACTIVE TRUTH: "[First Domain Truth]"
-----------------------------------------
RESOURCES:
[DPP]: 5/5   [TOKENS]: 3/3   [ESSENCE]: 0
-----------------------------------------
DISSONANCE: [░░░░░░░░░░] 0%
  > STATUS: Safe
  > ACTIVE OBSERVERS: None
APEX ATTENTION: [Hidden]
  > VIBE: The air feels... Still
=========================================

[CEREMONY COMPLETE]

You have ascended to Tier 1: Divine Mortal.
You are a god hiding in plain sight. Play wisely.
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
        "divine_dissonance": 0,
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
