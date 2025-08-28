import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from mcp.types import TextContent, Tool


def discover_slash_commands() -> Dict[str, str]:
    """Discover available slash commands from markdown files."""
    commands_dir = Path(".claude/commands")
    if not commands_dir.exists():
        return {}
    
    commands = {}
    for file_path in commands_dir.glob("*.md"):
        if file_path.name != "CLAUDE.md":  # Skip the marker file
            command_name = f"/{file_path.stem}"
            commands[command_name] = str(file_path)
    
    return commands


def get_tool_commands() -> List[str]:
    """Get list of slash commands that should be exposed as MCP tools."""
    all_commands = discover_slash_commands()
    # For now, only expose cerebras tool for security focus
    return [cmd for cmd in all_commands.keys() if cmd == "/cerebras"]


def create_tools() -> List[Tool]:
    """Create MCP tools that map to Claude slash commands - only cerebras for now."""
    tools = []
    
    # Only expose the cerebras tool
    tools.append(Tool(
        name="cerebras",
        description="Execute Claude slash command: /cerebras - Ultra-fast AI code generation using Cerebras API",
        inputSchema={
            "type": "object",
            "properties": {
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Arguments to pass to the cerebras command"
                }
            }
        }
    ))
    
    return tools


def sanitize_args(args: Any) -> str:
    """Sanitize command arguments to prevent injection."""
    if isinstance(args, list):
        # Join array arguments into a single string
        args = " ".join(str(arg) for arg in args)
    elif not isinstance(args, str):
        # Convert non-string arguments to string
        args = str(args) if args else ""
    
    # Remove dangerous characters
    dangerous_chars = [";", "&", "|", "`", "$", "<", ">", "(", ")", "{", "}", "[", "]", "\n", "\r"]
    for char in dangerous_chars:
        args = args.replace(char, "")
    
    return args


def execute_direct_command(command: str, args: str = "", cwd: str = None) -> str:
    """Execute a command directly with security safeguards."""
    if not cwd:
        # Dynamically find project root using CLAUDE.md marker
        current_path = Path(__file__).resolve()
        for parent in [current_path] + list(current_path.parents):
            if (parent / "CLAUDE.md").exists():
                cwd = str(parent)
                break
        else:
            cwd = os.environ.get("PROJECT_ROOT", ".")
    
    # Sanitize arguments
    safe_args = sanitize_args(args)
    
    # Construct the full command
    if safe_args:
        cmd_line = f"{command} {safe_args}"
    else:
        cmd_line = command
    
    # Execute with subprocess - use shell=False for security
    try:
        # Split command into components for secure execution - properly handle quotes
        cmd_parts = shlex.split(cmd_line)
        result = subprocess.run(
            cmd_parts,
            shell=False,
            capture_output=True,
            text=True,
            timeout=30,  # Security policy timeout
            check=True,
            cwd=cwd
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Command failed with exit code {e.returncode}: {e.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


def _execute_slash_command(command_name: str, args: str = "") -> str:
    """Execute slash command by returning instructions for Claude to execute directly."""
    # Return the SLASH_COMMAND_EXECUTE pattern that Claude processes via hooks
    # This matches the working pattern from cb93084f commit
    return f"SLASH_COMMAND_EXECUTE: {command_name} {args}"


def _is_test_related_command(command: str) -> bool:
    """Check if a command is related to testing."""
    test_commands = ["/test", "/run-tests"]
    return command in test_commands


async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for slash commands - only cerebras tool allowed."""
    # Only allow cerebras tool for security reasons
    if name != "cerebras":
        return [TextContent(type="text", text=f"Tool '{name}' is not available. Only '/cerebras' is currently supported.")]
    
    # Extract arguments for cerebras tool
    args = arguments.get("args", [])
    
    # Join array arguments into a single string for command execution
    if isinstance(args, list):
        args_str = " ".join(str(arg) for arg in args)
    else:
        args_str = str(args) if args else ""
    
    # Execute the cerebras command
    try:
        output = _execute_slash_command("/cerebras", args_str)
        return [TextContent(type="text", text=output)]
    except Exception as e:
        return [TextContent(type="text", text=f"Security error: {str(e)}")]


async def main():
    """Main entry point for the FastMCP server."""
    from fastmcp import FastMCP
    
    mcp = FastMCP("claude-slash-commands")
    
    # Register cerebras tool using decorator approach
    @mcp.tool()
    async def cerebras(args: list = None) -> str:
        """Execute Claude slash command: /cerebras - Ultra-fast AI code generation using Cerebras API"""
        if args is None:
            args = []
        
        # Convert args to string for command execution
        args_str = " ".join(str(arg) for arg in args)
        
        # Execute the cerebras command
        try:
            output = _execute_slash_command("/cerebras", args_str)
            return output
        except Exception as e:
            return f"Security error: {str(e)}"
    
    # Start the server
    await mcp.run_stdio_async()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())