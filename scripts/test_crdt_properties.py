# test_crdt_properties.py
"""
Property-based tests for CRDT mathematical properties using hypothesis.
Ensures the CRDT implementation maintains required mathematical guarantees.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
from typing import List, Dict, Any
from datetime import datetime
import copy

# Import the module we're testing
from memory_backup_crdt import crdt_merge


@composite
def memory_entry_strategy(draw):
    """Strategy to generate a single memory entry with CRDT metadata."""
    entry_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
    content = draw(st.text(min_size=0, max_size=100))
    host = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
    
    # Generate timestamp
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    
    timestamp = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"
    unique_id = f"{host}_{entry_id}_{timestamp}"
    
    return {
        "id": entry_id,
        "content": content,
        "_crdt_metadata": {
            "host": host,
            "timestamp": timestamp,
            "version": 1,
            "unique_id": unique_id
        }
    }


@composite
def memory_list_strategy(draw, min_size=1, max_size=10):
    """Strategy to generate a list of memory entries."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    entries = []
    used_ids = set()
    
    for _ in range(size):
        entry = draw(memory_entry_strategy())
        # Ensure some entries have the same ID for conflict testing
        if draw(st.booleans()) and used_ids:
            # Reuse an existing ID sometimes
            entry["id"] = draw(st.sampled_from(list(used_ids)))
            # But keep unique_id different
            entry["_crdt_metadata"]["unique_id"] = f"{entry['_crdt_metadata']['host']}_{entry['id']}_{entry['_crdt_metadata']['timestamp']}"
        else:
            used_ids.add(entry["id"])
        entries.append(entry)
    
    return entries


