#!/bin/bash
set -euo pipefail

# Fail helper - prints error and exits non-zero
fail() {
    echo "❌ $1" >&2
    if [ -t 1 ]; then
        read -p "Press Enter to exit..."
    fi
    exit 1
}

# Resolve script directory for absolute path invocation
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Mock CLAUDE_HOME with portable mktemp
MOCK_CLAUDE_HOME="$(mktemp -d -t claudetest.XXXXXX 2>/dev/null || mktemp -d /tmp/claudetest.XXXXXX)" || fail "Failed to create temp directory"
export CLAUDE_HOME="$MOCK_CLAUDE_HOME"

# Ensure cleanup on exit
trap 'rm -rf "$MOCK_CLAUDE_HOME"' EXIT

echo "🧪 Testing REAL installation to $MOCK_CLAUDE_HOME"
"$SCRIPT_DIR/install-claude-commands.sh" || fail "Installation failed"

echo "🔍 Verifying installation..."

# Check directories
for dir in agents commands scripts skills; do
    if [ -d "$MOCK_CLAUDE_HOME/$dir" ]; then
        echo "✅ Directory $dir exists"
    else
        fail "Directory $dir MISSING"
    fi
done

# Check files (recursive) with explicit status capture
AGENT_COUNT=$(find "$MOCK_CLAUDE_HOME/agents" -type f 2>/dev/null | wc -l | tr -d ' ') || fail "Failed to count agents"
echo "✅ Found $AGENT_COUNT agents"

COMMAND_COUNT=$(find "$MOCK_CLAUDE_HOME/commands" -type f 2>/dev/null | wc -l | tr -d ' ') || fail "Failed to count commands"
echo "✅ Found $COMMAND_COUNT command files"

# Check subdirectories in commands
if [ -d "$MOCK_CLAUDE_HOME/commands/_copilot_modules" ]; then
    echo "✅ Subdirectory _copilot_modules exists in commands"
else
    fail "Subdirectory _copilot_modules MISSING in commands"
fi

SCRIPT_COUNT=$(find "$MOCK_CLAUDE_HOME/scripts" -type f 2>/dev/null | wc -l | tr -d ' ') || fail "Failed to count scripts"
echo "✅ Found $SCRIPT_COUNT scripts"

# Verify scripts are executable with fail() helper
while IFS= read -r -d '' script; do
    if [ ! -x "$script" ]; then
        fail "Script $(basename "$script") is NOT executable"
    fi
done < <(find "$MOCK_CLAUDE_HOME/scripts" -type f -print0)

echo "✅ All scripts are executable"

SKILL_COUNT=$(find "$MOCK_CLAUDE_HOME/skills" -type f 2>/dev/null | wc -l | tr -d ' ') || fail "Failed to count skills"
echo "✅ Found $SKILL_COUNT skills"

echo "✨ Test PASSED!"
