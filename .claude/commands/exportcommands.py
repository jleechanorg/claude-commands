#!/usr/bin/env python3
"""
Claude Commands Exporter
Exports Claude Code command system to GitHub repository with automatic PR creation
"""

import os
import sys
import time
import subprocess
import tempfile
import shutil
import re
import json
import requests
from pathlib import Path

class ClaudeCommandsExporter:
    def __init__(self):
        self.project_root = self._get_project_root()
        self.export_dir = os.path.join(tempfile.gettempdir(), f"claude_commands_export_{int(time.time())}")
        self.repo_dir = os.path.join(tempfile.gettempdir(), f"claude_commands_repo_{int(time.time())}")
        self.export_branch = f"export-{time.strftime('%Y%m%d-%H%M%S')}"
        self.github_token = os.environ.get('GITHUB_TOKEN')

        # Counters for summary
        self.commands_count = 0
        self.hooks_count = 0
        self.scripts_count = 0

    def _get_project_root(self):
        """Get the project root directory"""
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("Not in a git repository")
        return result.stdout.strip()

    def export(self):
        """Main export workflow"""
        try:
            print("🚀 Starting Claude Commands Export...")
            print("=" * 50)

            self.phase1_local_export()
            pr_url = self.phase2_github_publish()
            self.report_success(pr_url)

        except Exception as e:
            self.handle_error(e)
            sys.exit(1)

    def phase1_local_export(self):
        """Phase 1: Create local export with directory exclusions"""
        print("\n📂 Phase 1: Creating Local Export...")
        print("-" * 40)

        # Create staging directory
        staging_dir = os.path.join(self.export_dir, "staging")
        os.makedirs(staging_dir, exist_ok=True)

        print(f"📁 Created export directory: {self.export_dir}")

        # Create subdirectories
        subdirs = ['commands', 'hooks', 'infrastructure-scripts', 'orchestration']
        for subdir in subdirs:
            os.makedirs(os.path.join(staging_dir, subdir), exist_ok=True)

        # Export commands
        self._export_commands(staging_dir)

        # Export hooks
        self._export_hooks(staging_dir)

        # Export infrastructure scripts
        self._export_infrastructure_scripts(staging_dir)

        # Export orchestration (with exclusions)
        self._export_orchestration(staging_dir)

        # Generate install script and README
        self._generate_install_script()
        self._generate_readme()

        # Create archive
        self._create_archive()

        print("✅ Phase 1 complete - Local export created")

    def _export_commands(self, staging_dir):
        """Export command definitions with content filtering"""
        print("📋 Exporting command definitions...")

        commands_dir = os.path.join(self.project_root, '.claude', 'commands')
        if not os.path.exists(commands_dir):
            print("⚠️  Warning: .claude/commands directory not found")
            return

        target_dir = os.path.join(staging_dir, 'commands')

        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)

        for file_path in Path(commands_dir).glob('*'):
            if file_path.is_file() and file_path.suffix in ['.md', '.py']:
                filename = file_path.name

                # Skip project-specific files
                if filename in ['testi.sh', 'run_tests.sh', 'copilot_inline_reply_example.sh']:
                    print(f"   ⏭ Skipping {filename} (project-specific)")
                    continue

                target_path = os.path.join(target_dir, filename)
                shutil.copy2(file_path, target_path)

                # Apply content transformations
                self._apply_content_filtering(target_path)

                print(f"   • {filename}")
                self.commands_count += 1

        print(f"✅ Exported {self.commands_count} commands")

    def _export_hooks(self, staging_dir):
        """Export Claude Code hooks with proper permissions, avoiding duplicates"""
        print("📎 Exporting Claude Code hooks...")

        hooks_dir = os.path.join(self.project_root, '.claude', 'hooks')
        if not os.path.exists(hooks_dir):
            print("⚠️  Warning: .claude/hooks directory not found")
            return

        target_dir = os.path.join(staging_dir, 'hooks')

        # Use rsync with exclusions to avoid nested .claude directories that create duplicates
        # CRITICAL: Exclusions must come before inclusions in rsync
        cmd = [
            'rsync', '-av',
            '--exclude=*/.claude/',      # Exclude nested .claude directories FIRST
            '--exclude=*/.claude/**',    # Exclude all content within nested .claude directories
            '--include=*/',              # Then include directories
            '--include=*.sh',
            '--include=*.py',
            '--include=*.md',
            '--exclude=*',               # Finally exclude everything else
            f"{hooks_dir}/",
            f"{target_dir}/"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Hook export failed: {result.stderr}")

        # Apply content filtering and count files
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith(('.sh', '.py', '.md')):
                    file_path = os.path.join(root, file)
                    self._apply_content_filtering(file_path)

                    # Ensure scripts are executable
                    if file.endswith(('.sh', '.py')):
                        os.chmod(file_path, 0o755)

                    self.hooks_count += 1
                    rel_path = os.path.relpath(file_path, target_dir)
                    print(f"   📎 {rel_path}")

        print(f"✅ Exported {self.hooks_count} hooks")

    def _export_infrastructure_scripts(self, staging_dir):
        """Export root-level infrastructure scripts"""
        print("🚀 Exporting infrastructure scripts...")

        target_dir = os.path.join(staging_dir, 'infrastructure-scripts')

        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)

        script_patterns = [
            'claude_start.sh', 'claude_mcp.sh', 'integrate.sh',
            'resolve_conflicts.sh', 'sync_branch.sh'
        ]

        for script_name in script_patterns:
            script_path = os.path.join(self.project_root, script_name)
            if os.path.exists(script_path):
                target_path = os.path.join(target_dir, script_name)
                shutil.copy2(script_path, target_path)
                self._apply_content_filtering(target_path)

                print(f"   • {script_name}")
                self.scripts_count += 1

        print(f"✅ Exported {self.scripts_count} infrastructure scripts")

    def _export_orchestration(self, staging_dir):
        """Export orchestration system with directory exclusions"""
        print("🤖 Exporting orchestration system (with exclusions)...")

        source_dir = os.path.join(self.project_root, 'orchestration')
        if not os.path.exists(source_dir):
            print("⚠️  Orchestration directory not found - skipping")
            return

        target_dir = os.path.join(staging_dir, 'orchestration')

        # Use rsync with explicit exclusions
        exclude_patterns = [
            '--exclude=analysis/',
            '--exclude=automation/',
            '--exclude=claude-bot-commands/',
            '--exclude=coding_prompts/',
            '--exclude=prototype/',
            '--exclude=tasks/',
        ]

        cmd = ['rsync', '-av'] + exclude_patterns + [f"{source_dir}/", f"{target_dir}/"]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⏭ Orchestration export partial or skipped: {result.stderr}")
        else:
            print("✅ Orchestration exported (excluded specified directories)")

    def _apply_content_filtering(self, file_path):
        """Apply content transformations to files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Apply transformations - FIXED: These now perform actual replacements
            content = re.sub(r'mvp_site/', '$PROJECT_ROOT/', content)
            content = re.sub(r'worldarchitect\.ai', 'your-project.com', content)
            content = re.sub(r'\bjleechan\b', '$USER', content)
            content = re.sub(r'TESTING=true vpython', 'TESTING=true python', content)
            content = re.sub(r'WorldArchitect\.AI', 'Your Project', content)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            print(f"⚠️  Warning: Content filtering failed for {file_path}: {e}")

    def _generate_install_script(self):
        """Generate install.sh script"""
        install_content = '''#!/bin/bash
# 🚀 Claude Commands Installation Script
# Auto-generated by /exportcommands

set -e  # Exit on any error

echo "🚀 Installing Claude Commands..."
echo "=================================="

# Check if we're in a git repository and navigate to root
if ! git_root=$(git rev-parse --show-toplevel 2>/dev/null); then
    echo "❌ Error: Not inside a git repository" >&2
    exit 1
fi
cd "$git_root"

# Create .claude directories
mkdir -p .claude/{commands,hooks}

# Install commands
echo "📋 Installing command definitions..."
if [ -d "commands" ]; then
    for file in commands/*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            if [[ "$filename" == "README"* ]]; then
                echo "   ⏭ Skipping $filename (documentation file)"
                continue
            fi
            echo "   • $filename"
            cp "$file" ".claude/commands/$filename"
        fi
    done
    echo "✅ Commands installed to .claude/commands/"
fi

# Install hooks
echo "📎 Installing Claude Code hooks..."
if [ -d "hooks" ]; then
    find hooks -type f \\( -name "*.sh" -o -name "*.py" -o -name "*.md" \\) -print0 | while IFS= read -r -d '' hook_file; do
        relative_path="${hook_file#hooks/}"
        target_path=".claude/hooks/$relative_path"
        target_dir=$(dirname "$target_path")

        mkdir -p "$target_dir"
        echo "   📎 $relative_path"
        cp "$hook_file" "$target_path"

        case "$relative_path" in
            *.sh|*.py) chmod +x "$target_path" ;;
        esac
    done
    echo "✅ Hooks installed to .claude/hooks/"
fi

# Install startup script
echo "🚀 Installing startup script..."
if [ -f "infrastructure-scripts/claude_start.sh" ]; then
    cp "infrastructure-scripts/claude_start.sh" "./claude_start.sh"
    chmod +x "./claude_start.sh"
    echo "✅ Startup script installed"
fi

# Update .gitignore
echo "📝 Updating .gitignore..."
if ! grep -q ".claude/" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo "# Claude Commands - Auto-installed" >> .gitignore
    echo ".claude/" >> .gitignore
    echo "claude_start.sh" >> .gitignore
    echo "✅ Updated .gitignore"
else
    echo "✅ .gitignore already up to date"
fi

echo ""
echo "🎉 Installation Complete!"
echo ""
echo "Next steps:"
echo "1. Adapt commands for your project (replace \\$PROJECT_ROOT placeholders)"
echo "2. Update claude_start.sh with your project-specific paths"
echo "3. Run ./claude_start.sh to start Claude Code with MCP servers"
echo ""
echo "⚠️  Remember: These are reference commands that may need adaptation"
'''

        # Ensure export directory exists
        os.makedirs(self.export_dir, exist_ok=True)

        install_path = os.path.join(self.export_dir, 'install.sh')
        with open(install_path, 'w') as f:
            f.write(install_content)
        os.chmod(install_path, 0o755)

        print("✅ Generated install.sh script")

    def _generate_readme(self):
        """Generate comprehensive README based on commands repo state"""
        # This README generation should analyze the COMMANDS REPO state, not worldarch project
        # It will be called from within the cloned commands repo directory
        readme_content = f'''# Claude Commands - Command Composition System

⚠️ **REFERENCE EXPORT** - This is a reference export from a working Claude Code project. These commands have been tested in production but may require adaptation for your specific environment. Claude Code excels at helping you customize them for your workflow.

Transform Claude Code into an autonomous development powerhouse through simple command hooks that enable complex workflow orchestration.

## 🚀 ONE-CLICK INSTALL

```bash
./install.sh
```

Auto-installs **{self.commands_count} commands** + **{self.hooks_count} hooks** + **infrastructure scripts** to your `.claude/` directory and copies `claude_start.sh` for immediate use.

## 📊 **Export Contents**

This comprehensive export includes:
- **📋 {self.commands_count} Command Definitions** - Complete workflow orchestration system (.claude/commands/)
- **📎 {self.hooks_count} Claude Code Hooks** - Essential workflow automation (.claude/hooks/)
- **🔧 {self.scripts_count} Infrastructure Scripts** - Development environment management
- **🤖 Orchestration System** - Core multi-agent task delegation (project-specific parts excluded)
- **📚 Complete Documentation** - Installation guide with adaptation examples

🚨 **DIRECTORY EXCLUSIONS APPLIED**: This export excludes the following project-specific directories:
- ❌ `analysis/` - Project-specific analytics
- ❌ `automation/` - Project-specific automation
- ❌ `claude-bot-commands/` - Project-specific bot implementation
- ❌ `coding_prompts/` - Project-specific AI prompting templates
- ❌ `prototype/` - Project-specific experimental code

## 🎯 The Magic: Simple Hooks → Powerful Workflows

### Command Chaining Examples
```bash
# Multi-command composition
"/arch /thinku /devilsadvocate /diligent"  # → comprehensive code analysis

# Sequential workflow chains
"/think about auth then /execute the solution"  # → analysis → implementation

# Conditional execution flows
"/test login flow and if fails /fix then /pr"  # → test → fix → create PR
```

## 📎 **Enhanced Hook System**

This export includes **{self.hooks_count} Claude Code hooks** that provide essential workflow automation with nested directory support and NUL-delimited processing for whitespace-safe file handling.

## 🔧 Installation & Setup

### Quick Start
```bash
# 1. Clone this repository to your project
git clone https://github.com/jleechanorg/claude-commands.git

# 2. Run one-click install
cd claude-commands
./install.sh

# 3. Start Claude Code with MCP servers
./claude_start.sh

# 4. Begin using composition commands
/execute "implement user authentication"
/pr "fix performance issues"
/copilot  # Fix any PR issues
```

## 🎯 Adaptation Guide

### Project-Specific Placeholders

Commands contain placeholders that need adaptation:
- `$PROJECT_ROOT/` → Your project's main directory
- `your-project.com` → Your domain/project name
- `$USER` → Your username
- `TESTING=true python` → Your test execution pattern

### Example Adaptations

**Before** (exported):
```bash
TESTING=true python $PROJECT_ROOT/test_file.py
```

**After** (adapted):
```bash
npm test src/components/test_file.js
```

## ⚠️ Important Notes

### Reference Export
This is a filtered reference export from a working Claude Code project. Commands may need adaptation for your specific environment, but Claude Code excels at helping you customize them.

### Requirements
- **Claude Code CLI** - Primary requirement for command execution
- **Git Repository Context** - Commands operate within git repositories
- **MCP Server Setup** - Some commands require MCP (Model Context Protocol) servers
- **Project-Specific Adaptation** - Paths and commands need customization for your environment

---

🚀 **Generated with [Claude Code](https://claude.ai/code)**

**Co-Authored-By: Claude <noreply@anthropic.com>**
'''

        # Ensure export directory exists
        os.makedirs(self.export_dir, exist_ok=True)

        readme_path = os.path.join(self.export_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        print("✅ Generated README.md based on current export state")

    def _create_archive(self):
        """Create compressed archive of export"""
        archive_name = f"claude_commands_export_{time.strftime('%Y%m%d_%H%M%S')}.tar.gz"
        archive_path = os.path.join(self.export_dir, archive_name)

        cmd = [
            'tar', '-czf', archive_path,
            '-C', self.export_dir,
            'staging/', 'install.sh', 'README.md'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️  Archive creation failed: {result.stderr}")
        else:
            print(f"✅ Created archive: {archive_name}")

    def phase2_github_publish(self):
        """Phase 2: Publish to GitHub with automatic PR creation"""
        print("\n🚀 Phase 2: Publishing to GitHub...")
        print("-" * 40)

        if not self.github_token:
            raise Exception("GITHUB_TOKEN environment variable not set")

        # Clone repository
        self._clone_repository()

        # Create and switch to export branch
        self._create_export_branch()

        # Copy exported content
        self._copy_to_repository()

        # Verify exclusions
        self._verify_exclusions()

        # Commit and push
        self._commit_and_push()

        # Create PR
        pr_url = self._create_pull_request()

        return pr_url

    def _clone_repository(self):
        """Clone the target repository"""
        print("📂 Cloning target repository...")

        cmd = ['gh', 'repo', 'clone', 'jleechanorg/claude-commands', self.repo_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Repository clone failed: {result.stderr}")

        print("✅ Repository cloned")

    def _create_export_branch(self):
        """Create and switch to export branch"""
        print(f"🌟 Creating export branch: {self.export_branch}")

        os.chdir(self.repo_dir)

        # Ensure we're on main and up to date
        subprocess.run(['git', 'checkout', 'main'], check=True)
        subprocess.run(['git', 'pull', 'origin', 'main'], check=True)

        # Create export branch
        subprocess.run(['git', 'checkout', '-b', self.export_branch], check=True)

        print("✅ Export branch created")

    def _copy_to_repository(self):
        """Copy exported content to repository - ADDITIVE BEHAVIOR (preserves existing)"""
        print("📋 Copying exported content (preserving existing)...")

        # 🚨 FIXED: ADDITIVE BEHAVIOR - No clearing of existing content!
        # Create target directories if they don't exist
        dirs_to_ensure = ['commands', 'hooks', 'infrastructure-scripts', 'orchestration']
        for dir_name in dirs_to_ensure:
            dir_path = os.path.join(self.repo_dir, dir_name)
            os.makedirs(dir_path, exist_ok=True)

        # Copy new content ADDITIVELY (preserves existing files)
        staging_dir = os.path.join(self.export_dir, 'staging')
        for item in os.listdir(staging_dir):
            src = os.path.join(staging_dir, item)
            dst = os.path.join(self.repo_dir, item)
            if os.path.isdir(src):
                # Copy directory contents, preserving existing files
                self._copy_directory_additive(src, dst)
            else:
                # Copy individual files (overwrites if exists, preserves others)
                shutil.copy2(src, dst)

        # Copy install script and README (these can overwrite)
        shutil.copy2(os.path.join(self.export_dir, 'install.sh'), self.repo_dir)
        shutil.copy2(os.path.join(self.export_dir, 'README.md'), self.repo_dir)

        print("✅ Content copied additively - existing commands preserved")

    def _copy_directory_additive(self, src_dir, dst_dir):
        """Copy directory contents while preserving existing files"""
        os.makedirs(dst_dir, exist_ok=True)

        for item in os.listdir(src_dir):
            src_item = os.path.join(src_dir, item)
            dst_item = os.path.join(dst_dir, item)

            if os.path.isdir(src_item):
                self._copy_directory_additive(src_item, dst_item)
            else:
                # Copy file (overwrites if exists, but preserves other files in directory)
                shutil.copy2(src_item, dst_item)
                print(f"   • Added/Updated: {item}")

        print("✅ Content copied to repository")

    def _verify_exclusions(self):
        """Verify that excluded directories are not present"""
        print("🔍 Verifying directory exclusions...")

        excluded_dirs = ['analysis', 'automation', 'claude-bot-commands', 'coding_prompts', 'prototype']
        found_excluded = []

        for dir_name in excluded_dirs:
            if os.path.exists(os.path.join(self.repo_dir, dir_name)):
                found_excluded.append(dir_name)

        if found_excluded:
            print(f"❌ ERROR: Excluded directories found: {', '.join(found_excluded)}")
            # Clean them up
            for dir_name in found_excluded:
                shutil.rmtree(os.path.join(self.repo_dir, dir_name))
            print("✅ Cleaned up excluded directories")
        else:
            print("✅ Confirmed: No excluded directories in export")

    def _commit_and_push(self):
        """Commit changes and push branch"""
        print("💾 Committing and pushing changes...")

        # Add all changes
        subprocess.run(['git', 'add', '.'], check=True)

        # Create commit message
        commit_message = f"""Fresh Claude Commands Export {time.strftime('%Y-%m-%d')}

