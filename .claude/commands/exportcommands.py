#!/usr/bin/env python3
"""
Claude Commands Exporter
Exports Claude Code command system to GitHub repository with automatic PR creation
"""

import os
import time
import subprocess
import tempfile
import shutil
import re
import json
import requests
from pathlib import Path
from export_config import get_exportable_components

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

        # Export configuration - uses shared config from .claude/commands/export_config.py
        # This ensures both /localexportcommands and /exportcommands export the same directories
        # Shared config defines: commands, hooks, agents, scripts, skills, settings.json
        # Note: 'orchestration' is added here specifically for GitHub export
        base_components = get_exportable_components()
        # Remove 'settings.json' from subdirs list (it's a file, not a directory)
        self.EXPORT_SUBDIRS = [c for c in base_components if c != 'settings.json']
        # Add orchestration for GitHub export
        if 'orchestration' not in self.EXPORT_SUBDIRS:
            self.EXPORT_SUBDIRS.append('orchestration')

        # Commands to skip during export (project-specific and user-specified exclusions)
        self.COMMANDS_SKIP_LIST = [
            'testi.sh', 'run_tests.sh', 'copilot_inline_reply_example.sh',  # project-specific
            'converge.md', 'converge.py', 'orchc.md', 'orchc.py',          # orchestration commands to exclude
            'conv.md', 'orchconverge.md',                                   # additional orchestration exclusions
            'copilotc.md', 'fixprc.md',                                     # new autonomous composition commands
            'gen.md', 'gene.md', 'pgen.md', 'pgene.md', 'proto_genesis.md' # proto genesis commands (project-specific)
        ]

        # Counters for summary
        self.commands_count = 0
        self.hooks_count = 0
        self.agents_count = 0
        self.scripts_count = 0
        self.skills_count = 0
        self.workflows_count = 0

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

        print("🔍 Using comprehensive directory export (commands, hooks, agents, scripts, skills, orchestration)")

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

        # Export scripts
        self._export_scripts(staging_dir)

        # Export .claude/scripts directory
        self._export_claude_scripts(staging_dir)

        # Export .claude/skills directory
        self._export_skills(staging_dir)

        # Export settings.json
        self._export_settings(staging_dir)

        # Export package.json and package-lock.json (for secondo command dependencies)
        self._export_dependencies(staging_dir)

        # Export orchestration (with exclusions)
        self._export_orchestration(staging_dir)

        # Export GitHub Actions workflows (as examples)
        self._export_github_workflows(staging_dir)

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

    def _get_scripts_from_settings(self):
        """Parse settings.json to find all referenced scripts"""
        settings_file = os.path.join(self.project_root, '.claude', 'settings.json')
        scripts_from_settings = set()

        if not os.path.exists(settings_file):
            return scripts_from_settings

        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find all script references in settings.json
            # Match patterns like: scripts/filename.sh or scripts/filename.py
            import_pattern = r'scripts/([a-zA-Z0-9_\-]+\.(sh|py))'
            matches = re.findall(import_pattern, content)

            for match in matches:
                script_name = match[0]  # filename.sh or filename.py
                scripts_from_settings.add(script_name)

            print(f"   📋 Found {len(scripts_from_settings)} scripts referenced in settings.json")
            for script in sorted(scripts_from_settings):
                print(f"      • {script}")

        except Exception as e:
            print(f"   ⚠️  Warning: Could not parse settings.json for script references: {e}")

        return scripts_from_settings

    def _export_scripts(self, staging_dir):
        """Export reusable scripts (both Claude Code specific and generally useful development tools)"""
        print("🚀 Exporting scripts...")

        target_dir = os.path.join(staging_dir, 'scripts')

        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)

        script_patterns = [
            # Claude Code infrastructure (generally useful for Claude Code users)
            'claude_start.sh', 'install_mcp_servers.sh',
            # Generally useful git/development workflow scripts
            'integrate.sh', 'resolve_conflicts.sh', 'sync_branch.sh', 'create_worktree.sh',
            # Code analysis and metrics
            'codebase_loc.sh', 'coverage.sh', 'loc.sh', 'loc_simple.sh',
            # Testing infrastructure
            'run_tests_with_coverage.sh', 'run_lint.sh',
            # CI/CD and infrastructure
            'setup-github-runner.sh', 'setup_email.sh',
            # Development environment
            'create_snapshot.sh', 'schedule_branch_work.sh', 'push.sh'
        ]

        # MCP helper scripts (required by install_mcp_servers.sh) - must be from scripts/ subdirectory
        mcp_helper_scripts = ['mcp_common.sh', 'load_tokens.sh']

        # Secondo command scripts (multi-model AI feedback system)
        secondo_scripts = ['auth-cli.mjs', 'secondo-cli.sh', 'test_secondo_pr.sh']

        # Get scripts referenced in settings.json
        settings_scripts = self._get_scripts_from_settings()

        for script_name in script_patterns:
            script_path = os.path.join(self.project_root, script_name)
            if os.path.exists(script_path):
                target_path = os.path.join(target_dir, script_name)
                shutil.copy2(script_path, target_path)
                self._apply_content_filtering(target_path)

                print(f"   • {script_name}")
                self.scripts_count += 1

        # Export MCP helper scripts from scripts/ subdirectory
        scripts_subdir = os.path.join(self.project_root, 'scripts')
        for script_name in mcp_helper_scripts:
            script_path = os.path.join(scripts_subdir, script_name)
            if os.path.exists(script_path):
                target_path = os.path.join(target_dir, script_name)
                shutil.copy2(script_path, target_path)
                self._apply_content_filtering(target_path)

                print(f"   • scripts/{script_name}")
                self.scripts_count += 1
            else:
                print(
                    f"   ⚠️  Warning: Required MCP helper script not found: scripts/{script_name}"
                )

        # Export secondo command scripts from scripts/ subdirectory
        for script_name in secondo_scripts:
            script_path = os.path.join(scripts_subdir, script_name)
            if os.path.exists(script_path):
                target_path = os.path.join(target_dir, script_name)
                shutil.copy2(script_path, target_path)
                self._apply_content_filtering(target_path)

                print(f"   • scripts/{script_name} (secondo)")
                self.scripts_count += 1
            else:
                print(
                    f"   ⚠️  Warning: Secondo script not found: scripts/{script_name}"
                )

        # Export scripts referenced in settings.json from scripts/ subdirectory
        for script_name in settings_scripts:
            # Skip if already exported (MCP helpers or root-level patterns)
            if script_name in mcp_helper_scripts:
                continue

            script_path = os.path.join(scripts_subdir, script_name)
            if os.path.exists(script_path):
                target_path = os.path.join(target_dir, script_name)
                shutil.copy2(script_path, target_path)
                self._apply_content_filtering(target_path)

                print(f"   • settings: scripts/{script_name}")
                self.scripts_count += 1
            else:
                print(
                    f"   ⚠️  Warning: Script referenced in settings.json not found: scripts/{script_name}"
                )

        print(f"✅ Exported {self.scripts_count} scripts")

    def _export_claude_scripts(self, staging_dir):
        """Export .claude/scripts directory and aggregate MCP launchers."""
        print("📜 Exporting .claude/scripts directory...")

        source_dir = Path(self.project_root) / '.claude' / 'scripts'
        target_dir = Path(staging_dir) / 'claude_scripts'
        target_dir.mkdir(parents=True, exist_ok=True)

        scripts_count = 0
        copied_names = set()

        def copy_script(path: Path):
            nonlocal scripts_count
            if not path.exists() or not path.is_file():
                return

            destination = target_dir / path.name
            shutil.copy2(path, destination)
            self._apply_content_filtering(str(destination))

            # Fix REPO_ROOT path for scripts exported to .claude/scripts/
            # Source scripts/ needs ".." to reach repo root
            # Export .claude/scripts/ needs "../.." to reach repo root
            self._fix_repo_root_path(str(destination))

            if destination.suffix == '.sh':
                try:
                    os.chmod(destination, 0o755)
                except OSError:
                    pass

            copied_names.add(path.name)
            scripts_count += 1
            print(f"   📜 {path.name}")

        # Export native Claude scripts (.claude/scripts)
        if source_dir.exists():
            for pattern in ('*.py', '*.sh'):
                for file_path in source_dir.glob(pattern):
                    if file_path.name in copied_names:
                        continue
                    copy_script(file_path)
        else:
            print("⚠️  Warning: .claude/scripts directory not found; attempting legacy MCP locations")

        # Backfill MCP launchers/utilities that remain outside .claude/scripts
        legacy_candidates = {
            'install_mcp_servers.sh': [
                Path(self.project_root) / 'scripts' / 'install_mcp_servers.sh',
                Path(self.project_root) / 'install_mcp_servers.sh',
            ],
            'mcp_common.sh': [
                Path(self.project_root) / 'scripts' / 'mcp_common.sh',
                Path(self.project_root) / 'mcp_common.sh',
            ],
            'mcp_dual_background.sh': [
                Path(self.project_root) / 'scripts' / 'mcp_dual_background.sh',
                Path(self.project_root) / 'mcp_dual_background.sh',
            ],
            'start_mcp_production.sh': [
                Path(self.project_root) / 'scripts' / 'start_mcp_production.sh',
                Path(self.project_root) / 'start_mcp_production.sh',
            ],
            'start_mcp_server.sh': [
                Path(self.project_root) / 'scripts' / 'start_mcp_server.sh',
                Path(self.project_root) / 'start_mcp_server.sh',
            ],
            'mcp_stdio_wrapper.py': [
                Path(self.project_root) / 'scripts' / 'mcp_stdio_wrapper.py',
                Path(self.project_root) / 'mcp_stdio_wrapper.py',
            ],
        }

        for script_name, candidates in legacy_candidates.items():
            if script_name in copied_names:
                continue
            for legacy_path in candidates:
                if legacy_path.exists():
                    copy_script(legacy_path)
                    break

        if scripts_count == 0:
            print("⚠️  Warning: No scripts were exported from available locations")
            return

        print(f"✅ Exported {scripts_count} .claude/scripts files (including MCP launchers)")

    def _export_skills(self, staging_dir):
        """Export .claude/skills directory for reference skills"""
        print("🧠 Exporting .claude/skills directory...")

        source_dir = os.path.join(self.project_root, '.claude', 'skills')
        if not os.path.exists(source_dir):
            print("⚠️  Warning: .claude/skills directory not found")
            return

        target_dir = os.path.join(staging_dir, 'skills')
        os.makedirs(target_dir, exist_ok=True)

        # Reuse directory copy helper for filtering and transformations
        self._copy_directory_with_filtering(source_dir, target_dir)

        allowed_extensions = ('.sh', '.py', '.md', '.json', '.toml', '.txt')
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith(allowed_extensions):
                    self.skills_count += 1
                    rel_path = os.path.relpath(os.path.join(root, file), target_dir)
                    print(f"   🧠 {rel_path}")

        print(f"✅ Exported {self.skills_count} skills")

    def _export_settings(self, staging_dir):
        """Export settings.json file"""
        print("⚙️  Exporting settings.json...")

        settings_file = os.path.join(self.project_root, '.claude', 'settings.json')
        if not os.path.exists(settings_file):
            print("⚠️  Warning: settings.json not found")
            return

        # Create settings_file in staging (will map to .claude/settings.json in repo)
        target_file = os.path.join(staging_dir, 'settings_json')
        shutil.copy2(settings_file, target_file)
        self._apply_content_filtering(target_file)

        print("✅ Exported settings.json")

    def _export_dependencies(self, staging_dir):
        """Export package.json and package-lock.json for secondo command dependencies"""
        print("📦 Exporting Node.js dependencies...")

        # Export package.json
        package_json = os.path.join(self.project_root, 'package.json')
        if os.path.exists(package_json):
            target_file = os.path.join(staging_dir, 'package.json')
            shutil.copy2(package_json, target_file)
            self._apply_content_filtering(target_file)
            print("   • package.json")
        else:
            print("   ⚠️  Warning: package.json not found (required for secondo auth-cli.mjs)")

        # Export package-lock.json for reproducible builds
        package_lock = os.path.join(self.project_root, 'package-lock.json')
        if os.path.exists(package_lock):
            target_file = os.path.join(staging_dir, 'package-lock.json')
            shutil.copy2(package_lock, target_file)
            self._apply_content_filtering(target_file)
            print("   • package-lock.json")

        print("✅ Exported Node.js dependencies")

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
            '--exclude=claude-bot-commands/',
            '--exclude=coding_prompts/',
            '--exclude=prototype/',
            '--exclude=tasks/',
            '--exclude=task-agent-create-autono-slash/',
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
        excluded_dirs = {'analysis', 'claude-bot-commands', 'coding_prompts', 'prototype', 'tasks', 'task-agent-create-autono-slash'}
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

    def _export_github_workflows(self, staging_dir):
        """Export GitHub Actions workflows with project-specific filtering.

        🚨 IMPORTANT: These are EXAMPLES ONLY that need to be integrated into your codebase.
        They cannot be used as-is because they contain project-specific:
        - Repository references
        - GCP project IDs
        - Service account configurations
        - Environment-specific variables
        """
        print("⚙️  Exporting GitHub Actions workflows (examples only)...")

        source_dir = os.path.join(self.project_root, '.github', 'workflows')
        if not os.path.exists(source_dir):
            print("⚠️  Warning: .github/workflows directory not found")
            return

        target_dir = os.path.join(staging_dir, 'workflows')
        os.makedirs(target_dir, exist_ok=True)

        # Counter for workflows
        workflows_count = 0

        # Copy workflow files with filtering
        for workflow_file in sorted(os.listdir(source_dir)):
            if workflow_file.endswith(('.yml', '.yaml')):
                src_file = os.path.join(source_dir, workflow_file)
                dst_file = os.path.join(target_dir, workflow_file)

                # Copy the file
                shutil.copy2(src_file, dst_file)

                # Apply content filtering to make it more generic
                self._apply_workflow_filtering(dst_file)

                workflows_count += 1
                print(f"   ⚙️  {workflow_file}")

        # Create README.md for the workflows directory
        self._create_workflows_readme(target_dir, workflows_count)

        # Store count for summary
        self.workflows_count = workflows_count
        print(f"✅ Exported {workflows_count} workflow examples")

    def _apply_workflow_filtering(self, file_path):
        """Apply project-specific filtering to workflow files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace project-specific values with placeholders
            # Order matters: match more specific patterns first to avoid partial matches
            content = re.sub(r'jleechanorg/worldarchitect\.ai', '$GITHUB_REPOSITORY', content)
            content = re.sub(r'worldarchitecture-ai', '$GCP_PROJECT_ID', content)
            content = re.sub(r'worldarchitect\.ai', 'your-project.com', content)
            content = re.sub(r'jleechanorg', '$GITHUB_OWNER', content)
            content = re.sub(r'\bjleechan\b', '$USER', content)

            # Add header comment to the file indicating it's an example
            header = """# ⚠️ EXAMPLE WORKFLOW - REQUIRES INTEGRATION
