#!/bin/bash
# test_analyze_code_authenticity.sh - Unit tests for code authenticity detection
# Tests various scenarios including edge cases and error conditions

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test directory setup
TEST_DIR=$(mktemp -d "/tmp/test_code_auth_XXXXXX")
ORIGINAL_DIR=$(pwd)

# Cleanup function
cleanup() {
    cd "$ORIGINAL_DIR"
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

# Test framework functions
run_test() {
    local test_name="$1"
    local test_function="$2"
    
    echo -e "\n${BLUE}Running: $test_name${NC}"
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if $test_function; then
        echo -e "${GREEN}✅ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-Assertion failed}"
    
    if [[ "$expected" != "$actual" ]]; then
        echo -e "${RED}$message${NC}"
        echo "Expected: $expected"
        echo "Actual: $actual"
        return 1
    fi
    return 0
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-String not found}"
    
    if ! echo "$haystack" | grep -q "$needle"; then
        echo -e "${RED}$message${NC}"
        echo "Looking for: $needle"
        echo "In: $haystack"
        return 1
    fi
    return 0
}

assert_file_exists() {
    local file="$1"
    local message="${2:-File not found}"
    
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}$message: $file${NC}"
        return 1
    fi
    return 0
}

assert_file_not_exists() {
    local file="$1"
    local message="${2:-File should not exist}"
    
    if [[ -f "$file" ]]; then
        echo -e "${RED}$message: $file${NC}"
        return 1
    fi
    return 0
}

# Mock Claude CLI for testing
create_mock_claude() {
    local response="$1"
    cat > "$TEST_DIR/claude" << EOF
#!/bin/bash
# Mock claude CLI for testing
echo "$response"
exit 0
EOF
    chmod +x "$TEST_DIR/claude"
}

# Create test git repository
setup_test_repo() {
    cd "$TEST_DIR"
    git init --quiet
    git config user.email "test@example.com"
    git config user.name "Test User"
    
    # Create initial commit
    echo "initial" > README.md
    git add README.md
    git commit -m "Initial commit" --quiet
    
    # Create main branch and set it as remote
    git branch -M main
    
    # Simulate remote by creating a bare repo
    git init --bare "$TEST_DIR/remote.git" --quiet
    git remote add origin "$TEST_DIR/remote.git"
    git push -u origin main --quiet
}

# Test 1: No changed files
test_no_changed_files() {
    setup_test_repo
    
    output=$("$ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh" 2>&1)
    exit_code=$?
    
    assert_equals 0 "$exit_code" "Exit code should be 0" &&
    assert_contains "$output" "No code files changed" "Should report no changes"
}

# Test 2: Changed files but no code files
test_no_code_files() {
    setup_test_repo
    
    # Add non-code files on a branch
    git checkout -b test-branch --quiet
    echo "Some docs" > docs.md
    echo "Config" > config.txt
    git add .
    git commit -m "Add non-code files" --quiet
    
    output=$("$ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh" 2>&1)
    exit_code=$?
    
    assert_equals 0 "$exit_code" "Exit code should be 0" &&
    assert_contains "$output" "No code files changed" "Should ignore non-code files"
}

# Test 3: File extension extraction
test_file_extension_extraction() {
    setup_test_repo
    
    # Create files with multiple dots on a branch
    git checkout -b test-branch --quiet
    mkdir -p src
    echo "print('test')" > "src/my.test.script.py"
    echo "console.log('test')" > "src/app.min.js"
    echo "func main() {}" > "src/server.go"
    git add .
    git commit -m "Add code files" --quiet
    
    # Mock claude to return analysis
    create_mock_claude "✅ No fake code patterns detected"
    export PATH="$TEST_DIR:$PATH"
    
    output=$("$ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh" 2>&1)
    
    # Check if files were processed
    assert_contains "$output" "my.test.script.py" "Should process Python file with dots" &&
    assert_contains "$output" "app.min.js" "Should process JS file with dots" &&
    assert_contains "$output" "server.go" "Should process Go file"
}

# Test 4: Fake code detection
test_fake_code_detection() {
    setup_test_repo
    
    # Create a file with fake code pattern on a branch
    git checkout -b test-branch --quiet
    cat > fake_code.py << 'EOF'
def handle_request(request):
    if 'error' in request.lower():
        return "Thank you for reporting this error!"
    elif 'bug' in request.lower():
        return "Excellent bug report!"
    else:
        return "Generic response"
EOF
    git add fake_code.py
    git commit -m "Add fake code" --quiet
    
    # Mock claude to detect fake code
    create_mock_claude "🚨 FAKE CODE DETECTED
    
File: fake_code.py
- Line 2-6: Hardcoded responses based on keyword matching
- This is fake because it uses simple keyword detection instead of real analysis"
    export PATH="$TEST_DIR:$PATH"
    
    output=$("$ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh" 2>&1)
    exit_code=$?
    
    assert_equals 1 "$exit_code" "Exit code should be 1 for fake code" &&
    assert_contains "$output" "Fake code patterns detected!" "Should report fake code" &&
    assert_contains "$output" "Consider reviewing the flagged code" "Should warn user"
}

# Test 5: Clean code passes
test_clean_code_passes() {
    setup_test_repo
    
    # Create legitimate code on a branch
    git checkout -b test-branch --quiet
    cat > good_code.py << 'EOF'
import logging

def process_data(data):
    """Process incoming data with proper validation."""
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    result = {}
    for key, value in data.items():
        result[key] = transform_value(value)
    
    return result

def transform_value(value):
    """Apply business logic transformation."""
    return value * 2 if isinstance(value, (int, float)) else str(value)
EOF
    git add good_code.py
    git commit -m "Add good code" --quiet
    
    # Mock claude to approve code
    create_mock_claude "✅ No fake code patterns detected"
    export PATH="$TEST_DIR:$PATH"
    
    output=$("$ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh" 2>&1)
    exit_code=$?
    
    assert_equals 0 "$exit_code" "Exit code should be 0 for clean code" &&
    assert_contains "$output" "No fake code patterns detected" "Should approve clean code"
}

