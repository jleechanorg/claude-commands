import atexit
import json
import os
import subprocess
import sys
import unittest

# Add the project root to the Python path to allow for imports
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, project_root)

# Add current directory for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import create_app function
from main import create_app

# Handle missing dependencies gracefully
try:
    from integration_test_lib import (
        IntegrationTestSetup,
        setup_integration_test_environment,
    )

    # Set up the integration test environment
    test_setup = setup_integration_test_environment(project_root)
    temp_prompts_dir = test_setup.create_test_prompts_directory()
    DEPS_AVAILABLE = True
except ImportError as e:
    print(f"Integration test dependencies not available: {e}")
    DEPS_AVAILABLE = False

# Initialize test configuration only if dependencies are available
if DEPS_AVAILABLE:
    # Temporarily change working directory to temp dir so imports find test prompts
    original_cwd = os.getcwd()
    os.chdir(temp_prompts_dir)

    # Get test configuration from the shared library
    TEST_MODEL_OVERRIDE = IntegrationTestSetup.TEST_MODEL_OVERRIDE
    # Configuration for test prompts - represents all checkboxes being selected
    TEST_SELECTED_PROMPTS = ["narrative", "mechanics"]  # All user-selectable prompts
    TEST_CUSTOM_OPTIONS = ["companions", "defaultWorld"]  # Additional test options
    USE_TIMEOUT = IntegrationTestSetup.USE_TIMEOUT

    # Mock system instructions
    mock_instructions = IntegrationTestSetup.mock_system_instructions()
    MOCK_INTEGRATION_NARRATIVE = mock_instructions["narrative"]
    MOCK_INTEGRATION_MECHANICS = mock_instructions["mechanics"]
    MOCK_INTEGRATION_CALIBRATION = mock_instructions["calibration"]

    # Register cleanup on exit

    atexit.register(lambda: test_setup.cleanup())


def create_mock_gemini_response(
    narrative="Test response", planning_block=None, state_updates=None
):
    """Create a mock response that mimics Gemini API structure."""
    response_data = {"narrative": narrative}

    if planning_block:
        response_data["planning_block"] = planning_block

    if state_updates:
        response_data["state_updates"] = state_updates

    # Create a mock response object
    mock_response = type("MockResponse", (), {})()
    mock_response.text = json.dumps(response_data)
    return mock_response


def run_god_command(test_instance, action, command_string=None):
    """Shared helper function to run god-command script and return output."""
    # Use sys.executable to ensure we're using the python from the venv
    python_executable = sys.executable
    script_path = os.path.join(project_root, "main.py")
    base_command = [
        python_executable,
        script_path,
        "god-command",
        action,
        "--campaign_id",
        test_instance.campaign_id,
        "--user_id",
        test_instance.user_id,
    ]
    if command_string:
        base_command.extend(["--command_string", command_string])

    # Set TESTING environment variable
    env = os.environ.copy()
    env["TESTING"] = "true"

    # Run the god-command from the original directory
    result = subprocess.run(
        base_command,
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )
    assert result.returncode == 0, f"god-command {action} failed: {result.stderr}"

    # The god-command logs JSON to stderr (via logging_util.info), not stdout
    if action == "ask":
        # Look for JSON in stderr output
        output = result.stderr
        # Find the line that starts with "Current game state:"
        lines = output.split("\n")
        json_lines = []
        capturing = False
        for line in lines:
            if "Current game state:" in line:
                capturing = True
                continue
            if capturing:
                json_lines.append(line)

        # Join the JSON lines and parse
        json_text = "\n".join(json_lines).strip()
        if json_text:
            return json_text
        # Fallback: try to find JSON block directly
        json_start = output.find("{")
        json_end = output.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            return output[json_start:json_end]
        test_instance.fail(f"No JSON found in god-command output: {output}")

    return result.stderr


