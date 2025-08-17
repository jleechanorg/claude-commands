---
allowed-tools: Bash(qwen:*), Read, Edit
description: Generate large amounts of code using Qwen Coder via Cerebras
---

# Qwen Coder Generation

Delegating this task to Qwen Coder running on Cerebras for fast, high-quality code generation.

## Current Context
- Working directory: !`pwd`
- Git status: !`git status --porcelain | head -5`
- Project structure: !`find . -maxdepth 2 -name "*.py" -o -name "*.js" -o -name "*.md" | head -10`

## Task Execution
!`.claude/commands/qwen/qwen_direct_cerebras.sh "$ARGUMENTS"`

## Post-Generation Analysis

I'll now review the Qwen-generated output and provide:

1. **Code Quality Assessment** - Security, performance, best practices
2. **Integration Strategy** - How to merge with existing codebase  
3. **Testing Recommendations** - Unit tests, edge cases, validation
4. **Refinements** - Error handling, documentation, optimizations
5. **Next Steps** - Implementation plan, deployment considerations

The Qwen output provides the foundation - I'll add the architectural thinking and integration expertise.