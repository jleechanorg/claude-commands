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
- **MCP Launchers** (claude_mcp.sh, codex_mcp.sh) → ~/.claude/ - MCP server launchers with dry-run support

**🚨 EXCLUDED**: Project-specific directories (schemas, templates, framework, guides, learnings, memory_templates, research) are NOT exported to maintain clean global ~/.claude structure.

**✅ INCLUDES**:
- MCP server scripts (mcp_common.sh, mcp_dual_background.sh, mcp_stdio_wrapper.py, etc. in scripts/)
- MCP launcher scripts (claude_mcp.sh, codex_mcp.sh in project root)
- Secondo authentication CLI (auth-cli.mjs)
- Node.js dependencies (package.json, package-lock.json)

**🚀 DRY-RUN SUPPORT**:
- Both claude_mcp.sh and codex_mcp.sh support `--dry-run` flag for testing without making changes
- Example: `~/.claude/claude_mcp.sh --dry-run` or `~/.claude/codex_mcp.sh --dry-run`

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

if [ -f ".claude/commands/export_config.py" ] && command -v python3 >/dev/null 2>&1; then
    # Read exportable components from Python config (portable to Bash 3.2)
    EXPORTABLE_COMPONENTS=()
    while IFS= read -r component; do
        [ -n "$component" ] && EXPORTABLE_COMPONENTS+=("$component")
    done < <(python3 - <<'PY'
import sys
sys.path.insert(0, '.claude/commands')
from export_config import get_exportable_components
for component in get_exportable_components():
    print(component)
PY
)
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
        if command -v rsync >/dev/null 2>&1; then
            # Use rsync for atomic, permission-preserving updates
            if [ -d "$source_path" ]; then
                mkdir -p "$target_path"
                rsync -a --delete "$source_path/" "$target_path/"
            else
                rsync -a "$source_path" "$target_path"
            fi
        else
            # Fallback without rsync: preserve attributes with cp -a
            if [ -e "$target_path" ]; then
                rm -rf "$target_path"
            fi
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

# Consolidate MCP scripts from root scripts/ to .claude/scripts/ before export

echo ""
echo "📦 Consolidating MCP scripts from root scripts/ to .claude/scripts/..."
echo "================================="

mkdir -p ".claude/scripts"

# Copy MCP-related scripts from root to .claude/scripts/
mcp_scripts=(
    "mcp_common.sh"
    "mcp_dual_background.sh"
    "mcp_stdio_wrapper.py"
    "start_mcp_production.sh"
    "start_mcp_server.sh"
)

mcp_copied=0
for script in "${mcp_scripts[@]}"; do
    if [ -f "scripts/$script" ]; then
        cp "scripts/$script" ".claude/scripts/$script"
        chmod +x ".claude/scripts/$script"
        echo "   ✅ Copied $script"
        mcp_copied=$((mcp_copied + 1))
    else
        echo "   ⚠️  $script not found in scripts/, skipping"
    fi
done

echo "   📊 Copied $mcp_copied MCP scripts to .claude/scripts/"

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

# Export MCP launcher scripts from project root

echo ""
echo "📦 Exporting MCP launcher scripts (with dry-run support)..."
echo "================================="

mcp_launchers=("claude_mcp.sh" "codex_mcp.sh")
launcher_count=0

for launcher in "${mcp_launchers[@]}"; do
    if [ -f "$launcher" ]; then
        cp "$launcher" "$HOME/.claude/$launcher"
        chmod +x "$HOME/.claude/$launcher"
        echo "   ✅ Exported $launcher"
        launcher_count=$((launcher_count + 1))
    else
        echo "   ⚠️  $launcher not found in project root, skipping"
    fi
done

echo "   📊 Exported $launcher_count MCP launcher scripts"

# Set executable permissions on hook files

if [ -d "$HOME/.claude/hooks" ]; then
    echo ""
    echo "🔧 Setting executable permissions on hooks..."
    find "$HOME/.claude/hooks" -name "*.sh" -exec chmod +x {} \;
    hook_count=$(find "$HOME/.claude/hooks" -name "*.sh" -print | wc -l)
    echo "   ✅ Made $hook_count hook files executable"
fi

# Set executable permissions on script files

if [ -d "$HOME/.claude/scripts" ]; then
    echo "🔧 Setting executable permissions on scripts..."
    find "$HOME/.claude/scripts" -name "*.sh" -exec chmod +x {} \;
    script_count=$(find "$HOME/.claude/scripts" -name "*.sh" -print | wc -l)
    echo "   ✅ Made $script_count script files executable"
fi

# Export summary

echo ""
echo "📊 Export Summary"
echo "================================="
echo "✅ Components exported: $exported_count/$total_components"

if [ -d "$HOME/.claude/commands" ]; then
    command_count=$(find "$HOME/.claude/commands" -name "*.md" -print | wc -l)
    echo "📋 Commands available: $command_count"
fi

if [ -d "$HOME/.claude/agents" ]; then
    agent_count=$(find "$HOME/.claude/agents" -name "*.md" -print | wc -l)
    echo "🤖 Agents available: $agent_count"
fi

if [ -d "$HOME/.claude/hooks" ]; then
    available_hook_count=$(find "$HOME/.claude/hooks" -name "*.sh" -print | wc -l)
    echo "🎣 Hooks available: $available_hook_count"
fi

if [ -d "$HOME/.claude/skills" ]; then
    skill_count=$(find "$HOME/.claude/skills" -name "*.md" -print | wc -l)
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
echo "8. claude_mcp.sh launcher: $([ -f "$HOME/.claude/claude_mcp.sh" ] && echo "✅ Present" || echo "⚠️  Missing")"
echo "9. codex_mcp.sh launcher: $([ -f "$HOME/.claude/codex_mcp.sh" ] && echo "✅ Present" || echo "⚠️  Missing")"

echo ""
echo "🎉 Local export completed successfully!"
echo ""
echo "🚀 Test MCP launchers with dry-run mode:"
echo "   cd ~ && ~/.claude/claude_mcp.sh --dry-run"
echo "   cd ~ && ~/.claude/codex_mcp.sh --dry-run"
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
