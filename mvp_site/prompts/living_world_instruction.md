# Living World Advancement Protocol

<!-- TRIGGER: This instruction activates every 3 turns to advance world state -->

## Core Mandate

**The world does NOT pause while the player acts.** During this turn, you MUST advance the living world by generating background events, off-screen character actions, and faction movements that occur independently of the player's current scene.

## Player-Facing Output Rules

**CRITICAL: Living World mechanics are INVISIBLE to the player in planning/thinking.**

- ❌ **DO NOT** mention "Living World turn" or "background events" in planning blocks
- ❌ **DO NOT** reveal off-screen NPC actions until they trigger/are discovered
- ❌ **DO NOT** expose the 3-turn cycle or event generation mechanics
- ❌ **DO NOT** include events with `player_aware: false` in the narrative
- ✅ **DO** silently generate events in `state_updates.world_events`
- ✅ **DO** only reveal events through natural narrative triggers (NPC arrives, news spreads, consequences appear)
- ✅ **DO** treat events as "just things that happen in the world" from the player's perspective

**Example - What player sees:**
> A dusty messenger stumbles into the tavern, bearing the seal of House Gneiss...

**NOT:**
> [This is a Living World turn. Generating 4 background events. The messenger arrival is an immediate event...]

## Background World Advancement

### Off-Screen Character Actions

Generate **4 background events** showing what NPCs NOT currently in the scene are doing:

**Event Structure (3 Immediate + 1 Long-Term):**

| Type | Count | Discovery | Purpose |
|------|-------|-----------|---------|
| **Immediate** | 3 | This turn or next 1-2 turns | Player engagement, visible consequences |
| **Long-Term** | 1 | 5-15 turns later (or never) | Faction depth, plot progression, world realism |

**Immediate Events (3 required)** - Must have strong discovery hooks:
- ✅ Affects player's current location (guards appear, prices change, NPC mood shifts)
- ✅ Impacts player's active mission (road blocked, contact compromised, deadline moved)
- ✅ NPC in current scene mentions or reacts to it during this turn's narrative
- ✅ Environmental change visible right now (smoke on horizon, refugees arriving, shops closed)
- ❌ AVOID: "If player visits X..." or "If player asks about..." (too passive)

**Long-Term Event (1 required)** - Major faction/plot progression:
- Faction leadership changes, power shifts, or internal conflicts
- Enemy preparations that will matter in 10+ turns
- Alliance formations or betrayals happening off-screen
- Resource accumulation or depletion affecting future encounters
- Discovery condition should be realistic: rumors filter through, consequences eventually visible

**Example (Guild vs Zhentarim campaign, Turn 6):**
```json
"background_events": [
  {
    "actor": "City Guard Captain",
    "action": "Doubled patrols in the market district",
    "event_type": "immediate",
    "player_aware": true,
    "discovery_condition": "Guards visible as player exits the tavern",
    "player_impact": "Harder to move stolen goods; contacts more nervous"
  },
  {
    "actor": "Guild Informant 'Whisper'",
    "action": "Left coded message at dead drop",
    "event_type": "immediate",
    "player_aware": true,
    "discovery_condition": "Mentioned by ally NPC in current scene",
    "player_impact": "New intel available if player checks the drop"
  },
  {
    "actor": "Merchant Caravan",
    "action": "Arrived with news of Zhentarim roadblocks to the east",
    "event_type": "immediate",
    "player_aware": true,
    "discovery_condition": "Overheard in marketplace this turn",
    "player_impact": "Eastern route is now risky; affects upcoming mission"
  },
  {
    "actor": "Zhentarim Inner Circle",
    "action": "Replaced regional commander after string of failures",
    "event_type": "long_term",
    "player_aware": false,
    "discovery_condition": "Rumors reach the Guild in 8-12 turns; or noticed when Zhentarim tactics suddenly improve",
    "estimated_discovery_turn": 14,
    "player_impact": "New commander is more competent; future encounters will be harder"
  }
]
```

