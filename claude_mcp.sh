#!/bin/bash
echo "🚀 Installing MCP Servers with Enhanced Reliability..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Set up logging
LOG_FILE="/tmp/claude_mcp_$(date +%Y%m%d_%H%M%S).log"
echo "📝 Logging to: $LOG_FILE"

# Function to log with timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to log errors with details
log_error_details() {
    local operation="$1"
    local package="$2"
    local error_output="$3"
    
    log_with_timestamp "ERROR: $operation failed for $package"
    log_with_timestamp "Error details: $error_output"
    echo "Error details: $error_output" >> "$LOG_FILE"
}

# Get Node and NPX paths
NODE_PATH=$(which node)
NPX_PATH=$(which npx)

if [ -z "$NODE_PATH" ] || [ -z "$NPX_PATH" ]; then
    echo -e "${RED}❌ Node.js or NPX not found. Please install Node.js first.${NC}"
    exit 1
fi

echo -e "${BLUE}📍 Node path: $NODE_PATH${NC}"
echo -e "${BLUE}📍 NPX path: $NPX_PATH${NC}"

# Check Node.js version and warn about compatibility
NODE_VERSION=$(node --version)
echo -e "${BLUE}📍 Node version: $NODE_VERSION${NC}"
log_with_timestamp "Node.js version: $NODE_VERSION"

# Check for major version compatibility
NODE_MAJOR=$(echo "$NODE_VERSION" | sed 's/v\([0-9]*\).*/\1/')
if [ "$NODE_MAJOR" -lt 20 ]; then
    echo -e "${YELLOW}⚠️ WARNING: Node.js $NODE_VERSION detected. MCP servers recommend Node 20+${NC}"
    echo -e "${YELLOW}   Some packages may show engine warnings but should still work${NC}"
    log_with_timestamp "WARNING: Node.js version $NODE_VERSION is below recommended v20+"
else
    echo -e "${GREEN}✅ Node.js version compatible with MCP servers${NC}"
fi

# Check npm permissions and suggest alternatives
echo -e "${BLUE}🔍 Checking npm global installation permissions...${NC}"
if npm list -g --depth=0 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ NPM global permissions look good${NC}"
    USE_GLOBAL=true
else
    echo -e "${YELLOW}⚠️ Global npm permissions may be restricted${NC}"
    echo -e "${YELLOW}   Will use npx direct installation method${NC}"
    USE_GLOBAL=false
fi

# Track installation results
declare -A INSTALL_RESULTS
TOTAL_SERVERS=0
SUCCESSFUL_INSTALLS=0
FAILED_INSTALLS=0

# Function to check if npm package exists
package_exists() {
    local package="$1"
    npm view "$package" version >/dev/null 2>&1
}

# Function to install npm package with permission-aware method
install_package() {
    local package="$1"
    log_with_timestamp "Attempting to install package: $package"

    if [ "$USE_GLOBAL" = true ]; then
        echo -e "${BLUE}  📦 Installing $package globally...${NC}"
        # Capture detailed error output
        local install_output
        install_output=$(npm install -g "$package" 2>&1)
        local exit_code=$?

        if [ $exit_code -eq 0 ]; then
            echo -e "${GREEN}  ✅ Package $package installed globally${NC}"
            log_with_timestamp "SUCCESS: Package $package installed globally"
            return 0
        else
            echo -e "${YELLOW}  ⚠️ Global installation failed, trying alternative methods...${NC}"
            log_error_details "npm install -g" "$package" "$install_output"
            
            # Check if it's a permission error
            if echo "$install_output" | grep -q "EACCES\|permission denied"; then
                echo -e "${YELLOW}  🔧 Permission issue detected - switching to npx-only mode${NC}"
                log_with_timestamp "Permission error detected, using npx-only approach"
                USE_GLOBAL=false
                return 0  # Continue with npx approach
            else
                echo -e "${RED}  📋 Install error: $install_output${NC}"
                return 1
            fi
        fi
    else
        echo -e "${BLUE}  📦 Using npx direct execution (no global install needed)${NC}"
        log_with_timestamp "Using npx direct execution for $package"
        return 0
    fi
}

