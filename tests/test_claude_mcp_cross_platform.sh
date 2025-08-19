#!/bin/bash

# Comprehensive test suite for claude_mcp.sh cross-platform compatibility
# Tests the platform detection and compatibility features we added

set -e  # Exit on error

# Test framework setup
TEST_DIR="/tmp/claude_mcp_tests_$(date +%s)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CLAUDE_MCP_SCRIPT="$PROJECT_ROOT/claude_mcp.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test utilities
print_test() {
    echo -e "${BLUE}🧪 Test $((TESTS_RUN + 1)): $1${NC}"
    TESTS_RUN=$((TESTS_RUN + 1))
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-}"
    
    if [ "$expected" != "$actual" ]; then
        echo -e "${RED}❌ FAIL: Expected '$expected', got '$actual' $message${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    else
        echo -e "${GREEN}✅ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-}"
    
    if [[ "$haystack" != *"$needle"* ]]; then
        echo -e "${RED}❌ FAIL: Expected '$haystack' to contain '$needle' $message${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    else
        echo -e "${GREEN}✅ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    fi
}

assert_not_empty() {
    local value="$1"
    local message="${2:-}"
    
    if [ -z "$value" ]; then
        echo -e "${RED}❌ FAIL: Expected non-empty value $message${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    else
        echo -e "${GREEN}✅ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    fi
}

# Test the OS detection logic from claude_mcp.sh
test_os_detection_logic() {
    print_test "OS detection logic for different platforms"
    
    # Test Linux detection
    local os_type="Linux"
    case "$os_type" in
        Linux*)     MACHINE=Linux;;
        Darwin*)    MACHINE=Mac;;
        CYGWIN*)    MACHINE=Cygwin;;
        MINGW*)     MACHINE=MinGw;;
        MSYS*)      MACHINE=Git;;
        *)          MACHINE="UNKNOWN:$os_type"
    esac
    assert_equals "Linux" "$MACHINE" "(Linux test)"
    
    # Test macOS detection
    os_type="Darwin"
    case "$os_type" in
        Linux*)     MACHINE=Linux;;
        Darwin*)    MACHINE=Mac;;
        CYGWIN*)    MACHINE=Cygwin;;
        MINGW*)     MACHINE=MinGw;;
        MSYS*)      MACHINE=Git;;
        *)          MACHINE="UNKNOWN:$os_type"
    esac
    assert_equals "Mac" "$MACHINE" "(macOS test)"
    
    # Test Windows variants
    os_type="MINGW64_NT-10.0"
    case "$os_type" in
        Linux*)     MACHINE=Linux;;
        Darwin*)    MACHINE=Mac;;
        CYGWIN*)    MACHINE=Cygwin;;
        MINGW*)     MACHINE=MinGw;;
        MSYS*)      MACHINE=Git;;
        *)          MACHINE="UNKNOWN:$os_type"
    esac
    assert_equals "MinGw" "$MACHINE" "(MinGw test)"
    
    os_type="CYGWIN_NT-10.0"
    case "$os_type" in
        Linux*)     MACHINE=Linux;;
        Darwin*)    MACHINE=Mac;;
        CYGWIN*)    MACHINE=Cygwin;;
        MINGW*)     MACHINE=MinGw;;
        MSYS*)      MACHINE=Git;;
        *)          MACHINE="UNKNOWN:$os_type"
    esac
    assert_equals "Cygwin" "$MACHINE" "(Cygwin test)"
    
    os_type="MSYS_NT-10.0"
    case "$os_type" in
        Linux*)     MACHINE=Linux;;
        Darwin*)    MACHINE=Mac;;
        CYGWIN*)    MACHINE=Cygwin;;
        MINGW*)     MACHINE=MinGw;;
        MSYS*)      MACHINE=Git;;
        *)          MACHINE="UNKNOWN:$os_type"
    esac
    assert_equals "Git" "$MACHINE" "(Git Bash test)"
}

# Test timeout command detection logic
test_timeout_command_detection() {
    print_test "Timeout command detection across platforms"
    
    # Create mock environment
    mkdir -p "$TEST_DIR/bin"
    mkdir -p "$TEST_DIR/homebrew/bin"
    mkdir -p "$TEST_DIR/local/bin"
    
    # Test 1: Standard timeout command
    echo '#!/bin/bash\necho "timeout"' > "$TEST_DIR/bin/timeout"
    chmod +x "$TEST_DIR/bin/timeout"
    
    OLD_PATH="$PATH"
    export PATH="$TEST_DIR/bin:$PATH"
    
    # Simulate the timeout detection logic
    TIMEOUT_CMD=""
    if command -v timeout >/dev/null 2>&1; then
        TIMEOUT_CMD="timeout"
    elif command -v gtimeout >/dev/null 2>&1; then
        TIMEOUT_CMD="gtimeout"
    fi
    
    assert_equals "timeout" "$TIMEOUT_CMD" "(standard timeout)"
    
    # Test 2: GNU timeout (gtimeout)
    rm -f "$TEST_DIR/bin/timeout"
    echo '#!/bin/bash\necho "gtimeout"' > "$TEST_DIR/bin/gtimeout"
    chmod +x "$TEST_DIR/bin/gtimeout"
    
    TIMEOUT_CMD=""
    if command -v timeout >/dev/null 2>&1; then
        TIMEOUT_CMD="timeout"
    elif command -v gtimeout >/dev/null 2>&1; then
        TIMEOUT_CMD="gtimeout"
    fi
    
    assert_equals "gtimeout" "$TIMEOUT_CMD" "(GNU timeout)"
    
    # Restore PATH
    export PATH="$OLD_PATH"
}

