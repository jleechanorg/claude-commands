---
description: /localexportcommands - Export Project Claude Configuration Locally
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Execute Documented Workflow

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps sequentially.

## 📋 REFERENCE DOCUMENTATION

# /localexportcommands - Export Project Claude Configuration Locally

Copies the project's .claude folder structure to your local ~/.claude directory, making commands and configurations available system-wide. **PRESERVES** existing conversation history and other critical data.

## Usage

```bash
/localexportcommands
```

## What Gets Exported

This command copies standard Claude Code directories to ~/.claude:

- **Commands** (.claude/commands/) → ~/.claude/commands/ - Slash commands
- **Hooks** (.claude/hooks/) → ~/.claude/hooks/ - Lifecycle hooks
- **Agents** (.claude/agents/) → ~/.claude/agents/ - Subagents
- **Scripts** (.claude/scripts/) → ~/.claude/scripts/ - Utility scripts (MCP scripts, secondo auth-cli.mjs, etc.)
- **Skills** (.claude/skills/) → ~/.claude/skills/ - Skill documentation and guides
- **Settings** (.claude/settings.json) → ~/.claude/settings.json - Configuration
- **Dependencies** (package.json, package-lock.json) → ~/.claude/ - Node.js dependencies for secondo command
- **Codex Skills** (.codex/skills/) → ~/.codex/skills/ - Codex CLI skill documentation
- **Codex Hooks** (.codex/hooks/) → ~/.codex/hooks/ - Codex CLI automation hooks
- **Ralph Toolkit** (ralph/) → ~/ralph/ - Portable Ralph runtime and libraries
**🚨 EXCLUDED**: Project-specific directories (schemas, templates, framework, guides, learnings, memory_templates, research) are NOT exported to maintain clean global ~/.claude structure.

