# /exportcommands - Export Claude Commands to Reference Repository

**Purpose**: Comprehensive export workflow to https://github.com/jleechanorg/claude-commands for reference and sharing

**Usage**: `/exportcommands` - Executes complete export pipeline with Git operations

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
# ⚠️ REFERENCE ONLY - DO NOT USE DIRECTLY

**WARNING**: This is a reference export from a specific project setup. These configurations:
- May contain project-specific paths and settings (mvp_site/, specific database configs)
- Have not been tested in isolation
- May require significant adaptation for your environment
- Include setup-specific assumptions and dependencies
- Reference personal GitHub repositories and specific project structure

Use this as inspiration and reference, not direct implementation.

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
    # Skip project-specific files
    case "$(basename "$file")" in
        "testi.sh"|"run_tests.sh"|"copilot_inline_reply_example.sh")
            echo "Skipping project-specific file: $file"
            continue
            ;;
    esac

    # Copy and filter content
    cp "$file" "staging/commands/$(basename "$file")"

    # Apply content transformations
    sed -i 's|mvp_site/|$PROJECT_ROOT/|g' "staging/commands/$(basename "$file")"
    sed -i 's|worldarchitect\.ai|your-project.com|g' "staging/commands/$(basename "$file")"
    sed -i "s|jleechan|${USER}|g" "staging/commands/$(basename "$file")"
    sed -i 's|TESTING=true vpython|TESTING=true python|g' "staging/commands/$(basename "$file")"

    # Add project-specific warning to commands with mvp_site references
    if grep -q "PROJECT_ROOT" "staging/commands/$(basename "$file")"; then
        sed -i '1i\# ⚠️ PROJECT-SPECIFIC PATHS - Requires adaptation for your environment\n' "staging/commands/$(basename "$file")"
    fi
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

        # Apply transformations
        sed -i 's|mvp_site/|$PROJECT_ROOT/|g' "staging/scripts/$script_name"
        sed -i 's|worldarchitect\.ai|your-project.com|g' "staging/scripts/$script_name"
        sed -i 's|/home/jleechan/projects/worldarchitect.ai|$WORKSPACE_ROOT|g' "staging/scripts/$script_name"
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

**🚨 Orchestration System Export** (`orchestration/` → `orchestration/`) - **WIP PROTOTYPE**:
- Export complete multi-agent task delegation system with Redis coordination
- **Architecture**: tmux-based agents (frontend, backend, testing, opus-master) with A2A communication
- **Usage**: `/orch [task]` for autonomous delegation, costs $0.003-$0.050/task
- **Requirements**: Redis server, tmux, Python venv, specialized agent workspaces
- Document autonomous workflow: task creation → agent assignment → execution → PR creation
- Include monitoring via `/orch monitor agents` and direct tmux attachment procedures
- Add scaling guidance for agent capacity and workload distribution
- **Status**: Active development prototype - successful task completion verified with PR generation

**🤖 Claude Bot Self-Hosting System Export** (`claude-bot-commands/` → `claude-bot-commands/`) - **PRODUCTION READY**:
- Export complete GitHub-based Claude command processing system for self-hosted deployments
- **Architecture**: GitHub Actions workflow with self-hosted runner executing Claude commands via repository issues
- **Components**: Server (`claude-bot-server.py`), workflow processor, debugging tools, comprehensive test suite
- **Features**: Repository-based command processing, automated PR creation, threaded comment responses
- **Usage**: Post command as GitHub issue → Self-hosted runner processes → Claude executes → Results posted
- **Requirements**: GitHub repository, self-hosted runner, Python environment, Claude Code CLI
- **Installation**: Complete setup guide with runner configuration and repository integration
- **Benefits**: Repository-native command processing, version-controlled command history, automated workflows

**⚙️ Automated PR Fixer System Export** (`automation/` → `automation/`) - **PRODUCTION READY**:
- Export intelligent cron-based PR automation system with comprehensive error handling
- **Core Script**: `simple_pr_batch.sh` - Autonomous PR analysis and fixing via `/copilot` integration
- **Cron Configuration**: `cron_entry.txt` - Every 10 minutes automated PR processing
- **Features**: Timeout handling (20min), attempt tracking (max 3), cooldown periods (4hr), email notifications
- **Workflow**: Detect failing PRs → Execute `/copilot` comprehensive analysis → Apply fixes → Track attempts
- **Error Handling**: Timeout detection, max attempt limits, email alerts for manual intervention required
- **Requirements**: Claude Code CLI, GitHub CLI, email configuration, cron access
- **Installation**: Cron setup, email notification configuration, GitHub token setup


**🔬 Development Infrastructure Export** - **SPECIALIZED DEVELOPMENT TOOLS**:
- **Prototype Framework** (`prototype/` → `prototyping/`):
  - Validation and benchmarking framework for experimental implementations
  - Performance profiling, accuracy measurement, alternative approach testing
  - Migration paths from prototype to production code
- **AI Prompting Templates** (`coding_prompts/` → `ai-prompts/`):
  - Multi-agent development system with SUPERVISOR-WORKER-REVIEWER architecture
  - Specialized prompts for code research, debugging, principal engineer reviews
  - Virtual agent coordination and context independence protocols
- **Analysis Framework** (`analysis/` → `analytics/`):
  - Campaign analytics, user activity reporting, Firebase collection analytics
  - Test result analysis, performance benchmarking, data validation tools

