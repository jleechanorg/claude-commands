#!/bin/bash
# Start the Testing Agent to ensure all tests pass

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Start the testing agent
./start_claude_agent.sh testing "Run ./run_tests.sh and fix any failing tests until all pass (100%)" "$(cd .. && pwd)"