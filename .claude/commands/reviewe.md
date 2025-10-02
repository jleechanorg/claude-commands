---
description: Enhanced Code Review Alias
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Execute Documented Workflow

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps sequentially.

## 📋 REFERENCE DOCUMENTATION

# Enhanced Code Review Alias

**Usage**: `/reviewe` (alias for `/review-enhanced`)

**Purpose**: Short alias for comprehensive enhanced code review

## Command Delegation

This command is an alias that delegates to `/review-enhanced`. 

**Execution**: 
```
/review-enhanced [arguments]
```

**Features**:
- Official Claude Code `/review` integration
- Multi-pass security analysis with code-review subagent  
- Context7 MCP for current API best practices
- GitHub integration with automated comment posting
- Categorized findings (🔴 Critical, 🟡 Important, 🔵 Suggestion, 🟢 Nitpick)

**Usage Examples**:
```bash

# Review current branch/PR

/reviewe

# Review specific PR

/reviewe 1226
/reviewe #1226
```

For complete documentation, see `/review-enhanced`.
