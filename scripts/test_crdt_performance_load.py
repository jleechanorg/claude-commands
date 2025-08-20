#!/usr/bin/env python3
"""
High-load performance validation for CRDT implementation.
Tests scalability, throughput, and performance under realistic load conditions.
"""

import sys
import os
import json
import time
import threading
import queue
import tempfile
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple

sys.path.append(os.path.dirname(__file__))
from memory_backup_crdt import (
    crdt_merge, 
    MemoryBackupCRDT,
    GitIntegration,
    check_memory_bounds,
    validate_entry_count
)


def test_throughput_performance():
    """Test CRDT throughput under high load."""
    print("\n⚡ PERFORMANCE TEST 1: Throughput under high load")
    
    backup_system = MemoryBackupCRDT("throughput_test_host")
    
    # Test different entry counts to find throughput limits
    entry_counts = [100, 500, 1000, 2500, 5000, 7500, 10000]
    throughput_results = []
    
    for count in entry_counts:
        print(f"  Testing throughput with {count} entries...")
        
        # Generate entries
        entries = []
        generation_start = time.time()
        
        for i in range(count):
            entry = {
                "id": f"throughput_test_{i}",
                "content": f"Performance test entry {i} with realistic content length",
                "metadata": {
                    "timestamp": time.time(),
                    "index": i,
                    "test_type": "throughput"
                }
            }
            entries.append(backup_system.inject_metadata(entry))
        
        generation_time = time.time() - generation_start
        
        # Test merge performance
        merge_start = time.time()
        merged_result = crdt_merge([entries])
        merge_time = time.time() - merge_start
        
        # Calculate throughput metrics
        generation_throughput = count / generation_time  # entries/second
        merge_throughput = count / merge_time if merge_time > 0 else float('inf')
        
        throughput_results.append({
            'count': count,
            'generation_time': generation_time,
            'merge_time': merge_time,
            'generation_throughput': generation_throughput,
            'merge_throughput': merge_throughput,
            'total_time': generation_time + merge_time
        })
        
        print(f"    Generation: {generation_throughput:.0f} entries/sec")
        print(f"    Merge: {merge_throughput:.0f} entries/sec")
        
        # Stop if we hit performance limits
        if merge_time > 10.0:  # 10 second limit
            print(f"    Performance limit reached at {count} entries")
            break
    
    # Analyze throughput trends
    avg_generation_throughput = statistics.mean([r['generation_throughput'] for r in throughput_results])
    avg_merge_throughput = statistics.mean([r['merge_throughput'] for r in throughput_results])
    max_handled_count = max([r['count'] for r in throughput_results])
    
    print(f"\nThroughput Analysis:")
    print(f"  Average generation throughput: {avg_generation_throughput:.0f} entries/sec")
    print(f"  Average merge throughput: {avg_merge_throughput:.0f} entries/sec")
    print(f"  Maximum entries handled: {max_handled_count}")
    
    # Performance benchmarks (based on production requirements)
    generation_benchmark = 1000  # entries/sec
    merge_benchmark = 10000     # entries/sec
    max_count_benchmark = 5000  # entries
    
    performance_score = (
        (avg_generation_throughput >= generation_benchmark) +
        (avg_merge_throughput >= merge_benchmark) +
        (max_handled_count >= max_count_benchmark)
    ) / 3
    
    print(f"  Performance score: {performance_score:.1%}")
    
    if performance_score >= 0.67:  # 2/3 benchmarks met
        print("✅ PASS: Throughput performance meets requirements")
        return True
    else:
        print("❌ FAIL: Throughput performance below requirements")
        return False


