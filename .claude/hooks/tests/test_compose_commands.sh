#!/bin/bash
# Regression coverage for compose-commands.sh input precedence handling

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_RUN=0
TESTS_PASSED=0

HOOK_SCRIPT="$(dirname "$0")/../compose-commands.sh"

print_result() {
    local status="$1"
    local name="$2"
    if [[ "$status" == "pass" ]]; then
        printf "${GREEN}✓${NC} %s\n" "$name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        printf "${RED}✗${NC} %s\n" "$name"
        if [[ $# -ge 3 ]]; then
            printf "    %s\n" "$3"
        fi
    fi
}

test_contains() {
    local name="$1"
    local actual="$2"
    local expected_substring="$3"
    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ "$actual" == *"$expected_substring"* ]]; then
        print_result pass "$name"
    else
        print_result fail "$name" "Expected substring: $expected_substring\n    Actual output: $actual"
    fi
}

echo "Testing compose-commands.sh input fallbacks"
printf "${YELLOW}=========================================${NC}\n"

# 1. stdin only path
stdin_output=$(printf '/think /debug solve it' | bash "$HOOK_SCRIPT")
test_contains "reads commands from stdin when available" "$stdin_output" "Detected slash commands:/think /debug"

# 2. CLI argument precedence over stdin
cli_precedence_output=$(printf '/plan' | bash "$HOOK_SCRIPT" /think /debug "focus on root cause")
test_contains "CLI arguments take precedence over stdin" "$cli_precedence_output" "Detected slash commands:/think /debug"

# 3. Environment variable precedence over CLI and stdin
env_precedence_output=$(CLAUDE_COMPOSE_INPUT='/review /execute check the repo' bash "$HOOK_SCRIPT" /think)
test_contains "CLAUDE_COMPOSE_INPUT overrides CLI arguments" "$env_precedence_output" "Detected slash commands:/review /execute"

# 4. Pass-through for SLASH_COMMAND_EXECUTE patterns
pass_through_output=$(bash "$HOOK_SCRIPT" SLASH_COMMAND_EXECUTE:/research)
test_contains "passes through SLASH_COMMAND_EXECUTE invocations" "$pass_through_output" "SLASH_COMMAND_EXECUTE:/research"

# Summary
printf "${YELLOW}=========================================${NC}\n"
printf "Tests run: %d\n" "$TESTS_RUN"
printf "Passed:    %d\n" "$TESTS_PASSED"

if [[ "$TESTS_RUN" -ne "$TESTS_PASSED" ]]; then
    printf "${RED}Failures detected${NC}\n" >&2
    exit 1
fi

printf "${GREEN}All compose-commands tests passed${NC}\n"
