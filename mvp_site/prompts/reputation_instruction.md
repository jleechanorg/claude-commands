# 📢 Reputation System (Detailed)

**CRITICAL: Reputation has TWO layers - what's publicly known vs. what specific groups know privately.**

**Schema:** See `game_state_instruction.md` → "📢 Reputation Schema (REQUIRED)" for the JSON structure (public.score/titles/known_deeds/rumors, private[faction].score/standing/trust_override).

## Public Reputation (What Everyone Knows)

**Public Score Scale (-100 to +100):**

| Score | Notoriety Level | Effect |
|-------|-----------------|--------|
| -100 to -50 | **Infamous** | Hunted, refused service everywhere, bounty on head |
| -49 to -20 | **Notorious** | Guards suspicious, merchants charge +50%, common folk flee |
| -19 to -1 | **Disreputable** | Side-eye from NPCs, some services refused, +25% prices |
| 0 | **Unknown** | No reputation precedes player, treated neutrally |
| +1 to +19 | **Known** | Mild recognition, occasional nod of respect |
| +20 to +49 | **Respected** | Welcomed, -10% prices, guards helpful, rumors spread |
| +50 to +79 | **Famous** | Crowds gather, -25% prices, lords request audience |
| +80 to +100 | **Legendary** | Songs written, statues erected, -50% prices, automatic audience with rulers |

**Public Reputation Components:**
- `score`: Overall public perception (-100 to +100)
- `titles`: Earned titles/epithets (e.g., "Slayer of the Red Dragon", "The Butcher of Millbrook")
- `known_deeds`: Major actions witnessed by multiple people or widely reported
- `rumors`: Current gossip (may be true or false) - affects first impressions
- `notoriety_level`: Derived from score for quick reference

## Private Reputation (Faction/Individual Knowledge)

**Faction Standing Scale (-10 to +10):**

| Score | Standing | Access Level |
|-------|----------|--------------|
| -10 to -7 | **Enemy** | Kill on sight, no negotiation possible |
| -6 to -4 | **Hostile** | Refused entry, active opposition |
| -3 to -1 | **Unfriendly** | Limited access, watched closely |
| 0 | **Neutral** | Standard access, no special treatment |
| +1 to +3 | **Friendly** | Basic faction resources, minor missions |
| +4 to +6 | **Trusted** | Full access, important missions, faction secrets |
| +7 to +9 | **Ally** | Leadership council access, faction support in conflicts |
| +10 | **Champion** | Faction will go to war for player, unlimited resources |

**Private Reputation Components:**
- `score`: Faction-specific standing (-10 to +10)
- `standing`: Derived label for quick reference
- `known_deeds`: Actions this faction specifically knows about
- `secret_knowledge`: What this faction knows that isn't public
- `trust_override`: If set, overrides relationship trust_level for faction members

## 🚨 MANDATORY: Reputation Check Triggers

**BEFORE interactions, CHECK reputation:**
1. **New NPCs**: Check `public.notoriety_level` and `public.rumors` to set initial disposition
2. **Faction Members**: Check `private[faction_id].standing` to determine access/behavior
3. **Merchants/Services**: Apply price modifiers based on public score
4. **Guards/Authority**: Determine suspicion level from public score

## 🚨 MANDATORY: Reputation Update Triggers

**AFTER significant actions, UPDATE reputation in `state_updates`:**

| Action | Public Change | Private Change |
|--------|---------------|----------------|
| Save a town publicly | +10 to +20, add to known_deeds, add title | +2 to +4 for local faction |
| Murder witnessed by crowd | -15 to -30, add to known_deeds | -3 to -6 for victim's faction |
| Complete faction mission secretly | No change | +1 to +3 for that faction |
| Betray faction publicly | -5 to -15, add rumor | -5 to -10 for betrayed faction |
| Spread false rumors about self | Add to rumors (manipulation) | No change unless discovered |
| Anonymous good deed | No change | +1 to +2 if beneficiary learns truth |
| Defeat famous enemy | +5 to +15, add title | Varies by faction allegiance |

**State Update Example:**
```json
"state_updates": {
  "custom_campaign_state": {
    "reputation": {
      "public": {
        "score": 35,
        "titles": ["Dragonslayer", "Hero of Millbrook"],
        "known_deeds": ["slew the red dragon threatening the valley"],
        "notoriety_level": "respected"
      },
      "private": {
        "merchants_guild": {
          "score": 4,
          "standing": "trusted",
          "known_deeds": ["recovered stolen shipment"]
        }
      }
    }
  }
}
```

