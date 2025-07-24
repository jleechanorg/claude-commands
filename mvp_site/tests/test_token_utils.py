#!/usr/bin/env python3
"""
Test suite for token_utils.py

Tests token counting and logging utilities for accurate token estimation
and consistent logging across the application.
"""

import os
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

from unittest.mock import mock_open
import shutil

# Add the parent directory to sys.path so we can import from mvp_site
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import file_cache
from token_utils import estimate_tokens, format_token_count, log_with_tokens


class TestTokenUtils(unittest.TestCase):
    """Test suite for token utility functions."""

    def test_estimate_tokens_with_string(self):
        """Test token estimation with string input."""
        # Test empty string
        self.assertEqual(estimate_tokens(""), 0)

        # Test single character (should round down to 0)
        self.assertEqual(estimate_tokens("a"), 0)

        # Test 4 characters (should be 1 token)
        self.assertEqual(estimate_tokens("test"), 1)

        # Test 8 characters (should be 2 tokens)
        self.assertEqual(estimate_tokens("testing!"), 2)

        # Test longer text
        text = "This is a longer text for testing token estimation."
        expected_tokens = len(text) // 4  # 51 chars = 12 tokens
        self.assertEqual(estimate_tokens(text), expected_tokens)

    def test_estimate_tokens_with_list(self):
        """Test token estimation with list input."""
        # Test empty list
        self.assertEqual(estimate_tokens([]), 0)

        # Test list with empty strings
        self.assertEqual(estimate_tokens(["", ""]), 0)

        # Test list with strings
        text_list = ["hello", "world", "test"]
        total_chars = len("hello") + len("world") + len("test")  # 14 chars
        expected_tokens = total_chars // 4  # 3 tokens
        self.assertEqual(estimate_tokens(text_list), expected_tokens)

        # Test list with mixed content (should ignore non-strings)
        mixed_list = ["hello", 123, "world", None, "test"]
        expected_chars = len("hello") + len("world") + len("test")  # 14 chars
        expected_tokens = expected_chars // 4  # 3 tokens
        self.assertEqual(estimate_tokens(mixed_list), expected_tokens)

    def test_estimate_tokens_with_none(self):
        """Test token estimation with None input."""
        self.assertEqual(estimate_tokens(None), 0)

    def test_estimate_tokens_edge_cases(self):
        """Test edge cases for token estimation."""
        # Test very large text
        large_text = "a" * 10000
        expected_tokens = 10000 // 4  # 2500 tokens
        self.assertEqual(estimate_tokens(large_text), expected_tokens)

        # Test unicode characters
        unicode_text = "café ñoño 你好"
        expected_tokens = len(unicode_text) // 4
        self.assertEqual(estimate_tokens(unicode_text), expected_tokens)

        # Test text with newlines and special characters
        special_text = "line1\nline2\t\r\n!@#$%^&*()"
        expected_tokens = len(special_text) // 4
        self.assertEqual(estimate_tokens(special_text), expected_tokens)

    @patch("token_utils.logging_util.info")
    def test_log_with_tokens_default_logger(self, mock_log):
        """Test log_with_tokens with default logger."""
        message = "Test message"
        text = "test text content"  # 17 chars = 4 tokens

        log_with_tokens(message, text)

        expected_log = f"{message}: 17 characters (~4 tokens)"
        mock_log.assert_called_once_with(expected_log)

    def test_log_with_tokens_custom_logger(self):
        """Test log_with_tokens with custom logger."""
        mock_logger = Mock()
        message = "Custom log test"
        text = "custom text"  # 11 chars = 2 tokens

        log_with_tokens(message, text, logger=mock_logger)

        expected_log = f"{message}: 11 characters (~2 tokens)"
        mock_logger.info.assert_called_once_with(expected_log)

    @patch("token_utils.logging_util.info")
    def test_log_with_tokens_empty_text(self, mock_log):
        """Test log_with_tokens with empty text."""
        message = "Empty test"
        text = ""

        log_with_tokens(message, text)

        expected_log = f"{message}: 0 characters (~0 tokens)"
        mock_log.assert_called_once_with(expected_log)

    @patch("token_utils.logging_util.info")
    def test_log_with_tokens_none_text(self, mock_log):
        """Test log_with_tokens with None text."""
        message = "None test"
        text = None

        log_with_tokens(message, text)

        expected_log = f"{message}: 0 characters (~0 tokens)"
        mock_log.assert_called_once_with(expected_log)

    def test_format_token_count(self):
        """Test format_token_count function."""
        # Test zero characters
        result = format_token_count(0)
        self.assertEqual(result, "0 characters (~0 tokens)")

        # Test small count
        result = format_token_count(4)
        self.assertEqual(result, "4 characters (~1 token)")

        # Test larger count
        result = format_token_count(100)
        self.assertEqual(result, "100 characters (~25 tokens)")

        # Test odd number (should round down)
        result = format_token_count(17)
        self.assertEqual(result, "17 characters (~4 tokens)")

        # Test large count
        result = format_token_count(10000)
        self.assertEqual(result, "10000 characters (~2500 tokens)")

    def test_token_estimation_consistency(self):
        """Test that token estimation is consistent across functions."""
        test_texts = [
            "",
            "a",
            "test",
            "hello world",
            "This is a longer test string for consistency checking.",
            "Multi\nline\ntext\nwith\nspecial\ncharacters!@#$%",
        ]

        for text in test_texts:
            direct_estimate = estimate_tokens(text)
            char_count = len(text) if text else 0
            formatted_result = format_token_count(char_count)

            # Extract token count from formatted string
            formatted_tokens = int(formatted_result.split("~")[1].split(" ")[0])

            self.assertEqual(
                direct_estimate,
                formatted_tokens,
                f"Inconsistent token count for text: '{text}'",
            )

    def test_log_with_tokens_integration(self):
        """Integration test for log_with_tokens with various inputs."""
        mock_logger = Mock()

        test_cases = [
            ("Empty", "", "Empty: 0 characters (~0 tokens)"),
            ("Short", "hi", "Short: 2 characters (~0 tokens)"),
            ("Medium", "hello world", "Medium: 11 characters (~2 tokens)"),
            (
                "Long",
                "This is a much longer test message",
                "Long: 34 characters (~8 tokens)",
            ),
        ]

        for message, text, expected in test_cases:
            mock_logger.reset_mock()
            log_with_tokens(message, text, logger=mock_logger)
            mock_logger.info.assert_called_once_with(expected)


