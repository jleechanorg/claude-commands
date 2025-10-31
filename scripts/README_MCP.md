# MCP Server Installation Scripts

**One-command setup for globally available MCP servers across all your projects.**

## 🚀 Quick Start

```bash
# Install for Claude (default)
./scripts/install_mcp_servers.sh

# Install for Codex
./scripts/install_mcp_servers.sh codex

# Install for both
./scripts/install_mcp_servers.sh both
```

## 📚 Documentation

- **[QUICK_START.md](./QUICK_START.md)** - 5-minute setup guide for new computers
- **[MCP_SETUP.md](./MCP_SETUP.md)** - Complete installation documentation
- **[MIGRATION.md](./MIGRATION.md)** - Migrating from old `claude_mcp.sh`/`codex_mcp.sh` launchers

## 📦 Files

| File | Purpose |
|------|---------|
| `install_mcp_servers.sh` | **Main installer** - Run this to install all MCP servers |
| `mcp_common.sh` | Shared installation logic (sourced by installer) |
| `QUICK_START.md` | Fast setup guide |
| `MCP_SETUP.md` | Detailed documentation |
| `MIGRATION.md` | Migration guide from old launchers |
| `README_MCP.md` | This file |

## 🎯 Key Features

- ✅ **Global Installation** - Servers available in all projects
- ✅ **User Scope Default** - No need to specify scope
- ✅ **Both Products** - Supports Claude and Codex
- ✅ **Auto-Detection** - Skips already-installed servers
- ✅ **Environment Loading** - Auto-loads API keys from `.bashrc`
- ✅ **Cross-Computer** - Copy 2 files, run 1 command

## 📋 What Gets Installed (15+ Servers)

**Core:** filesystem, serena, sequential-thinking, memory-server
**Search:** context7, ddg-search, perplexity-ask
**AI:** gemini-cli-mcp, grok
**Browser:** chrome-superpower, playwright-mcp, ios-simulator-mcp
**Cloud:** render, worldarchitect

## 💡 Common Use Cases

### New Computer Setup
```bash
git clone <repo-with-these-scripts>
cd <repo>
./scripts/install_mcp_servers.sh both
```

### Copy to New Repo
```bash
cp scripts/mcp_common.sh ~/new-repo/scripts/
cp scripts/install_mcp_servers.sh ~/new-repo/scripts/
cd ~/new-repo
./scripts/install_mcp_servers.sh
```

### Verify Installation
```bash
claude mcp list  # All should show ✓ Connected (User scope)
```

## 🔑 Required Environment Variables (Optional)

Some servers need API keys:

```bash
export XAI_API_KEY="your_key"           # grok
export PERPLEXITY_API_KEY="your_key"    # perplexity-ask
export RENDER_API_KEY="your_key"        # render
export GITHUB_TOKEN="your_token"        # GitHub MCP
```

Add to `~/.zshrc` or `~/.bashrc` for persistence.

## 📖 More Info

See [MCP_SETUP.md](./MCP_SETUP.md) for complete documentation.

---

**Note:** Old `claude_mcp.sh` and `codex_mcp.sh` launchers have been replaced by `install_mcp_servers.sh`. See [MIGRATION.md](./MIGRATION.md) for details.
