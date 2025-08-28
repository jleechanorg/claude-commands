# Context Optimization: MCP Cleanup Plan

**Branch**: `context_fixes`
**Created**: 2025-08-27
**Priority**: CRITICAL - Context at 93% usage (186K/200K tokens)

## Problem Analysis

### Current Context Crisis
- **Usage**: 186K/200K tokens (93%) - DANGER ZONE  
- **Free Space**: Only 14.4K tokens (7.2%) remaining
- **Primary Consumer**: MCP tools consuming 99.8K tokens (49.9% of total)
- **Impact**: Session likely to exhaust context within 5-10 more operations

### MCP Tools Bloat Breakdown
**Total MCP Tools**: 186 tool definitions loaded
**Usage Reality**: Only ~10-15 tools actively used per session

#### Biggest Consumers:
1. **GitHub Server**: ~150 tools (35K+ tokens) - KEEP (essential)
2. **Playwright MCP**: 25+ tools (12K+ tokens) - REMOVE (unused)  
3. **Notion Server**: 43+ tools (8K+ tokens) - REMOVE (unused)
4. **Puppeteer Server**: 7+ tools (3K+ tokens) - REMOVE (redundant with Playwright)
5. **React MCP**: 9+ tools (4K+ tokens) - REMOVE (unused)
6. **iOS Simulator**: 15+ tools (7K+ tokens) - DISABLE BY DEFAULT (keep for future)

#### Memory Duplication Issue:
- **CLAUDE.md loaded twice**: 23.8K tokens from duplicate paths
- Original: `/Users/jleechan/projects/worldarchitect.ai/CLAUDE.md` (11.8K)
- Worktree: `/Users/jleechan/projects/worldarchitect.ai/worktree_tests2/CLAUDE.md` (12.0K)

## Implementation Plan

### Phase 1: MCP Server Cleanup (Target: 50K+ token savings)

#### Servers to REMOVE (immediate deletion):
```bash
# These servers will be completely removed from claude_mcp.sh:
- notion-server         # 43+ tools, 8K+ tokens - never used
- puppeteer-server      # 7+ tools, 3K+ tokens - redundant with playwright  
- playwright-mcp        # 25+ tools, 12K+ tokens - unused browser automation
- react-mcp            # 9+ tools, 4K+ tokens - unused React tooling
```

#### Servers to KEEP (essential):
```bash  
# Core servers that provide essential functionality:
- serena               # Semantic operations, code analysis - CRITICAL
- github-server        # GitHub operations, PR management - CRITICAL  
- filesystem          # File operations - CRITICAL
- gemini-cli-mcp      # AI assistance - USEFUL
- context7            # Documentation fetching - USEFUL
- memory-server       # Knowledge graph - USEFUL
- sequential-thinking # Enhanced reasoning - USEFUL
```

#### Servers to DISABLE BY DEFAULT (keep for future):
```bash
# ios-simulator: Keep in codebase but disabled by default
# Can be enabled manually when needed for iOS development
```

### Phase 2: Configuration Changes

#### claude_mcp.sh Modifications:
1. **Comment out unused server configurations**
2. **Add iOS simulator disable flag**  
3. **Clean up server argument arrays**
4. **Update server startup logic**

#### Expected File Changes:
- `claude_mcp.sh`: Remove/disable unused MCP server configurations
- No other files need modification (servers are self-contained)

### Phase 3: Memory Deduplication (Target: 12K token savings)

#### Root Cause:
- Multiple CLAUDE.md files being loaded from different project paths
- Worktree structure causing duplicate memory contexts

#### Solution Approach:
- Investigate memory server configuration
- Remove duplicate CLAUDE.md references  
- Consolidate project memory to single authoritative source

## Expected Results

