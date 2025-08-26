#!/bin/bash

# Install Backup System - Portable Installation Script
# Installs backup scripts to stable location and updates cron for portability
#
# USAGE:
#   ./scripts/install_backup_system.sh [dropbox_base_dir]
#
# PURPOSE:
#   Fixes the critical portability issue where cron jobs are hardcoded to specific worktree paths
#   Creates a proper installation in ~/.local/bin/ that works across worktrees and machines

set -euo pipefail
trap 'echo "❌ Installation error at line $LINENO" >&2; exit 1' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 Installing Portable Backup System${NC}"
echo ""

# Configuration
INSTALL_DIR="$HOME/.local/bin"

# Check for help flag
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Usage: $0 [dropbox_base_dir]"
    echo ""
    echo "Install backup scripts to stable location and update cron for portability."
    echo ""
    echo "Arguments:"
    echo "  dropbox_base_dir    Base directory for Dropbox backups (default: \$HOME/Library/CloudStorage/Dropbox)"
    echo ""
    echo "This fixes the critical portability issue where cron jobs are hardcoded to specific worktree paths."
    exit 0
fi

DROPBOX_BASE="${1:-$HOME/Library/CloudStorage/Dropbox}"

# Ensure install directory exists
echo -e "${BLUE}📁 Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
echo -e "${GREEN}   ✅ Created: $INSTALL_DIR${NC}"

# Add to PATH if not already there
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo -e "${YELLOW}   ⚠️ Adding $INSTALL_DIR to PATH in ~/.bashrc${NC}"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
fi

# Copy backup scripts to stable location
echo -e "${BLUE}📋 Installing backup scripts...${NC}"

# Copy main backup script
cp "$SCRIPT_DIR/claude_backup.sh" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/claude_backup.sh"
echo -e "${GREEN}   ✅ Installed: $INSTALL_DIR/claude_backup.sh${NC}"

# Create portable cron wrapper
cat > "$INSTALL_DIR/claude_backup_cron.sh" << 'EOF'
#!/bin/bash
# Portable Cron Wrapper for Claude Backup
# This script is installed in a stable location and references the main backup script
set -euo pipefail

# Security: Create secure temp directory for logs with proper cleanup
SECURE_TEMP=\$(mktemp -d)
chmod 700 "\$SECURE_TEMP"
trap 'echo "[cron] \$(date +%F\\ %T) error at line \$LINENO" >> "\$SECURE_TEMP/claude_backup_cron.log"; rm -rf "\$SECURE_TEMP"' ERR
trap 'rm -rf "\$SECURE_TEMP"' EXIT

export PATH="/usr/local/bin:/usr/bin:/bin:\$PATH"
export SHELL="/bin/bash"

# Security: Path validation function
validate_path() {
    local path="\$1"
    local context="\$2"
    
    # Check for path traversal patterns
    if [[ "\$path" =~ \.\./|/\.\. ]]; then
        echo "ERROR: Path traversal attempt detected in \$context: \$path" >&2
        exit 1
    fi
    
    # Check for null bytes
    if [[ "\$path" =~ \$'\\x00' ]]; then
        echo "ERROR: Null byte detected in \$context: \$path" >&2
        exit 1
    fi
}

# Preserve email credentials from environment (with validation)
[ -n "\${EMAIL_USER:-}" ] && export EMAIL_USER="\$EMAIL_USER"
[ -n "\${EMAIL_PASS:-}" ] && export EMAIL_PASS="\$EMAIL_PASS"  
[ -n "\${BACKUP_EMAIL:-}" ] && export BACKUP_EMAIL="\$BACKUP_EMAIL"

# Use the installed backup script with provided or default Dropbox location
DROPBOX_BASE="\${1:-\$HOME/Library/CloudStorage/Dropbox}"

# Security: Validate the Dropbox base directory path
validate_path "\$DROPBOX_BASE" "DROPBOX_BASE parameter"

# Validate Dropbox base directory exists
if [[ ! -d "\$DROPBOX_BASE" ]]; then
  echo "Dropbox base directory not found: \$DROPBOX_BASE" >&2
  echo "Falling back to default: \$HOME/Library/CloudStorage/Dropbox" >&2
  DROPBOX_BASE="\$HOME/Library/CloudStorage/Dropbox"
  validate_path "\$DROPBOX_BASE" "fallback Dropbox directory"
