# 🚨 CRITICAL: NO NEW PYTHON FILES ALLOWED

## Clean Architecture Rules

This directory maintains the **ultimate clean architecture** for the modular copilot system.

### The ONE Rule: Python = Data Collection ONLY

**Current Python Files**:
- `commentfetch.py` - The ONLY allowed Python file for pure data collection
- `base.py` - Base class for utilities (mechanical helpers only)
- `utils.py` - Utility functions (mechanical operations only)

### 🚨 FORBIDDEN: Creating New Python Files

**DO NOT CREATE** any new Python files in this directory unless:
1. The user explicitly approves with the phrase **"approve1234"**
2. The file is for pure data collection with NO intelligence
3. There is no other way to accomplish the task

### Why This Rule Exists

We've repeatedly fallen into the trap of creating Python files that:
- Pattern match on content
- Make decisions based on text
- Generate responses from templates
- Simulate understanding

This violates our core principle: **Python = Plumbing, Claude = Intelligence**

### The Clean Architecture

```
/commentfetch (Python) → data collection → comments.json
                ↓
/copilot reads all .md files for intelligence
                ↓
/fixpr - Claude reads fixpr.md and executes
/commentreply - Claude reads commentreply.md and executes
/pushl - Git operations
```

### Remember

- **NO** fixpr.py (use fixpr.md)
- **NO** commentreply.py (use commentreply.md)
- **NO** new Python files without explicit "approve1234" permission
- **YES** to .md files that Claude executes directly
- **YES** to keeping Python as dumb plumbing only

## Enforcement

Any PR that adds Python files without "approve1234" approval should be immediately rejected.

The clean architecture depends on maintaining this discipline!