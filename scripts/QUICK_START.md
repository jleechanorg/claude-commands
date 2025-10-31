# MCP Quick Start - New Computer Setup

## 🚀 One Command Setup

```bash
# Clone any repo with the scripts
git clone <your-repo>
cd <your-repo>

# Install ALL MCP servers globally for Claude (default)
./scripts/install_mcp_servers.sh

# Or install for both Claude and Codex
./scripts/install_mcp_servers.sh both
```

**That's it!** All 15+ servers now available in every project.

---

## 🤔 How Global Availability Works

### User Scope vs Local Scope

**User Scope** (`-s user`):
```
~/.claude.json
└── mcpServers:
    ├── filesystem ✓
    ├── serena ✓
    ├── chrome-superpower ✓
    └── ... (available in ALL projects)
```

**Local Scope** (`-s local`):
```
/project1/.claude.json
└── mcpServers:
    └── custom-server ✓ (only in project1)

/project2/.claude.json
└── mcpServers:
    └── different-server ✓ (only in project2)
```

### Key Difference

| Scope | Storage | Availability |
|-------|---------|-------------|
| **User** | `~/.claude.json` | **ALL projects** |
| **Local** | `<project>/.claude.json` | **Single project** |

When Claude Code starts:
1. Loads servers from `~/.claude.json` (user scope) ✅
2. Loads servers from `<project>/.claude.json` (local scope) ✅
3. All loaded servers are available for use

---

## 💻 Different Computer Setup

### Step 1: Install Claude Code
```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Or download from: https://claude.com/claude-code
```

### Step 2: Clone Your Repo
```bash
git clone <your-repo-with-mcp-scripts>
cd <your-repo>
```

### Step 3: Run Installer
```bash
./scripts/install_mcp_servers.sh
```

### Step 4: Verify
```bash
claude mcp list
```

Expected output:
```
filesystem: ... - ✓ Connected
serena: ... - ✓ Connected
chrome-superpower: ... - ✓ Connected
... (15+ servers)
```

---

## 📦 What Gets Copied to New Computer

### Files Needed
- `scripts/mcp_common.sh` - Installation logic
- `scripts/install_mcp_servers.sh` - User scope launcher

### Files NOT Needed
These are created automatically:
- `~/.claude.json` - Created by installer
- MCP server packages - Downloaded by npm/npx

---

## 🔑 API Keys (Optional)

Some servers need API keys. Add to `~/.zshrc`:

```bash
export XAI_API_KEY="your_grok_key"
export PERPLEXITY_API_KEY="your_perplexity_key"
export RENDER_API_KEY="your_render_key"
```

Then run:
```bash
source ~/.zshrc
./scripts/install_mcp_servers.sh
```

---

## 🎯 Summary

**Global = User Scope = Available Everywhere**

When you run:
```bash
claude mcp add my-server -s user -- npx some-package
```

Or:
```bash
./scripts/install_mcp_servers.sh  # Uses user scope
```

The server is stored in `~/.claude.json` and **automatically available in ALL your projects**.

No need to reinstall per project! 🎉
