#!/usr/bin/env python3
"""
Tests for per-comment cache structure.

TDD: Tests written first, implementation follows.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Import the cache class
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from per_comment_cache import PerCommentCache


class TestPerCommentCache(unittest.TestCase):
    """Test suite for per-comment cache structure."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_dir = self.temp_dir / "test_cache"
        self.cache = PerCommentCache(self.cache_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_single_comment(self):
        """Test saving a single comment creates individual file."""
        # Arrange
        comment = {
            "id": "12345",
            "type": "general",
            "body": "Test comment",
            "author": "testuser",
            "created_at": "2026-01-16T00:00:00Z"
        }
        
        # Act
        self.cache.save_comment(comment)
        
        # Assert
        comment_file = self.cache_dir / "comments" / "12345.json"
        self.assertTrue(comment_file.exists())
        with open(comment_file) as f:
            saved = json.load(f)
        self.assertEqual(saved["id"], "12345")
        self.assertEqual(saved["body"], "Test comment")

    def test_save_multiple_comments(self):
        """Test saving multiple comments creates individual files."""
        # Arrange
        comments = [
            {"id": "1", "type": "general", "body": "Comment 1"},
            {"id": "2", "type": "inline", "body": "Comment 2"},
            {"id": "3", "type": "review", "body": "Comment 3"}
        ]
        
        # Act
        self.cache.save_comments(comments, "123", "2026-01-16T00:00:00Z", {})
        
        # Assert
        self.assertTrue((self.cache_dir / "comments" / "1.json").exists())
        self.assertTrue((self.cache_dir / "comments" / "2.json").exists())
        self.assertTrue((self.cache_dir / "comments" / "3.json").exists())
        
        index_file = self.cache_dir / "comments_index.json"
        self.assertTrue(index_file.exists())
        with open(index_file) as f:
            index = json.load(f)
        self.assertEqual(index["total"], 3)
        self.assertEqual(len(index["comment_ids"]), 3)

    def test_load_single_comment(self):
        """Test loading a single comment by ID."""
        # Arrange
        comment = {"id": "12345", "body": "Test"}
        self.cache.save_comment(comment)
        
        # Act
        loaded = self.cache.load_comment("12345")
        
        # Assert
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["id"], "12345")

    def test_load_all_comments(self):
        """Test loading all comments from cache."""
        # Arrange
        comments = [
            {"id": "1", "body": "Comment 1"},
            {"id": "2", "body": "Comment 2"}
        ]
        self.cache.save_comments(comments, "123", "2026-01-16T00:00:00Z", {})
        
        # Act
        loaded = self.cache.load_all_comments()
        
        # Assert
        self.assertEqual(len(loaded), 2)
        self.assertEqual({str(c["id"]) for c in loaded}, {"1", "2"})

    def test_add_or_update_comment(self):
        """Test adding a new comment or updating existing."""
        # Arrange
        initial_comment = {"id": "1", "body": "Original", "type": "general"}
        self.cache.save_comments([initial_comment], "123", "2026-01-16T00:00:00Z", {})
        
        # Act - Update existing
        updated = {"id": "1", "body": "Updated", "type": "general"}
        self.cache.add_or_update_comment(updated)
        
        # Assert
        loaded = self.cache.load_comment("1")
        self.assertEqual(loaded["body"], "Updated")
        
        # Act - Add new
        new_comment = {"id": "2", "body": "New", "type": "general"}
        self.cache.add_or_update_comment(new_comment)
        
        # Assert
        self.assertTrue((self.cache_dir / "comments" / "2.json").exists())
        all_comments = self.cache.load_all_comments()
        self.assertEqual(len(all_comments), 2)

    def test_index_metadata(self):
        """Test index file contains correct metadata."""
        # Arrange
        comments = [
            {"id": "1", "type": "general"},
            {"id": "2", "type": "inline"},
            {"id": "3", "type": "general"}
        ]
        ci_status = {"overall_state": "PASSING"}
        
        # Act
        self.cache.save_comments(comments, "123", "2026-01-16T00:00:00Z", ci_status)
        
        # Assert
        with open(self.cache_dir / "comments_index.json") as f:
            index = json.load(f)
        self.assertEqual(index["pr"], "123")
        self.assertEqual(index["total"], 3)
        self.assertEqual(index["by_type"]["general"], 2)
        self.assertEqual(index["by_type"]["inline"], 1)
        self.assertEqual(index["ci_status"], ci_status)

    def test_incremental_update_efficiency(self):
        """Test that updating one comment doesn't rewrite all files."""
        # Arrange
        comments = [{"id": str(i), "body": f"Comment {i}", "type": "general"} for i in range(10)]
        self.cache.save_comments(comments, "123", "2026-01-16T00:00:00Z", {})
        
        # Get initial modification times
        import time
        time.sleep(0.1)  # Ensure different timestamps
        initial_mtimes = {}
        for i in range(10):
            if i != 5:  # Skip the one we'll update
                file_path = self.cache_dir / "comments" / f"{i}.json"
                initial_mtimes[i] = file_path.stat().st_mtime
        
        # Act - Update only comment 5
        updated = {"id": "5", "body": "Updated comment 5", "type": "general"}
        self.cache.add_or_update_comment(updated)
        
        # Assert - Only comment 5 and index should be modified
        for i in range(10):
            file_path = self.cache_dir / "comments" / f"{i}.json"
            if i == 5:
                self.assertGreaterEqual(file_path.stat().st_mtime, initial_mtimes.get(5, 0))
            else:
                # Allow small time differences due to filesystem precision
                self.assertAlmostEqual(file_path.stat().st_mtime, initial_mtimes[i], delta=1)


if __name__ == "__main__":
    unittest.main()