🚨 DIRECTORY EXCLUSIONS APPLIED:
- Excluded: analysis/, automation/, claude-bot-commands/, coding_prompts/, prototype/
- These project-specific directories are filtered from exports per requirements

✅ EXPORT CONTENTS:
- 📋 Commands: {self.commands_count} command definitions with content filtering
- 📎 Hooks: {self.hooks_count} Claude Code hooks with nested structure
- 🚀 Infrastructure: {self.scripts_count} scripts for development environment management
- 🤖 Orchestration: Multi-agent task delegation system (core components only)
- 📚 Documentation: Complete README with installation guide and adaptation examples

🔄 CONTENT TRANSFORMATIONS:
- mvp_site/ → $PROJECT_ROOT/ (generic project paths)
- worldarchitect.ai → your-project.com (generic domain)
- jleechan → $USER (generic username)
- TESTING=true vpython → TESTING=true python (generic test commands)

🚀 ONE-CLICK INSTALL: ./install.sh script auto-installs to .claude/commands/ and .claude/hooks/

⚠️ Reference export - requires adaptation for other projects
🤖 Generated with Claude Code CLI"""

        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Push branch
        subprocess.run(['git', 'push', '-u', 'origin', self.export_branch], check=True)

        print("✅ Changes committed and pushed")

    def _create_pull_request(self):
        """Create pull request using GitHub API"""
        print("📝 Creating pull request...")

        pr_title = f"Claude Commands Export {time.strftime('%Y-%m-%d')}: Directory Exclusions Applied"
        pr_body = f"""**🚨 AUTOMATED EXPORT** with directory exclusions applied per requirements.