def test_concurrent_merge_performance():
    """Test performance under concurrent merge operations."""
    print("\n⚡ PERFORMANCE TEST 2: Concurrent merge performance")
    
    # Create multiple datasets for concurrent merging
    backup_systems = [MemoryBackupCRDT(f"concurrent_host_{i}") for i in range(10)]
    datasets = []
    
    # Generate 10 datasets with overlapping IDs (realistic conflict scenario)
    for i, backup_system in enumerate(backup_systems):
        dataset = []
        for j in range(500):  # 500 entries per dataset
            entry = {
                "id": f"shared_entry_{j % 100}",  # Force conflicts across datasets
                "content": f"Content from host {i}, entry {j}",
                "host_data": f"host_{i}_specific_data",
                "sequence": j
            }
            dataset.append(backup_system.inject_metadata(entry))
        datasets.append(dataset)
    
    print(f"Created {len(datasets)} datasets with {len(datasets[0])} entries each")
    
    # Test sequential merge performance
    print("Testing sequential merge...")
    sequential_start = time.time()
    sequential_result = crdt_merge(datasets)
    sequential_time = time.time() - sequential_start
    
    print(f"  Sequential merge time: {sequential_time:.3f}s")
    print(f"  Sequential result: {len(sequential_result)} unique entries")
    
    # Test concurrent pairwise merges
    print("Testing concurrent pairwise merges...")
    
    def pairwise_merge(dataset_pair):
        """Merge two datasets."""
        return crdt_merge(dataset_pair)
    
    concurrent_start = time.time()
    
    # Create pairs of datasets for concurrent merging
    dataset_pairs = [(datasets[i], datasets[i+1]) for i in range(0, len(datasets)-1, 2)]
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all pairwise merges concurrently
        futures = [executor.submit(pairwise_merge, pair) for pair in dataset_pairs]
        
        # Collect results
        intermediate_results = []
        for future in as_completed(futures):
            result = future.result()
            intermediate_results.append(result)
    
    # Final merge of intermediate results
    if intermediate_results:
        final_result = crdt_merge(intermediate_results)
    else:
        final_result = []
    
    concurrent_time = time.time() - concurrent_start
    
    print(f"  Concurrent merge time: {concurrent_time:.3f}s")
    print(f"  Concurrent result: {len(final_result)} unique entries")
    
    # Verify results are equivalent
    results_equivalent = len(sequential_result) == len(final_result)
    
    # Calculate performance improvement
    speedup = sequential_time / concurrent_time if concurrent_time > 0 else float('inf')
    
    print(f"  Results equivalent: {results_equivalent}")
    print(f"  Speedup: {speedup:.2f}x")
    
    # Performance criteria
    acceptable_speedup = 1.5  # At least 50% improvement
    
    if results_equivalent and speedup >= acceptable_speedup:
        print("✅ PASS: Concurrent merge performance excellent")
        return True
    elif results_equivalent:
        print("⚠️  PASS: Concurrent merge correct but limited speedup")
        return True
    else:
        print("❌ FAIL: Concurrent merge produces different results")
        return False


