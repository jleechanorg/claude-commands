---
description: GitHub Copilot Super Command
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

# GitHub Copilot Super Command

**Purpose**: Run comprehensive Copilot analysis on multiple PRs using orchestration agents

**Usage**: `/copilotsuper PR1 [PR2 PR3...]` or `/copilots PR1 [PR2 PR3...]`

**Action**: Uses orchestration system (see `orchestrate.md`) to spawn individual agents for processing multiple PRs in parallel with full Copilot analysis and fixes

## 🚀 Key Features

- **Parallel Processing**: Each PR gets its own orchestration agent working simultaneously
- **Complete Isolation**: Each agent uses isolated worktree to protect current work
- **Scalability**: Handle 10+ PRs concurrently (limited only by system resources)
- **Option 3 Architecture**: Uses integrated `copilot.py` with parallel data collection
- **Comprehensive Analysis**: Full GitHub comment extraction, test fixing, and CI resolution
- **Automatic Fixes**: Each agent commits and pushes changes to make PRs mergeable
- **Intelligent Optimization**: Skip unnecessary stages when PRs are already clean
- **Real-time Monitoring**: Track all agents' progress and aggregate results

## 🔧 Implementation Approach

**🚨 ORCHESTRATION INTEGRATION**: Uses the orchestration system's agent reuse architecture (see `orchestrate.md` for complete details).

**Core Workflow**:
1. **Parse PR Numbers**: Validate and collect PR arguments
2. **Delegate to Orchestration**: Uses `/orchestrate` to spawn individual agents per PR
3. **Agent Reuse Optimization**: Leverages orchestration's 50-80% efficiency gains through intelligent agent reuse
4. **Monitor Progress**: Track all agents via orchestration system
5. **Aggregate Results**: Compile summary from all agent results

**Individual Agent Per PR with Custom Workspace Management**:
```bash

# Delegates to orchestration system with custom workspace configuration for tmux-pr naming

for PR in $PR_LIST; do
    # Calculate workspace paths consistent with tmux-pr naming convention
    main_repo_path="$(git rev-parse --show-toplevel 2>/dev/null)"
    worktrees_root="${WORKTREE_ROOT:-"$(dirname "$main_repo_path")/.worktrees"}"
    workspace_name="tmux-pr${PR}"
    
    # Delegate to orchestration with custom workspace configuration
    /orchestrate "Run copilot analysis on PR #$PR --workspace-name $workspace_name --workspace-root $worktrees_root"
done
```

## 🏗️ Git Worktree Management

**Integrated with Orchestration System**: Each tmux agent spawns in independent git worktrees using the orchestration system's configurable workspace management, ensuring complete isolation and preventing conflicts.

**Enhanced Orchestration Integration**:
```bash

# Copilotsuper delegates to orchestration with embedded workspace configuration

for PR in $PR_LIST; do
    # Calculate workspace paths following tmux-pr{ID} naming convention
    main_repo_path="$(git rev-parse --show-toplevel 2>/dev/null)"
    worktrees_root="${WORKTREE_ROOT:-"$(dirname "$main_repo_path")/.worktrees"}"
    workspace_name="tmux-pr${PR}"
    
    # Delegate to orchestration with workspace config embedded in task description
    /orchestrate "Run copilot analysis on PR #$PR --workspace-name $workspace_name --workspace-root $worktrees_root"
done
```

**Orchestration System Integration**:
The orchestration system's `create_dynamic_agent()` function now accepts custom workspace configuration and automatically aligns agent names with workspace directories:

```python

# Enhanced orchestration agent creation with unified naming

agent_spec = {
    "name": agent_name,                               # Will be updated to match workspace_name
    "focus": f"Run copilot analysis on PR #{pr_number}",
    "workspace_config": {
        "workspace_name": f"tmux-pr{pr_number}",      # Agent name becomes: tmux-pr1234
        "workspace_root": worktrees_root              # External .worktrees directory
    }
}

# Result: Agent session name = tmux-pr1234, Workspace directory = tmux-pr1234

```

**Unified Naming & Workspace Management**:
- ✅ **Perfect Alignment**: Agent session names now match workspace directory names exactly
- ✅ **Meaningful Names**: Default orchestration uses task-based names instead of timestamps
- ✅ **Consistent PR Format**: `tmux-pr{ID}` format for all PR-related work across both systems
- ✅ **External Location**: Worktrees created in `.worktrees` directory outside main repo  
- ✅ **Reuse Optimization**: Orchestration checks for existing workspaces by name first
- ✅ **Branch Isolation**: Each task gets completely isolated git environment
- ✅ **Unified Cleanup**: Single orchestration system handles all workspace lifecycle management
- ✅ **Parameter Extraction**: Workspace configuration embedded in task descriptions and automatically extracted

**New Naming Examples**:
- **Default Tasks**: `task-agent-implement-auth` (instead of `task-agent-44509833`)
- **PR Tasks**: `tmux-pr1234` (agent name = workspace name = `tmux-pr1234`)
- **Workspaces**: Match agent names exactly (no more `agent_workspace_` prefix)

**Worktree Benefits**:
- ✅ **Perfect Isolation**: Each PR analysis in separate git environment
- ✅ **Reuse Optimization**: Existing worktrees reused for repeated analysis  
- ✅ **Consistent Naming**: `tmux-pr1234` format for easy identification
- ✅ **Safe External Location**: Created in `.worktrees` directory outside main repo
- ✅ **Automatic Cleanup**: Invalid worktrees detected and cleaned
- ✅ **Security**: PR number validation prevents path injection attacks

