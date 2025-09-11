#!/usr/bin/env python3
"""
Memory MCP Fetch Script - Python Version
Pulls latest memory data from backup repository and converts to MCP cache format
"""
import os
import sys
import json
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse

def validate_repository_url(url: str) -> bool:
    """Validate repository URL against whitelist for security"""
    try:
        parsed = urlparse(url)

        # Only allow HTTPS GitHub URLs
        if parsed.scheme != 'https':
            return False

        if parsed.netloc not in ['github.com', 'api.github.com']:
            return False

        # Validate path pattern for GitHub repositories
        if not re.match(r'^/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?/?$', parsed.path):
            return False

        return True
    except Exception:
        return False

def run_command(cmd: List[str], cwd: str = None) -> bool:
    """Execute shell command with proper error handling"""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return False

def clone_or_pull_repo(repo_url: str, target_dir: str) -> bool:
    """Clone repository if it doesn't exist, otherwise pull latest changes"""
    # Validate repository URL for security
    if not validate_repository_url(repo_url):
        print(f"❌ Invalid repository URL: {repo_url}")
        print("Only HTTPS GitHub URLs are allowed")
        return False

    target_path = Path(target_dir)

    if not target_path.exists():
        print(f"📥 Cloning memory backup repository...")
        return run_command([
            "git", "clone", repo_url, target_dir
        ])
    else:
        print(f"🔄 Fetching latest changes from memory repository...")

        # First fetch the latest changes
        if not run_command(["git", "fetch", "origin", "main"], cwd=target_dir):
            return False

        # Check if we have local changes
        result = subprocess.run(
            ["git", "diff", "--quiet", "HEAD"],
            cwd=target_dir,
            capture_output=True
        )

        # Exit code 0 = no changes, 1 = changes, other = error
        if result.returncode == 0:
            has_local_changes = False
        elif result.returncode == 1:
            has_local_changes = True
        else:
            print(f"❌ Error running git diff (exit {result.returncode}): {result.stderr.decode()}")
            return False

        if has_local_changes:
            print("⚠️ Local changes detected, stashing before pull...")
            if not run_command(["git", "stash"], cwd=target_dir):
                return False

        # Pull with rebase to handle divergent branches
        success = run_command(["git", "pull", "--rebase", "origin", "main"], cwd=target_dir)

        # Restore stashed changes if we stashed them
        if has_local_changes and success:
            print("🔄 Restoring local changes...")
            run_command(["git", "stash", "pop"], cwd=target_dir)

        return success

def load_memory_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load memory from JSONL file (backup repo format)"""
    memories = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        memories.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Skipping invalid JSON on line {line_num}: {e}")
                        continue
    return memories

def save_memory_array(memories: List[Dict[str, Any]], file_path: str) -> None:
    """Save memory to JSON array file (MCP cache format)"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(memories, f, indent=2)

def fetch_memory() -> None:
    """Main fetch function with improved error handling"""
    # Configuration
    cache_dir = os.path.expanduser("~/.cache/mcp-memory")
    repo_dir = os.path.expanduser("~/projects/worldarchitect-memory-backups")
    cache_file = os.path.join(cache_dir, "memory.json")
    repo_file = os.path.join(repo_dir, "memory.json")
    # Default to the main project's memory backup repository
    default_repo = "https://github.com/jleechanorg/worldarchitect-memory-backups.git"
    repo_url = os.getenv("BACKUP_REPO_URL", default_repo)

    print(f"📁 Using backup repository: {repo_url}")
    if os.getenv("BACKUP_REPO_URL"):
        print("   (from BACKUP_REPO_URL environment variable)")
    else:
        print("   (default repository - set BACKUP_REPO_URL to override)")

    # Validate repository URL
    if not repo_url:
        print("❌ Error: No backup repository URL available")
        return

    print("🚀 Starting memory fetch operation...")
    print(f"📍 Repository: {repo_url}")

    # Create cache directory
    os.makedirs(cache_dir, exist_ok=True)
    print(f"📁 Cache directory ready: {cache_dir}")

    # Clone or pull repository
    if not clone_or_pull_repo(repo_url, repo_dir):
        print("❌ Failed to update repository")
        return

    # Convert JSONL format to array format for MCP cache
    print("🔄 Converting memory format (JSONL → Array)...")

    try:
        # Load memories from repo (JSONL format)
        memories = load_memory_jsonl(repo_file)
        print(f"📊 Loaded {len(memories)} memories from backup repository")

        # Save to cache (Array format)
        save_memory_array(memories, cache_file)
        print(f"💾 Saved {len(memories)} memories to MCP cache")

        print("✅ Memory fetch complete!")
        print(f"   Repository: {repo_file}")
        print(f"   Cache: {cache_file}")

    except FileNotFoundError:
        print("⚠️ No memory.json found in repository, creating empty cache")
        save_memory_array([], cache_file)
    except Exception as e:
        print(f"❌ Error during format conversion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_memory()
