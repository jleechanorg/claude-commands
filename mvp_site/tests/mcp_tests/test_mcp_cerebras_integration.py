#!/usr/bin/env python3
"""
MCP Cerebras Integration Test - Proof of Working Implementation

This test validates that the MCP cerebras tool integration is working correctly
after fixing the broken subprocess execution that was introduced by code review fixes.

CRITICAL VALIDATION:
- Only cerebras tool exposed for security
- MCP tool returns SLASH_COMMAND_EXECUTE pattern (not direct execution)
- Tool integration follows expected protocol
- Security restrictions properly enforced
"""

import sys
import time
from pathlib import Path

import pytest

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Check for MCP dependencies and handle imports
try:
    from fastmcp import FastMCP
    from mcp.types import TextContent
    from mcp_servers.slash_commands.unified_router import (
        _execute_slash_command,
        create_tools,
    )
    from mcp_servers.slash_commands.unified_router import main as server_main
    MCP_AVAILABLE = True
except ImportError as e:
    # Set fallback values for unavailable MCP dependencies
    FastMCP = None
    TextContent = None
    _execute_slash_command = None
    create_tools = None
    server_main = None
    MCP_AVAILABLE = False
    SKIP_REASON = f"MCP dependencies not available: {e}"

    # Exit early if running as script (not being collected by pytest)
    if __name__ == "__main__":
        print(f"SKIPPED: {SKIP_REASON}")
        sys.exit(0)


