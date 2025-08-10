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
        
        # Versioning for change history
        self.current_version = None
        self.change_summary = ""

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
            print("Starting Claude Commands Export...")
            print("=" * 50)

            self.phase1_local_export()
            pr_url = self.phase2_github_publish()
            self.report_success(pr_url)

        except Exception as e:
            self.handle_error(e)
            sys.exit(1)

    def phase1_local_export(self):
        """Phase 1: Create local export with directory exclusions"""
        print("\nPhase 1: Creating Local Export...")
        print("-" * 40)

        # Create staging directory
        staging_dir = os.path.join(self.export_dir, "staging")
        os.makedirs(staging_dir, exist_ok=True)

        print(f" Created export directory: {self.export_dir}")

        # Create subdirectories
        subdirs = ['commands', 'hooks', 'infrastructure-scripts', 'orchestration']
        for subdir in subdirs:
            os.makedirs(os.path.join(staging_dir, subdir), exist_ok=True)

        # Export commands
        self._export_commands(staging_dir)

        # Export hooks
        self._export_hooks(staging_dir)

        # Export settings configuration
        self._export_settings_configuration(staging_dir)

        # Export infrastructure scripts
        self._export_infrastructure_scripts(staging_dir)

        # Export orchestration (with exclusions)
        self._export_orchestration(staging_dir)
        self._generate_readme()

        # Create archive
        self._create_archive()

        print("Success Phase 1 complete - Local export created")

    def _export_commands(self, staging_dir):
        """Export command definitions with content filtering"""
        print("Commands Exporting command definitions...")

        commands_dir = os.path.join(self.project_root, '.claude', 'commands')
        if not os.path.exists(commands_dir):
            print("Warning  Warning: .claude/commands directory not found")
            return

        target_dir = os.path.join(staging_dir, 'commands')

        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)

        for file_path in Path(commands_dir).glob('*'):
            if file_path.is_file() and file_path.suffix in ['.md', '.py']:
                filename = file_path.name

                # Skip project-specific files
                if filename in ['testi.sh', 'run_tests.sh', 'copilot_inline_reply_example.sh']:
                    print(f"   SKIP Skipping {filename} (project-specific)")
                    continue

                target_path = os.path.join(target_dir, filename)
                shutil.copy2(file_path, target_path)

                # Apply content transformations
                self._apply_content_filtering(target_path)

                print(f"    {filename}")
                self.commands_count += 1

        print(f"Success Exported {self.commands_count} commands")

    def _export_hooks(self, staging_dir):
        """Export Claude Code hooks with proper permissions, avoiding duplicates"""
        print("Hooks Exporting Claude Code hooks...")

        hooks_dir = os.path.join(self.project_root, '.claude', 'hooks')
        if not os.path.exists(hooks_dir):
            print("Warning  Warning: .claude/hooks directory not found")
            return

        target_dir = os.path.join(staging_dir, 'hooks')

        # Windows-compatible fallback - use shutil instead of rsync
        try:
            # Try rsync first (if available)
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
                raise Exception("rsync failed, using fallback")
                
        except:
            # Windows fallback - manual directory copy with filtering
            print("   Using Windows-compatible fallback...")
            self._copy_hooks_manual(hooks_dir, target_dir)

        # Apply content filtering and count files
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith(('.sh', '.py', '.md')):
                    file_path = os.path.join(root, file)
                    self._apply_content_filtering(file_path)

                    # Ensure scripts are executable
                    if file.endswith(('.sh', '.py')):
                        try:
                            os.chmod(file_path, 0o755)
                        except:
                            pass  # Windows may not support chmod

                    self.hooks_count += 1
                    rel_path = os.path.relpath(file_path, target_dir)
                    print(f"   Hooks {rel_path}")

        print(f"Success Exported {self.hooks_count} hooks")

    def _copy_hooks_manual(self, src_dir, dst_dir):
        """Manual hooks copy for Windows compatibility"""
        os.makedirs(dst_dir, exist_ok=True)
        
        for root, dirs, files in os.walk(src_dir):
            # Skip nested .claude directories
            dirs[:] = [d for d in dirs if d != '.claude']
            
            for file in files:
                if file.endswith(('.sh', '.py', '.md')):
                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(src_file, src_dir)
                    dst_file = os.path.join(dst_dir, rel_path)
                    
                    # Create directory structure
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(src_file, dst_file)

    def _export_settings_configuration(self, staging_dir):
        """Export filtered Claude Code settings configuration"""
        print("Settings Exporting Claude Code hook configuration...")
        
        settings_source = os.path.join(self.project_root, '.claude', 'settings.json')
        
        if not os.path.exists(settings_source):
            print("Warning  No .claude/settings.json found - skipping configuration export")
            return
            
        try:
            import json
            
            # Read current settings
            with open(settings_source, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Create export-safe configuration (hooks only, no sensitive permissions)
            export_settings = {
                "hooks": settings.get("hooks", {})
            }
            
            # Add installation note
            export_settings["_installation_note"] = "Generated by /exportcommands - Essential hook configuration for Claude Code workflow automation"
            
            # Write to staging
            settings_path = os.path.join(staging_dir, 'claude-settings.json')
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(export_settings, f, indent=2)
            
            print("Success Exported hook configuration to claude-settings.json")
            
        except Exception as e:
            print(f"Warning  Settings export failed: {e}")

    def _export_infrastructure_scripts(self, staging_dir):
        """Export root-level infrastructure scripts"""
        print("Starting Exporting infrastructure scripts...")

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

                print(f"    {script_name}")
                self.scripts_count += 1

        print(f"Success Exported {self.scripts_count} infrastructure scripts")

    def _export_orchestration(self, staging_dir):
        """Export orchestration system with directory exclusions"""
        print("Orchestration Exporting orchestration system (with exclusions)...")

        source_dir = os.path.join(self.project_root, 'orchestration')
        if not os.path.exists(source_dir):
            print("Warning  Orchestration directory not found - skipping")
            return

        target_dir = os.path.join(staging_dir, 'orchestration')

        try:
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
                raise Exception("rsync failed, using fallback")
        except:
            # Windows fallback - manual directory copy with exclusions
            print("   Using Windows-compatible fallback...")
            self._copy_orchestration_manual(source_dir, target_dir)

        print("Success Orchestration exported (excluded specified directories)")

    def _copy_orchestration_manual(self, src_dir, dst_dir):
        """Manual orchestration copy for Windows compatibility"""
        os.makedirs(dst_dir, exist_ok=True)
        
        excluded_dirs = {'analysis', 'automation', 'claude-bot-commands', 'coding_prompts', 'prototype', 'tasks'}
        
        for root, dirs, files in os.walk(src_dir):
            # Remove excluded directories from traversal
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, src_dir)
                dst_file = os.path.join(dst_dir, rel_path)
                
                # Create directory structure
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                
                # Copy file
                shutil.copy2(src_file, dst_file)

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
            print(f"Warning  Warning: Content filtering failed for {file_path}: {e}")

    def _determine_version_and_changes(self):
        """Determine version number - Python handles version, LLM handles changes"""
        print("Versioning Analyzing version history...")
        
        # Check if we're in the cloned repo directory
        if not os.path.exists('README.md'):
            # First export
            self.current_version = "v1.0.0"
            self.change_summary = "Initial command system export"
            print(f"   First export detected - Version: {self.current_version}")
            return
            
        try:
            with open('README.md', 'r', encoding='utf-8') as f:
                current_readme = f.read()
        except:
            self.current_version = "v1.0.0" 
            self.change_summary = "Initial command system export"
            return
            
        # Extract last version from README
        version_pattern = r'## Version History.*?###\s+([vV]?[\d\.]+)'
        version_matches = re.findall(version_pattern, current_readme, re.DOTALL | re.IGNORECASE)
        
        if version_matches:
            last_version = version_matches[0].replace('v', '').replace('V', '')
            # Increment minor version
            parts = last_version.split('.')
            if len(parts) >= 2:
                minor = int(parts[1]) + 1
                self.current_version = f"v{parts[0]}.{minor}.0"
            else:
                self.current_version = "v1.1.0"
        else:
            self.current_version = "v1.1.0"
            
        # Generate meaningful change summary based on current export
        changes = []
        if self.commands_count >= 100:
            changes.append(f"Comprehensive command system ({self.commands_count} commands)")
        if self.hooks_count >= 10:
            changes.append(f"Enhanced hook automation ({self.hooks_count} hooks)")
        if self.scripts_count >= 5:
            changes.append(f"Infrastructure automation ({self.scripts_count} scripts)")
        
        # Add feature-specific changes
        changes.extend([
            "Template-based README generation with dynamic content",
            "Obsolete file cleanup and maintenance",
            "Additive export strategy preserving existing content",
            "Enhanced content filtering and path normalization",
            "Version tracking and change history management"
        ])
        
        self.change_summary = " - ".join(changes)
        
        print(f"   Version: {self.current_version}")
        print(f"   Changes: {self.change_summary}")
        

    def _generate_readme(self):
        """Generate comprehensive README using README_EXPORT_TEMPLATE.md with dynamic counts"""
        # Determine version and changes before generating README
        self._determine_version_and_changes()
        
        # Read the README_EXPORT_TEMPLATE.md from source project
        template_path = os.path.join(self.project_root, '.claude', 'commands', 'README_EXPORT_TEMPLATE.md')
        if not os.path.exists(template_path):
            print(f"Warning: README_EXPORT_TEMPLATE.md not found at {template_path}")
            print("Falling back to basic README generation...")
            self._generate_fallback_readme()
            return
            
        print("📖 Using README_EXPORT_TEMPLATE.md for enhanced export documentation")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        # Replace dynamic placeholders with actual counts
        # FIXED: Order matters - general replacement first, then specific replacements
        readme_content = readme_content.replace('**80+ commands**', f'**{self.commands_count} commands**')
        readme_content = readme_content.replace('This export contains **80+ commands**', f'This export contains **{self.commands_count} commands**')
        
        # Version history is now manually maintained in README_EXPORT_TEMPLATE.md
        # No dynamic version history generation to avoid deletion issues
        
        # Write the enhanced README
        readme_path = os.path.join(self.export_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        print("Success Generated README.md using README_EXPORT_TEMPLATE.md")

    def _generate_fallback_readme(self):
        """Fallback README generation if template not found"""
        readme_content = f'''# Claude Commands - Command Composition System

⚠️ **REFERENCE EXPORT** - This is a reference export from a working Claude Code project.

## Export Contents

- **Commands**: {self.commands_count} workflow orchestration commands
- **Hooks**: {self.hooks_count} Claude Code automation hooks  
- **Scripts**: {self.scripts_count} infrastructure management scripts

## Installation

```bash
./install.sh
```

Auto-installs to `.claude/commands/` and `.claude/hooks/`
'''

        readme_path = os.path.join(self.export_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        print("Success Generated fallback README.md")

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
            print(f"Warning  Archive creation failed: {result.stderr}")
        else:
            print(f"Success Created archive: {archive_name}")

    def phase2_github_publish(self):
        """Phase 2: Publish to GitHub with automatic PR creation"""
        print("\nStarting Phase 2: Publishing to GitHub...")
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
                raise Exception("GitHub CLI (gh) not found in PATH or common locations. Please install GitHub CLI.")
        
        cmd = [gh_cmd, 'repo', 'clone', 'jleechanorg/claude-commands', self.repo_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Repository clone failed: {result.stderr}")

        print("Success Repository cloned")

    def _create_export_branch(self):
        """Create and switch to export branch"""
        print(f"Branch Creating export branch: {self.export_branch}")

        os.chdir(self.repo_dir)

        # Set git identity for commits
        subprocess.run(['git', 'config', 'user.email', 'noreply@anthropic.com'], check=True)
        subprocess.run(['git', 'config', 'user.name', 'Claude Code Export'], check=True)

        # Ensure we're on main and up to date
        subprocess.run(['git', 'checkout', 'main'], check=True)
        subprocess.run(['git', 'pull', 'origin', 'main'], check=True)
        
        # Analyze version history and changes while on main branch
        self._determine_version_and_changes()

        # Create export branch
        subprocess.run(['git', 'checkout', '-b', self.export_branch], check=True)

        print("Success Export branch created")

    def _remove_obsolete_files(self):
        """Remove obsolete files that no longer exist in source"""
        print("🧹 Cleaning up obsolete files...")
        
        obsolete_files = [
            # Obsolete hooks that have been renamed or removed
            'hooks/detect_speculation.sh',  # Old name, now uses detect_speculation_and_fake_code.sh
            # Add other obsolete files as needed
        ]
        
        removed_count = 0
        for file_path in obsolete_files:
            full_path = os.path.join(self.repo_dir, file_path)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                    print(f"    🗑️ Removed obsolete: {file_path}")
                    removed_count += 1
                except (OSError, PermissionError) as e:
                    print(f"    ⚠️ Failed to remove {file_path}: {e}")
                
        if removed_count > 0:
            print(f"✅ Removed {removed_count} obsolete files")
        else:
            print("✅ No obsolete files found to remove")

    def _copy_to_repository(self):
        """Copy exported content to repository - ADDITIVE BEHAVIOR (preserves existing)"""
        print("Commands Copying exported content (preserving existing)...")

        # Clean up obsolete files first
        self._remove_obsolete_files()

        # WARNING FIXED: ADDITIVE BEHAVIOR - No clearing of existing content!
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

        # Copy README (can overwrite)
        shutil.copy2(os.path.join(self.export_dir, 'README.md'), self.repo_dir)

        print("Success Content copied additively - existing commands preserved")

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
                print(f"    Added/Updated: {item}")

        print("Success Content copied to repository")

    def _verify_exclusions(self):
        """Verify that excluded directories are not present"""
        print("Verifying Verifying directory exclusions...")

        excluded_dirs = ['analysis', 'automation', 'claude-bot-commands', 'coding_prompts', 'prototype']
        found_excluded = []

        for dir_name in excluded_dirs:
            if os.path.exists(os.path.join(self.repo_dir, dir_name)):
                found_excluded.append(dir_name)

        if found_excluded:
            print(f"Error ERROR: Excluded directories found: {', '.join(found_excluded)}")
            # Clean them up
            for dir_name in found_excluded:
                shutil.rmtree(os.path.join(self.repo_dir, dir_name))
            print("Success Cleaned up excluded directories")
        else:
            print("Success Confirmed: No excluded directories in export")

    def _commit_and_push(self):
        """Commit changes and push branch"""
        print("Committing Committing and pushing changes...")

        # Add all changes - handle potential conflicts
        try:
            subprocess.run(['git', 'add', '.'], check=True)
        except subprocess.CalledProcessError as e:
            # Try to add files individually if bulk add fails
            print("   Bulk add failed, trying individual file add...")
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    status = line[0:2]
                    filename = line[3:]
                    if status.strip() in ['??', 'M', 'A', 'D']:  # Untracked, modified, added, deleted
                        try:
                            subprocess.run(['git', 'add', filename], check=True)
                        except subprocess.CalledProcessError:
                            print(f"   Warning: Could not add {filename}, skipping...")

        # Check if there are changes to commit
        status_result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if not status_result.stdout.strip():
            print("   No changes to commit")
        else:
            # Create commit message
            commit_message = f"""Fresh Claude Commands Export {time.strftime('%Y-%m-%d')}

WARNING DIRECTORY EXCLUSIONS APPLIED:
- Excluded: analysis/, automation/, claude-bot-commands/, coding_prompts/, prototype/
- These project-specific directories are filtered from exports per requirements

Success EXPORT CONTENTS:
- Commands Commands: {self.commands_count} command definitions with content filtering
- Hooks Hooks: {self.hooks_count} Claude Code hooks with nested structure
- Starting Infrastructure: {self.scripts_count} scripts for development environment management
- Orchestration Orchestration: Multi-agent task delegation system (core components only)
- DOCS Documentation: Complete README with installation guide and adaptation examples

UPDATE CONTENT TRANSFORMATIONS:
- mvp_site/ -> $PROJECT_ROOT/ (generic project paths)
- worldarchitect.ai -> your-project.com (generic domain)
- jleechan -> $USER (generic username)
- TESTING=true vpython -> TESTING=true python (generic test commands)

Starting ONE-CLICK INSTALL: ./install.sh script auto-installs to .claude/commands/ and .claude/hooks/

Warning Reference export - requires adaptation for other projects
Orchestration Generated with Claude Code CLI"""

            subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Push branch
        subprocess.run(['git', 'push', '-u', 'origin', self.export_branch], check=True)

        print("Success Changes committed and pushed")

    def _create_pull_request(self):
        """Create pull request using GitHub API"""
        print("Creating Creating pull request...")

        pr_title = f"Claude Commands Export {time.strftime('%Y-%m-%d')}: Directory Exclusions Applied"
        pr_body = f"""**WARNING AUTOMATED EXPORT** with directory exclusions applied per requirements.

## Ready Directory Exclusions Applied
This export **excludes** the following project-specific directories:
- Error `analysis/` - Project-specific analytics and reporting
- Error `automation/` - Project-specific automation scripts
- Error `claude-bot-commands/` - Project-specific bot implementation
- Error `coding_prompts/` - Project-specific AI prompting templates
- Error `prototype/` - Project-specific experimental code

## Success Export Contents
- **Commands {self.commands_count} Commands**: Complete workflow orchestration system
- **Hooks {self.hooks_count} Hooks**: Essential Claude Code workflow automation
- **Starting {self.scripts_count} Infrastructure Scripts**: Development environment management
- **Orchestration Orchestration System**: Core multi-agent task delegation (WIP prototype)
- **DOCS Complete Documentation**: Installation guide with adaptation examples

## Starting One-Click Installation
```bash
./install.sh
```
Auto-installs commands to `.claude/commands/`, hooks to `.claude/hooks/`, and copies `claude_start.sh`

## UPDATE Content Filtering Applied
- **Generic Paths**: mvp_site/ -> \\$PROJECT_ROOT/
- **Generic Domain**: worldarchitect.ai -> your-project.com
- **Generic User**: jleechan -> \\$USER
- **Generic Commands**: TESTING=true vpython -> TESTING=true python

## Warning Reference Export
This is a filtered reference export. Commands may need adaptation for specific environments, but Claude Code excels at helping customize them for any workflow.

---
Orchestration **Generated with [Claude Code](https://claude.ai/code)**"""

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

        print(f"Success Pull request created: {pr_url}")
        return pr_url

    def report_success(self, pr_url):
        """Report successful export completion"""
        print("\nComplete EXPORT COMPLETE!")
        print("=" * 50)
        print(f"Directory Local Export: {self.export_dir}")
        archive_files = [f for f in os.listdir(self.export_dir) if f.endswith('.tar.gz')]
        if archive_files:
            print(f"Archive Archive: {archive_files[0]}")
        print(f"Branch Branch: {self.export_branch}")
        print(f"PR Pull Request: {pr_url}")
        print(f"\nSummary Export Summary:")
        print(f"   Commands: {self.commands_count}")
        print(f"   Hooks: {self.hooks_count}")
        print(f"   Scripts: {self.scripts_count}")
        print(f"   Excluded: analysis/, automation/, claude-bot-commands/, coding_prompts/, prototype/")
        print(f"\nReady The export has been published and is ready for review!")

    def handle_error(self, error):
        """Handle export errors gracefully"""
        print(f"\nExport failed: {error}")
        print(f"Partial export may be available at: {self.export_dir}")
        if hasattr(self, 'repo_dir') and os.path.exists(self.repo_dir):
            print(f"Repository clone: {self.repo_dir}")
        print("\nDebug information:")
        print(f"   Project root: {self.project_root}")
        print(f"   GitHub token set: {'Yes' if self.github_token else 'No'}")

if __name__ == "__main__":
    exporter = ClaudeCommandsExporter()
    exporter.export()
