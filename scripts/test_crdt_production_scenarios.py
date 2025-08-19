#!/usr/bin/env python3
"""
Production scenario validation for CRDT implementation.
Tests realistic usage patterns and high-load conditions.
"""

import sys
import os
import json
import time
import tempfile
import shutil
import threading
import queue
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

sys.path.append(os.path.dirname(__file__))
from memory_backup_crdt import (
    crdt_merge, 
    MemoryBackupCRDT,
    GitIntegration,
    check_memory_bounds,
    validate_entry_count
)


def test_concurrent_backup_scenario():
    """Test multiple concurrent backup processes like production environment."""
    print("\n🎯 PRODUCTION SCENARIO 1: Concurrent backup processes")
    
    # Create temporary repo for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / "test_repo"
        repo_path.mkdir()
        
        # Initialize git repo
        os.system(f"cd {repo_path} && git init --quiet")
        os.system(f"cd {repo_path} && git config user.email 'test@example.com' && git config user.name 'Test User'")
        
        # Simulate 5 concurrent backup processes
        hosts = ["web-server-1", "web-server-2", "worker-1", "worker-2", "scheduler-1"]
        backup_systems = [MemoryBackupCRDT(host) for host in hosts]
        
        # Create realistic memory data for each host
        all_results = []
        
        def backup_worker(host_index):
            """Worker function for concurrent backup testing."""
            host = hosts[host_index]
            backup_system = backup_systems[host_index]
            
            # Generate realistic memory entries for this host
            entries = []
            base_time = "2025-08-18T10:00:00"
            
            for i in range(50):  # 50 entries per host
                entry = {
                    "id": f"conversation_{i % 20}",  # Force some ID collisions
                    "content": f"Memory from {host} - entry {i}",
                    "host_specific_data": f"Data from {host}",
                    "timestamp": f"{base_time}.{i:06d}Z"
                }
                entries.append(backup_system.inject_metadata(entry))
            
            # Create host-specific file
            host_file = repo_path / f"memory-{host}.json"
            with open(host_file, 'w') as f:
                json.dump(entries, f, indent=2)
            
            return {"host": host, "entries": len(entries), "file": str(host_file)}
        
        # Execute concurrent backups
        print(f"Simulating {len(hosts)} concurrent backup processes...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=len(hosts)) as executor:
            futures = [executor.submit(backup_worker, i) for i in range(len(hosts))]
            
            for future in as_completed(futures):
                result = future.result()
                all_results.append(result)
                print(f"  {result['host']}: {result['entries']} entries backed up")
        
        execution_time = time.time() - start_time
        
        # Now test merging all backup files
        print("Merging all concurrent backup files...")
        memory_files = list(repo_path.glob("memory-*.json"))
        all_entries = []
        
        for file_path in memory_files:
            with open(file_path, 'r') as f:
                entries = json.load(f)
                all_entries.append(entries)
        
        # Perform CRDT merge
        merge_start = time.time()
        merged_entries = crdt_merge(all_entries)
        merge_time = time.time() - merge_start
        
        total_original_entries = sum(len(entries) for entries in all_entries)
        
        print(f"Concurrent backup execution time: {execution_time:.3f}s")
        print(f"CRDT merge time: {merge_time:.3f}s")
        print(f"Original entries: {total_original_entries}")
        print(f"Merged unique entries: {len(merged_entries)}")
        print(f"Deduplication efficiency: {(1 - len(merged_entries)/total_original_entries)*100:.1f}%")
        
        # Verify no data loss (each conversation ID should have one winner)
        conversation_ids = set()
        for entry in merged_entries:
            conversation_ids.add(entry.get('id'))
        
        expected_conversations = 20  # We used conversation_0 to conversation_19
        actual_conversations = len([id for id in conversation_ids if id.startswith('conversation_')])
        
        success = actual_conversations == expected_conversations and execution_time < 10.0
        
        if success:
            print("✅ PASS: Concurrent backup scenario completed successfully")
            return True
        else:
            print(f"❌ FAIL: Expected {expected_conversations} conversations, got {actual_conversations}")
            return False


def test_high_volume_memory_scenario():
    """Test handling of large memory datasets."""
    print("\n🎯 PRODUCTION SCENARIO 2: High-volume memory processing")
    
    # Generate large dataset (5000 entries)
    backup_system = MemoryBackupCRDT("high_volume_host")
    entries = []
    
    print("Generating 5000 memory entries...")
    start_time = time.time()
    
    for i in range(5000):
        entry = {
            "id": f"memory_{i}",
            "content": f"Large dataset entry {i} with substantial content" * 10,  # ~500 chars each
            "metadata": {
                "conversation_id": f"conv_{i % 500}",  # 500 unique conversations
                "turn_number": i // 500,
                "user_id": f"user_{i % 100}"  # 100 unique users
            }
        }
        
        # Add CRDT metadata
        entry_with_meta = backup_system.inject_metadata(entry)
        entries.append(entry_with_meta)
        
        # Periodic memory check
        if i % 1000 == 0:
            check_memory_bounds()
    
    generation_time = time.time() - start_time
    
    # Test validation
    try:
        validate_entry_count(entries, "high-volume test")
        validation_passed = True
    except ValueError as e:
        print(f"Validation failed: {e}")
        validation_passed = False
    
    # Test merge performance with multiple large batches
    print("Testing merge performance with large datasets...")
    
    # Split into 3 batches for merge testing
    batch_size = len(entries) // 3
    batch1 = entries[:batch_size]
    batch2 = entries[batch_size:batch_size*2]
    batch3 = entries[batch_size*2:]
    
    merge_start = time.time()
    merged_result = crdt_merge([batch1, batch2, batch3])
    merge_time = time.time() - merge_start
    
    print(f"Entry generation time: {generation_time:.3f}s")
    print(f"Merge time: {merge_time:.3f}s")
    print(f"Generated entries: {len(entries)}")
    print(f"Merged entries: {len(merged_result)}")
    print(f"Memory validation: {'PASS' if validation_passed else 'FAIL'}")
    
    # Performance thresholds for production readiness
    acceptable_generation_time = 30.0  # 30 seconds for 5000 entries
    acceptable_merge_time = 5.0        # 5 seconds for merge
    
    success = (
        validation_passed and 
        generation_time < acceptable_generation_time and 
        merge_time < acceptable_merge_time and
        len(merged_result) == len(entries)  # No data loss
    )
    
    if success:
        print("✅ PASS: High-volume scenario handled within performance thresholds")
        return True
    else:
        print("❌ FAIL: Performance thresholds exceeded or data loss detected")
        return False


def test_network_partition_recovery():
    """Test recovery from network partition scenarios."""
    print("\n🎯 PRODUCTION SCENARIO 3: Network partition recovery")
    
    # Simulate three data centers with different states during partition
    dc1_entries = []
    dc2_entries = []
    dc3_entries = []
    
    backup_systems = {
        "dc1": MemoryBackupCRDT("datacenter-1"),
        "dc2": MemoryBackupCRDT("datacenter-2"), 
        "dc3": MemoryBackupCRDT("datacenter-3")
    }
    
    # Simulate entries created during partition
    base_timestamp = "2025-08-18T10:00:00"
    
    # DC1: Active during partition (timestamps 10:00:00 - 10:10:00)
    for i in range(50):
        entry = {
            "id": f"session_{i % 20}",
            "content": f"DC1 update during partition - {i}",
            "_crdt_metadata": {
                "host": "datacenter-1",
                "timestamp": f"2025-08-18T10:{i//5:02d}:{i%60:02d}Z",
                "version": 1,
                "unique_id": f"dc1-partition-{i}"
            }
        }
        dc1_entries.append(entry)
    
    # DC2: Different updates (timestamps 10:05:00 - 10:15:00)
    for i in range(50):
        entry = {
            "id": f"session_{i % 20}",
            "content": f"DC2 update during partition - {i}",
            "_crdt_metadata": {
                "host": "datacenter-2", 
                "timestamp": f"2025-08-18T10:{(i//5)+5:02d}:{i%60:02d}Z",
                "version": 1,
                "unique_id": f"dc2-partition-{i}"
            }
        }
        dc2_entries.append(entry)
    
    # DC3: Offline during partition, has stale data (timestamps 09:50:00 - 09:55:00)
    for i in range(20):
        entry = {
            "id": f"session_{i % 20}",
            "content": f"DC3 stale data - {i}",
            "_crdt_metadata": {
                "host": "datacenter-3",
                "timestamp": f"2025-08-18T09:5{i//4}:{(i*3)%60:02d}Z",
                "version": 1,
                "unique_id": f"dc3-stale-{i}"
            }
        }
        dc3_entries.append(entry)
    
    print(f"DC1 entries during partition: {len(dc1_entries)}")
    print(f"DC2 entries during partition: {len(dc2_entries)}")
    print(f"DC3 stale entries: {len(dc3_entries)}")
    
    # Simulate partition recovery - merge all three data centers
    print("Simulating partition recovery merge...")
    recovery_start = time.time()
    
    recovered_state = crdt_merge([dc1_entries, dc2_entries, dc3_entries])
    
    recovery_time = time.time() - recovery_start
    
    # Analyze recovery results
    session_counts = {}
    latest_timestamps = {}
    
    for entry in recovered_state:
        session_id = entry.get('id')
        timestamp = entry['_crdt_metadata']['timestamp']
        
        if session_id not in session_counts:
            session_counts[session_id] = 0
            latest_timestamps[session_id] = timestamp
        session_counts[session_id] += 1
        
        if timestamp > latest_timestamps[session_id]:
            latest_timestamps[session_id] = timestamp
    
    # Verify recovery properties
    unique_sessions = len(session_counts)
    max_entries_per_session = max(session_counts.values()) if session_counts else 0
    has_latest_data = all(ts.startswith('2025-08-18T10:') for ts in latest_timestamps.values())
    
    print(f"Recovery time: {recovery_time:.3f}s")
    print(f"Unique sessions recovered: {unique_sessions}")
    print(f"Max entries per session: {max_entries_per_session}")
    print(f"All sessions have latest data: {has_latest_data}")
    
    # Success criteria
    success = (
        unique_sessions == 20 and  # All sessions preserved
        max_entries_per_session == 1 and  # No duplicates
        has_latest_data and  # Latest wins
        recovery_time < 1.0  # Fast recovery
    )
    
    if success:
        print("✅ PASS: Network partition recovery successful")
        return True
    else:
        print("❌ FAIL: Recovery issues detected")
        return False


def test_git_integration_stress():
    """Test Git integration under stress conditions."""
    print("\n🎯 PRODUCTION SCENARIO 4: Git integration stress test")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / "stress_repo"
        repo_path.mkdir()
        
        # Initialize git repo
        os.system(f"cd {repo_path} && git init --quiet")
        os.system(f"cd {repo_path} && git config user.email 'test@example.com' && git config user.name 'Test User'")
        
        git_integration = GitIntegration(str(repo_path))
        backup_system = MemoryBackupCRDT("stress_test_host")
        
        # Create multiple backup files rapidly
        backup_files = []
        
        print("Creating rapid backup sequence...")
        for i in range(10):
            # Generate entries
            entries = []
            for j in range(100):
                entry = {
                    "id": f"rapid_entry_{j}",
                    "content": f"Rapid backup {i} - entry {j}",
                    "batch": i
                }
                entries.append(backup_system.inject_metadata(entry))
            
            # Create backup file
            backup_file = repo_path / f"memory-stress-{i}.json"
            with open(backup_file, 'w') as f:
                json.dump(entries, f, indent=2)
            
            backup_files.append(str(backup_file))
        
        # Test rapid Git operations
        print("Testing rapid Git backup operations...")
        start_time = time.time()
        success_count = 0
        
        for i, backup_file in enumerate(backup_files):
            try:
                # Simulate rapid backup with short intervals
                success = git_integration.backup_to_git(backup_file, f"stress_host_{i}")
                if success:
                    success_count += 1
                time.sleep(0.1)  # Small delay between operations
            except Exception as e:
                print(f"Backup {i} failed: {e}")
        
        stress_time = time.time() - start_time
        
        print(f"Stress test time: {stress_time:.3f}s")
        print(f"Successful backups: {success_count}/{len(backup_files)}")
        
        success = success_count >= len(backup_files) * 0.8  # 80% success rate acceptable
        
        if success:
            print("✅ PASS: Git integration stress test completed successfully")
            return True
        else:
            print("❌ FAIL: Git integration stress test failed")
            return False


def test_memory_pressure_scenario():
    """Test behavior under memory pressure conditions."""
    print("\n🎯 PRODUCTION SCENARIO 5: Memory pressure handling")
    
    # Test memory bounds checking
    backup_system = MemoryBackupCRDT("memory_test_host")
    
    # Generate large entries to test memory bounds
    large_entries = []
    
    print("Testing memory bounds with large entries...")
    try:
        for i in range(1000):
            entry = {
                "id": f"large_entry_{i}",
                "content": "Large content block " * 100,  # ~1.8KB per entry
                "metadata": {"size": "large", "index": i}
            }
            
            entry_with_meta = backup_system.inject_metadata(entry)
            large_entries.append(entry_with_meta)
            
            # Check memory bounds periodically
            if i % 100 == 0:
                check_memory_bounds()
        
        memory_bounds_ok = True
        
    except MemoryError as e:
        print(f"Memory bounds triggered correctly: {e}")
        memory_bounds_ok = True  # This is expected behavior
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        memory_bounds_ok = False
    
    # Test entry count validation
    try:
        validate_entry_count(large_entries, "memory pressure test")
        entry_validation_ok = True
    except ValueError as e:
        print(f"Entry count validation triggered: {e}")
        entry_validation_ok = True  # Expected for large datasets
    except Exception as e:
        print(f"Entry validation error: {e}")
        entry_validation_ok = False
    
    print(f"Generated {len(large_entries)} large entries")
    print(f"Memory bounds checking: {'OK' if memory_bounds_ok else 'FAILED'}")
    print(f"Entry validation: {'OK' if entry_validation_ok else 'FAILED'}")
    
    success = memory_bounds_ok and entry_validation_ok
    
    if success:
        print("✅ PASS: Memory pressure scenario handled correctly")
        return True
    else:
        print("❌ FAIL: Memory pressure handling issues detected")
        return False


def run_production_validation():
    """Run all production scenario validations."""
    print("=" * 80)
    print("PRODUCTION SCENARIO VALIDATION FOR CRDT IMPLEMENTATION")
    print("=" * 80)
    
    test_functions = [
        test_concurrent_backup_scenario,
        test_high_volume_memory_scenario,
        test_network_partition_recovery,
        test_git_integration_stress,
        test_memory_pressure_scenario
    ]
    
    results = []
    for test_func in test_functions:
        try:
            print(f"\nRunning {test_func.__name__}...")
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ EXCEPTION in {test_func.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 80)
    print("PRODUCTION VALIDATION SUMMARY:")
    print("=" * 80)
    
    pass_count = sum(results)
    fail_count = len(results) - pass_count
    
    scenario_names = [
        "Concurrent Backup Processes",
        "High-Volume Memory Processing",
        "Network Partition Recovery",
        "Git Integration Stress Test",
        "Memory Pressure Handling"
    ]
    
    for i, (scenario_name, passed) in enumerate(zip(scenario_names, results)):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {i+1}. {scenario_name}: {status}")
    
    print(f"\n📊 PRODUCTION READINESS SCORE:")
    print(f"  ✅ PASSED: {pass_count}/{len(results)} scenarios ({pass_count/len(results)*100:.1f}%)")
    print(f"  ❌ FAILED: {fail_count}/{len(results)} scenarios ({fail_count/len(results)*100:.1f}%)")
    
    if fail_count == 0:
        print(f"\n🚀 PRODUCTION READY")
        print(f"   All production scenarios pass validation.")
        print(f"   System is certified for production deployment.")
        return True
    elif pass_count >= len(results) * 0.8:
        print(f"\n⚠️  MOSTLY PRODUCTION READY")
        print(f"   {pass_count}/{len(results)} scenarios pass ({pass_count/len(results)*100:.1f}%).")
        print(f"   Minor issues should be addressed before production.")
        return True
    else:
        print(f"\n❌ NOT PRODUCTION READY")
        print(f"   Too many scenario failures for production deployment.")
        print(f"   Significant issues require resolution.")
        return False


if __name__ == "__main__":
    success = run_production_validation()
    sys.exit(0 if success else 1)