# Claude Commands Directory

## 🎯 Philosophy: Explicit > Implicit

This directory contains Claude Code slash commands that follow the **explicit execution principle**:

- ✅ **Documentation-driven workflows** where every command is visible
- ✅ **Python-based tools** for maintainability and cross-platform support
- ✅ **No hidden wrapper scripts** - users see exactly what runs
- ❌ **Shell scripts are NOT preferred** for command implementations

## 📋 Command Guidelines

### ✅ **Preferred Approach: Python + Documentation**
- **Python scripts** (`.py`) for command logic and data processing
- **Markdown documentation** (`.md`) with explicit command sequences
- **Direct tool calls** that users can see and customize

Example workflow in `copilot.md`:
```bash
# Explicit execution - user sees every command
python3 .claude/commands/copilot.py 780
./run_ci_replica.sh
gh pr view 780 --json statusCheckRollup
python3 .claude/commands/copilot_resolver.py [files]
```

### ❌ **Avoid: Shell Script Wrappers**
- **No `.sh` wrappers** that hide the actual commands being executed
- **No abstraction layers** that obscure the workflow
- **No "magic" scripts** that users can't easily understand or modify

### 🚨 **NEVER Create copilot.sh Again**
This was tried and **failed** because it:
- Hid commands behind a wrapper interface
- Contradicted the explicit execution philosophy
- Added unnecessary complexity vs. documentation-driven approach
- Made the workflow less transparent and harder to customize

## 🏗️ **Command Architecture Patterns**

### **Data Collection Commands**
- **Pattern**: `command.py` with clear argument parsing
- **Output**: Structured data files in `/tmp/` for LLM analysis
- **Integration**: Via explicit calls in documentation

### **Analysis Commands**
- **Pattern**: Standalone Python scripts that process collected data
- **Focus**: Single responsibility (conflict resolution, formatting, etc.)
- **Usage**: Direct execution with clear input/output contracts

### **Workflow Documentation**
- **Pattern**: `command.md` with step-by-step explicit execution
- **Includes**: Decision trees, troubleshooting, examples
- **Goal**: User can execute any step manually or automate selectively

## 📁 **Current Commands**

### **copilot.py** - Enhanced PR Analysis
- **Purpose**: Data collection, conflict detection, auto-fixing
- **Usage**: `python3 copilot.py [PR] [flags]`
- **Flags**: `--auto-fix`, `--merge-conflicts`, `--threaded-reply`

### **copilot_resolver.py** - Conflict Resolution
- **Purpose**: Automated conflict resolution with safety mechanisms
- **Usage**: `python3 copilot_resolver.py file1.py file2.py`
- **Features**: Backup, validation, rollback


## 🔧 **Development Guidelines**

### **Adding New Commands**
1. **Create Python script** with clear argument parsing
2. **Write documentation** with explicit usage examples
3. **Test explicit execution** - no hidden dependencies
4. **Update this README** with the new command

### **Modifying Existing Commands**
1. **Maintain explicit interfaces** - no hidden behavior changes
2. **Update documentation** to reflect new capabilities
3. **Test both automated and manual execution paths**
4. **Preserve backward compatibility** where possible

### **Command Design Principles**
- **Single Responsibility**: Each command does one thing well
- **Clear Interfaces**: Obvious inputs, outputs, and side effects
- **Error Handling**: Graceful degradation with helpful error messages
- **Documentation**: Every command has usage examples and troubleshooting

## 📚 **Learning from copilot.sh Mistake**

**What Happened**: Created `copilot.sh` as a wrapper script for CI integration
**Why It Failed**: Contradicted explicit execution philosophy, hid commands
**Lesson Learned**: Documentation-driven > Script-driven for transparency
**Never Again**: No shell script wrappers for Claude commands

**Correct Approach**: Enhance `copilot.py` with CI features and document explicit usage in `copilot.md`

## 🚨 CRITICAL ANTI-PATTERNS TO AVOID

### **NEVER Recreate Hook Files**
❌ **DO NOT** create `copilot_pre_hook.py` or `copilot_post_hook.py`
❌ **DO NOT** add copilot hook configuration to `.claude/settings.toml`
## Modular Copilot Commands

The copilot system follows a **clean architecture** where only /commentfetch uses Python for data collection, and all other commands work directly through .md files:

### Clean Architecture Commands

#### The 4 Modular Commands (Each Stands Alone):

1. **`/commentfetch`** - Fetch all PR comments ✅
   - Pure Python: Collects comments from all sources
   - Output: `/tmp/copilot_${SANITIZED_BRANCH}/comments_${SANITIZED_BRANCH}.json`
   - The ONLY command that needs Python (pure data collection)

2. **`/fixpr`** - Analyze CI failures and conflicts ✅
   - Pure Markdown: fixpr.md provides all functionality
   - Claude reads fixpr.md and executes analysis directly
   - Runs CI checks, analyzes failures, suggests fixes
   - NO Python file needed

3. **`/commentreply`** - Post comment responses ✅
   - Pure Markdown: commentreply.md guides Claude
   - Claude generates and posts replies directly via `gh api`
   - NO Python middleman, NO intermediate files
   - Direct execution with full transparency

4. **`/pushl`** - Push changes to remote ✅
   - Existing command for git operations
   - Handles add, commit, push workflow

#### Orchestration:
- **`/copilot`** - Intelligent orchestrator that chains the above commands
- Adapts workflow based on PR needs
- Ensures 100% comment coverage with DONE/NOT DONE

### Clean Architecture Principles

**Minimal Python, Maximum Claude Intelligence**

The clean approach:
- **Python**: ONLY for /commentfetch data collection
- **.md files**: Complete command implementations for /fixpr and /commentreply
- **Claude**: Executes .md instructions directly, no Python middleman
- **Transparency**: All actions shown before execution
- **Modularity**: Each command stands alone and can be chained

Clean data flow:
```
PHASE 1: DATA COLLECTION (Only /commentfetch uses Python)
commentfetch.py → comments.json
fixpr.py → fixes.json, comparison.json, conflicts.json
        ↓
PHASE 2: INTELLIGENT ANALYSIS (Claude + .md)
Claude reads data + applies .md intelligence
        ↓
PHASE 3: EXECUTION
Claude executes fixes directly
commentreply.py posts pre-generated replies
pushl handles git operations
```

### Why Hybrid?
- **Modularity**: Each command can stand alone
- **Composability**: Commands chain together naturally
- **Transparency**: Clear separation of data vs intelligence
- **Maintainability**: Python for stable plumbing, .md for evolving intelligence

---

**Remember**: If users can't see exactly what's running, it's probably the wrong approach.
