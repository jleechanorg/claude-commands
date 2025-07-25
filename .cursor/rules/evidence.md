# Evidence Citations for CLAUDE.md Rules

This file contains all evidence citations extracted from CLAUDE.md to reduce file size while maintaining traceability.

## Meta-Rules Evidence

### [MR1] PRE-ACTION CHECKPOINT
No specific evidence - foundational rule

### [MR2] NO FALSE ✅
No specific evidence - clarity rule

### [MR3] NO POSITIVITY
No specific evidence - behavioral rule

### [MR4] NO FAKE IMPLEMENTATIONS
- **PR #820**: 563+ lines of fake code removed (fixpr.py, commentreply.py, copilot.md duplication)
- **orchestrate_enhanced.py**: Placeholder comments frustrated user
- **Pattern**: Created Python intelligence files when .md files already handled the logic

### [MR5] ORCHESTRATION OVER DUPLICATION
- **PR #812**: 120 lines of duplicate systematic protocol removed from copilot.md
- **Pattern**: copilot.md duplicated GitHub API commands from other commands

### [MR6] NO OVER-ENGINEERING
- **PR #737**: Command composition over-engineering - built parallel command execution system instead of enhancing Claude Code CLI
- **PR #790**: Created .claude/commands/orchestrate.py instead of enhancing existing orchestration/ directory
- **Root Causes**: LLM capability underestimation, perfectionist engineering, integration avoidance

### [MR7] NO UNNECESSARY EXTERNAL APIS
- **PR #796**: GitHub comment fiasco - built Gemini integration that degraded to useless generic templates

### [MR8] EVIDENCE-BASED APPROACH
No specific evidence - methodology rule

## Critical Rules Evidence

### [CR1] Header PR Context Tracking
- **Pattern**: Recurring "PR: none" when user expects PR context to be tracked

### [CR2] Task Completion Verification
- **Example**: Agent modified schedule_branch_work.sh but no PR = TASK INCOMPLETE

### [CR3] Test Failures
- **PR #818**: Test failures required 100% fix rate, no partial acceptance

### [CR4] Command Failure Transparency
- **Pattern**: Silent git merge resolution leads to "ignored comment" perception

### [CR5] Data Loss Warnings
- **Example**: CodeRabbit data loss warning prevented silent corruption in backup script

## Development Guidelines Evidence

### Path Computation
- **PR #818**: Replaced fragile `.replace('/tests', '')` with proper directory navigation

### Dynamic Agent Assignment
- **PR #873**: Removed 150+ lines of hardcoded agent mappings

### PR Review Verification
- **PR #818**: Copilot suggested fixing 'string_type' that was already correct

### PR Comment Priority
- **PR #873**: Review fixed critical inline imports first

### Test Assertions
- **PR #818**: MBTI test checked .lower() but validation only does .strip()

### Exception Specificity
- **PR #818**: Improved test precision with Pydantic's ValidationError

### Test File Policy
- **PR #818**: CodeRabbit caught test_cache_busting_red_green.py violation

### Test With Real Conflicts
- **PR #780**: Real conflicts revealed false negative bug that clean PRs missed

## File Management Evidence

### File Deletion Impact
- **PR #722**: Required 36-file cleanup after deleting copilot.sh (695 lines)

### Scope Management
- **PR #722**: Called "consolidation" but became Option 3 rewrite with extensive cleanup

## Git Workflow Evidence

### Branch Confusion
- **PR #627/628**: Branch context confusion led to wrong PR destination

## Orchestration Evidence

### Task Completion
- **task-agent-3570**: Completed full workflow creating PR #887

### Hardcoding Anti-Pattern
- **task_dispatcher.py**: Created test agents for all tasks instead of dynamic assignment

## Setup Scripts Evidence

### Automation Setup
- **setup_automation.sh**: Successfully deployed complete cron job + monitoring system