---
allowed-tools: Bash
description: Comprehensive PR status with GitHub MCP orchestration
---

# /gstatus - Hybrid Orchestration Architecture

**Purpose**: Enhanced PR status via command composition + Python implementation

## 🔄 Orchestration Workflow

### Phase 1: GitHub Data Collection via /commentfetch
```bash
# Fetch PR comments using existing command (eliminates duplication)
echo "📊 Fetching GitHub data via /commentfetch orchestration..."
/commentfetch
```

### Phase 2: Comprehensive Status Display
```bash
# Execute Python implementation for git operations and formatting
echo "🔄 Generating comprehensive status..."
python3 .claude/commands/gstatus.py "$ARGUMENTS"
```

## 🏗️ Architecture Benefits

- **✅ Orchestration Over Duplication**: Uses `/commentfetch` instead of reimplementing GitHub API
- **✅ Separation of Concerns**: .md orchestrates, .py implements  
- **✅ No Fake Code**: Eliminated `call_github_mcp()` placeholder
- **✅ Clean Composition**: Best of command orchestration + specialized implementation

Claude: Display the orchestrated GitHub status with enhanced architecture messaging.