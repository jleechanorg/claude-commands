#!/usr/bin/env python3
"""
Enhanced Memory Backup Script with Fetch-Before-Backup
Dropbox-like synchronization for Memory MCP across multiple machines
"""
import json
import os
import subprocess
import sys
import re
from datetime import datetime
from typing import Dict, Any, List
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
    """Run a shell command and return success status"""
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return False

def load_memory_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load memory from JSONL file (backup repo format)"""
    memories = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        memories.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return memories

def load_memory_array(file_path: str) -> List[Dict[str, Any]]:
    """Load memory from JSON array file (MCP cache format)"""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
    except json.JSONDecodeError:
        return []

def save_memory_jsonl(memories: List[Dict[str, Any]], file_path: str) -> None:
    """Save memory to JSONL file (backup repo format)"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        for memory in memories:
            f.write(json.dumps(memory, separators=(',', ':')) + '\n')

def save_memory_array(memories: List[Dict[str, Any]], file_path: str) -> None:
    """Save memory to JSON array file (MCP cache format)"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(memories, f, indent=2)

def get_memory_timestamp(memory: Dict[str, Any]) -> str:
    """Extract timestamp from memory entry for CRDT comparison"""
    # Check various timestamp fields
    for field in ['timestamp', 'last_updated', 'created_at', '_crdt_metadata.timestamp']:
        if '.' in field:
            # Handle nested fields like _crdt_metadata.timestamp
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

    # Default timestamp if none found
    return "1970-01-01T00:00:00Z"

def merge_memory_entries(local_memories: List[Dict[str, Any]], remote_memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge two memory lists using CRDT Last-Write-Wins strategy"""
    # Create lookup by memory ID/name
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
            local_timestamp = get_memory_timestamp(local_memory)
            remote_timestamp = get_memory_timestamp(remote_memory)

            # Last-Write-Wins: keep the memory with later timestamp
            if remote_timestamp > local_timestamp:
                merged[memory_id] = remote_memory
        else:
            merged[memory_id] = remote_memory

    return list(merged.values())

def backup_memory() -> None:
    """Enhanced backup with fetch-before-backup for multi-machine sync"""
    cache_path = os.path.expanduser("~/.cache/mcp-memory/memory.json")
    repo_dir = os.path.expanduser("~/projects/worldarchitect-memory-backups")
    repo_path = os.path.join(repo_dir, "memory.json")
    # Default to the main project's memory backup repository
    default_repo = "https://github.com/jleechanorg/worldarchitect-memory-backups.git"
    repo_url = os.environ.get("BACKUP_REPO_URL", default_repo)

    print(f"📁 Using backup repository: {repo_url}")
    if os.environ.get("BACKUP_REPO_URL"):
        print("   (from BACKUP_REPO_URL environment variable)")
    else:
        print("   (default repository - set BACKUP_REPO_URL to override)")

    # Validate repository URL for security
    if not validate_repository_url(repo_url):
        print(f"❌ Invalid repository URL: {repo_url}")
        print("Only HTTPS GitHub URLs are allowed")
        return

    print(f"🔄 Starting enhanced memory backup - {datetime.now()}")

    # Step 1: Ensure repo exists and is up to date
    if not os.path.exists(repo_dir):
        print("📁 Cloning memory backup repository...")
        if not run_command([
            "git", "clone",
            repo_url,
            repo_dir
        ]):
            print("❌ Failed to clone repository")
            return

    # Step 2: Fetch latest changes from remote
    print("⬇️ Fetching latest changes from remote...")
    if not run_command(["git", "pull", "origin", "main"], cwd=repo_dir):
        print("⚠️ Failed to pull latest changes, continuing with local state")

    # Step 3: Load both memory sources
    cache_memories = load_memory_array(cache_path)
    # Check if repo file is in JSON array or JSONL format
    if os.path.exists(repo_path):
        with open(repo_path, 'r') as f:
            first_char = f.read(1)
        if first_char == '[':
            # JSON array format
            repo_memories = load_memory_array(repo_path)
        else:
            # JSONL format
            repo_memories = load_memory_jsonl(repo_path)
    else:
        repo_memories = []

    print(f"📊 Cache memories: {len(cache_memories)}")
    print(f"📊 Repo memories: {len(repo_memories)}")

    # Step 4: Merge using CRDT logic
    merged_memories = merge_memory_entries(cache_memories, repo_memories)
    print(f"🔀 Merged result: {len(merged_memories)} total memories")

    # Step 5: Save back to both locations
    save_memory_array(merged_memories, cache_path)
    save_memory_jsonl(merged_memories, repo_path)

    # Step 6: Check if there are changes to commit
    result = subprocess.run(
        ["git", "diff", "--quiet", "memory.json"],
        cwd=repo_dir,
        capture_output=True
    )

    if result.returncode != 0:  # There are changes
        print("📝 Changes detected, committing and pushing...")

        # Commit changes
        if not run_command(["git", "add", "memory.json"], cwd=repo_dir):
            print("❌ Failed to stage changes")
            return

        commit_msg = f"Memory backup from {os.uname().nodename} - {datetime.now().isoformat()}"
        if not run_command(["git", "commit", "-m", commit_msg], cwd=repo_dir):
            print("❌ Failed to commit changes")
            return

        # Push changes
        if not run_command(["git", "push", "origin", "main"], cwd=repo_dir):
            print("❌ Failed to push changes")
            return

        print("✅ Memory backup complete and pushed to repository")
    else:
        print("ℹ️ No changes detected, skipping commit")

    print(f"🎉 Enhanced memory backup finished - {datetime.now()}")

if __name__ == "__main__":
    backup_memory()
