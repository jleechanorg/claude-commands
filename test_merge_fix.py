#!/usr/bin/env python3
"""
Test for memory backup merge duplication fix
Red-Green TDD: Write failing test first, then fix
"""

import json
import hashlib
from typing import Dict, Any, List

def get_memory_timestamp(memory: Dict[str, Any]) -> str:
    """Extract timestamp from memory entry for CRDT comparison"""
    for field in ['timestamp', 'last_updated', 'created_at', '_crdt_metadata.timestamp']:
        if '.' in field:
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
    return "1970-01-01T00:00:00Z"

def merge_memory_entries_old_buggy(local_memories: List[Dict[str, Any]], remote_memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """OLD BUGGY VERSION - Creates duplicates with fallback counter"""
    merged = {}
    fallback_counter = 0

    # Process local memories first
    for memory in local_memories:
        memory_id = memory.get('id') or memory.get('name')
        if not memory_id:
            memory_id = f"memory_{fallback_counter}"  # ❌ BUG: Different ID each run
            fallback_counter += 1
        merged[memory_id] = memory

    # Merge remote memories using LWW
    for remote_memory in remote_memories:
        memory_id = remote_memory.get('id') or remote_memory.get('name')
        if not memory_id:
            memory_id = f"memory_{fallback_counter}"  # ❌ BUG: Different ID each run
            fallback_counter += 1

        if memory_id in merged:
            local_memory = merged[memory_id]
            local_timestamp = get_memory_timestamp(local_memory)
            remote_timestamp = get_memory_timestamp(remote_memory)

            if remote_timestamp > local_timestamp:
                merged[memory_id] = remote_memory
        else:
            merged[memory_id] = remote_memory

    return list(merged.values())

def merge_memory_entries_fixed(local_memories: List[Dict[str, Any]], remote_memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """FIXED VERSION - Uses content hash for consistent IDs"""
    merged = {}

    # Process local memories first
    for memory in local_memories:
        memory_id = memory.get('id') or memory.get('name')
        if not memory_id:
            # ✅ FIX: Use content hash for consistent ID
            content_hash = hashlib.md5(json.dumps(memory, sort_keys=True).encode()).hexdigest()[:8]
            memory_id = f"hash_{content_hash}"
        merged[memory_id] = memory

    # Merge remote memories using LWW
    for remote_memory in remote_memories:
        memory_id = remote_memory.get('id') or remote_memory.get('name')
        if not memory_id:
            # ✅ FIX: Use content hash for consistent ID
            content_hash = hashlib.md5(json.dumps(remote_memory, sort_keys=True).encode()).hexdigest()[:8]
            memory_id = f"hash_{content_hash}"

        if memory_id in merged:
            local_memory = merged[memory_id]
            local_timestamp = get_memory_timestamp(local_memory)
            remote_timestamp = get_memory_timestamp(remote_memory)

            if remote_timestamp > local_timestamp:
                merged[memory_id] = remote_memory
        else:
            merged[memory_id] = remote_memory

    return list(merged.values())

def test_merge_duplication_bug():
    """RED PHASE: Test that demonstrates the duplication bug"""

    # Create test entries without IDs (triggers fallback logic)
    test_entry = {
        "type": "entity",
        "entityType": "test",
        "observations": ["test data"]
    }

    # Simulate two backup runs with same data
    local_memories = [test_entry.copy()]
    remote_memories = [test_entry.copy()]

    # Test buggy version (should create duplicates)
    result_buggy_run1 = merge_memory_entries_old_buggy(local_memories, remote_memories)
    result_buggy_run2 = merge_memory_entries_old_buggy(result_buggy_run1, remote_memories)

    print(f"🔴 RED PHASE - Buggy version:")
    print(f"  Run 1 result: {len(result_buggy_run1)} entries")
    print(f"  Run 2 result: {len(result_buggy_run2)} entries")
    print(f"  Expected: 1 entry, Got: {len(result_buggy_run2)} entries")

    # This should FAIL (demonstrate the bug)
    assert len(result_buggy_run2) > 1, "❌ BUG: Creates duplicates!"

    # Test fixed version (should NOT create duplicates)
    result_fixed_run1 = merge_memory_entries_fixed(local_memories, remote_memories)
    result_fixed_run2 = merge_memory_entries_fixed(result_fixed_run1, remote_memories)

    print(f"🟢 GREEN PHASE - Fixed version:")
    print(f"  Run 1 result: {len(result_fixed_run1)} entries")
    print(f"  Run 2 result: {len(result_fixed_run2)} entries")
    print(f"  Expected: 1 entry, Got: {len(result_fixed_run2)} entries")

    # This should PASS (no duplicates)
    assert len(result_fixed_run2) == 1, "✅ FIX: No duplicates created!"

    print("🎯 RED-GREEN TDD SUCCESS: Bug identified and fixed!")

if __name__ == "__main__":
    test_merge_duplication_bug()