**Configuration Export**:
- Export relevant config files (filtered for sensitive data)
- Include setup templates and environment examples
- Document MCP server requirements and configuration
- Provide installation verification procedures

### Phase 3: Documentation Generation

**README Generation**:
- Use /execute for comprehensive research and structure generation
- Include prominent warning about reference-only status
- Add detailed installation instructions with prerequisites
- Document command categories and composition principles
- **🚨 Orchestration System Highlight**: Dedicated section showcasing WIP prototype capabilities
  - Multi-agent architecture diagram and component overview
  - Real-world usage examples: `/orch "fix failing tests"`, `/orch "implement feature X"`
  - Setup walkthrough: Redis → tmux → agent workspaces → task delegation
  - Success metrics: Cost-per-task, completion rates, PR generation verification
  - Monitoring workflows: agent status, task progress, resource utilization
- **🤖 Claude Bot Self-Hosting System**: Complete repository-based command processing
  - GitHub Actions integration with self-hosted runner architecture
  - Installation guide: Repository setup → Runner configuration → Command processing
  - Usage examples: Issue-based commands → Automated execution → PR creation
  - Production deployment patterns and scaling considerations
- **⚙️ Automated PR Fixer System**: Intelligent cron-based PR maintenance
  - Autonomous `/copilot` integration for comprehensive PR analysis and fixing
  - Error handling: Timeout detection, attempt limits, email notifications
  - Installation: Cron setup → Email configuration → GitHub integration
  - Real-world metrics: Processing frequency, success rates, manual intervention triggers
- **🔬 Development Infrastructure**: Specialized development tools
  - Prototype Framework: Validation, benchmarking, experimental implementations
  - AI Prompting: Multi-agent SUPERVISOR-WORKER-REVIEWER architecture
  - Analytics Framework: Campaign analytics, performance tracking, data validation
- Include troubleshooting and adaptation guidance

**Support Documentation**:
- Generate installation guide with step-by-step procedures
- Create configuration templates for different environments
- Include troubleshooting guide with common issues
- Provide usage examples with progressive complexity

### Phase 4: Git Operations & Publishing

**Repository Management**:
```bash
# Repository cleanup and fresh export already completed in Phase 2
cd "$REPO_DIR"

# Copy exported content from staging
cp -r /tmp/claude_commands_export_*/. .

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
- Scripts with dependency documentation
- Orchestration system with setup guides ($(ls orchestration/ | wc -l) files)
- Claude Bot Self-Hosting System ($(ls claude-bot-commands/ | wc -l) files)
- Automated PR Fixer System ($(ls automation/ | wc -l) files)
- Development Infrastructure: Prototyping, AI prompts, analytics ($(find prototype/ coding_prompts/ analysis/ -name "*.py" -o -name "*.md" | wc -l) files)
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
- Complete command system (70+ commands)
- **🚨 Orchestration Infrastructure (WIP Prototype)**: Multi-agent task delegation system
  - tmux-based agent architecture with Redis coordination
  - Autonomous task execution with PR generation verification
  - Real-world cost metrics: $0.003-$0.050 per task
  - Monitoring and scaling procedures
- **🤖 Claude Bot Self-Hosting System (PRODUCTION READY)**: Repository-based command processing
  - GitHub Actions workflow with self-hosted runner architecture
  - Issue-based command processing with automated PR creation
  - Complete setup guide and debugging tools
- **⚙️ Automated PR Fixer System (PRODUCTION READY)**: Intelligent cron-based automation
  - Autonomous `/copilot` integration for comprehensive PR analysis
  - Error handling, timeout detection, and email notifications
  - 10-minute processing cycles with attempt tracking
- **🔬 Development Infrastructure**: Specialized development tools
  - Prototype framework for validation and benchmarking
  - Multi-agent AI prompting with SUPERVISOR-WORKER-REVIEWER architecture
  - Analytics framework for performance tracking and data validation
- Supporting scripts and utilities
- Documentation and setup guides

## Usage
See README.md for installation and adaptation guidance."
```

**Verification**:
- Confirm PR creation and return link
- Validate exported content structure
- Test basic command loading in clean environment
- Document any export-specific issues or requirements

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
- `testing_http/` - HTTP testing with project-specific endpoints and configurations
- `testing_ui/` - Browser testing with project-specific UI elements and workflows
- `testing_mcp/` - MCP testing infrastructure with project-specific integrations
- `ci_replica/` - CI debugging tools with project-specific environment configurations
- Business documentation (`business_plan_v1.md`, `product_spec.md`)
- Task progress files (`TASK_*_PROGRESS_SUMMARY.md`)
- Memory MCP activation guides with project paths

**NEW SYSTEM INCLUSIONS** (⚠️ MUST EXPORT):
- `claude-bot-commands/` - Complete self-hosting repository system (PRODUCTION READY)
- `automation/` - Automated PR fixer system with cron integration (PRODUCTION READY)
- `prototype/` - Validation and benchmarking framework (SPECIALIZED TOOLS)
- `coding_prompts/` - Multi-agent AI prompting templates (SPECIALIZED TOOLS)
- `analysis/` - Analytics and data analysis framework (SPECIALIZED TOOLS)
- Include installation guides and setup documentation for all systems

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
