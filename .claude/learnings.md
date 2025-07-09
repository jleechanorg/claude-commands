# Claude's Learning Log

This file tracks all learnings from corrections, mistakes, and self-realizations. Referenced by CLAUDE.md.

## Command Execution

### Python/venv
- ✅ **ALWAYS** use `source venv/bin/activate && python`, never `vpython`
- ✅ Playwright IS installed in venv - activate venv to use it
- ✅ Run Python scripts from project root, not subdirectories

### Testing
- ✅ Browser tests: Use `source venv/bin/activate && python testing_ui/test_*.py`
- ✅ All tests: Prefix with `TESTING=true` environment variable
- ✅ Playwright can take real screenshots - no simulation needed

## Common Misconceptions

### Tools Available
- ❌ "Playwright not installed" - It IS installed, just needs venv
- ❌ "Can't run browser tests" - Can run them with proper setup
- ❌ "Need to simulate" - Real tools are available

### File Paths
- ✅ Always use absolute paths from project root
- ✅ Run commands from project root, not subdirectories

## Self-Correction Patterns

When I say these phrases, I'm recognizing a mistake:
- "Let me correct that..." → Document the correction
- "Oh, I should have..." → Add as rule
- "Actually, I need to..." → Update relevant section
- "My mistake..." → Learn and document

## Recent Self-Learnings

### 2025-01-08
- ✅ Created overly complex Python-based self-learning system when simple documentation updates work better
- ✅ Should focus on real, immediate documentation updates rather than elaborate frameworks
- ✅ /learn command implementation should be simple and direct

## Categories for Future Learning

1. **Command Syntax** - Correct usage of commands
2. **Tool Availability** - What's actually installed/available
3. **Path Management** - Where to run commands from
4. **Environment Setup** - venv, TESTING=true, etc.
5. **API/SDK Usage** - Correct imports and methods
6. **Git Workflow** - Branch management, PR process
7. **Testing Protocols** - How to properly run tests

---
*Auto-updated when Claude learns from corrections*