# Test 6: Error handling - Claude not available
test_claude_not_available() {
    setup_test_repo
    
    # Create code file on a branch
    git checkout -b test-branch --quiet
    echo "test code" > test.py
    git add test.py
    git commit -m "Add test file" --quiet
    
    # Don't add mock claude to PATH
    output=$("$ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh" 2>&1)
    exit_code=$?
    
    assert_equals 0 "$exit_code" "Should continue when Claude not available" &&
    assert_contains "$output" "Claude CLI not available" "Should report Claude missing"
}

# Test 7: Cleanup verification
test_cleanup_on_exit() {
    setup_test_repo
    
    # Create code file on a branch
    git checkout -b test-branch --quiet
    echo "test" > test.js
    git add test.js
    git commit -m "Add JS file" --quiet
    
    # Create mock that sleeps to test interrupt
    cat > "$TEST_DIR/claude" << 'EOF'
#!/bin/bash
echo "✅ No fake code patterns detected"
# Create a marker file to verify cleanup
touch /tmp/code_analysis_*.md.marker 2>/dev/null || true
EOF
    chmod +x "$TEST_DIR/claude"
    export PATH="$TEST_DIR:$PATH"
    
    # Run script
    "$ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh" >/dev/null 2>&1
    
    # Check that temp files are cleaned up
    temp_files=$(find /tmp -name "code_analysis_*.md" -mmin -1 2>/dev/null | wc -l)
    assert_equals 0 "$temp_files" "Temporary files should be cleaned up"
}

# Test 8: Multiple file types
test_multiple_file_types() {
    setup_test_repo
    
    # Create various code files on a branch
    git checkout -b test-branch --quiet
    echo "code" > test.py
    echo "code" > test.js
    echo "code" > test.ts
    echo "code" > test.go
    echo "code" > test.rs
    echo "code" > test.java
    echo "not code" > test.txt
    echo "not code" > test.md
    git add .
    git commit -m "Add various files" --quiet
    
    create_mock_claude "✅ No fake code patterns detected"
    export PATH="$TEST_DIR:$PATH"
    
    output=$("$ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh" 2>&1)
    
    # Verify correct files were analyzed
    assert_contains "$output" "test.py" "Should analyze Python" &&
    assert_contains "$output" "test.js" "Should analyze JavaScript" &&
    assert_contains "$output" "test.go" "Should analyze Go" &&
    ! assert_contains "$output" "test.txt" "Should not analyze text files" &&
    ! assert_contains "$output" "test.md" "Should not analyze markdown"
}

# Test 9: Error log file creation
test_error_logging() {
    setup_test_repo
    
    # Create code file on a branch
    git checkout -b test-branch --quiet
    echo "test" > test.py
    git add test.py
    git commit -m "Add Python file" --quiet
    
    # Create mock that fails
    cat > "$TEST_DIR/claude" << 'EOF'
#!/bin/bash
echo "Error: API rate limit exceeded" >&2
exit 1
EOF
    chmod +x "$TEST_DIR/claude"
    export PATH="$TEST_DIR:$PATH"
    
    output=$("$ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh" 2>&1)
    
    assert_contains "$output" "Check .* for details" "Should mention error log"
}

# Test 10: Learn command integration
test_learn_command_integration() {
    setup_test_repo
    
    # Create fake code on a branch
    git checkout -b test-branch --quiet
    echo "fake code" > fake.py
    git add fake.py
    git commit -m "Add fake code" --quiet
    
    # Create mock learn.sh
    mkdir -p "$TEST_DIR/claude_command_scripts/commands"
    cat > "$TEST_DIR/claude_command_scripts/commands/learn.sh" << 'EOF'
#!/bin/bash
echo "LEARN: Received input"
cat > /tmp/learn_received.txt
EOF
    chmod +x "$TEST_DIR/claude_command_scripts/commands/learn.sh"
    
    # Mock claude to detect fake code
    create_mock_claude "🚨 FAKE CODE DETECTED - Testing learn integration"
    export PATH="$TEST_DIR:$PATH"
    
    cd "$TEST_DIR"
    output=$("$ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh" 2>&1)
    
    assert_contains "$output" "Calling /learn" "Should call learn command" &&
    assert_file_exists "/tmp/learn_received.txt" "Learn should receive input"
    
    # Cleanup
    rm -f /tmp/learn_received.txt
}

# Main test runner
main() {
    echo -e "${BLUE}=== Code Authenticity Detection Unit Tests ===${NC}"
    echo "Test script: $0"
    echo "Testing: $ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh"
    echo ""
    
    # Run all tests
    run_test "No changed files" test_no_changed_files
    run_test "No code files changed" test_no_code_files
    run_test "File extension extraction" test_file_extension_extraction
    run_test "Fake code detection" test_fake_code_detection
    run_test "Clean code passes" test_clean_code_passes
    run_test "Claude not available" test_claude_not_available
    run_test "Cleanup on exit" test_cleanup_on_exit
    run_test "Multiple file types" test_multiple_file_types
    run_test "Error logging" test_error_logging
    run_test "Learn command integration" test_learn_command_integration
    
    # Summary
    echo -e "\n${BLUE}=== Test Summary ===${NC}"
    echo "Tests run: $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}✅ All tests passed!${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Some tests failed!${NC}"
        exit 1
    fi
}

# Run tests
main "$@"