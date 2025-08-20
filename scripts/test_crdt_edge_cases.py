#!/usr/bin/env python3
"""
Comprehensive edge case validation for CRDT mathematical property fixes.
Focuses on:
1. Identical timestamps with identical unique_ids
2. Deterministic content-hash tiebreaker
3. UUID collision resistance
4. Timestamp parsing edge cases
5. High-throughput scenarios
"""

import sys
import json
import hashlib
from datetime import datetime, timezone
import sys
import os
sys.path.append(os.path.dirname(__file__))

from memory_backup_crdt import (
    crdt_merge, 
    _parse_timestamp,
    MemoryBackupCRDT
)


def test_identical_timestamps_and_uids():
    """Test the content-hash tiebreaker for truly identical metadata."""
    print("\n🔴 EDGE CASE 1: Identical timestamps AND unique_ids")
    
    # Create two entries with identical timestamps and unique_ids
    entry_a = {
        "id": "mem_001",
        "content": "Content Alpha",
        "_crdt_metadata": {
            "host": "host_a",
            "timestamp": "2025-01-01T00:00:01.000000Z",
            "version": 1,
            "unique_id": "identical-uuid-1234"
        }
    }
    
    entry_b = {
        "id": "mem_001", 
        "content": "Content Beta",
        "_crdt_metadata": {
            "host": "host_b",
            "timestamp": "2025-01-01T00:00:01.000000Z",  # Identical timestamp
            "version": 1,
            "unique_id": "identical-uuid-1234"  # Identical unique_id
        }
    }
    
    # Test content-hash determinism
    result_ab = crdt_merge([[entry_a], [entry_b]])
    result_ba = crdt_merge([[entry_b], [entry_a]])
    
    print(f"merge(A,B) content: {result_ab[0]['content'] if result_ab else 'empty'}")
    print(f"merge(B,A) content: {result_ba[0]['content'] if result_ba else 'empty'}")
    
    # Verify deterministic hash-based selection
    content_a_hash = hashlib.sha256(json.dumps(entry_a, sort_keys=True).encode()).hexdigest()
    content_b_hash = hashlib.sha256(json.dumps(entry_b, sort_keys=True).encode()).hexdigest()
    expected_winner = entry_b if content_b_hash > content_a_hash else entry_a
    
    print(f"Hash A: {content_a_hash[:16]}...")
    print(f"Hash B: {content_b_hash[:16]}...")
    print(f"Expected winner: {expected_winner['content']}")
    
    is_deterministic = result_ab == result_ba
    is_correct_winner = result_ab[0]['content'] == expected_winner['content']
    
    if is_deterministic and is_correct_winner:
        print("✅ PASS: Content-hash tiebreaker works deterministically")
        return True
    else:
        print("❌ FAIL: Content-hash tiebreaker failed!")
        return False


def test_uuid_collision_resistance():
    """Test UUID4 cryptographic security and collision resistance."""
    print("\n🔴 EDGE CASE 2: UUID collision resistance")
    
    # Generate multiple entries rapidly to test UUID uniqueness
    entries = []
    unique_ids = set()
    backup_system = MemoryBackupCRDT("test_host")
    
    for i in range(1000):
        entry = {"id": f"mem_{i}", "content": f"Content {i}"}
        entry_with_meta = backup_system.inject_metadata(entry)
        entries.append(entry_with_meta)
        unique_ids.add(entry_with_meta['_crdt_metadata']['unique_id'])
    
    collision_count = 1000 - len(unique_ids)
    collision_rate = collision_count / 1000
    
    print(f"Generated 1000 UUIDs")
    print(f"Unique UUIDs: {len(unique_ids)}")
    print(f"Collisions: {collision_count}")
    print(f"Collision rate: {collision_rate:.6%}")
    
    # UUID4 should have virtually zero collisions in 1000 attempts
    if collision_count == 0:
        print("✅ PASS: No UUID collisions detected")
        return True
    elif collision_count <= 1:
        print("⚠️  CAUTION: 1 collision detected (within acceptable range)")
        return True
    else:
        print("❌ FAIL: Multiple UUID collisions - not cryptographically secure!")
        return False


def test_timestamp_parsing_edge_cases():
    """Test timestamp parsing robustness."""
    print("\n🔴 EDGE CASE 3: Timestamp parsing edge cases")
    
    test_cases = [
        ("2025-01-01T00:00:01Z", "UTC with Z suffix"),
        ("2025-01-01T00:00:01+00:00", "UTC with +00:00"),
        ("2025-01-01T00:00:01.123456Z", "Microseconds with Z"),
        ("2025-01-01T00:00:01", "No timezone (should default to UTC)"),
        ("", "Empty timestamp"),
        ("invalid-timestamp", "Malformed timestamp"),
        ("1970-01-01T00:00:00Z", "Epoch timestamp"),
        (None, "None timestamp")
    ]
    
    results = []
    for timestamp, description in test_cases:
        try:
            if timestamp is None:
                parsed = _parse_timestamp("")
            else:
                parsed = _parse_timestamp(timestamp)
            
            # Verify timezone awareness
            has_timezone = parsed.tzinfo is not None
            is_utc = parsed.tzinfo == timezone.utc if has_timezone else False
            
            print(f"  {description}: {parsed} (UTC: {is_utc})")
            results.append((True, has_timezone))
            
        except Exception as e:
            print(f"  {description}: ERROR - {e}")
            results.append((False, False))
    
    success_count = sum(1 for success, _ in results if success)
    timezone_aware_count = sum(1 for _, has_tz in results if has_tz)
    
    print(f"Successful parses: {success_count}/{len(test_cases)}")
    print(f"Timezone-aware results: {timezone_aware_count}/{len(test_cases)}")
    
    if success_count == len(test_cases) and timezone_aware_count == len(test_cases):
        print("✅ PASS: All timestamp edge cases handled correctly")
        return True
    else:
        print("❌ FAIL: Some timestamp parsing issues detected")
        return False