**Key Benefits** (via orchestration system):
- ✅ **Agent Reuse**: 50-80% efficiency gains through intelligent reuse
- ✅ **Complete Isolation**: Each PR gets dedicated agent workspace
- ✅ **100% Coverage**: Every PR processed by individual agent
- ✅ **Resource Optimization**: Strategic reuse without compromising quality

→ **See `orchestrate.md`** for complete agent reuse architecture and implementation details.

## 📋 Command Specification

### Input Validation

- **Required**: At least one PR number
- **Format**: Space-separated integers (e.g., `718 719 720`)
- **Validation**: Check PR exists and is accessible

### Process Flow

```
User: /copilotsuper 718 719 720

1. Validate PRs: Check accessibility of 718, 719, 720
2. Delegate to orchestration system (see orchestrate.md):
   - Spawns individual agents per PR with reuse optimization
   - Each PR gets dedicated agent via orchestration system
3. Orchestration handles:
   - Agent reuse optimization (50-80% efficiency gains)
   - Isolated worktree management
   - Parallel execution coordination
   - Progress monitoring
4. Aggregate results from orchestration agents
5. Present comprehensive summary report

→ See orchestrate.md for detailed agent lifecycle and reuse architecture
```

### Output Format

```
🤖 COPILOT SUPER ANALYSIS COMPLETE

📊 BATCH RESULTS:
- Processed: 3 PRs
- Fully Fixed: 2 PRs (718, 719)
- Needs Attention: 1 PR (720)

📋 DETAILED RESULTS:

✅ PR #718: handoff-reviewsuper-command
- Fixed: 5 Copilot suggestions
- Resolved: 2 failing tests
- Status: Ready to merge
- Commits: 3 new commits pushed

✅ PR #719: feature-auth-improvements
- Fixed: 3 security vulnerabilities
- Resolved: 1 CI/CD failure
- Status: Ready to merge
- Commits: 2 new commits pushed

⚠️ PR #720: database-optimization
- Fixed: 4 style issues
- Remaining: 1 performance blocker
- Status: Needs manual review
- Commits: 1 new commit pushed

🎯 SUMMARY: 2 PRs ready for merge, 1 needs attention
```

## 🎯 Use Cases

**Batch PR Cleanup**:
```bash
/copilotsuper 715 716 717 718

# Clean up multiple feature PRs before merge

```

**Release Preparation**:
```bash
/copilotsuper 720 721 722

# Ensure all release PRs are mergeable

```

**Daily Review Cycle**:
```bash
/copilots $(gh pr list --json number -q '.[].number' | head -5)

# Process 5 most recent PRs using convenient alias

```

## ⚡ Performance Considerations

**Enhanced Performance through Worktree Management**:
- **🏗️ Worktree Reuse**: Existing `tmux-pr{ID}` worktrees reused for 50-80% setup time savings
- **⚡ Parallel Processing**: All PRs processed simultaneously in isolated environments
- **📂 External Isolation**: Worktrees in dedicated `.worktrees` directory prevent repo contamination
- **♻️ Smart Cleanup**: Invalid worktrees automatically detected and cleaned for optimal performance
- **🎯 Consistent Naming**: `tmux-pr1234` format enables efficient worktree lookup and management

**Additional Performance (via orchestration system)**:
- **Agent Reuse**: 50-80% efficiency gains through intelligent agent reuse
- **Resource Optimization**: Strategic agent lifecycle management
- **Scalable Architecture**: Handle 10+ PRs with optimal resource utilization

→ **See `orchestrate.md`** for complete performance architecture and optimization details.

## 🚨 Safety Features

**Enhanced Safety through Git Worktree Isolation**:
- **🏗️ Worktree Isolation**: Each agent works in completely separate `tmux-pr{ID}` external directory
- **🔒 Branch Protection**: Absolute branch isolation - no interference with current work
- **♻️ Smart Reuse**: Existing worktrees validated before reuse, invalid ones cleaned
- **🧹 Auto Cleanup**: Orphaned worktrees detected and removed automatically
- **📍 Consistent Naming**: `tmux-pr1234` format for easy identification and management
- **🛡️ Failure Recovery**: Independent agent execution with fault tolerance
- **📂 External Structure**: Worktrees created in dedicated `.worktrees` directory outside main repo

**Additional Safety (via orchestration system)**:
- **Agent Reuse**: Intelligent agent lifecycle management
- **Resource Management**: Automatic workspace cleanup
- **Error Isolation**: Agent failures don't affect other PR processing

→ **See `orchestrate.md`** for complete orchestration safety protocols.

## 🔄 Integration with Existing Commands

**Relationship to `/copilot`**:
- `/copilot`: Single PR analysis (runs in current terminal)
- `/copilotsuper`: Multi-PR parallel processing (spawns orchestration agents)

**Synergy with `/reviewsuper`**:
- `/reviewsuper`: Critical architectural review
- `/copilotsuper`: Automated issue fixing
- **Combined workflow**: Review → Fix → Merge

## 📝 Implementation Notes

**Command Integration**: Uses orchestration system for all agent management
**Dependencies**: Orchestration system + existing `copilot.py` infrastructure
**Error Handling**: Managed by orchestration system's fault tolerance

→ **See `orchestrate.md`** for complete implementation details, dependencies, and error handling protocols.

## 🎉 Expected Benefits

- **Developer Efficiency**: Process multiple PRs without context switching
- **Merge Velocity**: Faster PR turnaround with automated fixes
- **Quality Assurance**: Consistent application of Copilot suggestions
- **Risk Reduction**: Safe batch processing without affecting current work