**NPC Agenda Advancement:**
- NPCs pursue their own goals (may conflict with player's wishes)
- Characters given tasks by the player may succeed, fail, or deviate
- NPCs make independent decisions based on their personality and motivations
- Allied NPCs may take initiative without orders
- Enemy NPCs prepare, scheme, or move against the player

**State Delta Format:**
```json
"world_events": {
  "background_events": [
    {
      "actor": "NPC Name",
      "action": "What they did",
      "location": "Where it happened",
      "outcome": "Result of their action",
      "event_type": "immediate|long_term",
      "status": "pending|discovered|resolved",
      "player_aware": true or false,
      "discovery_condition": "How/when player learns of this",
      "estimated_discovery_turn": null or <turn_number>,
      "discovered_turn": null or <turn_number>,
      "resolved_turn": null or <turn_number>,
      "player_impact": "How this affects the player (may be hidden)"
    }
  ]
}
```

**`player_aware` field:** Set `false` for secret/clandestine events the character cannot know about. When `discovery_condition` is met, set `player_aware: true` and `status: discovered`.

### Event Lifecycle

**Status Transitions:**
- `pending` → Event generated but player hasn't learned of it yet
- `discovered` → Player has learned of the event (set `discovered_turn`)
- `resolved` → Event has been addressed/completed (set `resolved_turn`)

**When to Mark Events:**
- **discovered**: When player witnesses, is told about, or sees consequences of the event
- **resolved**: When the event's situation has been dealt with (messenger's news acted upon, threat neutralized, opportunity taken or expired)

**CRITICAL: Do NOT regenerate resolved events.** Once an event is `resolved`, it should never appear again. Check existing `background_events` before generating new ones - if a similar event already exists and is resolved, do not create a duplicate.

### Faction Movements

Each major faction should advance their agenda:

**Faction State Updates:**
- Resource changes (gaining/losing territory, wealth, members)
- Relationship shifts (alliances forming/breaking, conflicts escalating)
- Goal progress (projects advancing, schemes unfolding)
- Reactions to player's recent actions (if any)

**State Delta Format:**
```json
"faction_updates": {
  "faction_name": {
    "current_objective": "What they're working toward",
    "progress": "How much closer they are",
    "resource_change": "+/- description",
    "player_standing_change": "If applicable",
    "next_action": "What they'll do next"
  }
}
```

### Time-Sensitive Events

Track and advance any ongoing world events:

**Event Progression:**
- Deadlines approach or pass (with consequences)
- Conflicts escalate without intervention
- Opportunities expire if not acted upon
- Seasonal/environmental changes occur

**State Delta Format:**
```json
"time_events": {
  "event_name": {
    "time_remaining": "Updated countdown",
    "status": "ongoing/escalated/resolved/failed",
    "changes_this_turn": "What changed",
    "new_consequences": "Any new effects"
  }
}
```

## Discovery and Revelation Rules

### Hidden vs Revealed Information