# Function to test if MCP server works
test_mcp_server() {
    local name="$1"
    echo -e "${BLUE}  🧪 Testing server $name...${NC}"
    
    # Try to get server info (this will fail if server can't start)
    if timeout 5s claude mcp list | grep -q "^$name:"; then
        echo -e "${GREEN}  ✅ Server $name is responding${NC}"
        return 0
    else
        echo -e "${YELLOW}  ⚠️ Server $name added but may need configuration${NC}"
        return 1
    fi
}

# Function to cleanup failed server installation
cleanup_failed_server() {
    local name="$1"
    echo -e "${YELLOW}  🧹 Cleaning up failed installation of $name...${NC}"
    claude mcp remove "$name" >/dev/null 2>&1 || true
}

# Enhanced function to add MCP server with full error checking
add_mcp_server() {
    local name="$1"
    local package="$2"
    shift 2
    local args="$@"
    
    TOTAL_SERVERS=$((TOTAL_SERVERS + 1))
    echo -e "${BLUE}🔧 Setting up $name...${NC}"
    log_with_timestamp "Setting up MCP server: $name (package: $package)"
    
    # Check if server already exists
    if server_already_exists "$name"; then
        echo -e "${GREEN}  ✅ Server $name already exists, skipping installation${NC}"
        log_with_timestamp "Server $name already exists, skipping"
        INSTALL_RESULTS["$name"]="ALREADY_EXISTS"
        SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
        return 0
    fi
    
    # Check if package exists in npm registry
    echo -e "${BLUE}  🔍 Checking if package $package exists in npm registry...${NC}"
    local registry_check
    registry_check=$(npm view "$package" version 2>&1)
    local registry_exit_code=$?
    
    if [ $registry_exit_code -ne 0 ]; then
        echo -e "${RED}  ❌ Package $package not found in npm registry${NC}"
        log_error_details "npm view" "$package" "$registry_check"
        INSTALL_RESULTS["$name"]="PACKAGE_NOT_FOUND"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        return 1
    else
        echo -e "${GREEN}  ✅ Package $package exists (version: $(echo "$registry_check" | head -1))${NC}"
        log_with_timestamp "Package $package exists in registry"
    fi
    
    # Check if package is installed globally (only if using global mode)
    if [ "$USE_GLOBAL" = true ]; then
        echo -e "${BLUE}  🔍 Checking global npm installation...${NC}"
        local global_check
        global_check=$(npm list -g "$package" 2>&1)
        local global_exit_code=$?
        
        if [ $global_exit_code -ne 0 ]; then
            echo -e "${YELLOW}  📦 Package $package not installed globally, installing...${NC}"
            log_with_timestamp "Package $package not installed globally, attempting installation"
            if ! install_package "$package"; then
                # If global install failed due to permissions, continue with npx
                if [ "$USE_GLOBAL" = false ]; then
                    echo -e "${BLUE}  🔄 Continuing with npx direct execution${NC}"
                else
                    INSTALL_RESULTS["$name"]="INSTALL_FAILED"
                    FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
                    return 1
                fi
            fi
        else
            echo -e "${GREEN}  ✅ Package $package already installed globally${NC}"
            log_with_timestamp "Package $package already installed globally"
            echo "Global package check: $global_check" >> "$LOG_FILE"
        fi
    else
        echo -e "${BLUE}  🔄 Using npx direct execution - no global installation required${NC}"
        log_with_timestamp "Using npx direct execution for $package"
    fi
    
    # Remove existing server if present
    claude mcp remove "$name" >/dev/null 2>&1 || true
    
    # Add server with error checking
    echo -e "${BLUE}  🔗 Adding MCP server $name...${NC}"
    log_with_timestamp "Attempting to add MCP server: $name"
    
    # Capture detailed error output from claude mcp add
    local add_output
    add_output=$(claude mcp add --scope user "$name" "$NPX_PATH" "$package" $args 2>&1)
    local add_exit_code=$?
    
    if [ $add_exit_code -eq 0 ]; then
        echo -e "${GREEN}  ✅ Successfully added $name${NC}"
        log_with_timestamp "Successfully added MCP server: $name"
        
        # Test if server actually works
        sleep 1  # Give server time to initialize
        if test_mcp_server "$name"; then
            INSTALL_RESULTS["$name"]="SUCCESS"
            SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
        else
            INSTALL_RESULTS["$name"]="NEEDS_CONFIG"
            SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))  # Still count as success
        fi
    else
        echo -e "${RED}  ❌ Failed to add $name to Claude MCP${NC}"
        log_error_details "claude mcp add" "$name" "$add_output"
        echo -e "${RED}  📋 Add error: $add_output${NC}"
        cleanup_failed_server "$name"
        INSTALL_RESULTS["$name"]="ADD_FAILED"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        return 1
    fi
}

