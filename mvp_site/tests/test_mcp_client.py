#!/usr/bin/env python3
"""
Comprehensive unit tests for MCP client functionality.
Tests the new async-to-sync bridging, event loop management, timeout protection,
and enhanced JSON handling introduced in PR #1453.
"""

import asyncio
import concurrent.futures
import json
import threading
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import requests
from flask import Flask, request

# Import the module under test using package namespace
from mvp_site.mcp_client import (
    MCPClient,
    MCPClientError,
    MCPError,
    MCPErrorCode,
    http_to_mcp_request,
    mcp_to_http_response,
)


class TestMCPClient(unittest.TestCase):
    """Test cases for MCPClient class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "http://localhost:8000"
        self.client = MCPClient(self.base_url, timeout=30)
        
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.client, 'session') and self.client.session:
            self.client.session.close()

    def test_init_validation(self):
        """Test MCPClient initialization and input validation."""
        # Test valid initialization
        client = MCPClient("http://localhost:8000", timeout=60)
        self.assertEqual(client.base_url, "http://localhost:8000")
        self.assertEqual(client.timeout, 60)
        self.assertFalse(client.skip_http)
        
        # Test URL normalization (trailing slash removal)
        client = MCPClient("http://localhost:8000/", timeout=30)
        self.assertEqual(client.base_url, "http://localhost:8000")
        
        # Test invalid inputs
        with self.assertRaises(ValueError):
            MCPClient("", timeout=30)  # Empty URL
            
        with self.assertRaises(ValueError):
            MCPClient("http://localhost:8000", timeout=0)  # Invalid timeout
            
        with self.assertRaises(ValueError):
            MCPClient("http://localhost:8000", timeout=-1)  # Negative timeout

    def test_skip_http_mode(self):
        """Test direct world_logic mode (skip_http=True)."""
        mock_world_logic = MagicMock()
        client = MCPClient(skip_http=True, world_logic_module=mock_world_logic)
        
        self.assertTrue(client.skip_http)
        self.assertIsNone(client.session)
        self.assertEqual(client.world_logic, mock_world_logic)

    def test_request_id_generation(self):
        """Test unique request ID generation."""
        id1 = self.client._generate_request_id()
        id2 = self.client._generate_request_id()
        
        self.assertIsInstance(id1, str)
        self.assertIsInstance(id2, str)
        self.assertNotEqual(id1, id2)
        # Basic UUID format check
        self.assertTrue(len(id1.replace('-', '')) == 32)

    def test_jsonrpc_request_creation(self):
        """Test JSON-RPC request payload creation."""
        # Test without parameters
        request = self.client._make_jsonrpc_request("test_method")
        self.assertEqual(request["jsonrpc"], "2.0")
        self.assertEqual(request["method"], "test_method")
        self.assertIn("id", request)
        self.assertNotIn("params", request)
        
        # Test with parameters
        params = {"arg1": "value1", "arg2": 42}
        request = self.client._make_jsonrpc_request("test_method", params)
        self.assertEqual(request["params"], params)

    def test_jsonrpc_response_handling_success(self):
        """Test successful JSON-RPC response handling."""
        response = {
            "jsonrpc": "2.0",
            "result": {"data": "success"},
            "id": "test-id"
        }
        
        result = self.client._handle_jsonrpc_response(response)
        self.assertEqual(result, {"data": "success"})

    def test_jsonrpc_response_handling_error(self):
        """Test JSON-RPC error response handling."""
        response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": "Method not found",
                "data": {"detail": "test"}
            },
            "id": "test-id"
        }
        
        with self.assertRaises(MCPClientError) as context:
            self.client._handle_jsonrpc_response(response)
            
        error = context.exception
        self.assertEqual(error.error_code, -32601)
        self.assertEqual(str(error), "Method not found")
        self.assertEqual(error.data, {"detail": "test"})

    @patch('mvp_site.mcp_client.requests.Session')
    def test_call_tool_success(self, mock_session_class):
        """Test successful async tool call."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"campaign_id": "test-123"},
            "id": "test-id"
        }
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Create client with mocked session
        client = MCPClient(self.base_url, timeout=30)
        client.session = mock_session
        
        # Run async call in event loop
        result = asyncio.run(client.call_tool("create_campaign", {"name": "Test"}))
        
        self.assertEqual(result, {"campaign_id": "test-123"})
        mock_session.post.assert_called_once()

    @patch('mvp_site.mcp_client.requests.Session')
    def test_call_tool_http_error(self, mock_session_class):
        """Test tool call with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = MCPClient(self.base_url, timeout=30)
        client.session = mock_session
        
        with self.assertRaises(MCPClientError) as context:
            asyncio.run(client.call_tool("test_tool", {}))
            
        error = context.exception
        # HTTP error status code should propagate through MCPClientError
        self.assertIn("HTTP error 500", str(error))
        self.assertEqual(error.error_code, 500)

    @patch('mvp_site.mcp_client.requests.Session')
    def test_call_tool_connection_error(self, mock_session_class):
        """Test tool call with connection error."""
        mock_session = Mock()
        mock_session.post.side_effect = requests.ConnectionError("Connection refused")
        mock_session_class.return_value = mock_session
        
        client = MCPClient(self.base_url, timeout=30)
        client.session = mock_session
        
        with self.assertRaises(MCPClientError) as context:
            asyncio.run(client.call_tool("test_tool", {}))
            
        self.assertIn("Connection error", str(context.exception))

    @patch('mvp_site.mcp_client.requests.Session')
    def test_call_tool_invalid_json(self, mock_session_class):
        """Test tool call with invalid JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = MCPClient(self.base_url, timeout=30)
        client.session = mock_session
        
        with self.assertRaises(MCPClientError) as context:
            asyncio.run(client.call_tool("test_tool", {}))
            
        self.assertIn("Invalid JSON response", str(context.exception))


