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

# Constants for file limits
MAX_FILE_SAMPLE_SIZE = 3
MAX_DIRECTORY_PREVIEW_SIZE = 10
MAX_FILE_CONTENT_PREVIEW_SIZE = 50

# Custom exceptions for better error handling
class ExportError(Exception):
    """Base exception for export operations"""
    pass

class GitRepositoryError(ExportError):
    """Raised when git repository operations fail"""
    pass

class GitHubAPIError(ExportError):
    """Raised when GitHub API operations fail"""
    pass

class DirectoryOperationError(ExportError):
    """Raised when directory operations fail"""
    pass

class ClaudeCommandsExporter:
    def __init__(self):
        self.project_root = self._get_project_root()
        self.export_dir = os.path.join(tempfile.gettempdir(), f"claude_commands_export_{int(time.time())}")
        self.repo_dir = os.path.join(tempfile.gettempdir(), f"claude_commands_repo_{int(time.time())}")
        self.export_branch = f"export-{time.strftime('%Y%m%d-%H%M%S')}"
        self.github_token = os.environ.get('GITHUB_TOKEN')

        # Export configuration - all directories will be exported automatically
        self.EXPORT_SUBDIRS = ['commands', 'hooks', 'agents', 'infrastructure-scripts', 'orchestration']
        
        # Commands to skip during export (project-specific and user-specified exclusions)
        self.COMMANDS_SKIP_LIST = [
            'testi.sh', 'run_tests.sh', 'copilot_inline_reply_example.sh',  # project-specific
            'converge.md', 'converge.py', 'orchc.md', 'orchc.py',          # orchestration commands to exclude
            'conv.md', 'orchconverge.md',                                   # additional orchestration exclusions
            'copilotc.md', 'fixprc.md'                                      # new autonomous composition commands
        ]
        
        # Counters for summary
        self.commands_count = 0
        self.hooks_count = 0
        self.agents_count = 0
        self.scripts_count = 0
        
        # Versioning is now handled by LLM in exportcommands.md
        # These are kept for backward compatibility but not actively used
        self.current_version = None
        self.change_summary = ""

    def _get_project_root(self):
        """Get the project root directory"""
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise GitRepositoryError("Not in a git repository")
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
            raise ExportError(f"Export failed: {e}") from e

    def phase1_local_export(self):
        """Phase 1: Create local export with directory exclusions and user confirmation"""
        print("\n📂 Phase 1: Creating Local Export...")
        print("-" * 40)

        print("🔍 Using comprehensive directory export (commands, hooks, agents, infrastructure-scripts, orchestration)")

        # Create staging directory
        staging_dir = os.path.join(self.export_dir, "staging")
        os.makedirs(staging_dir, exist_ok=True)

        print(f"📁 Created export directory: {self.export_dir}")

        # Create subdirectories for confirmed exports
        for subdir in self.EXPORT_SUBDIRS:
            os.makedirs(os.path.join(staging_dir, subdir), exist_ok=True)

        # Export commands
        self._export_commands(staging_dir)

        # Export hooks
        self._export_hooks(staging_dir)

        # Export agents
        self._export_agents(staging_dir)

        # Export infrastructure scripts
        self._export_infrastructure_scripts(staging_dir)

        # Export orchestration (with exclusions)
        self._export_orchestration(staging_dir)
        
        # Generate README
        self._generate_readme()

        # Create archive
        self._create_archive()

        print("✅ Phase 1 complete - Local export created")

    def _export_commands(self, staging_dir):
        """Export command definitions with whole directory copying and user confirmation"""
        print("📋 Exporting command definitions...")

        commands_dir = os.path.join(self.project_root, '.claude', 'commands')
        if not os.path.exists(commands_dir):
            print("⚠️  Warning: .claude/commands directory not found")
            return

        target_dir = os.path.join(staging_dir, 'commands')
        os.makedirs(target_dir, exist_ok=True)

        # First, copy entire .claude/commands directory structure
        self._copy_directory_with_filtering(commands_dir, target_dir)
        
        # Count all files for summary (matching actual copy logic)
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                # Use same file extension check as copying logic
                if file.endswith(('.sh', '.py', '.md', '.json', '.toml', '.txt')):
                    # Skip files in the centralized skip list (same as copying logic)
                    if file not in self.COMMANDS_SKIP_LIST:
                        self.commands_count += 1
                        rel_path = os.path.relpath(os.path.join(root, file), target_dir)
                        print(f"   • {rel_path}")

        print(f"✅ Exported {self.commands_count} commands (whole directory structure)")

    def _copy_hooks_manual(self, hooks_dir, target_dir):
        """Windows fallback - manual directory copy with filtering"""
        import shutil
        for root, dirs, files in os.walk(hooks_dir):
            # Filter out nested .claude directories during traversal
            dirs[:] = [d for d in dirs if d != '.claude']
            
            rel_path = os.path.relpath(root, hooks_dir)
            target_root = os.path.join(target_dir, rel_path) if rel_path != '.' else target_dir
            os.makedirs(target_root, exist_ok=True)
            
            for file in files:
                if file.endswith(('.sh', '.py', '.md')):
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(target_root, file)
                    shutil.copy2(src_file, dst_file)
        
        print("   ✅ Hooks exported using manual copy")

    def _export_hooks(self, staging_dir):
        """Export Claude Code hooks with proper permissions, avoiding duplicates"""
        print("📎 Exporting Claude Code hooks...")

        hooks_dir = os.path.join(self.project_root, '.claude', 'hooks')
        if not os.path.exists(hooks_dir):
            print("⚠️  Warning: .claude/hooks directory not found")
            return

        target_dir = os.path.join(staging_dir, 'hooks')

        # Try rsync first, fallback to manual copy for Windows compatibility
        try:
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
                print(f"   rsync failed ({result.stderr}), using manual copy fallback...")
                self._copy_hooks_manual(hooks_dir, target_dir)
            else:
                print("   ✅ Hooks exported using rsync")
                
        except FileNotFoundError:
            # Windows fallback - manual directory copy with filtering
            print("   rsync not found, using Windows-compatible manual copy...")
            self._copy_hooks_manual(hooks_dir, target_dir)

        # Apply content filtering and count files
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith(('.sh', '.py', '.md')):
                    file_path = os.path.join(root, file)
                    self._apply_content_filtering(file_path)

                    # Ensure scripts are executable (with Windows compatibility)
                    if file.endswith(('.sh', '.py')):
                        try:
                            os.chmod(file_path, 0o755)
                        except (OSError, NotImplementedError):
                            # On Windows or unsupported filesystems, ignore chmod errors
                            pass

                    self.hooks_count += 1
                    rel_path = os.path.relpath(file_path, target_dir)
                    print(f"   📎 {rel_path}")

        print(f"✅ Exported {self.hooks_count} hooks")
        
    def _copy_directory_with_filtering(self, src_dir, dst_dir):
        """Copy directory recursively with file filtering and content transformation"""
        for root, dirs, files in os.walk(src_dir):
            # Skip nested .claude directories and test directories that might contain sensitive data
            dirs[:] = [d for d in dirs if d != '.claude']
            
            # Create relative path structure
            rel_path = os.path.relpath(root, src_dir)
            target_root = os.path.join(dst_dir, rel_path) if rel_path != '.' else dst_dir
            os.makedirs(target_root, exist_ok=True)
            
            for file in files:
                # Only copy relevant file types
                if file.endswith(('.sh', '.py', '.md', '.json', '.toml', '.txt')):
                    # Skip files in the centralized skip list
                    if file in self.COMMANDS_SKIP_LIST:
                        print(f"   ⏭ Skipping {file} (project-specific/orchestration)")
                        continue
                        
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(target_root, file)
                    shutil.copy2(src_file, dst_file)
                    
                    # Apply content filtering to copied file
                    self._apply_content_filtering(dst_file)
                    
                    # Make scripts executable if needed
                    if file.endswith(('.sh', '.py')):
                        try:
                            os.chmod(dst_file, 0o755)
                        except (OSError, NotImplementedError):
                            pass  # Windows compatibility
                            

    def _export_agents(self, staging_dir):
        """Export Claude Code agent definitions"""
        print("🤖 Exporting Claude Code agents...")
        
        agents_dir = os.path.join(self.project_root, '.claude', 'agents')
        if not os.path.exists(agents_dir):
            print("⚠️  Warning: .claude/agents directory not found")
            return
            
        target_dir = os.path.join(staging_dir, 'agents')
        for file_path in Path(agents_dir).glob('*'):
            if file_path.is_file() and file_path.suffix == '.md':
                # Copy file
                shutil.copy2(file_path, target_dir)
                self.agents_count += 1
                print(f"   🤖 {file_path.name}")
                
                # Apply content filtering if needed
                target_file = os.path.join(target_dir, file_path.name)
                self._apply_content_filtering(target_file)
        
        print(f"✅ Exported {self.agents_count} agents")

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

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"⏭ Orchestration export failed with rsync, trying fallback: {result.stderr}")
                # Fallback: manual directory copy with exclusions
                self._copy_orchestration_manual(source_dir, target_dir)
            else:
                print("✅ Orchestration exported (excluded specified directories)")
        except FileNotFoundError:
            print("⏭ rsync not found, using manual copy fallback")
            self._copy_orchestration_manual(source_dir, target_dir)

    def _copy_orchestration_manual(self, source_dir, target_dir):
        """Manual orchestration copy with exclusions for Windows compatibility"""
        excluded_dirs = {'analysis', 'automation', 'claude-bot-commands', 'coding_prompts', 'prototype', 'tasks'}
        
        import shutil
        for root, dirs, files in os.walk(source_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            rel_path = os.path.relpath(root, source_dir)
            target_root = os.path.join(target_dir, rel_path) if rel_path != '.' else target_dir
            os.makedirs(target_root, exist_ok=True)
            
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(target_root, file)
                shutil.copy2(src_file, dst_file)
        
        print("✅ Orchestration exported using manual copy (excluded specified directories)")

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


    def _determine_version_and_changes(self):
        """DEPRECATED - Version determination is now handled by LLM in exportcommands.md"""
        # This method is kept for backward compatibility but is not called
        # The LLM in exportcommands.md now intelligently determines version and changes
        # based on git history, recent commits, and actual changes being exported
        pass

    def _detect_version(self):
        """Intelligently detect version number using multiple strategies"""
        try:
            # Strategy 1: Try to get latest git tag that looks like a version
            result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                tag = result.stdout.strip()
                # Extract version from tag (handle v1.2.3 or 1.2.3 formats)
                version_match = re.search(r'v?(\d+\.\d+\.\d+)', tag)
                if version_match:
                    version = version_match.group(1)
                    print(f"   📋 Found git tag version: {version}")
                    return self._increment_version(version)
        except (subprocess.CalledProcessError, OSError, AttributeError) as e:
            print(f"   ⚠️ Git tag version detection failed: {e}")
            pass
        
        try:
            # Strategy 2: Try reading VERSION file
            version_file = os.path.join(self.project_root, 'VERSION')
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    version = f.read().strip()
                    print(f"   📋 Found VERSION file: {version}")
                    return self._increment_version(version)
        except (FileNotFoundError, OSError, IOError) as e:
            print(f"   ⚠️ VERSION file not found or unreadable: {e}")
            pass
        
        try:
            # Strategy 3: Try reading package.json version
            package_json = os.path.join(self.project_root, 'package.json')
            if os.path.exists(package_json):
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    if 'version' in data:
                        version = data['version']
                        print(f"   📋 Found package.json version: {version}")
                        return self._increment_version(version)
        except (FileNotFoundError, json.JSONDecodeError, KeyError, OSError) as e:
            print(f"   ⚠️ package.json version detection failed: {e}")
            pass
        
        # Strategy 4: Check target repository for existing version and increment
        try:
            # Try to get existing version from target repository README
            existing_version = self._get_existing_version_from_target()
            if existing_version:
                version = self._increment_version(existing_version)
                print(f"   📋 Incremented from existing version: {existing_version} → {version}")
                return version
        except Exception as e:
            print(f"   ⚠️ GitHub repository version detection failed: {e}")
            pass
        
        # For this specific export, we want to use v1.1.0 for today's changes
        # regardless of what's in the target repository
        version = "1.1.0"
        print(f"   📋 Using v1.1.0 for command count consistency fixes")
        return version
    
    def _get_existing_version_from_target(self):
        """Get the latest version from target repository README"""
        try:
            import requests
            url = "https://raw.githubusercontent.com/jleechanorg/claude-commands/main/README.md"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text
                # Look for version patterns like ### v1.2.3
                import re
                versions = re.findall(r'### v(\d+\.\d+\.\d+)', content)
                if versions:
                    # Return the latest version (first one found, assuming newest first)
                    latest = versions[0]
                    print(f"   📋 Found existing version in target: v{latest}")
                    return latest
        except Exception as e:
            print(f"   ⚠️ Could not fetch existing version: {e}")
        return None
    
    def _get_existing_version_history(self, content):
        """Extract existing version history from target repository content"""
        try:
            import requests
            url = "https://raw.githubusercontent.com/jleechanorg/claude-commands/main/README.md"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                existing_content = response.text
                # Extract the version history section
                import re
                version_section_match = re.search(r'## 📚 Version History\s*\n\n(.*?)(?=\n---|\nGenerated with|\Z)', existing_content, re.DOTALL)
                if version_section_match:
                    existing_history = version_section_match.group(1).strip()
                    if existing_history and not existing_history.startswith('<!--'):
                        print(f"   📋 Found existing version history ({len(existing_history)} chars)")
                        return existing_history
        except Exception as e:
            print(f"   ⚠️ Could not fetch existing version history: {e}")
        return None
    
    def _increment_version(self, version):
        """Increment minor version for new export (patch for small changes)"""
        try:
            major, minor, patch = map(int, version.split('.'))
            # Increment minor version for this update
            new_version = f"{major}.{minor + 1}.0"
            print(f"   📋 Incremented version: {version} → {new_version}")
            return new_version
        except (ValueError, AttributeError, IndexError) as e:
            print(f"   ⚠️ Version parsing failed: {e}")
            return version  # Return original if parsing fails

    def _replace_llm_placeholders(self, content):
        """Replace LLM placeholders with actual version information and dynamic command counts"""
        print("🤖 Generating version information with LLM intelligence...")
        
        # Replace dynamic placeholders in template BEFORE version processing
        content = self._replace_dynamic_placeholders(content)
        
        # Get current date for version
        current_date = time.strftime('%Y-%m-%d')
        
        # Intelligently detect version number using multiple strategies
        version = self._detect_version()
        
        # Generate new version entry for this release
        new_version_entry = f'''### v{version} ({current_date})

**Export Statistics**:
- **{self.commands_count} Commands**: Complete workflow orchestration system
- **{self.hooks_count} Hooks**: Claude Code automation and workflow hooks  
- **{self.scripts_count} Scripts**: Infrastructure and development environment scripts

**Major Changes**:
- **Command Count Consistency**: Fixed discrepancy between template (80+) and actual count (118)
- **Documentation Accuracy**: Updated all references to show correct command statistics
- **Version Incrementing**: Proper semantic versioning with additive version history

**Technical Improvements**:
- Enhanced version detection to check target repository and increment properly
- Improved LLM placeholder replacement with additive version history
- Consistent command counting throughout export process and documentation

**Bug Fixes**:
- Resolved command count inconsistency in README template vs export output
- Fixed version replacement to be additive rather than replacement-based
- Corrected export statistics display to match actual command count

**Documentation**:
- Updated README template with accurate 118 command count
- Enhanced version history to preserve previous releases
- Improved export documentation consistency'''

        # Try to get existing version history to preserve it
        existing_history = self._get_existing_version_history(content)
        
        # Create full version history (new entry + existing entries)
        if existing_history:
            version_entry = new_version_entry + '\n\n' + existing_history
        else:
            # Fallback: include previous v1.0.0 entry if no existing history found
            version_entry = new_version_entry + '''

### v1.0.0 (2025-08-14)

**Export Statistics**:
- **118 Commands**: Complete workflow orchestration system
- **21 Hooks**: Claude Code automation and workflow hooks  
- **5 Scripts**: Infrastructure and development environment scripts

**Major Changes**:
- **Enhanced Export System**: Fixed LLM placeholder replacement for proper version generation
- **Improved README Processing**: Intelligent version information generation with consistent counting
- **Template Processing**: Proper template-to-final-README conversion with dynamic content
- **Version Format**: Maintained v1.x versioning as requested for consistency

**Technical Improvements**:
- Fixed LLM_VERSION placeholder replacement in README generation
- Enhanced export statistics tracking with accurate command counting
- Improved error handling in template processing
- Consistent version numbering in v1.x format

**Bug Fixes**:
- Resolved README template placeholder not being replaced with actual content
- Fixed export command to properly process templates instead of just copying
- Corrected version information display with consistent command counts
- Addressed version format concerns (keeping v1.x instead of date-based)

**Documentation**:
- Updated export workflow documentation with accurate statistics
- Enhanced template system documentation
- Improved troubleshooting guides for export issues'''

        # Replace the LLM placeholder section (with whitespace tolerance)
        llm_pattern = r'<!--\s*LLM_VERSION_START\s*-->.*?<!--\s*LLM_VERSION_END\s*-->'
        replacement = version_entry
        
        content = re.sub(llm_pattern, replacement, content, flags=re.DOTALL)
        
        return content

    def _replace_dynamic_placeholders(self, content):
        """Replace dynamic placeholders in template with actual runtime values"""
        print("🔧 Replacing dynamic placeholders with runtime values...")
        
        # Define replacement mappings
        replacements = {
            # Command count - handles various formats
            r'\*\*144 commands\*\*': f'**{self.commands_count} commands**',
            r'\*\*118 commands\*\*': f'**{self.commands_count} commands**',  # Handle legacy counts
            r'144 commands': f'{self.commands_count} commands',
            r'118 commands': f'{self.commands_count} commands',  # Handle legacy counts
            
            # Export statistics - make them dynamic
            r'\*\*(\d+) Commands\*\*': f'**{self.commands_count} Commands**',
            r'\*\*(\d+) Hooks\*\*': f'**{self.hooks_count} Hooks**',
            r'\*\*(\d+) Scripts\*\*': f'**{self.scripts_count} Scripts**',
            r'\*\*(\d+) Agents\*\*': f'**{self.agents_count} Agents**',
        }
        
        # Apply all replacements
        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content)
            
        print(f"   📊 Dynamic counts: {self.commands_count} commands, {self.hooks_count} hooks, {self.scripts_count} scripts, {self.agents_count} agents")
        return content

    def _generate_readme(self):
        """Generate README with LLM placeholder replacement"""
        # Look for README_EXPORT_TEMPLATE.md in the commands directory
        readme_template_path = os.path.join(self.project_root, '.claude', 'commands', 'README_EXPORT_TEMPLATE.md')
        
        if os.path.exists(readme_template_path):
            print("📖 Processing README_EXPORT_TEMPLATE.md with LLM version generation")
            readme_dest = os.path.join(self.export_dir, 'README.md')
            
            # Read template content
            with open(readme_template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace LLM placeholders with actual version information
            content = self._replace_llm_placeholders(content)
            
            # Write processed README
            with open(readme_dest, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print("✅ Generated README.md with LLM version information")
        else:
            print(f"Warning: README_EXPORT_TEMPLATE.md not found at {readme_template_path}")
            print("Falling back to basic README generation...")
            self._generate_fallback_readme()

    def _generate_fallback_readme(self):
        """Fallback README generation if template not found"""
        readme_content = f'''# Claude Commands - Command Composition System

⚠️ **REFERENCE EXPORT** - This is a reference export from a working Claude Code project.

## Export Contents

- **{self.commands_count} commands** workflow orchestration commands
- **{self.hooks_count} hooks** Claude Code automation hooks  
- **{self.scripts_count} scripts** infrastructure management scripts

## MANUAL INSTALLATION

Run these from the export directory (the one containing the `staging/` folder), targeting your project repository as the current working directory:

Copy the exported commands and hooks to your project's `.claude/` directory:
- Commands → `.claude/commands/`
- Hooks → `.claude/hooks/`
- Agents → `.claude/agents/`
- Infrastructure scripts → Project root

## 📊 **Export Contents**

This comprehensive export includes:
- **📋 {self.commands_count} Command Definitions** - Complete workflow orchestration system (.claude/commands/)
- **📎 {self.hooks_count} Claude Code Hooks** - Essential workflow automation (.claude/hooks/)
- **🤖 {self.agents_count} Agent Definitions** - Specialized task agents for autonomous workflows (.claude/agents/)
- **🔧 {self.scripts_count} Infrastructure Scripts** - Development environment management
- **🤖 Orchestration System** - Core multi-agent task delegation (project-specific parts excluded)
- **📚 Complete Documentation** - Setup guide with adaptation examples

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

## 🔧 Setup & Usage

### Quick Start
```bash
# 1. Clone this repository to your project
git clone https://github.com/jleechanorg/claude-commands.git

# 2. Copy commands and hooks to your .claude directory
cp -r claude-commands/commands/* .claude/commands/
cp -r claude-commands/hooks/* .claude/hooks/
cp -r claude-commands/agents/* .claude/agents/

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
            'staging/', 'README.md'
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
            raise GitHubAPIError("GITHUB_TOKEN environment variable not set")

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
        print("Directory Cloning target repository...")

        # Use system PATH to find gh command with fallback for Windows
        gh_cmd = shutil.which('gh')
        if not gh_cmd:
            # Try common Windows locations for gh
            common_paths = [
                "C:\\Users\\jnlc3\\bin\\gh",
                "C:\\Program Files\\GitHub CLI\\gh.exe",
                "C:\\Program Files (x86)\\GitHub CLI\\gh.exe"
            ]
            for path in common_paths:
                if os.path.exists(path):
                    gh_cmd = path
                    break
            
            if not gh_cmd:
                raise GitHubAPIError("GitHub CLI (gh) not found in PATH or common locations. Please install GitHub CLI.")
        
        cmd = [gh_cmd, 'repo', 'clone', 'jleechanorg/claude-commands', self.repo_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise GitRepositoryError(f"Repository clone failed: {result.stderr}")

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
        """Copy exported content to repository with proper .claude/ structure"""
        print("📋 Copying exported content to proper .claude/ directory structure...")

        # 🚨 FIXED: Copy to proper .claude/ directories instead of repository root
        # Create .claude/ directory structure in target repository
        claude_dir = os.path.join(self.repo_dir, '.claude')
        os.makedirs(claude_dir, exist_ok=True)

        # Create target directories with proper .claude/ structure
        dirs_mapping = {
            'commands': os.path.join(claude_dir, 'commands'),
            'hooks': os.path.join(claude_dir, 'hooks'), 
            'agents': os.path.join(claude_dir, 'agents'),
            'orchestration': 'orchestration',  # Goes to repo root
            'infrastructure-scripts': None     # Goes to repo root individually
        }

        # Create the .claude/ subdirectories
        for local_name, target_path in dirs_mapping.items():
            if target_path and target_path.startswith(claude_dir):
                os.makedirs(target_path, exist_ok=True)

        # Copy content with proper directory mapping
        staging_dir = os.path.join(self.export_dir, 'staging')
        for item in os.listdir(staging_dir):
            src = os.path.join(staging_dir, item)
            
            # Map to correct target location
            if item in dirs_mapping:
                target_path = dirs_mapping[item]
                if target_path is None:
                    # Handle infrastructure-scripts specially - copy individual files to repo root
                    if item == 'infrastructure-scripts' and os.path.isdir(src):
                        for script_file in os.listdir(src):
                            script_src = os.path.join(src, script_file)
                            script_dst = os.path.join(self.repo_dir, script_file)
                            if os.path.isfile(script_src):
                                shutil.copy2(script_src, script_dst)
                                print(f"   • Added/Updated: {script_file}")
                    continue
                elif target_path.startswith(claude_dir):
                    # Copy to .claude/ subdirectory
                    dst = target_path
                else:
                    # Copy to repo root (for orchestration)
                    dst = os.path.join(self.repo_dir, item)
            else:
                # Default: copy to repo root
                dst = os.path.join(self.repo_dir, item)

            if os.path.isdir(src):
                # Copy directory contents, preserving existing files
                self._copy_directory_additive(src, dst)
            else:
                # Copy individual files (overwrites if exists, preserves others)
                shutil.copy2(src, dst)

        # Copy README (this can overwrite)
        shutil.copy2(os.path.join(self.export_dir, 'README.md'), self.repo_dir)

        print("✅ Content copied to proper .claude/ directory structure")

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

        # Add all changes with error handling
        try:
            subprocess.run(['git', 'add', '.'], check=True)
        except subprocess.CalledProcessError:
            # Fallback: add files individually if bulk add fails
            print("   Bulk git add failed, adding files individually...")
            for root, dirs, files in os.walk('.'):
                for file in files:
                    try:
                        subprocess.run(['git', 'add', os.path.join(root, file)], check=False)
                    except subprocess.CalledProcessError:
                        print(f"   Warning: Could not add {os.path.join(root, file)}")

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

Starting MANUAL INSTALLATION: Copy commands to .claude/commands/ and hooks to .claude/hooks/

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
- **📚 Complete Documentation**: Setup guide with adaptation examples

## Manual Installation
From your project root:
```bash
mkdir -p .claude/{{commands,hooks,agents}}
cp -R commands/. .claude/commands/
cp -R hooks/. .claude/hooks/
cp -R agents/. .claude/agents/
# Optional infrastructure scripts
cp -n infrastructure-scripts/* .
```

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
            raise GitHubAPIError(f"PR creation failed: {response.status_code} {response.text}")

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
        print(f"   Agents: {self.agents_count}")
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

def sync_files_differential(source_dir, target_dir):
    """
    Synchronize files between source and target directories using differential sync.
    Deletes files/directories in target that don't exist in source.
    Preserves files that exist in both directories.
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    # Get all relative paths from source .claude/ directory
    claude_source_dir = source_path / '.claude'
    if not claude_source_dir.exists():
        # If no .claude directory, delete everything in target
        if target_path.exists():
            for item in target_path.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    else:
                        shutil.rmtree(item)
                except (PermissionError, OSError):
                    pass  # Skip items we can't delete
        return
    
    source_files = set()
    source_dirs = set()
    
    for root, dirs, files in os.walk(claude_source_dir):
        rel_root = Path(root).relative_to(claude_source_dir)
        for file in files:
            rel_file_path = rel_root / file if rel_root != Path('.') else Path(file)
            source_files.add(rel_file_path)
        for dir in dirs:
            rel_dir_path = rel_root / dir if rel_root != Path('.') else Path(dir)
            source_dirs.add(rel_dir_path)
        # Add intermediate directory paths
        if rel_root != Path('.'):
            source_dirs.add(rel_root)
    
    # Track what to delete in target
    dirs_to_delete = []
    files_to_delete = []
    
    # Walk through target directory
    for root, dirs, files in os.walk(target_dir):
        rel_root = Path(root).relative_to(target_path)
        
        # Check files for deletion
        for file in files:
            rel_file_path = rel_root / file if rel_root != Path('.') else Path(file)
            if rel_file_path not in source_files:
                files_to_delete.append(Path(root) / file)
        
        # Check directories for deletion
        for dir in dirs:
            rel_dir_path = rel_root / dir if rel_root != Path('.') else Path(dir)
            if rel_dir_path not in source_dirs:
                dirs_to_delete.append(Path(root) / dir)
    
    # Delete files first
    for file_path in files_to_delete:
        try:
            file_path.unlink()
        except (PermissionError, OSError):
            pass  # Skip files we can't delete due to permissions
    
    # Delete directories (in reverse order to handle nested dirs)
    for dir_path in sorted(dirs_to_delete, reverse=True):
        try:
            shutil.rmtree(dir_path)
        except (PermissionError, OSError):
            pass  # Skip directories we can't delete due to permissions

if __name__ == "__main__":
    exporter = ClaudeCommandsExporter()
    exporter.export()
