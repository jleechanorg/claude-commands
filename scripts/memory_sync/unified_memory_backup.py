#!/usr/bin/env python3
"""
Unified Memory Backup Script
Consolidates both automated cron and manual backup functionality
Supports CRDT merging, format conversion, and repository management
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from urllib.parse import urlparse
import re

class UnifiedMemoryBackup:
    def __init__(self, mode: str = "manual", repo_name: str = None):
        self.mode = mode
        self.is_cron = mode == "cron"
        self.timestamp = datetime.now()
        self.date_stamp = self.timestamp.strftime('%Y-%m-%d')

        # Auto-detect repository name if not provided
        if repo_name is None:
            repo_name = self._detect_repo_name()

        self.repo_name = repo_name

        # Configuration with repository-specific memory file
        memory_filename = f"memory_{repo_name}.json"
        self.memory_file = os.path.expanduser(f"~/.cache/mcp-memory/{memory_filename}")
        self.repo_url = os.environ.get("BACKUP_REPO_URL", "https://github.com/jleechanorg/worldarchitect-memory-backups.git")
        self.repo_dir = os.path.expanduser("~/.cache/memory-backup-repo")
        self.lock_file = os.path.expanduser(f"~/.cache/mcp-memory/backup_{repo_name}.lock")

        # Logging configuration
        self.verbose = not self.is_cron

    def _detect_repo_name(self) -> str:
        """Auto-detect current repository name for memory file naming"""
        try:
            # Try to get repository name from git remote
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, timeout=10, check=True
            )
            remote_url = result.stdout.strip()

            # Extract repository name from URL
            if remote_url:
                # Handle both HTTPS and SSH URLs
                repo_name = remote_url.split('/')[-1]
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                # Replace dots with dashes for filename compatibility
                repo_name = repo_name.replace('.', '-')
                return repo_name
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass

        # Fallback to directory name if git is not available
        try:
            cwd = os.getcwd()
            dir_name = os.path.basename(cwd)
            # Clean directory name for filename use
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '-', dir_name)
            return clean_name
        except:
            pass

        # Ultimate fallback
        return "default"

    def log(self, message: str, force: bool = False) -> None:
        """Log message with timestamp, respecting verbosity settings"""
        if self.verbose or force:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"{timestamp}: {message}")

    def error_exit(self, message: str) -> None:
        """Log error and exit"""
        self.log(f"ERROR: {message}", force=True)
        self.cleanup()
        sys.exit(1)

    def acquire_lock(self) -> None:
        """Prevent concurrent backup execution"""
        if os.path.exists(self.lock_file):
            with open(self.lock_file, 'r') as f:
                pid = f.read().strip()
            # Check if process is still running
            try:
                os.kill(int(pid), 0)
                self.error_exit(f"Another backup process is running (PID: {pid})")
            except (OSError, ValueError):
                # Process not running, remove stale lock
                os.unlink(self.lock_file)

        with open(self.lock_file, 'w') as f:
            f.write(str(os.getpid()))
        self.log("🔒 Acquired backup lock")

    def release_lock(self) -> None:
        """Release backup lock"""
        if os.path.exists(self.lock_file):
            os.unlink(self.lock_file)
            self.log("🔓 Released backup lock")

    def cleanup(self) -> None:
        """Cleanup resources"""
        self.release_lock()

    def validate_repository_url(self, url: str) -> bool:
        """Validate repository URL for security"""
        try:
            parsed = urlparse(url)
            if parsed.scheme != 'https':
                return False
            if parsed.netloc not in ['github.com', 'api.github.com']:
                return False
            if not re.match(r'^/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?/?$', parsed.path):
                return False
            return True
        except Exception:
            return False

    def run_command(self, cmd: List[str], cwd: str = None) -> bool:
        """Execute command with error handling"""
        try:
            result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {' '.join(cmd)}")
            self.log(f"Error: {e.stderr}")
            return False

    def validate_environment(self) -> None:
        """Validate prerequisites"""
        # Check memory file exists
        if not os.path.exists(self.memory_file):
            self.error_exit(f"Memory file not found: {self.memory_file}")

        # Validate JSON format
        try:
            with open(self.memory_file, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            self.error_exit(f"Memory file is not valid JSON: {e}")

        # Validate repository URL
        if not self.validate_repository_url(self.repo_url):
            self.error_exit(f"Invalid repository URL: {self.repo_url}")

        # Check required tools
        for tool in ['git']:
            if not subprocess.run(['which', tool], capture_output=True).returncode == 0:
                self.error_exit(f"Required tool not found: {tool}")

        self.log("✅ Environment validation passed")

    def setup_repository(self) -> None:
        """Clone or update repository"""
        if not os.path.exists(self.repo_dir):
            self.log("📁 Cloning memory backup repository...")
            if not self.run_command(['git', 'clone', self.repo_url, self.repo_dir]):
                self.error_exit("Failed to clone repository")

        # Fetch latest changes
        self.log("⬇️ Fetching latest changes from remote...")
        if not self.run_command(['git', 'pull', 'origin', 'main'], cwd=self.repo_dir):
            self.log("⚠️ Failed to pull latest changes, continuing with local state")

        # Create historical directory
        historical_dir = os.path.join(self.repo_dir, 'historical')
        os.makedirs(historical_dir, exist_ok=True)

        self.log("📁 Repository setup complete")

    def load_memory_array(self, file_path: str) -> List[Dict[str, Any]]:
        """Load memory from JSON array file"""
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def load_memory_jsonl(self, file_path: str) -> List[Dict[str, Any]]:
        """Load memory from JSONL file"""
        memories = []
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            memories.append(json.loads(line))
                        except json.JSONDecodeError:
                            self.log(f"⚠️ Skipping invalid JSON on line {line_num}")
                            continue
        return memories

    def save_memory_jsonl(self, memories: List[Dict[str, Any]], file_path: str) -> None:
        """Save memory to JSONL file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            for memory in memories:
                f.write(json.dumps(memory, separators=(',', ':')) + '\n')

    def save_memory_array(self, memories: List[Dict[str, Any]], file_path: str) -> None:
        """Save memory to JSON array file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(memories, f, indent=2)

    def get_memory_timestamp(self, memory: Dict[str, Any]) -> str:
        """Extract timestamp from memory entry for CRDT comparison"""
        for field in ['timestamp', 'last_updated', 'created_at', '_crdt_metadata.timestamp']:
            if '.' in field:
                parts = field.split('.')
                value = memory
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break
                if value:
                    return str(value)
            elif field in memory:
                return str(memory[field])
        return "1970-01-01T00:00:00Z"

    def merge_memory_entries(self, local_memories: List[Dict[str, Any]],
                           remote_memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge memory lists using CRDT Last-Write-Wins strategy"""
        merged = {}
        fallback_counter = 0

        # Process local memories first
        for memory in local_memories:
            memory_id = memory.get('id') or memory.get('name')
            if not memory_id:
                memory_id = f"memory_{fallback_counter}"
                fallback_counter += 1
            merged[memory_id] = memory

        # Merge remote memories using LWW
        for remote_memory in remote_memories:
            memory_id = remote_memory.get('id') or remote_memory.get('name')
            if not memory_id:
                memory_id = f"memory_{fallback_counter}"
                fallback_counter += 1

            if memory_id in merged:
                local_memory = merged[memory_id]
                local_timestamp = self.get_memory_timestamp(local_memory)
                remote_timestamp = self.get_memory_timestamp(remote_memory)

                if remote_timestamp > local_timestamp:
                    merged[memory_id] = remote_memory
            else:
                merged[memory_id] = remote_memory

        return list(merged.values())

    def create_historical_snapshot(self) -> None:
        """Create daily historical snapshot"""
        snapshot_file = os.path.join(self.repo_dir, 'historical', f'memory-{self.date_stamp}.json')

        if os.path.exists(snapshot_file):
            self.log(f"📊 Historical snapshot already exists for today")
            return

        # Copy current memory file to snapshot
        with open(self.memory_file, 'r') as src, open(snapshot_file, 'w') as dst:
            memories = json.load(src)

            # Add metadata header
            metadata = {
                "_metadata": {
                    "backup_date": self.timestamp.isoformat(),
                    "source_file": self.memory_file,
                    "entity_count": len(memories),
                    "snapshot_type": "historical_daily"
                }
            }

            json.dump([metadata] + memories, dst, indent=2)

        self.log(f"📊 Created historical snapshot: {os.path.basename(snapshot_file)}")

    def backup_memory(self) -> None:
        """Main backup function with CRDT merging"""
        self.log(f"🚀 Starting unified memory backup ({self.mode} mode)")
        self.log(f"📁 Repository: {self.repo_url}")

        # Load current memories
        cache_memories = self.load_memory_array(self.memory_file)
        self.log(f"📊 Local memories: {len(cache_memories)}")

        # Load existing backup memories
        repo_file = os.path.join(self.repo_dir, 'memory.json')
        if os.path.exists(repo_file):
            # Detect format
            with open(repo_file, 'r') as f:
                first_char = f.read(1)
            if first_char == '[':
                repo_memories = self.load_memory_array(repo_file)
            else:
                repo_memories = self.load_memory_jsonl(repo_file)
        else:
            repo_memories = []

        self.log(f"📊 Remote memories: {len(repo_memories)}")

        # CRDT merge
        merged_memories = self.merge_memory_entries(cache_memories, repo_memories)
        self.log(f"🔀 Merged result: {len(merged_memories)} total memories")

        # Save merged result back to both locations
        self.save_memory_array(merged_memories, self.memory_file)
        self.save_memory_jsonl(merged_memories, repo_file)

        # Create historical snapshot
        self.create_historical_snapshot()

        # Commit and push changes
        self.commit_and_push(len(merged_memories) - len(repo_memories))

    def commit_and_push(self, change_count: int) -> None:
        """Commit and push changes"""
        os.chdir(self.repo_dir)

        # Check for changes
        result = subprocess.run(['git', 'diff', '--quiet', 'memory.json', 'historical/'],
                              capture_output=True)

        if result.returncode == 0:
            self.log("ℹ️ No changes detected, skipping commit")
            return

        # Stage changes
        if not self.run_command(['git', 'add', 'memory.json', 'historical/']):
            self.error_exit("Failed to stage changes")

        # Create commit message
        entity_count = len(self.load_memory_jsonl(os.path.join(self.repo_dir, 'memory.json')))
        commit_msg = f"""Unified memory backup - {self.timestamp.isoformat()}

Mode: {self.mode}
Total entities: {entity_count}
Change: {change_count:+d} entities
Historical: historical/memory-{self.date_stamp}.json

🤖 Generated with Unified Memory Backup System
Co-Authored-By: Claude <noreply@anthropic.com>"""

        if not self.run_command(['git', 'commit', '-m', commit_msg]):
            self.error_exit("Failed to commit changes")

        if not self.run_command(['git', 'push', 'origin', 'main']):
            self.error_exit("Failed to push changes")

        self.log("✅ Successfully committed and pushed changes")

        # Get commit URL for user
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=self.repo_dir,
                              capture_output=True, text=True)
        if result.returncode == 0:
            commit_hash = result.stdout.strip()[:7]
            repo_name = self.repo_url.split('/')[-1].replace('.git', '')
            repo_user = self.repo_url.split('/')[-2]
            commit_url = f"https://github.com/{repo_user}/{repo_name}/commit/{commit_hash}"
            self.log(f"🔗 Commit URL: {commit_url}")

def main():
    parser = argparse.ArgumentParser(description="Unified Memory Backup Script")
    parser.add_argument('--mode', choices=['manual', 'cron'], default='manual',
                      help='Execution mode: manual (verbose) or cron (quiet)')
    parser.add_argument('--repo-name', type=str, default=None,
                      help='Repository name for memory file (auto-detected if not specified)')

    args = parser.parse_args()

    backup = UnifiedMemoryBackup(mode=args.mode, repo_name=args.repo_name)

    try:
        backup.acquire_lock()
        backup.validate_environment()
        backup.setup_repository()
        backup.backup_memory()
        backup.log(f"🎉 Unified memory backup completed successfully ({args.mode} mode)")
    except KeyboardInterrupt:
        backup.log("⚠️ Backup interrupted by user")
        sys.exit(1)
    except Exception as e:
        backup.error_exit(f"Unexpected error: {e}")
    finally:
        backup.cleanup()

if __name__ == "__main__":
    main()
