#!/usr/bin/env python3
"""
CRDT-based memory backup system for parallel backups without locks.
Uses Last-Write-Wins (LWW) conflict resolution for automatic merging.
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import project logging utility
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mvp_site'))
import logging_util

logger = logging_util.getLogger(__name__)


@dataclass
class CRDTMetadata:
    """CRDT metadata for tracking entry versions and conflicts."""
    host: str
    timestamp: str
    version: int
    unique_id: str


class MemoryBackupCRDT:
    """Handles CRDT operations for memory backup entries."""
    
    def __init__(self, host_id: Optional[str] = None):
        """Initialize with optional host ID."""
        self.host_id = host_id or socket.gethostname()
    
    def inject_metadata(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject CRDT metadata into a memory entry.
        
        Args:
            entry: Memory entry dictionary
            
        Returns:
            Entry with CRDT metadata added
        """
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        entry_id = entry.get('id', 'unknown')
        
        # Generate unique ID: hostname_id_timestamp
        unique_id = f"{self.host_id}_{entry_id}_{timestamp}"
        
        # Version increment if metadata exists
        version = 1
        if '_crdt_metadata' in entry:
            old_meta = entry['_crdt_metadata']
            if isinstance(old_meta, dict):
                version = old_meta.get('version', 0) + 1
        
        entry['_crdt_metadata'] = {
            'host': self.host_id,
            'timestamp': timestamp,
            'version': version,
            'unique_id': unique_id
        }
        
        return entry
    
    def prepare_memory_file(self, memory_file_path: str) -> List[Dict[str, Any]]:
        """
        Read and prepare memory entries with CRDT metadata.
        
        Args:
            memory_file_path: Path to memory JSON file
            
        Returns:
            List of entries with CRDT metadata
        """
        path = Path(memory_file_path)
        if not path.exists():
            logger.warning(f"Memory file not found: {memory_file_path}")
            return []
        
        try:
            with open(path, 'r') as f:
                entries = json.load(f)
                
            if not isinstance(entries, list):
                logger.error(f"Invalid format in {memory_file_path}: expected list")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {memory_file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error reading {memory_file_path}: {e}")
            return []
        
        # Add CRDT metadata to each entry
        prepared_entries = []
        for entry in entries:
            if not isinstance(entry, dict):
                logger.warning(f"Skipping non-dict entry: {entry}")
                continue
                
            # Only add metadata if not present
            if '_crdt_metadata' not in entry:
                entry = self.inject_metadata(entry)
            prepared_entries.append(entry)
        
        logger.info(f"Prepared {len(prepared_entries)} entries from {memory_file_path}")
        return prepared_entries


class GitIntegration:
    """Handles Git operations for memory backup with retry logic."""
    
    def __init__(self, repo_path: str):
        """
        Initialize Git integration.
        
        Args:
            repo_path: Path to Git repository
            
        Raises:
            ValueError: If path is not a Git repository
        """
        self.repo_path = Path(repo_path)
        if not (self.repo_path / '.git').exists():
            raise ValueError(f"{repo_path} is not a Git repository")
    
    def backup_to_git(self, file_path: str, host_id: str) -> bool:
        """
        Backup memory file to Git with exponential backoff retry.
        
        Args:
            file_path: Path to file to backup
            host_id: Host identifier for commit message
            
        Returns:
            True if backup successful, False otherwise
        """
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # Pull latest changes first
                self._git_pull()
                
                # Perform atomic commit
                self.atomic_commit(file_path, host_id)
                
                # Push changes
                self._git_push(attempt)
                
                logger.info("Backup completed successfully")
                return True
                
            except subprocess.CalledProcessError as e:
                wait_time = 0.1 * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Git operation failed (attempt {attempt+1}/{max_attempts}): {e}")
                
                if attempt < max_attempts - 1:
                    logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("Max retry attempts reached. Backup failed.")
        
        return False
    
    def atomic_commit(self, file_path: str, host_id: str) -> None:
        """
        Perform atomic Git operations for backup.
        
        Args:
            file_path: Path to file to commit
            host_id: Host identifier for commit message
            
        Raises:
            subprocess.CalledProcessError: If Git command fails
        """
        try:
            # Copy file to repo if not already there
            file_path = Path(file_path)
            if not file_path.is_relative_to(self.repo_path):
                dest_path = self.repo_path / f"memory-{host_id}.json"
                shutil.copy2(file_path, dest_path)
                file_path = dest_path
            
            # Add file to staging
            subprocess.run(
                ['git', 'add', str(file_path.relative_to(self.repo_path))],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Commit with descriptive message
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            commit_msg = f"Memory backup from {host_id} at {timestamp}"
            
            # Try to commit, but handle the case where there are no changes
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            # Handle both success and "nothing to commit" cases
            if result.returncode == 0:
                logger.info(f"Committed backup for {host_id}")
            elif result.returncode == 1 and 'nothing to commit' in result.stdout:
                logger.info(f"No changes to commit for {host_id}")
            else:
                raise subprocess.CalledProcessError(result.returncode, 'git commit', result.stderr)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            raise
    
    def _git_pull(self) -> None:
        """Pull latest changes from remote."""
        try:
            subprocess.run(
                ['git', 'pull', '--rebase'],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git pull failed: {e.stderr}")
            # Continue anyway - might be first commit
    
    def _git_push(self, attempt: int) -> None:
        """
        Push changes to remote with retry.
        
        Args:
            attempt: Current attempt number for backoff calculation
            
        Raises:
            subprocess.CalledProcessError: If push fails
        """
        try:
            subprocess.run(
                ['git', 'push'],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Successfully pushed changes to remote")
        except subprocess.CalledProcessError as e:
            # For testing environments without remotes, we can skip push
            if 'No configured push destination' in e.stderr or 'fatal: No configured push destination' in e.stderr:
                logger.warning("No remote configured, skipping push (this is normal in test environments)")
                return
            raise
    
    def handle_conflicts(self) -> None:
        """
        Handle Git conflicts automatically using CRDT merge.
        
        This would be called when a push fails due to conflicts.
        """
        # Get list of conflicted files
        result = subprocess.run(
            ['git', 'diff', '--name-only', '--diff-filter=U'],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        conflicted_files = result.stdout.strip().split('\n')
        
        for file_path in conflicted_files:
            if file_path.endswith('.json'):
                # For JSON files, use CRDT merge
                self._resolve_json_conflict(file_path)
    
    def _resolve_json_conflict(self, file_path: str) -> None:
        """Resolve JSON file conflict using CRDT merge."""
        # This would parse the conflict markers and merge using CRDT
        # For now, we'll take the remote version
        subprocess.run(
            ['git', 'checkout', '--theirs', file_path],
            cwd=self.repo_path,
            check=True
        )
        subprocess.run(
            ['git', 'add', file_path],
            cwd=self.repo_path,
            check=True
        )


def crdt_merge(memory_lists: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Merge memory entries using Last-Write-Wins strategy.
    
    Args:
        memory_lists: List of memory entry lists to merge
        
    Returns:
        Merged list of entries with conflicts resolved
    """
    # First pass: collect all unique entries by unique_id
    all_entries: Dict[str, Dict[str, Any]] = {}
    for memory_list in memory_lists:
        for entry in memory_list:
            if not isinstance(entry, dict):
                continue
            
            if '_crdt_metadata' in entry:
                uid = entry['_crdt_metadata'].get('unique_id')
                if uid:
                    # Only keep if not seen or use LWW/unique_id tiebreaker
                    if uid not in all_entries:
                        all_entries[uid] = entry
                    else:
                        # If same unique_id, use timestamp-based tiebreaker with content fallback
                        existing = all_entries[uid]
                        existing_time = _parse_timestamp(existing['_crdt_metadata']['timestamp'])
                        new_time = _parse_timestamp(entry['_crdt_metadata']['timestamp'])
                        if new_time > existing_time:
                            all_entries[uid] = entry
                        elif new_time == existing_time:
                            # Final tiebreaker: lexicographic content comparison for determinism
                            if str(entry.get('content', '')) > str(existing.get('content', '')):
                                all_entries[uid] = entry
    
    # Second pass: group by entry ID for LWW merge
    entries_by_id: Dict[str, Dict[str, Any]] = {}
    
    for entry in all_entries.values():
        entry_id = entry.get('id', 'unknown')
        
        # LWW: Keep entry with newest timestamp  
        if entry_id not in entries_by_id:
            entries_by_id[entry_id] = entry
        else:
            existing = entries_by_id[entry_id]
            
            # Compare timestamps if metadata exists
            if '_crdt_metadata' in entry and '_crdt_metadata' in existing:
                existing_time = _parse_timestamp(existing['_crdt_metadata']['timestamp'])
                new_time = _parse_timestamp(entry['_crdt_metadata']['timestamp'])
                
                if new_time > existing_time:
                    entries_by_id[entry_id] = entry
                elif new_time == existing_time:
                    # Tiebreaker: use unique_id for deterministic ordering
                    existing_uid = existing['_crdt_metadata'].get('unique_id', '')
                    new_uid = entry['_crdt_metadata'].get('unique_id', '')
                    if new_uid > existing_uid:
                        entries_by_id[entry_id] = entry
    
    # Convert to list and sort by timestamp
    merged_entries = list(entries_by_id.values())
    
    # Sort by timestamp for consistent ordering
    def get_timestamp(entry):
        if '_crdt_metadata' in entry:
            return _parse_timestamp(entry['_crdt_metadata']['timestamp'])
        return datetime.min
    
    merged_entries.sort(key=get_timestamp)
    
    return merged_entries


def _parse_timestamp(timestamp: str) -> datetime:
    """Parse ISO format timestamp to datetime object."""
    # Replace 'Z' with '+00:00' to preserve UTC timezone information
    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CRDT-based memory backup system for parallel backups without locks"
    )
    parser.add_argument('--backup', action='store_true', help='Run backup operation')
    parser.add_argument('--merge', action='store_true', help='Merge memory files')
    parser.add_argument('--host', default=socket.gethostname(), help='Hostname identifier')
    parser.add_argument('--repo', help='Git repository path (default: current directory)')
    parser.add_argument('--file', help='Memory file path for backup')
    parser.add_argument('--output', help='Output file for merge operation')
    
    args = parser.parse_args()
    
    # Default repo to current directory
    if not args.repo:
        args.repo = os.getcwd()
    
    if args.backup:
        if not args.file:
            logger.error("--file is required for backup operation")
            sys.exit(1)
        
        try:
            crdt = MemoryBackupCRDT(args.host)
            git = GitIntegration(args.repo)
            
            # Prepare entries with metadata
            entries = crdt.prepare_memory_file(args.file)
            
            if not entries:
                logger.warning("No entries to backup")
                sys.exit(0)
            
            # Write to host-specific file in repo
            output_file = Path(args.repo) / f"memory-{args.host}.json"
            with open(output_file, 'w') as f:
                json.dump(entries, f, indent=2)
            
            # Backup to Git
            success = git.backup_to_git(str(output_file), args.host)
            sys.exit(0 if success else 1)
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            sys.exit(1)
    
    elif args.merge:
        # Merge all memory-*.json files in repo
        repo_path = Path(args.repo)
        memory_files = list(repo_path.glob("memory-*.json"))
        
        if not memory_files:
            logger.warning("No memory files found to merge")
            sys.exit(0)
        
        # Load all memory files
        all_entries = []
        for file_path in memory_files:
            try:
                with open(file_path, 'r') as f:
                    entries = json.load(f)
                    all_entries.append(entries)
                    logger.info(f"Loaded {len(entries)} entries from {file_path.name}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        # Merge using CRDT
        merged = crdt_merge(all_entries)
        logger.info(f"Merged {len(merged)} unique entries")
        
        # Write output
        output_file = args.output or (repo_path / "unified-memory.json")
        with open(output_file, 'w') as f:
            json.dump(merged, f, indent=2)
        
        logger.info(f"Merged memory saved to {output_file}")
        sys.exit(0)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()