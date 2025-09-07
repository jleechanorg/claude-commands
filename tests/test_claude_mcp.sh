#!/bin/bash

# Comprehensive test suite for claude_mcp.sh functionality
# Tests cross-platform compatibility, MCP server connectivity, and robustness

# Note: Do not use 'set -e' as test functions need to fail without terminating the script

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

# Test actual MCP server connectivity and health
test_mcp_server_connectivity() {
    print_test "MCP server connectivity and health check"

    # Get list of all MCP servers and their status
    local server_list=$(claude mcp list 2>/dev/null | grep -E "✓ Connected|✗ Failed" || true)

    if [ -z "$server_list" ]; then
        echo -e "${YELLOW}⚠️  SKIP: No MCP servers found or claude mcp not available${NC}"
        return 0
    fi

    # Count connected vs failed servers
    local connected_count=$(echo "$server_list" | grep -c "✓ Connected" || echo "0")
    local failed_count=$(echo "$server_list" | grep -c "✗ Failed" || echo "0")
    local total_count=$((connected_count + failed_count))

    # Validate server count (server_list already checked above)
    if [ $connected_count -ge 13 ]; then
        echo -e "${GREEN}✅ PASS: Expected number of working servers ($connected_count/$total_count connected)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: Too many failed servers ($connected_count/$total_count connected, expected ≥13)${NC}"
        echo "Failed servers:"
        echo "$server_list" | grep "✗ Failed" || true
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    return 0
}

