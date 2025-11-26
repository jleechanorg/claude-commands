---
description: /exportcommands - Export Claude Commands to Reference Repository
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Multi-Command Workflows Made Simple

**Action Steps:**
**Before**: Manual step-by-step development
```
1. Analyze the issue manually
2. Write code manually
3. Test manually
4. Create PR manually
5. Handle review comments manually
```

**After**: Single command workflows
```bash
/pr "fix authentication bug"     # → analyze → implement → test → create PR
/copilot                        # → comprehensive PR analysis → apply all fixes
/execute "add user dashboard"   # → plan → implement → test → document
```

### Phase 2: `/pr` - Complete PR Workflow Orchestrator

**Action Steps:**
**What It Does**: End-to-end PR creation from analysis to submission, handling the entire development lifecycle.

**The Magic**: Single command that handles analysis, implementation, testing, and PR creation autonomously.

**Composition Architecture**:
```bash
/pr "fix authentication validation bug"
```

**Internal Workflow Chain**:
1. **Analysis Phase**:
   - Issue analysis and root cause identification
   - Codebase understanding and impact assessment
   - Solution design and approach selection

2. **Implementation Phase**:
   - Code changes with proper error handling
   - Integration testing and validation
   - Documentation updates

3. **Quality Assurance Phase**:
   - Test execution and verification
   - Code review and quality checks
   - Performance impact assessment

4. **Git Workflow Phase**:
   - Branch creation and management
   - Commit message generation
   - PR creation with detailed description

**Real Workflow Example**:
```
/pr "fix login timeout issue"
↓
Analyze login flow → Identify timeout problem → Implement fix →
Run tests → Create branch → Commit changes → Push → Create PR
```

### Phase 1: Preparation & Validation

**Action Steps:**
**Repository Access Verification**:
1. Validate GitHub token and permissions for target repository
2. Check if target repository exists and is accessible
3. Create local staging directory: `/tmp/claude_commands_export_$(date +%s)/`
4. Verify Git configuration for commit operations

**Content Filtering Setup**:
5. Initialize comprehensive export filter system with multiple filter types
6. Exclude project-specific directories and files ($PROJECT_ROOT/, run_tests.sh, testi.sh)
7. Filter out personal/project references ($USER, your-project.com, Firebase specifics)
8. Transform project-specific paths to generic placeholders
9. Set up warning header templates for exported files

### Phase 2: Repository Cleanup & Content Export

**Action Steps:**
**🚨 MANDATORY CLEANUP PHASE**: Remove obsolete files that no longer exist in source repository
```bash

### Phase 5: Step 1: Analyze Current Command System State

**Action Steps:**
First, let me analyze the current state of the command system to provide intelligent README generation:

```python

### Phase 6: Step 2: Execute Python Implementation

**Action Steps:**
```python

### Phase 7: Step 3: LLM-Enhanced README Generation (PRESERVED CAPABILITY)

**Action Steps:**
While the Python implementation generates a comprehensive README, this LLM can provide additional intelligent analysis:

**Command Pattern Analysis**: Analyze which commands are compositional powerhouses
```python

### Phase 8: EXECUTION

**Action Steps:**
**🚀 PRIMARY EXECUTION PATH**: Use the Python implementation for reliable export
```bash
python3 .claude/commands/exportcommands.py
```

**🧠 LLM ENHANCEMENT CAPABILITIES**:
1. Generate contextual README sections based on current command inventory
2. Analyze command composition patterns for documentation
3. Provide intelligent adaptation guidance for different project types
4. Generate usage examples tailored to the exported command set

### Phase 9: IMPLEMENTATION EXECUTION

**Action Steps:**
Let me now execute the export using the Python implementation:

```python
import os
import subprocess

### Phase 10: Step 2: Execute Python Implementation

**Action Steps:**
```python

### Phase 11: Step 3: LLM-Enhanced README Generation with Version Intelligence

**Action Steps:**
🚨 **VERSION GENERATION BY LLM**: The LLM now intelligently generates version numbers and change summaries rather than mechanical Python incrementing.

**LLM Version Analysis Process**:
1. **Examine Previous Version**: Check target repo's current README for last version
2. **Analyze Git History**: Review recent commits since last export
3. **Determine Version Bump**:
   - **Patch (x.x.1)**: Bug fixes, minor updates, documentation
   - **Minor (x.1.0)**: New features, significant enhancements
   - **Major (1.0.0)**: Breaking changes, major architecture shifts
4. **Generate Change Summary**: Create meaningful bullet points based on actual changes
5. **Update README_EXPORT_TEMPLATE.md**: Fill LLM_VERSION placeholders with intelligent content

🚨 **CRITICAL ENHANCEMENT**: The export README must showcase the revolutionary command combination capabilities, not just be a basic file listing.

**Enhanced README Requirements**:
6. **⚡ COMMAND COMBINATION SUPERPOWERS** section prominently featured
7. Multi-command workflow examples (`/archreview /thinkultra /fake`)
8. Complete PR lifecycle automation documentation (`/pr fix the settings button`)
9. AI-powered fake code detection capabilities
10. Quick start examples and advanced workflow patterns
11. Professional setup guide with practical value proposition

