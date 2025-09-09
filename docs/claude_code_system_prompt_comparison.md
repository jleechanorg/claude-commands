# Claude Code System Prompt Capture - Method Comparison

**Captured:** 2025-09-08
**Version:** Claude Code 1.0.108
**User:** jleechan

## Executive Summary

Successfully tested two different methods for capturing Claude Code's system prompt:

1. **✅ Debug Method**: `claude --debug api` (Working)
2. **✅ HTTP Proxy Method**: Custom Python proxy (Working)
3. **❌ ccproxy-api**: Configuration issues with Pydantic models

Both working methods successfully captured the complete ~32KB system prompt that Claude Code sends to the Anthropic API.

## Method Comparison

### Method 1: Claude CLI Debug Mode (Primary)

**Command**:
```bash
claude --debug api --dangerously-skip-permissions -p "Hello"
```

**Advantages**:
- ✅ **No setup required** - Works immediately with existing Claude Code
- ✅ **Complete capture** - Gets full system prompt directly from CLI
- ✅ **No external dependencies** - Uses built-in Claude Code functionality
- ✅ **Reliable** - Always works when Claude Code is installed

**Disadvantages**:
- ❌ **Mixed output** - System prompt embedded in debug logs
- ❌ **Manual extraction** - Need to parse debug output manually
- ❌ **Verbose** - Lots of debug information to sift through

**System Prompt Size**: ~32KB (same content as proxy method)

### Method 2: HTTP Proxy Intercept (Secondary)

**Setup**:
```python
# Custom Python proxy server
python3 /tmp/simple_claude_proxy.py
```

**Usage**:
```bash
ANTHROPIC_BASE_URL=http://localhost:8000 claude -p "test"
```

**Advantages**:
- ✅ **Clean capture** - Direct API request interception
- ✅ **JSON format** - Structured data with headers and body
- ✅ **Multiple requests** - Can capture variations across different prompts
- ✅ **Programmatic** - Easy to process captured data

**Disadvantages**:
- ❌ **Setup required** - Need to write and run proxy server
- ❌ **Network dependency** - Must route requests through proxy
- ❌ **Authentication exposure** - API key visible in proxy logs

**System Prompt Structure**:
```json
{
  "system": [
    {
      "type": "text",
      "text": "You are Claude Code, Anthropic's official CLI for Claude."
    },
    {
      "type": "text",
      "text": "[32KB full system prompt...]"
    }
  ]
}
```

### Method 3: ccproxy-api (Failed)

**Issue**: Configuration errors in version 0.1.7
```
Configuration error: `Settings` is not fully defined;
you should define `McpServer`, then call `Settings.model_rebuild()`
```

**Status**: Pydantic model compatibility issues, not resolved

## System Prompt Analysis

### Key Findings (Both Methods Confirmed)

**System Prompt Structure**:
- **Part 1**: Basic identity (58 bytes) - "You are Claude Code, Anthropic's official CLI for Claude."
- **Part 2**: Complete instructions (~32KB) - Full behavioral system prompt

**Total Size**: 32,532 bytes

**Content Includes**:
1. **Core Identity & Mission** - CLI tool for software engineering
2. **Security Constraints** - Defensive security only, no malicious assistance
3. **Behavioral Guidelines** - Tone, verbosity, response patterns
4. **Tool Usage Policies** - Comprehensive permission system
5. **MCP Server Instructions** - Integration with multiple MCP servers
6. **Project Context** - Environment variables, git status, file paths
7. **File Operation Protocols** - Strong anti-creation bias, integration-first
8. **Context Optimization** - Real-time context management strategies

### Critical Instructions Confirmed

Both methods captured identical content confirming:

- **CLAUDE.md Integration**: All project-specific instructions from `/Users/jleechan/projects/worktree_sysi/CLAUDE.md` are included
- **MCP Server Setup**: Instructions from multiple MCP servers (serena, filesystem, gemini-cli, memory-server, playwright, etc.)
- **Tool Permissions**: 158+ specific tool permissions pre-approved
- **Context Awareness**: Real-time environment context (git branch, working directory, date/time)

## Recommendations

### For One-Time Capture
**Use Debug Method**: `claude --debug api --dangerously-skip-permissions -p "test"`
- Fastest setup
- Most reliable
- No external dependencies

### For Research/Analysis
**Use HTTP Proxy Method**: Custom Python proxy
- Better for programmatic analysis
- Captures multiple request variations
- Structured JSON output

### For Production Integration
**Avoid ccproxy-api**: Version 0.1.7 has compatibility issues
- Try newer versions when available
- Consider alternative proxy solutions
- Custom proxy code is more reliable

## Files Generated

### Debug Method Outputs
- System prompt embedded in console debug output
- Manual extraction required

### Proxy Method Outputs
- `/tmp/ccproxy/claude_request_*.json` - Complete API requests
- `/tmp/ccproxy/complete_system_prompt_via_proxy.txt` - Extracted system prompt
- Multiple request captures for analysis

## Usage Examples

### Extract System Prompt via Debug Method
```bash
# Capture debug output
claude --debug api --dangerously-skip-permissions -p "test" 2>&1 | tee debug.log

# Extract system prompt (manual process - look for the large text block)
# System prompt appears after tool permission listings
```

### Extract System Prompt via Proxy Method
```bash
# Start proxy
python3 /tmp/simple_claude_proxy.py &

# Make request through proxy
ANTHROPIC_BASE_URL=http://localhost:8000 claude -p "test"

# Extract system prompt from captured JSON
jq -r '.body.system[0].text + "\n\n" + .body.system[1].text' /tmp/ccproxy/claude_request_*.json > system_prompt.txt
```

## Security Considerations

⚠️ **API Key Exposure**: Both methods expose Anthropic API keys in outputs
- Debug logs contain authentication headers
- Proxy logs contain full API requests with bearer tokens
- Ensure captured files are properly secured and not committed to repos

✅ **Safe for Research**: Both methods are safe for understanding Claude Code behavior
- No modification of Claude Code functionality
- Read-only analysis of system prompts
- Helps understand Claude Code's architectural patterns

---

*This analysis validates that Claude Code uses sophisticated, context-aware system prompts with extensive MCP integration and project-specific customization. The debug method provides the most accessible approach for researchers and developers interested in understanding Claude Code's internal behavior.*
