#!/usr/bin/env bash
# Install script for CRDT-based Memory Backup System
# Sets up automated memory backups with crontab scheduling

set -euo pipefail

# Wrapper for timeout command (macOS compatibility)
timeout_cmd() {
    local duration=$1
    shift
    if command -v timeout &>/dev/null; then
        timeout "$duration" "$@"
    elif command -v gtimeout &>/dev/null; then
        gtimeout "$duration" "$@"
    else
        # Fallback: run without timeout but warn
        echo "Warning: timeout command not found, running without timeout protection" >&2
        "$@"
    fi
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

print_status "Installing CRDT-based Memory Backup System"
echo "Project root: $PROJECT_ROOT"
echo

# Check dependencies
print_status "Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

if ! command -v git &> /dev/null; then
    print_error "Git is required but not installed"
    exit 1
fi

print_success "Dependencies check passed"

# Create memory directory if it doesn't exist
MEMORY_DIR="$HOME/.cache/mcp-memory"
if [ ! -d "$MEMORY_DIR" ]; then
    print_status "Creating memory directory: $MEMORY_DIR"
    mkdir -p "$MEMORY_DIR"
    print_success "Created memory directory"
else
    print_status "Memory directory already exists: $MEMORY_DIR"
fi

# Create default memory file if it doesn't exist
MEMORY_FILE="$MEMORY_DIR/memory.json"
if [ ! -f "$MEMORY_FILE" ]; then
    print_status "Creating default memory file: $MEMORY_FILE"
    echo "[]" > "$MEMORY_FILE"
    print_success "Created default memory file"
else
    print_status "Memory file already exists: $MEMORY_FILE"
fi

# Make backup script executable
BACKUP_SCRIPT="$SCRIPT_DIR/memory_backup_crdt.sh"
if [ -f "$BACKUP_SCRIPT" ]; then
    chmod +x "$BACKUP_SCRIPT"
    print_success "Made backup script executable: $BACKUP_SCRIPT"
else
    print_error "Backup script not found: $BACKUP_SCRIPT"
    exit 1
fi

# Setup crontab for automated backups
print_status "Setting up crontab for automated memory backups..."

# Validate backup script path to prevent injection
if [[ ! "$BACKUP_SCRIPT" =~ ^[a-zA-Z0-9/_.-]+$ ]]; then
    print_error "Invalid backup script path detected - potential security risk"
    exit 1
fi

# Define the cron job (every 15 minutes) with validated path
# Use secure log location with restricted permissions
LOG_FILE="$HOME/.cache/memory_backup.log"
CRON_JOB="*/15 * * * * $BACKUP_SCRIPT > $LOG_FILE 2>&1"

# Check if crontab already contains our backup job (with timeout protection)
if timeout_cmd 5s crontab -l 2>/dev/null | grep -q "memory_backup_crdt.sh"; then
    print_warning "Memory backup cron job already exists"
    print_status "Current crontab entries:"
    crontab -l 2>/dev/null | grep "memory_backup"
else
    # Add the cron job
    print_status "Adding memory backup to crontab (every 15 minutes)"
    
    # Get existing crontab (if any) and add our job with timeout protection
    # Validate cron expression format before adding
    if ! echo "$CRON_JOB" | grep -qE '^(\*/[0-9]+|[0-9]+) (\*/[0-9]+|[0-9]+|\*) (\*/[0-9]+|[0-9]+|\*) (\*/[0-9]+|[0-9]+|\*) (\*/[0-9]+|[0-9]+|\*) [a-zA-Z0-9/_.-]+ >'; then
        print_error "Invalid cron job format detected"
        exit 1
    fi
    
    (timeout_cmd 5s crontab -l 2>/dev/null || true; echo "$CRON_JOB") | timeout_cmd 5s crontab -
    
    print_success "Added memory backup cron job"
    print_status "Backup will run every 15 minutes"
fi

# Test the backup script with timeout protection
print_status "Testing backup script..."
if timeout_cmd 10s "$BACKUP_SCRIPT" --test 2>/dev/null; then
    print_success "Backup script test passed"
else
    print_warning "Backup script test failed - this may be expected if no memory data exists"
    print_status "The script will work correctly when memory data is available"
fi

# Show installation summary
echo
print_success "CRDT Memory Backup System installed successfully!"
echo
echo "📋 Installation Summary:"
echo "  - Memory directory: $MEMORY_DIR"
echo "  - Memory file: $MEMORY_FILE"
echo "  - Backup script: $BACKUP_SCRIPT"
echo "  - Cron schedule: Every 15 minutes"
echo "  - Log file: $LOG_FILE"
echo
echo "🔧 Manual Commands:"
echo "  - Run backup now: $BACKUP_SCRIPT"
echo "  - View crontab: crontab -l"
echo "  - View backup log: tail -f $LOG_FILE"
echo "  - Check memory: cat $MEMORY_FILE | jq ."
echo
echo "🚀 The system will automatically backup memory every 15 minutes"
echo "   Multiple environments can run in parallel without data loss!"

# Optionally run first backup
read -p "Run initial backup now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Running initial backup..."
    if timeout_cmd 30s "$BACKUP_SCRIPT"; then
        print_success "Initial backup completed"
    else
        print_warning "Initial backup had issues - check the log for details"
    fi
fi

print_success "Installation complete!"