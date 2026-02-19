#!/bin/bash

# 🚨 Claude Commands Installation Script
# Installs the complete Claude Code command system for development workflows

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Source directory (where plugin files live)
PLUGIN_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Active Claude Code directories (system-level)
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
CLAUDE_AGENTS_DIR="$CLAUDE_HOME/agents"
CLAUDE_COMMANDS_DIR="$CLAUDE_HOME/commands"
CLAUDE_SCRIPTS_DIR="$CLAUDE_HOME/scripts"
CLAUDE_SKILLS_DIR="$CLAUDE_HOME/skills"

# Source directories in plugin repo
SRC_AGENTS_DIR="$PLUGIN_SRC_DIR/.claude/agents"
SRC_COMMANDS_DIR="$PLUGIN_SRC_DIR/.claude/commands"
SRC_SCRIPTS_DIR="$PLUGIN_SRC_DIR/.claude/scripts"
SRC_SKILLS_DIR="$PLUGIN_SRC_DIR/.claude/skills"

# Legacy config
ORCHESTRATION_DIR="orchestration"
AUTOMATION_DIR="automation"
CLAUDE_BOT_DIR="claude-bot-commands"
INFRASTRUCTURE_DIR="infrastructure-scripts"

# Installation checks
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check for required tools
    local missing_tools=()

    command -v git >/dev/null 2>&1 || missing_tools+=("git")
    command -v python3 >/dev/null 2>&1 || missing_tools+=("python3")
    command -v pip >/dev/null 2>&1 || missing_tools+=("pip")

    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and run this script again."
        exit 1
    fi

    # Check for Claude Code CLI
    if ! command -v claude >/dev/null 2>&1; then
        log_warning "Claude Code CLI not found. Install from: https://claude.ai/code"
        log_info "The commands will still be installed but may require Claude Code CLI for full functionality."
    fi

    log_success "Prerequisites check completed"
}

# Directory setup
setup_directories() {
    log_info "Setting up ~/.claude directory structure..."

    mkdir -p "$CLAUDE_AGENTS_DIR"
    mkdir -p "$CLAUDE_COMMANDS_DIR"
    mkdir -p "$CLAUDE_SCRIPTS_DIR"
    mkdir -p "$CLAUDE_SKILLS_DIR"

    # Detect optional systems
    [ -d "$PLUGIN_SRC_DIR/$ORCHESTRATION_DIR" ] && log_info "Orchestration system detected"
    [ -d "$PLUGIN_SRC_DIR/$AUTOMATION_DIR" ] && log_info "Automation system detected"
    [ -d "$PLUGIN_SRC_DIR/$CLAUDE_BOT_DIR" ] && log_info "Claude Bot system detected"
    [ -d "$PLUGIN_SRC_DIR/$INFRASTRUCTURE_DIR" ] && log_info "Infrastructure scripts detected"

    log_success "Directory structure ready"
}

# Copy agents to ~/.claude/agents/
install_agents() {
    log_info "Installing agents to $CLAUDE_AGENTS_DIR ..."

    local agent_count=0

    if [ -d "$SRC_AGENTS_DIR" ]; then
        for file in "$SRC_AGENTS_DIR"/*.md; do
            if [ -f "$file" ]; then
                cp -f "$file" "$CLAUDE_AGENTS_DIR/"
                log_info "  Installed agent: $(basename "$file")"
                agent_count=$((agent_count + 1))
            fi
        done
    else
        log_warning "No agents source directory found at $SRC_AGENTS_DIR"
    fi

    log_success "Installed $agent_count agents"
}

# Copy commands to ~/.claude/commands/
install_commands() {
    log_info "Installing commands to $CLAUDE_COMMANDS_DIR ..."

    local command_count=0

    if [ -d "$SRC_COMMANDS_DIR" ]; then
        # Copy top-level .md and .py files
        for file in "$SRC_COMMANDS_DIR"/*.md "$SRC_COMMANDS_DIR"/*.py; do
            if [ -f "$file" ]; then
                cp -f "$file" "$CLAUDE_COMMANDS_DIR/"
                command_count=$((command_count + 1))
            fi
        done
        # Copy subdirectories (e.g. _copilot_modules, _shared, cerebras)
        for subdir in "$SRC_COMMANDS_DIR"/*/; do
            if [ -d "$subdir" ]; then
                local subdir_name
                subdir_name="$(basename "$subdir")"
                mkdir -p "$CLAUDE_COMMANDS_DIR/$subdir_name"
                cp -rf "$subdir"* "$CLAUDE_COMMANDS_DIR/$subdir_name/" 2>/dev/null || true
                log_info "  Installed command subdir: $subdir_name"
            fi
        done
    else
        log_warning "No commands source directory found at $SRC_COMMANDS_DIR"
    fi

    log_success "Installed $command_count command files"
}

