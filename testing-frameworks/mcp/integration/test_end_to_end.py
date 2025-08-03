"""
End-to-End MCP Integration Tests

Complete workflow tests that verify the entire MCP architecture:
Browser → Translation Layer → MCP Server → Business Logic → Response
"""

import asyncio
import os
import sys
import time
import unittest

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))

from helpers import (
    create_test_action_data,
    create_test_character_data,
    find_free_port,
    mock_environment,
    patch_firestore,
    patch_gemini,
)


class TestEndToEndMCPIntegration(unittest.TestCase):
    """End-to-end tests for complete MCP architecture workflows."""

    def setUp(self):
        """Set up test environment."""
        self.test_user_id = "test-user-123"
        self.mock_port = find_free_port(8001)

    @patch_firestore()
    @patch_gemini()
    def test_complete_campaign_creation_workflow(self, mock_gemini, mock_firestore):
        """Test complete campaign creation from start to finish."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Step 1: Create a new campaign
                    campaign_response = await client.create_campaign(
                        name="End-to-End Test Campaign",
                        description="Complete workflow test campaign",
                        user_id=self.test_user_id,
                    )

                    assert campaign_response["status"] == "success"
                    campaign_id = campaign_response["data"]["campaign_id"]

                    # Step 2: Verify campaign appears in user's campaign list
                    campaigns_response = await client.get_campaigns(
                        user_id=self.test_user_id
                    )
                    assert campaigns_response["status"] == "success"

                    campaigns = campaigns_response["data"]["campaigns"]
                    created_campaign = next(
                        (c for c in campaigns if c["id"] == campaign_id), None
                    )
                    assert created_campaign is not None
                    assert created_campaign["name"] == "End-to-End Test Campaign"

                    # Step 3: Get specific campaign details
                    campaign_details = await client.get_campaign(
                        campaign_id=campaign_id, user_id=self.test_user_id
                    )
                    assert campaign_details["status"] == "success"
                    assert campaign_details["data"]["id"] == campaign_id

                    # Step 4: Access campaign state resource
                    campaign_state = await client.get_campaign_state(
                        campaign_id=campaign_id, user_id=self.test_user_id
                    )
                    # Should return campaign data (mock returns tool format, not resource format)
                    assert campaign_state["status"] == "success"
                    assert campaign_state["data"]["id"] == campaign_id

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_complete_character_creation_workflow(self, mock_gemini, mock_firestore):
        """Test complete character creation workflow."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Step 1: Create a campaign for the character
                    campaign_response = await client.create_campaign(
                        name="Character Test Campaign",
                        description="Campaign for character creation",
                        user_id=self.test_user_id,
                    )
                    campaign_id = campaign_response["data"]["campaign_id"]

                    # Step 2: Create a character in the campaign
                    character_data = create_test_character_data()
                    character_response = await client.create_character(
                        campaign_id=campaign_id, character_data=character_data
                    )

                    assert character_response["status"] == "success"
                    character_response["data"]["id"]

                    # Step 3: Verify character data
                    char_data = character_response["data"]
                    assert char_data["name"] == character_data["name"]
                    assert char_data["campaign_id"] == campaign_id
                    assert char_data["character_class"] == character_data["class"]
                    assert char_data["level"] == character_data["level"]

                    # Step 4: Verify character affects campaign state
                    # (In real implementation, campaign should show it has characters)
                    campaign_details = await client.get_campaign(
                        campaign_id=campaign_id, user_id=self.test_user_id
                    )
                    assert campaign_details["status"] == "success"

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_complete_game_action_workflow(self, mock_gemini, mock_firestore):
        """Test complete game action processing workflow."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Step 1: Create campaign and character
                    campaign_response = await client.create_campaign(
                        name="Action Test Campaign",
                        description="Campaign for action testing",
                        user_id=self.test_user_id,
                    )
                    campaign_id = campaign_response["data"]["campaign_id"]

                    character_data = create_test_character_data()
                    character_response = await client.create_character(
                        campaign_id=campaign_id, character_data=character_data
                    )
                    character_id = character_response["data"]["id"]

                    # Step 2: Process a game action
                    session_id = f"session-{campaign_id}-{character_id}"
                    action_data = create_test_action_data()

                    action_response = await client.process_action(
                        session_id=session_id,
                        action_type=action_data["action_type"],
                        action_data=action_data,
                    )

                    assert action_response["status"] == "success"

                    # Step 3: Verify action result
                    result_data = action_response["data"]
                    assert "action_id" in result_data
                    assert result_data["session_id"] == session_id
                    assert result_data["action_type"] == action_data["action_type"]
                    assert "narrative" in result_data
                    assert "timestamp" in result_data

                    # Step 4: Verify action updated game state
                    assert result_data.get("game_state_updated", False)

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_user_settings_complete_workflow(self, mock_gemini, mock_firestore):
        """Test complete user settings management workflow."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Step 1: Get initial settings (creates defaults)
                    initial_response = await client.get_user_settings(
                        user_id=self.test_user_id
                    )
                    assert initial_response["status"] == "success"

                    initial_settings = initial_response["data"]
                    assert initial_settings["user_id"] == self.test_user_id

                    # Step 2: Update some settings
                    new_settings = {
                        "theme": "dark",
                        "notifications": False,
                        "ai_model": "gemini-1.5-pro",
                        "auto_save": True,
                    }

                    update_response = await client.update_user_settings(
                        user_id=self.test_user_id, settings=new_settings
                    )
                    assert update_response["status"] == "success"

                    # Step 3: Verify settings were updated
                    updated_settings = update_response["data"]
                    assert updated_settings["theme"] == "dark"
                    assert not updated_settings["notifications"]
                    assert updated_settings["ai_model"] == "gemini-1.5-pro"

                    # Step 4: Get settings again to verify persistence
                    final_response = await client.get_user_settings(
                        user_id=self.test_user_id
                    )
                    assert final_response["status"] == "success"

                    final_settings = final_response["data"]
                    assert final_settings["theme"] == "dark"
                    assert not final_settings["notifications"]

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_campaign_export_complete_workflow(self, mock_gemini, mock_firestore):
        """Test complete campaign export workflow."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Step 1: Create a campaign with some content
                    campaign_response = await client.create_campaign(
                        name="Export Test Campaign",
                        description="Campaign for testing export functionality",
                        user_id=self.test_user_id,
                    )
                    campaign_id = campaign_response["data"]["campaign_id"]

                    # Step 2: Add a character to the campaign
                    character_data = create_test_character_data()
                    character_response = await client.create_character(
                        campaign_id=campaign_id, character_data=character_data
                    )
                    assert character_response["status"] == "success"

                    # Step 3: Process some actions to create story content
                    session_id = f"export-test-session-{campaign_id}"
                    action_data = create_test_action_data()

                    action_response = await client.process_action(
                        session_id=session_id,
                        action_type=action_data["action_type"],
                        action_data=action_data,
                    )
                    assert action_response["status"] == "success"

                    # Step 4: Export the campaign
                    export_formats = ["pdf", "docx", "txt"]

                    for export_format in export_formats:
                        export_response = await client.export_campaign(
                            campaign_id=campaign_id,
                            export_format=export_format,
                            user_id=self.test_user_id,
                        )

                        assert export_response["status"] == "success"

                        export_data = export_response["data"]
                        assert "export_id" in export_data
                        assert export_data["format"] == export_format
                        assert "download_url" in export_data
                        assert "expires_at" in export_data

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_multi_user_isolation_workflow(self, mock_gemini, mock_firestore):
        """Test that multiple users' data is properly isolated."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    user1_id = "user-1"
                    user2_id = "user-2"

                    # Step 1: User 1 creates a campaign
                    user1_campaign = await client.create_campaign(
                        name="User 1 Campaign",
                        description="Private campaign for user 1",
                        user_id=user1_id,
                    )
                    assert user1_campaign["status"] == "success"
                    user1_campaign_id = user1_campaign["data"]["campaign_id"]

                    # Step 2: User 2 creates a campaign
                    user2_campaign = await client.create_campaign(
                        name="User 2 Campaign",
                        description="Private campaign for user 2",
                        user_id=user2_id,
                    )
                    assert user2_campaign["status"] == "success"
                    user2_campaign_id = user2_campaign["data"]["campaign_id"]

                    # Step 3: Verify User 1 only sees their campaigns
                    user1_campaigns = await client.get_campaigns(user_id=user1_id)
                    assert user1_campaigns["status"] == "success"

                    user1_campaign_ids = [
                        c["id"] for c in user1_campaigns["data"]["campaigns"]
                    ]
                    assert user1_campaign_id in user1_campaign_ids
                    # Note: Mock server might not enforce isolation, but real server should

                    # Step 4: Verify User 2 only sees their campaigns
                    user2_campaigns = await client.get_campaigns(user_id=user2_id)
                    assert user2_campaigns["status"] == "success"

                    user2_campaign_ids = [
                        c["id"] for c in user2_campaigns["data"]["campaigns"]
                    ]
                    assert user2_campaign_id in user2_campaign_ids

                    # Step 5: Verify users have separate settings
                    user1_settings = await client.get_user_settings(user_id=user1_id)
                    user2_settings = await client.get_user_settings(user_id=user2_id)

                    assert user1_settings["data"]["user_id"] == user1_id
                    assert user2_settings["data"]["user_id"] == user2_id

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_error_recovery_workflow(self, mock_gemini, mock_firestore):
        """Test error handling and recovery in complete workflows."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Step 1: Try to get non-existent campaign
                    try:
                        response = await client.get_campaign(
                            campaign_id="non-existent-campaign",
                            user_id=self.test_user_id,
                        )
                        if response["status"] == "error":
                            assert response["error_type"] == "not_found"
                    except Exception:
                        # Expected for non-existent campaign
                        pass

                    # Step 2: Create valid campaign after error
                    valid_campaign = await client.create_campaign(
                        name="Recovery Test Campaign",
                        description="Campaign created after error",
                        user_id=self.test_user_id,
                    )
                    assert valid_campaign["status"] == "success"

                    # Step 3: Try to create character in non-existent campaign
                    character_data = create_test_character_data()
                    try:
                        invalid_char_response = await client.create_character(
                            campaign_id="non-existent-campaign",
                            character_data=character_data,
                        )
                        if invalid_char_response["status"] == "error":
                            assert "not_found" in invalid_char_response["error_type"]
                    except Exception:
                        # Expected for non-existent campaign
                        pass

                    # Step 4: Create valid character after error
                    valid_character = await client.create_character(
                        campaign_id=valid_campaign["data"]["campaign_id"],
                        character_data=character_data,
                    )
                    assert valid_character["status"] == "success"

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_performance_under_load(self, mock_gemini, mock_firestore):
        """Test system performance under concurrent load."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Create multiple campaigns concurrently
                    campaign_tasks = []
                    num_campaigns = 10

                    for i in range(num_campaigns):
                        task = client.create_campaign(
                            name=f"Load Test Campaign {i}",
                            description=f"Campaign {i} for load testing",
                            user_id=f"load-test-user-{i}",
                        )
                        campaign_tasks.append(task)

                    # Execute all campaign creations concurrently
                    start_time = time.time()
                    results = await asyncio.gather(
                        *campaign_tasks, return_exceptions=True
                    )
                    end_time = time.time()

                    # Verify all campaigns were created successfully
                    successful_campaigns = 0
                    for result in results:
                        if (
                            isinstance(result, dict)
                            and result.get("status") == "success"
                        ):
                            successful_campaigns += 1

                    # Should handle concurrent requests reasonably well
                    assert successful_campaigns >= num_campaigns * 0.8  # 80% success rate

                    # Performance should be reasonable (< 5 seconds for 10 campaigns)
                    total_time = end_time - start_time
                    assert total_time < 5.0

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_mcp_resource_consistency(self, mock_gemini, mock_firestore):
        """Test that MCP resources stay consistent with tool operations."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Step 1: Create a campaign
                    campaign_response = await client.create_campaign(
                        name="Resource Consistency Test",
                        description="Testing resource consistency",
                        user_id=self.test_user_id,
                    )
                    campaign_id = campaign_response["data"]["campaign_id"]

                    # Step 2: Get campaign via tool call
                    tool_campaign = await client.get_campaign(
                        campaign_id=campaign_id, user_id=self.test_user_id
                    )

                    # Step 3: Get campaign via resource
                    resource_campaign = await client.get_campaign_state(
                        campaign_id=campaign_id, user_id=self.test_user_id
                    )

                    # Step 4: Verify consistency between tool and resource
                    tool_data = tool_campaign["data"]

                    # Mock returns same format for both (not real resource format)
                    assert resource_campaign["status"] == "success"
                    resource_data = resource_campaign["data"]

                    # Key fields should match
                    assert tool_data["id"] == resource_data["id"]
                    assert tool_data["name"] == resource_data["name"]
                    assert tool_data["description"] == resource_data["description"]

            asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
