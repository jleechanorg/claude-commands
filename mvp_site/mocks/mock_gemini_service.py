"""
Mock Gemini API service for function testing.
Provides realistic AI responses without making actual API calls.
"""
import json
import re
from datetime import datetime
from typing import Any, Dict, List

from .data_fixtures import SAMPLE_AI_RESPONSES, SAMPLE_STATE_UPDATES
from .structured_fields_fixtures import FULL_STRUCTURED_RESPONSE, GOD_MODE_RESPONSE

try:
    pass  # Import already handled above
except ImportError:
    # Fallback if fixtures not available
    FULL_STRUCTURED_RESPONSE = None
    GOD_MODE_RESPONSE = None


class MockGeminiResponse:
    """Mock response object that mimics the real Gemini API response."""

    def __init__(self, text: str):
        self.text = text

    def __str__(self):
        return self.text


class MockGeminiClient:
    """
    Mock Gemini client that simulates AI responses based on prompt patterns.
    Designed to behave like the real Gemini API for testing purposes.
    """

    def __init__(self):
        self.call_count = 0
        self.last_prompt = None
        self.response_mode = "normal"  # Can be set to trigger specific scenarios

        # Response patterns based on prompt content
        self.response_patterns = {
            "initial_story": self._generate_initial_story,
            "continue_story": self._generate_continue_story,
            "hp_discrepancy": self._generate_hp_discrepancy,
            "location_mismatch": self._generate_location_mismatch,
            "mission_completion": self._generate_mission_completion,
            "validation_prompt": self._generate_validation_response
        }

    def generate_content(self, prompt_parts, model: str = None) -> MockGeminiResponse:
        """
        Generate content based on prompt patterns.

        Args:
            prompt_parts: List of prompt strings or single prompt string
            model: Model name (ignored in mock)

        Returns:
            MockGeminiResponse with appropriate text
        """
        self.call_count += 1

        # Handle both list and string inputs
        if isinstance(prompt_parts, str):
            full_prompt = prompt_parts
        else:
            full_prompt = "\n".join(str(part) for part in prompt_parts)

        self.last_prompt = full_prompt

        # Determine response type based on prompt content and mode
        response_type = self._determine_response_type(full_prompt)
        response_text = self.response_patterns[response_type](full_prompt)

        return MockGeminiResponse(response_text)

    def _determine_response_type(self, prompt: str) -> str:
        """Determine what type of response to generate based on prompt content."""
        prompt_lower = prompt.lower()

        # Check for forced response mode first
        if self.response_mode == "hp_discrepancy":
            return "hp_discrepancy"
        elif self.response_mode == "location_mismatch":
            return "location_mismatch"
        elif self.response_mode == "mission_completion":
            return "mission_completion"

        # Pattern matching for different scenarios
        if "start a story" in prompt_lower or "initial story" in prompt_lower:
            return "initial_story"
        elif "validation" in prompt_lower and "inconsistencies" in prompt_lower:
            return "validation_prompt"
        elif "unconscious" in prompt_lower or "hp" in prompt_lower:
            return "hp_discrepancy"
        elif "forest" in prompt_lower and "tavern" in prompt_lower:
            return "location_mismatch"
        elif "dragon" in prompt_lower and "treasure" in prompt_lower:
            return "mission_completion"
        else:
            return "continue_story"

    def _generate_initial_story(self, prompt: str) -> str:
        """Generate an initial story response."""
        # Return structured JSON response for campaign creation
        initial_response = {
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
        return json.dumps(initial_response, indent=2)

    def _generate_continue_story(self, prompt: str) -> str:
        """Generate a normal story continuation."""
        # Check if we need to return structured JSON response
        if FULL_STRUCTURED_RESPONSE and ("json" in prompt.lower() or "structured" in prompt.lower()):
            # Check for god mode
            if "god mode:" in prompt.lower() or "god:" in prompt.lower():
                return json.dumps(GOD_MODE_RESPONSE, indent=2)
            else:
                return json.dumps(FULL_STRUCTURED_RESPONSE, indent=2)
        return SAMPLE_AI_RESPONSES["normal_response"]

    def _generate_hp_discrepancy(self, prompt: str) -> str:
        """Generate a response that creates HP discrepancy."""
        return SAMPLE_AI_RESPONSES["hp_discrepancy_response"]

    def _generate_location_mismatch(self, prompt: str) -> str:
        """Generate a response that creates location mismatch."""
        return SAMPLE_AI_RESPONSES["location_mismatch_response"]

    def _generate_mission_completion(self, prompt: str) -> str:
        """Generate a response indicating mission completion."""
        return SAMPLE_AI_RESPONSES["mission_completion_response"]

    def _generate_validation_response(self, prompt: str) -> str:
        """Generate a response that addresses validation concerns."""
        return """Sir Kaelan takes a moment to assess his situation carefully. He checks his wounds - though battered, he remains conscious and able to continue. The tavern around him feels familiar and safe.

[STATE_UPDATES_PROPOSED]
{
    "player_character_data": {
        "hp_current": 85
    },
    "world_data": {
        "current_location_name": "Ancient Tavern"
    }
}
[END_STATE_UPDATES_PROPOSED]"""

    def set_response_mode(self, mode: str):
        """Set the response mode to trigger specific scenarios."""
        self.response_mode = mode

    def reset(self):
        """Reset the mock to initial state."""
        self.call_count = 0
        self.last_prompt = None
        self.response_mode = "normal"


# Global mock instance for easy testing
mock_gemini_client = MockGeminiClient()


def get_mock_client():
    """Get the global mock client instance."""
    return mock_gemini_client


def parse_state_updates_from_response(response_text: str) -> Dict[str, Any]:
    """
    Parse state updates from a mock AI response.
    Mimics the real gemini_service.parse_llm_response_for_state_changes function.
    """
    matches = re.findall(r'\[STATE_UPDATES_PROPOSED\](.*?)\[END_STATE_UPDATES_PROPOSED\]',
                        response_text, re.DOTALL)

    if not matches:
        return {}

    # Take the last valid JSON block
    for json_string in reversed(matches):
        json_string = json_string.strip()

        # Handle optional markdown code block
        if json_string.startswith("```json"):
            json_string = json_string[7:]
        if json_string.endswith("```"):
            json_string = json_string[:-3]

        json_string = json_string.strip()

        try:
            proposed_changes = json.loads(json_string)
            if isinstance(proposed_changes, dict):
                return proposed_changes
        except json.JSONDecodeError:
            continue

    return {}