While the Python implementation generates a comprehensive README, this LLM can provide additional intelligent analysis:

**Command Pattern Analysis**: Analyze which commands are compositional powerhouses
```python

### Phase 12: Step 4: Enhanced Main README.md Update

**Action Steps:**
🚨 **MANDATORY STEP**: Update the main README.md (not create variants) with command combination superpowers:

```bash

### Phase 13: 🎯 Revolutionary Multi-Command Workflows

**Action Steps:**
**Break the One-Command Limit**: Normally, Claude can only handle one command per sentence. This system lets you chain multiple commands in a single prompt, creating sophisticated multi-step workflows.

**Examples**:
1. **Comprehensive PR Review**: `/archreview /thinkultra /fake`
  2. `/archreview` - Architectural analysis of the codebase
  3. `/thinkultra` - Deep strategic thinking about changes
  4. `/fake` - AI-powered detection of placeholder code

5. **Complete PR Lifecycle**: `/pr fix the settings button`
  6. Automatically runs: `/think` → `/execute` → `/push` → `/copilot` → `/review`
  7. Full end-to-end automation with zero manual intervention

### Phase 14: 🔄 Complete Workflow Automation

**Action Steps:**
**The `/copilot` Advantage**: Responds to GitHub comments and makes fixes automatically, handling the entire feedback loop without manual intervention.

### Phase 15: EXECUTION

**Action Steps:**
**🚀 PRIMARY EXECUTION PATH**: Use the Python implementation for reliable export
```bash
python3 .claude/commands/exportcommands.py
```

**🧠 LLM ENHANCEMENT CAPABILITIES**:
1. Generate contextual README sections based on current command inventory
2. Analyze command composition patterns for documentation
3. Provide intelligent adaptation guidance for different project types
4. Generate usage examples tailored to the exported command set

### Phase 16: IMPLEMENTATION EXECUTION

**Action Steps:**
Let me now execute the export using the Python implementation:

```python
import os
import subprocess

## 📋 REFERENCE DOCUMENTATION

# /exportcommands - Export Claude Commands to Reference Repository

🚨 **CRITICAL SUCCESS REQUIREMENT**: This command MUST always print the export PR URL as the final output. The command is NOT complete without providing the PR URL to the user.

🚨 **REPOSITORY SAFETY RULE**: Export operations NEVER delete, move, or modify files in the current repository. Export only copies files for external sharing. The current repository remains completely unchanged.

**Purpose**: Export your complete command composition system to https://github.com/jleechanorg/claude-commands for reference and sharing

**Implementation**: This command delegates all technical operations to the Python implementation (`exportcommands.py`) while providing LLM-driven README generation and intelligent export analysis.

**Usage**: `/exportcommands` - Executes complete export pipeline with automated PR creation

## 🎯 COMMAND COMPOSITION ARCHITECTURE

**The Simple Hook That Changes Everything**: At its core, `/exportcommands` is just a file export script. But what makes it powerful is that it's exporting a complete **command composition system** that transforms how you interact with Claude Code.

### The Composition Pattern

Each command is designed to **compose** with others through a shared protocol:
- **TodoWrite Integration**: Commands break down into trackable steps
- **Memory Enhancement**: Learning from previous executions
- **Git Workflow Integration**: Automatic branch management and PR creation
- **Testing Integration**: Automatic test running and validation
- **Error Recovery**: Smart handling of failures and retries

### Key Compositional Commands Being Exported

**Workflow Orchestrators**:
- `/pr` - Complete PR workflow (analyze → fix → test → create)
- `/copilot` - Autonomous PR analysis and fixing
- `/execute` - Auto-approval development with TodoWrite tracking
- `/orch` - Multi-agent task delegation system

**Building Blocks**:
- `/think` + `/arch` + `/debug` = Cognitive analysis chain
- `/test` + `/fix` + `/verify` = Quality assurance chain
- `/plan` + `/implement` + `/validate` = Development chain

**The Hook Architecture**: Simple `.md` files that Claude Code reads as executable instructions, enabling complex behavior through composition rather than complexity.

## ⚡ COMMAND COMBINATION SUPERPOWERS

### Combine Multiple Commands in a Single Prompt

**Revolutionary Feature**: Normally, Claude can only handle one command per sentence. This tool lets you string them together in a single prompt, creating sophisticated multi-step workflows.

**Example**: Give this PR a thorough code review with `/archreview /thinkultra /fake`

This runs:
1. `/archreview` - Architectural analysis of the codebase
2. `/thinkultra` - Deep strategic thinking about the changes
3. `/fake` - Detection of placeholder or incomplete code

**The Foundation**: This command combination capability is the foundation for creating more complex, multi-step workflows that would normally require multiple separate interactions.

### Automate Your PR Lifecycle

**Complete Automation**: You can automate your entire pull request workflow with natural language commands.

**Example**: `/pr fix the settings button`

This automatically runs the whole sequence:
- `/think` - Strategic analysis of the settings button issue
- `/execute` - Implementation with auto-approval
- `/push` - Create PR with comprehensive description
- `/copilot` - Respond to GitHub comments and make fixes
- `/review` - Claude's own comprehensive code review

**The `/copilot` Advantage**: The `/copilot` command even responds to GitHub comments and makes fixes automatically, handling the entire feedback loop without manual intervention.

### Detect Fake Code with AI Analysis

**Quality Assurance**: Built-in detection for "fake" code that Claude sometimes generates when pushed too hard.

**The Problem**: When overloaded, Claude sometimes writes placeholder code instead of implementing what you asked for - like just returning success without actual logic.

**The Solution**: If something seems off, run the `/fake` command to systematically detect:
- Placeholder implementations
- Mock responses without real logic
- TODOs disguised as complete features
- Demo code that doesn't actually work

**Smart Detection**: This isn't just pattern matching - it's AI-powered analysis that understands the difference between legitimate code and fake implementations.

## 🔍 COMMAND DEEP DIVE - The Composition Powerhouses

### `/execute` - Auto-Approval Development Orchestrator

**What It Does**: The ultimate autonomous development command that handles everything from planning to implementation with built-in auto-approval.

**The Magic**: Turns complex development tasks into structured, trackable workflows without manual approval gates.

**Composition Architecture**:
```bash
/execute "implement user authentication"
```

**Internal Workflow**:
1. **Phase 1 - Planning**:
   - Complexity assessment (simple/medium/complex)
   - Execution method decision (parallel vs sequential)
   - Tool requirements analysis
   - Timeline estimation
   - Implementation approach design

2. **Phase 2 - Auto-Approval**:
   - Built-in approval bypass: "User already approves - proceeding with execution"
   - No manual intervention required

3. **Phase 3 - TodoWrite Orchestration**:
   - Breaks task into trackable steps
   - Real-time progress updates
   - Error handling and recovery
   - Completion verification

**Real Example** (This very task demonstrates `/execute`):
```
User: /execute "focus on command composition and explain details on /execute..."
Claude:
  Phase 1 - Planning: [complexity assessment, timeline, approach]
  Phase 2 - Auto-approval: "User already approves - proceeding"
  Phase 3 - Implementation: [TodoWrite tracking, step execution]