# Function to check environment requirements
check_github_requirements() {
    if [ -z "$GITHUB_TOKEN" ]; then
        echo -e "${YELLOW}⚠️ GitHub MCP server works better with GITHUB_TOKEN environment variable${NC}"
        echo -e "${YELLOW}   You can set it with: export GITHUB_TOKEN=your_github_token${NC}"
        echo -e "${YELLOW}   Server will still work for public repositories without it${NC}"
    else
        echo -e "${GREEN}✅ GITHUB_TOKEN found - GitHub server will have full access${NC}"
    fi
}

# Check existing MCP installations first
echo -e "${BLUE}🔍 Checking existing MCP installations...${NC}"
log_with_timestamp "Checking existing MCP servers"

EXISTING_SERVERS=""
if EXISTING_SERVERS=$(claude mcp list 2>&1); then
    EXISTING_COUNT=$(echo "$EXISTING_SERVERS" | grep -E "^[a-zA-Z].*:" | wc -l)
    echo -e "${GREEN}✅ Found $EXISTING_COUNT existing MCP servers${NC}"
    log_with_timestamp "Found $EXISTING_COUNT existing MCP servers"
    
    if [ "$EXISTING_COUNT" -gt 0 ]; then
        echo -e "${BLUE}📋 Currently installed servers:${NC}"
        echo "$EXISTING_SERVERS" | head -10
        echo "$EXISTING_SERVERS" >> "$LOG_FILE"
    fi
else
    echo -e "${YELLOW}⚠️ Could not get MCP server list: $EXISTING_SERVERS${NC}"
    log_error_details "claude mcp list" "N/A" "$EXISTING_SERVERS"
fi
echo ""

# Function to check if MCP server already exists
server_already_exists() {
    local name="$1"
    echo "$EXISTING_SERVERS" | grep -q "^$name:"
}

# Check environment requirements
echo -e "${BLUE}🔍 Checking environment requirements...${NC}"
check_github_requirements
echo ""

# Core MCP Servers Installation
echo -e "${BLUE}📊 Installing Core MCP Servers...${NC}"

echo -e "\n${BLUE}1/6 Setting up GitHub MCP Server...${NC}"
add_mcp_server "github-server" "@modelcontextprotocol/server-github"

echo -e "\n${BLUE}2/6 Setting up File System MCP Server...${NC}"
add_mcp_server "filesystem-server" "@modelcontextprotocol/server-filesystem" ~/Documents ~/Desktop ~/Downloads ~/Projects

echo -e "\n${BLUE}3/6 Setting up Sequential Thinking MCP Server...${NC}"
add_mcp_server "sequential-thinking" "@modelcontextprotocol/server-sequential-thinking"

echo -e "\n${BLUE}4/6 Setting up Memory MCP Server...${NC}"
add_mcp_server "memory-server" "@modelcontextprotocol/server-memory"

