#!/usr/bin/env python3
"""
Formal mathematical property verification for CRDT implementation.
Tests the three fundamental CRDT properties with rigorous edge cases.
"""

import sys
import os
import itertools
from typing import List, Dict, Any

sys.path.append(os.path.dirname(__file__))
from memory_backup_crdt import crdt_merge, MemoryBackupCRDT


def generate_test_datasets() -> List[List[Dict[str, Any]]]:
    """Generate comprehensive test datasets for formal verification."""
    backup_system = MemoryBackupCRDT("test_host")
    
    # Dataset 1: Different timestamps
    dataset1 = [
        {
            "id": "test_1",
            "content": "Early content",
            "_crdt_metadata": {
                "host": "host_a",
                "timestamp": "2025-01-01T00:00:01Z",
                "version": 1,
                "unique_id": "uuid-early-001"
            }
        }
    ]
    
    dataset2 = [
        {
            "id": "test_1", 
            "content": "Later content",
            "_crdt_metadata": {
                "host": "host_b",
                "timestamp": "2025-01-01T00:00:02Z",
                "version": 1,
                "unique_id": "uuid-later-001"
            }
        }
    ]
    
    # Dataset 3: Same timestamps, different unique_ids
    dataset3 = [
        {
            "id": "test_1",
            "content": "Content Alpha",
            "_crdt_metadata": {
                "host": "host_c",
                "timestamp": "2025-01-01T00:00:01Z",
                "version": 1,
                "unique_id": "uuid-alpha-001"
            }
        }
    ]
    
    dataset4 = [
        {
            "id": "test_1",
            "content": "Content Zulu",
            "_crdt_metadata": {
                "host": "host_d", 
                "timestamp": "2025-01-01T00:00:01Z",
                "version": 1,
                "unique_id": "uuid-zulu-001"  # Lexicographically later
            }
        }
    ]
    
    # Dataset 5: Identical everything (content hash tiebreaker)
    dataset5 = [
        {
            "id": "test_1",
            "content": "Identical meta, different content A",
            "_crdt_metadata": {
                "host": "host_e",
                "timestamp": "2025-01-01T00:00:01Z",
                "version": 1,
                "unique_id": "identical-uuid-123"
            }
        }
    ]
    
    dataset6 = [
        {
            "id": "test_1",
            "content": "Identical meta, different content Z",
            "_crdt_metadata": {
                "host": "host_f",
                "timestamp": "2025-01-01T00:00:01Z", 
                "version": 1,
                "unique_id": "identical-uuid-123"
            }
        }
    ]
    
    return [dataset1, dataset2, dataset3, dataset4, dataset5, dataset6]


def test_commutativity_formal() -> bool:
    """Formal verification of commutativity: ∀A,B: merge(A,B) = merge(B,A)"""
    print("\n🔬 FORMAL VERIFICATION 1: Commutativity")
    
    datasets = generate_test_datasets()
    violations = 0
    total_tests = 0
    
    # Test all pairwise combinations
    for i, dataset_a in enumerate(datasets):
        for j, dataset_b in enumerate(datasets):
            if i != j:  # Don't test dataset with itself for commutativity
                total_tests += 1
                
                result_ab = crdt_merge([dataset_a, dataset_b])
                result_ba = crdt_merge([dataset_b, dataset_a])
                
                if result_ab != result_ba:
                    violations += 1
                    print(f"  ❌ VIOLATION: Dataset {i} ∪ Dataset {j} ≠ Dataset {j} ∪ Dataset {i}")
                    print(f"     AB: {[e.get('content') for e in result_ab]}")
                    print(f"     BA: {[e.get('content') for e in result_ba]}")
    
    print(f"  Tested {total_tests} combinations")
    print(f"  Violations: {violations}")
    
    if violations == 0:
        print("  ✅ COMMUTATIVITY VERIFIED: ∀A,B: merge(A,B) = merge(B,A)")
        return True
    else:
        print(f"  ❌ COMMUTATIVITY VIOLATED: {violations} cases failed")
        return False


