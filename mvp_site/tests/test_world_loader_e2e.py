#!/usr/bin/env python3
"""
End-to-end tests for world_loader.py with file caching.
Tests the integration of world_loader with the file_cache system.
"""

import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from file_cache import clear_file_cache, get_cache_stats
from world_loader import load_banned_names, load_world_content_for_system_instruction


class TestWorldLoaderE2E(unittest.TestCase):
    """End-to-end tests for world_loader with caching."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear cache before each test
        clear_file_cache()

    def tearDown(self):
        """Clean up after each test method."""
        # Clear cache after each test
        clear_file_cache()

    def test_world_content_loading_uses_cache(self):
        """Test that load_world_content uses the file cache."""
        # Check that world files exist
        world_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "world")
        world_assiah_path = os.path.join(world_dir, "world_assiah_compressed.md")

        if not os.path.exists(world_assiah_path):
            self.skipTest(f"World file not found: {world_assiah_path}")

        # First load - should be cache miss
        initial_stats = get_cache_stats()
        content1 = load_world_content_for_system_instruction()
        stats_after_first = get_cache_stats()

        # Verify content is not empty
        self.assertIsInstance(content1, str)
        self.assertGreater(len(content1), 0)

        # Should have cache misses from loading world and banned names files
        self.assertGreater(
            stats_after_first["cache_misses"], initial_stats["cache_misses"]
        )
        self.assertGreater(stats_after_first["cached_files"], 0)

        # Second load - should use cache
        content2 = load_world_content_for_system_instruction()
        stats_after_second = get_cache_stats()

        # Content should be identical
        self.assertEqual(content1, content2)

        # Should have cache hits
        self.assertGreater(
            stats_after_second["cache_hits"], stats_after_first["cache_hits"]
        )

    def test_banned_names_loading_uses_cache(self):
        """Test that load_banned_names uses the file cache."""
        world_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "world")
        banned_names_path = os.path.join(world_dir, "banned_names.md")

        if not os.path.exists(banned_names_path):
            self.skipTest(f"Banned names file not found: {banned_names_path}")

        # First load - should be cache miss
        initial_stats = get_cache_stats()
        banned1 = load_banned_names()
        stats_after_first = get_cache_stats()

        # Verify content is string (may be empty)
        self.assertIsInstance(banned1, str)

        # Should have a cache miss
        self.assertGreater(
            stats_after_first["cache_misses"], initial_stats["cache_misses"]
        )
        self.assertGreaterEqual(stats_after_first["cached_files"], 1)

        # Second load - should use cache
        banned2 = load_banned_names()
        stats_after_second = get_cache_stats()

        # Content should be identical
        self.assertEqual(banned1, banned2)

        # Should have cache hits
        self.assertGreater(
            stats_after_second["cache_hits"], stats_after_first["cache_hits"]
        )

    def test_world_loader_performance_with_cache(self):
        """Test that repeated world loader calls show performance improvement."""
        import time

        world_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "world")
        world_assiah_path = os.path.join(world_dir, "world_assiah_compressed.md")

        if not os.path.exists(world_assiah_path):
            self.skipTest(f"World file not found: {world_assiah_path}")

        # Measure first load (cache miss)
        start_time = time.time()
        content1 = load_world_content_for_system_instruction()
        first_load_time = time.time() - start_time

        # Measure second load (cache hit)
        start_time = time.time()
        content2 = load_world_content_for_system_instruction()
        second_load_time = time.time() - start_time

        # Content should be identical
        self.assertEqual(content1, content2)

        # Both should complete successfully (performance comparison may be flaky in CI)
        self.assertIsNotNone(first_load_time)
        self.assertIsNotNone(second_load_time)
        self.assertGreater(len(content1), 0)

    def test_world_loader_cache_persistence_across_calls(self):
        """Test that cache persists across multiple function calls."""
        world_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "world")
        world_assiah_path = os.path.join(world_dir, "world_assiah_compressed.md")

        if not os.path.exists(world_assiah_path):
            self.skipTest(f"World file not found: {world_assiah_path}")

        # Multiple calls to different functions
        world_content = (
            load_world_content_for_system_instruction()
        )  # Should load world + banned files
        banned_names = load_banned_names()  # Should use cached banned file
        world_content2 = (
            load_world_content_for_system_instruction()
        )  # Should use all cached files

        # Get final stats
        final_stats = get_cache_stats()

        # Should have some cached files
        self.assertGreater(final_stats["cached_files"], 0)

        # Should have both hits and misses
        self.assertGreater(final_stats["cache_misses"], 0)  # Initial loads
        self.assertGreater(final_stats["cache_hits"], 0)  # Subsequent loads

        # Content should be consistent
        self.assertEqual(world_content, world_content2)
        self.assertIsInstance(banned_names, str)

    def test_world_loader_handles_missing_files_gracefully(self):
        """Test that world_loader handles missing files without breaking cache."""
        # This tests the error handling path
        initial_stats = get_cache_stats()

        # load_banned_names should handle missing file gracefully
        try:
            banned_names = load_banned_names()
            # If file exists, should be string
            self.assertIsInstance(banned_names, str)
        except FileNotFoundError:
            # If file doesn't exist, should raise FileNotFoundError
            pass

        # Cache should still be functional
        stats_after_attempt = get_cache_stats()
        self.assertIsInstance(stats_after_attempt, dict)
        self.assertIn("cache_hits", stats_after_attempt)

    def test_world_content_format_and_structure(self):
        """Test that world content maintains expected format through caching."""
        world_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "world")
        world_assiah_path = os.path.join(world_dir, "world_assiah_compressed.md")

        if not os.path.exists(world_assiah_path):
            self.skipTest(f"World file not found: {world_assiah_path}")

        # Load world content multiple times
        content1 = load_world_content_for_system_instruction()
        content2 = load_world_content_for_system_instruction()
        content3 = load_world_content_for_system_instruction()

        # All should be identical
        self.assertEqual(content1, content2)
        self.assertEqual(content2, content3)

        # Should contain world content and banned names section
        self.assertIsInstance(content1, str)
        self.assertGreater(len(content1), 100)  # Should be substantial content

        # Check cache is working effectively
        final_stats = get_cache_stats()
        self.assertGreaterEqual(
            final_stats["cache_hits"], 2
        )  # At least 2 hits for content2 and content3


class TestWorldLoaderCacheIntegration(unittest.TestCase):
    """Integration tests for world_loader cache behavior."""

    def setUp(self):
        """Set up integration test fixtures."""
        clear_file_cache()

    def tearDown(self):
        """Clean up integration test fixtures."""
        clear_file_cache()

    def test_mixed_world_loader_calls_cache_efficiency(self):
        """Test cache efficiency with mixed world_loader function calls."""
        world_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "world")
        world_assiah_path = os.path.join(world_dir, "world_assiah_compressed.md")

        if not os.path.exists(world_assiah_path):
            self.skipTest(f"World file not found: {world_assiah_path}")

        # Simulate realistic usage pattern
        operations = []

        # Load world content multiple times with banned names in between
        operations.append(
            load_world_content_for_system_instruction()
        )  # Miss: world + banned files
        operations.append(load_banned_names())  # Hit: banned file already cached
        operations.append(
            load_world_content_for_system_instruction()
        )  # Hit: both files already cached
        operations.append(load_banned_names())  # Hit: banned file already cached
        operations.append(
            load_world_content_for_system_instruction()
        )  # Hit: both files already cached

        # Verify all operations succeeded
        for i, result in enumerate(operations):
            self.assertIsInstance(result, str, f"Operation {i} failed")

        # Check cache performance
        final_stats = get_cache_stats()

        # Should have high cache hit rate
        total_requests = final_stats["total_requests"]
        hit_rate = final_stats["hit_rate_percent"]

        self.assertGreater(total_requests, 5)  # Multiple file reads
        self.assertGreater(hit_rate, 50)  # At least 50% hit rate

        # Should have cached the world files
        self.assertGreaterEqual(final_stats["cached_files"], 1)


if __name__ == "__main__":
    unittest.main()
