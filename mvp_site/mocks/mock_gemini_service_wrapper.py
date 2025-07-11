"""
Mock Gemini Service wrapper that provides the same interface as the real gemini_service module.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .mock_gemini_service import MockGeminiClient
import logging_util
from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse

# Module-level client instance (like the real service)
_client = None

def get_client():
    """Get the mock Gemini client instance."""
    global _client
    if _client is None:
        logging_util.info("Mock Gemini Service: Creating mock client")
        _client = MockGeminiClient()
    return _client

def generate_content(prompt_parts, temperature=None, max_output_tokens=None, 
                    top_p=None, top_k=None, response_mime_type=None,
                    response_schema=None, model_name=None):
    """
    Mock generate_content function that mimics the real service interface.
    """
    client = get_client()
    
    # Log the call
    logging_util.debug(f"Mock Gemini Service: generate_content called with model={model_name}")
    
    # The mock doesn't use these parameters but accepts them for compatibility
    response = client.generate_content(prompt_parts, model=model_name)
    
    return response

def get_initial_story(prompt, selected_prompts=None, generate_companions=False, use_default_world=False):
    """
    Mock get_initial_story function that returns predefined content.
    """
    client = get_client()
    logging_util.info("Mock Gemini Service: get_initial_story called")
    
    # Use the imported classes
    
    narrative_text = """Sir Kaelan the Adamant awakens in the dimly lit Ancient Tavern, the scent of ale and wood smoke filling his nostrils. The mysterious key from his dungeon escape weighs heavy in his pocket. Gareth the innkeeper approaches with a knowing smile.

"Ah, Sir Kaelan! Word travels fast in these parts. I hear you seek the Lost Crown. Dangerous business, that. But perhaps... perhaps I can help."

Gareth leans in closer, his voice dropping to a whisper. "There's an old map in my possession. Shows the way to the Whispering Woods where the crown was last seen. But I'll need something in return..."

What do you do?"""
    
    # Create NarrativeResponse object with proper parameters
    state_updates = {
        "player": {
            "name": "Sir Kaelan the Adamant",
            "class": "Fighter",
            "level": 1,
            "hp": 10,
            "max_hp": 10,
            "conditions": []
        },
        "location": "Ancient Tavern",
        "time_of_day": "evening",
        "npcs": [
            {
                "name": "Gareth",
                "role": "Innkeeper",
                "disposition": "Friendly"
            }
        ],
        "items": [
            {
                "name": "Mysterious Key",
                "description": "An ornate key found during your dungeon escape"
            }
        ],
        "active_quests": [
            {
                "name": "Find the Lost Crown",
                "description": "Seek out the legendary Lost Crown",
                "status": "active"
            }
        ]
    }
    
    narrative_response = NarrativeResponse(
        narrative=narrative_text,
        entities_mentioned=["Sir Kaelan the Adamant", "Gareth"],
        location_confirmed="Ancient Tavern",
        turn_summary="Sir Kaelan awakens in the Ancient Tavern and speaks with Gareth about the Lost Crown.",
        state_updates=state_updates,
        session_header="Mock Campaign Session",
        planning_block="This is a mock planning block for testing.",
        dice_rolls=[],
        resources="Mock resources: 10 gold pieces"
    )
    
    # Create GeminiResponse object
    response = GeminiResponse(
        narrative_text=narrative_text,
        structured_response=narrative_response
    )
    
    return response

def continue_story(user_input, mode, story_context, current_game_state, selected_prompts=None, use_default_world=False):
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
        state_updates = {
            "combat_active": True,
            "enemy_hp": 15
        }
    elif "talk" in user_input.lower() or "speak" in user_input.lower():
        narrative_text = """You approach cautiously and attempt to engage in conversation. The figure turns to face you, revealing weathered features and wise eyes.
        
"Greetings, traveler," they say. "I've been expecting you."""
        state_updates = {
            "npcs": [
                {
                    "name": "Mysterious Figure",
                    "disposition": "Neutral"
                }
            ]
        }
    else:
        narrative_text = f"""You {user_input}.
        
The world responds to your actions, and new possibilities unfold before you."""
        state_updates = {}
    
    # Create response objects
    narrative_response = NarrativeResponse(
        narrative=narrative_text,
        entities_mentioned=[],
        location_confirmed="Unknown",
        turn_summary="Action taken.",
        state_updates=state_updates
    )
    response = GeminiResponse(
        narrative_text=narrative_text,
        structured_response=narrative_response
    )
    
    return response

# Export the same functions as the real service  
__all__ = ['get_client', 'generate_content', 'get_initial_story', 'continue_story']