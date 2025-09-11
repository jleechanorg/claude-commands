# Claude Slash Commands MCP Server

MCP server for Claude Code slash commands, providing unified access to slash command functionality.

## Features

- Unified router pattern for 29+ slash commands
- High-speed Cerebras code generation integration
- Secure, filtered command exposure
- FastMCP-based implementation

## Installation

From the repository root or the MCP server directory:

```bash
cd mcp_servers/slash_commands
pip install -e .
```

## Usage

### Via CLI Script (Recommended)

After installation, the server is available as a command:

```bash
claude-slash-commands-mcp
```

Add to Claude MCP configuration:

```bash
claude mcp add --scope user "claude-slash-commands" "claude-slash-commands-mcp"
```

### Direct Module Execution

Alternatively, run directly as a Python module:

```bash
python -m mcp_servers.slash_commands
```
