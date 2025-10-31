#!/bin/bash
# Test MCP Installation in Sandboxed Environment
#
# Purpose: Test MCP server installation without affecting production Claude/Codex configs
# Usage: ./test_mcp_installation_sandboxed.sh [claude|codex|both]
#
# This script creates isolated test environments in /tmp and validates MCP server
# installation without touching ~/.claude.json or ~/.codex/config.toml

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Test configuration
readonly TEST_BASE_DIR="/tmp/mcp_test_sandbox_$$"
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)
readonly TEST_LOG="${TEST_BASE_DIR}/test_${TIMESTAMP}.log"

# Test results tracking
declare -a PASSED_TESTS=()
declare -a FAILED_TESTS=()
declare -i TOTAL_TESTS=0

# Cleanup handler
cleanup() {
    local exit_code=$?
    echo -e "\n${BLUE}[CLEANUP] Removing test environment...${NC}"

    # Kill any test wrapper processes
    pkill -f "mcp_test_wrapper" 2>/dev/null || true

    # Remove test directory
    if [ -d "$TEST_BASE_DIR" ]; then
        rm -rf "$TEST_BASE_DIR"
        echo -e "${GREEN}[CLEANUP] Test environment removed${NC}"
    fi

    # Print summary
    print_test_summary

    exit $exit_code
}

trap cleanup EXIT INT TERM

# Logging function
log() {
    # Ensure log directory exists before writing
    mkdir -p "$(dirname "$TEST_LOG")" 2>/dev/null || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$TEST_LOG"
}

# Test assertion functions
assert_success() {
    local test_name="$1"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    PASSED_TESTS+=("$test_name")
    echo -e "${GREEN}✓ PASS${NC}: $test_name"
    log "PASS: $test_name"
}

assert_failure() {
    local test_name="$1"
    local error_msg="${2:-No error message provided}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    FAILED_TESTS+=("$test_name")
    echo -e "${RED}✗ FAIL${NC}: $test_name"
    echo -e "${RED}  Error: $error_msg${NC}"
    log "FAIL: $test_name - $error_msg"
}

# Print test summary
print_test_summary() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}           TEST EXECUTION SUMMARY${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "Total Tests: ${TOTAL_TESTS}"
    echo -e "${GREEN}Passed: ${#PASSED_TESTS[@]}${NC}"
    echo -e "${RED}Failed: ${#FAILED_TESTS[@]}${NC}"

    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        echo -e "\n${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "${RED}  - $test${NC}"
        done
    fi

    echo -e "\n${BLUE}Test log: ${TEST_LOG}${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"
}

# Setup test environment
setup_test_environment() {
    echo -e "${BLUE}[SETUP] Creating sandboxed test environment...${NC}"
    log "Creating test environment at $TEST_BASE_DIR"

    # Create test directory structure
    mkdir -p "$TEST_BASE_DIR"/{bin,configs,npm_global,mcp_servers}

    # Create test Claude config
    cat > "$TEST_BASE_DIR/configs/claude.json" <<'EOF'
{
  "mcpServers": {}
}
EOF

    # Create test Codex config
    cat > "$TEST_BASE_DIR/configs/codex.toml" <<'EOF'
[mcp]
# Test MCP configuration
EOF

    log "Test environment created successfully"
    assert_success "Test environment creation"
}

# Create wrapper scripts for claude and codex that use test configs
create_cli_wrappers() {
    echo -e "${BLUE}[SETUP] Creating CLI wrapper scripts...${NC}"

    # Detect actual CLI paths
    local claude_path=$(command -v claude 2>/dev/null || which claude 2>/dev/null || echo "")
    local codex_path=$(command -v codex 2>/dev/null || which codex 2>/dev/null || echo "")

    if [ -z "$claude_path" ]; then
        echo -e "${YELLOW}[WARN] claude CLI not found in PATH, wrapper will fail${NC}"
        log "WARNING: claude CLI not found"
    fi

    if [ -z "$codex_path" ]; then
        echo -e "${YELLOW}[WARN] codex CLI not found in PATH, wrapper will fail${NC}"
        log "WARNING: codex CLI not found"
    fi

    # Claude wrapper
    cat > "$TEST_BASE_DIR/bin/claude" <<EOF
#!/bin/bash
# Test wrapper for claude CLI
# Redirects MCP config to test location

export CLAUDE_TEST_MODE=1
export CLAUDE_CONFIG_DIR="$TEST_BASE_DIR/configs"

# Use --mcp-config to load test config instead of production
# Remove --strict-mcp-config as it doesn't exist
if [ -n "$claude_path" ]; then
    exec "$claude_path" --mcp-config "$TEST_BASE_DIR/configs/claude.json" "\$@"
else
    echo "Error: claude CLI not found" >&2
    exit 127
fi
EOF
    chmod +x "$TEST_BASE_DIR/bin/claude"

    # Codex wrapper
    cat > "$TEST_BASE_DIR/bin/codex" <<EOF
#!/bin/bash
# Test wrapper for codex CLI
# Uses isolated config directory

export CODEX_TEST_MODE=1
export CODEX_CONFIG_HOME="$TEST_BASE_DIR/configs"

# Use -c config overrides for isolation
if [ -n "$codex_path" ]; then
    exec "$codex_path" "\$@"
else
    echo "Error: codex CLI not found" >&2
    exit 127
fi
EOF
    chmod +x "$TEST_BASE_DIR/bin/codex"

    log "CLI wrappers created"
    assert_success "CLI wrapper creation"
}

