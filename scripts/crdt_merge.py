#!/usr/bin/env python3
"""
Pure CRDT merge functions for memory backup system.
Implements Last-Write-Wins (LWW) conflict resolution.
"""

import json
import socket
import sys
from datetime import UTC, datetime
from typing import Any


def add_crdt_metadata(
    entry: dict[str, Any],
    host: str | None = None,
    timestamp: str | None = None
) -> dict[str, Any]:
    """
    Add CRDT metadata to a memory entry.

    Args:
        entry: Memory entry dictionary
        host: Hostname (defaults to current hostname)
        timestamp: ISO timestamp (defaults to current UTC time)

    Returns:
        Entry with CRDT metadata added
    """
    if host is None:
        host = socket.gethostname()

    if timestamp is None:
        timestamp = datetime.now(UTC).isoformat().replace('+00:00', 'Z')

    # Get entry ID for unique ID generation
    entry_id = entry.get('id', 'unknown')

    # Version increment if metadata exists
    version = 1
    if '_crdt_metadata' in entry:
        old_meta = entry.get('_crdt_metadata', {})
        if isinstance(old_meta, dict):
            version = old_meta.get('version', 0) + 1

    # Generate unique ID
    unique_id = f"{host}_{entry_id}_{timestamp}"

    entry['_crdt_metadata'] = {
        'host': host,
        'timestamp': timestamp,
        'version': version,
        'unique_id': unique_id
    }

    return entry


def merge_by_lww(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Merge entries using Last-Write-Wins strategy.

    Args:
        entries: List of entries to merge

    Returns:
        Merged list with conflicts resolved by LWW
    """
    # Group entries by ID
    entries_by_id: dict[str, list[dict[str, Any]]] = {}

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        entry_id = entry.get('id', 'unknown')

        if entry_id not in entries_by_id:
            entries_by_id[entry_id] = []
        entries_by_id[entry_id].append(entry)

    # Resolve conflicts using LWW
    merged_entries = []

    for entry_id, entry_group in entries_by_id.items():
        if len(entry_group) == 1:
            merged_entries.append(entry_group[0])
        else:
            # Find entry with newest timestamp
            winner = entry_group[0]
            winner_time = _get_entry_timestamp(winner)

            for entry in entry_group[1:]:
                entry_time = _get_entry_timestamp(entry)
                if entry_time > winner_time:
                    winner = entry
                    winner_time = entry_time

            merged_entries.append(winner)

    # Sort by timestamp
    merged_entries.sort(key=_get_entry_timestamp)

    return merged_entries


def validate_crdt_structure(entry: dict[str, Any]) -> bool:
    """
    Validate that an entry has proper CRDT metadata structure.

    Args:
        entry: Entry to validate

    Returns:
        True if valid CRDT structure, False otherwise
    """
    if not isinstance(entry, dict):
        return False

    metadata = entry.get('_crdt_metadata')
    if metadata is None:
        return False

    if not isinstance(metadata, dict):
        return False

    required_fields = ['host', 'timestamp', 'version', 'unique_id']
    return all(field in metadata for field in required_fields)


def _get_entry_timestamp(entry: dict[str, Any]) -> datetime:
    """
    Get timestamp from entry metadata.

    Args:
        entry: Entry with potential CRDT metadata

    Returns:
        Datetime object for sorting
    """
    if '_crdt_metadata' in entry:
        metadata = entry['_crdt_metadata']
        if isinstance(metadata, dict) and 'timestamp' in metadata:
            return _parse_timestamp(metadata['timestamp'])

    # Return minimum datetime if no metadata
    return datetime.min


def _parse_timestamp(timestamp: str) -> datetime:
    """
    Parse ISO format timestamp to datetime object.

    Args:
        timestamp: ISO format timestamp string

    Returns:
        Datetime object
    """
    # Replace 'Z' with '+00:00' to preserve UTC timezone information
    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))


def compare_timestamps(ts1: str, ts2: str) -> int:
    """
    Compare two timestamps.

    Args:
        ts1: First timestamp
        ts2: Second timestamp

    Returns:
        -1 if ts1 < ts2, 0 if equal, 1 if ts1 > ts2
    """
    t1 = _parse_timestamp(ts1)
    t2 = _parse_timestamp(ts2)

    if t1 < t2:
        return -1
    if t1 > t2:
        return 1
    return 0


def create_unified_memory(memory_files: list[str]) -> list[dict[str, Any]]:
    """
    Create unified memory from multiple memory files.

    Args:
        memory_files: List of paths to memory JSON files

    Returns:
        Unified memory with CRDT merge applied
    """
    all_entries = []

    for file_path in memory_files:
        try:
            with open(file_path) as f:
                entries = json.load(f)
                if isinstance(entries, list):
                    all_entries.extend(entries)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading {file_path}: {e}")
            continue

    # Apply LWW merge
    return merge_by_lww(all_entries)


def main():
    """Command-line interface for testing CRDT merge."""

    if len(sys.argv) < 2:
        print("Usage: crdt_merge.py <memory_file1.json> [memory_file2.json ...]")
        sys.exit(1)

    memory_files = sys.argv[1:]
    merged = create_unified_memory(memory_files)

    # Output merged result
    print(json.dumps(merged, indent=2))


if __name__ == '__main__':
    main()
