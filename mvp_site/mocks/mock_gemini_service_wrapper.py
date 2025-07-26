"""
Mock Gemini Service wrapper that provides the same interface as the real gemini_service module.
"""

import os
import sys

from .structured_fields_fixtures import INITIAL_CAMPAIGN_RESPONSE

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging_util
from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse

from .mock_gemini_service import MockGeminiClient

# Module-level client instance (like the real service)
_client = None


def get_client():
    """Get the mock Gemini client instance."""
    global _client
    if _client is None:
        logging_util.info("Mock Gemini Service: Creating mock client")
        _client = MockGeminiClient()
    return _client


def generate_content(
    prompt_parts,
    temperature=None,
    max_output_tokens=None,
    top_p=None,
    top_k=None,
    response_mime_type=None,
    response_schema=None,
    model_name=None,
):
    """
    Mock generate_content function that mimics the real service interface.

    Note: Parameters temperature, max_output_tokens, top_p, top_k, response_mime_type,
    and response_schema are accepted for API compatibility but not used in mock.
    """
    client = get_client()

    # Log the call
    logging_util.debug(
        f"Mock Gemini Service: generate_content called with model={model_name}"
    )

    # The mock doesn't use these parameters but accepts them for compatibility
    response = client.generate_content(prompt_parts, model=model_name)

    return response


def get_initial_story(
    prompt,
    user_id=None,
    selected_prompts=None,
    generate_companions=False,
    use_default_world=False,
):
    """
    Mock get_initial_story function that returns predefined content.
    """
    client = get_client()
    logging_util.info("Mock Gemini Service: get_initial_story called")

    # Import structured response fixture for initial story
    try:
        # Use the narrative from the initial campaign response
        narrative_text = INITIAL_CAMPAIGN_RESPONSE.get(
            "narrative", "Default narrative text"
        )
    except ImportError:
        narrative_text = """Sir Kaelan the Adamant awakens in the dimly lit Ancient Tavern, the scent of ale and wood smoke filling his nostrils. The mysterious key from his dungeon escape weighs heavy in his pocket. Gareth the innkeeper approaches with a knowing smile.

"Ah, Sir Kaelan! Word travels fast in these parts. I hear you seek the Lost Crown. Dangerous business, that. But perhaps... perhaps I can help."

Gareth leans in closer, his voice dropping to a whisper. "There's an old map in my possession. Shows the way to the Whispering Woods where the crown was last seen. But I'll need something in return..."

What do you do?"""

    # Create NarrativeResponse object with proper parameters
    # Use structured fields from fixture if available
    if "INITIAL_CAMPAIGN_RESPONSE" in locals():
        narrative_response = NarrativeResponse(
            narrative=narrative_text,
            session_header=INITIAL_CAMPAIGN_RESPONSE.get(
                "session_header",
                "[SESSION_HEADER]\nTimestamp: Unknown\nLocation: Character Creation\nStatus: Creating Character",
            ),
            resources=INITIAL_CAMPAIGN_RESPONSE.get("resources", "None"),
            planning_block=INITIAL_CAMPAIGN_RESPONSE.get("planning_block", {}),
            dice_rolls=INITIAL_CAMPAIGN_RESPONSE.get("dice_rolls", []),
            god_mode_response=INITIAL_CAMPAIGN_RESPONSE.get("god_mode_response", ""),
            entities_mentioned=INITIAL_CAMPAIGN_RESPONSE.get("entities_mentioned", []),
            location_confirmed=INITIAL_CAMPAIGN_RESPONSE.get(
                "location_confirmed", "Character Creation"
            ),
            state_updates=INITIAL_CAMPAIGN_RESPONSE.get("state_updates", {}),
            debug_info=INITIAL_CAMPAIGN_RESPONSE.get("debug_info", {}),
            turn_summary="Initial campaign creation",
        )
    else:
        # Fallback with basic structure
        state_updates = {
            "world_data": {"current_location_name": "Character Creation"},
            "custom_campaign_state": {
                "campaign_title": "Test Campaign",
                "character_name": "Ser Arion",
                "setting": "Assiah",
            },
        }

        narrative_response = NarrativeResponse(
            narrative=narrative_text,
            entities_mentioned=[],
            location_confirmed="Character Creation",
            turn_summary="Campaign creation started.",
            state_updates=state_updates,
            session_header="[SESSION_HEADER]\nTimestamp: Unknown\nLocation: Character Creation\nStatus: Creating Character",
            planning_block={
                "thinking": "The player has specified a character. Present character creation options.",
                "choices": {
                    "ai_generated": {
                        "text": "AI Generated Character",
                        "description": "Let the AI create a complete D&D 5e character sheet.",
                        "risk_level": "safe",
                    },
                    "custom_class": {
                        "text": "Custom Class Creation",
                        "description": "Design unique custom mechanics.",
                        "risk_level": "safe",
                    },
                    "standard_dnd": {
                        "text": "Standard D&D Creation",
                        "description": "Choose from standard D&D 5e options.",
                        "risk_level": "safe",
                    },
                },
            },
            dice_rolls=[],
            resources="None",
        )

    # Create GeminiResponse object
    response = GeminiResponse(
        narrative_text=narrative_text, structured_response=narrative_response
    )

    return response


