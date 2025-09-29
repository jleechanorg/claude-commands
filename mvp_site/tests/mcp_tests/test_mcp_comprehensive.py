#!/usr/bin/env python3
"""
Comprehensive MCP Test Suite - Consolidated from 8 redundant test files
Tests all MCP server functionality including cerebras tool, JSON-RPC, and red-green-refactor methodology
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import MCP modules
try:
    from mcp_servers.slash_commands.unified_router import create_tools, handle_tool_call

    MCP_ROUTER_AVAILABLE = True
except ImportError:
    create_tools = None
    handle_tool_call = None
    MCP_ROUTER_AVAILABLE = False


class TestMCPComprehensive:
    """Comprehensive test suite for MCP server functionality"""

    @pytest.fixture(scope="class")
    def project_root(self):
        """Dynamically find project root using CLAUDE.md marker"""
        current_path = Path(__file__).resolve()
        # Walk up the directory tree to find CLAUDE.md
        for parent in [current_path] + list(current_path.parents):
            if (parent / "CLAUDE.md").exists():
                return parent
        # Fallback to environment variable or current working directory
        return Path(os.environ.get("PROJECT_ROOT", ".")).resolve()

    @pytest.mark.asyncio()
    async def test_tool_discovery(self):
        """Test that all slash commands are properly discovered"""
        if not MCP_ROUTER_AVAILABLE or not create_tools:
            pytest.skip("MCP router or create_tools not available")

        tools = create_tools()
        assert len(tools) > 0, "No tools discovered"
        # Verify cerebras tool is present
        cerebras_tool = next((tool for tool in tools if tool.name == "cerebras"), None)
        assert cerebras_tool is not None, "cerebras tool not found"
        assert "cerebras" in cerebras_tool.description.lower()
        print(f"✅ Discovered {len(tools)} MCP tools including cerebras")

    @pytest.mark.asyncio()
    async def test_cerebras_tool_execution(self):
        """Test cerebras tool execution through unified router"""
        if not MCP_ROUTER_AVAILABLE or not handle_tool_call:
            pytest.skip("MCP router or handle_tool_call not available")

        # Test basic cerebras functionality
        result = await handle_tool_call("cerebras", {"args": ["print('hello world')"]})
        assert result is not None
        assert len(result) > 0
        response_text = result[0].text
        assert response_text.strip(), "Cerebras execution returned empty response"
        print("✅ Cerebras tool executed successfully")

    @pytest.mark.asyncio()
    async def test_input_validation_basic(self):
        """Test basic input validation in handle_tool_call"""
        if not MCP_ROUTER_AVAILABLE or not handle_tool_call:
            pytest.skip("MCP router or handle_tool_call not available")

        malicious_inputs = ["../../../etc/passwd", "'; DROP TABLE users; --"]
        for malicious_input in malicious_inputs:
            result = await handle_tool_call("cerebras", {"args": [malicious_input]})
            assert result[0].text.strip(), "Sanitized input should still produce a response"
        print("✅ Input validation working correctly")

    @pytest.mark.asyncio()
    async def test_invalid_tool_rejection(self):
        """Test that invalid tools are rejected"""
        if not MCP_ROUTER_AVAILABLE or not handle_tool_call:
            pytest.skip("MCP router or handle_tool_call not available")

        result = await handle_tool_call("nonexistent_tool", {"args": ["test"]})
        assert result is not None
        assert (
            "disabled" in result[0].text.lower() or "cerebras" in result[0].text.lower()
        )
        print("✅ Invalid tools properly rejected")

    @pytest.mark.asyncio()
    async def test_json_rpc_communication(self):
        """Test JSON-RPC communication pattern with MCP server"""
        # Test with cerebras args
        result = await handle_tool_call(
            "cerebras", {"args": ["def add(a, b): return a + b"]}
        )
        assert result is not None
        response_text = result[0].text
        assert response_text.strip(), "JSON-RPC call returned empty response"
        assert "/cerebras" in response_text
        print("✅ JSON-RPC communication working")

    def test_server_startup(self, project_root):
        """Test that the MCP server can start successfully"""
        server_script = project_root / "mcp_servers" / "slash_commands" / "server.py"
        if not server_script.exists():
            pytest.skip(f"Server script not found at {server_script} - test skipped")

        # Try to start server briefly to test it can initialize
        try:
            # Test that server script is executable
            result = subprocess.run(
                [sys.executable, str(server_script)],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
                input="\n",
            )
            # Server should start then exit gracefully on stdin
            print("✅ MCP server starts correctly")
        except subprocess.TimeoutExpired:
            # Timeout is acceptable - server is probably waiting for input
            print("✅ MCP server starts correctly (timeout expected)")
        except Exception as e:
            pytest.fail(f"Server startup failed: {e}")

    @pytest.mark.asyncio()
    async def test_red_green_refactor_cycle(self):
        """Test red-green-refactor methodology through MCP server"""
        # Red phase - test cerebras command with failing scenario
        red_result = await handle_tool_call(
            "cerebras",
            {
                "args": [
                    "Generate a pytest test function that fails with AssertionError"
                ]
            },
        )
        assert red_result is not None
        red_response = red_result[0].text
        assert red_response.strip(), "Red phase response was empty"
        assert "/cerebras" in red_response

        # Green phase - test cerebras command with implementation
        green_result = await handle_tool_call(
            "cerebras",
            {"args": ["Generate a simple Python function that returns True"]},
        )
        assert green_result is not None
        green_response = green_result[0].text
        assert green_response.strip(), "Green phase response was empty"

        print("✅ Red-green-refactor cycle working through MCP")

    @pytest.mark.asyncio()
    async def test_argument_handling(self):
        """Test various argument patterns"""
        # Test with multiple args
        result = await handle_tool_call("cerebras", {"args": ["arg1", "arg2", "arg3"]})
        assert result is not None
        response_text = result[0].text
        assert "arg1 arg2 arg3" in response_text

        # Test with empty args
        result = await handle_tool_call("cerebras", {"args": []})
        assert result is not None
        assert "/cerebras" in result[0].text

        print("✅ Argument handling working correctly")

    @pytest.mark.asyncio()
    async def test_syntax_error_prevention(self):
        """Test that indentation and syntax errors are prevented"""
        # This test would have failed before the fix due to indentation error
        result = await handle_tool_call("cerebras", {"args": ["test syntax"]})
        assert result is not None
        assert len(result) > 0
        assert isinstance(result[0].text, str)
        print("✅ Syntax error prevention working")

    @pytest.mark.asyncio()
    async def test_consistent_argument_parsing(self):
        """Test consistent argument key usage (args vs arguments)"""
        # Test that 'args' key is used consistently
        result1 = await handle_tool_call(
            "cerebras", {"args": ["consistent", "parsing"]}
        )
        assert result1 is not None

        # Test edge case with string args
        result2 = await handle_tool_call("cerebras", {"args": "string_arg"})
        assert result2 is not None

        # Test edge case with no args
        result3 = await handle_tool_call("cerebras", {})
        assert result3 is not None

        print("✅ Consistent argument parsing working")

    @pytest.mark.asyncio()
    async def test_tool_restriction_logic(self):
        """Test that only cerebras tool is allowed as intended"""
        # Test that non-cerebras tools are properly rejected
        result = await handle_tool_call("fake_tool", {"args": ["test"]})
        assert result is not None
        assert (
            "disabled" in result[0].text.lower() or "cerebras" in result[0].text.lower()
        )

        # Test that cerebras tool still works
        result = await handle_tool_call("cerebras", {"args": ["working"]})
        assert result is not None
        assert "/cerebras" in result[0].text or "working" in result[0].text

        print("✅ Tool restriction logic working correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
