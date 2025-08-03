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

# Configuration
CLAUDE_COMMANDS_DIR=".claude/commands"
ORCHESTRATION_DIR="orchestration"
AUTOMATION_DIR="automation"
CLAUDE_BOT_DIR="claude-bot-commands"
SCRIPTS_DIR="claude_command_scripts"
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
    log_info "Setting up directory structure..."
    
    # Create main directories
    mkdir -p "$CLAUDE_COMMANDS_DIR"
    mkdir -p "$SCRIPTS_DIR"
    
    # Create optional directories if content exists
    [ -d "$ORCHESTRATION_DIR" ] && log_info "Orchestration system detected"
    [ -d "$AUTOMATION_DIR" ] && log_info "Automation system detected"
    [ -d "$CLAUDE_BOT_DIR" ] && log_info "Claude Bot system detected"
    [ -d "$INFRASTRUCTURE_DIR" ] && log_info "Infrastructure scripts detected"
    
    log_success "Directory structure created"
}

# Command installation
install_commands() {
    log_info "Installing command definitions..."
    
    local command_count=0
    
    if [ -d "$CLAUDE_COMMANDS_DIR" ]; then
        for file in "$CLAUDE_COMMANDS_DIR"/*.md "$CLAUDE_COMMANDS_DIR"/*.py; do
            if [ -f "$file" ]; then
                log_info "  Installing: $(basename "$file")"
                ((command_count++))
            fi
        done
    fi
    
    log_success "Installed $command_count command definitions"
}

# Script installation
install_scripts() {
    log_info "Installing command scripts..."
    
    local script_count=0
    
    if [ -d "$SCRIPTS_DIR" ]; then
        for script in "$SCRIPTS_DIR"/*.sh "$SCRIPTS_DIR"/*.py; do
            if [ -f "$script" ]; then
                chmod +x "$script" 2>/dev/null || true
                log_info "  Installing: $(basename "$script")"
                ((script_count++))
            fi
        done
    fi
    
    log_success "Installed $script_count command scripts"
}

# Infrastructure installation
install_infrastructure() {
    log_info "Installing infrastructure scripts..."
    
    local infra_count=0
    
    # Install root-level infrastructure scripts
    for script in claude_start.sh claude_mcp.sh start-claude-bot.sh integrate.sh resolve_conflicts.sh sync_branch.sh setup-github-runner.sh test_server_manager.sh; do
        if [ -f "$script" ]; then
            chmod +x "$script" 2>/dev/null || true
            log_info "  Installing: $script"
            ((infra_count++))
        fi
    done
    
    # Install infrastructure-scripts directory if it exists
    if [ -d "$INFRASTRUCTURE_DIR" ]; then
        for script in "$INFRASTRUCTURE_DIR"/*.sh; do
            if [ -f "$script" ]; then
                chmod +x "$script" 2>/dev/null || true
                log_info "  Installing: $(basename "$script")"
                ((infra_count++))
            fi
        done
    fi
    
    log_success "Installed $infra_count infrastructure scripts"
}

# Optional system installation
install_optional_systems() {
    log_info "Installing optional systems..."
    
    # Orchestration system
    if [ -d "$ORCHESTRATION_DIR" ]; then
        log_info "  Installing orchestration system (WIP prototype)"
        log_warning "    Orchestration requires: Redis, tmux, Python venv"
        log_info "    See orchestration/README.md for setup instructions"
    fi
    
    # Automation system
    if [ -d "$AUTOMATION_DIR" ]; then
        log_info "  Installing automation system (production ready)"
        log_warning "    Automation requires: cron access, email configuration"
        log_info "    See automation/README.md for setup instructions"
    fi
    
    # Claude Bot system
    if [ -d "$CLAUDE_BOT_DIR" ]; then
        log_info "  Installing Claude Bot system (production ready)"
        log_warning "    Claude Bot requires: GitHub repository, self-hosted runner"
        log_info "    See claude-bot-commands/README.md for setup instructions"
    fi
}

# Environment validation
validate_installation() {
    log_info "Validating installation..."
    
    # Check command availability
    local commands_found=0
    if [ -d "$CLAUDE_COMMANDS_DIR" ]; then
        commands_found=$(find "$CLAUDE_COMMANDS_DIR" -name "*.md" -o -name "*.py" | wc -l)
    fi
    
    # Check scripts availability
    local scripts_found=0
    if [ -d "$SCRIPTS_DIR" ]; then
        scripts_found=$(find "$SCRIPTS_DIR" -name "*.sh" -o -name "*.py" | wc -l)
    fi
    
    log_info "Installation summary:"
    log_info "  Commands: $commands_found"
    log_info "  Scripts: $scripts_found"
    
    if [ "$commands_found" -gt 0 ] && [ "$scripts_found" -gt 0 ]; then
        log_success "Claude Commands installation completed successfully!"
    else
        log_warning "Installation completed but some components may be missing"
    fi
}

# Usage information
show_usage() {
    log_info "Next steps:"
    echo
    echo "1. 📚 Read CLAUDE.md for complete usage instructions"
    echo "2. 🚀 Try basic commands: /help, /list, /execute"
    echo "3. 🔧 Configure systems as needed:"
    echo "   - Orchestration: See orchestration/README.md"
    echo "   - Automation: See automation/README.md"
    echo "   - Claude Bot: See claude-bot-commands/README.md"
    echo "4. 🎯 Start with cognitive commands: /think, /arch, /debug"
    echo
    log_info "For support, see: https://github.com/jleechanorg/claude-commands"
}

# Main installation flow
main() {
    echo
    log_info "🚀 Claude Commands Installation Script"
    log_info "Installing complete Claude Code command system..."
    echo
    
    check_prerequisites
    setup_directories
    install_commands
    install_scripts
    install_infrastructure
    install_optional_systems
    validate_installation
    
    echo
    show_usage
    echo
    log_success "Installation complete! 🎉"
}

# Error handling
trap 'log_error "Installation failed at line $LINENO. Check the output above for details."; exit 1' ERR

# Run main installation if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi