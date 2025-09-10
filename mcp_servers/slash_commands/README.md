# Claude Slash Commands MCP Server

MCP server for Claude Code slash commands, providing unified access to slash command functionality.

## Features

- Unified router pattern for 29+ slash commands
- High-speed Cerebras code generation integration
- Secure, filtered command exposure
- FastMCP-based implementation

## Installation

```bash
pip install -e .
```

## Usage

Add to Claude MCP configuration:

```bash
claude mcp add --scope user "claude-slash-commands" "claude-slash-commands-mcp"
```
