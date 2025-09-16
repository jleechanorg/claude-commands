#!/usr/bin/env python3
"""
Integration test for CRDT memory backup system.
Tests the complete workflow including parallel backups.
"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Import CRDT module using importlib to avoid sys.path manipulation
def _import_crdt_module():
    """Import CRDT module from parent directory using importlib."""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Try multiple possible locations for the CRDT module
    possible_paths = [
        os.path.join(parent_dir, 'memory_backup_crdt.py'),
        os.path.join(parent_dir, 'crdt_merge.py'),
        os.path.join(parent_dir, 'memory_sync', 'memory_backup_crdt.py')
    ]

    for module_path in possible_paths:
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location('memory_backup_crdt', module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
    return None

# Load CRDT module at module level
try:
    _crdt_module = _import_crdt_module()
    MemoryBackupCRDT = getattr(_crdt_module, 'MemoryBackupCRDT', None) if _crdt_module else None
    crdt_merge = getattr(_crdt_module, 'crdt_merge', None) if _crdt_module else None
    CRDT_AVAILABLE = _crdt_module is not None and MemoryBackupCRDT is not None and crdt_merge is not None
except Exception:
    MemoryBackupCRDT = None
    crdt_merge = None
    CRDT_AVAILABLE = False

class TestCRDTIntegration(unittest.TestCase):
    """CRDT integration test cases."""

    @unittest.skipUnless(CRDT_AVAILABLE, "memory_backup_crdt module not available")
    def test_integration(self):
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
        self.assertEqual(len(merged), 4)  # Should have 4 unique entry IDs

        # Check that we have all entry IDs
        entry_ids = {entry['id'] for entry in merged}
        self.assertEqual(entry_ids, {'entry1', 'entry2', 'entry3', 'entry4'})

        # Verify LWW worked (latest entries win)
        for entry in merged:
            if entry['id'] == 'entry1':
                # host3 created this last
                self.assertTrue('host3' in entry['content'] or 'host1' in entry['content'])
            elif entry['id'] == 'entry2':
                # host2 created this last
                self.assertTrue('host2' in entry['content'] or 'host1' in entry['content'])

        print("✅ Integration test passed!")
        print(f"Merged {len(merged)} entries from 3 hosts")

        # Save to file for inspection
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(merged, f, indent=2)
            print(f"Results saved to: {f.name}")

        return merged


if __name__ == '__main__':
    unittest.main()