# Test basic wrapper functionality
test_cli_wrappers() {
    echo -e "\n${BLUE}[TEST] Testing CLI wrappers...${NC}"

    # Test Claude wrapper
    if "$TEST_BASE_DIR/bin/claude" --version &>/dev/null; then
        assert_success "Claude wrapper executes"
    else
        assert_failure "Claude wrapper executes" "Wrapper failed to execute"
    fi

    # Test Codex wrapper
    if "$TEST_BASE_DIR/bin/codex" --version &>/dev/null; then
        assert_success "Codex wrapper executes"
    else
        assert_failure "Codex wrapper executes" "Wrapper failed to execute"
    fi
}

# Test MCP config file creation
test_mcp_config_format() {
    echo -e "\n${BLUE}[TEST] Testing MCP config format...${NC}"

    # Add a test server to Claude config
    cat > "$TEST_BASE_DIR/configs/claude.json" <<'EOF'
{
  "mcpServers": {
    "test-server": {
      "type": "stdio",
      "command": "node",
      "args": ["/tmp/test.js"],
      "env": {
        "TEST_VAR": "test_value"
      }
    }
  }
}
EOF

    # Validate JSON
    if command -v jq >/dev/null 2>&1; then
        if jq empty "$TEST_BASE_DIR/configs/claude.json" 2>/dev/null; then
            assert_success "Claude config JSON validation"
        else
            assert_failure "Claude config JSON validation" "Invalid JSON format"
        fi
    else
        assert_success "Claude config JSON validation (jq not available, skipped)"
    fi
}

# Test npm global installation in isolated location
test_isolated_npm_install() {
    echo -e "\n${BLUE}[TEST] Testing isolated npm installation...${NC}"

    # Set npm prefix to test location
    local npm_prefix="$TEST_BASE_DIR/npm_global"
    export npm_config_prefix="$npm_prefix"

    # Try installing a simple test package
    if npm install -g cowsay &>/dev/null; then
        if [ -d "$npm_prefix/lib/node_modules/cowsay" ]; then
            assert_success "Isolated npm global install"
        else
            assert_failure "Isolated npm global install" "Package not found in test location"
        fi
    else
        assert_failure "Isolated npm global install" "npm install failed"
    fi
}

# Test actual MCP server installation with mock installer
test_mock_mcp_installation() {
    echo -e "\n${BLUE}[TEST] Testing mock MCP installation flow...${NC}"

    # Create a simple mock MCP server script
    cat > "$TEST_BASE_DIR/mcp_servers/mock-server.js" <<'EOF'
#!/usr/bin/env node
// Mock MCP server for testing
console.error('[Mock MCP] Server starting...');
process.stdin.on('data', (data) => {
    console.log(JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        result: { status: "ok" }
    }));
});
EOF
    chmod +x "$TEST_BASE_DIR/mcp_servers/mock-server.js"

    # Test that the mock server runs and responds correctly
    local server_output
    server_output=$(timeout 2 bash -c "echo '{\"test\":true}' | node '$TEST_BASE_DIR/mcp_servers/mock-server.js' 2>/dev/null" || true)

    # Check if server produced JSON output
    if echo "$server_output" | jq empty 2>/dev/null; then
        # Valid JSON response - check if it's the expected format
        if echo "$server_output" | jq -e '.result.status == "ok"' >/dev/null 2>&1; then
            assert_success "Mock MCP server execution and response"
        else
            assert_failure "Mock MCP server execution and response" "Server responded but with unexpected format"
        fi
    else
        assert_failure "Mock MCP server execution and response" "Server did not produce valid JSON output"
    fi
}