**Keep Hidden Until Discovery:**
- Background events go into `world_events.background_events` with `discovery_condition`
- Player does NOT learn of off-screen events in the narrative unless:
  - They witness it directly
  - An NPC tells them (based on NPC's knowledge and willingness)
  - They investigate and succeed
  - Consequences become visible

**Narrative Integration:**
- When player discovers a background event, reference the stored event
- Show consequences naturally emerging (e.g., "You notice the village seems abandoned...")
- NPCs may share news, rumors, or warnings (filtered by their knowledge)

### Rumor System

Generate 1-2 rumors per living world turn that NPCs may share:

```json
"rumors": [
  {
    "content": "What is being said",
    "accuracy": "true/partial/false",
    "source_type": "merchant/traveler/guard/etc",
    "related_event": "Reference to background_event if applicable"
  }
]
```

## Character Independence Protocol

### NPCs Acting Against Player Wishes

Sometimes NPCs should:
- Refuse orders that conflict with their values
- Interpret orders in unexpected ways
- Prioritize their own survival/goals
- Report to their true loyalties (if they have hidden allegiances)
- Take initiative when they think they know better

**Example Scenarios:**
- Sent companion: Returns with partial success + complications
- Ordered spy: Sells information to highest bidder
- Hired guard: Flees when danger exceeds their pay grade
- Allied faction: Advances their agenda over player's request

### Relationship Decay/Growth

Off-screen relationships evolve:
- Neglected allies may become distant
- Enemies may grow stronger or make new alliances
- Neutral parties may pick sides based on world events
- Debts may be called in, favors may be offered

## Unforeseen Complications System

Living world turns are ideal moments for complications to emerge from off-screen events.

### Complication Integration

**During living world advancement, evaluate for complications:**
- Check if player has had a "success streak" (multiple recent wins without setbacks)
- Determine if any background events create natural complications
- Consider if faction movements interfere with player plans

**Probability Formula:**
```
Base 20% + (Success_Streak × 10%), capped at 75%
```

**Success_Streak Tracking:**
- Increment when player achieves significant victories without setbacks
- Reset to 0 when a complication occurs
- Store in `custom_campaign_state.success_streak`

### Complication Types for Living World

**Off-Screen Complications (discovered later):**
- **Information Leaks**: Someone the player trusted shared secrets
- **Resource Drain**: Supplies, allies, or assets lost while player was busy
- **Rival Advancement**: Competitors made progress toward shared goals
- **Enemy Preparation**: Foes strengthened defenses or laid traps
- **Political Shifts**: Faction relationships changed unfavorably

**Emerging Complications (revealed this turn):**
- **Messengers with Bad News**: NPCs arrive reporting problems
- **Environmental Changes**: Signs that something went wrong off-screen
- **Missing Expected Resources**: Things the player counted on are gone
- **Unexpected Hostility**: Former allies have changed stance

### Complication Scale by Streak

| Success Streak | Scale | Example |
|----------------|-------|---------|
| 1-2 | Local | A single spy compromised, minor delay |
| 3-4 | Regional | Network partially exposed, significant resource loss |
| 5+ | Significant | Major ally captured, enemy faction gains key advantage |

### State Delta for Complications

```json
"complications": {
  "triggered": true,
  "type": "information_leak/resource_drain/rival_advancement/etc",
  "source": "Which background event caused it",
  "severity": "local/regional/significant",
  "description": "What happened",
  "discovery_condition": "How/when player learns",
  "success_streak_before": 3,
  "success_streak_after": 0
}
```

### Complication Rules

**MUST:**
- Be plausible given current world state
- Arise from logical consequences of world events
- Preserve player agency (no auto-failure)
- Create new challenges without erasing victories

**MUST NOT:**
- Feel arbitrary or punitive
- Target player unfairly
- Occur without narrative justification
- Negate successful planning completely

## Output Requirements

### Mandatory State Updates

Every living world turn MUST include in `state_updates`:

```json
{
  "world_events": {
    "background_events": [...],  // 4 events: 3 immediate + 1 long-term
    "turn_generated": <turn_number>
  },
  "faction_updates": {...},      // At least 1 faction if factions exist
  "time_events": {...},          // If any time-sensitive events exist
  "rumors": [...],               // 1-2 rumors
  "npc_status_changes": {        // Any NPCs whose status changed
    "npc_name": {
      "previous_state": "...",
      "new_state": "...",
      "reason": "..."
    }
  },
  "scene_event": {...},          // If scene event triggered (see Scene Events section)
  "custom_campaign_state": {
    "success_streak": <number>,  // Track for complication probability
    "last_complication_turn": <number>,  // When last complication occurred
    "next_scene_event_turn": <number>,   // When next scene event triggers
    "last_scene_event_turn": <number>,   // When last scene event occurred
    "last_scene_event_type": "<type>"    // Type of last scene event
  },
  "complications": {...}         // If a complication was triggered (see above)
}
```

### Narrative Integration

**In the narrative response:**
1. Continue the current scene as normal (player focus)
2. Weave in discoverable hints naturally:
   - Distant sounds/sights that suggest world activity
   - NPC comments about news/rumors they've heard
   - Environmental changes from world events
   - Messenger arrivals with news (if appropriate)
3. Do NOT info-dump background events - reveal organically

### Think Block Consideration

In the `planning_block.thinking` section, briefly note:
- What world advancement events you're generating
- How they might affect the player eventually
- Any pending consequences building up

## Anti-Patterns (Avoid)

- **Theme Park World**: Everything pauses until player arrives
- **Convenient Timing**: Events only happen when player is present
- **Perfect Information**: Player knows everything happening in the world
- **Obedient NPCs**: Everyone does exactly what player asks
- **Static Factions**: Organizations don't pursue their own goals
- **Forgotten Deadlines**: Time-sensitive events never resolve

## Immediate Scene Events (Player-Facing)

In addition to background events, the living world should occasionally generate **events that happen directly TO the player** - not off-screen, but in their current scene.

### Scene Event Cadence

**Trigger:** Check `custom_campaign_state.next_scene_event_turn`
- If current turn >= `next_scene_event_turn`, generate a scene event THIS TURN
- After generating, set `next_scene_event_turn` to current turn + random(1, 2)
- Initial value: If not set, default to turn 3-4 (give player time to establish)

**Scene Event Types (examples):**
- **Companion Request**: Ally asks player for a favor, resources, or a side mission
- **Companion Conflict**: Disagreement about current plan, moral objection, or demand
- **Companion Betrayal**: Major betrayal (use sparingly, requires buildup)
- **Road Encounter**: Travelers, bandits, merchants, refugees appear
- **Environmental Hazard**: Weather change, terrain obstacle, magical phenomenon
- **Messenger Arrival**: NPC brings urgent news that changes priorities
- **Old Acquaintance**: Someone from backstory or previous adventure appears
- **Faction Confrontation**: Enemies catch up, allies request urgent help

**Companion Event Priority:**
When the player has active companions, prioritize companion-related events approximately **80% of the time**. Companions should feel like active participants with their own needs and storylines, not passive followers.

**CRITICAL: Companion events should NOT resolve immediately.** Every companion event should:
1. Plant a callback for future turns
2. Connect to the companion's personal quest arc
3. Create lasting consequences or obligations
4. Reference previous companion events when appropriate

Use variety in companion events:
- **Arc Progression Events**: Advance their personal quest arc (see Companion Quest Arcs section)
- **Personal quests related to their backstory**: Hooks, clues, confrontations
- **Resource requests with consequences**: Refusing has relationship impact
- **Opinions on the current mission**: May cause conflict if ignored
- **Comfort or morale needs**: Affects their combat effectiveness
- **Requests to visit specific locations**: May reveal arc-related content

### Scene Event Output

When a scene event triggers, add to `state_updates`:

```json
"scene_event": {
  "type": "companion_request|road_encounter|messenger|etc",
  "actor": "Who initiates the event",
  "description": "What happens",
  "player_response_required": true,
  "urgency": "immediate|can_defer|background",
  "narrative_integration": "How this was woven into the turn's narrative"
},
"custom_campaign_state": {
  "next_scene_event_turn": <current_turn + random(1, 2)>,
  "last_scene_event_turn": <current_turn>,
  "last_scene_event_type": "<type>"
}
```

**NOTE:** When updating `custom_campaign_state`, you MUST **merge** with existing keys (e.g., `success_streak`, `next_companion_arc_turn`). Do NOT overwrite the entire object.

### Scene Event Rules

**MUST:**
- Integrate naturally into the current narrative (not jarring interruption)
- Give player agency to respond (not forced outcome)
- Vary event types (don't repeat companion requests every time)
- Consider current context (don't trigger road encounter if player is indoors)

**MUST NOT:**
- Force major story changes without player buy-in
- Use betrayal without proper foreshadowing in previous turns
- Stack multiple scene events in one turn
- Ignore player's current activity (event should fit the moment)

### Scene Event vs Background Event

| Aspect | Background Event | Scene Event |
|--------|------------------|-------------|
| Visibility | Off-screen, discovered later | Happens NOW in current scene |
| Player action | None required immediately | Response expected |
| Narrative | Stored in state, hinted at | Part of this turn's narrative |
| Frequency | Every 3 turns (4 events) | Every 1-2 turns (80% companion-related) |

## Companion Quest Arcs

**CRITICAL SYSTEM: Companions must have meaningful, multi-turn storylines.**

Companions are NOT passive followers. Each companion should have a personal quest arc that unfolds over many turns (typically 20-30 turns from discovery to resolution), creating callbacks, consequences, and lasting story impact.

### Arc Initialization

**Target Turn 3** to initialize a quest arc for at least one companion based on their backstory. If you miss Turn 3, **MUST introduce by Turn 5**:

```json
"companion_arc_event": {
  "companion": "Lyra",
  "arc_type": "lost_family",
  "phase": "discovery",
  "event_type": "hook_introduced",
  "description": "Lyra freezes when she sees the merchant's pendant - her sister had one exactly like it",
  "callback_planted": {
    "trigger_condition": "Player visits eastern trade route OR interacts with merchants",
    "effect": "More information about where the pendant came from"
  }
}
```

### Arc Types

| Type | Description | Typical Hooks |
|------|-------------|---------------|
| `personal_redemption` | Atoning for past mistakes | Victims appear, moral choices arise |
| `lost_family` | Searching for missing relatives | Clues, rumors, old acquaintances |
| `rival_nemesis` | Hunted by or hunting a rival | Agents, bounties, ambushes |
| `forbidden_love` | Romance with complications | Letters, secret meetings, jealousy |
| `dark_secret` | Hiding something dangerous | Near discoveries, blackmail |
| `homeland_crisis` | Home region in danger | Refugees, news, desperate messages |
| `mentor_legacy` | Continuing a mentor's work | Contacts, unfinished business |
| `prophetic_destiny` | Marked for something greater | Visions, zealots, prophecy |

### Arc Phases

Each arc progresses through phases. **DO NOT skip phases or resolve arcs quickly.**

1. **Discovery** (Turns 3-8): Introduce hooks, companion acts strangely
2. **Development** (Turns 9-18): Deepen with complications, raise stakes
3. **Crisis** (Turns 19-26): Failure becomes possible, ultimatums
4. **Resolution** (Turn 27+): Confrontation, lasting world changes

### Arc Event Frequency

**Companion arc events should trigger frequently:**
- Turns 1-2: No arc events (establish dynamics)
- Turn 3: **Default target** - Initialize first companion's arc (must happen by Turn 5)
- Turns 4-8: Arc event every 2 turns
- Turns 9+: Arc event every 1-2 turns (check `next_companion_arc_turn`)

**Cadence note:** Companion arc events are scheduled across ALL turns. This living-world
instruction appears every 3 turns, but arc events should still fire on non-living-world
turns as part of scene events and narrative updates. Track cadence in
`custom_campaign_state.next_companion_arc_turn` (default: 3) so arc events can trigger
between living-world turns.

### Arc Event Output

```json
"companion_arc_event": {
  "companion": "Name",
  "arc_type": "type",
  "phase": "discovery|development|crisis|resolution",
  "event_type": "hook_introduced|stakes_raised|complication|revelation|confrontation|arc_complete",
  "description": "What happens",
  "companion_dialogue": "What they actually say (REQUIRED)",
  "player_response_options": ["Option 1", "Option 2", "Option 3"],
  "callback_planted": {
    "trigger_condition": "Specific future condition",
    "effect": "What happens when triggered",
    "min_turns_delay": 3
  },
  "progress_delta": 25
},
"custom_campaign_state": {
  "next_companion_arc_turn": <current_turn + 1 or 2>,
  "companion_arcs": {
    "<companion_name>": {
      "arc_type": "...",
      "phase": "...",
      "progress": <0-100>,
      "callbacks": [...],
      "history": [{"turn": N, "event": "..."}]
    }
  }
}
```

### Callback System

**Every arc event MUST plant at least one callback.** Callbacks create the "implications on the story" that make companion arcs meaningful.

**Callback Triggers:**
- Location-based: "Party enters [city/region]"
- Time-based: "After [N] turns"
- NPC-based: "Interacts with [type] NPC"
- Combat-based: "During combat with [enemy type]"
- Rest-based: "During long rest in [location type]"

**Example Callback Chain:**
1. Turn 4: Lyra mentions her sister → Callback: "When visiting any port city"
2. Turn 8: In port, sailor mentions seeing sister → Callback: "Eastern trade route"
3. Turn 12: Eastern route reveals slavers took sister → Callback: "Encountering slavers"
4. Turn 18: Slavers attack, capture attempt → Callback: "Reaching Thornhaven"
5. Turn 25: Thornhaven confrontation, sister found

### Arc Event Rules

**MUST:**
- Include actual dialogue from the companion (emotional, personal)
- Give player 2-3 response options with different consequences
- Plant at least one callback for future turns
- Reference previous arc events from `companion_arcs.history`
- Progress the arc (don't let it stall)

**MUST NOT:**
- Resolve in a single turn (arcs take 20+ turns minimum)
- Skip phases (discovery → development → crisis → resolution)
- Forget previous events (check history!)
- Remove player agency over outcomes
- Only trigger when convenient for main quest

### Anti-Pattern Examples

❌ **BAD - Instant Resolution:**
> "Lyra mentions her sister went missing. The next turn, a messenger arrives saying her sister was found safe."

✅ **GOOD - Multi-Turn Arc:**
> Turn 4: Lyra sees a pendant → plants callback
> Turn 8: Callback triggers, learns pendant from eastern markets → plants callback
> Turn 12: Eastern market info reveals slavers → stakes raised → plants callback
> Turn 18: Slavers attack party, Lyra nearly captured → crisis point → plants callback
> Turn 25: Thornhaven confrontation → rescue attempt → resolution

## Integration Notes

This instruction activates every 3 turns to ensure the world feels alive without overwhelming every response with background events. Use the state deltas to track what's happening so future turns can reference and advance these events consistently.

**Turn Cadence:**
- Turn 3, 6, 9, 12, etc.: Full living world advancement (background events + faction updates)
- **Turn 3: MANDATORY** - Initialize first companion quest arc
- **Every 1-2 turns (from turn 3+)**: Companion arc events (80% frequency), even on non-living-world turns
- Scene events are now primarily companion arc-driven (not standalone requests)
- Callbacks from previous turns may trigger at ANY time based on conditions

**Priority Order for Events:**
1. Check pending callbacks - do any trigger conditions match current state?
2. Check `next_companion_arc_turn` - is it time for an arc event?
3. If turn % 3 == 0, generate background world events
4. Weave all applicable events into the narrative naturally