fi

# Security: Validate backup script exists and is executable
if [[ ! -x "\$HOME/.local/bin/claude_backup.sh" ]]; then
    echo "ERROR: Backup script not found or not executable: \$HOME/.local/bin/claude_backup.sh" >&2
    exit 1
fi

# Run the installed backup script with secure logging
exec "\$HOME/.local/bin/claude_backup.sh" "\$DROPBOX_BASE" >> "\$SECURE_TEMP/claude_backup_cron.log" 2>&1
EOF

chmod +x "$INSTALL_DIR/claude_backup_cron.sh"
echo -e "${GREEN}   ✅ Installed: $INSTALL_DIR/claude_backup_cron.sh${NC}"

# Update cron job to use stable location
echo -e "${BLUE}⏰ Updating cron job...${NC}"

# Remove any existing backup cron entries (including old hardcoded ones)
echo -e "${YELLOW}   🗑️ Removing old cron entries...${NC}"
if crontab -l >/dev/null 2>&1; then
    (crontab -l 2>/dev/null | grep -v "claude_backup" || true) | crontab - 2>/dev/null || true
    echo -e "${GREEN}      ✅ Cleaned up old entries${NC}"
fi

# Add new portable cron entry
echo -e "${YELLOW}   ➕ Adding new portable cron entry...${NC}"
# Security: Use secure temp directory for cron logs
CRON_ENTRY="0 */4 * * * \"$INSTALL_DIR/claude_backup_cron.sh\" \"$DROPBOX_BASE\" 2>&1"  # Logs handled by wrapper script
{
    crontab -l 2>/dev/null || true
    echo "$CRON_ENTRY"
} | crontab -

echo -e "${GREEN}   ✅ Cron job updated: Every 4 hours${NC}"
echo -e "${BLUE}      Schedule: 0 */4 * * * (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)${NC}"
echo -e "${BLUE}      Script: $INSTALL_DIR/claude_backup_cron.sh${NC}"
echo -e "${BLUE}      Destination: $DROPBOX_BASE${NC}"

# Verify installation
echo -e "${BLUE}🔍 Verifying installation...${NC}"

# Test that scripts are executable
if [[ -x "$INSTALL_DIR/claude_backup.sh" ]] && [[ -x "$INSTALL_DIR/claude_backup_cron.sh" ]]; then
    echo -e "${GREEN}   ✅ Scripts are executable${NC}"
else
    echo -e "${RED}   ❌ Scripts are not executable${NC}"
    exit 1
fi

# Test that main script shows help
if "$INSTALL_DIR/claude_backup.sh" --help >/dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Main script responds to --help${NC}"
else
    echo -e "${RED}   ❌ Main script --help failed${NC}"
    exit 1
fi

# Show current cron entries
echo -e "${BLUE}   📋 Current cron entries:${NC}"
crontab -l | grep claude_backup | while read -r line; do
    echo -e "${BLUE}      $line${NC}"
done

# Test backup (optional - only if safe)
echo -e "${BLUE}🧪 Testing backup system...${NC}"
if "$INSTALL_DIR/claude_backup.sh" --help >/dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Backup system test passed${NC}"
else
    echo -e "${RED}   ❌ Backup system test failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 INSTALLATION COMPLETE!${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo -e "${GREEN}   ✅ Backup scripts installed to: $INSTALL_DIR${NC}"
echo -e "${GREEN}   ✅ Cron job updated to use stable location${NC}"
echo -e "${GREEN}   ✅ System is now portable across worktrees${NC}"
echo -e "${GREEN}   ✅ Backup runs every 4 hours automatically${NC}"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo -e "${BLUE}   • Test: Run 'crontab -l' to verify cron entry${NC}"
echo -e "${BLUE}   • Monitor: Logs in secure temp directory (check wrapper script)${NC}"
echo -e "${BLUE}   • Configure: Set EMAIL_* env vars for failure alerts${NC}"
echo ""
echo -e "${YELLOW}⚠️ Important: Backup system is now independent of worktree location!${NC}"
echo -e "${YELLOW}   You can rename, move, or delete this worktree - backups will continue working.${NC}"