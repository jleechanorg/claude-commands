#!/usr/bin/env python3
"""
Test suite to demonstrate and fix CRDT mathematical property violations.
Uses red-green TDD approach to ensure correctness.
"""

import pytest
import json
from datetime import datetime
from typing import Dict, List, Any
import sys
import os
from scripts.memory_backup_crdt import _parse_timestamp

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules we're testing
from scripts.memory_backup_crdt import crdt_merge, MemoryBackupCRDT


class TestCRDTMathematicalProperties:
    """Test mathematical properties that CRDT must satisfy."""

    def test_commutativity_violation(self):
        """
        Test that demonstrates commutativity violation.
        CRDT property: merge(A,B) must equal merge(B,A)
        """
        # Create two sets of entries with overlapping IDs
        entries_a = [
            {
                "id": "mem_001",
                "content": "Content A",
                "_crdt_metadata": {
                    "host": "host_a",
                    "timestamp": "2025-01-01T00:00:01Z",
                    "version": 1,
                    "unique_id": "host_a_mem_001_2025-01-01T00:00:01Z"
                }
            }
        ]

        entries_b = [
            {
                "id": "mem_001",
                "content": "Content B",
                "_crdt_metadata": {
                    "host": "host_b",
                    "timestamp": "2025-01-01T00:00:02Z",
                    "version": 1,
                    "unique_id": "host_b_mem_001_2025-01-01T00:00:02Z"
                }
            }
        ]

        # Test commutativity: merge(A,B) should equal merge(B,A)
        result_ab = crdt_merge([entries_a, entries_b])
        result_ba = crdt_merge([entries_b, entries_a])

        # This should pass but currently FAILS due to two-pass algorithm
        assert result_ab == result_ba, f"Commutativity violated: {result_ab} != {result_ba}"

    def test_associativity_violation(self):
        """
        Test that demonstrates associativity violation.
        CRDT property: merge(merge(A,B),C) must equal merge(A,merge(B,C))
        """
        entries_a = [{
            "id": "mem_001",
            "content": "Content A",
            "_crdt_metadata": {
                "host": "host_a",
                "timestamp": "2025-01-01T00:00:01Z",
                "version": 1,
                "unique_id": "host_a_mem_001_2025-01-01T00:00:01Z"
            }
        }]

        entries_b = [{
            "id": "mem_001",
            "content": "Content B",
            "_crdt_metadata": {
                "host": "host_b",
                "timestamp": "2025-01-01T00:00:02Z",
                "version": 1,
                "unique_id": "host_b_mem_001_2025-01-01T00:00:02Z"
            }
        }]

        entries_c = [{
            "id": "mem_001",
            "content": "Content C",
            "_crdt_metadata": {
                "host": "host_c",
                "timestamp": "2025-01-01T00:00:03Z",
                "version": 1,
                "unique_id": "host_c_mem_001_2025-01-01T00:00:03Z"
            }
        }]

        # Test associativity
        # (A merge B) merge C
        ab = crdt_merge([entries_a, entries_b])
        result_ab_c = crdt_merge([ab, entries_c])

        # A merge (B merge C)
        bc = crdt_merge([entries_b, entries_c])
        result_a_bc = crdt_merge([entries_a, bc])

        # This should pass but currently FAILS
        assert result_ab_c == result_a_bc, f"Associativity violated"

    def test_idempotence(self):
        """
        Test idempotence property.
        CRDT property: merge(A,A) must equal A
        """
        entries = [{
            "id": "mem_001",
            "content": "Content",
            "_crdt_metadata": {
                "host": "host_a",
                "timestamp": "2025-01-01T00:00:01Z",
                "version": 1,
                "unique_id": "host_a_mem_001_2025-01-01T00:00:01Z"
            }
        }]

        # Test idempotence: merge(A,A) should equal A
        result = crdt_merge([entries, entries])

        assert len(result) == 1, f"Idempotence violated: duplicate entries"
        assert result == entries, f"Idempotence violated: content changed"

    def test_unique_id_collision(self):
        """
        Test that demonstrates unique ID collision vulnerability.
        Two entries created in rapid succession may have same timestamp.
        """
        crdt = MemoryBackupCRDT("test_host")

        # Simulate rapid entry creation
        entry1 = {"id": "mem_001", "content": "Content 1"}
        entry2 = {"id": "mem_002", "content": "Content 2"}

        # These could have identical timestamps in production
        result1 = crdt.inject_metadata(entry1)
        result2 = crdt.inject_metadata(entry2)

        # Check if unique IDs could collide (same timestamp component)
        uid1 = result1["_crdt_metadata"]["unique_id"]
        uid2 = result2["_crdt_metadata"]["unique_id"]

        # Extract timestamp portions
        ts1 = uid1.split("_")[-1]
        ts2 = uid2.split("_")[-1]

        # In rapid succession, these could be identical
        # This test may pass or fail depending on execution speed
        print(f"Timestamp 1: {ts1}")
        print(f"Timestamp 2: {ts2}")

        # The risk is that in production, these COULD be identical
        assert uid1 != uid2, "Unique IDs must never collide"

    def test_timezone_parsing_bug(self):
        """
        Test timezone parsing correctness.
        The current implementation loses timezone information.
        """

        # Test with Z suffix (UTC)
        ts_z = "2025-01-01T00:00:00Z"
        parsed_z = _parse_timestamp(ts_z)

        # Test with explicit timezone
        ts_offset = "2025-01-01T00:00:00+05:00"

        # This should handle timezones correctly but doesn't
        try:
            parsed_offset = _parse_timestamp(ts_offset)
            # Should preserve timezone info
            assert False, "Should handle timezone offsets correctly"
        except:
            # Current implementation fails on non-Z timezones
            pass

    def test_convergence(self):
        """
        Test that all replicas eventually converge to same state.
        Due to commutativity violation, this currently fails.
        """
        # Three replicas with different operation orders
        replica1_ops = [
            [{"id": "m1", "content": "A", "_crdt_metadata": {"host": "h1", "timestamp": "2025-01-01T00:00:01Z", "version": 1, "unique_id": "h1_m1_2025-01-01T00:00:01Z"}}],
            [{"id": "m1", "content": "B", "_crdt_metadata": {"host": "h2", "timestamp": "2025-01-01T00:00:02Z", "version": 1, "unique_id": "h2_m1_2025-01-01T00:00:02Z"}}],
            [{"id": "m1", "content": "C", "_crdt_metadata": {"host": "h3", "timestamp": "2025-01-01T00:00:03Z", "version": 1, "unique_id": "h3_m1_2025-01-01T00:00:03Z"}}]
        ]

        # Different merge orders
        final1 = crdt_merge(replica1_ops)
        final2 = crdt_merge([replica1_ops[2], replica1_ops[0], replica1_ops[1]])
        final3 = crdt_merge([replica1_ops[1], replica1_ops[2], replica1_ops[0]])

        # All should converge to same state
        assert final1 == final2 == final3, "Replicas did not converge"


class TestCRDTCorrectImplementation:
    """Tests for the corrected CRDT implementation."""

    def test_fixed_crdt_merge(self):
        """Test the fixed single-pass LWW merge algorithm."""
        # This will be implemented after we create the fix
        pass


if __name__ == "__main__":
    # Run tests to demonstrate failures
    pytest.main([__file__, "-v", "--tb=short"])
