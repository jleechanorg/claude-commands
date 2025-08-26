import pytest
import json
import hashlib
import os
import time
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import threading


class TestCache:
    def __init__(self, cache_dir=".pytest_cache_optimizer"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "test_results.json"
        self.lock = threading.Lock()
        self.load_cache()

    def load_cache(self):
        if self.cache_file.exists():
            with open(self.cache_file, "r") as f:
                self.cache = json.load(f)
        else:
            self.cache = {}

    def save_cache(self):
        with self.lock:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)

    def get_test_hash(self, nodeid, file_path):
        """Generate a hash based on test nodeid and file content"""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            hash_content = f"{nodeid}{content}".encode()
            return hashlib.md5(hash_content).hexdigest()
        except FileNotFoundError:
            return hashlib.md5(nodeid.encode()).hexdigest()

    def is_cached(self, nodeid, file_path):
        test_hash = self.get_test_hash(nodeid, file_path)
        return test_hash in self.cache and self.cache[test_hash]["result"] == "passed"

    def cache_result(self, nodeid, file_path, result, duration):
        test_hash = self.get_test_hash(nodeid, file_path)
        self.cache[test_hash] = {
            "nodeid": nodeid,
            "file_path": str(file_path),
            "result": result,
            "duration": duration,
            "timestamp": time.time()
        }
        self.save_cache()

    def invalidate_cache(self, file_path):
        """Invalidate cache entries for a modified file"""
        if not self.cache_file.exists():
            return
            
        keys_to_remove = []
        for key, value in self.cache.items():
            if value["file_path"] == str(file_path):
                keys_to_remove.append(key)
                
        for key in keys_to_remove:
            del self.cache[key]
            
        self.save_cache()


class TestGroupOptimizer:
    def __init__(self, num_workers=4):
        self.num_workers = num_workers
        self.test_cache = TestCache()
        self.test_groups = defaultdict(list)
        self.test_durations = {}

    def group_tests_by_file(self, items):
        """Group tests by their source file for better parallelization"""
        file_groups = defaultdict(list)
        for item in items:
            file_path = item.location[0]
            file_groups[file_path].append(item)
            
        # Sort groups by total estimated duration (longest first)
        sorted_groups = sorted(
            file_groups.items(), 
            key=lambda x: sum(self.test_durations.get(item.nodeid, 1) for item in x[1]),
            reverse=True
        )
        
        # Distribute tests among workers
        for i, (file_path, tests) in enumerate(sorted_groups):
            worker_id = i % self.num_workers
            self.test_groups[worker_id].extend(tests)
            
        return list(self.test_groups.values())

    def get_cached_tests(self, items):
        cached_tests = []
        uncached_tests = []
        
        for item in items:
            file_path = Path(item.location[0])
            if self.test_cache.is_cached(item.nodeid, file_path):
                cached_tests.append(item)
            else:
                uncached_tests.append(item)
                
        return cached_tests, uncached_tests


def pytest_configure(config):
    config.option.num_workers = getattr(config.option, 'num_workers', 4)
    config.option.cache_optimizer = True


def pytest_collection_modifyitems(config, items):
    if not config.option.cache_optimizer:
        return
        
    optimizer = TestGroupOptimizer(config.option.num_workers)
    
    # Load test duration history if available
    duration_file = Path(".pytest_cache_optimizer/durations.json")
    if duration_file.exists():
        with open(duration_file, "r") as f:
            optimizer.test_durations = json.load(f)
    
    # Separate cached and uncached tests
    cached_tests, uncached_tests = optimizer.get_cached_tests(items)
    
    # Group uncached tests for parallel execution
    test_groups = optimizer.group_tests_by_file(uncached_tests)
    
    # Reorder items: run cached tests first, then grouped uncached tests
    reordered_items = cached_tests.copy()
    for group in test_groups:
        reordered_items.extend(group)
        
    items[:] = reordered_items


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    if call.when == "call":
        # Cache the test result after execution
        optimizer = TestGroupOptimizer()
        file_path = Path(item.location[0])
        result = "passed" if call.excinfo is None else "failed"
        duration = call.duration
        optimizer.test_cache.cache_result(item.nodeid, file_path, result, duration)
        
        # Save duration for future grouping optimization
        duration_file = Path(".pytest_cache_optimizer/durations.json")
        durations = {}
        if duration_file.exists():
            with open(duration_file, "r") as f:
                durations = json.load(f)
        durations[item.nodeid] = duration
        with open(duration_file, "w") as f:
            json.dump(durations, f, indent=2)


def pytest_sessionstart(session):
    # Check for file modifications and invalidate cache
    cache_dir = Path(".pytest_cache_optimizer")
    if not cache_dir.exists():
        return
        
    timestamp_file = cache_dir / "timestamps.json"
    timestamps = {}
    if timestamp_file.exists():
        with open(timestamp_file, "r") as f:
            timestamps = json.load(f)
    
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                mtime = file_path.stat().st_mtime
                if str(file_path) in timestamps and mtime > timestamps[str(file_path)]:
                    # File has been modified, invalidate its cache
                    test_cache = TestCache()
                    test_cache.invalidate_cache(file_path)
                timestamps[str(file_path)] = mtime
    
    with open(timestamp_file, "w") as f:
        json.dump(timestamps, f, indent=2)


def pytest_addoption(parser):
    parser.addoption(
        "--num-workers",
        action="store",
        default=4,
        type=int,
        help="Number of parallel workers for test execution"
    )
    parser.addoption(
        "--cache-optimizer",
        action="store_true",
        default=False,
        help="Enable test result caching and parallel execution optimizer"
    )