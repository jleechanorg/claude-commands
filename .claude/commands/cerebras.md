---
allowed-tools: Bash(cerebras:*), Read, Edit
description: Generate large amounts of code using Cerebras
---

# Cerebras Code Generation

Delegating this task to Cerebras for fast, high-quality code generation.

## Command Aliases
- `/cerebras` - Primary command name
- `/qwen` - Legacy alias (for backwards compatibility)
- `/c` - Short alias
- `/cereb` - Alternative short alias

## Current Context
- Working directory: !`pwd`
- Git status: !`git status --porcelain | head -5`
- Project structure: !`find . -maxdepth 2 -name "*.py" -o -name "*.js" -o -name "*.md" | head -10`

## Conversation Context Extraction and Task Execution

I'll now extract the recent conversation context to provide Cerebras with full background:

!`BRANCH_NAME="$(git branch --show-current | sed 's/[^a-zA-Z0-9_-]/_/g')"`
!`CTX_FILE="$(mktemp "/tmp/cerebras_context_${BRANCH_NAME}_XXXXXX.txt")"`
!`python3 .claude/commands/cerebras/extract_conversation_context.py 50000 > "$CTX_FILE"`
!`if [ -s "$CTX_FILE" ]; then CTX_ARG=(--context-file "$CTX_FILE"); else CTX_ARG=(); fi`
!`.claude/commands/cerebras/cerebras_direct.sh "${CTX_ARG[@]}" "$ARGUMENTS"`
!`rm -f "$CTX_FILE"  # Cleanup temporary context file`

## Post-Generation Analysis

I'll now review the Cerebras-generated output and provide:

1. **Code Quality Assessment** - Security, performance, best practices
2. **Integration Strategy** - How to merge with existing codebase  
3. **Testing Recommendations** - Unit tests, edge cases, validation
4. **Refinements** - Error handling, documentation, optimizations
5. **Next Steps** - Implementation plan, deployment considerations

The Cerebras output provides the foundation - I'll add the architectural thinking and integration expertise.