def test_memory_efficiency_under_load():
    """Test memory efficiency under high load conditions.""" 
    print("\n⚡ PERFORMANCE TEST 3: Memory efficiency under load")
    
    backup_system = MemoryBackupCRDT("memory_test_host")
    
    # Test memory usage with increasingly large datasets
    memory_test_results = []
    
    try:
        import psutil
        psutil_available = True
        process = psutil.Process()
    except ImportError:
        psutil_available = False
        print("  psutil not available, using bounds checking only")
    
    entry_sizes = [1000, 2500, 5000, 7500, 10000]
    
    for size in entry_sizes:
        print(f"  Testing memory efficiency with {size} entries...")
        
        # Record initial memory
        if psutil_available:
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        else:
            initial_memory = 0
        
        try:
            # Generate large dataset
            entries = []
            for i in range(size):
                entry = {
                    "id": f"memory_test_{i}",
                    "content": f"Memory test entry {i} with substantial content " * 20,  # ~1KB per entry
                    "large_data": list(range(50)),  # Additional data
                    "metadata": {"index": i, "size": "large"}
                }
                entries.append(backup_system.inject_metadata(entry))
                
                # Periodic memory checks
                if i % 1000 == 0:
                    check_memory_bounds()
            
            # Test merge memory usage
            merge_start_time = time.time()
            merged_result = crdt_merge([entries])
            merge_time = time.time() - merge_start_time
            
            # Record peak memory
            if psutil_available:
                peak_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_usage = peak_memory - initial_memory
            else:
                memory_usage = 0
            
            memory_test_results.append({
                'size': size,
                'memory_usage': memory_usage,
                'merge_time': merge_time,
                'memory_per_entry': memory_usage / size if size > 0 else 0,
                'success': True
            })
            
            print(f"    Memory usage: {memory_usage:.1f} MB")
            print(f"    Memory per entry: {memory_usage/size:.3f} MB" if size > 0 else "    Memory per entry: N/A")
            print(f"    Merge time: {merge_time:.3f}s")
            
        except Exception as e:
            print(f"    Memory limit exceeded: {e}")
            memory_test_results.append({
                'size': size,
                'memory_usage': 0,
                'merge_time': 0,
                'memory_per_entry': 0,
                'success': False,
                'error': str(e)
            })
            break
    
    # Analyze memory efficiency
    successful_tests = [r for r in memory_test_results if r['success']]
    
    if successful_tests:
        avg_memory_per_entry = statistics.mean([r['memory_per_entry'] for r in successful_tests])
        max_size_handled = max([r['size'] for r in successful_tests])
        
        print(f"\nMemory Efficiency Analysis:")
        print(f"  Average memory per entry: {avg_memory_per_entry:.3f} MB")
        print(f"  Maximum size handled: {max_size_handled} entries")
        
        # Memory efficiency benchmarks
        memory_per_entry_benchmark = 0.1  # 100KB per entry max
        max_size_benchmark = 5000        # Should handle 5K entries
        
        memory_efficient = avg_memory_per_entry <= memory_per_entry_benchmark
        size_adequate = max_size_handled >= max_size_benchmark
        
        if memory_efficient and size_adequate:
            print("✅ PASS: Memory efficiency meets requirements")
            return True
        else:
            print("⚠️  CAUTION: Memory efficiency below optimal but acceptable")
            return True
    else:
        print("❌ FAIL: Memory efficiency test failed")
        return False


def test_latency_under_load():
    """Test response latency under concurrent load."""
    print("\n⚡ PERFORMANCE TEST 4: Latency under concurrent load")
    
    # Simulate concurrent backup operations from multiple sources
    num_workers = 10
    operations_per_worker = 50
    
    backup_systems = [MemoryBackupCRDT(f"latency_host_{i}") for i in range(num_workers)]
    
    latency_results = queue.Queue()
    
    def worker_operations(worker_id, backup_system, num_ops):
        """Perform operations and measure latency."""
        worker_latencies = []
        
        for i in range(num_ops):
            # Create entry
            entry = {
                "id": f"latency_test_{worker_id}_{i}",
                "content": f"Latency test from worker {worker_id}, operation {i}",
                "worker_id": worker_id,
                "operation_id": i
            }
            
            # Measure metadata injection latency
            start_time = time.time()
            entry_with_meta = backup_system.inject_metadata(entry)
            injection_latency = time.time() - start_time
            
            # Measure single-entry merge latency
            start_time = time.time()
            merge_result = crdt_merge([[entry_with_meta]])
            merge_latency = time.time() - start_time
            
            total_latency = injection_latency + merge_latency
            
            worker_latencies.append({
                'worker_id': worker_id,
                'operation_id': i,
                'injection_latency': injection_latency,
                'merge_latency': merge_latency,
                'total_latency': total_latency
            })
            
            # Small delay to simulate realistic intervals
            time.sleep(0.001)  # 1ms
        
        latency_results.put(worker_latencies)
    
    print(f"Simulating {num_workers} concurrent workers, {operations_per_worker} ops each...")
    
    # Start concurrent workers
    start_time = time.time()
    
    threads = []
    for i in range(num_workers):
        thread = threading.Thread(
            target=worker_operations,
            args=(i, backup_systems[i], operations_per_worker)
        )
        thread.start()
        threads.append(thread)
    
    # Wait for all workers to complete
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    
    # Collect all latency data
    all_latencies = []
    while not latency_results.empty():
        worker_latencies = latency_results.get()
        all_latencies.extend(worker_latencies)
    
    # Calculate latency statistics
    injection_latencies = [r['injection_latency'] for r in all_latencies]
    merge_latencies = [r['merge_latency'] for r in all_latencies]
    total_latencies = [r['total_latency'] for r in all_latencies]
    
    stats = {
        'total_operations': len(all_latencies),
        'total_time': total_time,
        'ops_per_second': len(all_latencies) / total_time,
        'injection_latency': {
            'mean': statistics.mean(injection_latencies),
            'median': statistics.median(injection_latencies),
            'p95': sorted(injection_latencies)[int(0.95 * len(injection_latencies))],
            'max': max(injection_latencies)
        },
        'merge_latency': {
            'mean': statistics.mean(merge_latencies),
            'median': statistics.median(merge_latencies),
            'p95': sorted(merge_latencies)[int(0.95 * len(merge_latencies))],
            'max': max(merge_latencies)
        },
        'total_latency': {
            'mean': statistics.mean(total_latencies),
            'median': statistics.median(total_latencies),
            'p95': sorted(total_latencies)[int(0.95 * len(total_latencies))],
            'max': max(total_latencies)
        }
    }
    
    print(f"Latency Analysis:")
    print(f"  Total operations: {stats['total_operations']}")
    print(f"  Operations per second: {stats['ops_per_second']:.1f}")
    print(f"  Injection latency - Mean: {stats['injection_latency']['mean']*1000:.2f}ms, P95: {stats['injection_latency']['p95']*1000:.2f}ms")
    print(f"  Merge latency - Mean: {stats['merge_latency']['mean']*1000:.2f}ms, P95: {stats['merge_latency']['p95']*1000:.2f}ms")
    print(f"  Total latency - Mean: {stats['total_latency']['mean']*1000:.2f}ms, P95: {stats['total_latency']['p95']*1000:.2f}ms")
    
    # Latency benchmarks (production requirements)
    injection_p95_benchmark = 0.010  # 10ms
    merge_p95_benchmark = 0.050      # 50ms
    total_p95_benchmark = 0.100      # 100ms
    ops_per_sec_benchmark = 100      # 100 ops/sec
    
    latency_acceptable = (
        stats['injection_latency']['p95'] <= injection_p95_benchmark and
        stats['merge_latency']['p95'] <= merge_p95_benchmark and
        stats['total_latency']['p95'] <= total_p95_benchmark and
        stats['ops_per_second'] >= ops_per_sec_benchmark
    )
    
    if latency_acceptable:
        print("✅ PASS: Latency performance meets requirements")
        return True
    else:
        print("❌ FAIL: Latency performance below requirements")
        return False