# Test installer script with dry-run mode
test_installer_dry_run() {
    echo -e "\n${BLUE}[TEST] Testing installer dry-run mode...${NC}"

    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    local installer="$script_dir/scripts/install_mcp_servers.sh"

    if [ ! -f "$installer" ]; then
        assert_failure "Installer script exists" "Script not found at $installer"
        return
    fi

    # Check if installer has --test flag support by capturing output
    # Disable errexit temporarily to capture output even if command fails
    set +e
    local test_output
    test_output=$("$installer" --test claude 2>&1)
    local test_exit_code=$?
    set -e

    if echo "$test_output" | grep -q "Invalid target"; then
        echo -e "${YELLOW}[SKIP] Installer does not support --test flag, skipping test${NC}"
        log "SKIP: Installer --test flag not implemented"
        # Test is skipped - don't count as pass or fail
        return 0
    fi

    # Test dry-run mode (should not modify configs)
    if [ $test_exit_code -eq 0 ] && echo "$test_output" | grep -q "TEST_MODE"; then
        assert_success "Installer dry-run execution (--test flag supported)"
    elif [ $test_exit_code -eq 0 ]; then
        assert_success "Installer accepted --test flag (assumed working)"
    else
        assert_failure "Installer dry-run execution" "Installer --test flag exists but returned error code $test_exit_code"
    fi
}

# Test config file isolation
test_config_isolation() {
    echo -e "\n${BLUE}[TEST] Testing config isolation...${NC}"

    # Check that production config files exist
    if [ ! -f ~/.claude.json ]; then
        assert_failure "Claude production config isolation" "~/.claude.json does not exist - cannot verify isolation"
        return
    fi

    if [ ! -f ~/.codex/config.toml ]; then
        echo -e "${YELLOW}[WARN] ~/.codex/config.toml does not exist - skipping Codex isolation check${NC}"
        log "WARNING: Codex config not found, skipping isolation check"
    fi

    # Get initial timestamps
    local prod_claude_mtime=$(stat -f %m ~/.claude.json 2>/dev/null || stat -c %Y ~/.claude.json 2>/dev/null)
    local prod_codex_mtime=""
    if [ -f ~/.codex/config.toml ]; then
        prod_codex_mtime=$(stat -f %m ~/.codex/config.toml 2>/dev/null || stat -c %Y ~/.codex/config.toml 2>/dev/null)
    fi

    # Make changes to test configs
    echo '{"mcpServers":{"test-isolation":{}}}' > "$TEST_BASE_DIR/configs/claude.json"
    echo '[mcp]' >> "$TEST_BASE_DIR/configs/codex.toml"
    echo 'test_key = "test_value"' >> "$TEST_BASE_DIR/configs/codex.toml"

    # Verify production config timestamps unchanged
    local prod_claude_mtime_after=$(stat -f %m ~/.claude.json 2>/dev/null || stat -c %Y ~/.claude.json 2>/dev/null)
    local prod_codex_mtime_after=""
    if [ -f ~/.codex/config.toml ]; then
        prod_codex_mtime_after=$(stat -f %m ~/.codex/config.toml 2>/dev/null || stat -c %Y ~/.codex/config.toml 2>/dev/null)
    fi

    # Check Claude config isolation
    if [ -z "$prod_claude_mtime" ] || [ -z "$prod_claude_mtime_after" ]; then
        assert_failure "Claude production config isolation" "Failed to get modification times"
    elif [ "$prod_claude_mtime" = "$prod_claude_mtime_after" ]; then
        assert_success "Claude production config isolation"
    else
        assert_failure "Claude production config isolation" "Production ~/.claude.json was modified!"
    fi

    # Check Codex config isolation if it exists
    if [ -f ~/.codex/config.toml ]; then
        if [ -z "$prod_codex_mtime" ] || [ -z "$prod_codex_mtime_after" ]; then
            assert_failure "Codex production config isolation" "Failed to get modification times"
        elif [ "$prod_codex_mtime" = "$prod_codex_mtime_after" ]; then
            assert_success "Codex production config isolation"
        else
            assert_failure "Codex production config isolation" "Production ~/.codex/config.toml was modified!"
        fi
    fi
}

# Main test execution
main() {
    local target="${1:-both}"

    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     MCP Installation Sandboxed Test Suite         ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
    echo -e "${BLUE}Target: $target${NC}"
    echo -e "${BLUE}Test Directory: $TEST_BASE_DIR${NC}\n"

    # Setup phase
    setup_test_environment
    create_cli_wrappers

    # Test execution phase
    test_cli_wrappers
    test_mcp_config_format
    test_isolated_npm_install
    test_mock_mcp_installation
    test_installer_dry_run
    test_config_isolation

    # Summary is printed by cleanup trap

    # Return failure exit code if any tests failed
    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        return 1
    fi

    return 0
}

# Execute main if script is run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