## 🎯 Directory Exclusions Applied
This export **excludes** the following project-specific directories:
- ❌ `analysis/` - Project-specific analytics and reporting
- ❌ `automation/` - Project-specific automation scripts
- ❌ `claude-bot-commands/` - Project-specific bot implementation
- ❌ `coding_prompts/` - Project-specific AI prompting templates
- ❌ `prototype/` - Project-specific experimental code

## ✅ Export Contents
- **📋 {self.commands_count} Commands**: Complete workflow orchestration system
- **📎 {self.hooks_count} Hooks**: Essential Claude Code workflow automation
- **🚀 {self.scripts_count} Infrastructure Scripts**: Development environment management
- **🤖 Orchestration System**: Core multi-agent task delegation (WIP prototype)
- **📚 Complete Documentation**: Installation guide with adaptation examples

## 🚀 One-Click Installation
```bash
./install.sh
```
Auto-installs commands to `.claude/commands/`, hooks to `.claude/hooks/`, and copies `claude_start.sh`

## 🔄 Content Filtering Applied
- **Generic Paths**: mvp_site/ → \\$PROJECT_ROOT/
- **Generic Domain**: worldarchitect.ai → your-project.com
- **Generic User**: jleechan → \\$USER
- **Generic Commands**: TESTING=true vpython → TESTING=true python

