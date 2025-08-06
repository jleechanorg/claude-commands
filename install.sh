#!/bin/bash

# Claude Commands Installation Script
# Automatically installs command composition system to .claude/commands/

set -e

echo "🚀 Installing Claude Commands - Command Composition System"
echo ""

# Check if we're in a valid directory
if [ ! -d ".git" ]; then
    echo "⚠️  Warning: Not in a git repository. Claude Commands work best in git-managed projects."
    echo "   Consider running: git init"
fi

# Create .claude directory structure
if [ ! -d ".claude" ]; then
    echo "📁 Creating .claude directory..."
    mkdir -p .claude
fi

if [ ! -d ".claude/commands" ]; then
    echo "📁 Creating .claude/commands directory..."
    mkdir -p .claude/commands
fi

# Copy commands
echo "📋 Installing command files..."
if [ -d "commands" ]; then
    cp -r commands/* .claude/commands/
    echo "   ✅ Installed $(find commands -name '*.md' | wc -l) command definitions"
else
    echo "   ❌ Error: commands directory not found"
    exit 1
fi

# Copy infrastructure scripts if available
if [ -d "infrastructure-scripts" ]; then
    echo "🔧 Installing infrastructure scripts..."
    for script in infrastructure-scripts/*; do
        if [ -f "$script" ]; then
            cp "$script" ./
            chmod +x "./$(basename "$script")"
        fi
    done
    echo "   ✅ Installed infrastructure scripts"
fi

# Copy orchestration system if available
if [ -d "orchestration" ]; then
    echo "🤖 Installing orchestration system..."
    cp -r orchestration ./
    echo "   ✅ Installed orchestration system"
fi

# Copy utility scripts if available
if [ -d "scripts" ]; then
    echo "📜 Installing utility scripts..."
    mkdir -p scripts
    cp -r scripts/* ./scripts/
    echo "   ✅ Installed utility scripts"
fi

# Update .gitignore
echo "📝 Updating .gitignore..."
if [ -f ".gitignore" ]; then
    if ! grep -q ".claude/" .gitignore; then
        echo ".claude/" >> .gitignore
        echo "# Claude Commands - Auto-installed" >> .gitignore
    fi
else
    cat > .gitignore << EOF
.claude/
# Claude Commands - Auto-installed
EOF
fi

echo ""
echo "🎉 Installation Complete!"
echo ""
echo "🚀 Quick Start Commands:"
echo "   /execute \"implement user authentication\"  # Auto-approval development"
echo "   /pr \"fix performance issues\"              # Complete PR workflow"
echo "   /copilot                                   # Fix PR issues autonomously"
echo ""
echo "📚 Command Chaining Examples:"
echo "   \"/arch /thinku /devilsadvocate /diligent\" # Comprehensive analysis"
echo "   \"/think about auth then /execute solution\" # Sequential workflow"
echo ""
echo "⚠️  Note: This is a prototype system exported from a working environment."
echo "   Some commands may need adaptation for your specific setup."
echo "   Claude Code excels at helping you customize them!"
echo ""