class TestSharedEventLoop(unittest.TestCase):
    """Test cases for shared event loop management."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset class-level shared event loop state
        MCPClient._shared_event_loop = None
        MCPClient._loop_thread = None

    def tearDown(self):
        """Clean up shared event loop."""
        if MCPClient._shared_event_loop and not MCPClient._shared_event_loop.is_closed():
            MCPClient._shared_event_loop.call_soon_threadsafe(MCPClient._shared_event_loop.stop)
            time.sleep(0.1)  # Allow loop to stop
        MCPClient._shared_event_loop = None
        # Join background loop thread to ensure full teardown
        if MCPClient._loop_thread and MCPClient._loop_thread.is_alive():
            MCPClient._loop_thread.join(timeout=1)
        MCPClient._loop_thread = None

    def test_shared_event_loop_creation(self):
        """Test shared event loop creation and thread management."""
        # First call should create loop and thread
        loop1 = MCPClient._get_shared_event_loop()
        
        self.assertIsInstance(loop1, asyncio.AbstractEventLoop)
        self.assertFalse(loop1.is_closed())
        self.assertIsNotNone(MCPClient._loop_thread)
        self.assertTrue(MCPClient._loop_thread.is_alive())
        self.assertEqual(MCPClient._loop_thread.name, "MCP-EventLoop")
        
        # Second call should return same loop
        loop2 = MCPClient._get_shared_event_loop()
        self.assertIs(loop1, loop2)

    def test_shared_event_loop_thread_safety(self):
        """Test thread-safe access to shared event loop."""
        loops = []
        threads = []
        
        def get_loop():
            loops.append(MCPClient._get_shared_event_loop())
        
        # Create multiple threads accessing shared loop simultaneously
        for _ in range(5):
            thread = threading.Thread(target=get_loop)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)
        
        # All threads should get the same loop instance
        self.assertEqual(len(loops), 5)
        for loop in loops:
            self.assertIs(loop, loops[0])

    @patch('mvp_site.mcp_client.MCPClient.call_tool')
    def test_call_tool_sync_no_running_loop(self, mock_call_tool):
        """Test sync tool call when no event loop is running."""
        async def mock_async_call():
            return {"result": "success"}
        mock_call_tool.return_value = mock_async_call()
        
        client = MCPClient("http://localhost:8000", timeout=30)
        
        # This should work without an active event loop
        result = client.call_tool_sync("test_tool", {"arg": "value"})
        
        mock_call_tool.assert_called_once_with("test_tool", {"arg": "value"})
        self.assertEqual(result, {"result": "success"})

    @patch('mvp_site.mcp_client.MCPClient.call_tool')
    def test_call_tool_sync_with_running_loop_same(self, mock_call_tool):
        """Test sync tool call when already in the same event loop."""
        async def run_test():
            async def mock_async_call():
                return {"result": "success"}
            mock_call_tool.return_value = mock_async_call()
            
            client = MCPClient("http://localhost:8000", timeout=30)
            
            # Mock to make shared loop appear as current loop
            with patch.object(MCPClient, '_get_shared_event_loop', return_value=asyncio.get_running_loop()):
                
                result = client.call_tool_sync("test_tool", {"arg": "value"})
                
                mock_call_tool.assert_called_once_with("test_tool", {"arg": "value"})
        
        asyncio.run(run_test())

    @patch('mvp_site.mcp_client.MCPClient.call_tool')
    def test_call_tool_sync_with_different_loop(self, mock_call_tool):
        """Test sync tool call with different event loop running."""
        async def run_test():
            async def mock_async_call():
                return {"result": "success"}
            mock_call_tool.return_value = mock_async_call()
            
            client = MCPClient("http://localhost:8000", timeout=30)
            
            # Ensure shared loop is different from current
            shared_loop = MCPClient._get_shared_event_loop()
            current_loop = asyncio.get_running_loop()
            self.assertIsNot(shared_loop, current_loop)
            
            result = client.call_tool_sync("test_tool", {"arg": "value"})
            
            mock_call_tool.assert_called_once_with("test_tool", {"arg": "value"})
        
        asyncio.run(run_test())

    @patch('mvp_site.mcp_client.MCPClient.get_resource')
    def test_get_resource_sync_no_running_loop(self, mock_get_resource):
        """Test sync resource get when no event loop is running."""
        async def mock_async_get():
            return "resource_content"
        mock_get_resource.return_value = mock_async_get()
        
        client = MCPClient("http://localhost:8000", timeout=30)
        
        result = client.get_resource_sync("test://resource")
        
        mock_get_resource.assert_called_once_with("test://resource")

    @patch('mvp_site.mcp_client.MCPClient.get_resource')
    def test_get_resource_sync_with_running_loop(self, mock_get_resource):
        """Test sync resource get when event loop is already running."""
        async def run_test():
            async def mock_async_get():
                return "resource_content"
            mock_get_resource.return_value = mock_async_get()
            
            client = MCPClient("http://localhost:8000", timeout=30)
            
            result = client.get_resource_sync("test://resource")
            
            mock_get_resource.assert_called_once_with("test://resource")
        
        asyncio.run(run_test())


class TestTimeoutProtection(unittest.TestCase):
    """Test cases for timeout protection in future.result() calls."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = MCPClient("http://localhost:8000", timeout=5)  # Short timeout for testing

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.client, 'session') and self.client.session:
            self.client.session.close()
        # Clean up shared event loop
        if MCPClient._shared_event_loop and not MCPClient._shared_event_loop.is_closed():
            MCPClient._shared_event_loop.call_soon_threadsafe(MCPClient._shared_event_loop.stop)
            time.sleep(0.1)
        MCPClient._shared_event_loop = None
        MCPClient._loop_thread = None

    def test_sync_call_timeout_protection(self):
        """Test that sync calls use timeout protection on future.result()."""
        # This test verifies the timeout mechanism is in place
        # Mock the actual timeout behavior since we can't easily test real timeouts
        with patch('concurrent.futures.Future.result') as mock_result:
            mock_result.side_effect = concurrent.futures.TimeoutError()
            
            with self.assertRaises(concurrent.futures.TimeoutError):
                self.client.call_tool_sync("test_tool", {})

    def test_resource_sync_timeout_protection(self):
        """Test that sync resource calls use timeout protection."""
        # This test verifies the timeout mechanism is in place
        # Mock the actual timeout behavior since we can't easily test real timeouts
        with patch('concurrent.futures.Future.result') as mock_result:
            mock_result.side_effect = concurrent.futures.TimeoutError()
            
            with self.assertRaises(concurrent.futures.TimeoutError):
                self.client.get_resource_sync("test://resource")