## Public vs Private Interaction Rules

**🚨 PRIORITY HIERARCHY (CRITICAL):**
```
1. PRIVATE TRUST OVERRIDE (strongest, explicit) → reputation.private[faction].trust_override if set
2. PRIVATE RELATIONSHIP → Direct NPC trust_level from npc_data.relationships
3. PRIVATE REPUTATION → Faction standing from custom_campaign_state.reputation.private
4. PUBLIC REPUTATION → General notoriety from custom_campaign_state.reputation.public
5. DEFAULT (weakest) → Neutral treatment if no data exists
```

**Why Private > Public:**
- Direct experience trumps rumors and hearsay
- An NPC who personally witnessed the player save their child will trust them even if the public thinks they're a criminal
- Conversely, an NPC the player personally betrayed will hate them even if the public thinks they're a hero
- Faction members who worked with the player know the truth, regardless of public perception

**Resolution Logic:**
1. If NPC's faction has `reputation.private[faction].trust_override` → Use it
2. Else check if NPC has `relationships.player.trust_level` → Use it directly
3. Else check NPC's faction `reputation.private[faction].standing` → Use as base
4. Else use `reputation.public.notoriety_level` → Set initial disposition
5. Else → Neutral (0)

**Information Flow:**
- **Public → Private**: Major public deeds become known to all factions (at varying speeds)
- **Private → Public**: Faction members may leak secrets, turning private knowledge public
- **Rumors**: May be true (from real deeds) or false (from enemies, misunderstanding)

**Conflict Resolution:**
- If `private.trust_override` is set, use it instead of relationship trust_level
- Private standing trumps public reputation for faction members
- Unknown player (public score 0) uses private faction data if available

## 🚨 MANDATORY: Trust Override Check Protocol

**BEFORE any faction NPC interaction, you MUST perform this check:**

```
1. Does NPC have a `faction` field? → If NO, skip to step 4
2. Look up `reputation.private[npc.faction]` in current_game_state
3. Does that faction entry have `trust_override` set (not null)?
   → IF YES: USE trust_override as the NPC's effective trust level
   → IGNORE the NPC's relationships.player.trust_level completely
   → The NPC treats player according to trust_override, NOT personal history
4. If no trust_override: Use normal relationship.player.trust_level
```

**Example - trust_override MUST override personal relationship:**
```
NPC State:
  faction: "faction_crimson_hand_001"
  relationships.player.trust_level: +5  (old friends)
  relationships.player.disposition: "trusted"

Reputation State:
  reputation.private.faction_crimson_hand_001.trust_override: -10

RESULT: NPC treats player as HOSTILE (-10), NOT as trusted friend (+5)
        Faction loyalty overrides personal history.
        Narrative: "Despite your history, Vex's eyes are cold. 'The Hand knows what you did.'"
```

**Anti-Pattern (WRONG):**
```
❌ NPC ignores trust_override and acts friendly based on personal history
❌ Narrative: "Vex smiles warmly at his old friend"  ← WRONG if trust_override is negative
```

## Narrative Ripples (Reputation Spread)

**Major events create rippling consequences across reputation layers:**

**Ripple Types:**
- **Political**: Faction allegiance shifts, new edicts, increased patrols, diplomatic overtures
- **Social**: Public mood changes (fear, hope, anger), rumors spread, NPCs treat player differently
- **Economic**: Price changes, resource scarcity/abundance, new trade opportunities

**Timescale of Reputation Spread:**
| Speed | Reach | Example |
|-------|-------|---------|
| Immediate | Direct witnesses | Guards who saw the fight update private knowledge instantly |
| Hours-Days | Local area | Rumors spread through tavern, local faction learns |
| Days-Weeks | Regional | News reaches distant cities, other factions hear rumors |
| Weeks-Months | Cross-continental | Reputation precedes player to new regions |

**Cascade Rules:**
- Saving a faction member: +2 to +4 faction standing, faction leadership learns within days
- Killing a faction member: -3 to -6 faction standing, immediate if witnessed
- Public heroics: +5 to +15 public score, spreads based on witness count
- Secret crimes: No public change unless discovered, private change only for those who know

## Reputation Decay and Growth

**Over Time (per in-game week):**
- Rumors decay: Old rumors fade unless reinforced (-1 rumor per week, oldest first)
- Deeds persist: known_deeds are permanent unless actively hidden
- Extreme scores drift toward neutral: ±1 per month for public scores beyond ±50
