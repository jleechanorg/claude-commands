# /exportcommands - Export Claude Commands to Reference Repository

**Purpose**: Export your complete command composition system to https://github.com/jleechanorg/claude-commands for reference and sharing

**The Magic**: This simple export hook enables powerful workflow slash commands like `/pr`, `/copilot`, `/execute`, and complex multi-command compositions that turn Claude Code into an autonomous development powerhouse.

**What You're Really Exporting**: Not just commands, but a complete workflow composition architecture that enables:
- **Powerful Multi-Command Workflows**: `/pr` (analyze → fix → test → create PR), `/copilot` (comprehensive PR analysis + fixes)
- **Autonomous Development**: `/execute` with TodoWrite orchestration, `/orch` for multi-agent delegation
- **Advanced Compositions**: Commands that chain together for complex workflows like "analyze issue → implement fix → run tests → create PR → handle review comments"

**Usage**: `/exportcommands` - Executes complete export pipeline with Git operations

## 🎯 COMMAND COMPOSITION ARCHITECTURE

**The Simple Hook That Changes Everything**: At its core, `/exportcommands` is just a file export script. But what makes it powerful is that it's exporting a complete **command composition system** that transforms how you interact with Claude Code.

### Multi-Command Workflows Made Simple

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

### `/pr` - Complete PR Workflow Orchestrator

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

### Phase 1: Preparation & Validation

**Repository Access Verification**:
- Validate GitHub token and permissions for target repository
- Check if target repository exists and is accessible
- Create local staging directory: `/tmp/claude_commands_export_$(date +%s)/`
- Verify Git configuration for commit operations

**Content Filtering Setup**:
- Initialize comprehensive export filter system with multiple filter types
- Exclude project-specific directories and files (mvp_site/, run_tests.sh, testi.sh)
- Filter out personal/project references (jleechan, worldarchitect.ai, Firebase specifics)
- Transform project-specific paths to generic placeholders
- Set up warning header templates for exported files

### Phase 2: Repository Cleanup & Content Export

**🚨 MANDATORY CLEANUP PHASE**: Remove obsolete files that no longer exist in source repository
```bash
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
automation/
claude-bot-commands/
coding_prompts/
prototype/
EOF

# Filter files before export from staging area
while IFS= read -r pattern; do
    # Remove from staging area (covers both .claude/commands files and root directories)
    find staging -path "*${pattern}" -exec rm -rf {} + 2>/dev/null || true
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
sed -i 's|mvp_site/|$PROJECT_ROOT/|g' /tmp/claude_filtered.md
sed -i 's|worldarchitect\.ai|your-project.com|g' /tmp/claude_filtered.md
sed -i "s|jleechan|${USER}|g" /tmp/claude_filtered.md
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
    sed -i 's|mvp_site/||g' "staging/commands/$(basename "$file")"
    sed -i 's|worldarchitect\.ai|your-project.com|g' "staging/commands/$(basename "$file")"
    sed -i "s|jleechan|${USER}|g" "staging/commands/$(basename "$file")"
    sed -i 's|TESTING=true vpython|TESTING=true python|g' "staging/commands/$(basename "$file")"

    # Remove any remaining project-specific path references
    sed -i 's|/home/jleechan/projects/worldarchitect\.ai/[^/]*||g' "staging/commands/$(basename "$file")"
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
        sed -i 's|mvp_site/||g' "staging/scripts/$script_name"
        sed -i 's|worldarchitect\.ai|your-project.com|g' "staging/scripts/$script_name"
        sed -i 's|/home/jleechan/projects/worldarchitect\.ai/[^/]*||g' "staging/scripts/$script_name"
        sed -i 's|TESTING=true vpython|TESTING=true python|g' "staging/scripts/$script_name"

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
        sed -i 's|mvp_site/|$PROJECT_ROOT/|g' "staging/hooks/$relative_path"
        sed -i 's|worldarchitect\.ai|your-project.com|g' "staging/hooks/$relative_path"
        sed -i "s|jleechan|${USER}|g" "staging/hooks/$relative_path"
        sed -i 's|TESTING=true vpython|TESTING=true python|g' "staging/hooks/$relative_path"
        sed -i 's|/home/jleechan/projects/worldarchitect\.ai/[^/]*||g' "staging/hooks/$relative_path"
            
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
- **PostResponse Hooks**: Response quality validation (detect_speculation.sh)
- **Command Composition**: Hook utilities for advanced workflow orchestration (compose-commands.sh)
- **Testing Framework**: Complete hook testing utilities for validation and debugging
- **Project Adaptation**: Comprehensive filtering of project-specific paths and references
- **Executable Permissions**: Automatic permission setting for shell scripts
- **Documentation**: Clear adaptation requirements and functionality descriptions

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
        sed -i 's|jleechan|$USER|g' "staging/infrastructure-scripts/$script_name"
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

### Phase 3: Install Script Generation

**🚨 MANDATORY INSTALL SCRIPT CREATION**: Create user-friendly installation script

```bash
# Create comprehensive install script for exported commands
# Ensure staging directory exists and use proper path
STAGING_DIR="${STAGING_DIR:-/tmp/claude_commands_export_$(date +%s)}"
mkdir -p "$STAGING_DIR"