def continue_story(
    user_input,
    mode,
    story_context,
    current_game_state,
    selected_prompts=None,
    use_default_world=False,
):
    """
    Mock continue_story function that returns predefined content.
    """
    client = get_client()
    logging_util.info(f"Mock Gemini Service: continue_story called with mode={mode}")

    # Use the imported classes

    # Generate a response based on the user input
    if "attack" in user_input.lower():
        narrative_text = """You draw your sword and charge at your opponent! The clash of steel rings through the air as you engage in fierce combat.

Your strike lands true, dealing damage to your enemy."""
        state_updates = {"combat_active": True, "enemy_hp": 15}
    elif "talk" in user_input.lower() or "speak" in user_input.lower():
        narrative_text = """You approach cautiously and attempt to engage in conversation. The figure turns to face you, revealing weathered features and wise eyes.

"Greetings, traveler," they say. "I've been expecting you."""
        state_updates = {
            "npcs": [{"name": "Mysterious Figure", "disposition": "Neutral"}]
        }
    else:
        narrative_text = f"""You {user_input}.

The world responds to your actions, and new possibilities unfold before you."""
        state_updates = {}

    # Import structured fields if available
    try:
        from .structured_fields_fixtures import FULL_STRUCTURED_RESPONSE
    except ImportError:
        FULL_STRUCTURED_RESPONSE = None

    # Add structured fields to the response
    if FULL_STRUCTURED_RESPONSE:
        # Use full structured fields from fixtures
        narrative_response = NarrativeResponse(
            narrative=narrative_text,
            session_header=FULL_STRUCTURED_RESPONSE.get("session_header", "Session 1"),
            planning_block=FULL_STRUCTURED_RESPONSE.get("planning_block", {}),
            dice_rolls=FULL_STRUCTURED_RESPONSE.get("dice_rolls", []),
            resources=FULL_STRUCTURED_RESPONSE.get("resources", ""),
            npcs=FULL_STRUCTURED_RESPONSE.get("npcs", ""),
            locations=FULL_STRUCTURED_RESPONSE.get("locations", ""),
            lore=FULL_STRUCTURED_RESPONSE.get("lore", ""),
            secrets=FULL_STRUCTURED_RESPONSE.get("secrets", ""),
            god_mode_response=FULL_STRUCTURED_RESPONSE.get("god_mode_response", None),
            debug_info=FULL_STRUCTURED_RESPONSE.get("debug_info", None),
            entities_mentioned=[],
            location_confirmed="Unknown",
            turn_summary="Action taken.",
            state_updates=state_updates,
        )
    else:
        # Fallback to basic response
        narrative_response = NarrativeResponse(
            narrative=narrative_text,
            entities_mentioned=[],
            location_confirmed="Unknown",
            turn_summary="Action taken.",
            state_updates=state_updates,
        )

    response = GeminiResponse(
        narrative_text=narrative_text, structured_response=narrative_response
    )

    return response


# Export the same functions as the real service
__all__ = ["get_client", "generate_content", "get_initial_story", "continue_story"]
