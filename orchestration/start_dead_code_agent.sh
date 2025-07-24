#!/bin/bash
# Start the Dead Code Cleanup Agent with full context

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure we have the prompt file
if [ ! -f "dead_code_agent_prompt.txt" ]; then
    echo "Creating dead code context file..."
    cat > dead_code_agent_prompt.txt << 'EOF'
You are a Dead Code Cleanup Specialist. You have analyzed the codebase and found the following dead code:

## Dead Code Findings:

1. **Unused Functions in constants.py:**
   - `get_attribute_codes_for_system()` at line 100 - This function returns attribute codes but thorough analysis shows it's never imported or called anywhere
   - Remnant of multi-system design

2. **Potentially Unused Methods:**
   - `numeric_field_converter.py`: `convert_all_possible_ints()` (lines 69-97)
   - Only used internally and in tests, but not from external code

3. **Commented/Archived Code:**
   - Lines 78-84 in constants.py: Archived Destiny attribute system
   - Multiple references to archived features

## Your Task:

1. Create a new branch: `fix/remove-dead-code-cleanup`
2. Remove the identified dead code carefully:
   - Remove `get_attribute_codes_for_system()` function from constants.py
   - Evaluate if `convert_all_possible_ints()` is truly unused
   - Clean up commented archive code
3. Run tests to ensure nothing breaks: `./run_tests.sh`
4. If tests fail, investigate and fix any dependencies
5. Commit changes with descriptive message
6. Use `/pr` command to create a full PR with:
   - Title: "Remove dead code and unused functions"
   - Description listing what was removed and why
   - Test results showing all tests still pass

Start by creating the branch and removing the dead code systematically.
EOF
fi

# Start the agent
./start_claude_agent.sh dead-code "" "$(cd .. && pwd)"