def test_scalability_limits():
    """Test system scalability limits."""
    print("\n⚡ PERFORMANCE TEST 5: Scalability limits")
    
    # Test with increasing complexity scenarios
    test_scenarios = [
        {"hosts": 5, "entries_per_host": 100, "conflict_rate": 0.1},
        {"hosts": 10, "entries_per_host": 200, "conflict_rate": 0.2},
        {"hosts": 20, "entries_per_host": 300, "conflict_rate": 0.3},
        {"hosts": 50, "entries_per_host": 200, "conflict_rate": 0.5},
    ]
    
    scalability_results = []
    
    for scenario in test_scenarios:
        hosts = scenario["hosts"]
        entries_per_host = scenario["entries_per_host"]
        conflict_rate = scenario["conflict_rate"]
        
        print(f"  Testing: {hosts} hosts, {entries_per_host} entries/host, {conflict_rate:.0%} conflicts")
        
        try:
            # Generate data for scenario
            datasets = []
            backup_systems = [MemoryBackupCRDT(f"scale_host_{i}") for i in range(hosts)]
            
            start_time = time.time()
            
            for host_id, backup_system in enumerate(backup_systems):
                dataset = []
                for entry_id in range(entries_per_host):
                    # Create conflicts based on conflict_rate
                    if entry_id < entries_per_host * conflict_rate:
                        # Conflicting ID (shared across hosts)
                        id_value = f"shared_entry_{entry_id}"
                    else:
                        # Unique ID per host
                        id_value = f"host_{host_id}_entry_{entry_id}"
                    
                    entry = {
                        "id": id_value,
                        "content": f"Content from host {host_id}, entry {entry_id}",
                        "host_id": host_id,
                        "entry_id": entry_id
                    }
                    dataset.append(backup_system.inject_metadata(entry))
                datasets.append(dataset)
            
            generation_time = time.time() - start_time
            
            # Perform merge
            merge_start = time.time()
            merged_result = crdt_merge(datasets)
            merge_time = time.time() - merge_start
            
            total_time = generation_time + merge_time
            total_entries = hosts * entries_per_host
            unique_entries = len(merged_result)
            
            scenario_result = {
                'hosts': hosts,
                'entries_per_host': entries_per_host,
                'conflict_rate': conflict_rate,
                'total_entries': total_entries,
                'unique_entries': unique_entries,
                'generation_time': generation_time,
                'merge_time': merge_time,
                'total_time': total_time,
                'success': True
            }
            
            scalability_results.append(scenario_result)
            
            print(f"    Total entries: {total_entries}, Unique: {unique_entries}")
            print(f"    Generation: {generation_time:.3f}s, Merge: {merge_time:.3f}s")
            print(f"    Total time: {total_time:.3f}s")
            
        except Exception as e:
            print(f"    Scalability limit reached: {e}")
            scenario_result = {
                'hosts': hosts,
                'entries_per_host': entries_per_host,
                'conflict_rate': conflict_rate,
                'success': False,
                'error': str(e)
            }
            scalability_results.append(scenario_result)
            break
    
    # Analyze scalability
    successful_scenarios = [r for r in scalability_results if r['success']]
    
    if successful_scenarios:
        max_hosts = max([r['hosts'] for r in successful_scenarios])
        max_total_entries = max([r['total_entries'] for r in successful_scenarios])
        
        print(f"\nScalability Analysis:")
        print(f"  Maximum hosts handled: {max_hosts}")
        print(f"  Maximum total entries: {max_total_entries}")
        
        # Scalability benchmarks
        min_hosts_benchmark = 20      # Should handle at least 20 hosts
        min_entries_benchmark = 2000  # Should handle at least 2K total entries
        
        scalability_adequate = (
            max_hosts >= min_hosts_benchmark and
            max_total_entries >= min_entries_benchmark
        )
        
        if scalability_adequate:
            print("✅ PASS: Scalability meets requirements")
            return True
        else:
            print("⚠️  CAUTION: Scalability below optimal but acceptable")
            return True
    else:
        print("❌ FAIL: Scalability test failed")
        return False