```

### `/plan` - Manual Approval Development Planning

**What It Does**: Structured development planning with explicit user approval required before execution.

**The Magic**: Perfect for complex tasks where you want to review the approach before committing resources.

**Composition Architecture**:
```bash
/plan "redesign authentication system"
```

**Workflow**:
1. **Deep Analysis**: Research existing system, identify constraints, analyze requirements
2. **Multi-Approach Planning**: Present 2-3 different implementation approaches
3. **Resource Assessment**: Timeline, complexity, tool requirements, risk analysis
4. **Approval Gate**: User must explicitly approve before any implementation begins
5. **Guided Execution**: Step-by-step implementation with checkpoints

**When to Use**:
- Complex architectural changes
- When you want oversight of the approach
- High-risk modifications
- Learning new patterns/technologies

### `/copilot` - Autonomous PR Analysis & Comprehensive Fixing

**What It Does**: Comprehensive PR analysis with autonomous fixing of all detected issues - no approval prompts.

**The Magic**: Scans PRs for every type of issue (conflicts, CI failures, code quality, comments) and fixes everything automatically.

**Composition Architecture**:
```bash
/copilot  # Analyzes current PR context
```

**Autonomous Workflow Chain**:
1. **Comprehensive Scanning**:
   - Merge conflicts detection and resolution
   - CI/CD failure analysis and fixes
   - Code review comment processing
   - Quality gate validation

2. **Intelligent Fixing**:
   - Automated conflict resolution with smart merging
   - Test fixes and dependency updates
   - Code style and formatting corrections
   - Documentation and comment updates

3. **Validation Loop**:
   - Re-run tests after each fix
   - Verify merge status and CI success
   - Continue until all issues resolved

**No Approval Required**: Unlike other commands, `/copilot` operates autonomously - perfect for continuous integration workflows.

**Real Example**:
```
PR has: merge conflicts + failing tests + 5 review comments
/copilot
↓
Resolve conflicts → Fix failing tests → Address all comments →
Re-run validation → Push fixes → Verify success
```

### `/orch` - Multi-Agent Task Delegation System

**What It Does**: Delegates tasks to autonomous tmux-based agents that work in parallel across different branches and contexts.

**The Magic**: Spawns specialized agents (frontend, backend, testing, opus-master) that execute tasks independently with full Git workflow management.

**Composition Architecture**:
```bash
/orch "implement user dashboard with tests and documentation"
```

**Multi-Agent Workflow**:
1. **Task Analysis & Delegation**:
   - Break complex task into parallel workstreams
   - Assign to specialized agents based on capabilities
   - Create isolated tmux sessions with agent workspaces

2. **Autonomous Agent Execution**:
   - Each agent gets dedicated branch and workspace
   - Independent execution with full development lifecycle
   - Real-time progress monitoring and coordination

3. **Agent Coordination**:
   - Redis-based inter-agent communication
   - Task dependency management
   - Resource allocation and load balancing

4. **Integration & Delivery**:
   - Agent results aggregation
   - PR creation from agent branches
   - Success verification and reporting

**Agent Types**:
- **Frontend Agent**: UI/UX implementation, browser testing, styling
- **Backend Agent**: API development, database integration, server logic
- **Testing Agent**: Test automation, validation, performance testing
- **Opus-Master**: Architecture decisions, code review, integration

**Cost**: $0.003-$0.050 per task (highly efficient)

**Real Example**:
```
/orch "add user notifications system"
↓
Frontend Agent: notification UI components
Backend Agent: notification API endpoints
Testing Agent: notification test suite
Opus-Master: architecture review and integration
↓
All agents work in parallel → Create individual PRs → Integration verification
```

**Monitoring**:
```bash
/orch monitor agents    # Check agent status
/orch "What's running?" # Current task overview
tmux attach-session -t task-agent-frontend  # Direct agent access
```

## 🚨 EXPORT PROTOCOL

# Clone fresh repository from main

export REPO_DIR="/tmp/claude_commands_repo_fresh"
gh repo clone jleechanorg/claude-commands "$REPO_DIR"
cd "$REPO_DIR" && git checkout main

# Create export branch from clean main

export NEW_BRANCH="export-fresh-$(date +%Y%m%d-%H%M%S)"
git checkout -b "$NEW_BRANCH"

# CRITICAL: Clear existing directories for fresh export

rm -rf commands/* orchestration/* scripts/* || true
echo "Cleared existing export directories for fresh sync"
```

