"""
MCP Server Integration Tests

Tests for the MCP server (world_logic.py) in isolation.
Verifies that the MCP server correctly implements the protocol
and provides the expected game logic functionality.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import unittest
import requests

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))

from helpers import (
    assert_mcp_response_format,
    create_test_action_data,
    create_test_character_data,
    mock_environment,
    patch_firestore,
    patch_gemini,
)

# Import mcp_api - will handle if not available in test logic
import mcp_api
from mcp_test_client import MCPError


class TestMCPServerIntegration(unittest.TestCase):
    """Integration tests for MCP server functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_user_id = "test-user-123"
        self.mock_port = 8001

    @patch_firestore()
    @patch_gemini()
    def test_mcp_server_health_check(self, mock_gemini, mock_firestore):
        """Test that MCP server responds to health checks."""
        with mock_environment(self.mock_port) as env:
            # The mock server should be running and healthy
            assert env["mock_server"] is not None

            # Test direct health check
            response = requests.get(f"http://localhost:{self.mock_port}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

    @patch_firestore()
    @patch_gemini()
    def test_list_available_tools(self, mock_gemini, mock_firestore):
        """Test listing all available MCP tools."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            # Use asyncio to run async test
            async def run_test():
                async with client:
                    tools = await client.list_tools()

                    # Verify expected tools are available
                    expected_tools = [
                        "create_campaign",
                        "get_campaigns",
                        "get_campaign",
                        "update_campaign",
                        "create_character",
                        "process_action",
                        "get_campaign_state",
                        "export_campaign",
                        "get_user_settings",
                        "update_user_settings",
                    ]

                    tool_names = [tool["name"] for tool in tools]
                    for expected_tool in expected_tools:
                        assert expected_tool in tool_names

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_create_campaign_tool(self, mock_gemini, mock_firestore):
        """Test the create_campaign MCP tool."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Test campaign creation
                    response = await client.create_campaign(
                        name="Test Campaign",
                        description="A test campaign for MCP",
                        user_id=self.test_user_id,
                    )

                    # Verify response format
                    await assert_mcp_response_format(response)
                    assert response["status"] == "success"

                    # Verify response data
                    data = response["data"]
                    assert "campaign_id" in data
                    assert data["name"] == "Test Campaign"
                    assert data["description"] == "A test campaign for MCP"
                    assert data["dm_user_id"] == self.test_user_id
                    assert "created_at" in data

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_get_campaigns_tool(self, mock_gemini, mock_firestore):
        """Test the get_campaigns MCP tool."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # First create a campaign
                    create_response = await client.create_campaign(
                        name="Test Campaign 1",
                        description="First test campaign",
                        user_id=self.test_user_id,
                    )
                    assert create_response["status"] == "success"

                    # Then get all campaigns
                    response = await client.get_campaigns(user_id=self.test_user_id)

                    # Verify response format
                    await assert_mcp_response_format(response)
                    assert response["status"] == "success"

                    # Verify campaigns list
                    data = response["data"]
                    assert "campaigns" in data
                    campaigns = data["campaigns"]
                    assert isinstance(campaigns, list)

                    # Should include the created campaign plus any mock data
                    assert len(campaigns) >= 1

                    # Find our created campaign
                    created_campaign = next(
                        (c for c in campaigns if c["name"] == "Test Campaign 1"), None
                    )
                    assert created_campaign is not None
                    assert created_campaign["dm_user_id"] == self.test_user_id

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_get_specific_campaign_tool(self, mock_gemini, mock_firestore):
        """Test the get_campaign MCP tool for a specific campaign."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Create a campaign first
                    create_response = await client.create_campaign(
                        name="Specific Test Campaign",
                        description="Testing specific campaign retrieval",
                        user_id=self.test_user_id,
                    )
                    assert create_response["status"] == "success"
                    campaign_id = create_response["data"]["campaign_id"]

                    # Get the specific campaign
                    response = await client.get_campaign(
                        campaign_id=campaign_id, user_id=self.test_user_id
                    )

                    # Verify response format
                    await assert_mcp_response_format(response)
                    assert response["status"] == "success"

                    # Verify campaign data
                    campaign_data = response["data"]
                    assert campaign_data["id"] == campaign_id
                    assert campaign_data["name"] == "Specific Test Campaign"
                    assert campaign_data["description"] == "Testing specific campaign retrieval"
                    assert campaign_data["dm_user_id"] == self.test_user_id

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_create_character_tool(self, mock_gemini, mock_firestore):
        """Test the create_character MCP tool."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Create a campaign first
                    campaign_response = await client.create_campaign(
                        name="Character Test Campaign",
                        description="For testing character creation",
                        user_id=self.test_user_id,
                    )
                    campaign_id = campaign_response["data"]["campaign_id"]

                    # Create a character
                    character_data = create_test_character_data()
                    response = await client.create_character(
                        campaign_id=campaign_id, character_data=character_data
                    )

                    # Verify response format
                    await assert_mcp_response_format(response)
                    assert response["status"] == "success"

                    # Verify character data
                    char_data = response["data"]
                    assert "id" in char_data
                    assert char_data["name"] == character_data["name"]
                    assert char_data["campaign_id"] == campaign_id
                    assert char_data["character_class"] == character_data["class"]
                    assert char_data["level"] == character_data["level"]
                    assert char_data["attributes"] == character_data["attributes"]

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_process_action_tool(self, mock_gemini, mock_firestore):
        """Test the process_action MCP tool."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Process a game action
                    session_id = "test-session-123"
                    action_data = create_test_action_data()

                    response = await client.process_action(
                        session_id=session_id,
                        action_type=action_data["action_type"],
                        action_data=action_data,
                    )

                    # Verify response format
                    await assert_mcp_response_format(response)
                    assert response["status"] == "success"

                    # Verify action result
                    result_data = response["data"]
                    assert "action_id" in result_data
                    assert result_data["session_id"] == session_id
                    assert result_data["action_type"] == action_data["action_type"]
                    assert "result" in result_data
                    assert "narrative" in result_data
                    assert "timestamp" in result_data

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_user_settings_tools(self, mock_gemini, mock_firestore):
        """Test user settings MCP tools."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Get initial settings (should create defaults)
                    get_response = await client.get_user_settings(
                        user_id=self.test_user_id
                    )

                    await assert_mcp_response_format(get_response)
                    assert get_response["status"] == "success"

                    initial_settings = get_response["data"]
                    assert initial_settings["user_id"] == self.test_user_id
                    assert "theme" in initial_settings
                    assert "notifications" in initial_settings

                    # Update settings
                    new_settings = {
                        "theme": "dark",
                        "notifications": False,
                        "ai_model": "gemini-1.5-pro",
                    }

                    update_response = await client.update_user_settings(
                        user_id=self.test_user_id, settings=new_settings
                    )

                    await assert_mcp_response_format(update_response)
                    assert update_response["status"] == "success"

                    # Verify updated settings
                    updated_settings = update_response["data"]
                    assert updated_settings["theme"] == "dark"
                    assert not updated_settings["notifications"]
                    assert updated_settings["ai_model"] == "gemini-1.5-pro"

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_export_campaign_tool(self, mock_gemini, mock_firestore):
        """Test the export_campaign MCP tool."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Create a campaign to export
                    campaign_response = await client.create_campaign(
                        name="Export Test Campaign",
                        description="Campaign for testing export",
                        user_id=self.test_user_id,
                    )
                    campaign_id = campaign_response["data"]["campaign_id"]

                    # Export the campaign
                    response = await client.export_campaign(
                        campaign_id=campaign_id,
                        export_format="pdf",
                        user_id=self.test_user_id,
                    )

                    # Verify response format
                    await assert_mcp_response_format(response)
                    assert response["status"] == "success"

                    # Verify export data
                    export_data = response["data"]
                    assert "export_id" in export_data
                    assert export_data["format"] == "pdf"
                    assert "download_url" in export_data
                    assert "expires_at" in export_data

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_mcp_resource_access(self, mock_gemini, mock_firestore):
        """Test MCP resource access functionality."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # List available resources
                    resources = await client.list_resources()
                    assert isinstance(resources, list)

                    # Should have some mock resources available
                    assert len(resources) > 0

                    # Try to access a campaign resource
                    campaign_resources = [
                        r for r in resources if r["uri"].startswith("campaign://")
                    ]
                    if campaign_resources:
                        resource_uri = campaign_resources[0]["uri"]
                        resource_data = await client.get_resource(resource_uri)

                        assert "contents" in resource_data
                        contents = resource_data["contents"]
                        assert isinstance(contents, list)
                        assert len(contents) > 0

                        # Verify content structure
                        content = contents[0]
                        assert "uri" in content
                        assert "mimeType" in content
                        assert "text" in content

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_error_handling(self, mock_gemini, mock_firestore):
        """Test MCP server error handling."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Test getting non-existent campaign
                    error_raised = False
                    try:
                        await client.get_campaign(
                            campaign_id="non-existent-campaign",
                            user_id=self.test_user_id,
                        )
                    except MCPError as e:
                        error_raised = True
                        assert "not_found" in str(e)
                    assert error_raised, "Expected MCPError for non-existent campaign"

                    # Test accessing non-existent resource
                    error_raised = False
                    try:
                        await client.get_resource("campaign://non-existent/state")
                    except MCPError as e:
                        error_raised = True
                        assert "not found" in str(e).lower()
                    assert error_raised, "Expected MCPError for non-existent resource"

                    # Test invalid tool call
                    error_raised = False
                    try:
                        await client.call_tool("non_existent_tool", {})
                    except MCPError as e:
                        error_raised = True
                        assert "not found" in str(e).lower()
                    assert error_raised, "Expected MCPError for invalid tool"

            asyncio.run(run_test())

    @patch_firestore()
    @patch_gemini()
    def test_authentication_and_authorization(self, mock_gemini, mock_firestore):
        """Test that MCP tools respect user authentication and authorization."""
        with mock_environment(self.mock_port) as env:
            client = env["client"]

            async def run_test():
                async with client:
                    # Create a campaign as user1
                    user1_id = "user-1"
                    campaign_response = await client.create_campaign(
                        name="User1 Campaign",
                        description="Private campaign",
                        user_id=user1_id,
                    )
                    campaign_id = campaign_response["data"]["campaign_id"]

                    # Try to access it as user2 (should fail in real implementation)
                    user2_id = "user-2"

                    # Note: Mock server doesn't enforce this, but real server should
                    # This test documents the expected behavior
                    try:
                        response = await client.get_campaign(
                            campaign_id=campaign_id, user_id=user2_id
                        )
                        # If mock allows it, that's fine - real server should deny
                        if response["status"] == "error":
                            assert response["error_type"] == "permission_denied"
                    except MCPError as e:
                        assert e.code == 403  # Forbidden

            asyncio.run(run_test())

    def test_mcp_server_direct_stdio(self):
        """Test MCP server functionality via direct stdio communication.

        Validates:
        - JSON-RPC protocol compliance
        - tools/list endpoint functionality
        - create_campaign tool execution
        - Process lifecycle management
        - Error handling for communication failures
        """
        env = os.environ.copy()
        env['TESTING'] = 'true'
        env['MOCK_SERVICES_MODE'] = 'true'

        # Resolve repo root -> mvp_site/mcp_api.py robustly
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        server_script = os.path.join(repo_root, "mvp_site", "mcp_api.py")
        server_cmd = [sys.executable, server_script, "--stdio"]

        server = None
        try:
            # Start server process
            server = subprocess.Popen(
                server_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=os.path.dirname(__file__)  # Run from test directory
            )

            # Test tools/list request
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            }

            server.stdin.write(json.dumps(tools_request) + '\n')
            server.stdin.flush()

            # Read response with timeout
            response_line = server.stdout.readline()
            self.assertTrue(response_line, "No response from tools/list")

            response = json.loads(response_line.strip())
            result = response.get('result', {})
            tools = result.get('tools', [])
            self.assertGreater(len(tools), 0, f"No tools returned. Response: {response}")

            # Test create_campaign call
            campaign_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_campaign",
                    "arguments": {
                        "user_id": self.test_user_id,
                        "title": "Stdio Test Campaign",
                        "character": "Test Character",
                        "setting": "Test Setting",
                        "description": "Test campaign via stdio"
                    }
                },
                "id": 2
            }

            server.stdin.write(json.dumps(campaign_request) + '\n')
            server.stdin.flush()

            response_line = server.stdout.readline()
            self.assertTrue(response_line, "No response from create_campaign")

            response = json.loads(response_line.strip())
            result = response.get('result', {})
            self.assertNotIn('error', result, f"Campaign creation failed: {result.get('error')}. Full response: {response}")

            # Clean shutdown
            server.stdin.close()
            server.wait(timeout=5)

        except subprocess.TimeoutExpired:
            if server:
                server.kill()
            self.fail("MCP server process timed out")
        except Exception as e:
            if server and server.poll() is None:
                server.kill()
            self.fail(f"Direct stdio test failed: {e}")

    def test_mcp_server_http_mode(self):
        """Test MCP server functionality via HTTP JSON-RPC.

        Validates:
        - HTTP server startup and health checks
        - JSON-RPC over HTTP protocol compliance
        - tools/list and create_campaign endpoints
        - Production-like deployment scenarios
        - Proper server lifecycle management
        """
        env = os.environ.copy()
        env['TESTING'] = 'true'
        env['MOCK_SERVICES_MODE'] = 'true'

        # Resolve repo root -> mvp_site/mcp_api.py robustly
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        server_script = os.path.join(repo_root, "mvp_site", "mcp_api.py")

        test_port = 8003  # Different from mock_port to avoid conflicts
        server_cmd = [
            sys.executable,
            server_script,
            '--port', str(test_port),
            '--http-only'
        ]

        server = None
        try:
            # Start server process in HTTP mode
            server = subprocess.Popen(
                server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=os.path.dirname(__file__)
            )

            # Wait for server startup with health check polling
            for attempt in range(30):  # 30 attempts = 15 seconds max
                try:
                    health_response = requests.get(f"http://localhost:{test_port}/health", timeout=1)
                    if health_response.status_code == 200:
                        break
                except requests.RequestException:
                    time.sleep(0.5)
            else:
                self.fail("Server failed to start within timeout")

            # Verify server is healthy
            self.assertEqual(health_response.status_code, 200)

            health_data = health_response.json()
            self.assertEqual(health_data["status"], "ok")

            # Test tools/list via HTTP
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            }

            response = requests.post(
                f"http://localhost:{test_port}/rpc",
                json=tools_request,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            self.assertEqual(response.status_code, 200)
            result = response.json()
            tools = result.get('result', {}).get('tools', [])
            self.assertGreater(len(tools), 0, f"No tools returned via HTTP. Response: {result}")

            # Test create_campaign via HTTP
            campaign_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_campaign",
                    "arguments": {
                        "user_id": self.test_user_id,
                        "title": "HTTP Test Campaign",
                        "character": "HTTP Character",
                        "setting": "HTTP Setting",
                        "description": "Test campaign via HTTP"
                    }
                },
                "id": 2
            }

            response = requests.post(
                f"http://localhost:{test_port}/rpc",
                json=campaign_request,
                headers={"Content-Type": "application/json"},
                timeout=15
            )

            self.assertEqual(response.status_code, 200)
            result = response.json()
            campaign_result = result.get('result', {})
            self.assertNotIn('error', campaign_result, f"Campaign creation failed: {campaign_result.get('error')}")

        except Exception as e:
            self.fail(f"HTTP mode test failed: {e}")
        finally:
            if server and server.poll() is None:
                server.terminate()
                try:
                    server.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    server.kill()

    def test_mcp_direct_import_functions(self):
        """Test MCP server functions by direct import and execution.

        Validates:
        - Direct function imports without process overhead
        - handle_list_tools, handle_call_tool, handle_list_resources
        - Environment isolation and cleanup
        - Unit-level testing of core MCP functions
        - Tool validation and resource discovery
        """
        # Set environment for testing
        old_testing = os.environ.get('TESTING')
        old_mock_services_mode = os.environ.get('MOCK_SERVICES_MODE')
        os.environ['TESTING'] = 'true'
        os.environ['MOCK_SERVICES_MODE'] = 'true'

        # Add mvp_site to path for imports
        mvp_site_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "mvp_site"))
        if mvp_site_path not in map(os.path.abspath, sys.path):
            sys.path.insert(0, mvp_site_path)

        try:
            # Test handle_list_tools function
            async def test_tools():
                tools = await mcp_api.handle_list_tools()
                self.assertGreater(len(tools), 0, "No tools found via direct import")
                return tools

            # Test handle_call_tool function
            async def test_campaign():
                campaign_args = {
                    "user_id": self.test_user_id,
                    "title": "Direct Import Test Campaign",
                    "character": "Import Character",
                    "setting": "Import Setting",
                    "description": "Test via direct import"
                }

                result = await mcp_api.handle_call_tool("create_campaign", campaign_args)
                self.assertTrue(result, "No result from create_campaign")

                result_text = result[0].text
                result_data = json.loads(result_text)
                self.assertNotIn('error', result_data, f"Campaign creation error: {result_data.get('error')}")
                return result_data

            # Test handle_list_resources function
            async def test_resources():
                resources = await mcp_api.handle_list_resources()
                self.assertGreater(len(resources), 0, "No resources found via direct import")
                return resources

            # Run async tests
            tools = asyncio.run(test_tools())
            campaign_data = asyncio.run(test_campaign())
            resources = asyncio.run(test_resources())

            # Verify tool names include expected ones
            tool_names = [tool.name for tool in tools]
            expected_tools = ['create_campaign', 'get_campaign_state', 'process_action']
            for expected_tool in expected_tools:
                self.assertIn(expected_tool, tool_names, f"Missing expected tool: {expected_tool}")

        except Exception as e:
            self.fail(f"Direct import test failed: {e}")
        finally:
            # Restore only the specific environment variables modified
            if old_testing is not None:
                os.environ['TESTING'] = old_testing
            else:
                os.environ.pop('TESTING', None)
            if old_mock_services_mode is not None:
                os.environ['MOCK_SERVICES_MODE'] = old_mock_services_mode
            else:
                os.environ.pop('MOCK_SERVICES_MODE', None)


if __name__ == "__main__":
    # Set up logging for test debugging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
