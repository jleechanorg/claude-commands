#!/usr/bin/env python3
"""Centralized argparse helper builders for orchestration CLI scripts."""

from __future__ import annotations

import argparse

from orchestration.task_dispatcher import CLI_PROFILES


def add_agent_cli_and_model_arguments(
    parser: argparse.ArgumentParser,
    model_default: str | None = None,
    *,
    include_model: bool = True,
    model_dest: str = "model",
    model_help: str = "Model override for supported CLIs (default: system default).",
) -> None:
    """Add shared agent selection flags."""

    parser.add_argument(
        "--agent-cli",
        type=str,
        default=None,
        help="Agent CLI to use: claude, codex, gemini, cursor. Supports comma-separated chain for fallback (e.g., 'gemini,claude').",
    )
    if include_model:
        parser.add_argument(
            "--model",
            type=str,
            default=model_default,
            dest=model_dest,
            help=model_help,
        )


def add_shared_orchestration_arguments(
    parser: argparse.ArgumentParser,
    *,
    model_default: str | None = None,
    include_model: bool = True,
    model_dest: str = "model",
) -> None:
    """Add orchestration arguments shared by orchestrate_unified and ai_orch run mode."""

    parser.add_argument(
        "--context",
        type=str,
        default=None,
        help="Path to markdown file to inject into agent prompt as pre-computed context",
    )
    parser.add_argument(
        "--branch",
        type=str,
        default=None,
        help="Force checkout of specific branch (prevents new branch creation)",
    )
    parser.add_argument(
        "--pr",
        type=int,
        default=None,
        help="Existing PR number to update (prevents new PR creation)",
    )
    parser.add_argument("--mcp-agent", type=str, default=None, help="Pre-fill agent name for MCP Mail registration")
    parser.add_argument("--bead", type=str, default=None, help="Pre-fill bead ID for tracking")
    parser.add_argument(
        "--validate",
        type=str,
        default=None,
        help="Semantic validation command to run after agent completes",
    )
    parser.add_argument(
        "--no-new-pr",
        action="store_true",
        help="Hard block on PR creation (agents must use existing PR)",
    )
    parser.add_argument(
        "--no-new-branch",
        action="store_true",
        help="Hard block on branch creation (agents must use existing branch)",
    )

    worktree_group = parser.add_mutually_exclusive_group()
    worktree_group.add_argument(
        "--worktree",
        dest="no_worktree",
        action="store_false",
        help="Enable worktree isolation: create a dedicated git worktree per agent (opt-in).",
    )
    worktree_group.add_argument(
        "--no-worktree",
        dest="no_worktree",
        action="store_true",
        help="Deprecated/no-op: worktree isolation is disabled by default; this flag is ignored.",
    )
    parser.set_defaults(no_worktree=True)

    add_agent_cli_and_model_arguments(
        parser,
        model_default=model_default,
        include_model=include_model,
        model_dest=model_dest,
    )


def add_json_output_argument(
    parser: argparse.ArgumentParser,
    *,
    flag: str = "--json",
    dest: str = "json_output",
    help_text: str = "Output JSON representation",
) -> None:
    """Add a consistent JSON output flag."""

    parser.add_argument(flag, action="store_true", dest=dest, help=help_text)


def add_dry_run_argument(
    parser: argparse.ArgumentParser,
    *,
    flag: str = "--dry-run",
    dest: str = "dry_run",
    help_text: str = "Dry-run mode",
) -> None:
    """Add a consistent dry-run flag."""

    parser.add_argument(flag, action="store_true", dest=dest, help=help_text)


def add_live_cli_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_model: bool = True,
    include_detached: bool = True,
) -> None:
    """Add shared args for legacy/interactive AI CLI mode."""

    parser.add_argument(
        "--cli", choices=list(CLI_PROFILES.keys()), default="claude", help="AI CLI to use (default: claude)"
    )
    parser.add_argument("--name", help="Custom session name")
    parser.add_argument("--dir", help="Working directory (default: current directory)")
    if include_model:
        parser.add_argument("--model", help="Model to use (default: sonnet for claude)")
    if include_detached:
        parser.add_argument("--detached", action="store_true", help="Start in detached mode (don't attach immediately)")


def add_safe_monitor_arguments(parser: argparse.ArgumentParser) -> None:
    """Add args for safe read-only agent monitoring CLI."""

    parser.add_argument("agent", nargs="?", help="Agent session name to monitor")
    parser.add_argument("-a", "--all", action="store_true", help="Monitor all agents")
    parser.add_argument("-l", "--list", action="store_true", help="List running agents")
    parser.add_argument("-c", "--continuous", action="store_true", help="Continuous monitoring")
    parser.add_argument("-i", "--interval", type=int, default=5, help="Update interval in seconds")
    parser.add_argument("-n", "--lines", type=int, default=50, help="Number of lines to show")


def add_cleanup_arguments(parser: argparse.ArgumentParser) -> None:
    """Add args for completed-agent cleanup CLI."""

    add_json_output_argument(
        parser,
        flag="--json",
        dest="json",
        help_text="Output results in JSON format",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned up without actually doing it",
    )


def add_task_argument(
    parser: argparse.ArgumentParser,
    *,
    positional_name: str = "task",
    help_text: str = "Task description",
    nargs: str = "+",
    dest: str | None = None,
) -> None:
    """Add a consistent positional task argument for orchestration subcommands."""

    kwargs = {"nargs": nargs, "help": help_text}
    if dest is not None:
        kwargs["dest"] = dest
    parser.add_argument(positional_name, **kwargs)


def add_named_session_argument(
    parser: argparse.ArgumentParser,
    *,
    positional_name: str = "session",
    help_text: str = "Session name",
) -> None:
    """Add shared session positional argument used by attach/kill command handlers."""

    parser.add_argument(positional_name, help=help_text)


def add_test_runner_arguments(parser: argparse.ArgumentParser) -> None:
    """Add args for orchestration test runner CLI."""

    parser.add_argument(
        "test",
        nargs="?",
        help='Specific test to run (e.g., "unified" for test_orchestrate_unified.py)',
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--list", "-l", action="store_true", help="List available tests")
