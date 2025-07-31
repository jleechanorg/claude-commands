# GitHub Copilot Super Command

**Purpose**: Run comprehensive Copilot analysis on multiple PRs using orchestration agents

**Usage**: `/copilotsuper PR1 [PR2 PR3...]` or `/copilots PR1 [PR2 PR3...]`

**Action**: Spawn orchestration agents to process multiple PRs in parallel with full Copilot analysis and fixes

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

**Core Workflow**:
1. **Parse PR Numbers**: Validate and collect PR arguments
2. **Spawn Orchestration Agents**: Create one agent per PR using `/orch`
3. **Agent Tasks**: Each agent independently:
   - Checkouts PR branch in isolated worktree
   - Pulls latest from origin/main
   - Resolves any merge conflicts
   - Runs `/copilot` with intelligent stage optimization
   - Commits and pushes fixes (only when changes made)
4. **Monitor Progress**: Track all agents in real-time
5. **Aggregate Results**: Compile summary from all agent results

**Implementation Architecture**:
```bash
# Uses orchestration system to spawn agents
/orchestrate "Run copilot analysis on PR #$PR_NUMBER"

# Each agent executes in isolation:
python3 .claude/commands/copilot.py [PR_NUMBER]
```

**Benefits of Orchestration Approach**:
- ✅ **Parallel Execution**: All PRs processed simultaneously
- ✅ **Resource Isolation**: Each agent has dedicated workspace
- ✅ **No Branch Conflicts**: Worktrees prevent collisions
- ✅ **Scalable**: Handle many PRs concurrently
- ✅ **Fault Tolerant**: One agent failure doesn't affect others
- ✅ **Real-time Visibility**: Monitor all agents' progress

## 📋 Command Specification

### Input Validation
- **Required**: At least one PR number
- **Format**: Space-separated integers (e.g., `718 719 720`)
- **Validation**: Check PR exists and is accessible

### Process Flow
```
User: /copilotsuper 718 719 720

1. Validate PRs: Check accessibility of 718, 719, 720
2. Spawn 3 agents simultaneously:
   - Agent task-agent-XXXXX1 → PR #718
   - Agent task-agent-XXXXX2 → PR #719
   - Agent task-agent-XXXXX3 → PR #720
3. Agents work in parallel:
   - Each checks out PR in isolated worktree
   - Pulls latest from main, resolves conflicts
   - Runs copilot.py for analysis and fixes
   - Commits and pushes changes
4. Monitor progress:
   - Real-time status updates
   - Agent completion tracking
5. Aggregate results:
   - Agent 1: ✅ PR #718 - 5 issues fixed, ready to merge
   - Agent 2: ✅ PR #719 - 3 security fixes, CI passing
   - Agent 3: ⚠️ PR #720 - 1 blocking issue remains
6. Present comprehensive summary report
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

- **Parallel Processing**: All PRs processed simultaneously by independent agents
- **Resource Limits**: System can handle ~10 agents concurrently
- **Isolated Workspaces**: Each agent has dedicated worktree (no conflicts)
- **Automatic Scaling**: Agents spawned based on PR count
- **Timeout Handling**: Each agent has independent timeout (no blocking)

## 🚨 Safety Features

- **No Current Branch Changes**: Your work remains untouched
- **Agent Isolation**: Each agent works in separate worktree
- **Failure Recovery**: Other agents continue if one fails
- **Resource Cleanup**: Agents clean up their workspaces automatically
- **Conflict Prevention**: Worktrees eliminate branch conflicts

## 🔄 Integration with Existing Commands

**Relationship to `/copilot`**:
- `/copilot`: Single PR analysis (runs in current terminal)
- `/copilotsuper`: Multi-PR parallel processing (spawns orchestration agents)

**Synergy with `/reviewsuper`**:
- `/reviewsuper`: Critical architectural review
- `/copilotsuper`: Automated issue fixing
- **Combined workflow**: Review → Fix → Merge

## 📝 Implementation Notes

**Command Location**: `.claude/commands/copilotsuper.md`
**Script Location**: `claude_command_scripts/commands/copilotsuper.sh`
**Python Integration**: Leverages existing `copilot.py` infrastructure

**Dependencies**:
- GitHub CLI (`gh`) for PR operations
- Python 3 for preferred copilot script execution
- Bash for fallback copilot script execution
- Git for branch management
- Existing copilot command infrastructure (both Python and Shell)

**Error Handling**:
- Invalid PR numbers: Skip with warning
- Agent failures: Other agents continue independently
- Network issues: Each agent retries independently
- Resource limits: Queue additional PRs if agent limit reached
- Monitoring: Real-time status tracking for all agents

## 🎉 Expected Benefits

- **Developer Efficiency**: Process multiple PRs without context switching
- **Merge Velocity**: Faster PR turnaround with automated fixes
- **Quality Assurance**: Consistent application of Copilot suggestions
- **Risk Reduction**: Safe batch processing without affecting current work
