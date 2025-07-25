"""
Structured field fixtures for UI testing.
Provides proper JSON responses with all 10 fields from game_state_instruction.md.
"""

# Initial campaign creation response matching expected screenshots
INITIAL_CAMPAIGN_RESPONSE = {
    "session_header": "[SESSION_HEADER]\nTimestamp: Unknown\nLocation: Character Creation\nStatus: Creating Character",
    "resources": "None",
    "narrative": """You are Ser Arion, a 16 year old honorable knight on your first mission, sworn to protect the vast Celestial Imperium. For decades, the Empire has been ruled by the iron-willed Empress Sariel, a ruthless tyrant who uses psychic power to crush dissent. While her methods are terrifying, her reign has brought undeniable benefits: the roads are safe, commerce thrives, and the Imperium has never been stronger. But dark whispers speak of the Dragon Knights - an ancient order that once served the realm before mysteriously vanishing. As you journey through this morally complex world, you must decide: will you serve the tyrant who brings order, or seek a different path?

Scene #1: [CHARACTER CREATION - Step 1]

CAMPAIGN SUMMARY
================
Title: Celestial Imperium: Order Under Tyranny
Character: Ser Arion
Setting: Assiah
Description: You are Ser Arion, a 16 year old honorable knight on your first mission, sworn to protect the vast Celestial Imperium. For decades, the Empire has been ruled by the iron-willed Empress Sariel, a ruthless tyrant who uses psychic power to crush dissent. While her methods are terrifying, her reign has brought undeniable benefits: the roads are safe, commerce thrives, and the Imperium has never been stronger. But dark whispers speak of the Dragon Knights - an ancient order that once served the realm before mysteriously vanishing. As you journey through this morally complex world, you must decide: will you serve the tyrant who brings order, or seek a different path?
AI Personalities: Narrative, Mechanics
Options: Companions, Modified World

Now, how would you like to design Ser Arion using D&D 5e mechanics?
1. **[AIGenerated]:** I'll create a complete D&D version of Ser Arion based on his description and the world lore.
2. **[StandardDND]:** You choose Ser Arion's race (Human, given context) and class (Fighter, Paladin, etc.) from D&D options.
3. **[CustomClass]:** We'll create custom mechanics for Ser Arion's unique knightly abilities within the Celestial Imperium.

Which option would you prefer? (1, 2, or 3)""",
    "planning_block": {
        "thinking": "The player has specified a character. I need to present the character creation options to flesh out Ser Arion's D&D 5e mechanics, while strictly avoiding any narrative or in-world descriptions during this meta-game phase.",
        "context": "Character creation phase - presenting D&D mechanics options.",
        "choices": {
            "ai_generated": {
                "text": "AI Generated Character",
                "description": "Let the AI create a complete D&D 5e character sheet for Ser Arion.",
                "risk_level": "safe"
            },
            "custom_class": {
                "text": "Custom Class Creation",
                "description": "Work with the AI to design unique custom mechanics for Ser Arion's knightly abilities.",
                "risk_level": "safe"
            },
            "standard_dnd": {
                "text": "Standard D&D Creation",
                "description": "Choose Ser Arion's race (Human) and class from standard D&D 5e options.",
                "risk_level": "safe"
            }
        }
    },
    "dice_rolls": [],
    "god_mode_response": "",
    "entities_mentioned": [],
    "location_confirmed": "Character Creation",
    "state_updates": {
        "world_data": {
            "current_location_name": "Character Creation"
        },
        "custom_campaign_state": {
            "campaign_title": "Celestial Imperium: Order Under Tyranny",
            "character_name": "Ser Arion",
            "setting": "Assiah"
        }
    },
    "debug_info": {
        "dm_notes": ["Initial state creation, setting character creation in progress and recording campaign summary and initial state."],
        "state_rationale": "Initial state creation, setting character creation in progress and recording campaign summary and initial state."
    }
}