class BaseCampaignIntegrationTest(unittest.TestCase):
    """Base class for campaign integration tests with shared functionality.

    Provides common test setup, teardown, and utility methods for testing
    different campaign types with real Gemini/Firebase integration.
    """

    # Override these in subclasses
    CAMPAIGN_PROMPT = ""
    CAMPAIGN_TITLE = "Test Campaign"
    USER_ID_SUFFIX = "test-user"

    @classmethod
    def setUpClass(cls):
        """Create campaign for all tests to share."""
        if not DEPS_AVAILABLE:
            return
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.user_id = f"test-{cls.USER_ID_SUFFIX}"

        # Create campaign with subclass-specific prompt
        create_response = cls.client.post(
            "/api/campaigns",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": cls.user_id,
            },
            data=json.dumps(
                {
                    "prompt": cls.CAMPAIGN_PROMPT,
                    "title": cls.CAMPAIGN_TITLE,
                    "selected_prompts": TEST_SELECTED_PROMPTS,  # ['narrative', 'mechanics'] - all checkboxes checked
                    "custom_options": TEST_CUSTOM_OPTIONS,  # Additional options for complete testing
                }
            ),
        )
        if create_response.status_code != 201:
            error_details = {
                "status_code": create_response.status_code,
                "response_text": create_response.get_data(as_text=True),
                "headers": dict(create_response.headers),
                "campaign_title": cls.CAMPAIGN_TITLE,
            }
            print(f"CAMPAIGN CREATION FAILED: {json.dumps(error_details, indent=2)}")
        assert (
            create_response.status_code == 201
        ), f"Failed to create {cls.CAMPAIGN_TITLE} - Status: {create_response.status_code}, Response: {create_response.get_data(as_text=True)}"
        create_data = create_response.get_json()
        cls.campaign_id = create_data.get("campaign_id")
        assert cls.campaign_id is not None

    @classmethod
    def tearDownClass(cls):
        """Clean up the campaign after all tests complete."""
        if not DEPS_AVAILABLE or not hasattr(cls, "campaign_id") or not cls.campaign_id:
            return
        try:
            # Note: The API doesn't provide a delete endpoint, so we leave campaigns
            # This is acceptable for test data as it helps with debugging
            pass
        except Exception as e:
            print(f"Warning: Could not clean up campaign {cls.campaign_id}: {e}")

    def setUp(self):
        """Check dependencies and use shared campaign."""
        if not DEPS_AVAILABLE:
            self.fail("CRITICAL FAILURE: Integration test dependencies missing.")

        self.app = self.__class__.app
        self.client = self.__class__.client
        self.user_id = self.__class__.user_id
        self.campaign_id = self.__class__.campaign_id

    def start_campaign_story(self):
        """Common method to start the campaign story."""
        return self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps({"input": "Begin the story.", "mode": "character"}),
        )

    def send_character_action(self, action_text):
        """Send a character mode action to the campaign."""
        return self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps({"input": action_text, "mode": "character"}),
        )

    def get_game_state(self):
        """Get the current game state as a parsed JSON object."""
        # Use the campaign API endpoint to get state
        response = self.client.get(
            f"/api/campaigns/{self.campaign_id}",
            headers={
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
        )
        assert (
            response.status_code == 200
        ), f"Failed to get campaign state: {response.get_data(as_text=True)}"
        data = response.get_json()
        # Extract game_state from the response
        return data.get("game_state", {})

    def assert_character_created(
        self, expected_name, expected_class=None, expected_alignment=None
    ):
        """Common assertion for character creation."""
        state = self.get_game_state()
        assert "player_character_data" in state
        pc_data = state["player_character_data"]

        # Basic character data
        assert (
            pc_data.get("name") == expected_name
        ), f"Character should be named {expected_name}"
        assert pc_data.get("level") == 1, "Character should be level 1"

        if expected_class:
            if isinstance(expected_class, list):
                assert (
                    pc_data.get("class") in expected_class
                ), f"Character should be one of {expected_class}"
            else:
                assert (
                    pc_data.get("class") == expected_class
                ), f"Character should be {expected_class}"

        if expected_alignment:
            assert (
                pc_data.get("alignment") == expected_alignment
            ), f"Character should be {expected_alignment}"

        # Core fields - these may vary based on campaign type
        # For now, just verify the basic required fields
        required_fields = ["name", "level", "class"]
        for field in required_fields:
            assert field in pc_data, f"Character missing required field: {field}"

        return pc_data

    def assert_combat_active(self):
        """Common assertion for combat state."""
        state = self.get_game_state()
        combat_state = state.get("combat_state", {})
        assert combat_state.get("in_combat", False), "Combat state should be active"

        combatants = combat_state.get("combatants", [])
        assert len(combatants) > 1, "Should have multiple combatants"

        return combat_state, combatants

    def assert_story_progression(self, expected_elements):
        """Check that story elements are captured in core memories."""
        state = self.get_game_state()
        custom_state = state.get("custom_campaign_state", {})
        core_memories = custom_state.get("core_memories", [])

        assert (
            len(core_memories) > 1
        ), "Should have multiple core memories tracking story progression"

        # Check for expected story elements
        memory_text = " ".join(core_memories).lower()
        found_elements = sum(
            1 for element in expected_elements if element.lower() in memory_text
        )

        assert (
            found_elements > len(expected_elements) // 2
        ), f"Expected at least half of {expected_elements} in memories. Memories: {core_memories}"

        return core_memories


class TestDefaultDragonKnightCampaign(BaseCampaignIntegrationTest):
    """Test the Dragon Knight campaign with character creation, combat, and story progression.

    Uses real system prompts with 'all checkboxes checked' configuration:
    - narrative: Story guidance and character development
    - mechanics: Combat rules and game mechanics

    This simulates the complete user experience with full system prompts.
    """

    CAMPAIGN_PROMPT = """You are Ser Arion, a 16 year old honorable knight on your first mission, sworn to protect the vast Celestial Imperium. For decades, the Empire has been ruled by the iron-willed Empress Sariel, a ruthless tyrant who uses psychic power to crush dissent. While her methods are terrifying, her reign has brought undeniable benefits: the roads are safe, trade flourishes, and the common people no longer starve or fear bandits. You are a product of this "Silent Peace," and your oath binds you to the security and prosperity it provides.

Your loyalty is now brutally tested. You have been ordered to slaughter a settlement of innocent refugees whose very existence has been deemed a threat to the Empress's perfect, unyielding order. As you wrestle with this monstrous command, a powerful, new voice enters your mind—Aurum, the Gilded King, a magnificent gold dragon long thought to be a myth. He appears as a champion of freedom, urging you to defy the Empress's "soulless cage" and fight for a world of choice and glorious struggle.

You are now caught between two powerful and morally grey forces. Do you uphold your oath and commit an atrocity, believing the sacrifice of a few is worth the peace and safety of millions? Or do you break your vow and join the arrogant dragon's chaotic crusade, plunging the world back into violence for a chance at true freedom? This single choice will define your honor and your path in an empire where security is bought with blood."""

    CAMPAIGN_TITLE = "Dragon Knight Test Campaign"
    USER_ID_SUFFIX = "dragon-knight-user"

    def test_dragon_knight_character_creation(self):
        """Test automatic character creation when starting the Dragon Knight campaign."""
        # Start the story - LLM automatically creates the character
        response = self.start_campaign_story()
        assert response.status_code == 200

        # Verify character creation using base class helper
        self.assert_character_created("Ser Arion", ["Knight", "Paladin"], "Lawful Good")

        print(
            "✅ Character auto-creation test passed - Ser Arion created with all required fields"
        )

    def test_dragon_knight_combat_encounter(self):
        """Test combat mechanics and state management in Dragon Knight campaign."""
        # Start story and make choices
        self.start_campaign_story()
        self.send_character_action(
            "I choose to listen to Aurum the Gilded King. I will not slaughter these innocent refugees."
        )

        # Trigger combat
        combat_prompt = (
            'Suddenly, Imperial Guards arrive to enforce the Empress\'s order. "Surrender, traitor!" they shout. '
            "I draw my sword and prepare to fight them in combat. I attack the lead guard!"
        )
        response = self.send_character_action(combat_prompt)
        assert response.status_code == 200

        # Verify combat using base class helper
        combat_state, combatants = self.assert_combat_active()

        # Additional specific checks
        player_combatant = next(
            (
                c
                for c in combatants
                if c.get("side") == "player" and c.get("name") == "Ser Arion"
            ),
            None,
        )
        assert player_combatant is not None, "Ser Arion should be in combat"
        assert "hp_current" in player_combatant, "Player should have current HP"
        assert "hp_max" in player_combatant, "Player should have max HP"

        print(
            f"✅ Combat test passed - Combat active with {len(combatants)} combatants"
        )

    def test_dragon_knight_story_progression(self):
        """Test narrative choices and story progression through Dragon Knight campaign."""
        # Start the story using base class helper
        self.start_campaign_story()

        # Make narrative choices using base class helper
        choices = [
            (
                "I choose to listen to Aurum the Gilded King. I will not slaughter these innocent refugees. "
                "I sheath my sword and stand with the dragon against the Empress."
            ),
            (
                "I approach Theron and Elara. \"The dragon offers freedom from the Empress's tyranny. "
                'Will you stand with me against her forces?" I try to rally the refugees to our cause.'
            ),
            (
                'Suddenly, Imperial Guards arrive to enforce the Empress\'s order. "Surrender, traitor!" they shout. '
                "I draw my sword and prepare to fight them in combat. I attack the lead guard!"
            ),
        ]

        for choice in choices:
            response = self.send_character_action(choice)
            assert response.status_code == 200

        # Verify story progression using base class helper
        expected_elements = ["arion", "choice", "dragon", "aurum", "refugees"]
        core_memories = self.assert_story_progression(expected_elements)

        # Verify combat was triggered using base class helper
        combat_state, combatants = self.assert_combat_active()

        print(
            f"✅ Story progression test passed - {len(core_memories)} memories, combat active with {len(combatants)} combatants"
        )


class TestBG3AstarionCampaign(BaseCampaignIntegrationTest):
    """Test the BG3 Astarion custom campaign with character creation and story progression.

    This tests a custom Baldur's Gate 3 inspired campaign where the player is Astarion,
    the vampire spawn, testing custom character prompts and story integration.
    """

    CAMPAIGN_PROMPT = """You are Astarion, a vampire spawn who has just escaped from his cruel master Cazador after 200 years of servitude. The illithid tadpole in your brain has somehow freed you from Cazador's compulsion, but you still bear the scars of centuries of torture and manipulation.

You find yourself in a small village at dusk, your newfound freedom both exhilarating and terrifying. The hunger for blood gnaws at you, but for the first time in centuries, you can choose whether to feed. A young woman walks alone down a dark alley, humming softly to herself.

As you struggle with your vampiric nature and the weight of your past, you must decide: Will you embrace the monster Cazador made you, or fight against your dark impulses to forge a new path? Your choice here will define whether you remain a slave to your nature or become truly free."""

    CAMPAIGN_TITLE = "BG3 Astarion Test Campaign"
    USER_ID_SUFFIX = "bg3-astarion-user"

    def test_astarion_character_creation(self):
        """Test automatic character creation for Astarion campaign."""
        # Start the story - LLM automatically creates Astarion
        response = self.start_campaign_story()
        assert response.status_code == 200

        # Verify character creation - Astarion should be a Rogue or similar
        pc_data = self.assert_character_created(
            "Astarion", ["Rogue", "Vampire Spawn", "Ranger"], None
        )

        # Check for vampire-specific traits
        traits_text = (
            str(pc_data.get("traits", []))
            + " "
            + str(pc_data.get("race", ""))
            + " "
            + str(pc_data.get("subrace", ""))
        )
        assert (
            "vampire" in traits_text.lower() or "undead" in traits_text.lower()
        ), f"Astarion should have vampire/undead traits. Got: {traits_text}"

        print("✅ Astarion character creation test passed")

    def test_astarion_story_progression_full(self):
        """Test complete narrative arc with three choices and combat for Astarion."""
        # Start story
        self.start_campaign_story()

        # Narrative Choice 1: Resist the hunger (moral choice)
        choice_1 = (
            "I clench my fists and turn away from the woman. 'No,' I whisper to myself. "
            "'I am not Cazador's puppet anymore. I will not feed on innocents.' "
            "I retreat into the shadows, fighting the hunger."
        )
        response_1 = self.send_character_action(choice_1)
        assert response_1.status_code == 200

        # Narrative Choice 2: Seek alternative sustenance
        choice_2 = (
            "I search the village outskirts for animals - rats, birds, anything to quell this hunger. "
            "'There must be another way,' I tell myself. I find a stray dog and reluctantly feed, "
            "hating myself but refusing to harm innocents."
        )
        response_2 = self.send_character_action(choice_2)
        assert response_2.status_code == 200

        # Narrative Choice 3: Trigger combat with vampire hunters or Cazador's minions
        choice_3 = (
            "Suddenly, I sense familiar presences - vampire spawn, my former 'siblings' sent by Cazador! "
            "'Come back to master, brother,' they hiss from the shadows. 'Never!' I snarl, "
            "drawing my daggers. 'I'll die before I return to him!' I attack the nearest spawn!"
        )
        response_3 = self.send_character_action(choice_3)
        assert response_3.status_code == 200

        # Verify story progression - check for key story beats
        expected_elements = ["astarion", "cazador", "hunger", "vampire", "siblings"]
        core_memories = self.assert_story_progression(expected_elements)

        # Verify combat was triggered
        combat_state, combatants = self.assert_combat_active()

        # Check for Astarion in combat
        astarion = next((c for c in combatants if c.get("name") == "Astarion"), None)
        assert astarion is not None, "Astarion should be in combat"

        print(
            f"✅ Astarion full story progression test passed - {len(core_memories)} memories, combat with {len(combatants)} combatants"
        )

    def test_astarion_combat_mechanics(self):
        """Test combat mechanics when vampire hunters attack Astarion."""
        # Start story and make initial choice
        self.start_campaign_story()
        self.send_character_action(
            "I resist the urge to feed and look for another way."
        )

        # Trigger combat with vampire hunters (avoiding apostrophes in entity names)
        combat_trigger = (
            "A group of vampire hunters bursts into the alley! 'Found one!' their leader shouts. "
            "'Die, monster!' They draw silver weapons and attack. I have no choice but to defend myself. "
            "I draw my daggers and strike at the lead hunter!"
        )
        response = self.send_character_action(combat_trigger)
        assert response.status_code == 200

        # Verify combat state
        combat_state, combatants = self.assert_combat_active()

        # Check for Astarion in combat
        astarion = next((c for c in combatants if c.get("name") == "Astarion"), None)
        assert astarion is not None, "Astarion should be in combat"
        assert astarion.get("side") == "player", "Astarion should be on player side"

        # Check for enemy combatants (hunters)
        enemy_combatants = [c for c in combatants if c.get("side") == "enemy"]
        assert len(enemy_combatants) > 0, "Should have enemy combatants"

        # Verify Astarion has proper combat stats
        assert "hp_current" in astarion, "Astarion should have current HP"
        assert "hp_max" in astarion, "Astarion should have max HP"

        print(
            f"✅ Astarion combat mechanics test passed - Fighting {len(combatants)} combatants"
        )

    def test_character_creation_ai_generated_with_specified_character(self):
        """Test AIGenerated path with a pre-specified character (e.g., Geralt of Rivia)"""
        # Create campaign with specified character
        create_response = self.client.post(
            "/api/campaigns",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps(
                {
                    "prompt": "I want to play as Geralt of Rivia, the legendary witcher",
                    "title": "Witcher Campaign",
                    "selected_prompts": ["narrative", "mechanics"],
                }
            ),
        )
        assert create_response.status_code == 201
        campaign_id = create_response.get_json()["campaign_id"]

        # First interaction should recognize Geralt and offer design options
        interact_response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps({"input": "1"}),  # Select AIGenerated
        )
        assert interact_response.status_code == 200
        response_data = interact_response.get_json()

        # Verify character recognition
        assert "Geralt" in response_data["response"], "Should recognize Geralt"

        # Verify complete character sheet is shown
        response_text = response_data["response"]
        assert "CHARACTER SHEET" in response_text, "Should show character sheet"
        assert "STR:" in response_text, "Should show STR score"
        assert "DEX:" in response_text, "Should show DEX score"
        assert "CON:" in response_text, "Should show CON score"
        assert "INT:" in response_text, "Should show INT score"
        assert "WIS:" in response_text, "Should show WIS score"
        assert "CHA:" in response_text, "Should show CHA score"
        assert "Equipment:" in response_text, "Should show equipment"

        # Verify planning block
        assert "--- PLANNING BLOCK ---" in response_text, "Should have planning block"

        # Approve the character
        approve_response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps({"input": "1"}),  # Approve character
        )
        assert approve_response.status_code == 200

        # Verify character data is stored
        # Use the campaign API endpoint to get state
        state_response = self.client.get(
            f"/api/campaigns/{campaign_id}",
            headers={
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
        )
        assert state_response.status_code == 200
        state_data = state_response.get_json()
        final_state = state_data.get("game_state", {})
        pc_data = final_state.get("player_character_data", {})

        assert pc_data.get("name") == "Geralt", "Character name should be Geralt"
        assert "class" in pc_data, "Should have character class"
        assert "hp_max" in pc_data, "Should have max HP"

        print("✅ AIGenerated path with specified character test passed")

    def test_character_creation_ai_generated_no_character(self):
        """Test AIGenerated path without pre-specified character"""
        # Create campaign without specified character
        create_response = self.client.post(
            "/api/campaigns",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps(
                {
                    "prompt": "A dark fantasy world filled with ancient magic",
                    "title": "Dark Fantasy Campaign",
                    "selected_prompts": ["narrative", "mechanics"],
                }
            ),
        )
        assert create_response.status_code == 201
        campaign_id = create_response.get_json()["campaign_id"]

        # First interaction should offer generic character creation
        interact_response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps({"input": "1"}),  # Select AIGenerated
        )
        assert interact_response.status_code == 200
        response_data = interact_response.get_json()

        # Verify generic greeting
        response_text = response_data["response"]
        assert "CHARACTER SHEET" in response_text, "Should show character sheet"

        # Verify all required character elements
        assert "Race:" in response_text, "Should show race"
        assert "Class:" in response_text, "Should show class"
        assert "Level:" in response_text, "Should show level"
        assert "Background:" in response_text, "Should show background"
        assert "Why This Character:" in response_text, "Should explain choices"

        print("✅ AIGenerated path without character test passed")

    def test_character_creation_standard_dnd_path(self):
        """Test StandardD&D path with step-by-step choices"""
        # Create campaign
        create_response = self.client.post(
            "/api/campaigns",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps(
                {
                    "prompt": "Standard D&D adventure",
                    "title": "Standard D&D Campaign",
                    "selected_prompts": ["narrative", "mechanics"],
                }
            ),
        )
        assert create_response.status_code == 201
        campaign_id = create_response.get_json()["campaign_id"]

        # Select StandardD&D option
        interact_response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps({"input": "2"}),  # Select StandardD&D
        )
        assert interact_response.status_code == 200
        response_data = interact_response.get_json()

        # Should present race options
        response_text = response_data["response"]
        assert "Human" in response_text, "Should list Human race"
        assert "Elf" in response_text, "Should list Elf race"
        assert "Dwarf" in response_text, "Should list Dwarf race"

        # Select Human (option 1)
        race_response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps({"input": "1"}),  # Select Human
        )
        assert race_response.status_code == 200

        # Should now present class options
        class_text = race_response.get_json()["response"]
        assert "Fighter" in class_text, "Should list Fighter class"
        assert "Wizard" in class_text, "Should list Wizard class"

        print("✅ StandardD&D path test passed")

    def test_character_creation_custom_class_path(self):
        """Test CustomClass path with unique character concept"""
        # Create campaign with custom character idea
        create_response = self.client.post(
            "/api/campaigns",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps(
                {
                    "prompt": "I want to play as a time-traveling chronomancer",
                    "title": "Custom Character Campaign",
                    "selected_prompts": ["narrative", "mechanics"],
                }
            ),
        )
        assert create_response.status_code == 201
        campaign_id = create_response.get_json()["campaign_id"]

        # Select CustomClass option
        interact_response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps({"input": "3"}),  # Select CustomClass
        )
        assert interact_response.status_code == 200
        response_data = interact_response.get_json()

        # Should acknowledge custom concept
        response_text = response_data["response"]
        assert (
            "chronomancer" in response_text.lower()
        ), "Should acknowledge chronomancer concept"

        # Should ask for more details or present custom mechanics
        assert "--- PLANNING BLOCK ---" in response_text, "Should have planning block"

        print("✅ CustomClass path test passed")

    def test_character_creation_numeric_input_handling(self):
        """Test that numeric inputs are correctly interpreted during character creation"""
        # Create campaign
        create_response = self.client.post(
            "/api/campaigns",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps(
                {
                    "prompt": "Test numeric input handling",
                    "title": "Numeric Input Test",
                    "selected_prompts": ["narrative", "mechanics"],
                }
            ),
        )
        assert create_response.status_code == 201
        campaign_id = create_response.get_json()["campaign_id"]

        # Send numeric input "2" - should select StandardD&D, not continue story
        interact_response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps({"input": "2"}),
        )
        assert interact_response.status_code == 200
        response_data = interact_response.get_json()

        # Verify it interpreted as option selection, not story continuation
        response_text = response_data["response"]
        # Should present race/class options, not continue story
        races_presented = any(
            race in response_text for race in ["Human", "Elf", "Dwarf", "Halfling"]
        )
        assert (
            races_presented
        ), "Numeric input should trigger StandardD&D path, not story continuation"

        print("✅ Numeric input handling test passed")

    def test_character_creation_final_approval_enforcement(self):
        """Test that final approval step is always presented"""
        # Create campaign
        create_response = self.client.post(
            "/api/campaigns",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps(
                {
                    "prompt": "Test final approval",
                    "title": "Approval Test",
                    "selected_prompts": ["narrative", "mechanics"],
                }
            ),
        )
        assert create_response.status_code == 201
        campaign_id = create_response.get_json()["campaign_id"]

        # Select AIGenerated
        interact_response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps({"input": "1"}),
        )
        assert interact_response.status_code == 200
        response_data = interact_response.get_json()

        # Verify final approval options are presented
        response_text = response_data["response"]
        assert "Would you like to" in response_text, "Should ask for approval"
        approval_options = ["Play as this character", "Make changes", "Start over"]
        for option in approval_options:
            assert option in response_text, f"Should include '{option}' option"

        print("✅ Final approval enforcement test passed")

    def test_character_creation_shows_campaign_summary(self):
        """Test that character creation displays full campaign summary"""
        # Create campaign with all options
        create_response = self.client.post(
            "/api/campaigns",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps(
                {
                    "prompt": "I want to play as Drizzt Do'Urden in the Underdark",
                    "title": "Drizzt's Journey",
                    "selected_prompts": ["narrative", "mechanics"],
                }
            ),
        )
        assert create_response.status_code == 201
        campaign_id = create_response.get_json()["campaign_id"]

        # First interaction should show campaign summary
        interact_response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": self.user_id,
            },
            data=json.dumps({"input": ""}),  # Empty input to see initial response
        )
        assert interact_response.status_code == 200
        response_data = interact_response.get_json()
        response_text = response_data["response"]

        # Verify campaign summary is shown
        assert (
            "CAMPAIGN SUMMARY" in response_text
        ), "Should show campaign summary header"
        assert "Title:" in response_text, "Should show title field"
        assert "Character:" in response_text, "Should show character field"
        assert "Setting:" in response_text, "Should show setting field"
        assert "Description:" in response_text, "Should show description field"
        assert "AI Personalities:" in response_text, "Should show personalities"
        assert "Options:" in response_text, "Should show options"

        # Verify specific content
        assert "Drizzt" in response_text, "Should show character name"
        assert (
            "Narrative, Mechanics" in response_text
        ), "Should list active personalities"

        print("✅ Campaign summary display test passed")


if __name__ == "__main__":
    unittest.main()
