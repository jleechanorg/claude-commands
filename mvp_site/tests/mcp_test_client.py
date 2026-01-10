#!/usr/bin/env python3
"""
MCP Test Client for WorldArchitect.AI
Provides programmatic testing interface for the MCP server
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any

import requests

MCP_HTTP_PATH = "/mcp"


class MCPTestClient:
    """Test client for WorldArchitect.AI MCP server."""

    def __init__(
        self, base_url: str = "http://127.0.0.1:8000", log_file: str | None = None
    ):
        """Initialize MCP test client.

        Args:
            base_url: Base URL of the MCP server
            log_file: Optional path to log file for request/response logging
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "WorldArchitect-MCP-TestClient/1.0",
            }
        )
        self.log_file = log_file
        self.request_counter = 0

        # Initialize log file if specified
        if self.log_file:
            with open(self.log_file, "w") as f:
                json.dump(
                    {
                        "test_run": {
                            "start_time": datetime.utcnow().isoformat() + "Z",
                            "base_url": base_url,
                        },
                        "requests": [],
                    },
                    f,
                    indent=2,
                )

    def _log_request_response(
        self,
        endpoint: str,
        method: str,
        request_data: Any,
        response_data: Any,
        status_code: int,
    ):
        """Log request and response to file.

        Args:
            endpoint: API endpoint
            method: HTTP method or RPC method
            request_data: Request payload
            response_data: Response data
            status_code: HTTP status code
        """
        if not self.log_file:
            return

        self.request_counter += 1

        try:
            # Read existing log
            with open(self.log_file) as f:
                log_data = json.load(f)

            # Add new entry
            log_data["requests"].append(
                {
                    "sequence": self.request_counter,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "endpoint": endpoint,
                    "method": method,
                    "request": request_data,
                    "response": response_data,
                    "status_code": status_code,
                }
            )

            # Write updated log
            with open(self.log_file, "w") as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to log request/response: {e}", file=sys.stderr)

    def health_check(self) -> dict[str, Any]:
        """Check server health status.

        Returns:
            Health status response

        Raises:
            requests.RequestException: If request fails
        """
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        response_data = response.json()

        # Log request/response
        self._log_request_response(
            endpoint="/health",
            method="GET",
            request_data=None,
            response_data=response_data,
            status_code=response.status_code,
        )

        return response_data

    def json_rpc_request(
        self, method: str, params: dict | None = None, request_id: str | int = 1
    ) -> dict[str, Any]:
        """Send JSON-RPC 2.0 request to MCP server.

        Args:
            method: JSON-RPC method name
            params: Method parameters (optional)
            request_id: Request identifier

        Returns:
            JSON-RPC response

        Raises:
            requests.RequestException: If request fails
        """
        payload = {"jsonrpc": "2.0", "method": method, "id": request_id}

        if params is not None:
            payload["params"] = params

        response = self.session.post(
            f"{self.base_url.rstrip('/')}{MCP_HTTP_PATH}", json=payload
        )
        response.raise_for_status()
        response_data = response.json()

        # Log request/response
        self._log_request_response(
            endpoint=MCP_HTTP_PATH,
            method=method,
            request_data=payload,
            response_data=response_data,
            status_code=response.status_code,
        )

        return response_data

    def list_tools(self) -> list[dict[str, Any]]:
        """List available MCP tools.

        Returns:
            List of tool definitions
        """
        response = self.json_rpc_request("tools/list")
        if "result" in response and "tools" in response["result"]:
            return response["result"]["tools"]
        return []

    def list_resources(self) -> list[dict[str, Any]]:
        """List available MCP resources.

        Returns:
            List of resource definitions
        """
        response = self.json_rpc_request("resources/list")
        if "result" in response and "resources" in response["result"]:
            return response["result"]["resources"]
        return []

    def read_resource(self, uri: str) -> str:
        """Read MCP resource content.

        Args:
            uri: Resource URI to read

        Returns:
            Resource content
        """
        response = self.json_rpc_request("resources/read", {"uri": uri})
        if "result" in response:
            return response["result"]
        return ""

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call MCP tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        params = {"name": name, "arguments": arguments}
        return self.json_rpc_request("tools/call", params)

    # Convenience methods for specific tools

    def create_campaign(self, user_id: str, title: str, **kwargs) -> dict[str, Any]:
        """Create a new campaign.

        Args:
            user_id: Firebase user ID
            title: Campaign title
            **kwargs: Additional campaign parameters

        Returns:
            Campaign creation result
        """
        arguments = {"user_id": user_id, "title": title}
        arguments.update(kwargs)
        return self.call_tool("create_campaign", arguments)

    def get_campaign_state(self, user_id: str, campaign_id: str) -> dict[str, Any]:
        """Get campaign state.

        Args:
            user_id: Firebase user ID
            campaign_id: Campaign identifier

        Returns:
            Campaign state data
        """
        return self.call_tool(
            "get_campaign_state", {"user_id": user_id, "campaign_id": campaign_id}
        )

    def process_action(
        self, user_id: str, campaign_id: str, user_input: str, mode: str = "character"
    ) -> dict[str, Any]:
        """Process user action in campaign.

        Args:
            user_id: Firebase user ID
            campaign_id: Campaign identifier
            user_input: User's action or dialogue
            mode: Interaction mode (character/narrator)

        Returns:
            Action processing result
        """
        return self.call_tool(
            "process_action",
            {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "user_input": user_input,
                "mode": mode,
            },
        )

    def update_campaign(
        self, user_id: str, campaign_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Update campaign metadata.

        Args:
            user_id: Firebase user ID
            campaign_id: Campaign identifier
            updates: Fields to update

        Returns:
            Update result
        """
        return self.call_tool(
            "update_campaign",
            {"user_id": user_id, "campaign_id": campaign_id, "updates": updates},
        )

    def export_campaign(
        self, user_id: str, campaign_id: str, format: str = "pdf"
    ) -> dict[str, Any]:
        """Export campaign to document format.

        Args:
            user_id: Firebase user ID
            campaign_id: Campaign identifier
            format: Export format (pdf/docx/txt)

        Returns:
            Export result
        """
        return self.call_tool(
            "export_campaign",
            {"user_id": user_id, "campaign_id": campaign_id, "format": format},
        )

    def get_campaigns_list(self, user_id: str) -> dict[str, Any]:
        """Get list of user campaigns.

        Args:
            user_id: Firebase user ID

        Returns:
            Campaigns list
        """
        return self.call_tool("get_campaigns_list", {"user_id": user_id})

    def get_user_settings(self, user_id: str) -> dict[str, Any]:
        """Get user settings.

        Args:
            user_id: Firebase user ID

        Returns:
            User settings
        """
        return self.call_tool("get_user_settings", {"user_id": user_id})

    def update_user_settings(
        self, user_id: str, settings: dict[str, Any]
    ) -> dict[str, Any]:
        """Update user settings.

        Args:
            user_id: Firebase user ID
            settings: Settings to update

        Returns:
            Update result
        """
        return self.call_tool(
            "update_user_settings", {"user_id": user_id, "settings": settings}
        )


class MCPTestSuite:
    """Test suite for comprehensive MCP server testing."""

    def __init__(self, client: MCPTestClient):
        """Initialize test suite.

        Args:
            client: MCP test client instance
        """
        self.client = client
        self.test_user_id = "test-user-123"
        self.results = []

    def run_test(self, test_name: str, test_func) -> bool:
        """Run individual test and record result.

        Args:
            test_name: Name of the test
            test_func: Test function to execute

        Returns:
            True if test passed, False otherwise
        """
        print(f"Running: {test_name}")
        try:
            test_func()
            print(f"✅ PASSED: {test_name}")
            self.results.append((test_name, "PASSED", None))
            return True
        except Exception as e:
            print(f"❌ FAILED: {test_name} - {str(e)}")
            self.results.append((test_name, "FAILED", str(e)))
            return False

    def test_health_check(self):
        """Test server health endpoint."""
        response = self.client.health_check()
        assert response.get("status") == "healthy"
        assert response.get("server") == "world-logic"

    def test_tools_list(self):
        """Test tools listing."""
        tools = self.client.list_tools()
        assert len(tools) >= 8  # Expected number of tools

        expected_tools = {
            "create_campaign",
            "get_campaign_state",
            "process_action",
            "update_campaign",
            "export_campaign",
            "get_campaigns_list",
            "get_user_settings",
            "update_user_settings",
        }

        actual_tools = {tool["name"] for tool in tools}
        missing_tools = expected_tools - actual_tools
        assert not missing_tools, f"Missing tools: {missing_tools}"

    def test_resources_list(self):
        """Test resources listing."""
        resources = self.client.list_resources()
        assert len(resources) >= 3  # Expected number of resources

        expected_uris = {
            "worldarchitect://campaigns",
            "worldarchitect://game-rules",
            "worldarchitect://prompts",
        }

        actual_uris = {resource["uri"] for resource in resources}
        missing_uris = expected_uris - actual_uris
        assert not missing_uris, f"Missing resource URIs: {missing_uris}"

    def test_resource_read(self):
        """Test resource reading."""
        content = self.client.read_resource("worldarchitect://game-rules")
        assert content and "D&D 5e" in content

    def test_campaign_workflow(self):
        """Test complete campaign workflow."""
        # Create campaign
        campaign_result = self.client.create_campaign(
            user_id=self.test_user_id,
            title="Test Campaign",
            character="Test character",
            setting="Test setting",
        )

        assert "result" in campaign_result
        # Note: Exact response structure may vary based on implementation

        # Get campaigns list
        campaigns_result = self.client.get_campaigns_list(self.test_user_id)
        assert "result" in campaigns_result

        # Note: For full integration testing, you would need actual campaign IDs
        # from the create_campaign response to test get_campaign_state, etc.

    def test_user_settings(self):
        """Test user settings functionality."""
        # Get settings
        settings_result = self.client.get_user_settings(self.test_user_id)
        assert "result" in settings_result

        # Update settings
        update_result = self.client.update_user_settings(
            self.test_user_id, {"theme": "dark", "auto_save": True}
        )
        assert "result" in update_result

    def test_error_handling(self):
        """Test error handling scenarios."""
        # Test invalid tool name
        try:
            self.client.call_tool("nonexistent_tool", {})
            # Should not raise exception but return error in response
        except requests.RequestException:
            pass  # Network errors are acceptable

        # Test missing required parameters
        try:
            self.client.create_campaign("", "")  # Empty parameters
            # Should not raise exception but return error in response
        except requests.RequestException:
            pass  # Network errors are acceptable

    def run_all_tests(self) -> dict[str, Any]:
        """Run all tests in the suite.

        Returns:
            Test results summary
        """
        print("Starting MCP Test Suite...")
        print("=" * 50)

        tests = [
            ("Health Check", self.test_health_check),
            ("Tools List", self.test_tools_list),
            ("Resources List", self.test_resources_list),
            ("Resource Read", self.test_resource_read),
            ("Campaign Workflow", self.test_campaign_workflow),
            ("User Settings", self.test_user_settings),
            ("Error Handling", self.test_error_handling),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1

        print("=" * 50)
        print(f"Test Results: {passed}/{total} passed")

        if passed == total:
            print("🎉 All tests passed!")
        else:
            print(f"❌ {total - passed} tests failed")

        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "results": self.results,
        }


def main():
    """Main test execution function."""
    parser = argparse.ArgumentParser(description="MCP Test Client")
    parser.add_argument(
        "--server", default="http://127.0.0.1:8000", help="MCP server URL"
    )
    parser.add_argument(
        "--test",
        choices=["health", "tools", "resources", "campaign", "settings", "all"],
        default="all",
        help="Test to run",
    )
    parser.add_argument(
        "--log-file", help="Path to JSON file for logging requests/responses"
    )

    args = parser.parse_args()

    client = MCPTestClient(args.server, log_file=args.log_file)

    try:
        # Test server connectivity
        print(f"Testing connection to {args.server}...")
        client.health_check()
        print("✅ Server is reachable")

        if args.test == "all":
            suite = MCPTestSuite(client)
            results = suite.run_all_tests()
            sys.exit(0 if results["failed"] == 0 else 1)
        else:
            # Run individual tests
            suite = MCPTestSuite(client)
            test_map = {
                "health": suite.test_health_check,
                "tools": suite.test_tools_list,
                "resources": suite.test_resources_list,
                "campaign": suite.test_campaign_workflow,
                "settings": suite.test_user_settings,
            }

            if args.test in test_map:
                suite.run_test(args.test, test_map[args.test])
            else:
                print(f"Unknown test: {args.test}")
                sys.exit(1)

    except requests.ConnectionError:
        print(f"❌ Cannot connect to server at {args.server}")
        print("Make sure the MCP server is running:")
        print("python3 mvp_site/mcp_api.py --host localhost --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