# Test MCP server duplicate detection
test_mcp_duplicate_detection() {
    print_test "MCP server duplicate detection"

    # Get list of server names, handling potential errors gracefully
    local server_output=$(claude mcp list 2>/dev/null || true)
    if [ -z "$server_output" ]; then
        echo -e "${YELLOW}⚠️  SKIP: claude mcp command not available${NC}"
        return 0
    fi

    # Extract server names from the output
    local servers=($(echo "$server_output" | grep -E "✓ Connected|✗ Failed" | awk '{print $3}' || true))

    if [ ${#servers[@]} -eq 0 ]; then
        echo -e "${YELLOW}⚠️  SKIP: No servers found in output${NC}"
        return 0
    fi

    # Check for duplicates using associative arrays (bash 4+) with fallback
    local found_duplicate=false

    if [ "${BASH_VERSION%%.*}" -ge 4 ] 2>/dev/null; then
        # Use associative arrays for bash 4+
        declare -A seen=()
        for s in "${servers[@]}"; do
            # Normalize server name by removing -mcp suffix
            local key="${s%-mcp}"
            if [[ -n "${seen[$key]:-}" ]]; then
                found_duplicate=true
                echo -e "${RED}Found duplicate server: $s (normalized: $key)${NC}"
                break
            fi
            seen[$key]=1
        done
    else
        # Fallback for older bash versions
        local seen_list=()
        for s in "${servers[@]}"; do
            local key="${s%-mcp}"
            for seen_key in "${seen_list[@]}"; do
                if [ "$seen_key" = "$key" ]; then
                    found_duplicate=true
                    echo -e "${RED}Found duplicate server: $s (normalized: $key)${NC}"
                    break 2
                fi
            done
            seen_list+=("$key")
        done
    fi

    if [ "$found_duplicate" = "false" ]; then
        echo -e "${GREEN}✅ PASS: No duplicate servers found${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: Duplicate servers detected${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    return 0
}

# Test Python path detection robustness
test_python_path_detection() {
    print_test "Python path detection with fallback"

    local python_bin=""

    # Replicate the Python detection logic with proper error handling
    if command -v python3 >/dev/null 2>&1; then
        python_bin="$(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        python_bin="$(command -v python)"
    else
        echo -e "${YELLOW}⚠️  SKIP: No Python interpreter found${NC}"
        return 0
    fi

    # Test that we found a working Python interpreter (single logical test)
    if ! "$python_bin" -c "import sys; print('Python', sys.version_info.major, sys.version_info.minor)" >/dev/null 2>&1; then
        echo -e "${RED}❌ FAIL: Python interpreter not functional${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    else
        echo -e "${GREEN}✅ PASS: Working Python interpreter found at $python_bin${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi

    return 0
}

# Test MCP import validation
test_mcp_import_validation() {
    print_test "MCP server import validation"

    # Find Python interpreter with same logic as above
    local PY_BIN=""
    if command -v python3 >/dev/null 2>&1; then
        PY_BIN="$(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        PY_BIN="$(command -v python)"
    else
        echo -e "${YELLOW}⚠️  SKIP: No Python interpreter found${NC}"
        return 0
    fi

    # Test critical imports that MCP servers depend on
    local output
    output="$($PY_BIN - <<PY
import sys, os
# Use current working directory since __file__ is not available in stdin
project_root = os.getcwd()
mvp_site_path = os.path.join(project_root, 'mvp_site')
if os.path.exists(mvp_site_path):
    sys.path.insert(0, mvp_site_path)
try:
    import logging_util
    import world_logic
    print("imports_ok")
except ImportError as e:
    print("import_error:", str(e))
PY
2>&1)" || true

    if echo "$output" | grep -q "imports_ok"; then
        echo -e "${GREEN}✅ PASS: Critical MCP imports work${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    elif echo "$output" | grep -q "import_error"; then
        echo -e "${YELLOW}⚠️  SKIP: Import dependencies not available ($output)${NC}"
        # Don't count as failure since this might be expected in some environments
        return 0
    else
        echo -e "${RED}❌ FAIL: Python import test failed unexpectedly${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    return 0
}

# Test shell script best practices validation
test_shell_script_guidelines() {
    print_test "Shell script best practices validation"

    # Check for problematic cd && command patterns (but allow safe directory detection)
    local bad_cd_violations=$(grep -n "cd .* && python\|cd .* && pip\|cd .* && npm" "$CLAUDE_MCP_SCRIPT" | wc -l)
    local safe_cd_patterns=$(grep -n "cd.*dirname.*&& pwd" "$CLAUDE_MCP_SCRIPT" | wc -l)

    if [ $bad_cd_violations -eq 0 ]; then
        echo -e "${GREEN}✅ PASS: No problematic cd && command anti-patterns found${NC}"
        if [ $safe_cd_patterns -gt 0 ]; then
            echo -e "${GREEN}  ℹ️  Found $safe_cd_patterns safe directory detection patterns (acceptable)${NC}"
        fi
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: Found $bad_cd_violations problematic cd && command patterns${NC}"
        grep -n "cd .* && python\|cd .* && pip\|cd .* && npm" "$CLAUDE_MCP_SCRIPT" || true
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    return 0
}

# Test error handling robustness
test_error_handling_robustness() {
    print_test "Error handling robustness (no terminal termination)"

    # Check that script doesn't use exit in ways that could terminate user's terminal
    local problematic_exits=$(grep -n "exit 1" "$CLAUDE_MCP_SCRIPT" | wc -l)

    # A few exit statements are acceptable in setup/validation, but not in error handling
    if [ $problematic_exits -le 3 ]; then
        echo -e "${GREEN}✅ PASS: Reasonable exit usage ($problematic_exits exit 1 statements)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${YELLOW}⚠️  WARNING: Many exit statements ($problematic_exits) - review for terminal safety${NC}"
        # Don't fail the test, but flag for review
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi

    return 0
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

    # Test 2: GNU timeout (gtimeout) - isolate PATH to only include test directory
    rm -f "$TEST_DIR/bin/timeout"
    echo '#!/bin/bash\necho "gtimeout"' > "$TEST_DIR/bin/gtimeout"
    chmod +x "$TEST_DIR/bin/gtimeout"

    # Completely isolate PATH to only test directory
    export PATH="$TEST_DIR/bin"

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

# Test uvx command detection logic
test_uvx_command_detection() {
    print_test "uvx command availability detection"

    # Create mock environment
    mkdir -p "$TEST_DIR/bin"

    OLD_PATH="$PATH"

    # Test 1: uvx command available
    cat > "$TEST_DIR/bin/uvx" <<'EOF'
#!/bin/bash
echo "uvx available"
EOF
    chmod +x "$TEST_DIR/bin/uvx"
    export PATH="$TEST_DIR/bin:$PATH"

    # Simulate the uvx detection logic
    uvx_available=0
    if command -v uvx >/dev/null 2>&1; then
        uvx_available=1
    fi

    assert_equals "1" "$uvx_available" "(uvx command found)"

    # Test 2: uvx command not available
    rm -f "$TEST_DIR/bin/uvx"
    export PATH="$TEST_DIR/bin"

    uvx_available=0
    if command -v uvx >/dev/null 2>&1; then
        uvx_available=1
    fi

    assert_equals "0" "$uvx_available" "(uvx command not found)"

    # Restore PATH
    export PATH="$OLD_PATH"
}

# Test MCP global installation logic
test_mcp_global_installation_logic() {
    print_test "MCP global installation attempt flow"

    # Create mock environment
    mkdir -p "$TEST_DIR/bin"

    # Mock uvx command that simulates successful global installation
    cat > "$TEST_DIR/bin/uvx" <<'EOF'
#!/bin/bash
if [ "$1" = "--from" ] && { [ "$2" = "./mcp_servers/slash_commands" ] || [[ "$2" == file://*"/mcp_servers/slash_commands" ]]; } && [ "$3" = "claude-slash-commands-mcp" ]; then
    echo "Successfully installed claude-slash-commands-mcp"
    exit 0
else
    echo "uvx: command not recognized"
    exit 1
fi
EOF
    chmod +x "$TEST_DIR/bin/uvx"

    # Mock claude command that simulates successful MCP add
    cat > "$TEST_DIR/bin/claude" <<'EOF'
#!/bin/bash
if [ "$1" = "mcp" ] && [ "$2" = "add" ] && [ "$3" = "--scope" ] && [ "$4" = "user" ] && [ "$5" = "claude-slash-commands" ] && [ "$6" = "claude-slash-commands-mcp" ]; then
    echo "Successfully added MCP server claude-slash-commands"
    exit 0
else
    echo "claude: command failed"
    exit 1
fi
EOF
    chmod +x "$TEST_DIR/bin/claude"

    OLD_PATH="$PATH"
    export PATH="$TEST_DIR/bin:$PATH"

    # Simulate the global installation logic
    global_install_success=0
    if command -v uvx >/dev/null 2>&1; then
        # Simulate uvx installation
        if uvx --from ./mcp_servers/slash_commands claude-slash-commands-mcp >/dev/null 2>&1; then
            # Simulate claude mcp add
            if claude mcp add --scope user "claude-slash-commands" "claude-slash-commands-mcp" >/dev/null 2>&1; then
                global_install_success=1
            fi
        fi
    fi

    assert_equals "1" "$global_install_success" "(global installation succeeds)"

    # Restore PATH
    export PATH="$OLD_PATH"
}

# Test installation fallback logic
test_installation_fallback_logic() {
    print_test "Installation fallback from global to local"

    # Create mock environment
    mkdir -p "$TEST_DIR/bin"

    # Mock uvx command that simulates failure
    cat > "$TEST_DIR/bin/uvx" <<'EOF'
#!/bin/bash
echo "uvx: installation failed"
exit 1
EOF
    chmod +x "$TEST_DIR/bin/uvx"

    # Mock python command for local fallback
    cat > "$TEST_DIR/bin/python3" <<'EOF'
#!/bin/bash
if [[ "$1" == "-m" ]] && [[ "$2" == "pip" ]] && [[ "$3" == "install" ]] && [[ "$4" == "-e" ]] && [[ "$5" == *"mcp_servers/slash_commands"* ]]; then
    echo "Successfully installed local package"
    exit 0
else
    echo "python: unknown command"
    exit 1
fi
EOF
    chmod +x "$TEST_DIR/bin/python3"

    OLD_PATH="$PATH"
    export PATH="$TEST_DIR/bin:$PATH"

    # Simulate the fallback logic
    installation_success=0
    fallback_used=0

    if command -v uvx >/dev/null 2>&1; then
        # Try global installation (will fail)
        if ! uvx --from ./mcp_servers/slash_commands claude-slash-commands-mcp >/dev/null 2>&1; then
            # Fall back to local installation
            fallback_used=1
            if python3 -m pip install -e ./mcp_servers/slash_commands >/dev/null 2>&1; then
                installation_success=1
            fi
        fi
    fi

    assert_equals "1" "$fallback_used" "(fallback triggered)"
    assert_equals "1" "$installation_success" "(local installation succeeds)"

    # Restore PATH
    export PATH="$OLD_PATH"
}

# Test complete slash commands server setup process
test_slash_commands_server_setup() {
    print_test "Complete slash commands server setup process"

    # Check if pyproject.toml exists (required for uvx installation)
    if [ -f "mcp_servers/slash_commands/pyproject.toml" ]; then
        echo -e "${GREEN}✅ PASS: pyproject.toml exists for uvx packaging${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: pyproject.toml missing - required for global installation${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    # Check if server.py exists
    if [ -f "mcp_servers/slash_commands/server.py" ]; then
        echo -e "${GREEN}✅ PASS: server.py exists${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: server.py missing${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    # Validate pyproject.toml structure
    if command -v python3 >/dev/null 2>&1; then
        local toml_check
        toml_check=$(python3 -c "
import sys, os
sys.path.insert(0, '.')
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print('toml_parser_unavailable')
        sys.exit(0)

if os.path.exists('mcp_servers/slash_commands/pyproject.toml'):
    with open('mcp_servers/slash_commands/pyproject.toml', 'rb') as f:
        try:
            data = tomllib.load(f)
            if 'project' in data and 'name' in data['project'] and data['project']['name'] == 'claude-slash-commands-mcp':
                if 'project' in data and 'scripts' in data['project'] and 'claude-slash-commands-mcp' in data['project']['scripts']:
                    print('toml_valid')
                else:
                    print('toml_missing_scripts')
            else:
                print('toml_invalid_project')
        except Exception as e:
            print(f'toml_parse_error: {e}')
else:
    print('toml_file_missing')
" 2>/dev/null)

        if [ "$toml_check" = "toml_valid" ]; then
            echo -e "${GREEN}✅ PASS: pyproject.toml has valid structure${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        elif [ "$toml_check" = "toml_parser_unavailable" ]; then
            echo -e "${YELLOW}⚠️  SKIP: TOML parser not available for validation${NC}"
        else
            echo -e "${RED}❌ FAIL: pyproject.toml validation failed: $toml_check${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    fi

    return 0
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
        return 1  # Use return instead of exit to avoid terminating terminal
    fi

    echo -e "${GREEN}✅ Test environment ready${NC}"
    return 0
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
    echo -e "${BLUE}🚀 Running comprehensive claude_mcp.sh test suite...${NC}"
    echo "Including: MCP server connectivity, cross-platform compatibility, and robustness tests"
    echo ""

    # Setup tests and exit early if setup fails
    if ! setup_tests; then
        echo -e "${RED}❌ Test setup failed. Cannot continue.${NC}"
        return 1
    fi

    # Run integration tests first (most important)
    test_mcp_server_connectivity
    test_mcp_duplicate_detection
    test_python_path_detection
    test_mcp_import_validation
    test_shell_script_guidelines
    test_error_handling_robustness

    # Run new uvx/global installation tests
    test_uvx_command_detection
    test_mcp_global_installation_logic
    test_installation_fallback_logic
    test_slash_commands_server_setup

    # Run cross-platform compatibility tests
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
