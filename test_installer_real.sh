#!/bin/bash
set -e

# Resolve script directory for absolute path invocation
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Mock CLAUDE_HOME with portable mktemp
MOCK_CLAUDE_HOME="$(mktemp -d -t claudetest.XXXXXX 2>/dev/null || mktemp -d /tmp/claudetest.XXXXXX)"
export CLAUDE_HOME="$MOCK_CLAUDE_HOME"

# Ensure cleanup on exit
trap 'rm -rf "$MOCK_CLAUDE_HOME"' EXIT

echo "🧪 Testing REAL installation to $MOCK_CLAUDE_HOME"
"$SCRIPT_DIR/install-claude-commands.sh"

echo "🔍 Verifying installation..."

# Check directories
for dir in agents commands scripts skills; do
    if [ -d "$MOCK_CLAUDE_HOME/$dir" ]; then
        echo "✅ Directory $dir exists"
    else
        echo "❌ Directory $dir MISSING"
        exit 1
    fi
done

# Check files (recursive)
AGENT_COUNT=$(find "$MOCK_CLAUDE_HOME/agents" -type f | wc -l | tr -d ' ')
echo "✅ Found $AGENT_COUNT agents"

COMMAND_COUNT=$(find "$MOCK_CLAUDE_HOME/commands" -type f | wc -l | tr -d ' ')
echo "✅ Found $COMMAND_COUNT command files"

# Check subdirectories in commands
if [ -d "$MOCK_CLAUDE_HOME/commands/_copilot_modules" ]; then
    echo "✅ Subdirectory _copilot_modules exists in commands"
else
    echo "❌ Subdirectory _copilot_modules MISSING in commands"
    exit 1
fi

SCRIPT_COUNT=$(find "$MOCK_CLAUDE_HOME/scripts" -type f | wc -l | tr -d ' ')

echo "✅ Found $SCRIPT_COUNT scripts"



# Verify scripts are executable

while IFS= read -r -d '' script; do

    if [ ! -x "$script" ]; then

        echo "❌ Script $(basename "$script") is NOT executable"

        exit 1

    fi

done < <(find "$MOCK_CLAUDE_HOME/scripts" -type f -print0)

echo "✅ All scripts are executable"



SKILL_COUNT=$(find "$MOCK_CLAUDE_HOME/skills" -type f | wc -l | tr -d ' ')

echo "✅ Found $SKILL_COUNT skills"



echo "✨ Test PASSED!"
