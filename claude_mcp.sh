#!/bin/bash
echo "🚀 Installing Top MCP Servers with User Scope (Absolute Paths)..."

# Get Node and NPX paths
NODE_PATH=$(which node)
NPX_PATH=$(which npx)
NPM_ROOT=$(npm root -g)

echo "📍 Node path: $NODE_PATH"
echo "📍 NPX path: $NPX_PATH"
echo "📍 Global npm modules path: $NPM_ROOT"

# Function to add MCP server with fallback
add_mcp_server() {
    local name="$1"
    local package="$2"
    shift 2
    local args="$@"
    
    echo "Setting up $name..."
    
    # Try absolute paths in order of preference
    if [ -f "$NPM_ROOT/$package/dist/index.js" ]; then
        echo "  ✅ Using global absolute path: $NODE_PATH $NPM_ROOT/$package/dist/index.js"
        claude mcp add --scope user "$name" "$NODE_PATH" "$NPM_ROOT/$package/dist/index.js" $args
    elif [ -f "node_modules/$package/dist/index.js" ]; then
        echo "  ✅ Using local absolute path: $NODE_PATH $(pwd)/node_modules/$package/dist/index.js"
        claude mcp add --scope user "$name" "$NODE_PATH" "$(pwd)/node_modules/$package/dist/index.js" $args
    else
        echo "  🔄 Falling back to npx: $NPX_PATH $package"
        claude mcp add --scope user "$name" "$NPX_PATH" "$package" $args
    fi
}

# Core Top 5 MCP Servers
echo "📊 Setting up GitHub MCP Server..."
add_mcp_server "github-server" "@modelcontextprotocol/server-github"

echo "📁 Setting up File System MCP Server..."
add_mcp_server "filesystem-server" "@modelcontextprotocol/server-filesystem" ~/Documents ~/Desktop ~/Downloads ~/Projects

echo "🧠 Setting up Sequential Thinking MCP Server..."
add_mcp_server "sequential-thinking" "@modelcontextprotocol/server-sequential-thinking"

echo "💾 Setting up Memory MCP Server..."
add_mcp_server "memory-server" "@modelcontextprotocol/server-memory"

echo "🌐 Setting up Puppeteer MCP Server..."
add_mcp_server "puppeteer-server" "@modelcontextprotocol/server-puppeteer"

# Additional Useful Servers
echo "🔍 Setting up Brave Search MCP Server..."
add_mcp_server "brave-search" "@modelcontextprotocol/server-brave-search"

echo "📝 Setting up Notion MCP Server (if available)..."
# Note: Package name might vary, trying common variants
if npm view @makenotion/notion-mcp-server > /dev/null 2>&1; then
    add_mcp_server "notion-server" "@makenotion/notion-mcp-server"
elif npm view @notionhq/notion-mcp-server > /dev/null 2>&1; then
    add_mcp_server "notion-server" "@notionhq/notion-mcp-server"
else
    echo "  ⚠️ Notion MCP server package not found, skipping..."
fi

# Verify installation
echo "✅ Verifying installation..."
claude mcp list

echo "🎉 All MCP servers installed successfully with user scope!"