class TestJSONHandling(unittest.TestCase):
    """Test cases for enhanced JSON body handling."""

    def test_http_to_mcp_request_empty_json_objects(self):
        """Test that empty JSON objects/arrays are preserved."""
        # Flask imports moved to module top-level
        
        app = Flask(__name__)
        
        # Test empty object
        with app.test_request_context('/', method='POST', 
                                    json={}, 
                                    content_type='application/json'):
            result = http_to_mcp_request(request, "test_tool")
            # Empty object should be preserved, plus HTTP metadata and headers
            self.assertIn("_http_method", result)
            self.assertIn("_http_path", result) 
            self.assertIn("_http_headers", result)
            self.assertEqual(result["_http_method"], "POST")
        
        # Test empty array - Note: Flask typically expects JSON objects for form-style processing
        with app.test_request_context('/', method='POST',
                                    data='[]',
                                    content_type='application/json'):
            request_obj = request
            # Manually set JSON to array for testing
            with patch.object(request_obj, 'get_json', return_value=[]):
                result = http_to_mcp_request(request_obj, "test_tool")
                # Empty array should not be processed by update() but should not crash
                self.assertIn("_http_method", result)

    def test_http_to_mcp_request_falsy_values(self):
        """Test that falsy but valid JSON values are handled correctly."""
        # Flask imports moved to module top-level
        
        app = Flask(__name__)
        
        # Test with falsy but valid values
        with app.test_request_context('/', method='POST',
                                    json={"count": 0, "enabled": False, "message": ""},
                                    content_type='application/json'):
            result = http_to_mcp_request(request, "test_tool")
            
            self.assertEqual(result["count"], 0)
            self.assertEqual(result["enabled"], False)
            self.assertEqual(result["message"], "")

    def test_http_to_mcp_request_none_body(self):
        """Test that None JSON body is filtered out correctly."""
        # Flask imports moved to module top-level
        
        app = Flask(__name__)
        
        with app.test_request_context('/', method='POST', content_type='application/json'):
            # Mock get_json to return None
            with patch.object(request, 'get_json', return_value=None):
                result = http_to_mcp_request(request, "test_tool")
                
                # Should only contain HTTP metadata, no body data
                # Note: will also include _http_headers with content-type
                expected_keys = {"_http_method", "_http_path", "_http_headers"}
                self.assertTrue(expected_keys.issubset(set(result.keys())))

    def test_http_to_mcp_request_security(self):
        """Test that sensitive headers are properly masked in logging."""
        # Flask imports moved to module top-level
        
        app = Flask(__name__)
        
        with app.test_request_context('/', method='POST',
                                    headers={'Authorization': 'Bearer secret-token'},
                                    json={"test": "data"}):
            
            # Capture log output to verify masking
            with patch('mvp_site.mcp_client.logger') as mock_logger:
                result = http_to_mcp_request(request, "test_tool")
                
                # Verify actual result has real auth header
                self.assertEqual(result["_http_headers"]["authorization"], "Bearer secret-token")
                
                # Verify logged version has masked auth header
                mock_logger.debug.assert_called()
                args, kwargs = mock_logger.debug.call_args
                payload_str = " ".join(map(str, args)) + " " + " ".join(f"{k}={v}" for k, v in kwargs.items())
                self.assertIn("***MASKED***", payload_str)
                self.assertNotIn("secret-token", payload_str)

    def test_mcp_to_http_response_json_serialization(self):
        """Test MCP result to HTTP response conversion."""
        # Test dict result
        result = {"campaign_id": "test-123", "status": "created"}
        response = mcp_to_http_response(result, 201)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data, result)
        
        # Test string result - should be wrapped in {"result": ...}
        result = "Simple string response"
        response = mcp_to_http_response(result)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data, {"result": result})


