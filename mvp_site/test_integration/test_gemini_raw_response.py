"""
Test to capture and examine the raw Gemini API response.
"""

import json
import os
import sys
import traceback
import unittest

import gemini_service
from game_state import GameState

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from integration_test_lib import setup_integration_test_environment

# Handle missing dependencies gracefully
try:
    DEPS_AVAILABLE = True
except ImportError as e:
    print(f"Integration test dependencies not available: {e}")
    DEPS_AVAILABLE = False


@unittest.skipIf(not DEPS_AVAILABLE, "Dependencies not available")
class TestGeminiRawResponse(unittest.TestCase):
    """Test to see the actual raw response from Gemini API."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_setup = setup_integration_test_environment(project_root)

        # Ensure we have API keys
        if not os.environ.get("GEMINI_API_KEY"):
            raise unittest.SkipTest("GEMINI_API_KEY not found")

    def test_raw_gemini_response(self):
        """Test what Gemini actually returns when called directly."""
        print("\n=== Testing Raw Gemini Response ===")

        # Create a simple story context
        story_context = [
            {"text": "You stand in a forest clearing.", "actor": "user", "mode": "god"}
        ]

        # Create a basic game state
        game_state = GameState()
        game_state.debug_mode = True  # Enable debug mode

        # Call Gemini directly
        try:
            response = gemini_service.continue_story(
                user_input="I look around the clearing.",
                mode="character",
                story_context=story_context,
                current_game_state=game_state,
                selected_prompts=["narrative"],
                use_default_world=False,
            )

            print(f"\nResponse type: {type(response)}")
            print(f"Response attributes: {dir(response)}")

            if hasattr(response, "narrative_text"):
                print(f"\nNarrative text preview: {response.narrative_text[:200]}...")

            if hasattr(response, "_raw_narrative_text"):
                print(
                    f"\nRaw narrative text preview: {response._raw_narrative_text[:200]}..."
                )

            if hasattr(response, "structured_response"):
                print(
                    f"\nHas structured response: {response.structured_response is not None}"
                )
                if response.structured_response:
                    print(
                        f"Structured response type: {type(response.structured_response)}"
                    )
                    if hasattr(response.structured_response, "to_dict"):
                        print(
                            f"Structured data: {response.structured_response.to_dict()}"
                        )

            if hasattr(response, "debug_info"):
                print(f"\nDebug info: {response.debug_info}")

            # Try to check if the original response was JSON
            if hasattr(response, "provider"):
                print(f"\nProvider: {response.provider}")

        except Exception as e:
            print(f"\nError calling Gemini: {e}")

            traceback.print_exc()

    def test_raw_api_call(self):
        """Test the raw API call to see exact response format."""
        print("\n=== Testing Raw API Call ===")

        # Try to call the lower level API directly
        try:
            # Build a simple prompt
            prompt = """You are a game master. The player says: "I look around."

Respond in this EXACT JSON format:
{
    "narrative": "Your story response here",
    "entities_mentioned": [],
    "location_confirmed": "Forest Clearing",
    "state_updates": {},
    "debug_info": {
        "dm_notes": ["Your DM thoughts"],
        "dice_rolls": [],
        "resources": "HD: 3/3",
        "state_rationale": "No state changes"
    }
}"""

            # Try to call the API directly
            model_name = "gemini-1.5-flash"
            response = gemini_service._call_gemini_api([prompt], model_name)

            print(f"\nRaw API response type: {type(response)}")
            print(f"\nRaw API response: {response[:500]}...")

            # Check if it's JSON
            try:
                parsed = json.loads(response)
                print("\n✅ Raw response is valid JSON!")
                print(f"JSON keys: {list(parsed.keys())}")
            except:
                print("\n❌ Raw response is NOT JSON")

        except Exception as e:
            print(f"\nError with raw API call: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
