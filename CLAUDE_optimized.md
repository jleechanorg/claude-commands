# CLAUDE.md - Primary Operating Protocol

## 🚨 CRITICAL: MANDATORY BRANCH HEADER PROTOCOL

**EVERY SINGLE RESPONSE MUST END WITH THIS HEADER - NO EXCEPTIONS:**

```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

**Header Generation:**
- **PREFERRED:** Use `/header` command
- **Manual:** `git branch --show-current` | `git rev-parse --abbrev-ref @{upstream}` | `gh pr list --head $(git branch --show-current) --json number,url`

**❌ NEVER SKIP THIS HEADER - USER WILL CALL YOU OUT IMMEDIATELY**

## Legend
🚨 = CRITICAL | ⚠️ = MANDATORY | ✅ = Always/Do | ❌ = Never/Don't | → = See reference

## File Organization
- **CLAUDE.md**: Primary protocol (this file)
- **.cursor/rules/**: Detailed documentation
- **.claude/commands/**: Command documentation
- **Evidence**: → .cursor/rules/evidence.md

## Meta-Rules

🚨 **PRE-ACTION CHECKPOINT**: "Does this violate CLAUDE.md?" before ANY action

🚨 **DUAL COMPOSITION**: Cognitive(/think) = semantic | Operational(/headless) = protocol | Tool(/execute) = direct

🚨 **NO FALSE ✅**: Only for 100% complete | Use ❌⚠️🔄 for partial

🚨 **NO POSITIVITY**: Self-critical | No premature victory

🚨 **NO PREMATURE VICTORY**: Full verification required
- Agent tasks: PR created + pushed + linked
- Direct tasks: Changes committed + pushed + tested

🚨 **NO EXCUSES FOR TEST FAILURES**: Fix ALL | 100% pass rate

🚨 **NO ASSUMPTIONS**: Wait for actual output | Don't speculate

🚨 **TRUST USER CAPABILITY**: Focus on execution accuracy

🚨 **NO FAKE IMPLEMENTATIONS**: Real > Nothing > Fake
- No placeholder code or demo files
- Audit existing before creating new
- → evidence.md for examples

🚨 **ORCHESTRATION OVER DUPLICATION**: Delegate to existing commands

🚨 **NO OVER-ENGINEERING**: Trust LLM | Enhance existing | User value first

🚨 **NO FALSE PROMISES**: Be honest about capabilities

🚨 **NO UNNECESSARY EXTERNAL APIS**: Try direct solution first

🚨 **GEMINI API JUSTIFICATION**: Only when Claude can't do it

🚨 **USE LLM CAPABILITIES**: Natural understanding over rules

🚨 **NEVER SIMULATE INTELLIGENCE**: Use actual Claude for responses

🚨 **EVIDENCE-BASED**: Extract→Show→Analyze→Fix

## Self-Learning Protocol

**AUTO-LEARN**: Document corrections immediately
**Process**: Detect → Analyze → Document → Apply → Memory MCP
**/learn**: Unified command with Memory MCP integration

## Claude Code Specific Behavior

1. **Directory**: Worktree in environment
2. **Tools**: File ops, bash, web available
3. **Test**: `TESTING=true vpython` from root
4. **Paths**: Always absolute
5. **SDK**: `from google import genai`
6. **Dates**: YYYY-MM-DD (MM=month number)
7. **Branch**: → Git Workflow
8. **Tool Explain vs Execute**: State clearly
9. **Push Verify**: Check remote after push
10. **PR Status**: OPEN=WIP | MERGED=Complete
11. **Playwright MCP**: Default browser automation
12. **Context7 MCP**: Use for API docs on errors
13. **GitHub Priority**: MCP→gh CLI→slash commands
14. **Memory Protocol**: Search on /think /learn /debug /analyze /fix /plan /execute /arch /test /pr

### 🔧 GitHub MCP Setup
**Token**: Set in `claude_mcp.sh` ~line 247
**Private Repos**: Direct functions only

## Orchestration System

**Docs**: → .claude/commands/orchestrate.md

### Agent Operation
- tmux sessions | Redis required
- `/orch` delegates only - NO direct execution
- Cost: $0.003-$0.050/task
- Task completion requires full workflow

## Project Overview

WorldArchitect.AI = AI tabletop RPG platform
Stack: Python/Flask | Gemini | Firestore | JS/Bootstrap
**Docs**: → .cursor/rules/project_overview.md

## Core Principles

**Work**: Clarify→Act | User law | No delete | Focus goal
**Response**: Structured(complex) | Direct(simple)
**Rules**: General→CLAUDE.md | Technical→lessons.mdc
**Testing**: Red-green | Test truth | → test_protocols.md

## Development Guidelines

### Standards
- SOLID, DRY | Module imports only
- Path: os.path operations | pathlib.Path
- Dynamic agents: Capability scoring
- Logging: `import logging_util`

### PR Review
- Verify current state first
- Priority: CRITICAL→HIGH→MEDIUM→LOW

### Testing Protocol
**Zero Tolerance**: Fix ALL failures
**Commands**: `./run_tests.sh`
**Real Conflicts**: Required for testing
→ .cursor/rules/test_protocols.md

### File Rules
- Never add to mvp_site/ without permission
- Add tests to existing files only
- Browser tests: Playwright MCP
- HTTP tests: requests library

## Git Workflow

| Rule | Description | Action |
|------|-------------|--------|
| Main=Truth | No direct push | PR only |
| PR Required | All changes | `gh pr create` |
| Upstream | Set tracking | `git push -u` |
| Integration | After merge | `./integrate.sh` |
| Conflicts | Analyze→Test | Document |

**Branch Protection**: Never switch without request
**Command Transparency**: Explain failures immediately

## Environment & Tools

1. **venv**: Verify activated
2. **Scripts**: Idempotent, any directory
3. **Tests**: From project root
4. **Logs**: `/tmp/worldarchitectai_logs/`
5. **Tool Failure**: Try alternative
→ .cursor/rules/validation_commands.md

## Operations Guide

### Memory MCP
- Search first: `mcp__memory-server__search_nodes`
- Create entities with observations
- Build relationships

### TodoWrite
- Required: 3+ steps, complex tasks
- Flow: pending→in_progress→completed

### Common Ops
- MultiEdit: 3-4 max per call
- Context: Check % before complex ops
- Backups: → /tmp before major changes

## Slash Commands

**Docs**: → .claude/commands/

### Classification
- **Cognitive**: /think /arch /debug (semantic)
- **Operational**: /headless /orch (protocol)
- **Tool**: /execute /test /pr (direct)

### Critical
- `/execute`: TodoWrite checklist required
- `/orch`: Monitor only, no execution
- `/learn`: Memory MCP integration

## Special Protocols

### PR Comments
Address ALL sources | Include suppressed
Data loss warnings = CRITICAL

### Testing
- Browser: Playwright MCP only
- HTTP: requests only
- Real API: User decides cost

### References
PR format: "PR #123: https://github.com/..."

## Quick Reference

- Test: `TESTING=true vpython mvp_site/test.py`
- Branch: `./integrate.sh`
- All Tests: `./run_tests.sh`
- Deploy: `./deploy.sh`

## Additional Docs

- **Lessons**: → .cursor/rules/lessons.mdc
- **Examples**: → .cursor/rules/examples.md
- **Evidence**: → .cursor/rules/evidence.md
- **Commands**: → .cursor/rules/validation_commands.md

## API Timeout Prevention

Edits: 3-4 max | Think: 5-6 max | Response: Bullets | Tools: Batch