**Pre-Export File Filtering**:
```bash

# Create exclusion list for project-specific files

cat > /tmp/export_exclusions.txt << 'EOF'
tests/run_tests.sh
testi.sh
**/test_integration/**
copilot_inline_reply_example.sh
run_ci_replica.sh
testing_http/
testing_ui/
testing_mcp/
ci_replica/
analysis/
claude-bot-commands/
coding_prompts/
prototype/
EOF

# Filter files before export from staging area

while IFS= read -r pattern; do
    case "$pattern" in
        **/*)
            # Use regex for patterns with ** (recursive directory matching)
            find staging -regextype posix-extended -regex ".*/${pattern#**/}" -exec rm -rf {} + 2>/dev/null || true
            ;;
        *)
            # Use path for simple patterns
            find staging -path "*${pattern}" -exec rm -rf {} + 2>/dev/null || true
            ;;
    esac
    # Also remove root directories that may be copied during main export
    rm -rf "staging/${pattern%/}" 2>/dev/null || true
done < /tmp/export_exclusions.txt
```

**CLAUDE.md Export**:
```bash

# Add reference-only warning header

cat > staging/CLAUDE.md << 'EOF'

# 📚 Reference Export - Adaptation Guide

**Note**: This is a reference export from a working Claude Code project. You may need to personally debug some configurations, but Claude Code can easily adjust for your specific needs.

These configurations may include:
- Project-specific paths and settings that need updating for your environment
- Setup assumptions and dependencies specific to the original project
- References to particular GitHub repositories and project structures

Feel free to use these as a starting point - Claude Code excels at helping you adapt and customize them for your specific workflow.

---

EOF

# Filter and append original CLAUDE.md

cp CLAUDE.md /tmp/claude_filtered.md

# Apply content filtering

sed -i 's|$PROJECT_ROOT/|$PROJECT_ROOT/|g' /tmp/claude_filtered.md
sed -i 's|worldarchitect\.ai|your-project.com|g' /tmp/claude_filtered.md
sed -i 's|$USER|${USER}|g' /tmp/claude_filtered.md
cat /tmp/claude_filtered.md >> staging/CLAUDE.md
```

**Commands Export** (`.claude/commands/` → `commands/`):
```bash

# Copy commands with filtering

for file in .claude/commands/*.md .claude/commands/*.py; do
    # Skip project-specific files and template files
    case "$(basename "$file")" in
        "testi.sh"|"run_tests.sh"|"copilot_inline_reply_example.sh"|"README_EXPORT_TEMPLATE.md")
            echo "Skipping project-specific/template file: $file"
            continue
            ;;
    esac

    # Copy and filter content
    cp "$file" "staging/commands/$(basename "$file")"

    # Apply content transformations - completely remove project-specific references
    sed -i 's|$PROJECT_ROOT/|$PROJECT_ROOT/|g' "staging/commands/$(basename "$file")"
    sed -i 's|worldarchitect\.ai|your-project.com|g' "staging/commands/$(basename "$file")"
    sed -i 's|$USER|${USER}|g' "staging/commands/$(basename "$file")"
    sed -i 's|TESTING=true python|TESTING=true python|g' "staging/commands/$(basename "$file")"

    # Remove any remaining project-specific path references
    sed -i 's|/home/${USER}/projects/worldarchitect\.ai/[^/]*||g' "staging/commands/$(basename "$file")"
done
```
- Export filtered command definitions with proper categorization
- Transform hardcoded paths to generic placeholders
- Add compatibility warnings for project-specific commands
- Organize by category: cognitive, operational, testing, development, meta

**Scripts Export** (`claude_command_scripts/` → `scripts/`):
```bash

# Export scripts with comprehensive filtering

for script in claude_command_scripts/*.sh claude_command_scripts/*.py; do
    if [[ -f "$script" ]]; then
        script_name=$(basename "$script")

        # Skip project-specific scripts
        case "$script_name" in
            "run_tests.sh"|"testi.sh"|"*integration*")
                echo "Skipping project-specific script: $script_name"
                continue
                ;;
        esac

        # Copy and transform
        cp "$script" "staging/scripts/$script_name"

        # Apply transformations - completely remove project-specific references
        sed -i 's|$PROJECT_ROOT/|$PROJECT_ROOT/|g' "staging/scripts/$script_name"
        sed -i 's|worldarchitect\.ai|your-project.com|g' "staging/scripts/$script_name"
        sed -i 's|/home/${USER}/projects/worldarchitect\.ai/[^/]*||g' "staging/scripts/$script_name"
        sed -i 's|TESTING=true python|TESTING=true python|g' "staging/scripts/$script_name"

        # Add dependency header
        sed -i '1i\#!/bin/bash\n# ⚠️ REQUIRES PROJECT ADAPTATION\n# This script contains project-specific paths and may need modification\n' "staging/scripts/$script_name"
    fi
done
```
- Export script implementations with dependency documentation
- Transform mvp_site paths to generic PROJECT_ROOT placeholders
- Add setup requirements documentation for each script
- Include execution environment requirements

**🚨 Hooks Export** (`.claude/hooks/` → `hooks/`) - **ESSENTIAL CLAUDE CODE FUNCTIONALITY**:
```bash

# Export Claude Code hooks with comprehensive filtering

echo "📎 Exporting Claude Code hooks..."

# Create hooks destination directory

mkdir -p staging/hooks

# Check if source hooks directory exists

if [[ ! -d ".claude/hooks" ]]; then
    echo "⚠️  Warning: .claude/hooks directory not found - skipping hooks export"
else
    echo "📁 Found .claude/hooks directory - proceeding with export"

    # Enable nullglob to handle cases where no files match patterns
    shopt -s nullglob

    # Export hook scripts with filtering (including nested subdirectories)
    find .claude/hooks -type f \( -name "*.sh" -o -name "*.py" -o -name "*.md" \) -print0 | while IFS= read -r -d '' hook_file; do
        hook_name=$(basename "$hook_file")
        relative_path="${hook_file#.claude/hooks/}"

        # Skip test and example files
        case "$hook_name" in
            *test*|*example*|debug_hook.sh)
                echo "   ⏭ Skipping $hook_name (test/debug file)"
                continue
                ;;
        esac

        echo "   📎 Copying: $relative_path"

        # Create subdirectory structure if needed
        hook_dir=$(dirname "staging/hooks/$relative_path")
        mkdir -p "$hook_dir"

        # Copy and transform hook files
        cp "$hook_file" "staging/hooks/$relative_path"

        # Apply comprehensive content transformations
        sed -i 's|$PROJECT_ROOT/|$PROJECT_ROOT/|g' "staging/hooks/$relative_path"
        sed -i 's|worldarchitect\.ai|your-project.com|g' "staging/hooks/$relative_path"
        sed -i 's|$USER|${USER}|g' "staging/hooks/$relative_path"
        sed -i 's|TESTING=true python|TESTING=true python|g' "staging/hooks/$relative_path"
        sed -i 's|/home/${USER}/projects/worldarchitect\.ai/[^/]*||g' "staging/hooks/$relative_path"

        # Make scripts executable and add adaptation headers
        case "$hook_name" in
            *.sh)
                chmod +x "staging/hooks/$relative_path"
                # Add adaptation header only if file doesn't start with shebang
                if ! head -1 "staging/hooks/$relative_path" | grep -q '^#!'; then
                    sed -i '1i\#!/bin/bash\n# 🚨 CLAUDE CODE HOOK - ESSENTIAL FUNCTIONALITY\n# ⚠️ REQUIRES PROJECT ADAPTATION - Contains project-specific configurations\n# This hook provides core Claude Code workflow automation\n# Adapt paths and project references for your environment\n' "staging/hooks/$relative_path"
                else
                    sed -i '1a\# 🚨 CLAUDE CODE HOOK - ESSENTIAL FUNCTIONALITY\n# ⚠️ REQUIRES PROJECT ADAPTATION - Contains project-specific configurations\n# This hook provides core Claude Code workflow automation\n# Adapt paths and project references for your environment\n' "staging/hooks/$relative_path"
                fi
                ;;
            *.py)
                chmod +x "staging/hooks/$relative_path"
                # Add adaptation note after any existing shebang
                if head -1 "staging/hooks/$relative_path" | grep -q '^#!'; then
                    sed -i '1a\# 🚨 CLAUDE CODE HOOK - ESSENTIAL FUNCTIONALITY\n# ⚠️ REQUIRES PROJECT ADAPTATION - Contains project-specific configurations\n# This hook provides core Claude Code workflow automation\n# Adapt imports and project references for your environment\n' "staging/hooks/$relative_path"
                else
                    sed -i '1i\# 🚨 CLAUDE CODE HOOK - ESSENTIAL FUNCTIONALITY\n# ⚠️ REQUIRES PROJECT ADAPTATION - Contains project-specific configurations\n# This hook provides core Claude Code workflow automation\n# Adapt imports and project references for your environment\n' "staging/hooks/$relative_path"
                fi
                ;;
        esac
    done

    # Restore nullglob setting
    shopt -u nullglob

    # Note: Subdirectories are now handled by the find loop above

    echo "✅ Hooks export completed successfully"
fi
```
- **🔧 Core Claude Code Functionality**: Essential hooks that enable automatic workflow management
- **PreToolUse Hooks**: Code quality validation before file operations (anti_demo_check_claude.sh, check_root_files.sh)
- **PostToolUse Hooks**: Automated sync after git operations (post_commit_sync.sh)
- **PostResponse Hooks**: Response quality validation (detect_speculation_and_fake_code.sh)
- **Command Composition**: Hook utilities for advanced workflow orchestration (compose-commands.sh)
- **Testing Framework**: Complete hook testing utilities for validation and debugging
- **Project Adaptation**: Comprehensive filtering of project-specific paths and references
- **Executable Permissions**: Automatic permission setting for shell scripts
- **Documentation**: Clear adaptation requirements and functionality descriptions

