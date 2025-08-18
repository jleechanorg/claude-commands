#!/usr/bin/env python3
"""
Simplified test to demonstrate CRDT violations without import issues.
Red-Green TDD approach.
"""

import sys
import json
from datetime import datetime


def simple_crdt_merge(memory_lists):
    """Current implementation from memory_backup_crdt.py (simplified)"""
    # First pass: collect all unique entries by unique_id
    all_entries = {}
    for memory_list in memory_lists:
        for entry in memory_list:
            if not isinstance(entry, dict):
                continue
            
            if '_crdt_metadata' in entry:
                uid = entry['_crdt_metadata'].get('unique_id')
                if uid:
                    if uid not in all_entries:
                        all_entries[uid] = entry
                    else:
                        # If same unique_id, use deterministic selection
                        existing_content = str(all_entries[uid].get('content', ''))
                        new_content = str(entry.get('content', ''))
                        if new_content > existing_content:
                            all_entries[uid] = entry
    
    # Second pass: group by entry ID for LWW merge
    entries_by_id = {}
    
    for entry in all_entries.values():
        entry_id = entry.get('id', 'unknown')
        
        # LWW: Keep entry with newest timestamp  
        if entry_id not in entries_by_id:
            entries_by_id[entry_id] = entry
        else:
            existing = entries_by_id[entry_id]
            
            # Compare timestamps if metadata exists
            if '_crdt_metadata' in entry and '_crdt_metadata' in existing:
                existing_time = existing['_crdt_metadata']['timestamp']
                new_time = entry['_crdt_metadata']['timestamp']
                
                if new_time > existing_time:
                    entries_by_id[entry_id] = entry
                elif new_time == existing_time:
                    # Tiebreaker: use unique_id for deterministic ordering
                    existing_uid = existing['_crdt_metadata'].get('unique_id', '')
                    new_uid = entry['_crdt_metadata'].get('unique_id', '')
                    if new_uid > existing_uid:
                        entries_by_id[entry_id] = entry
    
    return list(entries_by_id.values())


def test_commutativity():
    """Test: merge(A,B) should equal merge(B,A)"""
    print("\n🔴 TEST 1: Commutativity")
    
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
    
    # Test commutativity
    result_ab = simple_crdt_merge([entries_a, entries_b])
    result_ba = simple_crdt_merge([entries_b, entries_a])
    
    print(f"merge(A,B) = {json.dumps(result_ab[0]['content'] if result_ab else 'empty')}")
    print(f"merge(B,A) = {json.dumps(result_ba[0]['content'] if result_ba else 'empty')}")
    
    if result_ab == result_ba:
        print("✅ PASS: Commutativity holds")
        return True
    else:
        print("❌ FAIL: Commutativity violated!")
        return False


def test_associativity():
    """Test: merge(merge(A,B),C) should equal merge(A,merge(B,C))"""
    print("\n🔴 TEST 2: Associativity")
    
    entries_a = [{
        "id": "mem_001",
        "content": "A",
        "_crdt_metadata": {
            "host": "host_a",
            "timestamp": "2025-01-01T00:00:01Z",
            "version": 1,
            "unique_id": "host_a_mem_001_2025-01-01T00:00:01Z"
        }
    }]
    
    entries_b = [{
        "id": "mem_001",
        "content": "B",
        "_crdt_metadata": {
            "host": "host_b",
            "timestamp": "2025-01-01T00:00:02Z",
            "version": 1,
            "unique_id": "host_b_mem_001_2025-01-01T00:00:02Z"
        }
    }]
    
    entries_c = [{
        "id": "mem_001",
        "content": "C",
        "_crdt_metadata": {
            "host": "host_c",
            "timestamp": "2025-01-01T00:00:03Z",
            "version": 1,
            "unique_id": "host_c_mem_001_2025-01-01T00:00:03Z"
        }
    }]
    
    # (A merge B) merge C
    ab = simple_crdt_merge([entries_a, entries_b])
    result_ab_c = simple_crdt_merge([ab, entries_c])
    
    # A merge (B merge C)
    bc = simple_crdt_merge([entries_b, entries_c])
    result_a_bc = simple_crdt_merge([entries_a, bc])
    
    print(f"((A∪B)∪C) = {result_ab_c[0]['content'] if result_ab_c else 'empty'}")
    print(f"(A∪(B∪C)) = {result_a_bc[0]['content'] if result_a_bc else 'empty'}")
    
    if result_ab_c == result_a_bc:
        print("✅ PASS: Associativity holds")
        return True
    else:
        print("❌ FAIL: Associativity violated!")
        return False


def test_idempotence():
    """Test: merge(A,A) should equal A"""
    print("\n🔴 TEST 3: Idempotence")
    
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
    
    result = simple_crdt_merge([entries, entries])
    
    print(f"Original: {entries}")
    print(f"merge(A,A): {result}")
    
    if len(result) == 1 and result == entries:
        print("✅ PASS: Idempotence holds")
        return True
    else:
        print("❌ FAIL: Idempotence violated!")
        return False


def fixed_crdt_merge(memory_lists):
    """Fixed single-pass LWW merge that preserves mathematical properties."""
    entries_by_id = {}
    
    for memory_list in memory_lists:
        for entry in memory_list:
            if not isinstance(entry, dict) or '_crdt_metadata' not in entry:
                continue
                
            entry_id = entry.get('id', 'unknown')
            
            if entry_id not in entries_by_id:
                entries_by_id[entry_id] = entry
            else:
                # Pure LWW comparison - single criterion
                existing = entries_by_id[entry_id]
                existing_ts = existing['_crdt_metadata']['timestamp']
                new_ts = entry['_crdt_metadata']['timestamp']
                
                if new_ts > existing_ts:
                    entries_by_id[entry_id] = entry
                elif new_ts == existing_ts:
                    # Deterministic tiebreaker using unique_id
                    existing_uid = existing['_crdt_metadata'].get('unique_id', '')
                    new_uid = entry['_crdt_metadata'].get('unique_id', '')
                    if new_uid > existing_uid:
                        entries_by_id[entry_id] = entry
    
    return list(entries_by_id.values())


def test_fixed_implementation():
    """Test the fixed implementation."""
    print("\n🟢 TESTING FIXED IMPLEMENTATION")
    
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
    
    # Test commutativity with fixed version
    result_ab = fixed_crdt_merge([entries_a, entries_b])
    result_ba = fixed_crdt_merge([entries_b, entries_a])
    
    print(f"Fixed merge(A,B) = {result_ab[0]['content'] if result_ab else 'empty'}")
    print(f"Fixed merge(B,A) = {result_ba[0]['content'] if result_ba else 'empty'}")
    
    if result_ab == result_ba:
        print("✅ FIXED: Commutativity now holds!")
        return True
    else:
        print("❌ Still broken")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("CRDT MATHEMATICAL PROPERTY TESTS")
    print("=" * 60)
    
    # Run tests on current implementation
    results = []
    results.append(test_commutativity())
    results.append(test_associativity())
    results.append(test_idempotence())
    
    print("\n" + "=" * 60)
    print("CURRENT IMPLEMENTATION RESULTS:")
    failures = sum(1 for r in results if not r)
    print(f"❌ {failures} FAILURES out of 3 tests")
    
    print("\n" + "=" * 60)
    print("TESTING FIXED IMPLEMENTATION:")
    test_fixed_implementation()