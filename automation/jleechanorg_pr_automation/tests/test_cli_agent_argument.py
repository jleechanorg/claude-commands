#!/usr/bin/env python3
"""Test --cli-agent argument parsing and usage"""

import argparse
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from automation.jleechanorg_pr_automation.jleechanorg_pr_monitor import (
    _parse_cli_agent_chain,
    _normalize_model,
)


def test_parse_cli_agent_chain_single():
    """Test parsing single CLI agent"""
    assert _parse_cli_agent_chain("claude") == "claude"
    assert _parse_cli_agent_chain("gemini") == "gemini"
    assert _parse_cli_agent_chain("cursor") == "cursor"


def test_parse_cli_agent_chain_multiple():
    """Test parsing comma-separated CLI agent chain"""
    assert _parse_cli_agent_chain("gemini,cursor") == "gemini,cursor"
    assert _parse_cli_agent_chain("claude,gemini") == "claude,gemini"
    assert _parse_cli_agent_chain("gemini,cursor,claude") == "gemini,cursor,claude"


def test_parse_cli_agent_chain_whitespace():
    """Test parsing with whitespace handling"""
    assert _parse_cli_agent_chain("gemini, cursor") == "gemini,cursor"
    assert _parse_cli_agent_chain(" gemini , cursor ") == "gemini,cursor"


def test_parse_cli_agent_chain_deduplication():
    """Test deduplication of CLI agents"""
    assert _parse_cli_agent_chain("gemini,gemini,cursor") == "gemini,cursor"
    assert _parse_cli_agent_chain("claude,gemini,claude") == "claude,gemini"


def test_argparse_integration():
    """Test that argparse correctly parses --cli-agent argument"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cli-agent",
        "--fixpr-agent",
        dest="cli_agent",
        type=_parse_cli_agent_chain,
        default="claude",
        help="AI CLI chain",
    )
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--fixpr", action="store_true")
    parser.add_argument("--fix-comment", action="store_true")

    # Test single value
    args = parser.parse_args(["--cli-agent", "gemini"])
    assert args.cli_agent == "gemini"

    # Test comma-separated value (as single argument)
    args = parser.parse_args(["--cli-agent", "gemini,cursor"])
    assert args.cli_agent == "gemini,cursor"

    # Test with --fixpr
    args = parser.parse_args(["--fixpr", "--cli-agent", "gemini,cursor", "--model", "gemini-3-auto"])
    assert args.cli_agent == "gemini,cursor"
    assert args.model == "gemini-3-auto"
    assert args.fixpr is True

    # Test with --fix-comment (note: --max-prs not in test parser, so skip it)
    args = parser.parse_args(["--fix-comment", "--cli-agent", "gemini,cursor"])
    assert args.cli_agent == "gemini,cursor"

    # Test backwards compatibility alias
    args = parser.parse_args(["--fixpr-agent", "cursor"])
    assert args.cli_agent == "cursor"


def test_invalid_cli_agent():
    """Test that invalid CLI agents raise ArgumentTypeError"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli-agent", type=_parse_cli_agent_chain, default="claude")

    # Test invalid CLI
    try:
        parser.parse_args(["--cli-agent", "invalid"])
        assert False, "Should have raised ArgumentTypeError"
    except SystemExit:
        pass  # argparse raises SystemExit on error

    # Test empty string
    try:
        parser.parse_args(["--cli-agent", ""])
        assert False, "Should have raised ArgumentTypeError"
    except SystemExit:
        pass


if __name__ == "__main__":
    import unittest

    class TestCLIAgentArgument(unittest.TestCase):
        def test_parse_cli_agent_chain_single(self):
            test_parse_cli_agent_chain_single()

        def test_parse_cli_agent_chain_multiple(self):
            test_parse_cli_agent_chain_multiple()

        def test_parse_cli_agent_chain_whitespace(self):
            test_parse_cli_agent_chain_whitespace()

        def test_parse_cli_agent_chain_deduplication(self):
            test_parse_cli_agent_chain_deduplication()

        def test_argparse_integration(self):
            test_argparse_integration()

        def test_invalid_cli_agent(self):
            test_invalid_cli_agent()

    unittest.main()
