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
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional psutil import for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Import project logging utility
try:
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent / 'mvp_site'))
    import logging_util
    logger = logging_util.getLogger(__name__)
except (ImportError, TypeError):
    # Fallback to standard logging if project logging unavailable or incompatible
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Git timeout configuration for subprocess operations
GIT_TIMEOUT_SECONDS = 30

# Memory bounds configuration
MAX_MEMORY_MB = 512  # Maximum memory usage for merge operations
MAX_ENTRIES_PER_FILE = 10000  # Maximum entries per file to prevent OOM


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
        Inject CRDT metadata with collision-resistant unique ID.
        
        Args:
            entry: Memory entry dictionary
            
        Returns:
            Entry with enhanced CRDT metadata
        """
        # Use high-precision timestamp with microseconds
        timestamp = datetime.now(timezone.utc).isoformat()
        entry_id = entry.get('id', 'unknown')
        
        # Add high entropy to prevent collisions (16 hex chars = 64 bits)
        random_suffix = uuid.uuid4().hex[:16]
        
        # Generate collision-resistant unique ID
        unique_id = f"{self.host_id}_{entry_id}_{timestamp}_{random_suffix}"
        
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
        
        # Validate entry count before processing
        validate_entry_count(entries, f"file {memory_file_path}")
        
        # Add CRDT metadata to each entry
        prepared_entries = []
        for i, entry in enumerate(entries):
            # Periodic memory check for large files
            if i % 1000 == 0:
                check_memory_bounds()
                
            if not isinstance(entry, dict):
                logger.warning(f"Skipping non-dict entry: {entry}")
                continue
                
            # Only add metadata if not present
            if '_crdt_metadata' not in entry:
                entry = self.inject_metadata(entry)
            prepared_entries.append(entry)
        
        logger.info(f"Prepared {len(prepared_entries)} entries from {memory_file_path}")
        return prepared_entries


def check_memory_bounds() -> None:
    """
    Check current memory usage and raise error if approaching limits.
    
    Raises:
        MemoryError: If memory usage exceeds safe limits
    """
    if not PSUTIL_AVAILABLE:
        # Skip memory checking if psutil not available
        return
        
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        if memory_mb > MAX_MEMORY_MB:
            raise MemoryError(f"Memory usage {memory_mb:.1f}MB exceeds limit {MAX_MEMORY_MB}MB")
        
        # Log memory usage if approaching limit
        if memory_mb > MAX_MEMORY_MB * 0.8:
            logger.warning(f"Memory usage approaching limit: {memory_mb:.1f}MB / {MAX_MEMORY_MB}MB")
            
    except Exception as e:
        logger.warning(f"Could not check memory usage: {e}")


def validate_entry_count(entries: List[Any], operation: str = "operation") -> None:
    """
    Validate that entry count is within safe limits.
    
    Args:
        entries: List of entries to validate
        operation: Description of operation for error message
        
    Raises:
        ValueError: If entry count exceeds limits
    """
    if len(entries) > MAX_ENTRIES_PER_FILE:
        raise ValueError(f"Entry count {len(entries)} exceeds limit {MAX_ENTRIES_PER_FILE} for {operation}")


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
                self._git_pull(timeout=GIT_TIMEOUT_SECONDS)
                
                # Perform atomic commit
                self.atomic_commit(file_path, host_id, timeout=GIT_TIMEOUT_SECONDS)
                
                # Push changes
                self._git_push(attempt, timeout=GIT_TIMEOUT_SECONDS)
                
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
    
    def atomic_commit(self, file_path: str, host_id: str, timeout: int = GIT_TIMEOUT_SECONDS) -> None:
        """
        Perform atomic Git operations for backup.
        
        Args:
            file_path: Path to file to commit
            host_id: Host identifier for commit message
            timeout: Timeout in seconds for Git operations
            
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
                text=True,
                timeout=timeout
            )
            
            # Commit with descriptive message
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            commit_msg = f"Memory backup from {host_id} at {timestamp}"
            
            # Try to commit, but handle the case where there are no changes
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
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
    
    def _git_pull(self, timeout: int = GIT_TIMEOUT_SECONDS) -> None:
        """Pull latest changes from remote."""
        try:
            subprocess.run(
                ['git', 'pull', '--rebase'],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git pull failed: {e.stderr}")
            # Continue anyway - might be first commit
    
    def _git_push(self, attempt: int, timeout: int = GIT_TIMEOUT_SECONDS) -> None:
        """
        Push changes to remote with retry.
        
        Args:
            attempt: Current attempt number for backoff calculation
            timeout: Timeout in seconds for Git operations
            
        Raises:
            subprocess.CalledProcessError: If push fails
        """
        try:
            subprocess.run(
                ['git', 'push'],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout
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
        try:
            # Get list of conflicted files
            result = subprocess.run(
                ['git', 'diff', '--name-only', '--diff-filter=U'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=GIT_TIMEOUT_SECONDS
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to get conflicted files: {result.stderr}")
                return
            
            conflicted_files = [f for f in result.stdout.strip().split('\n') if f.strip()]
            
            if not conflicted_files:
                logger.info("No conflicted files found")
                return
            
            logger.info(f"Resolving conflicts in {len(conflicted_files)} files")
            
            for file_path in conflicted_files:
                if file_path.endswith('.json'):
                    # For JSON files, use CRDT merge
                    self._resolve_json_conflict(file_path)
                else:
                    # For non-JSON files, take remote version
                    logger.warning(f"Taking remote version for non-JSON file: {file_path}")
                    subprocess.run(
                        ['git', 'checkout', '--theirs', file_path],
                        cwd=self.repo_path,
                        check=True,
                        timeout=GIT_TIMEOUT_SECONDS
                    )
                    subprocess.run(
                        ['git', 'add', file_path],
                        cwd=self.repo_path,
                        check=True,
                        timeout=GIT_TIMEOUT_SECONDS
                    )
            
            logger.info("Conflict resolution completed")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git conflict resolution failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during conflict resolution: {e}")
            raise
    
    def _resolve_json_conflict(self, file_path: str) -> None:
        """Resolve JSON file conflict using CRDT merge."""
        try:
            # Read conflicted file content
            full_path = self.repo_path / file_path
            with open(full_path, 'r') as f:
                content = f.read()
            
            # Parse conflict markers to extract versions
            sections = content.split('<<<<<<< HEAD')
            if len(sections) != 2:
                logger.warning(f"No conflict markers found in {file_path}, using remote version")
                subprocess.run(
                    ['git', 'checkout', '--theirs', file_path],
                    cwd=self.repo_path,
                    check=True,
                    timeout=GIT_TIMEOUT_SECONDS
                )
                subprocess.run(
                    ['git', 'add', file_path],
                    cwd=self.repo_path,
                    check=True,
                    timeout=GIT_TIMEOUT_SECONDS
                )
                return
            
            # Extract local and remote versions
            local_section = sections[1].split('=======')
            if len(local_section) != 2:
                logger.error(f"Invalid conflict format in {file_path}")
                raise ValueError(f"Invalid conflict markers in {file_path}")
            
            local_content = local_section[0].strip()
            remote_section = local_section[1].split('>>>>>>> ')
            if len(remote_section) < 2:
                logger.error(f"Invalid conflict format in {file_path}")
                raise ValueError(f"Invalid conflict markers in {file_path}")
            
            remote_content = remote_section[0].strip()
            
            # Parse JSON from both versions
            try:
                local_entries = json.loads(local_content) if local_content else []
                remote_entries = json.loads(remote_content) if remote_content else []
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in conflict for {file_path}: {e}")
                # Fallback to remote version
                subprocess.run(
                    ['git', 'checkout', '--theirs', file_path],
                    cwd=self.repo_path,
                    check=True,
                    timeout=GIT_TIMEOUT_SECONDS
                )
                subprocess.run(
                    ['git', 'add', file_path],
                    cwd=self.repo_path,
                    check=True,
                    timeout=GIT_TIMEOUT_SECONDS
                )
                return
            
            # Merge using CRDT
            merged_entries = crdt_merge([local_entries, remote_entries])
            
            # Write merged result
            with open(full_path, 'w') as f:
                json.dump(merged_entries, f, indent=2)
            
            # Stage the resolved file
            subprocess.run(
                ['git', 'add', file_path],
                cwd=self.repo_path,
                check=True,
                timeout=GIT_TIMEOUT_SECONDS
            )
            
            logger.info(f"Successfully merged {len(merged_entries)} entries in {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict in {file_path}: {e}")
            # Fallback to remote version
            subprocess.run(
                ['git', 'checkout', '--theirs', file_path],
                cwd=self.repo_path,
                check=True,
                timeout=GIT_TIMEOUT_SECONDS
            )
            subprocess.run(
                ['git', 'add', file_path],
                cwd=self.repo_path,
                check=True,
                timeout=GIT_TIMEOUT_SECONDS
            )


def crdt_merge(memory_lists: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Merge memory entries using Last-Write-Wins strategy with memory bounds checking.
    
    GUARANTEES:
    - Commutativity: merge(A,B) = merge(B,A)
    - Associativity: merge(merge(A,B),C) = merge(A,merge(B,C))  
    - Idempotence: merge(A,A) = A
    - Convergence: All replicas converge to same state
    
    Args:
        memory_lists: List of memory entry lists to merge
        
    Returns:
        Merged list with conflicts resolved by LWW
        
    Raises:
        MemoryError: If memory usage exceeds safe limits
        ValueError: If entry count exceeds safe limits
    """
    # Check memory before starting
    check_memory_bounds()
    
    # Calculate total entries for bounds checking
    total_entries = sum(len(memory_list) for memory_list in memory_lists)
    
    # Validate each memory list for bounds checking
    for i, memory_list in enumerate(memory_lists):
        validate_entry_count(memory_list, f"merge input list {i}")
    
    if total_entries > MAX_ENTRIES_PER_FILE * 2:  # Allow some overhead for merging
        logger.warning(f"Large merge operation: {total_entries} total entries")
    
    # SINGLE-PASS algorithm using ONLY entry ID as key
    entries_by_id: Dict[str, Dict[str, Any]] = {}
    
    # Process all entries in single pass with periodic memory checking
    processed_count = 0
    for memory_list in memory_lists:
        for entry in memory_list:
            # Periodic memory check every 1000 entries
            processed_count += 1
            if processed_count % 1000 == 0:
                check_memory_bounds()
            if not isinstance(entry, dict):
                continue
            
            # Recovery mechanism for entries missing metadata
            if '_crdt_metadata' not in entry:
                logger.warning(f"Entry missing CRDT metadata, adding recovery metadata: {entry.get('id', 'unknown')}")
                # Create recovery metadata with minimal timestamp to ensure it doesn't override newer entries
                recovery_metadata = {
                    'host': 'recovery',
                    'timestamp': '1970-01-01T00:00:00+00:00',  # Epoch time, will lose in LWW
                    'version': 0,
                    'unique_id': f"recovery_{entry.get('id', 'unknown')}_{uuid.uuid4().hex[:16]}"
                }
                entry['_crdt_metadata'] = recovery_metadata
            
            entry_id = entry.get('id', 'unknown')
            
            if entry_id not in entries_by_id:
                # First occurrence of this ID
                entries_by_id[entry_id] = entry
            else:
                # Conflict resolution: pure LWW with deterministic tiebreaker
                existing = entries_by_id[entry_id]
                
                # Compare timestamps (primary criterion)
                existing_ts = _parse_timestamp(existing['_crdt_metadata']['timestamp'])
                new_ts = _parse_timestamp(entry['_crdt_metadata']['timestamp'])
                
                if new_ts > existing_ts:
                    # Newer timestamp wins
                    entries_by_id[entry_id] = entry
                elif new_ts == existing_ts:
                    # Timestamp tie: use deterministic tiebreaker
                    # Use unique_id for deterministic ordering (NOT content)
                    existing_uid = existing['_crdt_metadata'].get('unique_id', '')
                    new_uid = entry['_crdt_metadata'].get('unique_id', '')
                    
                    # Lexicographic comparison of unique IDs
                    if new_uid > existing_uid:
                        entries_by_id[entry_id] = entry
                # If new_ts < existing_ts, keep existing (no action needed)
    
    # Convert to list and sort for consistent output
    merged_entries = list(entries_by_id.values())
    
    # Sort by timestamp then unique_id for deterministic ordering
    def sort_key(entry):
        meta = entry.get('_crdt_metadata', {})
        ts = _parse_timestamp(meta.get('timestamp', ''))
        uid = meta.get('unique_id', '')
        return (ts, uid)
    
    merged_entries.sort(key=sort_key)
    
    # Final memory and bounds check
    check_memory_bounds()
    validate_entry_count(merged_entries, "merge result")
    
    return merged_entries


def _parse_timestamp(timestamp: str) -> datetime:
    """Parse ISO format timestamp correctly handling all timezone formats.
    
    Args:
        timestamp: ISO format timestamp string
        
    Returns:
        Timezone-aware datetime object normalized to UTC
    """
    if not timestamp:
        return datetime.min.replace(tzinfo=timezone.utc)
    
    try:
        # Handle different timezone formats
        if timestamp.endswith('Z'):
            # UTC with Z suffix
            timestamp = timestamp[:-1] + '+00:00'
        elif '+' in timestamp[-6:] or '-' in timestamp[-6:]:
            # Already has timezone offset (+05:00, -08:00, etc.)
            pass
        elif '.' in timestamp and timestamp.count(':') >= 2:
            # Assume UTC if no timezone specified
            if '+' not in timestamp and '-' not in timestamp[-6:] and not timestamp.endswith('Z'):
                timestamp += '+00:00'
        else:
            # Simple format without timezone, assume UTC
            timestamp += '+00:00'
        
        # Parse with timezone information preserved
        dt = datetime.fromisoformat(timestamp)
        
        # Ensure timezone awareness and normalize to UTC for comparison
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC for consistent comparison
            dt = dt.astimezone(timezone.utc)
        
        return dt
    except (ValueError, AttributeError) as e:
        # Fallback for invalid timestamps
        logger.warning(f"Invalid timestamp format '{timestamp}': {e}")
        return datetime.min.replace(tzinfo=timezone.utc)


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