echo -e "\n${BLUE}5/6 Setting up Puppeteer MCP Server...${NC}"
add_mcp_server "puppeteer-server" "@modelcontextprotocol/server-puppeteer"

echo -e "\n${BLUE}6/6 Setting up Brave Search MCP Server...${NC}"
add_mcp_server "brave-search" "@modelcontextprotocol/server-brave-search"

# Optional: Notion Server (if available)
echo -e "\n${BLUE}📝 Checking for Notion MCP Server...${NC}"
if package_exists "@notionhq/notion-mcp-server"; then
    add_mcp_server "notion-server" "@notionhq/notion-mcp-server"
elif package_exists "@makenotion/notion-mcp-server"; then
    add_mcp_server "notion-server" "@makenotion/notion-mcp-server"
else
    echo -e "${YELLOW}  ⚠️ Notion MCP server package not found, skipping...${NC}"
fi

# Final verification and results
echo -e "\n${BLUE}✅ Verifying final installation...${NC}"
MCP_LIST=$(claude mcp list 2>/dev/null)
ACTUAL_SERVERS=$(echo "$MCP_LIST" | grep -E "^[a-zA-Z].*:" | wc -l)

echo -e "\n${GREEN}📋 Installation Results Summary:${NC}"
echo -e "${GREEN}=================================${NC}"
echo -e "${BLUE}Total servers attempted: $TOTAL_SERVERS${NC}"
echo -e "${GREEN}Successful installations: $SUCCESSFUL_INSTALLS${NC}"
echo -e "${RED}Failed installations: $FAILED_INSTALLS${NC}"
echo -e "${BLUE}Currently active servers: $ACTUAL_SERVERS${NC}"

echo -e "\n${BLUE}📊 Detailed Results:${NC}"
for server in "${!INSTALL_RESULTS[@]}"; do
    result="${INSTALL_RESULTS[$server]}"
    case "$result" in
        "SUCCESS")
            echo -e "${GREEN}  ✅ $server: Installed and working${NC}"
            ;;
        "NEEDS_CONFIG")
            echo -e "${YELLOW}  ⚠️ $server: Installed but may need configuration${NC}"
            ;;
        "ALREADY_EXISTS")
            echo -e "${BLUE}  ℹ️ $server: Already existed, skipped installation${NC}"
            ;;
        "PACKAGE_NOT_FOUND")
            echo -e "${RED}  ❌ $server: Package not found in npm registry${NC}"
            ;;
        "INSTALL_FAILED")
            echo -e "${RED}  ❌ $server: Failed to install npm package${NC}"
            ;;
        "ADD_FAILED")
            echo -e "${RED}  ❌ $server: Failed to add to Claude MCP${NC}"
            ;;
    esac
done

echo -e "\n${BLUE}🔍 Current MCP Server List:${NC}"
echo "$MCP_LIST"

# Final logging summary
log_with_timestamp "Installation completed: $SUCCESSFUL_INSTALLS successful, $FAILED_INSTALLS failed"
echo -e "\n${BLUE}📝 Detailed log saved to: $LOG_FILE${NC}"
echo -e "${BLUE}💡 To view log: cat $LOG_FILE${NC}"

if [ "$SUCCESSFUL_INSTALLS" -gt 0 ]; then
    echo -e "\n${GREEN}🎉 MCP servers installed successfully!${NC}"
    if [ "$FAILED_INSTALLS" -gt 0 ]; then
        echo -e "${YELLOW}⚠️ Some servers failed to install. Check the detailed results above or log file.${NC}"
        echo -e "${YELLOW}💡 Log file: $LOG_FILE${NC}"
    fi
    exit 0
else
    echo -e "\n${RED}❌ No servers were successfully installed. Please check the errors above.${NC}"
    echo -e "${RED}💡 Check the detailed log: $LOG_FILE${NC}"
    exit 1
fi