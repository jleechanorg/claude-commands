#!/bin/bash
# Test that hooks work from any directory

echo "Testing Directory Independence of Hooks"
echo "======================================"

# Get project root for testing
find_project_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/.git" ]] || [[ -f "$dir/CLAUDE.md" ]]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    echo "$PWD"
}

PROJECT_ROOT=$(find_project_root)
echo "Detected project root: $PROJECT_ROOT"

# Test from current directory (worktree_roadmap)
echo -e "\n📝 Test 1: From current directory ($(basename $PWD))"
echo '{"tool_name": "Write", "tool_input": {"file_path": "bad_file.py", "content": "def test(): pass"}}' | ./claude_command_scripts/check_root_files.sh | head -3

# Test from subdirectory
echo -e "\n📝 Test 2: From subdirectory (claude_command_scripts/)"
cd claude_command_scripts
echo '{"tool_name": "Write", "tool_input": {"file_path": "bad_file.py", "content": "def test(): pass"}}' | ./check_root_files.sh | head -3

# Test from parent directory  
echo -e "\n📝 Test 3: From parent directory"
cd ../..
echo '{"tool_name": "Write", "tool_input": {"file_path": "bad_file.py", "content": "def test(): pass"}}' | ./worktree_roadmap/claude_command_scripts/check_root_files.sh | head -3

# Test anti-demo hook from different directory
echo -e "\n📝 Test 4: Anti-demo hook from different directory"
echo '{"tool_name": "Write", "tool_input": {"file_path": "test.py", "content": "def test():\n    # TODO: implement\n    return \"demo data\""}}' | ./worktree_roadmap/claude_command_scripts/anti_demo_check_claude.sh | head -3

echo -e "\n✅ All tests should show proper detection regardless of current directory"