class TestContextManager(unittest.TestCase):
    """Test cases for context manager functionality."""

    @patch('mvp_site.mcp_client.requests.Session')
    def test_context_manager_usage(self, mock_session_class):
        """Test MCPClient as context manager."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        with MCPClient("http://localhost:8000") as client:
            self.assertIsNotNone(client.session)
        
        # Session should be closed after exiting context
        mock_session.close.assert_called_once()

    def test_context_manager_exception_handling(self):
        """Test context manager cleanup on exceptions."""
        mock_session = Mock()
        
        try:
            with MCPClient("http://localhost:8000") as client:
                client.session = mock_session
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Session should still be closed even with exception
        mock_session.close.assert_called_once()


class TestErrorHandling(unittest.TestCase):
    """Test cases for comprehensive error handling."""

    def test_mcp_error_creation(self):
        """Test MCPError dataclass creation."""
        error = MCPError(
            code=MCPErrorCode.INVALID_PARAMS.value,
            message="Invalid parameters",
            data={"param": "user_id"}
        )
        
        self.assertEqual(error.code, -32602)
        self.assertEqual(error.message, "Invalid parameters")
        self.assertEqual(error.data, {"param": "user_id"})

    def test_mcp_client_error_creation(self):
        """Test MCPClientError exception creation."""
        error = MCPClientError(
            "Test error message",
            error_code=-32601,
            data={"details": "method not found"}
        )
        
        self.assertEqual(str(error), "Test error message")
        self.assertEqual(error.error_code, -32601)
        self.assertEqual(error.data, {"details": "method not found"})

    def test_error_codes_enum(self):
        """Test MCP error codes enum."""
        self.assertEqual(MCPErrorCode.PARSE_ERROR.value, -32700)
        self.assertEqual(MCPErrorCode.INVALID_REQUEST.value, -32600)
        self.assertEqual(MCPErrorCode.METHOD_NOT_FOUND.value, -32601)
        self.assertEqual(MCPErrorCode.INVALID_PARAMS.value, -32602)
        self.assertEqual(MCPErrorCode.INTERNAL_ERROR.value, -32603)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)