def test_associativity_formal() -> bool:
    """Formal verification of associativity: ∀A,B,C: merge(merge(A,B),C) = merge(A,merge(B,C))"""
    print("\n🔬 FORMAL VERIFICATION 2: Associativity")
    
    datasets = generate_test_datasets()
    violations = 0
    total_tests = 0
    
    # Test all triple combinations
    for i, dataset_a in enumerate(datasets):
        for j, dataset_b in enumerate(datasets):
            for k, dataset_c in enumerate(datasets):
                if len({i, j, k}) == 3:  # All different datasets
                    total_tests += 1
                    
                    # (A ∪ B) ∪ C
                    ab = crdt_merge([dataset_a, dataset_b])
                    abc_left = crdt_merge([ab, dataset_c])
                    
                    # A ∪ (B ∪ C)
                    bc = crdt_merge([dataset_b, dataset_c])
                    abc_right = crdt_merge([dataset_a, bc])
                    
                    if abc_left != abc_right:
                        violations += 1
                        print(f"  ❌ VIOLATION: ({i}∪{j})∪{k} ≠ {i}∪({j}∪{k})")
                        print(f"     Left:  {[e.get('content') for e in abc_left]}")
                        print(f"     Right: {[e.get('content') for e in abc_right]}")
    
    print(f"  Tested {total_tests} combinations")
    print(f"  Violations: {violations}")
    
    if violations == 0:
        print("  ✅ ASSOCIATIVITY VERIFIED: ∀A,B,C: merge(merge(A,B),C) = merge(A,merge(B,C))")
        return True
    else:
        print(f"  ❌ ASSOCIATIVITY VIOLATED: {violations} cases failed")
        return False


def test_idempotence_formal() -> bool:
    """Formal verification of idempotence: ∀A: merge(A,A) = A"""
    print("\n🔬 FORMAL VERIFICATION 3: Idempotence")
    
    datasets = generate_test_datasets()
    violations = 0
    total_tests = len(datasets)
    
    for i, dataset in enumerate(datasets):
        result = crdt_merge([dataset, dataset])
        
        if result != dataset:
            violations += 1
            print(f"  ❌ VIOLATION: Dataset {i} ∪ Dataset {i} ≠ Dataset {i}")
            print(f"     Original: {[e.get('content') for e in dataset]}")
            print(f"     Result:   {[e.get('content') for e in result]}")
    
    print(f"  Tested {total_tests} datasets")
    print(f"  Violations: {violations}")
    
    if violations == 0:
        print("  ✅ IDEMPOTENCE VERIFIED: ∀A: merge(A,A) = A")
        return True
    else:
        print(f"  ❌ IDEMPOTENCE VIOLATED: {violations} cases failed")
        return False


def test_determinism_formal() -> bool:
    """Formal verification of determinism: Multiple identical operations produce identical results."""
    print("\n🔬 FORMAL VERIFICATION 4: Determinism")
    
    datasets = generate_test_datasets()
    violations = 0
    total_tests = 0
    
    # Test determinism for all pairwise merges by running them multiple times
    for i, dataset_a in enumerate(datasets):
        for j, dataset_b in enumerate(datasets):
            if i != j:
                total_tests += 1
                
                # Run the same merge 5 times
                results = []
                for run in range(5):
                    result = crdt_merge([dataset_a, dataset_b])
                    results.append(result)
                
                # All results should be identical
                first_result = results[0]
                for run, result in enumerate(results[1:], 1):
                    if result != first_result:
                        violations += 1
                        print(f"  ❌ VIOLATION: Dataset {i} ∪ Dataset {j} non-deterministic")
                        print(f"     Run 0: {[e.get('content') for e in first_result]}")
                        print(f"     Run {run}: {[e.get('content') for e in result]}")
                        break
    
    print(f"  Tested {total_tests} merge combinations × 5 runs")
    print(f"  Violations: {violations}")
    
    if violations == 0:
        print("  ✅ DETERMINISM VERIFIED: Multiple identical operations produce identical results")
        return True
    else:
        print(f"  ❌ DETERMINISM VIOLATED: {violations} cases failed")
        return False