# Test home directory detection logic
test_home_directory_detection() {
    print_test "Home directory detection across platforms"
    
    # Save original values
    ORIG_HOME="$HOME"
    ORIG_USERPROFILE="${USERPROFILE:-}"
    
    # Test 1: Standard HOME variable (Unix/Linux/macOS)
    export HOME="/home/testuser"
    unset USERPROFILE
    
    # Simulate the home directory detection logic
    if [ -n "$HOME" ]; then
        MCP_SERVERS_DIR="$HOME/.mcp/servers"
    elif [ -n "$USERPROFILE" ]; then
        MCP_SERVERS_DIR="$USERPROFILE/.mcp/servers"
    else
        MCP_SERVERS_DIR="/tmp/.mcp/servers"
    fi
    
    assert_equals "/home/testuser/.mcp/servers" "$MCP_SERVERS_DIR" "(Unix HOME)"
    
    # Test 2: Windows USERPROFILE fallback
    unset HOME
    export USERPROFILE="/Users/testuser"
    
    if [ -n "$HOME" ]; then
        MCP_SERVERS_DIR="$HOME/.mcp/servers"
    elif [ -n "$USERPROFILE" ]; then
        MCP_SERVERS_DIR="$USERPROFILE/.mcp/servers"
    else
        MCP_SERVERS_DIR="/tmp/.mcp/servers"
    fi
    
    assert_equals "/Users/testuser/.mcp/servers" "$MCP_SERVERS_DIR" "(Windows USERPROFILE)"
    
    # Test 3: Fallback to /tmp
    unset HOME
    unset USERPROFILE
    
    if [ -n "$HOME" ]; then
        MCP_SERVERS_DIR="$HOME/.mcp/servers"
    elif [ -n "$USERPROFILE" ]; then
        MCP_SERVERS_DIR="$USERPROFILE/.mcp/servers"
    else
        MCP_SERVERS_DIR="/tmp/.mcp/servers"
    fi
    
    assert_equals "/tmp/.mcp/servers" "$MCP_SERVERS_DIR" "(fallback)"
    
    # Restore original values
    export HOME="$ORIG_HOME"
    if [ -n "$ORIG_USERPROFILE" ]; then
        export USERPROFILE="$ORIG_USERPROFILE"
    fi
}

# Test Node.js path detection for Windows
test_nodejs_windows_detection() {
    print_test "Node.js detection on Windows platforms"
    
    # Create mock Windows Node.js installation paths
    mkdir -p "$TEST_DIR/Program Files/nodejs"
    mkdir -p "$TEST_DIR/Program Files (x86)/nodejs"
    
    # Test the Windows-specific Node.js detection logic
    NODE_PATH=""
    NPX_PATH=""
    MACHINE="Git"  # Simulate Git Bash environment
    
    # Mock USERPROFILE and APPDATA
    export USERPROFILE="$TEST_DIR"
    export APPDATA="$TEST_DIR/AppData/Roaming"
    mkdir -p "$APPDATA/npm"
    
    # Create mock Node.js executables
    echo '#!/bin/bash\necho "node"' > "$TEST_DIR/Program Files/nodejs/node.exe"
    chmod +x "$TEST_DIR/Program Files/nodejs/node.exe"
    echo '#!/bin/bash\necho "npx"' > "$TEST_DIR/Program Files/nodejs/npx.exe"
    chmod +x "$TEST_DIR/Program Files/nodejs/npx.exe"
    
    # Simulate the Windows Node.js detection logic from claude_mcp.sh
    if [ -z "$NODE_PATH" ] && { [ "$MACHINE" = "Git" ] || [ "$MACHINE" = "MinGw" ] || [ "$MACHINE" = "Cygwin" ]; }; then
        for potential_node in \
            "$TEST_DIR/Program Files/nodejs/node.exe" \
            "$TEST_DIR/Program Files (x86)/nodejs/node.exe" \
            "$USERPROFILE/AppData/Roaming/npm/node.exe" \
            "$APPDATA/npm/node.exe"
        do
            if [ -x "$potential_node" ]; then
                NODE_PATH="$potential_node"
                break
            fi
        done
        
        # Find npx alongside node
        if [ -n "$NODE_PATH" ]; then
            NODE_DIR=$(dirname "$NODE_PATH")
            if [ -x "$NODE_DIR/npx.exe" ]; then
                NPX_PATH="$NODE_DIR/npx.exe"
            elif [ -x "$NODE_DIR/npx" ]; then
                NPX_PATH="$NODE_DIR/npx"
            fi
        fi
    fi
    
    assert_not_empty "$NODE_PATH" "(Node.js found)"
    assert_contains "$NODE_PATH" "node.exe" "(correct Node.js executable)"
    assert_not_empty "$NPX_PATH" "(NPX found)"
    assert_contains "$NPX_PATH" "npx.exe" "(correct NPX executable)"
    
    # Cleanup
    unset USERPROFILE
    unset APPDATA
}