cat > "$STAGING_DIR/install.sh" << 'EOF'
#!/bin/bash
# Claude Commands Installation Script
# Auto-generated by /exportcommands

set -e  # Exit on any error

echo "🚀 Installing Claude Commands..."
echo "=================================="

# Check if we're in a git repository and navigate to root
if ! git_root=$(git rev-parse --show-toplevel 2>/dev/null); then
    echo "❌ Error: Not inside a git repository" >&2
    exit 1
fi
cd "$git_root"

# Create .claude/commands directory if it doesn't exist
if [ ! -d ".claude" ]; then
    echo "📁 Creating .claude directory..."
    mkdir -p .claude
fi

if [ ! -d ".claude/commands" ]; then
    echo "📁 Creating .claude/commands directory..."
    mkdir -p .claude/commands
fi

# Copy commands from exported commands/ to .claude/commands/
echo "📋 Installing command definitions..."
if [ -d "commands" ]; then
    for file in commands/*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            # Skip README files - they belong in the repository root
            if [[ "$filename" == "README"* ]]; then
                echo "   ⏭ Skipping $filename (documentation file)"
                continue
            fi
            echo "   • $filename"
            cp "$file" ".claude/commands/$filename"
        fi
    done
    echo "✅ Commands installed to .claude/commands/"
else
    echo "⚠️  Warning: commands/ directory not found"
fi

# Create .claude/hooks directory if it doesn't exist
if [ ! -d ".claude/hooks" ]; then
    echo "📁 Creating .claude/hooks directory..."
    mkdir -p .claude/hooks
fi

# Copy hooks from exported hooks/ to .claude/hooks/ (with subdirectory support)
echo "📎 Installing Claude Code hooks..."
if [ -d "hooks" ]; then
    # Use find with NUL-delimited output to handle filenames with spaces safely
    find hooks -type f \( -name "*.sh" -o -name "*.py" -o -name "*.md" \) -print0 | while IFS= read -r -d '' hook_file; do
        relative_path="${hook_file#hooks/}"
        target_path=".claude/hooks/$relative_path"
        target_dir=$(dirname "$target_path")
        
        # Create target directory if needed
        mkdir -p "$target_dir"
        
        echo "   📎 $relative_path"
        cp "$hook_file" "$target_path"
        
        # Ensure executables keep their bit
        case "$relative_path" in
            *.sh|*.py) chmod +x "$target_path" ;;
        esac
    done
    echo "✅ Hooks installed to .claude/hooks/"
else
    echo "⚠️  Warning: hooks/ directory not found"
fi

# Copy claude_start.sh from infrastructure-scripts to root
echo "🚀 Installing startup script..."
if [ -f "infrastructure-scripts/claude_start.sh" ]; then
    echo "   • claude_start.sh"
    cp "infrastructure-scripts/claude_start.sh" "./claude_start.sh"
    chmod +x "./claude_start.sh"
    echo "✅ Startup script installed to root directory"
else
    echo "⚠️  Warning: claude_start.sh not found in infrastructure-scripts/"
fi

# Update .gitignore with copied files
echo "📝 Updating .gitignore..."
gitignore_entries=""

# Function to add gitignore entries atomically and prevent duplicates
add_to_gitignore() {
    local entry="$1"
    local comment="$2"

    if ! grep -Fq "^$comment" .gitignore 2>/dev/null; then
        echo "" >> .gitignore
        echo "$comment" >> .gitignore
        echo "$entry" >> .gitignore
        return 0
    fi
    return 1
}

# Check and add entries only if needed
entries_added=false

if add_to_gitignore ".claude/" "# Claude Commands - Auto-installed by install.sh"; then
    entries_added=true
fi
if add_to_gitignore ".claude/commands/" "# Claude Commands - Auto-installed by install.sh"; then
    entries_added=true
fi
if add_to_gitignore ".claude/hooks/" "# Claude Code Hooks - Auto-installed by install.sh"; then
    entries_added=true
fi

if add_to_gitignore "claude_start.sh" "# Claude startup script - Auto-installed"; then
    entries_added=true
fi

if [ "$entries_added" = true ]; then
    echo "✅ Updated .gitignore with installed files"
else
    echo "✅ .gitignore already contains necessary entries"
fi

echo ""
echo "🎉 Installation Complete!"
echo ""
echo "Next steps:"
echo "1. Adapt commands for your project (replace \$PROJECT_ROOT placeholders)"
echo "2. Update claude_start.sh with your project-specific paths"
echo "3. Run ./claude_start.sh to start Claude Code with MCP servers"
echo ""
echo "⚠️  Remember: These are reference commands that may need project-specific adaptation"
EOF

chmod +x "$STAGING_DIR/install.sh"
echo "✅ Created install.sh script with command installation logic"
```

**Install Script Features**:
- **Safety Checks**: Verifies git repository context
- **Directory Creation**: Creates `.claude/commands/` and `.claude/hooks/` if needed
- **Command Installation**: Copies commands from `commands/` to `.claude/commands/` (excludes README files)
- **🚨 Hooks Installation**: Copies essential Claude Code hooks from `hooks/` to `.claude/hooks/` with proper permissions
- **Executable Permissions**: Ensures all shell scripts (.sh files) are executable
- **Startup Script**: Copies `claude_start.sh` to root directory with executable permissions
- **GitIgnore Management**: Automatically adds installed files (.claude/, hooks, startup script) to .gitignore
- **User Guidance**: Provides clear next steps and adaptation requirements
- **Error Handling**: Graceful handling of missing files with warnings

### Phase 4: README Accuracy Validation & Documentation Generation

**🚨 MANDATORY README ACCURACY VALIDATION**: Verify README reflects current repo state before export

```bash
echo "🔍 Validating README accuracy against current repo state..."

# 1. Check copilot architecture accuracy
CURRENT_COPILOT_PHASES=$(grep -o "Phase [0-9]" .claude/commands/copilot.md | wc -l)
TEMPLATE_COPILOT_LAYERS=$(grep -o "Layer [0-9]" .claude/commands/README_EXPORT_TEMPLATE.md | wc -l)
echo "   Copilot phases in repo: $CURRENT_COPILOT_PHASES"
echo "   Copilot layers in template: $TEMPLATE_COPILOT_LAYERS"

if [ "$CURRENT_COPILOT_PHASES" != "$TEMPLATE_COPILOT_LAYERS" ]; then
    echo "❌ WARNING: Copilot architecture mismatch detected!"
    echo "   Current repo has $CURRENT_COPILOT_PHASES phases, template shows $TEMPLATE_COPILOT_LAYERS layers"
fi

# 2. Verify key directory structures exist
MISSING_DIRS=""
for dir in orchestration; do
    if [ ! -d "$dir" ]; then
        MISSING_DIRS="$MISSING_DIRS $dir"
    fi
done

if [ -n "$MISSING_DIRS" ]; then
    echo "❌ WARNING: Template references missing directories:$MISSING_DIRS"
else
    echo "✅ All referenced directories exist in repo"
fi

# 3. Count actual commands vs template claims
ACTUAL_COMMANDS=$(find .claude/commands/ -name "*.md" -not -name "README*" | wc -l)
TEMPLATE_CLAIM=$(grep -o "[0-9]\++" .claude/commands/README_EXPORT_TEMPLATE.md | head -1)
echo "   Actual commands: $ACTUAL_COMMANDS"
echo "   Template claims: $TEMPLATE_CLAIM"

# 4. Verify export exclusions are still accurate
echo "🔍 Checking export exclusions against current repo state..."
while IFS= read -r pattern; do
    if find . -path "*${pattern}" -type f 2>/dev/null | grep -q .; then
        echo "   Found files matching exclusion pattern: $pattern"
    fi
done << 'EOF'
tests/run_tests.sh
testi.sh
**/test_integration/**
copilot_inline_reply_example.sh
run_ci_replica.sh
testing_http/
testing_ui/
testing_mcp/
ci_replica/
EOF

echo "✅ README validation complete - proceeding with export"
```

**🚨 MANDATORY README GENERATION**: README.md is ALWAYS included in export
```bash
# CRITICAL: Always copy README from reference template to staging directory
echo "📖 Generating README.md from reference template..."
if [[ ! -f ".claude/commands/README_EXPORT_TEMPLATE.md" ]]; then
    echo "❌ ERROR: README_EXPORT_TEMPLATE.md not found"
    exit 1
fi

# Copy template to staging directory (NOT to repository directly)
cp .claude/commands/README_EXPORT_TEMPLATE.md "$STAGING_DIR/README.md"

# Apply project-agnostic transformations
sed -i 's|your-project.com|your-project.com|g' "$STAGING_DIR/README.md"
sed -i "s|jleechan|${USER}|g" "$STAGING_DIR/README.md"
sed -i 's|worldarchitect\.ai|your-project.com|g' "$STAGING_DIR/README.md"

echo "✅ README.md generated successfully in staging directory"
```

**🚨 CRITICAL: README must be copied from STAGING_DIR to REPO_DIR**:
```bash
# Copy README from staging to repository (happens in Phase 5)
cp "$STAGING_DIR/README.md" "$REPO_DIR/README.md"
echo "✅ README.md copied to repository"
```
- **🎯 COMPOSITION-FIRST DOCUMENTATION**: Template includes comprehensive technical details
  - Hook mechanism: How .md files become executable workflows
  - Multi-command chaining in single sentences with real examples
  - Nested command layers showing the full architecture depth
  - Before/after workflow transformation examples
- **🔧 TECHNICAL ARCHITECTURE DETAILS**: Template reveals the composition system depth
  - `/copilot`: 7-layer autonomous system breakdown
  - `/execute`: 3-layer orchestration system structure
  - `/pr`: 4-layer development lifecycle workflow
  - `/orch`: Multi-agent delegation with coordination layers
- **🚨 INSTALL SCRIPT DOCUMENTATION**: Template prominently features installation
  - Quick start: `./install.sh` to auto-install commands and startup script
  - Installation verification procedures
  - Troubleshooting guide for common installation issues
- **💡 COMPOSITION THROUGH SHARED PROTOCOLS**: Template explains how commands integrate
  - TodoWrite integration with trackable steps
  - Memory enhancement learning from executions
  - Git workflow integration with automatic branch/PR management
  - Error recovery with smart retry and failure handling
- **🎯 MULTI-COMMAND CHAINING EXAMPLES**: Template shows real composition patterns
  - Sequential: "/think about X then /arch the solution then /execute it"
  - Conditional: "/test and if fails /fix then /pr the changes"
  - Parallel: "/debug issue while /research best practices then /plan"
  - Full workflow: "/analyze /design /execute /pr then /copilot any issues"
- **🚨 Orchestration System Highlight**: Dedicated section showcasing WIP prototype capabilities
  - Multi-agent architecture diagram and component overview
  - Real-world usage examples: `/orch "fix failing tests"`, `/orch "implement feature X"`
  - Setup walkthrough: Redis → tmux → agent workspaces → task delegation
  - Success metrics: Cost-per-task, completion rates, PR generation verification
  - Monitoring workflows: agent status, task progress, resource utilization
- **🚨 Infrastructure Scripts**: Complete development environment management
  - **Environment Bootstrap**: `claude_start.sh` - Multi-service startup with health checks
  - **MCP Installation**: `claude_mcp.sh` - Comprehensive MCP server setup automation
  - **GitHub Integration**: `start-claude-bot.sh` - Repository-based command processing
  - **Git Workflows**: `integrate.sh`, `resolve_conflicts.sh`, `sync_branch.sh` - Branch management
  - **CI/CD Setup**: `setup-github-runner.sh` - Self-hosted runner automation
  - **Service Management**: `test_server_manager.sh` - Multi-service orchestration
  - Installation guides with adaptation requirements for different projects
  - Service configuration templates and health check patterns
- Include troubleshooting and adaptation guidance

**Support Documentation**:
- Generate installation guide with step-by-step procedures
- Create configuration templates for different environments
- Include troubleshooting guide with common issues
- Provide usage examples with progressive complexity

### Phase 5: Git Operations & Publishing

**Repository Management**:
```bash
# Repository cleanup and fresh export already completed in Phase 2
cd "$REPO_DIR"

# 🚨 CRITICAL: Copy exported content EXCLUDING unwanted directories
echo "📂 Copying export content with exclusions..."

# Get the export directory path
EXPORT_DIR=$(ls -d /tmp/claude_commands_export_* | head -1)

# Copy specific directories and files, EXCLUDING the unwanted ones
rsync -av --exclude='analysis/' --exclude='automation/' --exclude='claude-bot-commands/' --exclude='coding_prompts/' --exclude='prototype/' "$EXPORT_DIR/" . --delete-excluded

# Verify exclusions worked
echo "✅ Export copied with exclusions applied"
if [[ -d "analysis" || -d "automation" || -d "claude-bot-commands" || -d "coding_prompts" || -d "prototype" ]]; then
    echo "❌ ERROR: Unwanted directories found in export! Cleaning up..."
    rm -rf analysis automation claude-bot-commands coding_prompts prototype
    echo "✅ Cleaned up unwanted directories"
else
    echo "✅ Confirmed: No unwanted directories in export"
fi

# Commit changes with cleanup notation
git add .
git commit -m "Fresh export: Remove obsolete files, add current command system

🚨 CLEANUP APPLIED:
- Removed obsolete files that no longer exist in source repository
- Cleared existing directories for fresh sync from main branch
- Eliminated incorrect claude/ directory structure

✅ CURRENT EXPORT:
- CLAUDE.md with reference warnings
- All command definitions with categorization and proper filtering
- **🚀 INSTALL SCRIPT**: Auto-install commands to .claude/commands/ and setup claude_start.sh
- Scripts with dependency documentation
- Infrastructure Scripts: Complete development environment management ($(ls infrastructure-scripts/ | wc -l) scripts)
- Orchestration system with setup guides ($(ls orchestration/ | wc -l) files)
- Content filtering: mvp_site → \$PROJECT_ROOT, worldarchitect.ai → your-project.com
- Comprehensive README and documentation

⚠️ Reference export - requires adaptation for other projects"

# Push and create PR
git push -u origin "$export_branch"
gh pr create --title "Claude Commands Export $(date +%Y-%m-%d)" \
  --body "Automated export of Claude command system for reference.

## ⚠️ Reference Only
This export contains project-specific configurations that require adaptation.

## Contents
- **🚀 ONE-CLICK INSTALL**: `./install.sh` script auto-installs commands to `.claude/commands/`, hooks to `.claude/hooks/`, and copies `claude_start.sh`
- Complete command system (70+ commands)
- **🚨 Essential Claude Code Hooks**: Core workflow automation hooks (PreToolUse, PostToolUse, PostResponse, Stop)
  - Code quality validation before file operations
  - Automated sync after git operations
  - Response quality validation and branch header generation
- **🚨 Orchestration Infrastructure (WIP Prototype)**: Multi-agent task delegation system
  - tmux-based agent architecture with Redis coordination
  - Autonomous task execution with PR generation verification
  - Real-world cost metrics: $0.003-$0.050 per task
  - Monitoring and scaling procedures
- **🚨 Infrastructure Scripts**: Complete development environment management
  - Environment bootstrap: claude_start.sh - Multi-service startup with health checks
  - MCP installation: claude_mcp.sh - Comprehensive MCP server setup automation
  - GitHub integration: start-claude-bot.sh - Repository-based command processing
  - Git workflows: integrate.sh, resolve_conflicts.sh, sync_branch.sh - Branch management
  - CI/CD setup: setup-github-runner.sh - Self-hosted runner automation
  - Service management: test_server_manager.sh - Multi-service orchestration
- Supporting scripts and utilities
- Documentation and setup guides

## Usage
**Quick Install**: Run `./install.sh` to auto-install commands and startup script
See README.md for detailed installation and adaptation guidance."
```

**🚨 MANDATORY POST-EXPORT VALIDATION**:
```bash
echo "🔍 Post-export validation - checking exported content accuracy..."

cd "$REPO_DIR"

# 1. Validate README claims against exported content
echo "📊 Validating README claims against actual export..."
README_COMMAND_COUNT=$(grep -o "[0-9]\++" README.md | head -1)
ACTUAL_EXPORTED_COMMANDS=$(find commands/ -name "*.md" -not -name "README*" | wc -l)
echo "   README claims: ${README_COMMAND_COUNT} commands"
echo "   Actually exported: $ACTUAL_EXPORTED_COMMANDS commands"

if [ "${README_COMMAND_COUNT//+}" -gt "$ACTUAL_EXPORTED_COMMANDS" ]; then
    echo "❌ WARNING: README overstates command count!"
fi

# 2. Verify copilot architecture consistency
if grep -q "6-Layer" README.md && grep -q "7-Layer" README.md; then
    echo "❌ ERROR: Mixed copilot layer references detected in export!"
elif grep -q "6-Layer" README.md; then
    echo "✅ Copilot architecture: 6-Layer system (current)"
elif grep -q "7-Layer" README.md; then
    echo "❌ WARNING: 7-Layer system in README may be outdated"
fi

# 3. Check for accidentally exported project-specific content
echo "🔍 Scanning for project-specific content that should have been filtered..."
PROJECT_SPECIFIC_FOUND=""
if grep -r "mvp_site/" . --exclude-dir=.git >/dev/null 2>&1; then
    PROJECT_SPECIFIC_FOUND="$PROJECT_SPECIFIC_FOUND mvp_site/"
fi
if grep -r "jleechan" . --exclude-dir=.git >/dev/null 2>&1; then
    PROJECT_SPECIFIC_FOUND="$PROJECT_SPECIFIC_FOUND jleechan"
fi
if grep -r "worldarchitect\.ai" . --exclude-dir=.git >/dev/null 2>&1; then
    PROJECT_SPECIFIC_FOUND="$PROJECT_SPECIFIC_FOUND worldarchitect.ai"
fi

if [ -n "$PROJECT_SPECIFIC_FOUND" ]; then
    echo "❌ WARNING: Project-specific content found:$PROJECT_SPECIFIC_FOUND"
    echo "   This content should have been filtered during export"
else
    echo "✅ No project-specific content detected"
fi

# 4. Verify install script exists and is executable
if [ -f "install.sh" ] && [ -x "install.sh" ]; then
    echo "✅ Install script present and executable"
else
    echo "❌ ERROR: Install script missing or not executable"
fi

# 5. Check that referenced directories exist in export
echo "🔍 Verifying referenced directories exist in export..."
for dir in orchestration; do
    if [ -d "$dir" ]; then
        FILE_COUNT=$(find "$dir" -type f | wc -l)
        echo "   ✅ $dir/ ($FILE_COUNT files)"
    else
        echo "   ❌ Missing: $dir/ (referenced in README)"
    fi
done

echo "✅ Post-export validation complete"
```

**Final Verification**:
- Confirm PR creation and return link
- Validate exported content structure matches README claims
- Test basic command loading in clean environment
- Document any export-specific issues or requirements
- Run accuracy validation against current vs. exported state

## 🚨 MANDATORY FILE EXCLUSIONS

**Project-Specific Files (NEVER EXPORT)**:
- `tests/run_tests.sh` - Project-specific test runner
- `testi.sh` - Integration test script with hardcoded paths
- `run_tests_with_coverage.sh` - Coverage script with mvp_site dependencies
- `coverage.sh` - Project-specific coverage tool
- `loc.sh` - Line of code counter for mvp_site
- `run_local_server.sh` - Server launcher with hardcoded paths
- `run_test_server.sh` - Test server with project structure
- `tools/localserver.sh` - Local development server
- Files with hardcoded `mvp_site/` dependencies
- Personal configuration files with sensitive paths
- Project-specific Python scripts with database connections
- Testing scripts that require specific project setup
- Firebase connection scripts (`scripts/debug_firebase_connection.py`)
- Business plan and product specification documents
- Worktree-specific paths and configurations

**Directory Exclusions**:
- Any directory containing project-specific database configurations
- Scripts requiring specific virtual environment setup
- `scripts/` - Firebase and database-specific utilities (but INCLUDE automation/ and orchestration/ core)
- `orchestration/` workspaces with hardcoded paths (but INCLUDE orchestration system core)
- Testing infrastructure directories (as defined in export exclusion list above):
  - `testing_http/` - HTTP testing with project-specific endpoints
  - `testing_ui/` - Browser testing with project-specific UI elements
  - `testing_mcp/` - MCP testing infrastructure with project-specific integrations
  - `ci_replica/` - CI debugging tools with project-specific environment configurations
- Business documentation (`business_plan_v1.md`, `product_spec.md`)
- Task progress files (`TASK_*_PROGRESS_SUMMARY.md`)
- Memory MCP activation guides with project paths


**🚨 ROOT-LEVEL INFRASTRUCTURE SCRIPTS** (⚠️ MUST EXPORT):
- `claude_start.sh` - Complete Claude Code + MCP ecosystem startup script with multi-service management
- `claude_mcp.sh` - Comprehensive MCP server installation and configuration system
- `start-claude-bot.sh` - GitHub-based Claude bot command server startup script
- `integrate.sh` - Fresh branch creation workflow with cleanup and safety checks
- `resolve_conflicts.sh` - Systematic Git conflict resolution workflow
- `sync_branch.sh` - Branch synchronization and update patterns
- `setup-github-runner.sh` - GitHub Actions self-hosted runner setup automation
- `test_server_manager.sh` - Multi-service test server management utilities

## 🔍 CONTENT FILTERING RULES

**Automatic Text Replacements**:
```bash
# File content transformations
sed -i 's|mvp_site/|$PROJECT_ROOT/|g' "$file"
sed -i 's|worldarchitect\.ai|your-project.com|g' "$file"
sed -i "s|jleechan|${USER}|g" "$file"
sed -i 's|WorldArchitect\.AI|Your Project|g' "$file"
sed -i 's|TESTING=true vpython|TESTING=true python|g' "$file"
sed -i 's|Flask/Gunicorn|Web Framework|g' "$file"
sed -i 's|Firebase/Firestore|Database|g' "$file"
sed -i 's|serviceAccountKey\.json|database_credentials.json|g' "$file"
sed -i 's|worktree_worker[0-9]*|workspace|g' "$file"
sed -i 's|github\.com/jleechan|github.com/$USER|g' "$file"
sed -i 's|D&D 5e|Tabletop RPG|g' "$file"
sed -i 's|WorldArchitect\.AI|Your RPG Platform|g' "$file"
```

**Python Import Filtering**:
- Remove sys.path modifications pointing to mvp_site
- Replace project-specific imports with generic placeholders
- Filter out database-specific connection strings

**Command Path Filtering**:
- Replace hardcoded test paths with environment variables
- Remove references to specific virtual environments
- Generalize deployment-specific commands

## Content Transformation Rules

**Path Generalization**:
- `mvp_site/` → `$PROJECT_ROOT/`
- `/home/jleechan/projects/worldarchitect.ai/` → `$WORKSPACE_ROOT/`
- `worldarchitect.ai` → `your-project.com`
- `jleechan` → `$USER`
- Hardcoded file paths → Environment variable placeholders
- Project-specific test commands → Generic test patterns

**Project References**:
- `WorldArchitect.AI` → `Your Project`
- `D&D/RPG` specific → Generic game/app references
- Firebase/Firestore → Generic database references
- Flask/Gunicorn specifics → Generic web framework references
- Personal GitHub references → Generic repository patterns

**Command Adaptations**:
- Testing commands: Add environment setup requirements, remove hardcoded test paths
- Deployment commands: Generalize for different platforms, filter Firebase specifics
- Integration commands: Document external dependencies, remove database connection strings
- Python scripts: Remove sys.path.insert statements pointing to mvp_site
- Shell scripts: Replace vpython with python, generalize virtual environment activation

## Error Handling

**Repository Access Issues**:
- Validate GitHub token setup
- Check repository permissions
- Provide manual export fallback instructions

**Content Export Failures**:
- Log specific file processing errors and filtering issues
- Continue export with warnings for failed items and skipped project-specific files
- Provide recovery procedures for partial exports
- Validate that all mvp_site references have been properly filtered
- Ensure no personal information (jleechan, specific paths) remains in exported content

**Git Operation Failures**:
- Handle branch conflicts and naming issues
- Provide manual Git workflow instructions
- Include rollback procedures for failed operations

## Orchestration System Documentation Standards

**WIP Prototype Status Documentation**:
- Clearly mark orchestration components as active development prototypes
- Include real-world performance metrics and cost data from production usage
- Document proven workflows: task delegation → agent execution → PR creation
- Provide scaling guidance for multi-agent environments
- Include monitoring procedures for agent health and task progress

**Architecture Documentation Requirements**:
- tmux session management and agent isolation procedures
- Redis coordination protocol and A2A communication patterns
- Agent workspace setup and dependency management
- Task routing and capability-based assignment algorithms
- Recovery procedures for failed agents and orphaned tasks

**Usage Examples for Public Documentation**:
- Basic task delegation: `/orch "implement login validation"`
- Complex workflows: `/orch "fix all failing tests and create PR"`
- Monitoring operations: `/orch monitor agents` and direct tmux access
- Cost optimization: agent reuse, task batching, resource management
- Integration patterns: Claude Code CLI → orchestration → GitHub workflows

## Memory Enhancement

This command automatically searches Memory MCP for:
- Previous export experiences and lessons learned
- Command adaptation patterns and successful transformations
- Documentation improvements and user feedback
- Repository maintenance and update procedures
- Orchestration system performance data and optimization patterns

## Success Criteria

**Export Completion Verification**:
- All major content categories exported successfully
- README and documentation generated
- Git operations completed (branch, commit, push, PR)
- PR link returned to user for verification

**Content Quality Validation**:
- Reference warnings prominently displayed
- Project-specific content appropriately generalized
- Installation instructions comprehensive and testable
- Command categories properly organized

**Memory Enhancement**: This command automatically searches memory context using Memory MCP for relevant export experiences, adaptation patterns, and lessons learned from previous command sharing initiatives.
