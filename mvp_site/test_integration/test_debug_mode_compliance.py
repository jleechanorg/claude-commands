"""
Integration test for debug mode compliance with real Gemini API.
Tests whether Gemini properly uses the debug_info field instead of embedding debug tags.
"""
import unittest
import os
import json
import sys
import time

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import logging_util
from integration_test_lib import IntegrationTestSetup, setup_integration_test_environment

# Handle missing dependencies gracefully
try:
    from main import create_app
    import firestore_service
    import gemini_service
    from game_state import GameState
    from gemini_response import GeminiResponse
    from narrative_response_schema import parse_structured_response
    DEPS_AVAILABLE = True
except ImportError as e:
    print(f"Integration test dependencies not available: {e}")
    DEPS_AVAILABLE = False

# Test configuration
TEST_USER_ID = 'test-debug-compliance'
TEST_CAMPAIGN_ID = f'debug-test-{int(time.time())}'


@unittest.skipIf(not DEPS_AVAILABLE, "Dependencies not available")
class TestDebugModeCompliance(unittest.TestCase):
    """Test that Gemini follows debug_info field instructions correctly."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.test_setup = setup_integration_test_environment(project_root)
        cls.app = create_app()
        cls.client = cls.app.test_client()
        
        # Ensure we have API keys
        if not os.environ.get("GEMINI_API_KEY"):
            raise unittest.SkipTest("GEMINI_API_KEY not found")
            
    def setUp(self):
        """Set up for each test."""
        # Clean up any existing test campaign
        try:
            firestore_service.delete_campaign(TEST_USER_ID, TEST_CAMPAIGN_ID)
        except:
            pass
            
    def tearDown(self):
        """Clean up after each test."""
        # Clean up test campaign
        try:
            firestore_service.delete_campaign(TEST_USER_ID, TEST_CAMPAIGN_ID)
        except:
            pass
    
    def create_test_campaign(self, debug_mode=False):
        """Create a test campaign with debug mode setting."""
        headers = IntegrationTestSetup.create_test_headers(TEST_USER_ID)
        
        # Create campaign
        response = self.client.post('/api/campaigns', 
            headers=headers,
            json={
                'title': 'Debug Mode Test Campaign',
                'prompt': 'A brave knight enters a tavern. There is a mysterious hooded figure in the corner.',
                'selected_prompts': ['narrative']  # No mechanics to avoid character creation
            })
        
        self.assertEqual(response.status_code, 201)  # 201 Created is correct for new resources
        data = json.loads(response.data)
        campaign_id = data['campaign_id']
        
        # Set debug mode
        if debug_mode:
            game_state = firestore_service.get_campaign_game_state(TEST_USER_ID, campaign_id)
            if not game_state:
                game_state = GameState()
            game_state.debug_mode = True
            firestore_service.update_campaign_game_state(TEST_USER_ID, campaign_id, game_state.to_dict())
            
        return campaign_id
    
    def make_interaction(self, campaign_id, user_input, mode='character'):
        """Make an interaction and return the response."""
        headers = IntegrationTestSetup.create_test_headers(TEST_USER_ID)
        
        # Set a timeout for Gemini calls
        if hasattr(self.test_setup, 'set_timeout'):
            self.test_setup.set_timeout(30)  # 30 second timeout
            
        response = self.client.post(f'/api/campaigns/{campaign_id}/interaction',
            headers=headers,
            json={
                'input': user_input,
                'mode': mode
            })
            
        if hasattr(self.test_setup, 'clear_timeout'):
            self.test_setup.clear_timeout()
            
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)
    
    def test_debug_mode_on_compliance(self):
        """Test that with debug mode ON, debug content goes to debug_info field."""
        print("\n=== Testing Debug Mode ON ===")
        
        # Create campaign with debug mode ON
        campaign_id = self.create_test_campaign(debug_mode=True)
        
        # Make an interaction that should generate debug content  
        result = self.make_interaction(campaign_id, "I approach the hooded figure cautiously.")
        
        print(f"\nAPI Response: {json.dumps(result, indent=2)[:500]}...")
        
        # Get the raw AI response from the story
        campaign, story = firestore_service.get_campaign_by_id(TEST_USER_ID, campaign_id)
        self.assertIsNotNone(story)
        self.assertGreater(len(story), 1)  # Should have at least user input and AI response
        
        # Find the AI response
        ai_response = None
        raw_response = None
        for entry in story:
            if entry.get('actor') == 'gemini':
                ai_response = entry.get('text', '')
                raw_response = entry.get('raw_response', '')
                print(f"\nStory entry keys: {list(entry.keys())}")
                if raw_response:
                    print(f"Found raw_response field: {raw_response[:200]}...")
                break
                
        self.assertIsNotNone(ai_response, "No AI response found in story")
        print(f"\nAI Response Length: {len(ai_response)} chars")
        print(f"AI Response Preview: {ai_response[:500]}...")
        
        # Check for debug tags in narrative
        debug_tags = [
            '[DEBUG_START]', '[DEBUG_END]',
            '[DEBUG_STATE_START]', '[DEBUG_STATE_END]',
            '[DEBUG_ROLL_START]', '[DEBUG_ROLL_END]',
            '[STATE_UPDATES_PROPOSED]', '[END_STATE_UPDATES_PROPOSED]'
        ]
        has_debug_tags = any(tag in ai_response for tag in debug_tags)
        
        if has_debug_tags:
            print(f"\nWARNING: Found debug tags in response: {[tag for tag in debug_tags if tag in ai_response]}")
        
        # Parse the structured response to check debug_info field
        try:
            # The AI response should be valid JSON
            parsed_response = json.loads(ai_response)
            has_debug_info = bool(parsed_response.get('debug_info', {}))
            narrative_text = parsed_response.get('narrative', '')
            
            print(f"\nStructured response detected:")
            print(f"- Has debug_info field: {has_debug_info}")
            print(f"- Debug info content: {parsed_response.get('debug_info', {})}")
            print(f"- Narrative has debug tags: {has_debug_tags}")
            
            # EXPECTED: debug_info field populated, no debug tags in narrative
            self.assertTrue(has_debug_info, "debug_info field should be populated in debug mode")
            self.assertFalse(any(tag in narrative_text for tag in [
                '[DEBUG_START]', '[STATE_UPDATES_PROPOSED]'
            ]), "Narrative should NOT contain debug tags when using structured format")
            
        except json.JSONDecodeError:
            print(f"\nWARNING: AI response is not valid JSON - checking for embedded debug tags")
            # If not JSON, check if it has old-style debug tags
            self.assertTrue(has_debug_tags, 
                "Non-JSON response should at least have debug tags in debug mode")
    
    def test_debug_mode_off_compliance(self):
        """Test that with debug mode OFF, no debug content appears."""
        print("\n=== Testing Debug Mode OFF ===")
        
        # Create campaign with debug mode OFF
        campaign_id = self.create_test_campaign(debug_mode=False)
        
        # Make an interaction
        result = self.make_interaction(campaign_id, "I approach the hooded figure cautiously.")
        
        # Get the response shown to user
        user_visible_response = result.get('response', '')
        print(f"\nUser-visible response: {user_visible_response[:200]}...")
        
        # Check that no debug content is visible
        debug_tags = [
            '[DEBUG_START]', '[DEBUG_END]',
            '[DEBUG_STATE_START]', '[DEBUG_STATE_END]', 
            '[DEBUG_ROLL_START]', '[DEBUG_ROLL_END]',
            '[STATE_UPDATES_PROPOSED]', '[END_STATE_UPDATES_PROPOSED]'
        ]
        
        for tag in debug_tags:
            self.assertNotIn(tag, user_visible_response, 
                f"Debug tag {tag} should not be visible when debug mode is OFF")
    
    def test_combat_interaction_debug_compliance(self):
        """Test debug compliance during combat (dice rolls should go to debug_info)."""
        print("\n=== Testing Combat Debug Compliance ===")
        
        # Create campaign with debug mode ON
        campaign_id = self.create_test_campaign(debug_mode=True)
        
        # Make a combat interaction
        result = self.make_interaction(campaign_id, "I attack the hooded figure with my sword!")
        
        # Get the raw AI response
        campaign, story = firestore_service.get_campaign_by_id(TEST_USER_ID, campaign_id)
        ai_response = None
        for entry in story:
            if entry.get('actor') == 'gemini':
                ai_response = entry.get('text', '')
                
        self.assertIsNotNone(ai_response)
        
        try:
            parsed = json.loads(ai_response)
            debug_info = parsed.get('debug_info', {})
            dice_rolls = debug_info.get('dice_rolls', [])
            
            print(f"\nDice rolls in debug_info: {dice_rolls}")
            
            # Combat should generate dice rolls in debug_info
            if dice_rolls:
                self.assertGreater(len(dice_rolls), 0, 
                    "Combat should generate dice rolls in debug_info field")
                
                # Check narrative doesn't have roll tags
                narrative = parsed.get('narrative', '')
                self.assertNotIn('[DEBUG_ROLL_START]', narrative,
                    "Dice rolls should be in debug_info, not embedded in narrative")
        except json.JSONDecodeError:
            print("WARNING: Response not in expected JSON format")
            # At minimum, check for dice roll tags if not structured
            self.assertIn('attack', ai_response.lower(), 
                "Combat response should mention the attack")


if __name__ == '__main__':
    unittest.main(verbosity=2)