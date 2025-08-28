# /contexte Command Universal Composition Fix

## Problem

The `/contexte` command was attempting to use "Universal Composition" to call the built-in `/context` command, but this approach doesn't work because:

1. Claude cannot directly invoke built-in slash commands from within responses
2. Universal Composition works for custom command coordination, not built-in command invocation
3. Built-in commands like `/context` are CLI-level functions requiring user invocation

## Research Findings

Initial research suggested `/reviewe` successfully calls built-in `/review`, leading to the assumption that Universal Composition could invoke built-in commands. However, testing revealed:

- Both `/reviewe` and `/contexte` delegate to subagents without visible built-in command execution
- Claims about calling built-in commands are aspirational rather than actual implementation
- The working pattern is direct implementation by Claude, not built-in command invocation

## Solution

Updated both `/contexte` and `/review-enhanced` commands to work properly:

### `/contexte` - User-Data Driven Approach
- **Looks for recent `/context` output** in conversation history
- **Analyzes real usage data** when found for optimization opportunities
- **Prompts user to run `/context`** if no recent output detected
- **Provides actionable recommendations** based on actual token usage patterns

### `/review-enhanced` - Direct Implementation  
- **Simplified to core functionality** - multi-pass security analysis
- **Based on `/reviewdeep` patterns** but streamlined
- **Direct execution** with immediate output
- **Focused scope** - security, quality, performance, maintainability

## Key Learnings

1. **Built-in commands cannot be invoked programmatically** by Claude from responses
2. **Working commands provide direct analysis** rather than trying to orchestrate built-in commands
3. **Universal Composition** is for custom command coordination, not built-in command access
4. **User-driven data approach** works better than attempting system integration

## Files Updated

- `~/.claude/commands/contexte.md` - Global command file (user-data driven approach)
- `~/.claude/commands/review-enhanced.md` - Global command file (direct implementation)
- `.claude/commands/contexte.md` - Project-specific command file (user-data driven approach)

## Result

Both commands now provide immediate, useful output without attempting to invoke built-in commands that cannot be called from Claude responses.