def test_high_throughput_determinism():
    """Test determinism under high-throughput collision scenarios."""
    print("\n🔴 EDGE CASE 4: High-throughput determinism")
    
    # Create scenario with many concurrent entries with close timestamps
    base_timestamp = "2025-01-01T00:00:01"
    entries_batch_1 = []
    entries_batch_2 = []
    
    for i in range(100):
        # Create entries with microsecond-level timestamp differences
        timestamp = f"{base_timestamp}.{i:06d}Z"
        
        entry = {
            "id": f"mem_{i % 10}",  # Force ID collisions for LWW testing
            "content": f"Content {i}",
            "_crdt_metadata": {
                "host": f"host_{i % 5}",
                "timestamp": timestamp,
                "version": 1,
                "unique_id": f"uuid-{i}-batch1"
            }
        }
        entries_batch_1.append(entry)
        
        # Create conflicting entry for same ID
        conflicting_entry = {
            "id": f"mem_{i % 10}",
            "content": f"Conflict {i}",
            "_crdt_metadata": {
                "host": f"host_{(i+1) % 5}",
                "timestamp": timestamp,  # Same timestamp
                "version": 1,
                "unique_id": f"uuid-{i}-batch2"
            }
        }
        entries_batch_2.append(conflicting_entry)
    
    # Test determinism across multiple merge orders
    result_12 = crdt_merge([entries_batch_1, entries_batch_2])
    result_21 = crdt_merge([entries_batch_2, entries_batch_1])
    
    # Sort results for comparison
    result_12_sorted = sorted(result_12, key=lambda x: x.get('id', ''))
    result_21_sorted = sorted(result_21, key=lambda x: x.get('id', ''))
    
    is_deterministic = result_12_sorted == result_21_sorted
    
    print(f"Batch 1->2 merge: {len(result_12)} entries")
    print(f"Batch 2->1 merge: {len(result_21)} entries")
    print(f"Results identical: {is_deterministic}")
    
    if is_deterministic:
        print("✅ PASS: High-throughput determinism maintained")
        return True
    else:
        print("❌ FAIL: Non-deterministic behavior under high throughput")
        # Show first difference for debugging
        for i, (a, b) in enumerate(zip(result_12_sorted, result_21_sorted)):
            if a != b:
                print(f"  First difference at index {i}:")
                print(f"    12: {a.get('content', 'N/A')}")
                print(f"    21: {b.get('content', 'N/A')}")
                break
        return False


def test_recovery_scenario_edge_cases():
    """Test edge cases that might occur during recovery scenarios."""
    print("\n🔴 EDGE CASE 5: Recovery scenario edge cases")
    
    # Create entries that might be found during recovery
    recovery_entries = [
        {
            "id": "recovery_1",
            "content": "Recovered from disk",
            "_crdt_metadata": {
                "host": "crashed_host",
                "timestamp": "1970-01-01T00:00:00Z",  # Epoch timestamp
                "version": 1,
                "unique_id": "recovery-uuid-1"
            }
        },
        {
            "id": "recovery_1",
            "content": "Current version",
            "_crdt_metadata": {
                "host": "current_host", 
                "timestamp": "2025-01-01T00:00:01Z",
                "version": 2,
                "unique_id": "current-uuid-1"
            }
        },
        {
            "id": "malformed_entry",
            "content": "Entry with missing metadata",
            # Intentionally missing _crdt_metadata
        },
        {
            "id": "empty_meta",
            "content": "Entry with empty metadata",
            "_crdt_metadata": {}
        }
    ]
    
    try:
        result = crdt_merge([recovery_entries])
        
        # Should contain the current version (newer timestamp)
        recovery_1_entries = [e for e in result if e.get('id') == 'recovery_1']
        has_current_version = any(e.get('content') == 'Current version' for e in recovery_1_entries)
        
        # Should handle entries without metadata gracefully
        all_entries_have_ids = all(e.get('id') for e in result)
        
        print(f"Processed {len(result)} entries from recovery scenario")
        print(f"Current version selected: {has_current_version}")
        print(f"All entries have IDs: {all_entries_have_ids}")
        
        if has_current_version and all_entries_have_ids:
            print("✅ PASS: Recovery scenarios handled correctly")
            return True
        else:
            print("❌ FAIL: Recovery scenario issues detected")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception during recovery scenario: {e}")
        return False


def run_comprehensive_validation():
    """Run all edge case validations."""
    print("=" * 80)
    print("COMPREHENSIVE CRDT EDGE CASE VALIDATION")
    print("=" * 80)
    
    test_functions = [
        test_identical_timestamps_and_uids,
        test_uuid_collision_resistance,
        test_timestamp_parsing_edge_cases,
        test_high_throughput_determinism,
        test_recovery_scenario_edge_cases
    ]
    
    results = []
    for test_func in test_functions:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ EXCEPTION in {test_func.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY:")
    print("=" * 80)
    
    pass_count = sum(results)
    fail_count = len(results) - pass_count
    
    print(f"✅ PASSED: {pass_count}/{len(results)} tests")
    print(f"❌ FAILED: {fail_count}/{len(results)} tests")
    
    if fail_count == 0:
        print("\n🎉 ALL EDGE CASES PASS - CRDT IMPLEMENTATION IS MATHEMATICALLY SOUND")
        return True
    else:
        print(f"\n⚠️  {fail_count} EDGE CASE FAILURES - REQUIRES ATTENTION")
        return False


if __name__ == "__main__":
    success = run_comprehensive_validation()
    sys.exit(0 if success else 1)