### Token Reduction Calculation:
```
Current Usage: 186K tokens (93%)

Removals:
- Playwright MCP:     -12K tokens
- Notion Server:      -8K tokens  
- Puppeteer Server:   -3K tokens
- React MCP:          -4K tokens
- Memory Duplication: -12K tokens
- Minor cleanup:      -6K tokens
                    ---------------
Total Savings:        -45K tokens

New Usage: ~141K tokens (70.5%)
New Free Space: ~59K tokens (29.5%)
```

### Performance Impact:
- **Context Health**: 93% → 70% (YELLOW → GREEN)
- **Session Extension**: +30-45 minutes of working time
- **Tool Performance**: Faster MCP initialization and tool discovery
- **Memory Efficiency**: Cleaner context without unused tool definitions

## Implementation Steps

### Step 1: Create Backup
```bash
# Backup current claude_mcp.sh before modifications
cp claude_mcp.sh claude_mcp.sh.backup
```

### Step 2: Edit claude_mcp.sh  
```bash
# Comment out unused servers:
# notion_server_args=(...)
# puppeteer_server_args=(...)  
# playwright_args=(...)
# react_mcp_args=(...)

# Add iOS simulator disable flag
IOS_SIMULATOR_ENABLED=${IOS_SIMULATOR_ENABLED:-false}
```

### Step 3: Update Server Lists
```bash
# Remove from active server arrays:
servers=(
    # Keep essential servers only
    "serena:$serena_args"
    "github-server:$github_server_args" 
    "filesystem:$filesystem_args"
    # ... other essential servers
)
```

### Step 4: Test & Validate
```bash
# Restart Claude Code session
# Run /context to verify token reduction
# Test essential MCP functionality
```

## Rollback Plan

### If Issues Arise:
```bash
# Restore original configuration
cp claude_mcp.sh.backup claude_mcp.sh

# Restart Claude Code session  
# Verify original functionality restored
```

### Selective Re-enablement:
```bash
# If specific server needed, uncomment in claude_mcp.sh:
# server_name_args=(...)

# Add back to active servers array
# Restart session to reload
```

## Validation Criteria

### Success Metrics:
- ✅ Context usage drops to <75% (150K tokens or less)
- ✅ Free space increases to >25% (50K+ tokens available)
- ✅ Essential MCP functions remain operational (Serena, GitHub, filesystem)
- ✅ Session can continue for 30+ minutes without checkpoint

### Functionality Tests:
- ✅ Serena MCP semantic operations work
- ✅ GitHub MCP operations work (PR creation, issue management)
- ✅ Filesystem operations work (read, write, edit)  
- ✅ Command composition and slash commands functional
- ✅ Memory and context optimization hooks operational

## Risk Assessment

### Low Risk Items:
- **Unused server removal**: Servers not used in typical workflows
- **iOS simulator disable**: Can be re-enabled when needed
- **Configuration cleanup**: Non-breaking changes to unused sections

### Medium Risk Items:
- **Memory deduplication**: May affect project context loading
- **MCP initialization changes**: Could affect tool discovery timing

### Mitigation Strategies:
- **Backup original configuration** before any changes
- **Incremental changes**: Remove one server at a time if issues arise
- **Test essential functions** after each major change
- **Keep rollback plan ready** for immediate restoration

## Timeline

- **Total Duration**: 30-45 minutes
- **Phase 1 (MCP Cleanup)**: 15-20 minutes  
- **Phase 2 (Configuration)**: 10-15 minutes
- **Phase 3 (Memory Fix)**: 10-15 minutes
- **Testing & Validation**: 5-10 minutes

## Success Criteria

### Must Achieve:
1. **Context usage < 75%** (target: 70%)
2. **Free space > 25%** (target: 30%) 
3. **Essential MCP functions work** (Serena, GitHub, filesystem)
4. **Session longevity +30 minutes** minimum

### Nice to Have:
1. **Faster MCP initialization** from fewer servers
2. **Cleaner tool discovery** with focused server list  
3. **Memory efficiency gains** from deduplication
4. **iOS simulator ready** for future iOS development

This optimization will immediately resolve the context crisis and provide substantial working room for continued development work.