#!/usr/bin/env python3
"""
Mock Gemini Service for UI Testing
Provides realistic responses without API costs
"""

import json
import os
import random
import time


class MockGeminiService:
    """Mock service that replaces real Gemini API calls with pre-captured responses"""

    def __init__(self):
        self.mock_data_dir = os.path.dirname(__file__)
        self.load_mock_responses()

    def load_mock_responses(self):
        """Load all mock response files"""
        try:
            # Load Dragon Knight responses
            with open(
                os.path.join(self.mock_data_dir, "dragon_knight_responses.json")
            ) as f:
                self.dragon_knight_data = json.load(f)

            # Add fallback responses if files don't exist
            self.fallback_responses = {
                "dragon_knight": {
                    "narrative_text": "Welcome, Ser Arion, to your first mission in service of the Celestial Imperium! The weight of your oath as a Dragon Knight settles upon your shoulders as Commander Vaelthys briefs you on reports of strange disturbances in the border village of Millhaven...",
                    "session_header": "Year 11 New Peace, Day 1 | Imperial Training Grounds | Lvl 1 Paladin | HP: 10/10 | XP: 0/300",
                    "planning_block": {
                        "thinking": "Introducing Ser Arion to his first real mission, establishing the world of the Celestial Imperium and the moral complexity he'll face.",
                        "context": "Young knight beginning his service in a world where order comes through tyranny.",
                    },
                },
                "custom": {
                    "narrative_text": "Your adventure begins! Based on your character and setting, let me craft an opening that brings your unique vision to life...",
                    "session_header": "Session 1, Turn 1 | Starting Location | Lvl 1 | HP: 10/10 | XP: 0/300",
                    "planning_block": {
                        "thinking": "Adapting to the player's custom character and world choices to create an engaging opening.",
                        "context": "Custom campaign beginning with player-specified elements.",
                    },
                },
            }

        except Exception as e:
            print(f"Warning: Could not load mock responses: {e}")
            self.dragon_knight_data = {}

    def get_initial_story(self, campaign_data):
        """
        Mock the gemini_service.get_initial_story() function
        Returns a realistic response based on campaign type
        """
        campaign_type = campaign_data.get("campaign_type", "custom")
        character = campaign_data.get("character", "")
        setting = campaign_data.get("setting", "")

        # Simulate realistic delay
        time.sleep(random.uniform(0.5, 1.5))

        if campaign_type == "dragon-knight":
            return self._get_dragon_knight_response(character, setting)
        return self._get_custom_response(character, setting)

    def _get_dragon_knight_response(self, character, setting):
        """Generate Dragon Knight campaign response"""
        # Use mock data if available, otherwise fallback
        if "initial_story_response" in self.dragon_knight_data:
            base_response = self.dragon_knight_data["initial_story_response"]

            # Customize with any character/setting modifications
            narrative = base_response["text"]
            if character and character != "Ser Arion":
                narrative = narrative.replace("Ser Arion", character)

            return {
                "success": True,
                "response": narrative,
                "structured_response": base_response.get("structured_response", {}),
                "user_scene_number": 1,
                "session_header": base_response.get("structured_response", {}).get(
                    "session_header", ""
                ),
                "planning_block": base_response.get("structured_response", {}).get(
                    "planning_block", {}
                ),
                "dice_rolls": base_response.get("structured_response", {}).get(
                    "dice_rolls", []
                ),
                "resource_updates": base_response.get("structured_response", {}).get(
                    "resource_updates", {}
                ),
            }
        # Fallback Dragon Knight response
        fallback = self.fallback_responses["dragon_knight"]
        return {
            "success": True,
            "response": fallback["narrative_text"],
            "user_scene_number": 1,
            "session_header": fallback["session_header"],
            "planning_block": fallback["planning_block"],
        }

    def _get_custom_response(self, character, setting):
        """Generate custom campaign response"""
        char_text = character if character else "a brave adventurer"
        setting_text = setting if setting else "a mysterious realm"

        custom_narrative = f"""Welcome to your adventure, {char_text}!

You find yourself in {setting_text}, where destiny awaits. The path ahead is uncertain, but your courage and determination will guide you through whatever challenges lie ahead.

What would you like to do first in this new world?"""

        return {
            "success": True,
            "response": custom_narrative,
            "user_scene_number": 1,
            "session_header": f"Session 1, Turn 1 | {setting_text} | Lvl 1 | HP: 10/10 | XP: 0/300",
            "planning_block": {
                "thinking": f"Custom campaign opening for {char_text} in {setting_text}",
                "context": "Player-defined custom adventure beginning",
            },
        }

    def continue_story(self, user_input, campaign_data, game_state):
        """Mock story continuation for interactions"""
        time.sleep(random.uniform(1.0, 2.0))  # Simulate API delay

        # Simple response based on input
        responses = [
            "Your action has consequences as the story unfolds...",
            "The world reacts to your decision in unexpected ways...",
            "As you proceed, new challenges and opportunities arise...",
            "Your journey takes an interesting turn as...",
        ]

        narrative = random.choice(responses)

        return {
            "success": True,
            "response": narrative,
            "user_scene_number": game_state.get("scene_number", 1) + 1,
            "session_header": f"Session 1, Turn {game_state.get('turn_number', 1) + 1}",
            "planning_block": {
                "thinking": f"Responding to player action: {user_input}",
                "context": "Continuing the adventure based on player choices",
            },
        }


# Monkey patch function to replace real Gemini calls
def mock_gemini_get_initial_story(
    prompt,
    selected_prompts=None,
    custom_options=None,
    generate_companions=False,
    use_default_world=False,
    **kwargs,
):
    """Mock function to replace gemini_service.get_initial_story"""

    # Extract campaign data from parameters
    campaign_data = {
        "campaign_type": "custom",  # Default
        "character": "",
        "setting": "",
    }

    # Parse prompt to extract character/setting or detect Dragon Knight
    if isinstance(prompt, str):
        if "Ser Arion" in prompt and "Celestial Imperium" in prompt:
            # This is the Dragon Knight campaign
            campaign_data["campaign_type"] = "dragon-knight"
            campaign_data["character"] = "Ser Arion"
            campaign_data["setting"] = "World of Assiah"
        elif prompt.startswith("Character:"):
            # Parse character/setting format
            lines = prompt.split("\n")
            for line in lines:
                if line.startswith("Character:"):
                    campaign_data["character"] = line.replace("Character:", "").strip()
                elif line.startswith("Setting:"):
                    campaign_data["setting"] = line.replace("Setting:", "").strip()

    # Use mock service
    mock_service = MockGeminiService()
    return mock_service.get_initial_story(campaign_data)


# Export for easy import
__all__ = ["MockGeminiService", "mock_gemini_get_initial_story"]
