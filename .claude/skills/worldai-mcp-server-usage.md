# Your Project MCP Server Usage

## Overview

The Your Project MCP server uses **JSON-RPC 2.0** protocol over HTTP POST.

## Endpoint

```http
POST http://localhost:8081/mcp
Content-Type: application/json
```

## Authentication Bypass (Local Dev)

Use the `X-Test-User-ID` header for local testing without Firebase auth:
```bash
-H "X-Test-User-ID: <firebase_uid>"
```

**Finding the user ID:** Check server logs for `user=<uid>` entries:
```bash
export PROJECT_LOG_DIR="${PROJECT_LOG_DIR:-/tmp/your-project.com}"
grep "user=" "$PROJECT_LOG_DIR"/*/flask-server.log | tail -10
```

> **Log location note:** The examples assume local-dev logs under `/tmp/<project>/*/flask-server.log`.
> In containers or systemd services, use `docker logs <container>` or `journalctl -u <service>` and set
> `PROJECT_LOG_DIR` to the path where your deployment writes logs.

## Available Tools

```bash
# List all tools
curl -s -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}' | jq '.result.tools[].name'
```

Tools:
- `create_campaign` - Create a new campaign
- `get_campaign_state` - Get current campaign state
- `process_action` - Send player action and get response
- `update_campaign` - Update campaign settings
- `export_campaign` - Export campaign data
- `get_campaigns_list` - List user's campaigns
- `get_user_settings` - Get user preferences
- `update_user_settings` - Update user preferences

## JSON-RPC Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "<tool_name>",
    "arguments": {
      "<arg1>": "<value1>",
      "user_id": "<firebase_uid>"
    }
  },
  "id": 1
}
```

## Common Operations

### Get Campaign State

```bash
cat > /tmp/req.json << 'EOF'
{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_campaign_state", "arguments": {"campaign_id": "<campaign_id>", "user_id": "<uid>"}}, "id": 1}
EOF
curl -s -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -H "X-Test-User-ID: <uid>" \
  -d @/tmp/req.json | jq '.result'
```

### Process Player Action

```bash
cat > /tmp/req.json << 'EOF'
{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "process_action", "arguments": {"campaign_id": "<campaign_id>", "user_id": "<uid>", "user_input": "I attack the goblin", "mode": "character"}}, "id": 1}
EOF
curl -s -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -H "X-Test-User-ID: <uid>" \
  -d @/tmp/req.json | jq '.result | {dice_rolls, narrative: .narrative[0:200]}'
```

### List Campaigns

```bash
cat > /tmp/req.json << 'EOF'
{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_campaigns_list", "arguments": {"user_id": "<uid>"}}, "id": 1}
EOF
curl -s -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -H "X-Test-User-ID: <uid>" \
  -d @/tmp/req.json | jq '.result.campaigns'
```

## Debugging Tips

### Check Server Logs

```bash
# Real-time log monitoring
tail -f "$PROJECT_LOG_DIR"/*/flask-server.log

# Check for dice roll processing
grep -E "NATIVE|Phase|tool_call|dice" "$PROJECT_LOG_DIR"/*/flask-server.log | tail -20

# Find user IDs for campaigns
grep "user=" "$PROJECT_LOG_DIR"/*/flask-server.log | tail -10
```

### Common Issues

1. **Campaign not found**: Use correct Firebase UID (not email)
2. **Method not allowed (405)**: Use POST to `/mcp` endpoint
3. **Empty dice_rolls**: LLM may skip tool calls - check Phase 1/2 logs
