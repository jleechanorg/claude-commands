# MCP Server Installation Guide

## 🌍 Global Installation (Recommended)

Install all MCP servers globally so they're available in **every project**.

### On Your Current Computer

```bash
# For Claude (default)
./scripts/install_mcp_servers.sh

# For Codex
./scripts/install_mcp_servers.sh codex

# For both Claude and Codex
./scripts/install_mcp_servers.sh both
```

### On a New Computer

1. **Clone any repo with mcp_common.sh**:
   ```bash
   git clone <your-repo>
   cd <your-repo>
   ```

2. **Run the installer**:
   ```bash
   # For Claude (default)
   ./scripts/install_mcp_servers.sh

   # Or for both Claude and Codex
   ./scripts/install_mcp_servers.sh both
   ```

3. **Done!** All 15+ MCP servers now available globally.

## 📦 What Gets Installed

### Core Infrastructure
- **filesystem** - File system operations
- **serena** - Semantic code search and editing
- **sequential-thinking** - Enhanced reasoning
- **memory-server** - Persistent memory across sessions

### Documentation & Search
- **context7** - Up-to-date library documentation
- **ddg-search** - DuckDuckGo search (free)
- **perplexity-ask** - Perplexity AI search (premium)

### AI Models
- **gemini-cli-mcp** - Google Gemini integration
- **grok** - xAI Grok integration (requires API key)

### Browser Automation
- **chrome-superpower** - Chrome browser control
- **playwright-mcp** - Playwright automation
- **ios-simulator-mcp** - iOS simulator control

### Cloud Services
- **render** - Render.com deployment
- **worldarchitect** - WorldArchitect.AI backend

## 🔧 Advanced Usage

### Install for Specific Product

```bash
# Claude only (default)
./scripts/install_mcp_servers.sh claude

# Codex only
./scripts/install_mcp_servers.sh codex

# Both Claude and Codex
./scripts/install_mcp_servers.sh both
```

### Install to Specific Scope (Advanced)

The new installer **always uses user scope** for global availability. For advanced use cases:

```bash
# User scope (global - default)
MCP_SCOPE=user ./scripts/install_mcp_servers.sh

# Local scope (project-only - not recommended)
MCP_SCOPE=local ./scripts/install_mcp_servers.sh

# Dual scope (both user and local)
MCP_INSTALL_DUAL_SCOPE=true ./scripts/install_mcp_servers.sh
```

### Verify Installation

```bash
# For Claude
claude mcp list

# For Codex
codex mcp list
```

All servers should show `✓ Connected` and `Scope: User config (available in all your projects)`

### Copy to New Repo

```bash
# Copy the installer scripts
cp scripts/mcp_common.sh ~/new-repo/scripts/
cp scripts/install_mcp_servers.sh ~/new-repo/scripts/

# In new repo
cd ~/new-repo
./scripts/install_mcp_servers.sh
```

## 🔑 Required API Keys

Some servers require API keys (set as environment variables):

```bash
export XAI_API_KEY="your_grok_key"           # For grok
export PERPLEXITY_API_KEY="your_key"         # For perplexity-ask
export RENDER_API_KEY="your_key"             # For render
export GITHUB_TOKEN="your_token"             # For GitHub MCP
```

Add these to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
echo 'export XAI_API_KEY="your_key"' >> ~/.zshrc
source ~/.zshrc
```

## 🐛 Troubleshooting

### Server Failed to Connect

```bash
# Check server status
claude mcp get <server-name>

# Remove and reinstall
claude mcp remove <server-name> -s user
./scripts/install_mcp_servers.sh
```

### Chrome Superpowers Not Found

Chrome Superpowers requires the Claude Code plugin:
1. Install via Claude Code settings
2. Plugin installs to `~/.claude/plugins/cache/superpowers-chrome/`
3. Rerun installer

### Check Logs

```bash
# View installation logs
ls /tmp/claude_mcp*.log

# View latest log
tail -f /tmp/claude_mcp_$(date +%Y%m%d)_*.log
```

## 📝 File Structure

```
scripts/
├── mcp_common.sh              # Shared installation logic
├── install_mcp_servers.sh     # User scope installer (run this!)
└── MCP_SETUP.md              # This file
```

## 🔄 Updating Servers

Servers installed via npm (most of them) auto-update when you reinstall:

```bash
./scripts/install_mcp_servers.sh
```

The script detects existing servers and skips or updates as needed.