class TestCRDTMathematicalProperties:
    """Test mathematical properties that CRDT must satisfy."""
    
    @given(
        entries_a=memory_list_strategy(min_size=1, max_size=5),
        entries_b=memory_list_strategy(min_size=1, max_size=5)
    )
    @settings(max_examples=100, deadline=5000)
    def test_commutativity(self, entries_a, entries_b):
        """Test that merge operation is commutative: merge(A,B) = merge(B,A)."""
        # Deep copy to avoid mutation
        a_copy = copy.deepcopy(entries_a)
        b_copy = copy.deepcopy(entries_b)
        
        # Merge in different orders
        result_ab = crdt_merge([entries_a, entries_b])
        result_ba = crdt_merge([b_copy, a_copy])
        
        # Sort by unique_id for comparison
        result_ab_sorted = sorted(result_ab, key=lambda x: x['_crdt_metadata']['unique_id'])
        result_ba_sorted = sorted(result_ba, key=lambda x: x['_crdt_metadata']['unique_id'])
        
        # Should be equal regardless of merge order
        assert len(result_ab_sorted) == len(result_ba_sorted)
        for i in range(len(result_ab_sorted)):
            assert result_ab_sorted[i] == result_ba_sorted[i]

    @given(
        entries_a=memory_list_strategy(min_size=1, max_size=3),
        entries_b=memory_list_strategy(min_size=1, max_size=3),
        entries_c=memory_list_strategy(min_size=1, max_size=3)
    )
    @settings(max_examples=50, deadline=5000)
    def test_associativity(self, entries_a, entries_b, entries_c):
        """Test that merge operation is associative: merge(merge(A,B),C) = merge(A,merge(B,C))."""
        # Deep copy to avoid mutation
        a_copy1 = copy.deepcopy(entries_a)
        a_copy2 = copy.deepcopy(entries_a)
        b_copy1 = copy.deepcopy(entries_b)
        b_copy2 = copy.deepcopy(entries_b)
        c_copy1 = copy.deepcopy(entries_c)
        c_copy2 = copy.deepcopy(entries_c)
        
        # Left grouping: (A merge B) merge C
        ab_merged = crdt_merge([a_copy1, b_copy1])
        result_left = crdt_merge([ab_merged, c_copy1])
        
        # Right grouping: A merge (B merge C)
        bc_merged = crdt_merge([b_copy2, c_copy2])
        result_right = crdt_merge([a_copy2, bc_merged])
        
        # Sort for comparison
        result_left_sorted = sorted(result_left, key=lambda x: x['_crdt_metadata']['unique_id'])
        result_right_sorted = sorted(result_right, key=lambda x: x['_crdt_metadata']['unique_id'])
        
        # Should be equal regardless of grouping
        assert len(result_left_sorted) == len(result_right_sorted)
        for i in range(len(result_left_sorted)):
            assert result_left_sorted[i] == result_right_sorted[i]

    @given(entries=memory_list_strategy(min_size=1, max_size=10))
    @settings(max_examples=100, deadline=5000)
    def test_idempotence(self, entries):
        """Test that merge operation is idempotent: merge(A,A) = A."""
        # Deep copy for comparison
        entries_copy = copy.deepcopy(entries)
        
        # Merge with itself
        result = crdt_merge([entries, entries_copy])
        
        # Should be the same as original (possibly reordered)
        result_sorted = sorted(result, key=lambda x: x['_crdt_metadata']['unique_id'])
        entries_sorted = sorted(entries, key=lambda x: x['_crdt_metadata']['unique_id'])
        
        # For idempotence with LWW, we expect the same unique entries
        unique_ids_result = {e['_crdt_metadata']['unique_id'] for e in result_sorted}
        unique_ids_original = {e['_crdt_metadata']['unique_id'] for e in entries_sorted}
        
        # Should have same number of unique entries
        assert len(unique_ids_result) == len(unique_ids_original)

    @given(
        replica1=memory_list_strategy(min_size=1, max_size=5),
        replica2=memory_list_strategy(min_size=1, max_size=5),
        replica3=memory_list_strategy(min_size=1, max_size=5)
    )
    @settings(max_examples=50, deadline=5000)
    def test_convergence(self, replica1, replica2, replica3):
        """Test that all replicas eventually reach the same state."""
        # Each replica starts with its own data
        r1 = copy.deepcopy(replica1)
        r2 = copy.deepcopy(replica2)
        r3 = copy.deepcopy(replica3)
        
        # Simulate different merge orders
        # Replica 1: merges with 2, then with 3
        state1 = crdt_merge([r1, r2])
        state1 = crdt_merge([state1, r3])
        
        # Replica 2: merges with 3, then with 1
        r1_copy = copy.deepcopy(replica1)
        r2_copy = copy.deepcopy(replica2)
        r3_copy = copy.deepcopy(replica3)
        state2 = crdt_merge([r2_copy, r3_copy])
        state2 = crdt_merge([state2, r1_copy])
        
        # Replica 3: merges with 1, then with 2
        r1_copy2 = copy.deepcopy(replica1)
        r2_copy2 = copy.deepcopy(replica2)
        r3_copy2 = copy.deepcopy(replica3)
        state3 = crdt_merge([r3_copy2, r1_copy2])
        state3 = crdt_merge([state3, r2_copy2])
        
        # All should converge to the same state
        state1_sorted = sorted(state1, key=lambda x: x['_crdt_metadata']['unique_id'])
        state2_sorted = sorted(state2, key=lambda x: x['_crdt_metadata']['unique_id'])
        state3_sorted = sorted(state3, key=lambda x: x['_crdt_metadata']['unique_id'])
        
        # All states should be identical
        assert len(state1_sorted) == len(state2_sorted) == len(state3_sorted)
        for i in range(len(state1_sorted)):
            assert state1_sorted[i] == state2_sorted[i] == state3_sorted[i]


class TestCRDTConflictResolution:
    """Test CRDT conflict resolution properties."""
    
    @given(
        host1=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        host2=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        content1=st.text(min_size=1, max_size=50),
        content2=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=50)
    def test_deterministic_conflict_resolution(self, host1, host2, content1, content2):
        """Test that conflict resolution is deterministic."""
        assume(host1 != host2)  # Different hosts
        assume(content1 != content2)  # Different content
        
        # Create conflicting entries (same ID, different content)
        entry1 = {
            "id": "conflict_id",
            "content": content1,
            "_crdt_metadata": {
                "host": host1,
                "timestamp": "2025-01-01T00:00:00Z",
                "version": 1,
                "unique_id": f"{host1}_conflict_id_2025-01-01T00:00:00Z"
            }
        }
        
        entry2 = {
            "id": "conflict_id",
            "content": content2,
            "_crdt_metadata": {
                "host": host2,
                "timestamp": "2025-01-01T00:00:01Z",  # Newer
                "version": 1,
                "unique_id": f"{host2}_conflict_id_2025-01-01T00:00:01Z"
            }
        }
        
        # Merge multiple times in different orders
        result1 = crdt_merge([[entry1], [entry2]])
        result2 = crdt_merge([[entry2], [entry1]])
        result3 = crdt_merge([[entry1, entry2]])
        result4 = crdt_merge([[entry2, entry1]])
        
        # All should resolve to the same winner (newer timestamp)
        assert len(result1) == len(result2) == len(result3) == len(result4) == 1
        assert result1[0] == result2[0] == result3[0] == result4[0]
        assert result1[0]['content'] == content2  # Newer entry wins
        assert result1[0]['_crdt_metadata']['host'] == host2


