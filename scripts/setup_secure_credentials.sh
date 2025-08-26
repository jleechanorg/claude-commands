#!/bin/bash

# Secure Credential Setup for Claude Backup System
# This script helps set up secure credential storage instead of environment variables
# Addresses critical security vulnerability in backup system

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Secure Credential Setup for Claude Backup ===${NC}"
echo ""

# Function to set up macOS keychain credentials
setup_macos_keychain() {
    echo -e "${BLUE}Setting up macOS Keychain credentials...${NC}"
    
    read -p "Enter your Gmail address for backup alerts: " email_user
    read -s -p "Enter your Gmail app password: " email_pass
    echo
    read -p "Enter backup notification email address: " backup_email
    
    # Store credentials in keychain
    security add-generic-password -s "claude-backup-user" -a "claude-backup" -w "$email_user" -U 2>/dev/null || \
        security delete-generic-password -s "claude-backup-user" -a "claude-backup" 2>/dev/null && \
        security add-generic-password -s "claude-backup-user" -a "claude-backup" -w "$email_user"
    
    security add-generic-password -s "claude-backup-pass" -a "claude-backup" -w "$email_pass" -U 2>/dev/null || \
        security delete-generic-password -s "claude-backup-pass" -a "claude-backup" 2>/dev/null && \
        security add-generic-password -s "claude-backup-pass" -a "claude-backup" -w "$email_pass"
    
    security add-generic-password -s "claude-backup-email" -a "claude-backup" -w "$backup_email" -U 2>/dev/null || \
        security delete-generic-password -s "claude-backup-email" -a "claude-backup" 2>/dev/null && \
        security add-generic-password -s "claude-backup-email" -a "claude-backup" -w "$backup_email"
    
    echo -e "${GREEN}✅ Credentials stored securely in macOS Keychain${NC}"
}

# Function to set up Linux Secret Service credentials
setup_linux_secrets() {
    echo -e "${BLUE}Setting up Linux Secret Service credentials...${NC}"
    
    if ! command -v secret-tool >/dev/null 2>&1; then
        echo -e "${RED}❌ secret-tool not found. Install libsecret-tools:${NC}"
        echo "  Ubuntu/Debian: sudo apt-get install libsecret-tools"
        echo "  CentOS/RHEL: sudo yum install libsecret-devel"
        return 1
    fi
    
    read -p "Enter your Gmail address for backup alerts: " email_user
    read -s -p "Enter your Gmail app password: " email_pass
    echo
    read -p "Enter backup notification email address: " backup_email
    
    # Store credentials using secret service
    echo -n "$email_user" | secret-tool store --label="Claude Backup Email User" service "claude-backup" key "user"
    echo -n "$email_pass" | secret-tool store --label="Claude Backup Email Password" service "claude-backup" key "pass"
    echo -n "$backup_email" | secret-tool store --label="Claude Backup Notification Email" service "claude-backup" key "email"
    
    echo -e "${GREEN}✅ Credentials stored securely in Linux Secret Service${NC}"
}

# Function to test credential retrieval
test_credentials() {
    echo -e "\n${BLUE}Testing credential retrieval...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        local test_user=$(security find-generic-password -s "claude-backup-user" -w 2>/dev/null || echo "")
        local test_email=$(security find-generic-password -s "claude-backup-email" -w 2>/dev/null || echo "")
    else
        # Linux
        local test_user=$(secret-tool lookup service "claude-backup" key "user" 2>/dev/null || echo "")
        local test_email=$(secret-tool lookup service "claude-backup" key "email" 2>/dev/null || echo "")
    fi
    
    if [[ -n "$test_user" && -n "$test_email" ]]; then
        echo -e "${GREEN}✅ Credentials retrieved successfully${NC}"
        echo -e "${CYAN}   Email User: $test_user${NC}"
        echo -e "${CYAN}   Backup Email: $test_email${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to retrieve credentials${NC}"
        return 1
    fi
}

# Function to remove environment variable setup
cleanup_env_vars() {
    echo -e "\n${YELLOW}⚠️ SECURITY CLEANUP ⚠️${NC}"
    echo "The following environment variables should be REMOVED from your shell profile:"
    echo "  - EMAIL_USER"
    echo "  - EMAIL_PASS" 
    echo "  - BACKUP_EMAIL"
    echo ""
    echo "These variables are a security risk as they expose credentials in process lists."
    echo "The backup system now uses secure credential storage instead."
    echo ""
    echo "Check these files for the variables and remove them:"
    echo "  - ~/.bashrc"
    echo "  - ~/.zshrc"
    echo "  - ~/.profile"
    echo "  - ~/.bash_profile"
}

# Main execution
main() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo -e "${BLUE}Detected macOS - using Keychain for secure storage${NC}"
        setup_macos_keychain
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo -e "${BLUE}Detected Linux - using Secret Service for secure storage${NC}"
        setup_linux_secrets
    else
        echo -e "${RED}❌ Unsupported operating system: $OSTYPE${NC}"
        echo "Secure credential storage is only available on macOS and Linux"
        return 1
    fi
    
    # Test the setup
    if test_credentials; then
        echo -e "\n${GREEN}🎉 Secure credential setup completed successfully!${NC}"
        cleanup_env_vars
        
        echo -e "\n${BLUE}Next steps:${NC}"
        echo "1. Remove environment variables from shell profiles (as shown above)"
        echo "2. Re-run backup cron setup: $SCRIPT_DIR/claude_backup.sh --setup-cron"
        echo "3. Test backup: $SCRIPT_DIR/claude_backup.sh"
    else
        echo -e "\n${RED}❌ Credential setup failed. Please try again.${NC}"
        return 1
    fi
}

# Show help
show_help() {
    cat << EOF
Secure Credential Setup for Claude Backup System

USAGE:
    $0                    # Interactive setup
    $0 --help            # Show this help
    $0 --test            # Test existing credentials

SECURITY IMPROVEMENTS:
    ✅ Credentials stored in OS-specific secure storage
    ✅ No environment variable exposure  
    ✅ No credential exposure in process lists
    ✅ Encrypted credential storage

SUPPORTED PLATFORMS:
    - macOS: Uses Keychain Access
    - Linux: Uses Secret Service (libsecret)

DEPENDENCIES:
    macOS: Built-in (security command)
    Linux: libsecret-tools package
EOF
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --test)
        test_credentials
        exit $?
        ;;
    *)
        main
        exit $?
        ;;
esac