**✅ INCLUDES**:
- MCP server scripts (mcp_common.sh, mcp_dual_background.sh, mcp_stdio_wrapper.py, etc.)
- **Unified MCP installer** (install_mcp_servers.sh) - Installs all MCP servers for Claude/Codex/both
- **Secondo authentication CLI** (auth-cli.mjs in .claude/scripts/)
- Node.js dependencies (package.json, package-lock.json)
- **Ralph toolkit scripts** (ralph.sh, ralph-pair.sh, lib/*.sh, dashboard assets)

**🚀 UNIFIED MCP INSTALLER**:
- `install_mcp_servers.sh` replaces old claude_mcp.sh and codex_mcp.sh launchers
- Usage: `~/.claude/scripts/install_mcp_servers.sh [claude|codex|both]` (default: claude)
- Supports `--test-dir` flag for testing without modifying production configs

## Implementation

```bash
#!/bin/bash

echo "🚀 Starting local export of .claude configuration..."

# Validate source directory

if [ ! -d ".claude" ]; then
    echo "❌ ERROR: .claude directory not found in current project"
    echo "   Make sure you're running this from a project root with .claude/ folder"
    exit 1
fi

# Source shared export component configuration from Python
# This ensures both /localexportcommands and /exportcommands export the same directories

if [ -f ".claude/commands/export_config.py" ]; then
    # Read exportable components from Python config (portable - no mapfile)
    EXPORTABLE_COMPONENTS=($(python3 -c "
import sys
sys.path.insert(0, '.claude/commands')
from export_config import get_exportable_components
for component in get_exportable_components():
    print(component)
"))
    echo "✅ Using shared Python export configuration"
else
    echo "⚠️  Warning: Shared export config not found, using fallback list"
    # Fallback list if shared config unavailable
    # This list contains ONLY standard Claude Code directories, not project-specific custom ones
    EXPORTABLE_COMPONENTS=(
        "commands"      # Slash commands (.md files) - STANDARD
        "hooks"         # Lifecycle hooks - STANDARD
        "agents"        # Subagents/specialized AI assistants - STANDARD
        "scripts"       # Utility scripts (MCP scripts, secondo auth-cli.mjs, etc.) - STANDARD
        "skills"        # Skill documentation and guides - STANDARD
        "settings.json" # Configuration file - STANDARD
    )
fi

# Create backup of existing ~/.claude components (selective backup strategy)

backup_timestamp="$(date +%Y%m%d_%H%M%S)"
if [ -d "$HOME/.claude" ]; then
    echo "📦 Creating selective backup of existing ~/.claude configuration..."
    # Create backup directory once before processing components
    backup_dir="$HOME/.claude.backup.$backup_timestamp"
    mkdir -p "$backup_dir"

    for component in "${EXPORTABLE_COMPONENTS[@]}"; do
        if [ -e "$HOME/.claude/$component" ]; then
            cp -r "$HOME/.claude/$component" "$backup_dir/"
            echo "   📋 Backed up $component"
        fi
    done
fi

# Create target directory (preserve existing structure)

echo "📁 Ensuring ~/.claude directory exists..."
mkdir -p "$HOME/.claude"

# Export function for individual components (selective update only)

export_component() {
    local component=$1
    local source_path=".claude/$component"
    local target_path="$HOME/.claude/$component"

    if [ -e "$source_path" ]; then
        echo "📋 Updating $component..."

        # Path safety check - prevent dangerous operations
        case "$target_path" in
            "$HOME/.claude"|"$HOME/.claude/"|"")
                echo "❌ ERROR: Refusing dangerous target path: $target_path"
                return 1
                ;;
        esac

        # Safer, metadata-preserving update with rsync or cp -a fallback
        # NOTE: We intentionally do NOT use --delete to preserve:
        #   - Plugin-installed commands (e.g., superpowers)
        #   - Manually added symlinks or files
        #   - Other tools that install to ~/.claude/
        if command -v rsync >/dev/null 2>&1; then
            # Use rsync for atomic, permission-preserving updates (no --delete)
            if [ -d "$source_path" ]; then
                mkdir -p "$target_path"
                rsync -a "$source_path/" "$target_path/"
            else
                rsync -a "$source_path" "$target_path"
            fi
        else
            # Fallback without rsync: merge using cp -a (no deletion)
            # This preserves existing files not in source (plugins, manual additions)
            if [ -d "$source_path" ]; then
                mkdir -p "$target_path"
                cp -a "$source_path/." "$target_path"
            else
                cp -a "$source_path" "$target_path"
            fi
        fi
        echo "   ✅ $component updated successfully"
        return 0
    else
        echo "   ⚠️  $component not found, skipping"
        return 1
    fi
}

# Copy MCP scripts from root scripts/ directly to ~/.claude/scripts/ (NOT to working dir)

echo ""
echo "📦 Copying MCP scripts from root scripts/ to ~/.claude/scripts/..."
echo "================================="

mkdir -p "$HOME/.claude/scripts"

# Copy MCP-related scripts from root directly to ~/.claude/scripts/
# Note: This does NOT modify the working directory - only the target ~/.claude/
mcp_scripts=(
    "mcp_common.sh"
    "mcp_dual_background.sh"
    "mcp_stdio_wrapper.py"
    "start_mcp_production.sh"
    "start_mcp_server.sh"
    "install_mcp_servers.sh"
)

mcp_copied=0
for script in "${mcp_scripts[@]}"; do
    if [ -f "scripts/$script" ]; then
        cp "scripts/$script" "$HOME/.claude/scripts/$script"
        chmod +x "$HOME/.claude/scripts/$script"
        echo "   ✅ Copied $script"
        mcp_copied=$((mcp_copied + 1))
    else
        echo "   ⚠️  $script not found in scripts/, skipping"
    fi
done

echo "   📊 Copied $mcp_copied MCP scripts to ~/.claude/scripts/"

# Track export statistics

exported_count=0
total_components=0

# Use the predefined components list for export

components=("${EXPORTABLE_COMPONENTS[@]}")

echo ""
echo "📦 Exporting components..."
echo "================================="

for component in "${components[@]}"; do
    total_components=$((total_components + 1))
    if export_component "$component"; then
        exported_count=$((exported_count + 1))
    fi
done

# Export Node.js dependencies for secondo command

echo ""
echo "📦 Exporting Node.js dependencies (for secondo command)..."
echo "================================="

if [ -f "package.json" ]; then
    cp "package.json" "$HOME/.claude/package.json"
    echo "   ✅ Exported package.json"
else
    echo "   ⚠️  package.json not found, skipping"
fi

if [ -f "package-lock.json" ]; then
    cp "package-lock.json" "$HOME/.claude/package-lock.json"
    echo "   ✅ Exported package-lock.json"
else
    echo "   ⚠️  package-lock.json not found, skipping"
fi

# Set executable permissions on hook files

if [ -d "$HOME/.claude/hooks" ]; then
    echo ""
    echo "🔧 Setting executable permissions on hooks..."
    find "$HOME/.claude/hooks" -name "*.sh" -exec chmod +x {} \;
    hook_count=$(find "$HOME/.claude/hooks" -name "*.sh" -print0 | grep -zc .)
    echo "   ✅ Made $hook_count hook files executable"
fi

# Set executable permissions on script files

if [ -d "$HOME/.claude/scripts" ]; then
    echo "🔧 Setting executable permissions on scripts..."
    find "$HOME/.claude/scripts" -name "*.sh" -exec chmod +x {} \;
    script_count=$(find "$HOME/.claude/scripts" -name "*.sh" -print0 | grep -zc .)
    echo "   ✅ Made $script_count script files executable"
fi

# Export summary

echo ""
echo "📊 Export Summary"
echo "================================="
echo "✅ Components exported: $exported_count/$total_components"

if [ -d "$HOME/.claude/commands" ]; then
    command_count=$(find "$HOME/.claude/commands" -name "*.md" -print0 | grep -zc .)
    echo "📋 Commands available: $command_count"
fi

if [ -d "$HOME/.claude/agents" ]; then
    agent_count=$(find "$HOME/.claude/agents" -name "*.md" -print0 | grep -zc .)
    echo "🤖 Agents available: $agent_count"
fi

if [ -d "$HOME/.claude/hooks" ]; then
    available_hook_count=$(find "$HOME/.claude/hooks" -name "*.sh" -print0 | grep -zc .)
    echo "🎣 Hooks available: $available_hook_count"
fi

if [ -d "$HOME/.claude/skills" ]; then
    skill_count=$(find "$HOME/.claude/skills" -name "*.md" -print0 | grep -zc .)
    echo "🧠 Skills available: $skill_count"
fi

echo ""
echo "🎯 System-Wide Access Enabled!"
echo "================================="
echo "Your Claude Code commands and configurations are now available globally."
echo ""
echo "📁 Target directory: ~/.claude"
echo "🔍 Verify installation:"
echo "   ls -la ~/.claude"
echo ""
echo "🚀 Commands from this project can now be used in any Claude Code session!"

# Export Codex skills from .codex/skills/ to ~/.codex/skills/
echo ""
echo "📦 Exporting Codex skills..."
echo "================================="

if [ -d ".codex/skills" ]; then
    mkdir -p "$HOME/.codex/skills"

    # Count skills before copy
    codex_skill_count=$(find .codex/skills -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')

    # Use rsync if available, otherwise cp -a
    if command -v rsync >/dev/null 2>&1; then
        rsync -a ".codex/skills/" "$HOME/.codex/skills/"
    else
        cp -a ".codex/skills/." "$HOME/.codex/skills/"
    fi

    echo "   ✅ Exported $codex_skill_count Codex skills to ~/.codex/skills/"
else
    echo "   ⚠️  .codex/skills/ not found, skipping Codex skills export"
fi

# Export Codex hooks from .codex/hooks/ to ~/.codex/hooks/
echo ""
echo "📦 Exporting Codex hooks..."
echo "================================="

if [ -d ".codex/hooks" ]; then
    mkdir -p "$HOME/.codex/hooks"

    # Count hooks before copy
    codex_hook_count=$(find .codex/hooks -mindepth 1 -maxdepth 1 -type f \( -name "*.sh" -o -name "*.py" \) | wc -l | tr -d ' ')

    # Use rsync if available, otherwise cp -a
    if command -v rsync >/dev/null 2>&1; then
        rsync -a ".codex/hooks/" "$HOME/.codex/hooks/"
    else
        cp -a ".codex/hooks/." "$HOME/.codex/hooks/"
    fi

    # Set executable permissions on shell scripts
    if [ -d "$HOME/.codex/hooks" ]; then
        if ! find "$HOME/.codex/hooks" -name "*.sh" -exec chmod +x {} \; ; then
            echo "   ⚠️  Failed to set executable permissions on one or more Codex hooks" >&2
        fi
    fi

    echo "   ✅ Exported $codex_hook_count Codex hooks to ~/.codex/hooks/"
else
    echo "   ⚠️  .codex/hooks/ not found, skipping Codex hooks export"
fi

# Export Codex hooks engine config from .codex/hooks.json to ~/.codex/hooks.json
echo ""
echo "📦 Exporting Codex hooks config..."
echo "================================="

if [ -f ".codex/hooks.json" ]; then
    mkdir -p "$HOME/.codex"
    cp ".codex/hooks.json" "$HOME/.codex/hooks.json"
    echo "   ✅ Exported Codex hooks config to ~/.codex/hooks.json"
else
    echo "   ⚠️  .codex/hooks.json not found, skipping Codex hooks config export"
fi

# Enable codex_hooks feature (required by Codex CLI hooks engine)
if command -v codex >/dev/null 2>&1; then
    if codex features enable codex_hooks >/dev/null 2>&1; then
        echo "   ✅ Enabled Codex feature flag: codex_hooks"
    else
        echo "   ⚠️  Could not auto-enable codex_hooks feature. Run: codex features enable codex_hooks"
    fi
else
    echo "   ⚠️  codex CLI not found; enable manually after install: codex features enable codex_hooks"
fi

# Export Ralph toolkit from root ralph/ to ~/ralph/
echo ""
echo "📦 Exporting Ralph toolkit..."
echo "================================="

if [ -d "ralph" ]; then
    mkdir -p "$HOME/ralph"
    backup_root="$HOME/.claude/backups"
    backup_dir="$backup_root/ralph-$(date +%Y%m%d-%H%M%S)"

    if [ -d "$HOME/ralph" ] && [ "$(ls -A "$HOME/ralph" 2>/dev/null)" ]; then
        mkdir -p "$backup_root" "$backup_dir"
        if command -v rsync >/dev/null 2>&1; then
            rsync -a "$HOME/ralph/" "$backup_dir/"
        else
            cp -a "$HOME/ralph/." "$backup_dir/"
        fi
        echo "   🔁 Backed up existing ~/ralph to $backup_dir"
    fi

    if command -v rsync >/dev/null 2>&1; then
        rsync -a --delete \
            --exclude="prd.json" \
            --exclude="progress.txt" \
            --exclude="metrics.json" \
            --exclude="archive/" \
            --exclude=".last-branch" \
            "ralph/" "$HOME/ralph/"
    else
        tmp_dir="$HOME/ralph.tmp.$$"
        rm -rf "$tmp_dir"
        mkdir -p "$tmp_dir"
        cp -a "ralph/." "$tmp_dir/"

        # Remove repo runtime files from tmp_dir so fresh install does not leak source state
        rm -f "$tmp_dir/prd.json" "$tmp_dir/progress.txt" "$tmp_dir/metrics.json" "$tmp_dir/.last-branch"
        rm -rf "$tmp_dir/archive"

        for runtime_file in "prd.json" "progress.txt" "metrics.json" ".last-branch"; do
            if [ -e "$HOME/ralph/$runtime_file" ]; then
                cp -a "$HOME/ralph/$runtime_file" "$tmp_dir/$runtime_file"
            fi
        done

        if [ -d "$HOME/ralph/archive" ]; then
            mkdir -p "$tmp_dir/archive"
            cp -a "$HOME/ralph/archive/." "$tmp_dir/archive/"
        fi

        rm -rf "$HOME/ralph"
        mv "$tmp_dir" "$HOME/ralph"
    fi

    find "$HOME/ralph" -name "*.sh" -exec chmod +x {} \;
    echo "   ✅ Exported Ralph toolkit to ~/ralph (toolkit synced, runtime state preserved)"
else
    echo "   ⚠️  ralph/ directory not found, skipping Ralph toolkit export"
fi

echo ""
# Validation checklist

echo ""
echo "✅ Post-Export Validation Checklist"
echo "================================="
echo "1. Commands directory: $([ -d "$HOME/.claude/commands" ] && echo "✅ Present" || echo "❌ Missing")"
echo "2. Settings file: $([ -f "$HOME/.claude/settings.json" ] && echo "✅ Present" || echo "❌ Missing")"
echo "3. Hooks directory: $([ -d "$HOME/.claude/hooks" ] && echo "✅ Present" || echo "❌ Missing")"
echo "4. Agents directory: $([ -d "$HOME/.claude/agents" ] && echo "✅ Present" || echo "❌ Missing")"
echo "5. Scripts directory: $([ -d "$HOME/.claude/scripts" ] && echo "✅ Present" || echo "❌ Missing")"
echo "6. Skills directory: $([ -d "$HOME/.claude/skills" ] && echo "✅ Present" || echo "❌ Missing")"
echo "7. package.json: $([ -f "$HOME/.claude/package.json" ] && echo "✅ Present" || echo "⚠️  Missing (secondo may not work)")"
echo "8. install_mcp_servers.sh: $([ -f "$HOME/.claude/scripts/install_mcp_servers.sh" ] && echo "✅ Present" || echo "⚠️  Missing")"
echo "9. Codex skills directory: $([ -d "$HOME/.codex/skills" ] && echo "✅ Present ($(find "$HOME/.codex/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ') skills)" || echo "⚠️  Missing")"
echo "10. Codex hooks directory: $([ -d "$HOME/.codex/hooks" ] && echo "✅ Present ($(find "$HOME/.codex/hooks" -mindepth 1 -maxdepth 1 -type f | wc -l | tr -d ' ') hooks)" || echo "⚠️  Missing")"
echo "11. Codex hooks config: $([ -f "$HOME/.codex/hooks.json" ] && echo "✅ Present" || echo "⚠️  Missing")"
echo "12. Ralph toolkit entrypoint: $([ -x "$HOME/ralph/ralph.sh" ] && echo "✅ Present" || echo "⚠️  Missing or not executable")"

echo ""
echo "🎉 Local export completed successfully!"
echo ""

# Install Node.js dependencies if package.json was exported
if [ -f "$HOME/.claude/package.json" ]; then
    echo "📦 Installing Node.js dependencies for secondo authentication..."
    if command -v npm >/dev/null 2>&1; then
        (cd "$HOME/.claude" && npm install --silent 2>&1 | grep -v "^npm WARN" || true)
        if [ -d "$HOME/.claude/node_modules/express" ]; then
            echo "   ✅ Express installed successfully"
        else
            echo "   ⚠️  Express installation may have failed"
            echo "   Run manually: cd ~/.claude && npm install"
        fi
    else
        echo "   ⚠️  npm not found. Install Node.js dependencies manually:"
        echo "      cd ~/.claude && npm install"
    fi
    echo ""
fi

echo "🚀 Next steps:"
echo "1. Authenticate (run outside Claude Code):"
echo "   node ~/.claude/scripts/auth-cli.mjs login"
echo ""
echo "2. Test authentication:"
echo "   node ~/.claude/scripts/auth-cli.mjs status"
echo ""
echo "3. Test MCP installer:"
echo "   ~/.claude/scripts/install_mcp_servers.sh --test-dir /tmp/mcp-test claude"
```

## Benefits

- **System-Wide Availability**: Commands work across all Claude Code projects
- **Consistent Environment**: Same tools and configurations everywhere
- **Easy Updates**: Re-run to sync latest project changes
- **Safe Operation**: Creates selective backups of only updated components
- **Conversation History Preservation**: Never touches existing projects/ directory or conversation data
- **Comprehensive Coverage**: Updates all relevant .claude components while preserving critical data

## Safety Features

- **🚨 CONVERSATION HISTORY PROTECTION**: Never touches ~/.claude/projects/ directory
- Creates timestamped backup of only components being updated
- Validates source directory before starting
- Individual component copying (partial failures don't break everything)
- Preserves file permissions and executable status
- Selective update approach protects critical user data
- Comprehensive feedback and validation

## Use Cases

- Setting up a new development machine
- Sharing Claude Code configuration across projects
- Maintaining consistent tooling environment
- Backing up and restoring Claude Code setup
- Team standardization of Claude Code tools

## Notes

- Run from project root containing .claude directory
- Safe to run multiple times (creates new selective backups)
- Hooks automatically made executable after copy
- Settings.json merged/replaced based on content
- Commands adapt automatically to current project context
- **🚨 IMPORTANT**: This version preserves conversation history - previous versions destroyed ~/.claude/projects/