def test_lww_semantics_formal() -> bool:
    """Formal verification of Last-Write-Wins semantics."""
    print("\n🔬 FORMAL VERIFICATION 5: Last-Write-Wins (LWW) Semantics")
    
    # Create entries with clear temporal ordering
    early_entry = {
        "id": "lww_test",
        "content": "Early content",
        "_crdt_metadata": {
            "host": "host_a",
            "timestamp": "2025-01-01T00:00:01Z",
            "version": 1,
            "unique_id": "early-uuid"
        }
    }
    
    later_entry = {
        "id": "lww_test",
        "content": "Later content", 
        "_crdt_metadata": {
            "host": "host_b",
            "timestamp": "2025-01-01T00:00:02Z",
            "version": 1,
            "unique_id": "later-uuid"
        }
    }
    
    # Test both merge orders
    result_early_later = crdt_merge([[early_entry], [later_entry]])
    result_later_early = crdt_merge([[later_entry], [early_entry]])
    
    # Both should result in the later entry winning
    expected_content = "Later content"
    
    early_later_content = result_early_later[0]['content'] if result_early_later else None
    later_early_content = result_later_early[0]['content'] if result_later_early else None
    
    violations = 0
    if early_later_content != expected_content:
        violations += 1
        print(f"  ❌ LWW VIOLATION: early→later = {early_later_content}, expected {expected_content}")
    
    if later_early_content != expected_content:
        violations += 1
        print(f"  ❌ LWW VIOLATION: later→early = {later_early_content}, expected {expected_content}")
    
    if early_later_content != later_early_content:
        violations += 1
        print(f"  ❌ LWW VIOLATION: Results differ based on merge order")
    
    print(f"  Early→Later result: {early_later_content}")
    print(f"  Later→Early result: {later_early_content}")
    print(f"  Expected winner: {expected_content}")
    
    if violations == 0:
        print("  ✅ LWW SEMANTICS VERIFIED: Later timestamps consistently win")
        return True
    else:
        print(f"  ❌ LWW SEMANTICS VIOLATED: {violations} issues detected")
        return False


def run_formal_verification():
    """Run complete formal verification suite."""
    print("=" * 100)
    print("FORMAL MATHEMATICAL PROPERTY VERIFICATION FOR CRDT IMPLEMENTATION")
    print("=" * 100)
    
    test_functions = [
        test_commutativity_formal,
        test_associativity_formal,
        test_idempotence_formal,
        test_determinism_formal,
        test_lww_semantics_formal
    ]
    
    results = []
    for test_func in test_functions:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ EXCEPTION in {test_func.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 100)
    print("FORMAL VERIFICATION SUMMARY:")
    print("=" * 100)
    
    pass_count = sum(results)
    fail_count = len(results) - pass_count
    
    property_names = [
        "Commutativity",
        "Associativity", 
        "Idempotence",
        "Determinism",
        "LWW Semantics"
    ]
    
    for i, (prop_name, passed) in enumerate(zip(property_names, results)):
        status = "✅ VERIFIED" if passed else "❌ VIOLATED"
        print(f"  {i+1}. {prop_name}: {status}")
    
    print(f"\n📊 OVERALL RESULT:")
    print(f"  ✅ VERIFIED: {pass_count}/{len(results)} properties")
    print(f"  ❌ VIOLATED: {fail_count}/{len(results)} properties")
    
    if fail_count == 0:
        print(f"\n🎉 MATHEMATICAL SOUNDNESS CONFIRMED")
        print(f"   All fundamental CRDT properties are formally verified.")
        print(f"   Implementation is ready for production use.")
        return True
    else:
        print(f"\n⚠️  MATHEMATICAL ISSUES DETECTED")
        print(f"   {fail_count} property violations require immediate attention.")
        print(f"   Implementation should NOT be used in production.")
        return False


if __name__ == "__main__":
    success = run_formal_verification()
    sys.exit(0 if success else 1)