## ⚠️ Reference Export
This is a filtered reference export. Commands may need adaptation for specific environments, but Claude Code excels at helping customize them for any workflow.

---
🤖 **Generated with [Claude Code](https://claude.ai/code)**"""

        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        data = {
            'title': pr_title,
            'body': pr_body,
            'head': self.export_branch,
            'base': 'main'
        }

        response = requests.post(
            'https://api.github.com/repos/jleechanorg/claude-commands/pulls',
            headers=headers,
            json=data
        )

        if response.status_code != 201:
            raise Exception(f"PR creation failed: {response.status_code} {response.text}")

        pr_data = response.json()
        pr_url = pr_data['html_url']

        print(f"✅ Pull request created: {pr_url}")
        return pr_url

    def report_success(self, pr_url):
        """Report successful export completion"""
        print("\n🎉 EXPORT COMPLETE!")
        print("=" * 50)
        print(f"📂 Local Export: {self.export_dir}")
        archive_files = [f for f in os.listdir(self.export_dir) if f.endswith('.tar.gz')]
        if archive_files:
            print(f"📦 Archive: {archive_files[0]}")
        print(f"🌟 Branch: {self.export_branch}")
        print(f"🔗 Pull Request: {pr_url}")
        print(f"\n📊 Export Summary:")
        print(f"   Commands: {self.commands_count}")
        print(f"   Hooks: {self.hooks_count}")
        print(f"   Scripts: {self.scripts_count}")
        print(f"   Excluded: analysis/, automation/, claude-bot-commands/, coding_prompts/, prototype/")
        print(f"\n🎯 The export has been published and is ready for review!")

    def handle_error(self, error):
        """Handle export errors gracefully"""
        print(f"\n❌ Export failed: {error}")
        print(f"📂 Partial export may be available at: {self.export_dir}")
        if hasattr(self, 'repo_dir') and os.path.exists(self.repo_dir):
            print(f"🗂️  Repository clone: {self.repo_dir}")
        print("\n🔧 Debug information:")
        print(f"   Project root: {self.project_root}")
        print(f"   GitHub token set: {'Yes' if self.github_token else 'No'}")

if __name__ == "__main__":
    exporter = ClaudeCommandsExporter()
    exporter.export()