# This workflow was exported from a working project and serves as an EXAMPLE ONLY.
# You MUST adapt the following before using:
# - $GCP_PROJECT_ID → Your Google Cloud project ID
# - $GITHUB_REPOSITORY → Your repository (owner/repo)
# - $GITHUB_OWNER → Your GitHub username or org
# - Service account configurations and secrets
# - Environment-specific variables and paths
#
# See workflows/README.md for integration instructions.
# ---

"""
            # Only add header if not already present
            if '⚠️ EXAMPLE WORKFLOW' not in content:
                content = header + content

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            print(f"⚠️  Warning: Workflow filtering failed for {file_path}: {e}")
            # Remove partially written file to avoid exporting broken workflows
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"   Removed broken workflow file: {os.path.basename(file_path)}")
            except Exception as cleanup_error:
                print(f"⚠️  Warning: Failed to remove broken workflow file {file_path}: {cleanup_error}")

    def _fix_repo_root_path(self, file_path):
        """Fix REPO_ROOT path calculation for scripts exported to .claude/scripts/.

        Scripts from scripts/ directory use ".." to reach repo root.
        When exported to .claude/scripts/, they need "../.." instead.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Fix REPO_ROOT path: scripts/ uses ".." but .claude/scripts/ needs "../.."
            # Match pattern: REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
            # Replace with: REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
            content = re.sub(
                r'REPO_ROOT="\$\(cd "\$\{SCRIPT_DIR\}/\.\." && pwd\)"',
                'REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"',
                content
            )

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            print(f"⚠️  Warning: REPO_ROOT path fix failed for {file_path}: {e}")

    def _create_workflows_readme(self, workflows_dir, count):
        """Create a README.md explaining workflows are examples only."""
        readme_content = f'''# GitHub Actions Workflows - EXAMPLES ONLY

⚠️ **IMPORTANT: These workflows are EXAMPLES and require integration into your codebase.**

## What This Directory Contains

This directory contains **{count} GitHub Actions workflow examples** exported from a working Claude Code project. These serve as reference implementations and templates for common CI/CD patterns.

## ⚠️ Why These Cannot Be Used As-Is

These workflows contain project-specific configurations that **must be adapted** before use:

1. **GCP Project IDs**: References to `$GCP_PROJECT_ID` need your actual Google Cloud project
2. **Repository References**: `$GITHUB_REPOSITORY` placeholders need your `owner/repo`
3. **Service Accounts**: Workload Identity Federation and service account configurations are project-specific
4. **Secrets**: Workflow secrets (API keys, tokens) must be configured in your repository
5. **Environment Variables**: Project-specific env vars need customization
6. **Path References**: Some paths may be specific to the original project structure

## How to Integrate These Workflows

### Step 1: Create Your Workflows Directory
```bash
mkdir -p .github/workflows
```

### Step 2: Copy and Adapt Workflows
For each workflow you want to use:

1. Copy the workflow file to `.github/workflows/`
2. Replace ALL placeholder values:
   - `$GCP_PROJECT_ID` → Your GCP project ID (e.g., `my-project-123`)
   - `$GITHUB_REPOSITORY` → Your repo (e.g., `myorg/myrepo`)
   - `$GITHUB_OWNER` → Your GitHub username or organization
   - `$USER` → Your username if applicable

3. Configure required secrets in your repository settings:
   - `GITHUB_TOKEN` (usually automatic)
   - `GCP_SERVICE_ACCOUNT` if using GCP deployments
   - Any API keys referenced in the workflow

### Step 3: Validate Before Committing
```bash
# Check YAML syntax
yamllint .github/workflows/*.yml

# Or use actionlint for GitHub Actions specific validation
actionlint
```

## Workflow Categories

### CI/CD Workflows
- **test.yml** - Run tests on push/PR
- **deploy-*.yml** - Deployment workflows
- **presubmit.yml** - Pre-merge validation

### Automation Workflows
- **pr-cleanup.yml** - Automatic PR maintenance
- **auto-deploy-*.yml** - Automatic deployment triggers
- **slash-dispatch.yml** - Slash command dispatching

### Code Quality
- **hook-tests.yml** - Claude Code hook validation
- **doc-size-check.yml** - Documentation size limits

## Common Adaptations

### For Google Cloud Deployments
```yaml
# Replace this:
env:
  GCP_PROJECT: $GCP_PROJECT_ID

# With your actual project:
env:
  GCP_PROJECT: my-actual-project-id
```

### For Repository References
```yaml
# Replace this:
repository: $GITHUB_REPOSITORY

# With your repo:
repository: myorg/myrepo
```

### For Service Account Authentication
Set up Workload Identity Federation or use a service account key:
```yaml
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: projects/YOUR_PROJECT_NUMBER/locations/global/workloadIdentityPools/YOUR_POOL/providers/YOUR_PROVIDER
    service_account: YOUR_SA@YOUR_PROJECT.iam.gserviceaccount.com
```

## Need Help?

Claude Code can assist with adapting these workflows to your specific project. Just describe your CI/CD requirements and ask for help customizing the relevant workflow files.

---

**Source**: Exported from [WorldArchitect.AI](https://github.com/jleechanorg/worldarchitect.ai) Claude Code configuration
'''

        readme_path = os.path.join(workflows_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print("   📝 Created workflows/README.md with integration instructions")

    def _apply_content_filtering(self, file_path):
        """Apply content transformations to files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Skip transformations for files that should preserve patterns
            filename = os.path.basename(file_path)
            # Skip mvp_site transformation for loc_simple.sh (uses relative paths intentionally)
            # Skip ALL transformations for exportcommands.py (contains regex patterns that should not be transformed)
            # Compare by filename because the staging copy lives in a different directory than the source file.
            skip_all_transforms = filename == Path(__file__).name
            skip_mvp_transform = filename == 'loc_simple.sh'

            # Apply transformations - Enhanced for portability
            # Skip all transformations for exportcommands.py to preserve regex patterns
            if skip_all_transforms:
                # Don't apply any transformations to exportcommands.py
                pass
            else:
                if not skip_mvp_transform:
                    content = re.sub(r'mvp_site/', '$PROJECT_ROOT/', content)
                content = re.sub(r'worldarchitect\.ai', 'your-project.com', content)
                content = re.sub(r'\bjleechan\b', '$USER', content)
                content = re.sub(r'TESTING=true vpython', 'TESTING=true python', content)
                content = re.sub(r'WorldArchitect\.AI', 'Your Project', content)

                # New portable patterns
                content = re.sub(r'~/worldarchitect\.ai', '$(git rev-parse --show-toplevel)', content)
                content = re.sub(r'~/your-project\.com', '$(git rev-parse --show-toplevel)', content)
                content = re.sub(r'jleechantest@gmail\.com', '<your-email@gmail.com>', content)
                content = re.sub(r'/tmp/worldarchitectai', '/tmp/$PROJECT_NAME', content)
                content = re.sub(r'/tmp/worldarchitect\.ai', '/tmp/$PROJECT_NAME', content)
                # Handle GitHub URLs in echo statements with proper quote termination (consolidated pattern)
                content = re.sub(r'https://github\.com/jleechanorg/[^/\s"]+(?:\.git)?(?=\${NC}\")', '$(git config --get remote.origin.url)', content)

                # SOURCE_DIR variable patterns - improved matching
                content = re.sub(r'\bfind\s+["\']?(?:\./)?mvp_site["\']?', 'find "$SOURCE_DIR"', content)
                content = re.sub(r'\bcd\s+["\']?(?:\./)?mvp_site["\']?', 'cd "$SOURCE_DIR"', content)

                # Add SOURCE_DIR initialization to scripts that reference mvp_site but don't define it
                if 'SOURCE_DIR' in content and not re.search(r'^\s*SOURCE_DIR=', content, re.MULTILINE) and 'mvp_site' in content:
                    # Insert SOURCE_DIR definition after PROJECT_ROOT or early in script
                    if 'PROJECT_ROOT=' in content:
                        content = re.sub(r'(PROJECT_ROOT=[^\n]*\n)', r'\1\n# Source directory for project files\nSOURCE_DIR="$PROJECT_ROOT"\n', content)
                    else:
                        # Insert after shebang and initial comments (flexible for any shebang)
                        content = re.sub(r'(#![^\n]*\n(?:#[^\n]*\n)*)', r'\1\n# Source directory for project files\nSOURCE_DIR="$PROJECT_ROOT"\n', content)
                content = re.sub(r'if\s+\[\s*!\s*-d\s*["\']mvp_site["\']\s*\]', 'if [ ! -d "$SOURCE_DIR" ]', content)

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
        print("   📋 Using v1.1.0 for command count consistency fixes")
        return version

    def _get_existing_version_from_target(self):
        """Get the latest version from target repository README"""
        try:
            url = "https://raw.githubusercontent.com/jleechanorg/claude-commands/main/README.md"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text
                # Look for version patterns like ### v1.2.3
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
            url = "https://raw.githubusercontent.com/jleechanorg/claude-commands/main/README.md"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                existing_content = response.text
                # Extract the version history section
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
- **{self.scripts_count} Scripts**: Development and automation tools (scripts/ directory)
- **{self.skills_count} Skills**: Shared knowledge references (.claude/skills/)

**Major Changes**:
- **Script Allowlist Expansion**: Added 12 generally useful development scripts to the scripts export
- **Development Workflow Tools**: Now includes git workflow, code analysis, testing, and CI/CD scripts
- **Enhanced Export Utility**: Broader coverage of reusable development infrastructure

**New Scripts Included**:
- **Git Workflow**: create_worktree.sh, push.sh for branch management
- **Code Analysis**: codebase_loc.sh, loc.sh, loc_simple.sh for metrics
- **Testing Utilities**: run_tests_with_coverage.sh, run_lint.sh
- **CI/CD Tools**: setup-github-runner.sh, setup_email.sh
- **Development Environment**: create_snapshot.sh, schedule_branch_work.sh

**Technical Improvements**:
- Expanded script_patterns list from 5 to 15 generally useful scripts
- Better categorization of Claude Code specific vs universally useful tools
- Enhanced documentation for script adaptability across projects

**Documentation**:
- Updated scripts export description
- Clear separation between project-specific and generally useful scripts
- Improved adaptation guidance for cross-project usage'''

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
- **5 Scripts**: Development and automation tools (scripts/ directory)

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
            r'\*\*(\d+) Skills\*\*': f'**{self.skills_count} Skills**',
            r'\*\*(\d+) skills\*\*': f'**{self.skills_count} skills**',
        }

        # Apply all replacements
        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content)

        print(f"   📊 Dynamic counts: {self.commands_count} commands, {self.hooks_count} hooks, {self.scripts_count} scripts, {self.agents_count} agents, {self.skills_count} skills")
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
- **{self.scripts_count} scripts** reusable automation scripts (scripts/)
- **{self.skills_count} skills** shared knowledge references (.claude/skills/)

## MANUAL INSTALLATION

Run these from the export directory (the one containing the `staging/` folder), targeting your project repository as the current working directory:

Copy the exported commands and hooks to your project's `.claude/` directory:
- Commands → `.claude/commands/`
- Hooks → `.claude/hooks/`
- Agents → `.claude/agents/`
- Scripts → `scripts/` in your project root
- Skills → `.claude/skills/`

## 📊 **Export Contents**

This comprehensive export includes:
- **📋 {self.commands_count} Command Definitions** - Complete workflow orchestration system (.claude/commands/)
- **📎 {self.hooks_count} Claude Code Hooks** - Essential workflow automation (.claude/hooks/)
- **🤖 {self.agents_count} Agent Definitions** - Specialized task agents for autonomous workflows (.claude/agents/)
- **🧠 {self.skills_count} Skills** - Knowledge base exports (.claude/skills/)
- **🔧 {self.scripts_count} Scripts** - Development environment management (scripts/)
- **🤖 Orchestration System** - Core multi-agent task delegation (project-specific parts excluded)
- **📚 Complete Documentation** - Setup guide with adaptation examples

🚨 **DIRECTORY EXCLUSIONS APPLIED**: This export excludes the following project-specific directories:
- ❌ `analysis/` - Project-specific analytics
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
cp -r claude-commands/skills/* .claude/skills/

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
        print("Cloning target repository...")

        # Use system PATH to find gh command with fallback for common locations
        gh_cmd = shutil.which('gh')
        if not gh_cmd:
            # Try common locations for gh (Linux and Windows)
            common_paths = [
                os.path.expanduser("~/.local/bin/gh"),  # Linux user install
                "/usr/local/bin/gh",                    # Linux system install
                os.path.join(os.path.expanduser("~"), "bin", "gh"),  # Windows/Linux user bin
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
            'claude_scripts': os.path.join(claude_dir, 'scripts'),  # .claude/scripts directory
            'skills': os.path.join(claude_dir, 'skills'),           # .claude/skills directory
            'settings_json': os.path.join(claude_dir, 'settings.json'),  # .claude/settings.json file
            'orchestration': 'orchestration',  # Goes to repo root
            'scripts': None,                   # Goes to repo root within scripts/
            'workflows': 'workflows'           # GitHub workflows - goes to repo root as examples
        }

        # Create the .claude/ subdirectories (but not for files like settings.json)
        for local_name, target_path in dirs_mapping.items():
            # Create directory only if target_path is a directory (no file extension)
            if target_path and target_path.startswith(claude_dir) and not Path(target_path).suffix:
                os.makedirs(target_path, exist_ok=True)

        # Copy content with proper directory mapping
        staging_dir = os.path.join(self.export_dir, 'staging')
        for item in os.listdir(staging_dir):
            src = os.path.join(staging_dir, item)

            # Map to correct target location
            if item in dirs_mapping:
                target_path = dirs_mapping[item]
                if target_path is None:
                    # Handle scripts specially - copy to scripts/ directory in repo root
                    if item == 'scripts' and os.path.isdir(src):
                        scripts_dir = os.path.join(self.repo_dir, 'scripts')
                        os.makedirs(scripts_dir, exist_ok=True)

                        for script_file in sorted(os.listdir(src)):
                            script_src = os.path.join(src, script_file)
                            script_dst = os.path.join(scripts_dir, script_file)
                            if os.path.isfile(script_src):
                                shutil.copy2(script_src, script_dst)
                                # Ensure executability for shell/python scripts (Windows-safe)
                                if script_file.endswith(('.sh', '.py')):
                                    try:
                                        os.chmod(script_dst, 0o755)
                                    except (OSError, NotImplementedError):
                                        pass
                                print(f"   • Added/Updated: scripts/{script_file}")
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

            # Skip virtual environments, node_modules, and broken symlinks
            if item in ('venv', 'node_modules', '__pycache__', '.git'):
                continue
            if os.path.islink(src_item) and not os.path.exists(src_item):
                print(f"   ⏭ Skipping broken symlink: {item}")
                continue

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

        excluded_dirs = ['analysis', 'claude-bot-commands', 'coding_prompts', 'prototype']
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

        # Configure git user for commit (needed in clean clone)
        subprocess.run(['git', 'config', 'user.email', 'claude-export@anthropic.com'], check=True)
        subprocess.run(['git', 'config', 'user.name', 'Claude Export'], check=True)
        # Disable commit signing (may not be configured in cloned repo)
        subprocess.run(['git', 'config', 'commit.gpgsign', 'false'], check=True)

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
- Excluded: analysis/, claude-bot-commands/, coding_prompts/, prototype/
- These project-specific directories are filtered from exports per requirements

✅ EXPORT CONTENTS:
- 📋 Commands: {self.commands_count} command definitions with content filtering
- 📎 Hooks: {self.hooks_count} Claude Code hooks with nested structure
- 🚀 Scripts: {self.scripts_count} reusable automation scripts (scripts/ directory)
- 🧠 Skills: {self.skills_count} shared knowledge references (.claude/skills/)
- ⚙️  Workflows: {self.workflows_count} GitHub Actions workflow examples (require integration)
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
- ❌ `claude-bot-commands/` - Project-specific bot implementation
- ❌ `coding_prompts/` - Project-specific AI prompting templates
- ❌ `prototype/` - Project-specific experimental code

## ✅ Export Contents
- **📋 {self.commands_count} Commands**: Complete workflow orchestration system
- **📎 {self.hooks_count} Hooks**: Essential Claude Code workflow automation
- **🚀 {self.scripts_count} Scripts**: Development environment management (scripts/ directory)
- **🧠 {self.skills_count} Skills**: Reference knowledge exports (.claude/skills/)
- **⚙️  {self.workflows_count} Workflows**: GitHub Actions examples (REQUIRE INTEGRATION)
- **🤖 Orchestration System**: Core multi-agent task delegation (WIP prototype)
- **📚 Complete Documentation**: Setup guide with adaptation examples

## Manual Installation
From your project root:
```bash
mkdir -p .claude/{{commands,hooks,agents,skills}}
mkdir -p scripts
cp -R commands/. .claude/commands/
cp -R hooks/. .claude/hooks/
cp -R agents/. .claude/agents/
cp -R skills/. .claude/skills/
# Optional scripts directory
cp -n scripts/* ./scripts/
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
        print("\n📊 Export Summary:")
        print(f"   Commands: {self.commands_count}")
        print(f"   Hooks: {self.hooks_count}")
        print(f"   Agents: {self.agents_count}")
        print(f"   Scripts: {self.scripts_count}")
        print(f"   Skills: {self.skills_count}")
        print(f"   Workflows: {self.workflows_count} (examples only)")
        print("   Excluded: analysis/, claude-bot-commands/, coding_prompts/, prototype/")
        print("\n🎯 The export has been published and is ready for review!")

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
