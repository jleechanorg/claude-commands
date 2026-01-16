"""
Modular copilot commands package - Clean Architecture

Only ONE command for data collection. Claude does everything else.
"""

from .base import CopilotCommandBase
from .commentfetch import CommentFetch
from .utils import GitHubAPI, JSONSchemas

# Command registry - ONLY data collection commands
COMMAND_REGISTRY = {
    "commentfetch": CommentFetch,
    # That's it! Claude handles everything else
}


def get_command(name: str):
    """Get command class by name.

    Args:
        name: Command name to retrieve

    Returns:
        Command class or None if not found
    """
    return COMMAND_REGISTRY.get(name)


def list_commands():
    """List all available commands.

    Returns:
        List of command names
    """
    return list(COMMAND_REGISTRY.keys())


# Export only what's needed for data collection
__all__ = [
    "CopilotCommandBase",
    "CommentFetch",
    "GitHubAPI",
    "JSONSchemas",
    "get_command",
    "list_commands",
    "COMMAND_REGISTRY",
]