# Copy scripts to ~/.claude/scripts/
install_scripts() {
    log_info "Installing scripts to $CLAUDE_SCRIPTS_DIR ..."

    local script_count=0

    if [ -d "$SRC_SCRIPTS_DIR" ]; then
        for file in "$SRC_SCRIPTS_DIR"/*; do
            if [ -f "$file" ]; then
                cp -f "$file" "$CLAUDE_SCRIPTS_DIR/"
                chmod +x "$CLAUDE_SCRIPTS_DIR/$(basename "$file")" 2>/dev/null || true
                log_info "  Installed script: $(basename "$file")"
                script_count=$((script_count + 1))
            fi
        done
    else
        log_warning "No scripts source directory found at $SRC_SCRIPTS_DIR"
    fi

    log_success "Installed $script_count scripts"
}

# Copy skills to ~/.claude/skills/
install_skills() {
    log_info "Installing skills to $CLAUDE_SKILLS_DIR ..."

    local skill_count=0

    if [ -d "$SRC_SKILLS_DIR" ]; then
        for file in "$SRC_SKILLS_DIR"/*.md; do
            if [ -f "$file" ]; then
                cp -f "$file" "$CLAUDE_SKILLS_DIR/"
                skill_count=$((skill_count + 1))
            fi
        done
    else
        log_warning "No skills source directory found at $SRC_SKILLS_DIR"
    fi

    log_success "Installed $skill_count skills"
}

# Infrastructure installation (root-level scripts, not copied to ~/.claude)
install_infrastructure() {
    log_info "Making infrastructure scripts executable..."

    local infra_count=0

    for script in claude_start.sh claude_mcp.sh start-claude-bot.sh integrate.sh resolve_conflicts.sh sync_branch.sh setup-github-runner.sh test_server_manager.sh; do
        if [ -f "$PLUGIN_SRC_DIR/$script" ]; then
            chmod +x "$PLUGIN_SRC_DIR/$script" 2>/dev/null || true
            infra_count=$((infra_count + 1))
        fi
    done

    if [ -d "$PLUGIN_SRC_DIR/$INFRASTRUCTURE_DIR" ]; then
        for script in "$PLUGIN_SRC_DIR/$INFRASTRUCTURE_DIR"/*.sh; do
            if [ -f "$script" ]; then
                chmod +x "$script" 2>/dev/null || true
                infra_count=$((infra_count + 1))
            fi
        done
    fi

    log_success "Made $infra_count infrastructure scripts executable"
}

# Optional system installation
install_optional_systems() {
    log_info "Installing optional systems..."

    if [ -d "$PLUGIN_SRC_DIR/$ORCHESTRATION_DIR" ]; then
        log_info "  Orchestration system (WIP prototype)"
        log_warning "    Requires: Redis, tmux, Python venv"
        log_info "    See orchestration/README.md for setup instructions"
    fi

    if [ -d "$PLUGIN_SRC_DIR/$AUTOMATION_DIR" ]; then
        log_info "  Automation system (production ready)"
        log_warning "    Requires: cron access, email configuration"
        log_info "    See automation/README.md for setup instructions"
    fi

    if [ -d "$PLUGIN_SRC_DIR/$CLAUDE_BOT_DIR" ]; then
        log_info "  Claude Bot system (production ready)"
        log_warning "    Requires: GitHub repository, self-hosted runner"
        log_info "    See claude-bot-commands/README.md for setup instructions"
    fi
}

# Environment validation
validate_installation() {
    log_info "Validating installation..."

    local agents_found=0
    local commands_found=0
    local scripts_found=0

    [ -d "$CLAUDE_AGENTS_DIR" ] && agents_found=$(find "$CLAUDE_AGENTS_DIR" -maxdepth 1 -name "*.md" | wc -l)
    [ -d "$CLAUDE_COMMANDS_DIR" ] && commands_found=$(find "$CLAUDE_COMMANDS_DIR" -maxdepth 1 \( -name "*.md" -o -name "*.py" \) | wc -l)
    [ -d "$CLAUDE_SCRIPTS_DIR" ] && scripts_found=$(find "$CLAUDE_SCRIPTS_DIR" -maxdepth 1 -type f | wc -l)

    log_info "Installation summary:"
    log_info "  Agents:   $agents_found  → $CLAUDE_AGENTS_DIR"
    log_info "  Commands: $commands_found  → $CLAUDE_COMMANDS_DIR"
    log_info "  Scripts:  $scripts_found  → $CLAUDE_SCRIPTS_DIR"

    if [ "$agents_found" -gt 0 ] && [ "$commands_found" -gt 0 ] && [ "$scripts_found" -gt 0 ]; then
        log_success "Claude Commands installation completed successfully!"
    else
        log_warning "Installation completed but some components may be missing"
    fi
}

# Usage information
show_usage() {
    log_info "Next steps:"
    echo
    echo "1. Read CLAUDE.md for complete usage instructions"
    echo "2. Try basic commands: /help, /list, /execute"
    echo "3. Configure systems as needed:"
    echo "   - Orchestration: See orchestration/README.md"
    echo "   - Automation: See automation/README.md"
    echo "   - Claude Bot: See claude-bot-commands/README.md"
    echo "4. Start with cognitive commands: /think, /arch, /debug"
    echo
    log_info "For support, see: https://github.com/jleechanorg/claude-commands"
}

# Main installation flow
main() {
    echo
    log_info "Claude Commands Installation Script"
    log_info "Installing complete Claude Code command system..."
    log_info "Source: $PLUGIN_SRC_DIR"
    log_info "Target: $CLAUDE_HOME"
    echo

    check_prerequisites
    setup_directories
    install_agents
    install_commands
    install_scripts
    install_skills
    install_infrastructure
    install_optional_systems
    validate_installation

    echo
    show_usage
    echo
    log_success "Installation complete!"
}

# Error handling
trap 'log_error "Installation failed at line $LINENO. Check the output above for details."; exit 1' ERR

# Run main installation if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
