"""
Data fixtures for testing.
Provides realistic sample data for campaigns, game states, and AI responses.

Note: This is a data fixtures file, not a test file.
It provides sample data for other tests to use.
"""

import datetime
import os
import sys

from mvp_site import constants

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Sample campaign data
SAMPLE_CAMPAIGN = {
    "id": "test_campaign_123",
    "title": "The Lost Crown Adventure",
    "user_id": "test_user_456",
    "prompt": "Start an adventure in a medieval fantasy world",
    "selected_prompts": [
        constants.PROMPT_TYPE_NARRATIVE,
        constants.PROMPT_TYPE_MECHANICS,
    ],
    "created_at": datetime.datetime(2023, 6, 15, 10, 30, 0, tzinfo=datetime.timezone.utc),
    "last_played": datetime.datetime(2023, 6, 15, 14, 45, 0, tzinfo=datetime.timezone.utc),
}

# Sample game state data
SAMPLE_GAME_STATE = {
    "game_state_version": 1,
    "player_character_data": {
        "name": "Sir Kaelan the Adamant",
        "hp_current": 85,
        "hp_max": 100,
        "level": 3,
        "experience": 2750,
        "gold": 150,
        constants.KEY_MBTI: "ENFJ",
        "alignment": "Lawful Good",
        "core_ambition": "Restore the lost crown to the rightful heir",
        "next_milestone": "Find the Crown's first fragment",
    },
    "world_data": {
        "current_location_name": "Ancient Tavern",
        "current_location": "Ancient Tavern",
        "weather": "Misty evening",
        "world_time": {"hour": 18, "minute": 30, "second": 0, "time_of_day": "Evening"},
    },
    "npc_data": {
        "innkeeper": {
            "name": "Gareth the Wise",
            "relationship": "Friendly",
            constants.KEY_MBTI: "ISFJ",
            "last_interaction": "Provided information about the crown",
        },
        "mysterious_stranger": {
            "name": "Shadowcloak",
            "relationship": "Unknown",
            constants.KEY_MBTI: "INTJ",
            "last_interaction": "Warned about dangers ahead",
        },
    },
    "custom_campaign_state": {
        "active_missions": ["Find the Lost Crown", "Investigate the abandoned tower"],
        "completed_missions": ["Escape from the dungeon"],
        "core_memories": [
            "Escaped from the dark dungeon with mysterious key",
            "Met Gareth who knows about the crown's history",
            "Shadowcloak warned about the tower's dangers",
        ],
        "last_story_mode_sequence_id": 5,
    },
    "last_state_update_timestamp": datetime.datetime(
        2023, 6, 15, 14, 45, 0, tzinfo=datetime.timezone.utc
    ),
    "migration_status": "MIGRATED",
    "debug_mode": True,
}

# Sample story context
SAMPLE_STORY_CONTEXT = [
    {
        constants.KEY_ACTOR: constants.ACTOR_USER,
        constants.KEY_TEXT: "I look around the tavern and approach the innkeeper",
        constants.KEY_MODE: constants.MODE_CHARACTER,
        "sequence_id": 1,
        "timestamp": datetime.datetime(2023, 6, 15, 14, 30, 0, tzinfo=datetime.timezone.utc),
    },
    {
        constants.KEY_ACTOR: constants.ACTOR_GEMINI,
        constants.KEY_TEXT: "The tavern is dimly lit by flickering candles. Gareth the innkeeper looks up from cleaning a mug, his weathered face breaking into a warm smile. 'Ah, Sir Kaelan! I've been expecting you. I hear you seek information about the Lost Crown.'",
        constants.KEY_MODE: constants.MODE_CHARACTER,
        "sequence_id": 2,
        "timestamp": datetime.datetime(2023, 6, 15, 14, 31, 0, tzinfo=datetime.timezone.utc),
    },
    {
        constants.KEY_ACTOR: constants.ACTOR_USER,
        constants.KEY_TEXT: "Tell me what you know about the crown",
        constants.KEY_MODE: constants.MODE_CHARACTER,
        "sequence_id": 3,
        "timestamp": datetime.datetime(2023, 6, 15, 14, 32, 0, tzinfo=datetime.timezone.utc),
    },
]

# Sample AI responses for different scenarios
SAMPLE_AI_RESPONSES = {
    "normal_response": "Sir Kaelan nods thoughtfully as he processes the innkeeper's words. The flickering candlelight dances across his determined features.",
    "hp_discrepancy_response": "Sir Kaelan lies unconscious on the tavern floor, completely drained of life force after the mysterious encounter.",
    "location_mismatch_response": "Standing in the middle of the dark forest, Sir Kaelan hears the ancient trees whispering secrets of the lost crown.",
    "mission_completion_response": "With the dragon finally defeated and the treasure secured, Sir Kaelan's quest was complete. The Lost Crown gleamed in his hands.",
    "state_update_response": """Sir Kaelan carefully examines the crown fragment, feeling its ancient power.

[STATE_UPDATES_PROPOSED]
{
    "player_character_data": {
        "hp_current": 90,
        "experience": 3000
    },
    "custom_campaign_state": {
        "core_memories": {
            "append": ["Discovered the first crown fragment in the tower"]
        }
    }
}
[END_STATE_UPDATES_PROPOSED]""",
}

# Sample state updates for testing
SAMPLE_STATE_UPDATES = {
    "hp_update": {"player_character_data": {"hp_current": 75, "hp_max": 100}},
    "location_update": {
        "world_data": {"current_location_name": "Dark Forest", "weather": "Foggy"}
    },
    "mission_completion": {
        "custom_campaign_state": {
            "completed_missions": {"append": ["Find the Lost Crown"]},
            "active_missions": [],
        }
    },
    "complex_update": {
        "player_character_data": {"hp_current": 95, "gold": 200, "experience": 3500},
        "world_data": {
            "current_location_name": "Royal Palace",
            "world_time": {"hour": 6, "minute": 0, "second": 0, "time_of_day": "Dawn"},
        },
        "custom_campaign_state": {
            "core_memories": {"append": ["Returned the crown to the rightful heir"]}
        },
    },
}

# Discrepancy scenarios for validation testing
DISCREPANCY_SCENARIOS = {
    "hp_unconscious": {
        "game_state": {"player_character_data": {"hp_current": 25, "hp_max": 100}},
        "narrative": "The hero lies unconscious on the ground, completely drained of life force.",
        "expected_discrepancies": 1,
    },
    "location_conflict": {
        "game_state": {"world_data": {"current_location_name": "Tavern"}},
        "narrative": "Standing in the middle of the dark forest, surrounded by ancient trees.",
        "expected_discrepancies": 1,
    },
    "mission_completed": {
        "game_state": {
            "custom_campaign_state": {
                "active_missions": ["Find the lost treasure", "Defeat the dragon"]
            }
        },
        "narrative": "With the dragon finally defeated and the treasure secured, the quest was complete.",
        "expected_discrepancies": 2,
    },
}
