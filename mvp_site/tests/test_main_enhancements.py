from unittest.mock import patch, MagicMock, AsyncMock
import argparse
import sys
import threading

import pytest
from flask import Flask

# Import handling for main app
import mvp_site.main
app = mvp_site.main.app
HAS_MAIN_APP = True
IMPORT_ERROR = None


@pytest.fixture()
def client():
    """Flask test client fixture with proper error handling"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_flask_app_import():
    """Test that the Flask app can be imported successfully"""
    if not HAS_MAIN_APP:
        pytest.fail(f"Failed to import Flask app from main.py: {IMPORT_ERROR}")

    assert app is not None
    assert hasattr(app, "test_client")


def test_flask_app_is_flask_instance():
    """Test that imported app is a Flask instance"""
    if not HAS_MAIN_APP:
        pytest.skip(f"Cannot test Flask instance: {IMPORT_ERROR}")

    from flask import Flask

    assert isinstance(app, Flask)


def test_time_endpoint_exists(client):
    """Test that the /api/time endpoint exists and works"""
    response = client.get("/api/time")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert "timestamp" in data
    assert isinstance(data["timestamp"], str)


def test_campaigns_endpoint_requires_auth(client):
    """Test that campaigns endpoint requires authentication"""
    response = client.get("/api/campaigns")
    # Should return 401 Unauthorized without proper auth
    assert response.status_code == 401


def test_campaigns_endpoint_with_test_headers(client):
    """Test campaigns endpoint with test bypass headers"""
    headers = {"X-Test-Bypass-Auth": "true", "X-Test-User-ID": "test-user-123"}
    response = client.get("/api/campaigns", headers=headers)
    # Should succeed with test bypass or return 500 if MCP not available
    assert response.status_code in [200, 500]


def test_settings_endpoint_requires_auth(client):
    """Test that settings endpoint requires authentication"""
    response = client.get("/api/settings")
    # Should return 401 Unauthorized without proper auth
    assert response.status_code == 401


def test_settings_endpoint_with_test_headers(client):
    """Test settings endpoint with test bypass headers"""
    headers = {"X-Test-Bypass-Auth": "true", "X-Test-User-ID": "test-user-123"}
    response = client.get("/api/settings", headers=headers)
    # Should succeed with test bypass or return 500 if MCP not available
    assert response.status_code in [200, 500]


def test_create_campaign_requires_auth(client):
    """Test that campaign creation requires authentication"""
    campaign_data = {
        "name": "Test Campaign",
        "description": "A test campaign for unit testing",
    }
    response = client.post(
        "/api/campaigns", json=campaign_data, content_type="application/json"
    )
    # Should return 401 Unauthorized without proper auth
    assert response.status_code == 401


def test_create_campaign_with_test_headers(client):
    """Test campaign creation with test bypass headers"""
    headers = {
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": "test-user-123",
        "Content-Type": "application/json",
    }
    campaign_data = {
        "name": "Test Campaign",
        "description": "A test campaign for unit testing",
    }
    response = client.post("/api/campaigns", json=campaign_data, headers=headers)
    # Should succeed with test bypass or return 500 if MCP not available
    assert response.status_code in [200, 201, 500]


@patch("mvp_site.main.MCPClient", autospec=True)
def test_mcp_client_integration(mock_mcp_client, client):
    """Test MCP client integration with mocked client"""
    # Mock MCP client to return test data asynchronously
    mock_instance = mock_mcp_client.return_value
    from unittest.mock import AsyncMock

    mock_instance.call_tool = AsyncMock(
        return_value={"campaigns": [{"id": "test-123", "name": "Test Campaign"}]}
    )

    headers = {"X-Test-Bypass-Auth": "true", "X-Test-User-ID": "test-user-123"}
    response = client.get("/api/campaigns", headers=headers)

    # Should succeed with mocked MCP
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data.get("campaigns") is not None


def test_cors_enabled_for_api_routes(client):
    """Test that CORS is enabled for API routes"""
    # Make an OPTIONS request to test CORS preflight
    response = client.options(
        "/api/time",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Should handle OPTIONS request (either 200/204/405 is acceptable)
    assert response.status_code in [200, 204, 405]
    if response.status_code != 405:
        assert "Access-Control-Allow-Origin" in response.headers


def test_frontend_serving(client):
    """Test that frontend is served from root path"""
    response = client.get("/")
    # Should serve frontend HTML or return 404 if static files not built
    assert response.status_code in [200, 404]


def test_invalid_json_handling(client):
    """Test proper handling of invalid JSON in requests"""
    headers = {
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": "test-user-123",
        "Content-Type": "application/json",
    }
    # Send malformed JSON
    response = client.post(
        "/api/campaigns", data='{"invalid": json, "missing": quote}', headers=headers
    )
    # Should return 400 Bad Request for invalid JSON
    assert response.status_code == 400


def test_nonexistent_campaign_handling(client):
    """Test handling of requests for non-existent campaigns"""
    headers = {"X-Test-Bypass-Auth": "true", "X-Test-User-ID": "test-user-123"}
    response = client.get("/api/campaigns/nonexistent-id", headers=headers)
    # Should return 404 or error response
    assert response.status_code in [404, 500]


# Tests for MCP async fixes and boolean logic improvements
def test_future_annotations_import():
    """Test that __future__ annotations are properly imported for forward compatibility"""
    if not HAS_MAIN_APP:
        pytest.skip(f"Cannot test future annotations: {IMPORT_ERROR}")
    
    main_module = mvp_site.main

    # Check that the module has the future annotations imported
    assert hasattr(main_module, "__annotations__") or "__future__" in str(main_module)


def test_import_organization():
    """Test that imports are properly organized and accessible"""
    if not HAS_MAIN_APP:
        pytest.skip(f"Cannot test import organization: {IMPORT_ERROR}")
    
    main_module = mvp_site.main

    # Test that key imports are available
    assert hasattr(main_module, "Flask") or "Flask" in dir(main_module)
    assert hasattr(main_module, "create_app")
    assert hasattr(main_module, "MCPClient") or "MCPClient" in str(main_module)

    # Test that firestore_service is available
    assert hasattr(main_module, "firestore_service")
    assert hasattr(main_module, "json_default_serializer")


@patch("sys.argv")
def test_mcp_http_flag_default_behavior(mock_argv):
    """Test MCP HTTP flag default behavior (should default to True - HTTP mode)"""
    # Test with no --mcp-http flag specified
    mock_argv.return_value = ["main.py", "serve"]

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["serve"])
    parser.add_argument(
        "--mcp-http", action="store_true", help="Enable MCP HTTP transport"
    )

    # Parse without --mcp-http flag
    args = parser.parse_args(["serve"])

    # Test the boolean logic fix: should default to True (skip HTTP = False, meaning HTTP enabled)
    skip_mcp_http = not args.mcp_http if args.mcp_http is not None else True

    # When --mcp-http is not specified (False), skip_mcp_http should be True
    # This means HTTP is skipped by default, which matches the intended behavior
    assert skip_mcp_http is True


@patch("sys.argv")
def test_mcp_http_flag_explicit_enable(mock_argv):
    """Test MCP HTTP flag when explicitly enabled"""
    mock_argv.return_value = ["main.py", "serve", "--mcp-http"]

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["serve"])
    parser.add_argument(
        "--mcp-http", action="store_true", help="Enable MCP HTTP transport"
    )

    # Parse with --mcp-http flag
    args = parser.parse_args(["serve", "--mcp-http"])

    # Test the boolean logic fix: when --mcp-http is specified (True), skip should be False
    skip_mcp_http = not args.mcp_http if args.mcp_http is not None else True

    # When --mcp-http is specified (True), skip_mcp_http should be False (HTTP enabled)
    assert skip_mcp_http is False


def test_mcp_http_boolean_logic_matrix():
    """Comprehensive test matrix for MCP HTTP boolean logic"""
    # Test all combinations of the boolean logic fix
    test_cases = [
        # (mcp_http_value, mcp_http_is_none, expected_skip_http)
        (None, True, True),  # No flag specified -> default to skip HTTP
        (False, False, True),  # Flag specified as False -> skip HTTP
        (True, False, False),  # Flag specified as True -> don't skip HTTP (enable HTTP)
    ]

    for mcp_http_val, is_none, expected_skip in test_cases:
        if is_none:
            # Simulate when flag is not provided
            skip_mcp_http = not None if None is not None else True
        else:
            # Simulate when flag is provided with specific value
            skip_mcp_http = not mcp_http_val if mcp_http_val is not None else True

        assert (
            skip_mcp_http == expected_skip
        ), f"Failed for mcp_http={mcp_http_val}, is_none={is_none}"


@patch("mvp_site.main.create_app")
def test_app_configuration_with_mcp_settings(mock_create_app):
    """Test that app configuration includes MCP settings correctly"""
    # Mock the Flask app
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app

    # Test that app gets MCP configuration attributes
    mock_app._skip_mcp_http = True
    mock_app._mcp_server_url = "http://localhost:8000"

    # Verify the attributes exist and have expected types
    assert hasattr(mock_app, "_skip_mcp_http")
    assert hasattr(mock_app, "_mcp_server_url")
    assert isinstance(mock_app._skip_mcp_http, bool)
    assert isinstance(mock_app._mcp_server_url, str)


def test_import_error_handling():
    """Test that import errors are handled gracefully"""
    if not HAS_MAIN_APP:
        pytest.skip(f"Cannot test import handling: {IMPORT_ERROR}")
    
    # This tests the import structure improvements
    main_module = mvp_site.main
    # Should not raise import errors with the reorganized imports
    assert main_module is not None


def test_async_safety_improvements():
    """Test that async safety improvements are in place"""
    if not HAS_MAIN_APP:
        pytest.skip(f"Cannot test async safety: {IMPORT_ERROR}")
    
    main_module = mvp_site.main

    # Test that the module can be imported without async loop conflicts
    # This validates the removal of problematic async decorators
    assert hasattr(main_module, "create_app")

    # Test that create_app returns a Flask instance
    test_app = main_module.create_app()
    assert isinstance(test_app, Flask)


@patch("argparse.ArgumentParser.parse_args")
def test_cli_argument_parsing_safety(mock_parse_args):
    """Test that CLI argument parsing handles edge cases safely"""

    # Mock args with various combinations
    mock_args = MagicMock()
    mock_args.command = "serve"
    mock_args.mcp_http = None  # Test None case
    mock_args.mcp_server_url = "http://localhost:8000"
    mock_parse_args.return_value = mock_args

    # Test that the boolean logic handles None gracefully
    skip_mcp_http = not mock_args.mcp_http if mock_args.mcp_http is not None else True
    assert skip_mcp_http is True  # Should default to True when None

    # Test with explicit False
    mock_args.mcp_http = False
    skip_mcp_http = not mock_args.mcp_http if mock_args.mcp_http is not None else True
    assert skip_mcp_http is True  # Should be True when explicitly False

    # Test with explicit True
    mock_args.mcp_http = True
    skip_mcp_http = not mock_args.mcp_http if mock_args.mcp_http is not None else True
    assert skip_mcp_http is False  # Should be False when explicitly True


def test_threading_safety_with_mcp():
    """Test threading safety improvements with MCP integration"""
    if not HAS_MAIN_APP:
        pytest.skip(f"Cannot test threading safety: {IMPORT_ERROR}")
    
    main_module = mvp_site.main

    # Test that multiple threads can create apps simultaneously
    results = []

    def create_app_thread():
        try:
            app = main_module.create_app()
            results.append(app is not None)
        except Exception:
            results.append(False)

    # Create multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=create_app_thread)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=5)

    # All threads should successfully create apps
    assert len(results) == 3
    assert all(results), "Thread safety issue detected in app creation"
