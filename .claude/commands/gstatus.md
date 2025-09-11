---
allowed-tools: Bash
description: Comprehensive PR status with GitHub MCP orchestration
---

# /gstatus - Hybrid Orchestration Architecture

**Purpose**: Enhanced PR status with comprehensive CI analysis via Python implementation

## 🚨 CRITICAL CI STATUS DETECTION

**ENHANCED**: Now properly detects failing tests and CI issues like `/fixpr` command does

### Key Improvements:
- ✅ **statusCheckRollup Analysis**: Properly parses GitHub CI status data
- ✅ **Failing Test Detection**: Identifies specific failing test suites
- ✅ **Merge State Analysis**: Distinguishes between MERGEABLE/UNSTABLE/DIRTY/CONFLICTING
- ✅ **True Mergeable Status**: Don't trust `mergeable: "MERGEABLE"` alone - validate CI passes
- ✅ **Comprehensive Coverage**: Shows passing, failing, and pending checks with details

## 🔄 Orchestration Workflow

### Phase 1: GitHub Data Collection via /commentfetch
```bash
# Fetch PR comments using existing command (eliminates duplication)
echo "📊 Fetching GitHub data via /commentfetch orchestration..."
/commentfetch
```

### Phase 2: Comprehensive Status Display with CI Analysis
```bash
# Execute Python implementation with enhanced CI status checking
echo "🔄 Generating comprehensive status with CI analysis..."
python3 .claude/commands/gstatus.py "$ARGUMENTS"
```

## 🏗️ Architecture Benefits

- **✅ Orchestration Over Duplication**: Uses `/commentfetch` instead of reimplementing GitHub API
- **✅ Separation of Concerns**: .md orchestrates, .py implements
- **✅ No Fake Code**: Eliminated `call_github_mcp()` placeholder
- **✅ Clean Composition**: Best of command orchestration + specialized implementation

Claude: Display the orchestrated GitHub status with enhanced architecture messaging.