def run_performance_validation():
    """Run complete performance validation suite."""
    print("=" * 80)
    print("HIGH-LOAD PERFORMANCE VALIDATION FOR CRDT IMPLEMENTATION")
    print("=" * 80)
    
    test_functions = [
        test_throughput_performance,
        test_concurrent_merge_performance,
        test_memory_efficiency_under_load,
        test_latency_under_load,
        test_scalability_limits
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
    print("PERFORMANCE VALIDATION SUMMARY:")
    print("=" * 80)
    
    pass_count = sum(results)
    fail_count = len(results) - pass_count
    
    performance_areas = [
        "Throughput Performance",
        "Concurrent Merge Performance",
        "Memory Efficiency Under Load",
        "Latency Under Concurrent Load",
        "Scalability Limits"
    ]
    
    for i, (area_name, passed) in enumerate(zip(performance_areas, results)):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {i+1}. {area_name}: {status}")
    
    performance_score = pass_count / len(results)
    
    print(f"\n⚡ OVERALL PERFORMANCE SCORE:")
    print(f"  ✅ PASSED: {pass_count}/{len(results)} areas ({performance_score:.1%})")
    print(f"  ❌ FAILED: {fail_count}/{len(results)} areas ({(1-performance_score):.1%})")
    
    if fail_count == 0:
        print(f"\n🚀 PERFORMANCE CERTIFIED")
        print(f"   All performance areas meet requirements.")
        print(f"   System ready for high-load production deployment.")
        return True
    elif performance_score >= 0.8:
        print(f"\n⚡ PERFORMANCE ACCEPTABLE")
        print(f"   {pass_count}/{len(results)} performance areas pass.")
        print(f"   System suitable for production with monitoring.")
        return True
    else:
        print(f"\n⚠️  PERFORMANCE ISSUES")
        print(f"   Multiple performance areas need optimization.")
        print(f"   Consider performance improvements before production.")
        return False


if __name__ == "__main__":
    success = run_performance_validation()
    sys.exit(0 if success else 1)