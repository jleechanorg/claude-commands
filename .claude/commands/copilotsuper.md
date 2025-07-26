# GitHub Copilot Super Command

**Purpose**: Run comprehensive Copilot analysis on multiple PRs in isolated environments

**Usage**: `/copilotsuper PR1 [PR2 PR3...]`

**Action**: Batch process multiple PRs with full Copilot analysis and fixes while preserving current branch context

## 🚀 Key Features

- **Complete Isolation**: Uses fresh branches to protect current work
- **Batch Processing**: Handle multiple PRs in sequence
- **Option 3 Architecture**: Uses new integrated `copilot.py` with parallel data collection
- **Comprehensive Analysis**: Full GitHub comment extraction (488 comments in 18.25s), test fixing, and CI resolution
- **Automatic Fixes**: Commits and pushes changes to make PRs mergeable
- **Clean Restoration**: Returns to original branch when complete

## 🔧 Implementation Approach

**Core Workflow**:
1. **Save Current Context**: Record original branch and working state
2. **For Each PR**:
   - Create isolated branch using `/nb` equivalent
   - Checkout target PR using `gh pr checkout`
   - Execute `python3 .claude/commands/copilot.py PR#`
   - Collect results and status
3. **Aggregate Results**: Compile summary of all PR fixes
4. **Return to Original**: Restore user's working context

**Implementation Preference**:
```bash
# Primary (preferred): Python implementation
python3 .claude/commands/copilot.py [PR_NUMBER]

# Fallback: Shell implementation
./claude_command_scripts/commands/copilot.sh [PR_NUMBER]
```

**Benefits over Task tool approach**:
- ✅ Uses proven working implementations (Python preferred, Shell fallback)
- ✅ Direct GitHub API integration
- ✅ Reliable execution (no slash command issues)
- ✅ Consistent behavior across environments
- ✅ Automatic selection of best available implementation

## 📋 Command Specification

### Input Validation
- **Required**: At least one PR number
- **Format**: Space-separated integers (e.g., `718 719 720`)
- **Validation**: Check PR exists and is accessible

### Process Flow
```
User: /copilotsuper 718 719 720

1. Save context: current branch = handoff-reviewsuper-command
2. Create workspace: dev_copilotsuper_[timestamp]
3. Process PR #718:
   - gh pr checkout 718
   - python3 .claude/commands/copilot.py 718
   - Record: ✅ 5 issues fixed, 2 tests resolved
4. Process PR #719:
   - gh pr checkout 719
   - python3 .claude/commands/copilot.py 719
   - Record: ✅ 3 security issues fixed, CI passing
5. Process PR #720:
   - gh pr checkout 720
   - python3 .claude/commands/copilot.py 720
   - Record: ❌ 1 blocking issue remains
6. Return to: handoff-reviewsuper-command
7. Summary report with all results
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
/copilotsuper $(gh pr list --json number -q '.[].number' | head -5)
# Process 5 most recent PRs
```

## ⚡ Performance Considerations

- **Sequential Processing**: PRs processed one at a time to avoid conflicts
- **Isolated Workspaces**: Each PR gets clean environment
- **Resource Management**: Cleanup temporary branches after completion
- **Timeout Handling**: Skip PRs that take too long to process

## 🚨 Safety Features

- **No Current Branch Changes**: Original work remains untouched
- **Failure Recovery**: Continue processing remaining PRs if one fails
- **State Preservation**: Always return to original branch and state
- **Conflict Prevention**: Use isolated branches for all operations

## 🔄 Integration with Existing Commands

**Relationship to `/copilot`**:
- `/copilot`: Single PR analysis (user runs directly)
- `/copilotsuper`: Multi-PR batch processing (AI orchestrated)

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
- Network failures: Retry with exponential backoff
- Script failures: Continue with remaining PRs
- Context restoration: Always return to original state

## 🎉 Expected Benefits

- **Developer Efficiency**: Process multiple PRs without context switching
- **Merge Velocity**: Faster PR turnaround with automated fixes
- **Quality Assurance**: Consistent application of Copilot suggestions
- **Risk Reduction**: Safe batch processing without affecting current work