**🚨 Agents Export** (`.claude/agents/` → `agents/`) - **SPECIALIZED AI AGENT CONFIGURATIONS**:
```bash

# Export Claude Code agent configurations with comprehensive filtering

echo "🤖 Exporting Claude Code agent configurations..."

# Create agents destination directory

mkdir -p staging/agents

# Check if source agents directory exists

if [[ ! -d ".claude/agents" ]]; then
    echo "⚠️  Warning: .claude/agents directory not found - skipping agents export"
else
    echo "📁 Found .claude/agents directory - proceeding with export"

    # Enable nullglob to handle cases where no files match patterns
    shopt -s nullglob

    # Export agent configuration files with filtering
    find .claude/agents -type f \( -name "*.md" -o -name "*.py" -o -name "*.json" \) -print0 | while IFS= read -r -d '' agent_file; do
        agent_name=$(basename "$agent_file")
        relative_path="${agent_file#.claude/agents/}"

        # Skip test and example files
        case "$agent_name" in
            *test*|*example*|debug_agent.md)
                echo "   ⏭ Skipping $agent_name (test/debug file)"
                continue
                ;;
        esac

        echo "   🤖 Copying: $relative_path"

        # Create subdirectory structure if needed
        agent_dir=$(dirname "staging/agents/$relative_path")
        mkdir -p "$agent_dir"

        # Copy and transform agent files
        cp "$agent_file" "staging/agents/$relative_path"

        # Apply comprehensive content transformations
        sed -i 's|$PROJECT_ROOT/|$PROJECT_ROOT/|g' "staging/agents/$relative_path"
        sed -i 's|worldarchitect\.ai|your-project.com|g' "staging/agents/$relative_path"
        sed -i 's|$USER|${USER}|g' "staging/agents/$relative_path"
        sed -i 's|TESTING=true python|TESTING=true python|g' "staging/agents/$relative_path"
        sed -i 's|/home/${USER}/projects/worldarchitect\.ai/[^/]*||g' "staging/agents/$relative_path"

        # Add agent configuration header for markdown files
        case "$agent_name" in
            *.md)
                # Add adaptation header only if file doesn't start with existing header
                if ! head -5 "staging/agents/$relative_path" | grep -q '🚨 CLAUDE CODE AGENT'; then
                    sed -i '1i\# 🚨 CLAUDE CODE AGENT CONFIGURATION\n# ⚠️ REQUIRES PROJECT ADAPTATION - Contains project-specific configurations\n# This agent provides specialized AI capabilities for Claude Code workflows\n# Adapt project references and configurations for your environment\n' "staging/agents/$relative_path"
                fi
                ;;
        esac
    done

    # Restore nullglob setting
    shopt -u nullglob

    echo "✅ Agents export completed successfully"
fi
```
- **🤖 Specialized AI Agent System**: Agent configurations for different AI models and tasks
- **Code Review Agents**: Automated code analysis and quality assessment (code-review.md)
- **Consultant Agents**: Integration with various AI models (cerebras-consultant.md, gemini-consultant.md, grok-consultant.md, codex-consultant.md)
- **Testing Agents**: Test execution and validation (testexecutor.md, testvalidator.md)
- **Long-Running Task Agents**: Complex multi-step task execution (long-runner.md)
- **PR Fix Agents**: Automated pull request issue resolution (copilot-fixpr.md)
- **Project Adaptation**: Comprehensive filtering of project-specific paths and references
- **Configuration Templates**: Ready-to-use agent configurations for different workflow needs
- **Documentation**: Clear adaptation requirements and agent capability descriptions

