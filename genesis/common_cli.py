"""Shared CLI parsing utilities for Genesis scripts."""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass

DEFAULT_MAX_ITERATIONS = 20
DEFAULT_POOL_SIZE = 5


class GenesisUsageError(Exception):
    """Raised when CLI arguments are invalid."""


class GenesisHelpRequested(Exception):
    """Raised when the user requests CLI help."""


USAGE_MESSAGE = """Usage: python genesis/genesis.py <goal_directory> [max_iterations]
   or: python genesis/genesis.py --refine "<goal>" [max_iterations] [--interactive] [--iterate]

Examples:
  python genesis/genesis.py goals/2025-01-22-1530-rest-api/ 10
  python genesis/genesis.py --refine "build a REST API" 5
  python genesis/genesis.py --refine "build a REST API" 5 --interactive  # requires approval
  python genesis/genesis.py --refine "build a REST API" 5 --iterate     # skip initial generation

Flags:
  --interactive: Require manual approval for refinements
  --iterate:     Skip initial bulk generation phase, start with iterative refinement
  --claude:      Use Claude for generation (Codex is default)
  --codex:       Explicitly use Codex for generation (default)
  --pool-size <n>   Override subagent pool size

Note: Refinement is auto-approved by default. Use --interactive for manual approval.
      Codex is used unless --claude is provided.
"""


@dataclass
class GenesisArguments:
    """Normalized configuration for Genesis style scripts."""

    mode: str  # "goal" or "refine"
    goal_directory: str | None
    refine_goal: str | None
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    skip_initial_generation: bool = False
    interactive: bool = False
    use_codex: bool = True
    pool_size: int = DEFAULT_POOL_SIZE


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--refine", type=str, help="Refine the provided goal description")
    parser.add_argument("--iterate", action="store_true", help="Skip initial Cerebras generation phase")
    parser.add_argument("--interactive", action="store_true", help="Require manual approval for refinements")
    parser.add_argument("--codex", dest="codex_flag", action="store_true", help="Use Codex")
    parser.add_argument("--claude", dest="claude_flag", action="store_true", help="Use Claude")
    parser.add_argument("--pool-size", type=int, help="Override subagent pool size")
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("positional", nargs="*")
    return parser


def extract_model_preference(argv: Sequence[str] | None) -> bool | None:
    """Return model preference flag without validating positional arguments."""

    if argv is None:
        return None

    use_codex: bool | None = None
    for value in argv:
        if value == "--claude":
            use_codex = False
        elif value == "--codex":
            use_codex = True
    return use_codex


def parse_genesis_cli(argv: Sequence[str]) -> GenesisArguments:
    """Parse Genesis CLI arguments into a structured configuration."""

    if len(argv) <= 1:
        raise GenesisUsageError(USAGE_MESSAGE)

    parser = _build_parser()
    namespace, extras = parser.parse_known_args(argv[1:])

    if namespace.help:
        raise GenesisHelpRequested()

    if extras:
        # argparse only returns extras for unexpected options; treat as usage error.
        raise GenesisUsageError(f"Unexpected arguments: {' '.join(extras)}\n\n{USAGE_MESSAGE}")

    if namespace.codex_flag and namespace.claude_flag:
        raise GenesisUsageError("Cannot specify both --codex and --claude")

    use_codex = True
    if namespace.codex_flag:
        use_codex = True
    elif namespace.claude_flag:
        use_codex = False

    positional: list[str] = list(namespace.positional)

    # Determine mode and positional requirements.
    mode: str
    goal_directory: str | None = None
    refine_goal: str | None = None
    max_iterations = DEFAULT_MAX_ITERATIONS

    if namespace.refine is not None:
        mode = "refine"
        refine_goal = namespace.refine
        if positional:
            max_candidate = positional.pop(0)
            try:
                max_iterations = int(max_candidate)
            except ValueError as exc:
                raise GenesisUsageError(
                    f"Invalid max_iterations value: {max_candidate!r}\n\n{USAGE_MESSAGE}"
                ) from exc
            if max_iterations <= 0:
                raise GenesisUsageError(
                    f"max_iterations must be a positive integer (got {max_iterations})\n\n{USAGE_MESSAGE}"
                )
    else:
        if not positional:
            raise GenesisUsageError(USAGE_MESSAGE)
        mode = "goal"
        goal_directory = positional.pop(0)
        if positional:
            max_candidate = positional.pop(0)
            try:
                max_iterations = int(max_candidate)
            except ValueError as exc:
                raise GenesisUsageError(
                    f"Invalid max_iterations value: {max_candidate!r}\n\n{USAGE_MESSAGE}"
                ) from exc
            if max_iterations <= 0:
                raise GenesisUsageError(
                    f"max_iterations must be a positive integer (got {max_iterations})\n\n{USAGE_MESSAGE}"
                )

    if positional:
        raise GenesisUsageError(f"Unexpected arguments: {' '.join(positional)}\n\n{USAGE_MESSAGE}")

    pool_size = DEFAULT_POOL_SIZE if namespace.pool_size is None else namespace.pool_size
    if pool_size <= 0:
        raise GenesisUsageError(
            f"pool size must be a positive integer (got {pool_size})\n\n{USAGE_MESSAGE}"
        )

    return GenesisArguments(
        mode=mode,
        goal_directory=goal_directory,
        refine_goal=refine_goal,
        max_iterations=max_iterations,
        skip_initial_generation=namespace.iterate,
        interactive=namespace.interactive,
        use_codex=use_codex,
        pool_size=pool_size,
    )


def print_usage(message: str | None = None) -> None:
    """Print the shared usage message, optionally prefixed by an error."""

    if message:
        message_text = message.strip()
        usage_text = USAGE_MESSAGE.strip()
        stream = sys.stderr
        if message_text and message_text != usage_text:
            print(message_text, file=stream)
            print("", file=stream)
    else:
        stream = sys.stdout
    print(USAGE_MESSAGE.strip(), file=stream)


__all__ = [
    "GenesisArguments",
    "GenesisUsageError",
    "GenesisHelpRequested",
    "DEFAULT_MAX_ITERATIONS",
    "DEFAULT_POOL_SIZE",
    "extract_model_preference",
    "parse_genesis_cli",
    "print_usage",
]
