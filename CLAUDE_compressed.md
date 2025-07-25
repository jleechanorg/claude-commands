# CLAUDE.md - Operating Protocol

## 🚨 CRITICAL: MANDATORY BRANCH HEADER PROTOCOL

**EVERY RESPONSE MUST END WITH:**
```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

**Methods**: `/header` (preferred) | Manual: `git branch --show-current` + `git rev-parse --abbrev-ref @{upstream}` + `gh pr list`

**❌ NEVER SKIP - USER WILL CALL YOU OUT**

## Legend
🚨=CRITICAL | ⚠️=MANDATORY | ✅=Do | ❌=Don't | →=See ref

## Core Files
- CLAUDE.md: Primary protocol
- .cursor/rules/*.md: Detailed docs
- .claude/commands/: Command docs

## Meta-Rules [MR]

🚨 [MR1] **PRE-ACTION**: Ask "Violates CLAUDE.md?" before ANY action
🚨 [MR2] **NO FALSE ✅**: 100% only | Use ❌⚠️🔄 for partial
🚨 [MR3] **NO POSITIVITY**: Self-critical | No premature victory
🚨 [MR4] **NO FAKE CODE**: Real implementation > Nothing > Fake → evidence.md
🚨 [MR5] **ORCHESTRATION > DUPLICATION**: Delegate, don't reimplement
🚨 [MR6] **NO OVER-ENGINEERING**: Trust LLM | Enhance existing | User value first
🚨 [MR7] **EVIDENCE-BASED**: Extract→Analyze→Verify→Fix | Show evidence
🚨 [MR8] **COMMAND ARCHITECTURE**: Cognitive(semantic) | Operational(protocol) | Tool(direct)

## Critical Rules [CR]

🚨 [CR1] **Header PR Tracking**: Match actual work context, not just branch
🚨 [CR2] **Copilot Autonomous**: No approval prompts during /copilot
🚨 [CR3] **Task Completion**: Full verification required (PR created+pushed+linked)
🚨 [CR4] **Test Failures**: Fix ALL | No excuses | 100% pass
🚨 [CR5] **Running Commands**: Wait for output | Don't speculate
🚨 [CR6] **External APIs**: Try direct first | Justify external need
🚨 [CR7] **Import Protocol**: Module-level only | No inline/conditional
🚨 [CR8] **PR Status**: OPEN=WIP | MERGED=Complete | CLOSED=Abandoned

## Claude Code Behavior [CB]

1. Directory: Worktree shown in env
2. Tools: File ops | Bash | Web
3. Tests: `TESTING=true vpython` from root
4. Paths: Always absolute
5. SDK: `from google import genai`
6. Dates: YYYY-MM-DD (MM=month number)
7. Branch: → Git Workflow
8. Tool Explain vs Execute: State clearly
9. Push Verify: Check remote after push
10. Playwright MCP: Default browser automation
11. Context7 MCP: Use for API docs on errors
12. GitHub Priority: MCP→gh CLI→slash commands
13. Memory Protocol: Search on /think /learn /debug etc

## Project

WorldArchitect.AI = AI tabletop RPG (D&D 5e)
Stack: Python3.11/Flask | Gemini | Firestore | JS/Bootstrap | Docker
Docs: → .cursor/rules/project_overview.md

## Git Workflow [GW]

| Rule | Action | Notes |
|------|--------|-------|
| Main=Truth | ❌ push main | PR only |
| PR Required | ALL changes via PR | |
| Branch Fresh | `./integrate.sh` after merge | |
| Upstream | `git push -u origin branch` | |
| Conflicts | Analyze→Test→Document | |

## Development [DV]

- SOLID, DRY | Module imports only
- Path: os.path.dirname/join | pathlib.Path
- Dynamic agents: Capability scoring, no hardcoding
- PR Review: Verify before applying
- Test Policy: Add to existing files
- Browser Tests: Playwright MCP | testing_ui/
- HTTP Tests: requests | testing_http/

## Testing [TP]

Zero tolerance | `./run_tests.sh` | Fix ALL
Real conflicts required | Match validation exactly
→ .cursor/rules/test_protocols.md

## Orchestration [OR]

Agents: tmux sessions | Redis coordination
Commands: /orch delegates only | NO direct execution
Cost: $0.003-0.050/task
→ .claude/commands/orchestrate.md

## Operations [OP]

- Memory MCP: Search→Create→Relate
- TodoWrite: 3+ steps | pending→in_progress→completed
- MultiEdit: 3-4 max per call
- Backups: → /tmp before major changes

## Special Protocols [SP]

- PR Comments: Address ALL | Include suppressed
- Data Loss: CRITICAL priority
- Browser vs HTTP: Never confuse
- PR Refs: Full GitHub URLs

## Quick Ref

- Test: `TESTING=true vpython mvp_site/test.py`
- Branch: `./integrate.sh`
- All Tests: `./run_tests.sh`
- Deploy: `./deploy.sh`

## Evidence & Details

→ .cursor/rules/evidence.md [Evidence citations]
→ .cursor/rules/lessons.mdc [Technical lessons]
→ .cursor/rules/*.md [Detailed protocols]
→ .claude/commands/ [Command docs]

## Timeout Prevention

Edits: 3-4 max | Think: 5-6 max | Response: Bullets | Tools: Batch