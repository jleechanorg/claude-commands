#!/bin/bash
echo "🚀 Installing Top MCP Servers with User Scope..."

# Core Top 5 MCP Servers
echo "📊 Setting up GitHub MCP Server..."
claude mcp add --scope user github-server npx @modelcontextprotocol/server-github

echo "📁 Setting up File System MCP Server..."
claude mcp add --scope user filesystem-server npx @modelcontextprotocol/server-filesystem ~/Documents ~/Desktop ~/Downloads ~/Projects

echo "🧠 Setting up Sequential Thinking MCP Server..."
claude mcp add --scope user sequential-thinking npx @modelcontextprotocol/server-sequential-thinking

echo "💾 Setting up Memory MCP Server..."
claude mcp add --scope user memory-server npx @modelcontextprotocol/server-memory

echo "🌐 Setting up Puppeteer MCP Server..."
claude mcp add --scope user puppeteer-server npx @modelcontextprotocol/server-puppeteer

# Additional Useful Servers
echo "🔍 Setting up Brave Search MCP Server..."
claude mcp add --scope user brave-search npx @modelcontextprotocol/server-brave-search

echo "📝 Setting up Notion MCP Server..."
claude mcp add --scope user notion-server npx @makenotion/notion-mcp-server

# Verify installation
echo "✅ Verifying installation..."
claude mcp list

echo "🎉 All MCP servers installed successfully with user scope!"
