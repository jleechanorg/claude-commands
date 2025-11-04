# Secondo MCP Server

**Multi-Model AI Second Opinion via Model Context Protocol**

This MCP server provides access to multi-model AI feedback through Anthropic's Model Context Protocol (MCP). Get comprehensive analysis from 5 AI models (Cerebras, Gemini, Perplexity, OpenAI, Grok) with synthesized recommendations and industry sources.

## Features

- ✅ **MCP Compliant**: Implements official Model Context Protocol specification
- ✅ **Multi-Model AI**: Consults 5 different AI models for comprehensive feedback
- ✅ **Intelligent Synthesis**: Combines perspectives into actionable recommendations
- ✅ **OAuth Authentication**: Secure authentication via AI Universe backend
- ✅ **Rate Limited**: 60 requests/hour (authenticated)
- ✅ **Industry Sources**: Includes citations and references
- ✅ **Multiple Feedback Types**: Design review, code review, bug analysis, or comprehensive

## Architecture

This is a **lightweight MCP wrapper** that:
- Exposes MCP-compliant HTTP endpoints (`/tools`, `/execute`)
- Delegates to existing `secondo-cli.sh` script (no duplication)
- Handles authentication via `auth-cli.mjs`
- Maintains connection to AI Universe backend

## Installation

### 1. Install Dependencies

```bash
# From project root
npm install

# From MCP server directory
cd mcp_servers/secondo
npm install
```

### 2. Authenticate

```bash
# Run from project root
node scripts/auth-cli.mjs login
```

This opens your browser for OAuth authentication with AI Universe backend.

### 3. Test the Server

```bash
# Start server
npm start

# In another terminal, test endpoints
curl http://localhost:3003/health | jq .
curl http://localhost:3003/tools | jq .
```

## MCP Endpoints

### `GET /tools`

Returns tool definitions (MCP discovery endpoint).

**Response:**
```json
[
  {
    "name": "get_second_opinion",
    "description": "Get comprehensive multi-model AI feedback...",
    "parameters": {
      "type": "object",
      "properties": {
        "feedback_type": {
          "type": "string",
          "enum": ["design", "code-review", "bugs", "all"]
        },
        "question": {
          "type": "string"
        }
      }
    }
  }
]
```

### `POST /execute`

Executes the secondo tool (MCP execution endpoint).

**Request:**
```json
{
  "tool_name": "get_second_opinion",
  "parameters": {
    "feedback_type": "code-review",
    "question": "Should I use Redis or in-memory caching for rate limiting?"
  }
}
```

**Response:**
```json
{
  "result": "{\"success\":true,\"output\":\"...comprehensive feedback...\"}"
}
```

## Usage with Claude Code

### As MCP Server

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "secondo": {
      "command": "node",
      "args": ["mcp_servers/secondo/server.js"],
      "env": {
        "MCP_SECONDO_PORT": "3003"
      }
    }
  }
}
```

### As Plugin

**Two Installation Options:**

#### Option 1: Secondo Only (Lightweight)

Install ONLY the secondo commands and MCP server:

```bash
# Clone the repository
git clone https://github.com/jleechanorg/worldarchitect.ai.git
cd worldarchitect.ai

# Install secondo-only plugin
/plugin install .claude-plugin/secondo-plugin.json
```

**What you get:**
- ✅ `/secondo` command
- ✅ `/second_opinion` command
- ✅ Secondo MCP server (port 3003)
- ❌ No worldarchitect hooks, agents, or other commands

#### Option 2: Full WorldArchitect.AI Suite (Complete)

Install the complete suite with all features:

```bash
# Clone the repository
git clone https://github.com/jleechanorg/worldarchitect.ai.git
cd worldarchitect.ai

