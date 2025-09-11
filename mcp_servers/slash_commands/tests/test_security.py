#!/usr/bin/env python3
"""
Security tests for MCP server - Updated for unified_router architecture
"""

import asyncio
import os
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for MCP server imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import MCP server components - use unified router architecture
try:
    from ..unified_router import handle_tool_call, create_tools
except ImportError:
    # Fallback for direct execution
    from unified_router import handle_tool_call, create_tools


class TestSecurity:
    """Test security aspects of the MCP server"""

    @pytest.mark.asyncio
    async def test_input_validation_basic(self):
        """Test basic input validation in handle_tool_call"""

        # Test with potentially malicious input - should just pass as text
        malicious_inputs = [
            "../../../etc/passwd",
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "$(rm -rf /)",
            "`cat /etc/passwd`"
        ]

        for malicious_input in malicious_inputs:
            # Mock subprocess to prevent actual execution
            with patch("subprocess.run") as mock_subprocess:
                mock_subprocess.return_value = Mock(
                    returncode=0,
                    stdout="SLASH_COMMAND_EXECUTE: /cerebras",
                    stderr=""
                )

                # Test with cerebras which should return SLASH_COMMAND_EXECUTE
                result = await handle_tool_call("cerebras", {"args": [malicious_input]})
                assert len(result) > 0
                assert "SLASH_COMMAND_EXECUTE:" in result[0].text
                # Malicious input is just passed as argument text, not executed

    @pytest.mark.asyncio
    async def test_subprocess_security_basic(self):
        """Test that tool execution returns expected format"""

        # Test that cerebras tool returns SLASH_COMMAND_EXECUTE pattern
        result = await handle_tool_call("cerebras", {"args": []})

        # Should return result in expected format
        assert len(result) > 0
        assert "SLASH_COMMAND_EXECUTE:" in result[0].text

        # Result should contain the command pattern
        assert "/cerebras" in result[0].text

    @pytest.mark.asyncio
    async def test_tool_discovery_security(self):
        """Test that tool discovery doesn't expose sensitive information"""

        tools = create_tools()

        # Should have discovered tools without errors
        assert len(tools) > 0

        # Tool names should not contain sensitive paths
        tool_names = [t.name for t in tools]

        for tool_name in tool_names:
            # Should not contain system paths
            assert "/etc/" not in tool_name
            assert "/bin/" not in tool_name
            assert "/usr/" not in tool_name
            assert ".." not in tool_name

    @pytest.mark.asyncio
    async def test_error_handling_security(self):
        """Test that error messages don't leak sensitive information"""

        # Test with non-existent tool
        result = await handle_tool_call("nonexistent_tool_xyz", {})

        assert len(result) > 0
        error_text = result[0].text.lower()

        # Error message should not contain sensitive paths
        assert "/etc/" not in error_text
        assert "/home/" not in error_text
        assert "/usr/" not in error_text

        # Should indicate tool not available
        assert "not available" in error_text or "not supported" in error_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