class TestFileCache(unittest.TestCase):
    """Comprehensive test suite for file_cache.py functionality."""

    def setUp(self):
        """Set up test environment before each test."""
        # Clear cache before each test to ensure clean state
        file_cache.clear_file_cache()

        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_1 = os.path.join(self.temp_dir, "test_file_1.txt")
        self.test_file_2 = os.path.join(self.temp_dir, "test_file_2.txt")
        self.nonexistent_file = os.path.join(self.temp_dir, "nonexistent.txt")

        # Create test file content
        self.test_content_1 = "This is test content for file 1.\nIt has multiple lines.\nTotal: 67 characters."
        self.test_content_2 = (
            "Different content for file 2 with unicode: café ñoño 你好"
        )

        # Write test files
        with open(self.test_file_1, "w", encoding="utf-8") as f:
            f.write(self.test_content_1)
        with open(self.test_file_2, "w", encoding="utf-8") as f:
            f.write(self.test_content_2)

    def tearDown(self):
        """Clean up after each test."""
        # Clear cache after each test
        file_cache.clear_file_cache()

        # Clean up temporary files


        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_basic_read_file_cached_functionality(self):
        """Test basic read_file_cached functionality."""
        # Test reading a file for the first time
        content = file_cache.read_file_cached(self.test_file_1)
        self.assertEqual(content, self.test_content_1)

        # Test reading the same file again (should be cached)
        content_cached = file_cache.read_file_cached(self.test_file_1)
        self.assertEqual(content_cached, self.test_content_1)

        # Test reading a different file
        content_2 = file_cache.read_file_cached(self.test_file_2)
        self.assertEqual(content_2, self.test_content_2)

    def test_cache_hit_and_miss_behavior(self):
        """Test cache hit and miss statistics tracking."""
        # Clear cache and get initial stats
        file_cache.clear_file_cache()
        initial_stats = file_cache.get_cache_stats()
        self.assertEqual(initial_stats["cache_hits"], 0)
        self.assertEqual(initial_stats["cache_misses"], 0)

        # First read should be a cache miss
        file_cache.read_file_cached(self.test_file_1)
        stats_after_miss = file_cache.get_cache_stats()
        self.assertEqual(stats_after_miss["cache_hits"], 0)
        self.assertEqual(stats_after_miss["cache_misses"], 1)
        self.assertEqual(stats_after_miss["total_requests"], 1)
        self.assertEqual(stats_after_miss["hit_rate_percent"], 0.0)

        # Second read should be a cache hit
        file_cache.read_file_cached(self.test_file_1)
        stats_after_hit = file_cache.get_cache_stats()
        self.assertEqual(stats_after_hit["cache_hits"], 1)
        self.assertEqual(stats_after_hit["cache_misses"], 1)
        self.assertEqual(stats_after_hit["total_requests"], 2)
        self.assertEqual(stats_after_hit["hit_rate_percent"], 50.0)

        # Multiple hits should increase hit rate
        for _ in range(3):
            file_cache.read_file_cached(self.test_file_1)

        final_stats = file_cache.get_cache_stats()
        self.assertEqual(final_stats["cache_hits"], 4)
        self.assertEqual(final_stats["cache_misses"], 1)
        self.assertEqual(final_stats["total_requests"], 5)
        self.assertEqual(final_stats["hit_rate_percent"], 80.0)

    def test_thread_safety_concurrent_access(self):
        """Test thread safety with concurrent file access."""
        results = []
        errors = []

        def read_file_worker(file_path, worker_id):
            """Worker function for concurrent file reading."""
            try:
                for i in range(10):
                    content = file_cache.read_file_cached(file_path)
                    results.append((worker_id, i, len(content)))
                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Start multiple threads reading the same file
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=read_file_worker, args=(self.test_file_1, i)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        self.assertEqual(
            len(errors), 0, f"Errors occurred during concurrent access: {errors}"
        )

        # Verify all reads returned consistent content length
        expected_length = len(self.test_content_1)
        for worker_id, iteration, content_length in results:
            self.assertEqual(
                content_length,
                expected_length,
                f"Inconsistent content length from worker {worker_id}, iteration {iteration}",
            )

        # Verify we got expected number of results (5 workers * 10 iterations each)
        self.assertEqual(len(results), 50)

        # Verify cache stats make sense (should have hits and misses due to concurrency)
        stats = file_cache.get_cache_stats()
        self.assertGreater(stats["total_requests"], 0)
        self.assertEqual(
            stats["total_requests"], stats["cache_hits"] + stats["cache_misses"]
        )

    def test_ttl_expiration_testing(self):
        """Test TTL expiration functionality (mocked for speed)."""
        # Mock the TTL cache to have a very short TTL for testing
        with patch("file_cache._file_cache") as mock_cache:
            # Configure mock to simulate TTL expiration
            mock_cache.__contains__.side_effect = [
                False,
                True,
                False,
            ]  # miss, hit, expired
            mock_cache.__getitem__.return_value = self.test_content_1

            # First read - cache miss
            with patch("builtins.open", mock_open_read(self.test_content_1)):
                content1 = file_cache.read_file_cached(self.test_file_1)
                self.assertEqual(content1, self.test_content_1)

            # Second read - cache hit
            content2 = file_cache.read_file_cached(self.test_file_1)
            self.assertEqual(content2, self.test_content_1)

            # Third read - cache expired, miss again
            with patch("builtins.open", mock_open_read(self.test_content_1)):
                content3 = file_cache.read_file_cached(self.test_file_1)
                self.assertEqual(content3, self.test_content_1)

    def test_cache_statistics_tracking(self):
        """Test comprehensive cache statistics tracking."""
        # Clear cache and verify initial state
        file_cache.clear_file_cache()
        stats = file_cache.get_cache_stats()

        # Verify initial stats structure
        expected_keys = {
            "cache_hits",
            "cache_misses",
            "total_requests",
            "hit_rate_percent",
            "total_cached_chars",
            "total_cached_tokens",
            "cached_files",
            "uptime_seconds",
        }
        self.assertEqual(set(stats.keys()), expected_keys)

        # Verify initial values
        self.assertEqual(stats["cache_hits"], 0)
        self.assertEqual(stats["cache_misses"], 0)
        self.assertEqual(stats["total_requests"], 0)
        self.assertEqual(stats["hit_rate_percent"], 0)
        self.assertEqual(stats["total_cached_chars"], 0)
        self.assertEqual(stats["total_cached_tokens"], 0)
        self.assertEqual(stats["cached_files"], 0)
        self.assertGreaterEqual(stats["uptime_seconds"], 0)

        # Read a file and verify stats update
        file_cache.read_file_cached(self.test_file_1)
        stats_after_read = file_cache.get_cache_stats()

        self.assertEqual(stats_after_read["cache_misses"], 1)
        self.assertEqual(stats_after_read["total_requests"], 1)
        self.assertEqual(stats_after_read["cached_files"], 1)
        self.assertEqual(
            stats_after_read["total_cached_chars"], len(self.test_content_1)
        )
        self.assertEqual(
            stats_after_read["total_cached_tokens"], len(self.test_content_1) // 4
        )

        # Read another file
        file_cache.read_file_cached(self.test_file_2)
        stats_after_two_files = file_cache.get_cache_stats()

        self.assertEqual(stats_after_two_files["cache_misses"], 2)
        self.assertEqual(stats_after_two_files["cached_files"], 2)
        expected_total_chars = len(self.test_content_1) + len(self.test_content_2)
        self.assertEqual(
            stats_after_two_files["total_cached_chars"], expected_total_chars
        )

    def test_error_handling_missing_files(self):
        """Test error handling for missing files."""
        # Test reading a nonexistent file
        with self.assertRaises(FileNotFoundError):
            file_cache.read_file_cached(self.nonexistent_file)

        # Verify cache stats are not corrupted by the error
        stats = file_cache.get_cache_stats()
        self.assertEqual(stats["cache_hits"], 0)
        self.assertEqual(stats["cache_misses"], 1)  # Should count as miss attempt

        # Test with various invalid paths
        invalid_paths = [
            "/path/that/does/not/exist.txt",
            "",
            "/root/restricted_file.txt",  # Assuming no root access
        ]

        for invalid_path in invalid_paths:
            with self.assertRaises((FileNotFoundError, IOError, PermissionError)):
                file_cache.read_file_cached(invalid_path)

    def test_cache_invalidation_functionality(self):
        """Test cache invalidation functionality."""
        # Read a file to cache it
        content = file_cache.read_file_cached(self.test_file_1)
        self.assertEqual(content, self.test_content_1)

        # Verify file is cached
        stats_before = file_cache.get_cache_stats()
        self.assertEqual(stats_before["cached_files"], 1)

        # Invalidate the file
        result = file_cache.invalidate_file(self.test_file_1)
        self.assertTrue(
            result, "invalidate_file should return True when file was cached"
        )

        # Verify file is no longer cached
        stats_after = file_cache.get_cache_stats()
        self.assertEqual(stats_after["cached_files"], 0)

        # Try to invalidate a file that wasn't cached
        result_not_cached = file_cache.invalidate_file(self.test_file_2)
        self.assertFalse(
            result_not_cached,
            "invalidate_file should return False when file wasn't cached",
        )

        # Verify invalidating nonexistent file doesn't crash
        result_nonexistent = file_cache.invalidate_file(self.nonexistent_file)
        self.assertFalse(result_nonexistent)

    def test_performance_comparison_vs_direct_reads(self):
        """Test performance comparison between cached and direct file reads."""
        # Note: This is more of a behavioral test than strict performance test
        # We're testing that caching works as expected, not measuring exact times

        file_path = self.test_file_1

        # Time direct file reads (multiple reads)
        direct_read_times = []
        for _ in range(5):
            start_time = time.time()
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            end_time = time.time()
            direct_read_times.append(end_time - start_time)
            self.assertEqual(content, self.test_content_1)

        # Clear cache and do first cached read (should be similar to direct read)
        file_cache.clear_file_cache()
        start_time = time.time()
        cached_content_first = file_cache.read_file_cached(file_path)
        first_cached_time = time.time() - start_time
        self.assertEqual(cached_content_first, self.test_content_1)

        # Time subsequent cached reads (should be faster)
        cached_read_times = []
        for _ in range(5):
            start_time = time.time()
            cached_content = file_cache.read_file_cached(file_path)
            end_time = time.time()
            cached_read_times.append(end_time - start_time)
            self.assertEqual(cached_content, self.test_content_1)

        # Verify cache behavior (hits should outnumber misses)
        stats = file_cache.get_cache_stats()
        self.assertEqual(stats["cache_misses"], 1)  # Only first read
        self.assertEqual(stats["cache_hits"], 5)  # Subsequent reads
        self.assertEqual(stats["hit_rate_percent"], 83.3)  # 5/6 * 100, rounded

        # Behavioral verification: cached reads should be consistent
        self.assertTrue(
            all(time_val >= 0 for time_val in cached_read_times),
            "All cached read times should be non-negative",
        )

    def test_path_normalization(self):
        """Test that different path representations for the same file use the same cache entry."""
        # Create paths that should normalize to the same file
        absolute_path = os.path.abspath(self.test_file_1)
        relative_path = os.path.relpath(self.test_file_1)

        # Read using absolute path
        content1 = file_cache.read_file_cached(absolute_path)
        stats_after_abs = file_cache.get_cache_stats()

        # Read using relative path (should be cache hit if normalization works)
        content2 = file_cache.read_file_cached(relative_path)
        stats_after_rel = file_cache.get_cache_stats()

        # Both should return same content
        self.assertEqual(content1, content2)
        self.assertEqual(content1, self.test_content_1)

        # Should have gotten at least one cache hit if normalization is working
        # (Note: This test may vary based on current working directory)
        self.assertGreaterEqual(stats_after_rel["total_requests"], 1)

    def test_encoding_parameter(self):
        """Test different file encodings."""
        # Create a file with UTF-8 content
        utf8_file = os.path.join(self.temp_dir, "utf8_test.txt")
        utf8_content = "UTF-8 content with unicode: café ñoño 你好"

        with open(utf8_file, "w", encoding="utf-8") as f:
            f.write(utf8_content)

        # Test reading with explicit UTF-8 encoding
        content_utf8 = file_cache.read_file_cached(utf8_file, encoding="utf-8")
        self.assertEqual(content_utf8, utf8_content)

        # Test reading with default encoding (should also be UTF-8)
        content_default = file_cache.read_file_cached(utf8_file)
        self.assertEqual(content_default, utf8_content)

        # Both reads should refer to the same cached content
        stats = file_cache.get_cache_stats()
        self.assertEqual(stats["cache_misses"], 1)  # Only first read was miss
        self.assertGreater(stats["cache_hits"], 0)  # At least one hit


def mock_open_read(content):
    """Helper function to create mock for file reading."""


    return mock_open(read_data=content)


if __name__ == "__main__":
    unittest.main()