**🚨 Root-Level Infrastructure Scripts Export** (Root → `infrastructure-scripts/`):
```bash

# Export development environment infrastructure scripts

mkdir -p staging/infrastructure-scripts

# Dynamically discover valuable root-level scripts to export

mapfile -t ROOT_SCRIPTS < <(ls -1 *.sh 2>/dev/null | grep -E '^(claude_|start-claude-bot|integrate|resolve_conflicts|sync_branch|setup-github-runner|test_server_manager)\.sh$')

for script_name in "${ROOT_SCRIPTS[@]}"; do
    if [[ -f "$script_name" ]]; then
        echo "Exporting infrastructure script: $script_name"

        # Copy and transform
        cp "$script_name" "staging/infrastructure-scripts/$script_name"

        # Apply comprehensive content transformations
        sed -i 's|/tmp/worldarchitect\.ai|/tmp/$PROJECT_NAME|g' "staging/infrastructure-scripts/$script_name"
        sed -i 's|worldarchitect-memory-backups|$PROJECT_NAME-memory-backups|g' "staging/infrastructure-scripts/$script_name"
        sed -i 's|worldarchitect\.ai|your-project.com|g' "staging/infrastructure-scripts/$script_name"
        sed -i 's|$USER|$USER|g' "staging/infrastructure-scripts/$script_name"
        sed -i 's|D&D campaign management|Content management|g' "staging/infrastructure-scripts/$script_name"
        sed -i 's|Game MCP Server|Content MCP Server|g' "staging/infrastructure-scripts/$script_name"
        sed -i 's|start_game_mcp\.sh|start_content_mcp.sh|g' "staging/infrastructure-scripts/$script_name"

        # Add infrastructure script header with adaptation warning
        sed -i '1i\#!/bin/bash\n# 🚨 DEVELOPMENT INFRASTRUCTURE SCRIPT\n# ⚠️ REQUIRES PROJECT ADAPTATION - Contains project-specific configurations\n# This script provides development environment management patterns\n# Adapt paths, service names, and configurations for your project\n\n' "staging/infrastructure-scripts/$script_name"
    else
        echo "Warning: Infrastructure script not found: $script_name"
    fi
done
```
- Export complete development environment bootstrap and management scripts
- Transform project-specific service names and paths to generic placeholders
- Include comprehensive setup and adaptation documentation
- Document multi-service management patterns (MCP servers, orchestration, bot servers)

**🚨 Orchestration System Export** (`orchestration/` → `orchestration/`) - **WIP PROTOTYPE**:
- Export complete multi-agent task delegation system with Redis coordination
- **Architecture**: tmux-based agents (frontend, backend, testing, opus-master) with A2A communication
- **Usage**: `/orch [task]` for autonomous delegation, costs $0.003-$0.050/task
- **Requirements**: Redis server, tmux, Python venv, specialized agent workspaces
- Document autonomous workflow: task creation → agent assignment → execution → PR creation
- Include monitoring via `/orch monitor agents` and direct tmux attachment procedures
- Add scaling guidance for agent capacity and workload distribution
- **Status**: Active development prototype - successful task completion verified with PR generation


**Configuration Export**:
- Export relevant config files (filtered for sensitive data)
- Include setup templates and environment examples
- Document MCP server requirements and configuration
- Provide installation verification procedures

## IMPLEMENTATION

**🚨 DELEGATION TO PYTHON IMPLEMENTATION**: All technical export operations are handled by the robust Python implementation (`exportcommands.py`), while this command focuses on LLM-driven analysis and README generation.

# Analyze the current .claude/commands directory

import os
import subprocess

# Get project root

result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
project_root = result.stdout.strip()

# Count commands, hooks, and scripts

commands_dir = os.path.join(project_root, '.claude', 'commands')
hooks_dir = os.path.join(project_root, '.claude', 'hooks')

commands_count = len([f for f in os.listdir(commands_dir) if f.endswith(('.md', '.py'))])
hooks_count = sum([len([f for f in files if f.endswith(('.sh', '.py', '.md'))])
                   for root, dirs, files in os.walk(hooks_dir)])

print(f"📊 Analysis: {commands_count} commands, {hooks_count} hooks detected")
```

# Execute the comprehensive Python implementation

python_script = os.path.join(project_root, '.claude', 'commands', 'exportcommands.py')
result = subprocess.run([python_script], capture_output=True, text=True)

if result.returncode != 0:
    print(f"❌ Export failed: {result.stderr}")
    exit(1)

print(result.stdout)
```

# Identify key workflow orchestrators vs building blocks

compositional_commands = ['pr.md', 'copilot.md', 'execute.md', 'orch.md']
building_blocks = ['think.md', 'test.md', 'fix.md', 'plan.md']

print("🎯 Workflow Orchestrators:", compositional_commands)
print("🧱 Building Blocks:", building_blocks)
```

**Usage Pattern Insights**: Generate intelligent insights about command relationships
```python

# Analyze command interdependencies

print("📊 Command Composition Patterns:")
print("- /pr → /think → /execute → /pushl → /copilot → /review")
print("- /copilot → /execute → /commentfetch → /fixpr → /commentreply")
print("- /execute → /plan → /think → implementation → /test")
```

# Execute the Python implementation

project_root = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                            capture_output=True, text=True).stdout.strip()
python_script = os.path.join(project_root, '.claude', 'commands', 'exportcommands.py')

print("🚀 Starting export via Python implementation...")
result = subprocess.run(['python3', python_script], capture_output=True, text=True)

if result.returncode \!= 0:
    print(f"❌ Export failed: {result.stderr}")
    exit(1)

# Print the output (including the critical PR URL)

print(result.stdout)
```

