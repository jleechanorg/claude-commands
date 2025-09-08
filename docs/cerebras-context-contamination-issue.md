# Cerebras Context Contamination Issue

## Issue Summary

**Problem**: The Cerebras generation command intermittently fails to generate actual code, instead returning only wrapper messages like `[Used mcp__claude-slash-commands__cerebras tool]`.

**Root Cause**: Context contamination - the automatic conversation context extraction includes debugging discussions about MCP tools, which Cerebras learns and reproduces in subsequent generations.

**Status**: ✅ **RESOLVED** - Use `--no-auto-context` flag to prevent contamination

## Technical Details

### The Problem Mechanism

1. **Context Extraction**: The `cerebras_direct.sh` script automatically extracts recent conversation history
2. **Contamination**: When debugging Cerebras issues, conversations contain MCP tool references
3. **Pattern Learning**: Cerebras learns these patterns from context and reproduces them
4. **Feedback Loop**: The debugging process itself contaminates the system being debugged

### Evidence

**Raw API Request showing contaminated context:**
```json
{
  "model": "qwen-3-coder-480b",
  "messages": [
    {
      "role": "user",
      "content": "# Recent Conversation Context\n\n## Assistant (2025-09-08T06:17:23.723Z)\n[Used mcp__serena__read_file tool]\n\n## Assistant (2025-09-08T06:18:43.486Z)\n[Used Bash tool]..."
    }
  ]
}
```

**API Response returning learned pattern:**
```json
{
  "choices": [{
    "message": {
      "content": "[Used mcp__claude-slash-commands__cerebras tool]"
    }
  }]
}
```

## Failing Prompt

This is the exact prompt that demonstrates the issue:

```bash
.claude/commands/cerebras/cerebras_direct.sh "I need you to update a design document for a Python proxy that adds slash commands to Codex CLI. The current design has critical compatibility issues with Claude Code CLI specification that must be fixed.

## CONTEXT: Current Design Problems

The architecture review found 7 critical issues:
1. ❌ Command discovery only checks .claude/ (missing ~/.claude/)
2. ❌ No precedence rules (project should override personal)
3. ❌ Missing frontmatter parsing (YAML with allowed-tools, description, etc.)
4. ❌ No argument substitution (\$ARGUMENTS, \$1, \$2, etc.)
5. ❌ Missing bash execution (! prefix)
6. ❌ Missing file references (@ prefix)
7. ❌ No namespacing support (subdirectories)

## CLAUDE CODE CLI SPECIFICATION (MUST FOLLOW EXACTLY):

### Command Discovery:
- Commands from \`.claude/commands/\` AND \`~/.claude/commands/\`
- Project-level overrides personal-level
- Supports subdirectories for namespacing
- Command name derived from filename without .md

### Markdown File Structure:
\`\`\`markdown
---
allowed-tools: Bash(git:*)
argument-hint: \"file or directory\"
description: \"Command description\"
model: \"claude-3-sonnet\"
---

Command instructions here with \$ARGUMENTS and \$1, \$2 substitution.
\`\`\`

### Argument Handling:
- \$ARGUMENTS = entire argument string
- \$1, \$2, \$3 = positional arguments
- Substituted in markdown content before execution

### Execution Model:
- ! prefix = bash command execution
- @ prefix = file references
- Tool permissions from frontmatter
- Default = send enhanced prompt to AI

## TASK: UPDATE DESIGN.MD

Please rewrite the \"Phase 2: Slash Commands - Module Architecture\" section with:

1. **Correct Command Discovery**: Both .claude/ and ~/.claude/ with proper precedence
2. **Proper Markdown Parsing**: Frontmatter + argument substitution
3. **Complete Execution Model**: Bash (!), file refs (@), tool permissions
4. **Maintain Module System**: Keep as enhancement layer over Claude Code CLI compatibility
5. **Practical Implementation**: Code that actually works with real Claude Code CLI commands

Focus on correctness and exact compatibility. Show the corrected code with proper:
- \`discover_claude_commands()\` function for dual-directory discovery
- \`parse_command_file()\` with YAML frontmatter and \$ARGUMENTS substitution
- \`handle_slash_command()\` with complete execution logic
- Integration with the existing module system

Make it comprehensive enough to implement correctly in 1-2 iterations."
```

**Expected Result**: Complete architectural implementation with corrected discovery functions
**Actual Result**: `[Used mcp__claude-slash-commands__cerebras tool]` (wrapper message only)

## Solution

### Immediate Fix
```bash
# This works - prevents context contamination:
.claude/commands/cerebras/cerebras_direct.sh --no-auto-context "your prompt here"

# This may fail - includes contaminated conversation:
.claude/commands/cerebras/cerebras_direct.sh "your prompt here"
```

### Test Results
**With `--no-auto-context`:**
- ✅ Perfect code generation (19 lines of Python)
- ✅ Fast response (341ms)
- ✅ Clean prompt (21 tokens)

**With context extraction:**
- ❌ Wrapper message only
- ❌ Contaminated prompt (13,949+ tokens)
- ❌ Pattern reproduction instead of generation

## Recommended Actions

### 1. Update Documentation
Add warning to `cerebras_direct.sh` documentation about context contamination risks.

### 2. Improve Context Filtering
Modify the context extraction to exclude MCP tool references:
```bash
# Filter out MCP tool references from context
context=$(extract_context | grep -v "Used.*tool" | grep -v "mcp__")
```

### 3. Add Debug Flag
Provide a debug flag to show what context is being included:
```bash
--show-context  # Display extracted context before sending
```

## Files Affected

- **Script**: `.claude/commands/cerebras/cerebras_direct.sh` (lines 133-174, context extraction)
- **Context Extractor**: `extract_conversation_context.py` (may need MCP filtering)

## Debugging Timeline

1. **Initial Issue**: Intermittent Cerebras failures with wrapper messages
2. **Investigation**: Raw API inspection revealed contaminated context
3. **Root Cause**: Conversation history containing MCP tool references
4. **Solution**: `--no-auto-context` flag bypasses contamination
5. **Verification**: Clean generation with filtered context

## Critical Insight

This was a **feedback loop problem** where the debugging process itself contaminated the system being debugged. The "intermittent" behavior was actually deterministic:
- Context extraction ON = contaminated responses
- Context extraction OFF = clean generation

This highlights the importance of isolating debugging environments from production systems.
