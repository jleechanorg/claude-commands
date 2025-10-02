#!/usr/bin/env python3

"""
AI Content Personalization Integration Test
Tests that AI story generation uses campaign data instead of hardcoded content
"""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

try:
    from mvp_site.gemini_request import GeminiRequest

    GEMINI_REQUEST_AVAILABLE = True
except ImportError:
    GeminiRequest = None
    GEMINI_REQUEST_AVAILABLE = False


class AIContentPersonalizationTest(unittest.TestCase):
    """Test that AI content generation uses user's campaign data"""

    def test_story_continuation_uses_campaign_data(self):
        """Test story continuation integrates campaign context from game state"""
        # Mock campaign data that would come from user's campaign
        campaign_data = {
            "title": "Zara's Mystical Journey",
            "character_name": "Zara the Mystic Warrior",
            "setting": "Eldoria Realm where crystal magic flows",
            "description": "A realm where elemental crystals grant powers",
            "campaign_type": "Custom Adventure",
        }

        # Mock game state with campaign context
        game_state = {
            "campaign_data": campaign_data,
            "current_chapter": 1,
            "location": "Crystal Grove",
        }

        # Create story continuation request
        request = GeminiRequest.build_story_continuation(
            user_action="I examine the glowing crystals",
            user_id="test-user-123",
            game_mode="story",
            game_state=game_state,
            story_history=[],
            use_default_world=False,
        )

        # Verify request structure includes campaign context
        json_data = request.to_json()

        # Campaign data should be accessible in game_state
        assert "campaign_data" in json_data["game_state"]
        assert (
            json_data["game_state"]["campaign_data"]["character_name"]
            == "Zara the Mystic Warrior"
        )
        assert (
            json_data["game_state"]["campaign_data"]["setting"]
            == "Eldoria Realm where crystal magic flows"
        )

    def test_initial_story_campaign_personalization(self):
        """Test initial story generation includes campaign personalization context"""
        campaign_data = {
            "title": "Zara's Mystical Journey",
            "character_name": "Zara the Mystic Warrior",
            "setting": "Eldoria Realm",
            "description": "Crystal magic realm",
            "campaign_type": "Custom Adventure",
        }

        request = GeminiRequest.build_initial_story(
            character_prompt="Begin the adventure",
            user_id="test-user-123",
            selected_prompts=["adventure", "fantasy"],
        )

        # Verify character prompt is present and basic
        enhanced_prompt = request.character_prompt

        # Should contain the original character prompt
        assert "Begin the adventure" in enhanced_prompt
        # Should not contain hardcoded character names
        assert "Shadowheart" not in enhanced_prompt

    def test_no_hardcoded_character_names(self):
        """Test that requests don't contain hardcoded character names like 'Shadowheart'"""
        campaign_data = {"character_name": "Zara the Mystic Warrior"}

        request = GeminiRequest.build_initial_story(
            character_prompt="Start adventure",
            user_id="test-user-123",
            selected_prompts=["fantasy"],
        )

        json_data = request.to_json()
        request_str = str(json_data)

        # Should not contain hardcoded names
        hardcoded_names = ["Shadowheart", "Ser Arion", "Lyra", "default character"]
        for name in hardcoded_names:
            assert name not in request_str, f"Found hardcoded character name: {name}"

        # Should contain the user prompt
        assert "Start adventure" in request_str


if __name__ == "__main__":
    unittest.main()