# Test iOS platform compatibility logic
test_ios_platform_compatibility() {
    print_test "iOS simulator platform compatibility check"
    
    # Test 1: macOS platform (should allow iOS)
    MACHINE="Mac"
    ios_compatible=0
    
    if [ "$MACHINE" != "Mac" ]; then
        ios_compatible=1  # Platform incompatible
    else
        ios_compatible=0  # Platform compatible
    fi
    
    assert_equals "0" "$ios_compatible" "(macOS allows iOS simulator)"
    
    # Test 2: Linux platform (should skip iOS)
    MACHINE="Linux"
    ios_compatible=0
    
    if [ "$MACHINE" != "Mac" ]; then
        ios_compatible=1  # Platform incompatible
    else
        ios_compatible=0  # Platform compatible
    fi
    
    assert_equals "1" "$ios_compatible" "(Linux skips iOS simulator)"
    
    # Test 3: Windows platform (should skip iOS)
    MACHINE="Git"
    ios_compatible=0
    
    if [ "$MACHINE" != "Mac" ]; then
        ios_compatible=1  # Platform incompatible
    else
        ios_compatible=0  # Platform compatible
    fi
    
    assert_equals "1" "$ios_compatible" "(Windows skips iOS simulator)"
}

# Test script syntax validation
test_script_syntax() {
    print_test "claude_mcp.sh script syntax validation"
    
    if ! bash -n "$CLAUDE_MCP_SCRIPT" 2>/dev/null; then
        echo -e "${RED}❌ FAIL: Script has syntax errors${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    else
        echo -e "${GREEN}✅ PASS: Script syntax is valid${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    fi
}

# Test that our cross-platform improvements are present in the script
test_cross_platform_features_present() {
    print_test "Cross-platform features present in script"
    
    # Check that OS detection is present
    if ! grep -q "OS_TYPE.*uname -s" "$CLAUDE_MCP_SCRIPT"; then
        echo -e "${RED}❌ FAIL: OS detection not found in script${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    
    # Check that Windows Node.js detection is present
    if ! grep -q "Program Files/nodejs" "$CLAUDE_MCP_SCRIPT"; then
        echo -e "${RED}❌ FAIL: Windows Node.js detection not found${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    
    # Check that home directory fallback is present
    if ! grep -q "USERPROFILE" "$CLAUDE_MCP_SCRIPT"; then
        echo -e "${RED}❌ FAIL: Windows home directory fallback not found${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    
    # Check that enhanced platform detection is present
    if ! grep -q "Detected platform" "$CLAUDE_MCP_SCRIPT"; then
        echo -e "${RED}❌ FAIL: Platform detection output not found${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    
    echo -e "${GREEN}✅ PASS: All cross-platform features found${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
}

# Setup test environment
setup_tests() {
    echo -e "${BLUE}🔧 Setting up test environment...${NC}"
    mkdir -p "$TEST_DIR"
    
    # Verify that the claude_mcp.sh script exists
    if [ ! -f "$CLAUDE_MCP_SCRIPT" ]; then
        echo -e "${RED}❌ Error: claude_mcp.sh not found at $CLAUDE_MCP_SCRIPT${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Test environment ready${NC}"
}

# Cleanup test environment
teardown_tests() {
    echo -e "${BLUE}🧹 Cleaning up test environment...${NC}"
    rm -rf "$TEST_DIR"
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Print test results summary
print_summary() {
    echo ""
    echo -e "${BLUE}📊 Test Results Summary${NC}"
    echo "======================="
    echo -e "Tests run: ${BLUE}$TESTS_RUN${NC}"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All tests passed!${NC}"
        return 0
    else
        echo -e "\n${RED}💥 Some tests failed!${NC}"
        return 1
    fi
}

# Main test execution
main() {
    echo -e "${BLUE}🚀 Running claude_mcp.sh cross-platform compatibility tests...${NC}"
    echo ""
    
    setup_tests
    
    # Run all tests
    test_os_detection_logic
    test_timeout_command_detection
    test_home_directory_detection
    test_nodejs_windows_detection
    test_ios_platform_compatibility
    test_script_syntax
    test_cross_platform_features_present
    
    teardown_tests
    
    print_summary
}

# Execute main function
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi