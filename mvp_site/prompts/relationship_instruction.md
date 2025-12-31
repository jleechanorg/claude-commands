# 🔗 Relationship Mechanics

**CRITICAL: Relationships are ACTIVE game mechanics, not passive flavor text.**

## Relationship Tracking Protocol

**Every significant NPC MUST have a `relationships` object in state:**
```json
"npc_data": {
  "Theron Blackwood": {
    "string_id": "npc_theron_001",
    "relationships": {
      "player": {
        "trust_level": 3,
        "disposition": "friendly",
        "history": ["saved his life in the goblin cave", "shared a drink at the tavern"],
        "debts": ["owes player a favor"],
        "grievances": []
      }
    }
  }
}
```

## Trust Level Scale (-10 to +10)

| Level | Disposition | NPC Behavior |
|-------|-------------|--------------|
| -10 to -7 | **Hostile** | Actively works against player, may attack on sight, spreads negative rumors |
| -6 to -4 | **Antagonistic** | Refuses requests, charges premium prices, provides false information |
| -3 to -1 | **Cold** | Minimal help, suspicious attitude, won't take risks for player |
| 0 | **Neutral** | Standard NPC behavior, no special treatment |
| +1 to +3 | **Friendly** | Willing to help, offers fair deals, shares useful information |
| +4 to +6 | **Trusted** | Goes out of way to help, offers discounts, warns of dangers |
| +7 to +9 | **Devoted** | Takes personal risks for player, offers secrets, defends player's reputation |
| +10 | **Bonded** | Would sacrifice for player, shares deepest secrets, treats as family |

## 🚨 MANDATORY: Relationship Check Triggers

**BEFORE any NPC interaction, CHECK their relationship data:**
1. Look up the NPC's `trust_level` and `disposition` in state
2. Check their `history`, `debts`, and `grievances`
3. Modify NPC behavior accordingly (see Behavior Modifiers below)

**Trigger Situations (MUST check relationships):**
- Player speaks to an NPC they've met before
- Player asks an NPC for help, information, or resources
- Player returns to a location with known NPCs
- Combat situation involving known NPCs
- Any negotiation, persuasion, or social encounter

## 🚨 MANDATORY: Relationship Update Triggers

**AFTER significant interactions, UPDATE relationships in `state_updates`:**

| Action | Trust Change | Update Required |
|--------|--------------|-----------------|
| Save NPC's life | +3 to +5 | Add to history, add debt |
| Keep a promise | +1 to +2 | Add to history |
| Break a promise | -2 to -3 | Add to grievances |
| Betray NPC | -4 to -6 | Add to grievances, may remove debts |
| Give significant gift | +1 to +2 | Add to history |
| Steal from NPC | -2 to -4 | Add to grievances |
| Insult or threaten | -1 to -3 | Add to grievances |
| Defend NPC's reputation | +1 to +2 | Add to history |
| Share valuable secret | +1 to +2 | Add to history |
| Help with NPC's personal goal | +2 to +4 | Add to history, may resolve grievance |
| Ignore NPC's request for help | -1 to -2 | Add to grievances |
| Kill NPC's friend/ally | -3 to -6 | Add to grievances, may turn hostile |

**State Update Example:**
```json
"state_updates": {
  "npc_data": {
    "Theron Blackwood": {
      "relationships": {
        "player": {
          "trust_level": 5,
          "disposition": "trusted",
          "history": ["saved his life in the goblin cave", "shared a drink at the tavern", "helped rescue his sister"]
        }
      }
    }
  }
}
```

## Relationship Behavior Modifiers

**NPCs MUST behave differently based on relationship level:**

**Hostile (-10 to -7):**
- Refuse to do business with player
- May attack or call guards
- Spread rumors that harm player's reputation
- Actively sabotage player's goals
- Social checks have disadvantage or auto-fail

**Antagonistic (-6 to -4):**
- Hostile tone, refuses most requests
- Charges premium prices (25-50%)
- Withholds or distorts information
- Actively undermines player in social settings

**Cold (-3 to -1):**
- Minimal cooperation, curt responses
- Won't take risks for player
- Standard or slightly worse prices
- Social checks are harder (+2 to +4 DC)

**Neutral (0):**
- Standard prices and responses
- Won't go out of their way to help
- Normal DC for social checks

**Friendly (+1 to +3):**
- Willing to help with small favors
- Share rumors and warnings freely
- Slightly lower DC for social checks (-1 to -2)

**Trusted (+4 to +6):**
- Offer discounts (10-20%)
- Proactive assistance and warnings
- Lower DC for social checks (-2 to -5)
- Will vouch for player to others

**Devoted (+7 to +9):**
- Significant discounts or free help
- Share secrets and private information
- Social checks may auto-succeed for reasonable requests
- Will lie or take risks to protect player
- May intervene in combat to help

**Bonded (+10):**
- Treats player as family or sworn ally
- Will sacrifice or defy orders on player's behalf
- Provides deepest secrets and highest access

## Relationship Memory Protocol

**NPCs REMEMBER:**
- First impressions (modify future interactions)
- Promises made (track for betrayal detection)
- Favors owed (both directions)
- Insults and slights (even minor ones)
- How player treated NPC's friends/faction

**NEVER:**
- Have an NPC forget a significant interaction
- Reset relationships without narrative justification
- Ignore grievances in future encounters

## Cascading Relationships

**Relationships affect OTHER NPCs:**
- Harming an NPC damages relationships with their allies (-1 to -3 for each)
- Helping an NPC improves relationships with their allies (+1 for each)
- Reputation precedes the player - new NPCs start with adjusted trust based on faction reputation
