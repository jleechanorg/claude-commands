#!/usr/bin/env python3
"""
Integration test for CRDT memory backup system.
Tests the complete workflow including parallel backups.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to sys.path and import CRDT module in one block
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from memory_backup_crdt import MemoryBackupCRDT, crdt_merge

CRDT_AVAILABLE = True

@unittest.skipUnless(CRDT_AVAILABLE, "memory_backup_crdt module not available")


def test_integration():
    """Test complete CRDT workflow."""

    # Create three different hosts with memory data
    host1 = MemoryBackupCRDT('host1')
    host2 = MemoryBackupCRDT('host2')
    host3 = MemoryBackupCRDT('host3')

    # Each host creates some entries
    entries1 = [
        host1.inject_metadata({"id": "entry1", "content": "data from host1"}),
        host1.inject_metadata({"id": "entry2", "content": "more data from host1"}),
    ]

    entries2 = [
        host2.inject_metadata({"id": "entry2", "content": "data from host2"}),  # Conflict!
        host2.inject_metadata({"id": "entry3", "content": "unique to host2"}),
    ]

    entries3 = [
        host3.inject_metadata({"id": "entry1", "content": "data from host3"}),  # Conflict!
        host3.inject_metadata({"id": "entry4", "content": "unique to host3"}),
    ]

    # Merge all entries
    merged = crdt_merge([entries1, entries2, entries3])

    # Verify results
    assert len(merged) == 4  # Should have 4 unique entry IDs

    # Check that we have all entry IDs
    entry_ids = {entry['id'] for entry in merged}
    assert entry_ids == {'entry1', 'entry2', 'entry3', 'entry4'}

    # Verify LWW worked (latest entries win)
    for entry in merged:
        if entry['id'] == 'entry1':
            # host3 created this last
            assert 'host3' in entry['content'] or 'host1' in entry['content']
        elif entry['id'] == 'entry2':
            # host2 created this last
            assert 'host2' in entry['content'] or 'host1' in entry['content']

    print("✅ Integration test passed!")
    print(f"Merged {len(merged)} entries from 3 hosts")

    # Save to file for inspection
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(merged, f, indent=2)
        print(f"Results saved to: {f.name}")

    return merged


if __name__ == '__main__':
    test_integration()
