#!/bin/bash

# Demonstrate the ORIGINAL BROKEN LOGIC would fail our TDD tests
# This shows the RED phase would have failed before our fix

echo "=== DEMONSTRATING ORIGINAL BROKEN LOGIC ==="
echo "This shows what our TDD tests would catch BEFORE the fix"
echo ""

# Original BROKEN logic from before our fix
test_broken_logic() {
    local dropbox_dir="$1"
    local cli_arg="$2"
    
    (
        export DROPBOX_DIR="$dropbox_dir"
        DEVICE_NAME="test-device"
        set -- "$cli_arg"
        
        # ORIGINAL BROKEN LOGIC (missing device suffix for DROPBOX_DIR)
        DEFAULT_BACKUP_DIR="$HOME/Library/CloudStorage/Dropbox/claude_backup_$DEVICE_NAME"
        if [ -n "${1:-}" ] && [[ "${1:-}" != --* ]]; then
            BACKUP_DESTINATION="${1%/}/claude_backup_$DEVICE_NAME"
        else
            # BUG: This line was missing device suffix for DROPBOX_DIR
            BACKUP_DESTINATION="${DROPBOX_DIR:-$DEFAULT_BACKUP_DIR}"
        fi
        
        echo "$BACKUP_DESTINATION"
    )
}

# Test the critical failing case
echo "Matrix [2,1] - DROPBOX_DIR Environment Override with BROKEN logic"
result=$(test_broken_logic "/custom/dropbox" "")
expected="/custom/dropbox/claude_backup_test-device"

if [[ "$expected" != "$result" ]]; then
    echo "❌ FAIL: BROKEN logic missing device suffix (as expected)"
    echo "   Expected: $expected"  
    echo "   Actual:   $result"
    echo "   BUG: DROPBOX_DIR used directly without device suffix!"
else
    echo "✅ This shouldn't happen - broken logic should fail"
fi

echo ""
echo "This demonstrates our TDD approach caught the critical bug:"
echo "- DROPBOX_DIR environment variable was bypassing device suffix"
echo "- Backups would land in base Dropbox folder instead of device-specific subfolder"
echo "- Our matrix tests would have caught this in RED phase before implementation"