#!/usr/bin/env bash
# Memory MCP Setup Script - Portable installation for any user
# Creates necessary directories, configures backup system, and sets up cron job

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_info() {
    print_color "$BLUE" "ℹ️  $1"
}

print_success() {
    print_color "$GREEN" "✅ $1"
}

print_warning() {
    print_color "$YELLOW" "⚠️  $1"
}

print_error() {
    print_color "$RED" "❌ $1"
}

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
USER_HOME="$HOME"
MEMORY_DIR="$SCRIPT_DIR"
CONFIG_FILE="$MEMORY_DIR/config.json"
BACKUP_SCRIPT="$MEMORY_DIR/backup_memory.sh"
DEPLOYED_SCRIPT="$USER_HOME/backup_memory.sh"

print_info "Memory MCP Setup Script"
print_info "Repository: $REPO_ROOT"
print_info "Memory directory: $MEMORY_DIR"
print_info "User home: $USER_HOME"

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install git first."
        exit 1
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --is-inside-work-tree &> /dev/null; then
        print_error "Not in a git repository. Please run from within the project."
        exit 1
    fi
    
    # Check if gh CLI is installed (optional)
    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI (gh) not found. PR detection will be limited."
    fi
    
    # Check if cron is available
    if ! command -v crontab &> /dev/null; then
        print_warning "Cron not available. Automatic backups will not be set up."
    fi
    
    print_success "Prerequisites check complete"
}

# Create configuration file
create_config() {
    print_info "Creating configuration file..."
    
    # Detect if this is a fork
    local origin_url
    origin_url=$(git remote get-url origin 2>/dev/null || echo "")
    local is_fork="false"
    
    if [[ "$origin_url" != *"jleechan2015/worldarchitect.ai"* ]]; then
        is_fork="true"
        print_warning "Detected fork repository. Backup will be local-only by default."
    fi
    
    # Create configuration
    cat > "$CONFIG_FILE" << EOF
{
    "version": "1.0.0",
    "user_home": "$USER_HOME",
    "repo_root": "$REPO_ROOT",
    "memory_dir": "$MEMORY_DIR",
    "memory_file": "$USER_HOME/.cache/mcp-memory/memory.json",
    "backup_worktree": "$USER_HOME/worldarchitect-backup",
    "is_fork": $is_fork,
    "backup_enabled": true,
    "backup_to_remote": $([ "$is_fork" = "false" ] && echo "true" || echo "false"),
    "backup_interval_hours": 1,
    "max_backup_retries": 3,
    "log_file": "$USER_HOME/.cache/mcp-memory/backup.log",
    "origin_url": "$origin_url",
    "setup_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
    
    print_success "Configuration created: $CONFIG_FILE"
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    
    # Create MCP cache directory
    mkdir -p "$USER_HOME/.cache/mcp-memory"
    
    # Create backup worktree if it doesn't exist
    local backup_dir="$USER_HOME/worldarchitect-backup"
    if [ ! -d "$backup_dir" ]; then
        print_info "Creating backup worktree: $backup_dir"
        git worktree add "$backup_dir" main || {
            print_error "Failed to create backup worktree"
            exit 1
        }
    else
        print_success "Backup worktree already exists: $backup_dir"
    fi
    
    print_success "Directories created"
}

# Deploy backup script
deploy_backup_script() {
    print_info "Deploying backup script..."
    
    if [ ! -f "$BACKUP_SCRIPT" ]; then
        print_error "Backup script not found: $BACKUP_SCRIPT"
        exit 1
    fi
    
    # Copy script to user home
    cp "$BACKUP_SCRIPT" "$DEPLOYED_SCRIPT"
    chmod +x "$DEPLOYED_SCRIPT"
    
    # Update script to use configuration
    sed -i.bak "s|REPO_DIR=.*|REPO_DIR=\"\$USER_HOME/worldarchitect-backup\"|g" "$DEPLOYED_SCRIPT"
    sed -i.bak "s|MEMORY_FILE=.*|MEMORY_FILE=\"\$USER_HOME/.cache/mcp-memory/memory.json\"|g" "$DEPLOYED_SCRIPT"
    
    print_success "Backup script deployed: $DEPLOYED_SCRIPT"
}

# Set up cron job
setup_cron() {
    print_info "Setting up cron job..."
    
    if ! command -v crontab &> /dev/null; then
        print_warning "Cron not available. Skipping automatic backup setup."
        return
    fi
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "backup_memory.sh"; then
        print_warning "Cron job already exists. Skipping..."
        return
    fi
    
    # Add cron job
    (crontab -l 2>/dev/null; echo "0 * * * * $DEPLOYED_SCRIPT >> $USER_HOME/.cache/mcp-memory/backup.log 2>&1") | crontab -
    
    print_success "Cron job set up for hourly backups"
}

# Test backup functionality
test_backup() {
    print_info "Testing backup functionality..."
    
    # Create a test memory file if it doesn't exist
    if [ ! -f "$USER_HOME/.cache/mcp-memory/memory.json" ]; then
        print_info "Creating test memory file..."
        echo '{"type":"entity","name":"setup_test","entityType":"test","observations":["Testing Memory MCP setup"]}' > "$USER_HOME/.cache/mcp-memory/memory.json"
    fi
    
    # Run backup script
    if "$DEPLOYED_SCRIPT"; then
        print_success "Backup test successful"
    else
        print_error "Backup test failed"
        exit 1
    fi
}

# Print completion message
print_completion() {
    print_success "Memory MCP setup complete!"
    echo
    print_info "Configuration:"
    echo "  - Config file: $CONFIG_FILE"
    echo "  - Backup script: $DEPLOYED_SCRIPT"
    echo "  - Memory file: $USER_HOME/.cache/mcp-memory/memory.json"
    echo "  - Backup worktree: $USER_HOME/worldarchitect-backup"
    echo "  - Log file: $USER_HOME/.cache/mcp-memory/backup.log"
    echo
    print_info "Next steps:"
    echo "  1. Test the backup: $DEPLOYED_SCRIPT"
    echo "  2. Check logs: tail -f $USER_HOME/.cache/mcp-memory/backup.log"
    echo "  3. Verify cron job: crontab -l"
    echo "  4. Use enhanced header: python3 $MEMORY_DIR/enhanced_header_command.py"
}

# Main setup process
main() {
    print_info "Starting Memory MCP setup..."
    
    check_prerequisites
    create_config
    create_directories
    deploy_backup_script
    setup_cron
    test_backup
    print_completion
}

# Run main function
main "$@"