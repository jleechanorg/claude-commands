#!/usr/bin/env python3
"""
Test scenarios for Milestone 0.4
Provides game states for different desync-prone situations
"""

from typing import Any


def get_scenario(scenario_id: str, campaign_id: str = "test") -> dict[str, Any]:
    """Get a test scenario game state"""

    scenarios = {
        "multi_character": create_multi_character_scenario(),
        "split_party": create_split_party_scenario(),
        "combat_injured": create_combat_injured_scenario(),
        "hidden_characters": create_hidden_characters_scenario(),
        "npc_heavy": create_npc_heavy_scenario(),
    }

    return scenarios.get(scenario_id, scenarios["multi_character"])


def create_multi_character_scenario() -> dict[str, Any]:
    """Scenario 1: All party members present in same location"""
    return {
        "scenario_id": "multi_character",
        "description": "Party discussing plans in tavern",
        "session": 5,
        "turn": 23,
        "game_state": {
            "location": "The Silver Stag Tavern",
            "player_character_data": {
                "name": "Lyra",
                "hp": 28,
                "hp_max": 32,
                "class": "Ranger",
            },
            "npc_data": {
                "Theron": {
                    "present": True,
                    "hp": 45,
                    "hp_max": 45,
                    "class": "Fighter",
                    "conscious": True,
                },
                "Marcus": {
                    "present": True,
                    "hp": 20,
                    "hp_max": 24,
                    "class": "Wizard",
                    "conscious": True,
                },
                "Elara": {
                    "present": True,
                    "hp": 30,
                    "hp_max": 30,
                    "class": "Cleric",
                    "conscious": True,
                },
            },
            "combat_state": {"in_combat": False},
        },
        "expected_entities": ["Lyra", "Theron", "Marcus", "Elara"],
        "common_desync": "One or more party members omitted from narrative",
    }


def create_split_party_scenario() -> dict[str, Any]:
    """Scenario 2: Party split across different locations"""
    return {
        "scenario_id": "split_party",
        "description": "Rogue scouting while party waits",
        "session": 8,
        "turn": 45,
        "game_state": {
            "location": "Town Square",
            "player_character_data": {
                "name": "Shadowblade",
                "hp": 25,
                "hp_max": 28,
                "class": "Rogue",
                "actual_location": "Warehouse District",
            },
            "npc_data": {
                "Grimnar": {
                    "present": True,
                    "location": "Town Square",
                    "hp": 50,
                    "hp_max": 52,
                    "conscious": True,
                },
                "Lyanna": {
                    "present": True,
                    "location": "Town Square",
                    "hp": 35,
                    "hp_max": 35,
                    "conscious": True,
                },
                "Finn": {
                    "present": False,
                    "location": "The Inn",
                    "hp": 40,
                    "hp_max": 40,
                    "conscious": True,
                },
            },
            "combat_state": {"in_combat": False},
            "special_note": "Shadowblade is scouting alone in Warehouse District",
        },
        "expected_entities": ["Shadowblade"],  # Only PC should be mentioned
        "expected_absent": ["Grimnar", "Lyanna"],  # Should be noted as elsewhere
        "common_desync": "Merging split locations or wrong character placement",
    }


def create_combat_injured_scenario() -> dict[str, Any]:
    """Scenario 3: Combat with injured/low HP characters"""
    return {
        "scenario_id": "combat_injured",
        "description": "Mid-combat with injuries",
        "session": 12,
        "turn": 67,
        "game_state": {
            "location": "Goblin Cave",
            "player_character_data": {
                "name": "Aldric",
                "hp": 5,
                "hp_max": 40,
                "class": "Paladin",
                "conditions": ["bloodied", "exhausted"],
            },
            "npc_data": {
                "Mira": {
                    "present": True,
                    "hp": 12,
                    "hp_max": 30,
                    "conscious": True,
                    "conditions": ["wounded"],
                },
                "Goblin Chief": {
                    "present": True,
                    "hp": 18,
                    "hp_max": 35,
                    "conscious": True,
                    "hostile": True,
                },
                "Goblin Warrior 1": {
                    "present": True,
                    "hp": 8,
                    "hp_max": 15,
                    "conscious": True,
                    "hostile": True,
                },
                "Goblin Warrior 2": {
                    "present": True,
                    "hp": 0,
                    "hp_max": 15,
                    "conscious": False,
                    "conditions": ["dead"],
                },
            },
            "combat_state": {
                "in_combat": True,
                "round": 4,
                "participants": ["Aldric", "Mira", "Goblin Chief", "Goblin Warrior 1"],
            },
        },
        "expected_entities": ["Aldric", "Mira", "Goblin Chief", "Goblin Warrior 1"],
        "common_desync": "Injured characters omitted or dead enemies included",
    }


def create_hidden_characters_scenario() -> dict[str, Any]:
    """Scenario 4: Hidden/invisible characters present"""
    return {
        "scenario_id": "hidden_characters",
        "description": "Stealth mission with hidden allies",
        "session": 6,
        "turn": 89,
        "game_state": {
            "location": "Noble's Manor - Grand Hall",
            "player_character_data": {
                "name": "Whisper",
                "hp": 22,
                "hp_max": 25,
                "class": "Rogue",
                "conditions": ["hidden"],
            },
            "npc_data": {
                "Lord Blackwood": {
                    "present": True,
                    "hp": 30,
                    "hp_max": 30,
                    "conscious": True,
                    "aware_of_pcs": False,
                },
                "Guard Captain": {
                    "present": True,
                    "hp": 40,
                    "hp_max": 40,
                    "conscious": True,
                },
                "Zara": {
                    "present": True,
                    "hp": 28,
                    "hp_max": 28,
                    "conscious": True,
                    "conditions": ["invisible"],
                    "class": "Wizard",
                },
                "Felix": {
                    "present": True,
                    "hp": 35,
                    "hp_max": 35,
                    "conscious": True,
                    "conditions": ["disguised"],
                    "disguise": "Servant",
                },
            },
            "combat_state": {"in_combat": False},
            "special_conditions": ["stealth_required", "no_detection"],
        },
        "expected_entities": ["Lord Blackwood", "Guard Captain", "Felix"],
        "hidden_entities": ["Whisper", "Zara"],
        "common_desync": "Hidden characters revealed or visible characters omitted",
    }


def create_npc_heavy_scenario() -> dict[str, Any]:
    """Scenario 5: Many NPCs present (crowd scene)"""
    return {
        "scenario_id": "npc_heavy",
        "description": "Royal court with many nobles",
        "session": 10,
        "turn": 112,
        "game_state": {
            "location": "Throne Room",
            "player_character_data": {
                "name": "Sir Garrett",
                "hp": 48,
                "hp_max": 48,
                "class": "Knight",
            },
            "npc_data": {
                "King Aldwin": {
                    "present": True,
                    "hp": 40,
                    "hp_max": 40,
                    "conscious": True,
                    "role": "monarch",
                },
                "Queen Elissa": {
                    "present": True,
                    "hp": 35,
                    "hp_max": 35,
                    "conscious": True,
                },
                "Prince Roderick": {
                    "present": True,
                    "hp": 38,
                    "hp_max": 38,
                    "conscious": True,
                },
                "Lord Commander Hayes": {
                    "present": True,
                    "hp": 45,
                    "hp_max": 45,
                    "conscious": True,
                },
                "Court Wizard Merlin": {
                    "present": True,
                    "hp": 25,
                    "hp_max": 25,
                    "conscious": True,
                },
                "Lady Rosanne": {
                    "present": True,
                    "hp": 20,
                    "hp_max": 20,
                    "conscious": True,
                },
                "Duke Blackthorne": {
                    "present": True,
                    "hp": 42,
                    "hp_max": 42,
                    "conscious": True,
                },
                "Ambassador Chen": {
                    "present": True,
                    "hp": 30,
                    "hp_max": 30,
                    "conscious": True,
                },
            },
            "combat_state": {"in_combat": False},
            "scene_type": "social",
            "focus_npcs": ["King Aldwin", "Queen Elissa", "Lord Commander Hayes"],
        },
        "expected_entities": ["Sir Garrett", "King Aldwin", "Queen Elissa"],
        "should_mention": ["Lord Commander Hayes"],  # Key NPCs
        "can_summarize": [
            "Prince Roderick",
            "Court Wizard Merlin",
            "Lady Rosanne",
            "Duke Blackthorne",
            "Ambassador Chen",
        ],  # Background NPCs
        "common_desync": "Important NPCs lost in crowd or all NPCs omitted",
    }


def get_all_scenarios() -> list[str]:
    """Get list of all scenario IDs"""
    return [
        "multi_character",
        "split_party",
        "combat_injured",
        "hidden_characters",
        "npc_heavy",
    ]
