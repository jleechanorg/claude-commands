# Migration Guide: Old Launchers → New Installer

## 🔄 What Changed

The old launcher scripts in project root have been replaced with a unified installer:

**Removed:**
- ❌ `claude_mcp.sh` (project root)
- ❌ `codex_mcp.sh` (project root)

**New:**
- ✅ `scripts/install_mcp_servers.sh` (supports both Claude and Codex)

## 📋 Old vs New

### Before (Old Launchers)

```bash
# Install for Claude
./claude_mcp.sh

# Install for Codex
./codex_mcp.sh
```

### After (New Unified Installer)

```bash
# Install for Claude (default)
./scripts/install_mcp_servers.sh

# Install for Codex
./scripts/install_mcp_servers.sh codex

# Install for both
./scripts/install_mcp_servers.sh both
```

## ✨ Benefits of New Installer

1. **Unified Interface** - One script for both Claude and Codex
2. **Better Organization** - Lives in `scripts/` directory (not project root)
3. **User Scope Default** - Always installs to user scope for global availability
4. **Better Error Handling** - Checks if CLI is installed before proceeding
5. **Environment Variable Loading** - Automatically loads API keys from `.bashrc` for Codex
6. **Clear Usage Help** - Built-in help message for invalid arguments

## 🚀 Migration Steps

### If You Have Scripts/Automation Using Old Launchers

**Replace this:**
```bash
./claude_mcp.sh
./codex_mcp.sh
```

**With this:**
```bash
./scripts/install_mcp_servers.sh both
```

### If You Have Documentation Referencing Old Launchers

Update your docs to reference:
```bash
./scripts/install_mcp_servers.sh [claude|codex|both]
```

## 🆕 New Features

### Install for Both Products at Once

```bash
# Old way - two separate commands
./claude_mcp.sh
./codex_mcp.sh

# New way - single command
./scripts/install_mcp_servers.sh both
```

### Explicit Product Selection

```bash
# More explicit than old launchers
./scripts/install_mcp_servers.sh claude   # Clear what it does
./scripts/install_mcp_servers.sh codex    # Clear what it does
```

### Better Error Messages

```bash
# Old: Would fail silently if CLI not installed
./claude_mcp.sh  # No clear error

# New: Clear error with instructions
./scripts/install_mcp_servers.sh
# ❌ claude CLI not found. Please install Claude first.
# 💡 Install from: https://claude.com/claude-code
```

## 🔧 Advanced: Scope Control

Both old and new scripts support scope control:

```bash
# Old way
MCP_SCOPE=user ./claude_mcp.sh

# New way (same)
MCP_SCOPE=user ./scripts/install_mcp_servers.sh
```

But the **new installer defaults to user scope** (global availability), so you don't need to specify it!

## 📝 File Structure Comparison

### Before
```
worktree_worker3/
├── claude_mcp.sh          ← Root clutter
├── codex_mcp.sh           ← Root clutter
└── scripts/
    └── mcp_common.sh
```

### After (Cleaner)
```
worktree_worker3/
└── scripts/
    ├── mcp_common.sh
    ├── install_mcp_servers.sh  ← New unified installer
    ├── MCP_SETUP.md
    ├── QUICK_START.md
    └── MIGRATION.md (this file)
```

## ❓ FAQ

### Q: Can I still use local scope?
**A:** Yes, but it's not recommended. Use `MCP_SCOPE=local` if needed.

### Q: Will my existing MCP servers be affected?
**A:** No! The installer detects existing servers and skips reinstallation.

### Q: Do I need to uninstall anything?
**A:** No! Just start using the new installer. Old servers work fine.

### Q: What if I have custom modifications to old launchers?
**A:** The new installer sources the same `mcp_common.sh`, so your customizations there still work.

## ✅ Verify Migration

After switching to the new installer:

```bash
# Check Claude servers
claude mcp list

# Check Codex servers
codex mcp list

# All should show: Scope: User config (available in all your projects)
```

If everything shows `✓ Connected` with user scope, migration is complete! 🎉