# Complete structured response with all 10 required fields
FULL_STRUCTURED_RESPONSE = {
    "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Ches 20, 10:00\nLocation: Goblin Cave - Main Chamber\nStatus: Lvl 5 Fighter | HP: 28/32 (Temp: 0) | AC: 18 | XP: 6500/14000 | Gold: 125gp\nResources: HD: 3/5 | Second Wind: 1/1 | Action Surge: 1/1 | Potions: 2\nConditions: None | Exhaustion: 0 | Inspiration: No",
    "resources": "HD: 3/5 | Second Wind: 1/1 | Action Surge: 1/1 | Potions: 2 | Rations: 5",
    "narrative": "You swing your sword in a mighty arc, catching the goblin off guard. The blade bites deep into its shoulder, causing it to shriek in pain and stumble backward. Dark blood spatters the cave floor as the creature clutches its wound, its eyes now filled with fear rather than aggression.\n\nThe goblin chieftain at the back of the cave rises from his crude throne, anger flashing in his yellow eyes. He barks a command in the guttural goblin tongue, and two more goblins emerge from the shadows, rusty blades at the ready.",
    "planning_block": {
        "thinking": "The player has wounded one goblin but now faces three enemies total. This is a dangerous situation that requires tactical thinking.",
        "context": "The cave is dimly lit with limited maneuvering room. The wounded goblin is retreating while two fresh enemies advance.",
        "choices": {
            "press_attack": {
                "text": "Press the Attack",
                "description": "Continue attacking the wounded goblin to finish it off before it can recover",
                "risk_level": "medium"
            },
            "defensive_stance": {
                "text": "Take Defensive Stance",
                "description": "Fall back to a defensive position and prepare to counter their attacks",
                "risk_level": "low"
            },
            "action_surge": {
                "text": "Use Action Surge",
                "description": "Unleash a flurry of attacks using your fighter's Action Surge ability",
                "risk_level": "high"
            },
            "intimidate": {
                "text": "Intimidate Enemies",
                "description": "Try to intimidate the goblins with a fierce battle cry and aggressive posture",
                "risk_level": "medium"
            }
        }
    },
    "dice_rolls": [
        "Attack Roll: 1d20+7 = 15+7 = 22 (Hit!)",
        "Damage Roll: 1d8+4 = 6+4 = 10 slashing damage",
        "Goblin Constitution Save: 1d20+1 = 8+1 = 9 (Failed - remains conscious but badly wounded)"
    ],
    "god_mode_response": "",
    "entities_mentioned": ["goblin", "goblin chieftain", "wounded goblin"],
    "location_confirmed": "Goblin Cave - Main Chamber",
    "state_updates": {
        "npcs": {
            "goblin_warrior_1": {
                "hp": 2,
                "max_hp": 12,
                "status": "badly_wounded",
                "position": "retreating"
            },
            "goblin_chieftain": {
                "hp": 28,
                "max_hp": 28,
                "status": "angry",
                "position": "throne"
            },
            "goblin_warrior_2": {
                "hp": 12,
                "max_hp": 12,
                "status": "advancing"
            },
            "goblin_warrior_3": {
                "hp": 12,
                "max_hp": 12,
                "status": "advancing"
            }
        },
        "combat": {
            "in_combat": True,
            "round": 2,
            "turn_order": ["player", "goblin_chieftain", "goblin_warrior_2", "goblin_warrior_3", "goblin_warrior_1"]
        }
    },
    "debug_info": {
        "dm_notes": [
            "Player made a successful attack against goblin_warrior_1",
            "Introducing reinforcements to increase challenge",
            "Chieftain will likely cast a spell next round if not engaged"
        ],
        "state_rationale": "Updated NPC HP values and positions based on combat results. Added new combatants to the encounter."
    }
}

# God mode specific response
GOD_MODE_RESPONSE = {
    "session_header": "",
    "resources": "",
    "narrative": "",
    "planning_block": {},
    "dice_rolls": [],
    "god_mode_response": "=== GOD MODE INFORMATION ===\n\nCurrent Scene State:\n- 3 goblins in main chamber (1 wounded, 2 fresh)\n- Goblin chieftain has spell scroll of Magic Missile\n- Hidden treasure: 50gp in chest behind throne\n- Secret passage in north wall (DC 15 Perception to find)\n- Trap on chest (DC 12 to disarm)\n\nUpcoming Events:\n- If chieftain reaches 50% HP, will attempt to flee through secret passage\n- Reinforcements arrive in 5 rounds if alarm is raised\n\nSuggested Plot Hooks:\n1. Chieftain has map fragment showing dungeon deeper levels\n2. One goblin is actually a polymorphed merchant\n3. Ancient dwarven runes on walls hint at lost treasure",
    "entities_mentioned": ["goblin chieftain", "polymorphed merchant"],
    "location_confirmed": "Goblin Cave - Main Chamber",
    "state_updates": {},
    "debug_info": {
        "dm_notes": ["God mode query - provided scene overview and suggestions"],
        "state_rationale": "No state changes in god mode response"
    }
}

# Response with all fields but some empty (minimal response)
MINIMAL_STRUCTURED_RESPONSE = {
    "session_header": "[SESSION_HEADER]\nTimestamp: Dawn\nLocation: Village Square\nStatus: Resting",
    "resources": "All resources full",
    "narrative": "The morning sun rises over the peaceful village square. Birds chirp in the nearby trees as merchants begin setting up their stalls for the day's trade.",
    "planning_block": {
        "thinking": "Peaceful moment for character interaction and exploration",
        "choices": {
            "visit_merchant": {
                "text": "Visit the Merchants",
                "description": "Browse the wares at the market stalls",
                "risk_level": "safe"
            },
            "explore_village": {
                "text": "Explore the Village",
                "description": "Walk around and get familiar with the village layout",
                "risk_level": "safe"
            }
        }
    },
    "dice_rolls": [],
    "god_mode_response": "",
    "entities_mentioned": [],
    "location_confirmed": "Village Square",
    "state_updates": {},
    "debug_info": {
        "dm_notes": ["Starting a new day in the village"],
        "state_rationale": "No combat or state changes in this peaceful scene"
    }
}
