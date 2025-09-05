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

## Cerebras Script Modes

The cerebras_direct.sh script supports two modes of operation:

### Default Mode
- Uses structured system prompts for consistent code generation
- Provides comprehensive documentation and error handling in generated code
- Better for architectural design documents and robust implementations
- Example: `/cerebras "Create a Python function that adds two numbers"`

### Light Mode (--light flag)
- Skips system prompts for faster, more direct code generation
- Focuses on implementation without extensive documentation
- Includes comprehensive testing strategies in output
- Better for rapid prototyping and implementation-focused tasks
- Example: `/cerebras --light "Create a Python function that adds two numbers"`

## When to Use Each Mode

### Use Default Mode When:
- Generating architectural design documents
- You need detailed explanations of design decisions
- You want consistent code quality and structure
- Working on small tasks where documentation is valued
- You prefer iterative implementations for stack safety

### Use Light Mode When:
- You want faster code generation without system prompts
- Generating implementation-focused design documents
- You need comprehensive testing strategies included
- Working on medium to large tasks
- You encounter rate limiting with default mode
- You accept reduced guardrails and will manually review outputs
- You will not include secrets/PII and can run in a trusted environment

## Current Context
- Working directory: !`pwd`
- Git status: !`git status --porcelain | head -5`
- Project structure: !`find . -maxdepth 2 -name "*.py" -o -name "*.js" -o -name "*.md" | head -10`

## Task Execution

!`.claude/commands/cerebras/cerebras_direct.sh "$ARGUMENTS"`

## Post-Generation Analysis

I'll now review the Cerebras-generated output and provide:

1. **Code Quality Assessment** - Security, performance, best practices
2. **Integration Strategy** - How to merge with existing codebase  
3. **Testing Recommendations** - Unit tests, edge cases, validation
4. **Refinements** - Error handling, documentation, optimizations
5. **Next Steps** - Implementation plan, deployment considerations

The Cerebras output provides the foundation - I'll add the architectural thinking and integration expertise.