# Install full plugin suite
/plugin install .
```

**What you get:**
- ✅ `/secondo` command
- ✅ `/second_opinion` command
- ✅ Secondo MCP server (port 3003)
- ✅ All worldarchitect slash commands (150+ commands)
- ✅ All worldarchitect agents
- ✅ All worldarchitect hooks (automation, quality checks)

## Usage Examples

### Via Slash Command

```bash
# General feedback
/secondo

# Specific feedback type
/secondo design
/secondo code-review
/secondo bugs

# With custom question
/secondo "Should I use Redis or in-memory caching?"
```

### Via MCP Tool

Claude Code automatically discovers the tool and can use it during conversations:

```
User: "Get me a second opinion on my rate limiting implementation"
Claude: [Uses get_second_opinion tool via MCP]
```

## Configuration

### Environment Variables

- `MCP_SECONDO_PORT` - Server port (default: 3003)
- `MCP_SECONDO_HOST` - Server host (default: localhost)
- `MAX_ERROR_OUTPUT` - Maximum error output characters (default: 2000)
- `NODE_ENV` - Environment mode (development/production)

> **Tip:** `MAX_ERROR_OUTPUT` must be a positive integer. Values below 100 or invalid strings are ignored and the default (2000 characters) is used to keep diagnostics readable without overwhelming Claude Code's UI.

### Rate Limits

> **Note:** These rate limits are enforced by the backend AI Universe service, not by this MCP server.

- **Authenticated**: 60 requests/hour
- **Multi-model synthesis**: 1 per hour per user
- Token expires after 30 days

## Troubleshooting

### Authentication Issues

```bash
# Check authentication status
node scripts/auth-cli.mjs status

# Re-authenticate
node scripts/auth-cli.mjs login

# Get current token
node scripts/auth-cli.mjs token
```

### Server Not Starting

```bash
# Check port availability
lsof -i :3003

# Check logs
tail -f /tmp/secondo-mcp-test.log

# Verify dependencies
npm list express
```

### Tool Execution Fails

```bash
# Verify secondo-cli.sh exists
ls -la scripts/secondo-cli.sh

# Test directly
./scripts/secondo-cli.sh all "test question"

# Check authentication
node scripts/auth-cli.mjs status
```

## Development

### Running in Development Mode

```bash
# With auto-reload on file changes
npm run dev
```

### Testing

```bash
# Health check
npm test

# Full endpoint test
curl -X POST http://localhost:3003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "get_second_opinion",
    "parameters": {
      "feedback_type": "all",
      "question": "Test question"
    }
  }' | jq .
```

### Architecture Diagram

```
┌─────────────────┐
│   Claude Code   │
└────────┬────────┘
         │ MCP Protocol
         ▼
┌─────────────────┐
│  Secondo MCP    │
│     Server      │
│   (Express)     │
└────────┬────────┘
         │
         ├──▶ GET /tools (tool discovery)
         ├──▶ POST /execute (tool execution)
         │
         ▼
┌─────────────────┐
│ secondo-cli.sh  │  ◀── Reuses existing script
│   (wrapper)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AI Universe    │
│    Backend      │  ◀── Multi-model synthesis
│   (Remote MCP)  │
└─────────────────┘
```

## Benefits

✅ **System-Wide**: Install once, use everywhere
✅ **No Duplication**: Reuses existing secondo-cli.sh logic
✅ **OAuth Security**: Secure authentication flow
✅ **MCP Standard**: Compatible with all MCP clients
✅ **Lightweight**: Minimal overhead, delegates to backend
✅ **Maintainable**: Single source of truth for logic

## Resources

- [Model Context Protocol Docs](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)
- [Claude Code Plugins](https://www.anthropic.com/news/claude-code-plugins)
- [MCP GitHub](https://github.com/modelcontextprotocol)
- [AI Universe Backend](https://ai-universe-backend-dev-114133832173.us-central1.run.app)

## License

MIT - See [LICENSE](../../LICENSE) file

## Support

- **Issues**: https://github.com/jleechanorg/worldarchitect.ai/issues
- **Docs**: See `.claude/commands/second_opinion.md`
