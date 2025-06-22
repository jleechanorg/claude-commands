import unittest
import os
import uuid

# This test file will only define and run tests if all dependencies are met.

# Hardcoded paths for credentials, as requested.
GEMINI_API_KEY_PATH = "/home/jleechan/.gemini_api_key_secret"
FIREBASE_KEY_PATH = "/home/jleechan/projects/worldarchitect.ai/serviceAccountKey.json"
TEST_USER_ID = "integration_test_user_standalone"

# --- Conditional Test Definition ---
# Check for all requirements before defining the test class.
# This is the most robust way to ensure the file doesn't cause errors
# in environments where dependencies are not met.
ALL_REQUIREMENTS_MET = (
    os.path.exists(FIREBASE_KEY_PATH) and
    os.path.exists(GEMINI_API_KEY_PATH)
)

if ALL_REQUIREMENTS_MET:
    # Only import heavy dependencies if we are actually going to run the test.
    from unittest.mock import patch
    import firebase_admin
    from firebase_admin import credentials
    import gemini_service
    import firestore_service
    from game_state import GameState

    class TestTruncationIntegration(unittest.TestCase):
        
        @classmethod
        def setUpClass(cls):
            """Read the API key and initialize Firebase for all tests."""
            with open(GEMINI_API_KEY_PATH, 'r') as f:
                cls.gemini_api_key = f.read().strip()
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(FIREBASE_KEY_PATH)
                firebase_admin.initialize_app(cred)

        def setUp(self):
            """Set up a real campaign and set the Gemini API key for the test."""
            # FOR TESTING: Clear any cached client to ensure the new API key is used.
            gemini_service._clear_client() 
            
            os.environ['GEMINI_API_KEY'] = self.gemini_api_key
            self.user_id = TEST_USER_ID
            
            self.initial_game_state = GameState(
                player_character_data={"name": "Tester"},
                world_data={"current_location_name": "Test Zone"},
                custom_campaign_state={"core_memories": []}
            )
            
            self.campaign_id = firestore_service.create_campaign(
                user_id=self.user_id,
                title=f"Truncation Test Campaign - {uuid.uuid4()}",
                initial_prompt="This is the start of a very long story.",
                opening_story="The story begins.",
                initial_game_state=self.initial_game_state.to_dict()
            )
            print(f"Created campaign {self.campaign_id} for test.")

        def tearDown(self):
            """Warning about cleanup and unsetting the API key."""
            del os.environ['GEMINI_API_KEY']
            print(f"WARNING: Test complete for campaign: {self.campaign_id}.")
            print("A 'delete_campaign' function would be needed for cleanup.")

        def test_long_history_truncation_and_core_memory_generation(self):
            """Tests the full pipeline using a real campaign."""
            print("Populating long story history...")
            for i in range(100):
                firestore_service.add_story_entry(
                    user_id=self.user_id, campaign_id=self.campaign_id,
                    actor="user" if i % 2 == 0 else "gemini",
                    text=f"This is a sentence for turn number {i}."
                )
            
            _, story_context = firestore_service.get_campaign_by_id(self.user_id, self.campaign_id)
            current_game_state = firestore_service.get_campaign_game_state(self.user_id, self.campaign_id)
            
            self.assertIsInstance(current_game_state, GameState)

            user_input = "After that long journey, I sit and reflect on the key moments that brought me here."

            with patch('gemini_service.TURNS_TO_KEEP_AT_START', 20), \
                 patch('gemini_service.TURNS_TO_KEEP_AT_END', 30):
                
                print("Calling Gemini API...")
                self.assertIsNotNone(story_context)
                self.assertIsNotNone(current_game_state)
                
                llm_response_text = gemini_service.continue_story(
                    user_input=user_input, mode="character",
                    story_context=story_context,
                    current_game_state=current_game_state,
                    selected_prompts=['narrative']
                )

                print(f"\n--- LLM Response ---\n{llm_response_text}\n--------------------\n")
                state_changes = gemini_service.parse_llm_response_for_state_changes(llm_response_text)
                print(f"\n--- Parsed State Changes ---\n{state_changes}\n--------------------------\n")

                self.assertIn('custom_campaign_state.core_memories', state_changes)
                new_memories = state_changes.get('custom_campaign_state.core_memories', [])
                self.assertIsInstance(new_memories, list)
                self.assertGreater(len(new_memories), 0)
                self.assertIsInstance(new_memories[0], str)

# This check ensures that the test runner can always execute the file,
# even if no tests are defined because requirements aren't met.
if __name__ == '__main__':
    unittest.main() 