class TestCRDTMonotonicity:
    """Test that CRDT operations are monotonic."""
    
    @given(
        initial=memory_list_strategy(min_size=1, max_size=5),
        additional=memory_list_strategy(min_size=1, max_size=5)
    )
    @settings(max_examples=50)
    def test_monotonic_growth(self, initial, additional):
        """Test that merge operations only add or update, never remove entries."""
        # Get initial state
        initial_merged = crdt_merge([initial])
        initial_ids = {e['_crdt_metadata']['unique_id'] for e in initial_merged}
        
        # Merge with additional data
        combined = crdt_merge([initial, additional])
        combined_ids = {e['_crdt_metadata']['unique_id'] for e in combined}
        
        # Combined should contain all initial IDs (monotonic growth)
        # Note: With LWW, unique_ids might change, but entry IDs should be preserved
        initial_entry_ids = {e['id'] for e in initial_merged}
        combined_entry_ids = {e['id'] for e in combined}
        
        # All initial entry IDs should still be present
        assert initial_entry_ids.issubset(combined_entry_ids)
        
        # Combined should have at least as many unique entries
        assert len(combined_ids) >= len(set(e['id'] for e in initial_merged))


class TestCRDTEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_merge(self):
        """Test merging empty lists."""
        result = crdt_merge([])
        assert result == []
        
        result = crdt_merge([[], []])
        assert result == []

    def test_single_entry_merge(self):
        """Test merging single entries."""
        entry = {
            "id": "single",
            "content": "content",
            "_crdt_metadata": {
                "host": "host1",
                "timestamp": "2025-01-01T00:00:00Z",
                "version": 1,
                "unique_id": "host1_single_2025-01-01T00:00:00Z"
            }
        }
        
        result = crdt_merge([[entry]])
        assert len(result) == 1
        assert result[0] == entry

    @given(num_duplicates=st.integers(min_value=2, max_value=10))
    def test_many_duplicates(self, num_duplicates):
        """Test merging many duplicate entries."""
        base_entry = {
            "id": "duplicate",
            "content": "original",
            "_crdt_metadata": {
                "host": "host0",
                "timestamp": "2025-01-01T00:00:00Z",
                "version": 1,
                "unique_id": "host0_duplicate_2025-01-01T00:00:00Z"
            }
        }
        
        # Create duplicates with different timestamps
        duplicates = []
        for i in range(num_duplicates):
            entry = copy.deepcopy(base_entry)
            entry["content"] = f"content_{i}"
            entry["_crdt_metadata"]["host"] = f"host{i}"
            entry["_crdt_metadata"]["timestamp"] = f"2025-01-01T00:00:{i:02d}Z"
            entry["_crdt_metadata"]["unique_id"] = f"host{i}_duplicate_2025-01-01T00:00:{i:02d}Z"
            duplicates.append([entry])
        
        result = crdt_merge(duplicates)
        
        # Should have only one entry (last one wins)
        assert len(result) == 1
        assert result[0]["content"] == f"content_{num_duplicates-1}"

    def test_large_timestamp_differences(self):
        """Test entries with large timestamp differences."""
        entry_old = {
            "id": "time_test",
            "content": "very old",
            "_crdt_metadata": {
                "host": "host1",
                "timestamp": "2020-01-01T00:00:00Z",
                "version": 1,
                "unique_id": "host1_time_test_2020-01-01T00:00:00Z"
            }
        }
        
        entry_new = {
            "id": "time_test",
            "content": "very new",
            "_crdt_metadata": {
                "host": "host2",
                "timestamp": "2030-12-31T23:59:59Z",
                "version": 1,
                "unique_id": "host2_time_test_2030-12-31T23:59:59Z"
            }
        }
        
        result = crdt_merge([[entry_old], [entry_new]])
        
        # Newer should win regardless of time difference
        assert len(result) == 1
        assert result[0]["content"] == "very new"