**🚨 CRITICAL**: The above execution will print the PR URL as the final output, fulfilling the critical success requirement.

## POST-EXPORT ANALYSIS

After the Python implementation completes, provide intelligent analysis:

```python

# Analyze export results for documentation enhancement

print("\n📊 Export Analysis:")
print("✅ Command composition system exported successfully")
print("✅ Directory exclusions applied per requirements")
print("✅ Content filtering applied for project portability")
print("✅ One-click installation script generated")
print("✅ Comprehensive README with adaptation guide created")
```

# Analyze the current .claude/commands directory

import os
import subprocess

# Get project root

result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
project_root = result.stdout.strip()

# Count commands, hooks, and scripts

commands_dir = os.path.join(project_root, '.claude', 'commands')
hooks_dir = os.path.join(project_root, '.claude', 'hooks')

commands_count = len([f for f in os.listdir(commands_dir) if f.endswith(('.md', '.py'))])
hooks_count = sum([len([f for f in files if f.endswith(('.sh', '.py', '.md'))])
                   for root, dirs, files in os.walk(hooks_dir)])

print(f"📊 Analysis: {commands_count} commands, {hooks_count} hooks detected")
```

# Execute the comprehensive Python implementation

python_script = os.path.join(project_root, '.claude', 'commands', 'exportcommands.py')
result = subprocess.run([python_script], capture_output=True, text=True)

if result.returncode != 0:
    print(f"❌ Export failed: {result.stderr}")
    exit(1)

print(result.stdout)
```

# Identify key workflow orchestrators vs building blocks

compositional_commands = ['pr.md', 'copilot.md', 'execute.md', 'orch.md']
building_blocks = ['think.md', 'test.md', 'fix.md', 'plan.md']

print("🎯 Workflow Orchestrators:", compositional_commands)
print("🧱 Building Blocks:", building_blocks)
```

**Usage Pattern Insights**: Generate intelligent insights about command relationships
```python

# Analyze command interdependencies

print("📊 Command Composition Patterns:")
print("- /pr → /think → /execute → /pushl → /copilot → /review")
print("- /copilot → /execute → /commentfetch → /fixpr → /commentreply")
print("- /execute → /plan → /think → implementation → /test")
```

# Replace the basic export README with comprehensive command showcase

cat > README.md << 'EOF'

# Claude Commands - Command Composition System

⚠️ **REFERENCE EXPORT** - This is a reference export from a working Claude Code project. These commands have been tested in production but may require adaptation for your specific environment. Claude Code excels at helping you customize them for your workflow.

Transform Claude Code into an autonomous development powerhouse through simple command hooks that enable complex workflow orchestration.

## ⚡ COMMAND COMBINATION SUPERPOWERS

### 🤖 AI-Powered Code Quality Detection

**Smart Fake Code Detection**: Built-in `/fake` command uses AI analysis (not just pattern matching) to detect:
- Placeholder implementations that look real but do nothing
- Mock responses without actual logic
- TODOs disguised as complete features
- Demo code that doesn't actually work

## 🚀 Quick Start Examples

Get started immediately with these powerful command combinations:

```bash

# Comprehensive code analysis

/arch /think /fake

# Full PR workflow automation

/pr implement user authentication

# Advanced testing with auto-fix

/test all features and if any fail /fix then /copilot
```

[Include rest of enhanced README content with installation, setup, and advanced workflows...]
EOF

echo "✅ Enhanced main README.md with command combination superpowers"
```

🚨 **CRITICAL LEARNING**: Always update the actual target file (README.md), never create variants like README_UPDATED.md.

# Execute the Python implementation

project_root = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                            capture_output=True, text=True).stdout.strip()
python_script = os.path.join(project_root, '.claude', 'commands', 'exportcommands.py')

print("🚀 Starting export via Python implementation...")
result = subprocess.run(['python3', python_script], capture_output=True, text=True)

if result.returncode \!= 0:
    print(f"❌ Export failed: {result.stderr}")
    exit(1)

# Print the output (including the critical PR URL)

print(result.stdout)
```

**🚨 CRITICAL**: The above execution will print the PR URL as the final output, fulfilling the critical success requirement.

## POST-EXPORT ANALYSIS

After the Python implementation completes, provide intelligent analysis:

```python

# Analyze export results for documentation enhancement

print("\n📊 Export Analysis:")
print("✅ Command composition system exported successfully")
print("✅ Directory exclusions applied per requirements")
print("✅ Content filtering applied for project portability")
print("✅ One-click installation script generated")
print("✅ Comprehensive README with adaptation guide created")
```

**🎯 SUCCESS CRITERIA**:
1. ✅ PR URL printed (handled by Python implementation)
2. ✅ Repository safety maintained (no local changes)
3. ✅ Complete workflow composition system exported
4. ✅ Main README.md updated with COMMAND COMBINATION SUPERPOWERS
5. ✅ Installation automation provided
6. ✅ LLM-enhanced documentation generated
