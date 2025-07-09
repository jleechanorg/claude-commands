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
- ✅ Some test scripts handle TESTING=true internally, but always better to be explicit
- ✅ Correct format: `source venv/bin/activate && TESTING=true python testing_ui/test_*.py`

## Common Misconceptions

### Tools Available
- ❌ "Playwright not installed" - It IS installed, just needs venv
- ❌ "Can't run browser tests" - Can run them with proper setup
- ❌ "Need to simulate" - Real tools are available
- ❌ "Firebase not available" - Firebase IS available for testing
- ❌ "Gemini API not available" - Gemini API IS available for testing
- ❌ "Real APIs cost too much" - Testing with real APIs is permitted
- ⚠️ **PATTERN**: I keep assuming tools aren't available when they are!

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
- ✅ Tried `vpython` again despite knowing it doesn't exist - muscle memory from other projects
- ✅ Keep trying to `cd` into directories instead of running from project root
- ✅ **PATTERN**: Default to changing directories is wrong - always run from root!
- ✅ I tend to simulate mistakes for demonstration rather than making real ones
- ✅ Real learning comes from actual command execution, not simulated scenarios

### 2025-01-09
- ✅ User preemptively corrected me about Firebase/Gemini availability before I made the mistake
- ✅ **PATTERN**: I tend to say APIs "cost too much" or "aren't available" when they actually are
- ✅ Similar to Playwright pattern - assuming tools aren't available when they are
- ✅ Firebase and Gemini APIs ARE available for testing and should be used
- ✅ Need to stop using cost as an excuse to avoid real API testing
- ✅ **VERIFIED**: Successfully tested Firebase campaign creation and Gemini story generation
- ✅ **REAL RESULTS**: Firebase stored campaign `dss3zJKUrBAnOOwPZqPw`, Gemini generated full story response with game mechanics

## What Actually Works (Proven by Tests)

### Browser Testing Capabilities
- ✅ **Flask server management** - Tests can start/stop servers automatically
- ✅ **Real browser automation** - Playwright controls actual Chrome browser
- ✅ **Screenshot capture** - Real PNGs saved to `/tmp/worldarchitectai/browser/`
- ✅ **Test authentication** - `?test_mode=true&test_user_id=X` bypasses auth
- ✅ **Multi-step workflows** - Can navigate wizards, fill forms, click buttons
- ✅ **DOM inspection** - Can check element visibility, classes, content

### Stop Saying These Things
- ❌ "Can't run browser tests" → YES WE CAN
- ❌ "Playwright not installed" → IT IS INSTALLED
- ❌ "Need to simulate" → NO, USE REAL BROWSER
- ❌ "Can't take screenshots" → REAL SCREENSHOTS WORK
- ❌ "Can't use real Firebase" → FIREBASE IS AVAILABLE FOR TESTING
- ❌ "Can't use real Gemini" → GEMINI API IS AVAILABLE FOR TESTING
- ❌ "Costs too much money" → TESTING WITH REAL APIS IS PERMITTED

## Coverage Analysis

### 2025-01-08 Coverage Findings
- ✅ Coverage improved from 59% to 67% since last measurement
- ✅ Use `./coverage.sh` for unit tests only (default, fast ~76s)
- ✅ Use `./coverage.sh --integration` to include integration tests
- ✅ HTML report saved to `/tmp/worldarchitectai/coverage/index.html`
- ✅ Integration tests show 0% coverage when not included (by design)
- ✅ 124 unit tests all passing, excellent test suite health

### Coverage Discrepancies
- ⚠️ CLAUDE.md had outdated coverage numbers (showed 85% for files that are 70-74%)
- ✅ Updated CLAUDE.md with actual current measurements
- ✅ Coverage has more total statements now (21k vs 16k) indicating codebase growth

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