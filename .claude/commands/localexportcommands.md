# /localexportcommands - Export Project Claude Configuration Locally

Copies the project's .claude folder structure to your local ~/.claude directory, making commands and configurations available system-wide. **PRESERVES** existing conversation history and other critical data.

## Usage
```bash
/localexportcommands
```

## What Gets Exported

This command copies the entire project .claude structure to ~/.claude:

- **Commands** (.claude/commands/) → ~/.claude/commands/
- **Hooks** (.claude/hooks/) → ~/.claude/hooks/
- **Agents** (.claude/agents/) → ~/.claude/agents/
- **Settings** (.claude/settings.json) → ~/.claude/settings.json
- **Schemas** (.claude/schemas/) → ~/.claude/schemas/
- **Templates** (.claude/templates/) → ~/.claude/templates/
- **Scripts** (.claude/scripts/) → ~/.claude/scripts/
- **Framework** (.claude/framework/) → ~/.claude/framework/
- **Other directories and files** as needed

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

# Define exportable components list (extracted for maintainability)
# This list determines what gets backed up and exported
EXPORTABLE_COMPONENTS=(
    "commands"
    "hooks"
    "agents"
    "settings.json"
    "schemas"
    "templates"
    "scripts"
    "framework"
    "guides"
    "learnings"
    "memory_templates"
    "research"
)

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

        # Remove existing component before copying (but preserve other directories)
        if [ -e "$target_path" ]; then
            rm -rf "$target_path"
        fi

        # Copy new component
        if [ -d "$source_path" ]; then
            mkdir -p "$target_path"
            cp -r "$source_path/." "$target_path"
        else
            cp "$source_path" "$target_path"
        fi
        echo "   ✅ $component updated successfully"
        return 0
    else
        echo "   ⚠️  $component not found, skipping"
        return 1
    fi
}

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

echo ""
echo "🎉 Local export completed successfully!"
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
