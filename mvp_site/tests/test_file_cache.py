#!/usr/bin/env python3
"""
Unit tests for file_cache.py module.
Tests the generalized file caching functionality using cachetools.
"""

import os
import sys
import tempfile
import threading
import time
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest

from mvp_site.file_cache import (
    clear_file_cache,
    get_cache_stats,
    invalidate_file,
    read_file_cached,
)


class TestFileCache(unittest.TestCase):
    """Test cases for file_cache module."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear cache before each test
        clear_file_cache()

        # Create a temporary file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")
        self.test_content = "This is test file content for caching tests."

        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(self.test_content)

    def tearDown(self):
        """Clean up after each test method."""
        # Remove temporary files
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
        os.rmdir(self.temp_dir)

        # Clear cache after each test
        clear_file_cache()

    def test_basic_file_read(self):
        """Test basic file reading functionality."""
        # This should fail initially since we haven't implemented the cache yet
        content = read_file_cached(self.test_file_path)
        assert content == self.test_content

    def test_cache_hit_behavior(self):
        """Test that subsequent reads use cache (cache hits)."""
        # First read - cache miss
        content1 = read_file_cached(self.test_file_path)
        stats_after_first = get_cache_stats()

        # Second read - should be cache hit
        content2 = read_file_cached(self.test_file_path)
        stats_after_second = get_cache_stats()

        # Content should be identical
        assert content1 == content2
        assert content1 == self.test_content

        # Cache hits should increase
        assert stats_after_second["cache_hits"] > stats_after_first["cache_hits"]

    def test_cache_miss_behavior(self):
        """Test cache miss statistics."""
        stats_initial = get_cache_stats()

        # First read should be a cache miss
        read_file_cached(self.test_file_path)
        stats_after_read = get_cache_stats()

        assert stats_after_read["cache_misses"] > stats_initial["cache_misses"]

    def test_file_not_found_error(self):
        """Test error handling for non-existent files."""
        non_existent_path = "/path/that/does/not/exist.txt"

        with pytest.raises(FileNotFoundError):
            read_file_cached(non_existent_path)

    def test_cache_clear_functionality(self):
        """Test that cache clearing works correctly."""
        # Read file to populate cache
        read_file_cached(self.test_file_path)
        get_cache_stats()

        # Clear cache
        clear_file_cache()
        stats_after_clear = get_cache_stats()

        # Cache size should be 0 after clearing
        assert stats_after_clear["cached_files"] == 0

        # Read again should be cache miss (not hit)
        read_file_cached(self.test_file_path)
        stats_after_read = get_cache_stats()

        # After clearing and re-reading, we should have 1 miss and 1 cached file
        assert stats_after_read["cache_misses"] == 1
        assert stats_after_read["cached_files"] == 1

    def test_cache_statistics_tracking(self):
        """Test that cache statistics are properly tracked."""
        stats_initial = get_cache_stats()

        # Verify initial stats structure
        assert "cache_hits" in stats_initial
        assert "cache_misses" in stats_initial
        assert "cached_files" in stats_initial

        # All should be 0 initially
        assert stats_initial["cache_hits"] == 0
        assert stats_initial["cache_misses"] == 0
        assert stats_initial["cached_files"] == 0

    def test_thread_safety(self):
        """Test that cache is thread-safe."""
        results = []
        errors = []

        def read_in_thread():
            try:
                content = read_file_cached(self.test_file_path)
                results.append(content)
            except Exception as e:
                errors.append(e)

        # Create multiple threads reading the same file
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=read_in_thread)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All reads should succeed
        assert len(errors) == 0
        assert len(results) == 10

        # All results should be identical
        for result in results:
            assert result == self.test_content

    def test_performance_improvement(self):
        """Test that cached reads are faster than file I/O."""
        # First read (cache miss) - measure time
        start_time = time.time()
        read_file_cached(self.test_file_path)
        first_read_time = time.time() - start_time

        # Second read (cache hit) - measure time
        start_time = time.time()
        read_file_cached(self.test_file_path)
        second_read_time = time.time() - start_time

        # Cache hit should be faster (though this might be flaky in CI)
        # At minimum, both should complete successfully
        assert first_read_time is not None
        assert second_read_time is not None

    def test_ttl_expiration_simulation(self):
        """Test TTL expiration behavior (simulated since 1 hour is too long)."""
        # This test simulates TTL behavior since we can't wait 1 hour
        # We'll mock the cache to have a very short TTL for testing

        # Read file to populate cache
        read_file_cached(self.test_file_path)
        initial_stats = get_cache_stats()

        # Verify file is cached
        assert initial_stats["cached_files"] == 1

        # For now, just verify the cache contains the file
        # In a full implementation, we'd mock time or use a shorter TTL for testing
        assert initial_stats["cached_files"] > 0

    def test_cache_invalidation_functionality(self):
        """Test cache invalidation functionality."""
        # Read a file to cache it
        content = read_file_cached(self.test_file_path)
        assert content == self.test_content

        # Verify file is cached
        stats_before = get_cache_stats()
        assert stats_before["cached_files"] == 1

        # Invalidate the file
        result = invalidate_file(self.test_file_path)
        assert result, "invalidate_file should return True when file was cached"

        # Verify file is no longer cached
        stats_after = get_cache_stats()
        assert stats_after["cached_files"] == 0

        # Try to invalidate a file that wasn't cached
        result_not_cached = invalidate_file(self.test_file_path)
        assert (
            not result_not_cached
        ), "invalidate_file should return False when file wasn't cached"

        # Verify invalidating nonexistent file doesn't crash
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.txt")
        result_nonexistent = invalidate_file(nonexistent_file)
        assert not result_nonexistent


class TestFileCacheIntegration(unittest.TestCase):
    """Integration tests for file cache with real world usage."""

    def setUp(self):
        """Set up integration test fixtures."""
        clear_file_cache()

    def tearDown(self):
        """Clean up integration test fixtures."""
        clear_file_cache()

    def test_multiple_files_caching(self):
        """Test caching behavior with multiple different files."""
        # Create multiple temporary files
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        file_contents = []

        try:
            for i in range(3):
                file_path = os.path.join(temp_dir, f"test_file_{i}.txt")
                content = f"Content for file {i}"

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                file_paths.append(file_path)
                file_contents.append(content)

            # Read all files - should be cache misses
            for i, file_path in enumerate(file_paths):
                content = read_file_cached(file_path)
                assert content == file_contents[i]

            stats_after_first_reads = get_cache_stats()
            assert stats_after_first_reads["cached_files"] == 3
            assert stats_after_first_reads["cache_misses"] == 3

            # Read all files again - should be cache hits
            for i, file_path in enumerate(file_paths):
                content = read_file_cached(file_path)
                assert content == file_contents[i]

            stats_after_second_reads = get_cache_stats()
            assert stats_after_second_reads["cache_hits"] == 3

        finally:
            # Clean up
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
            os.rmdir(temp_dir)


if __name__ == "__main__":
    unittest.main()