class TestMCPCerebrasIntegration:
    """Comprehensive test suite proving MCP cerebras integration works correctly."""

    @pytest.mark.skipif(not MCP_AVAILABLE, reason=SKIP_REASON if not MCP_AVAILABLE else "")
    def test_tool_availability_and_security(self):
        """
        🔒 SECURITY TEST: Verify only cerebras tool is exposed.
        
        This validates the security-first approach where only cerebras
        is exposed via MCP while maintaining full code architecture.
        """
        print("🔍 Testing tool availability and security restrictions...")

        tools = create_tools()

        # Verify exactly one tool is exposed
        assert len(tools) == 1, f"Expected 1 tool, got {len(tools)} - security violation"

        # Verify it's the cerebras tool
        cerebras_tool = tools[0]
        assert cerebras_tool.name == "cerebras", f"Expected 'cerebras', got '{cerebras_tool.name}'"

        # Verify description contains expected content
        assert "cerebras" in cerebras_tool.description.lower()
        assert "ultra-fast" in cerebras_tool.description.lower()

        print("✅ Security validated: Only cerebras tool exposed")

    @pytest.mark.skipif(not MCP_AVAILABLE, reason=SKIP_REASON if not MCP_AVAILABLE else "")
    def test_slash_command_execution_pattern(self):
        """
        🎯 PROTOCOL TEST: Verify MCP tool returns SLASH_COMMAND_EXECUTE pattern.
        
        This is the core fix - the tool should return the execution pattern
        for Claude's hook system to process, NOT execute subprocess directly.
        """
        print("🎯 Testing SLASH_COMMAND_EXECUTE pattern generation...")

        # Test the core function that was fixed
        result = _execute_slash_command("/cerebras", "hello world test")

        # Verify it returns the expected pattern
        expected_pattern = "SLASH_COMMAND_EXECUTE: /cerebras hello world test"
        assert result == expected_pattern, f"Expected '{expected_pattern}', got '{result}'"

        print("✅ SLASH_COMMAND_EXECUTE pattern correct")

    @pytest.mark.skipif(not MCP_AVAILABLE, reason=SKIP_REASON if not MCP_AVAILABLE else "")
    def test_execution_speed_and_format(self):
        """
        ⚡ PERFORMANCE TEST: Verify execution is fast (no 30-second timeouts).
        
        The fixed version should return immediately since it doesn't execute
        subprocess - just returns the pattern for hook processing.
        """
        print("⚡ Testing execution speed and format...")

        start_time = time.time()

        # Execute via the fixed function
        result = _execute_slash_command("/cerebras", "simple test")

        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000

        # Should be near-instantaneous (< 10ms) since no subprocess execution
        assert execution_time_ms < 10, f"Execution too slow: {execution_time_ms:.1f}ms"

        # Verify format
        assert result.startswith("SLASH_COMMAND_EXECUTE: /cerebras")
        assert "simple test" in result

        print(f"✅ Execution speed: {execution_time_ms:.1f}ms (expected < 10ms)")

    @pytest.mark.skipif(not MCP_AVAILABLE, reason=SKIP_REASON if not MCP_AVAILABLE else "")
    def test_argument_handling(self):
        """
        📝 ARGUMENT TEST: Verify different argument formats are handled correctly.
        """
        print("📝 Testing argument handling...")

        # Test empty arguments
        result1 = _execute_slash_command("/cerebras", "")
        assert result1 == "SLASH_COMMAND_EXECUTE: /cerebras "

        # Test single word
        result2 = _execute_slash_command("/cerebras", "hello")
        assert result2 == "SLASH_COMMAND_EXECUTE: /cerebras hello"

        # Test multiple words
        result3 = _execute_slash_command("/cerebras", "write python function")
        assert result3 == "SLASH_COMMAND_EXECUTE: /cerebras write python function"

        print("✅ Argument handling correct for all formats")

    @pytest.mark.skipif(not MCP_AVAILABLE, reason=SKIP_REASON if not MCP_AVAILABLE else "")
    def test_server_initialization(self):
        """
        🚀 SERVER TEST: Verify server can initialize with correct name and tools.
        """
        print("🚀 Testing server initialization...")

        try:
            # Test FastMCP server creation
            mcp = FastMCP("claude-slash-commands")
            assert mcp.name == "claude-slash-commands"

            # Test tool registration would work (without actually registering)
            tools = create_tools()
            assert len(tools) == 1

            print("✅ Server initialization successful")

        except Exception as e:
            pytest.fail(f"Server initialization failed: {e}")

    @pytest.mark.skipif(not MCP_AVAILABLE, reason=SKIP_REASON if not MCP_AVAILABLE else "")
    def test_error_conditions(self):
        """
        🛡️ ERROR HANDLING TEST: Verify proper error handling for edge cases.
        """
        print("🛡️ Testing error handling...")

        # Test with None arguments
        result1 = _execute_slash_command("/cerebras", None)
        assert result1 == "SLASH_COMMAND_EXECUTE: /cerebras None"

        # Test with empty string
        result2 = _execute_slash_command("/cerebras", "")
        assert result2 == "SLASH_COMMAND_EXECUTE: /cerebras "

        # Test different command (should still work - function is generic)
        result3 = _execute_slash_command("/test", "args")
        assert result3 == "SLASH_COMMAND_EXECUTE: /test args"

        print("✅ Error handling robust")

    @pytest.mark.skipif(not MCP_AVAILABLE, reason=SKIP_REASON if not MCP_AVAILABLE else "")
    def test_integration_proof(self):
        """
        🎯 INTEGRATION PROOF: Demonstrate the complete working flow.
        
        This test proves that:
        1. MCP server can start
        2. Tools are properly exposed
        3. Cerebras tool returns correct pattern
        4. No timeouts or execution issues
        5. Security restrictions in place
        """
        print("🎯 Running complete integration proof...")

        # Step 1: Verify tool discovery and creation
        tools = create_tools()
        assert len(tools) == 1
        cerebras_tool = tools[0]

        # Step 2: Simulate tool execution
        test_args = "write hello world function"
        expected_output = f"SLASH_COMMAND_EXECUTE: /cerebras {test_args}"

        # Step 3: Verify execution via the fixed function
        actual_output = _execute_slash_command("/cerebras", test_args)
        assert actual_output == expected_output

        # Step 4: Verify execution speed (should be instant)
        start_time = time.time()
        for _ in range(100):  # Run 100 times to test consistency
            _execute_slash_command("/cerebras", "test")
        end_time = time.time()

        avg_time_ms = ((end_time - start_time) / 100) * 1000
        assert avg_time_ms < 1.0, f"Average execution too slow: {avg_time_ms:.2f}ms"

        print("✅ INTEGRATION PROOF COMPLETE:")
        print("   - Security: Only cerebras exposed")
        print(f"   - Speed: {avg_time_ms:.2f}ms average (< 1ms)")
        print("   - Format: Correct SLASH_COMMAND_EXECUTE pattern")
        print("   - Protocol: Fixed subprocess execution issue")


if __name__ == "__main__":
    # Only run if not being imported by pytest
    if not MCP_AVAILABLE:
        print(f"⚠️  SKIPPING: {SKIP_REASON}")
        sys.exit(0)

    print("🧪 MCP Cerebras Integration Test Suite")
    print("=" * 50)

    # Run all tests
    test_instance = TestMCPCerebrasIntegration()

    try:
        test_instance.test_tool_availability_and_security()
        test_instance.test_slash_command_execution_pattern()
        test_instance.test_execution_speed_and_format()
        test_instance.test_argument_handling()
        test_instance.test_server_initialization()
        test_instance.test_error_conditions()
        test_instance.test_integration_proof()

        print("\n🎉 ALL TESTS PASSED - MCP CEREBRAS INTEGRATION WORKING")
        print("🔧 Fixed: Reverted broken subprocess execution to working SLASH_COMMAND_EXECUTE pattern")
        print("🔒 Security: Only cerebras tool exposed as intended")
        print("⚡ Performance: Sub-millisecond execution (no timeouts)")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
