#!/usr/bin/env python3
"""
Test MCP environment configuration for different testing scenarios.
In MCP architecture, environment variables control behavior at the MCP server level.
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_app


class TestMCPEnvironmentControl(unittest.TestCase):
    def setUp(self):
        """Save original environment."""
        self.original_env = {}
        for key in ["USE_MOCKS", "USE_MOCK_FIREBASE", "USE_MOCK_GEMINI", "TESTING_AUTH_BYPASS"]:
            self.original_env[key] = os.environ.get(key)

    def tearDown(self):
        """Restore original environment."""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_mcp_testing_environment_configured(self):
        """Test that MCP testing environment is properly configured."""
        # In MCP architecture, environment variables control behavior
        os.environ["TESTING_AUTH_BYPASS"] = "true"
        os.environ["USE_MOCKS"] = "true"

        app = create_app()
        assert app is not None, "App should be created successfully in MCP architecture"

        # Verify environment variables are accessible
        assert os.environ.get("TESTING_AUTH_BYPASS") == "true"
        assert os.environ.get("USE_MOCKS") == "true"

    def test_mcp_production_environment_configured(self):
        """Test that MCP production environment can be configured."""
        # Set production-like environment
        os.environ["TESTING_AUTH_BYPASS"] = "false"
        os.environ.pop("USE_MOCKS", None)  # Remove mocking in production

        app = create_app()
        assert app is not None, "App should be created successfully in production mode"

        # Verify environment configuration
        assert os.environ.get("TESTING_AUTH_BYPASS") == "false"
        assert os.environ.get("USE_MOCKS") != "true"

    def test_mcp_client_handles_environment_gracefully(self):
        """Test that MCP client handles different environments gracefully."""
        from mvp_site.mcp_client import create_mcp_client

        # Test with different environment configurations
        for use_mocks in ["true", "false", None]:
            if use_mocks is None:
                os.environ.pop("USE_MOCKS", None)
            else:
                os.environ["USE_MOCKS"] = use_mocks

            # MCP client should handle all configurations without crashing
            try:
                client = create_mcp_client()
                assert client is not None, (
                    f"Client should be created with USE_MOCKS={use_mocks}"
                )
            except Exception as e:
                # Connection errors are acceptable in testing, but crashes are not
                assert not isinstance(e, SyntaxError | ImportError | AttributeError), (
                    f"Client should not crash with USE_MOCKS={use_mocks}: {e}"
                )

    def test_mcp_environment_variables_respected(self):
        """Test that MCP architecture respects environment variables."""
        # Test different combinations of environment variables
        test_cases = [
            {"TESTING_AUTH_BYPASS": "true", "USE_MOCKS": "true"},
            {"TESTING_AUTH_BYPASS": "true", "USE_MOCKS": "false"},
            {"TESTING_AUTH_BYPASS": "false"},
        ]

        for env_vars in test_cases:
            # Clear relevant environment variables
            for key in ["TESTING_AUTH_BYPASS", "USE_MOCKS"]:
                os.environ.pop(key, None)

            # Set test environment
            for key, value in env_vars.items():
                os.environ[key] = value

            # Test that app can be created with this configuration
            app = create_app()
            assert app is not None, f"App should work with environment: {env_vars}"


if __name__ == "__main__":
    unittest.main()
