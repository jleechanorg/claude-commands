#!/bin/bash
set -euo pipefail

fail() {
    local message="$1"
    echo "❌ $message"
    if [ -t 0 ]; then
        read -r -p "Press Enter to continue..."
    fi
    exit 1
}

count_files() {
    local dir="$1"
    local -a files=()
    if ! mapfile -d '' -t files < <(find "$dir" -type f -print0); then
        fail "Failed to count files in $dir"
    fi
    echo "${#files[@]}"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOCK_CLAUDE_HOME="$(mktemp -d -t claudetest.XXXXXX 2>/dev/null || mktemp -d /tmp/claudetest.XXXXXX)"
export CLAUDE_HOME="$MOCK_CLAUDE_HOME"
trap 'rm -rf "$MOCK_CLAUDE_HOME"' EXIT

echo "🧪 Testing REAL installation to $MOCK_CLAUDE_HOME"
"$SCRIPT_DIR/install-claude-commands.sh"

echo "🔍 Verifying installation..."
for dir in agents commands scripts skills; do
    [ -d "$MOCK_CLAUDE_HOME/$dir" ] || fail "Directory $dir MISSING"
    echo "✅ Directory $dir exists"
done

AGENT_COUNT="$(count_files "$MOCK_CLAUDE_HOME/agents")"
echo "✅ Found $AGENT_COUNT agents"

COMMAND_COUNT="$(count_files "$MOCK_CLAUDE_HOME/commands")"
echo "✅ Found $COMMAND_COUNT command files"

[ -d "$MOCK_CLAUDE_HOME/commands/_copilot_modules" ] || fail "Subdirectory _copilot_modules MISSING in commands"
echo "✅ Subdirectory _copilot_modules exists in commands"

SCRIPT_COUNT="$(count_files "$MOCK_CLAUDE_HOME/scripts")"
echo "✅ Found $SCRIPT_COUNT scripts"

while IFS= read -r -d '' script; do
    [ -x "$script" ] || fail "Script $(basename "$script") is NOT executable"
done < <(find "$MOCK_CLAUDE_HOME/scripts" -type f -print0)
echo "✅ All scripts are executable"

SKILL_COUNT="$(count_files "$MOCK_CLAUDE_HOME/skills")"
echo "✅ Found $SKILL_COUNT skills"

echo "✨ Test PASSED!"
