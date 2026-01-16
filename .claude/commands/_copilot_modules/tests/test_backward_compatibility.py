#!/usr/bin/env python3
"""
Tests for backward compatibility with legacy cache format.
"""

import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from per_comment_cache import PerCommentCache


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with legacy format."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_dir = self.temp_dir / "test_cache"
        self.cache = PerCommentCache(self.cache_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_all_comments_handles_missing_index(self):
        """Test that loading works when index doesn't exist."""
        # Arrange - no index file
        
        # Act
        comments = self.cache.load_all_comments()
        
        # Assert
        self.assertEqual(comments, [])

    def test_load_comment_handles_missing_file(self):
        """Test that loading non-existent comment returns None."""
        # Act
        comment = self.cache.load_comment("nonexistent")
        
        # Assert
        self.assertIsNone(comment)

    def test_save_comments_creates_both_formats(self):
        """Test that saving creates per-comment structure."""
        # Arrange
        comments = [
            {"id": "1", "type": "general", "body": "Comment 1"},
            {"id": "2", "type": "inline", "body": "Comment 2"}
        ]
        
        # Act
        self.cache.save_comments(comments, "123", "2026-01-16T00:00:00Z", {})
        
        # Assert - per-comment files exist
        self.assertTrue((self.cache_dir / "comments" / "1.json").exists())
        self.assertTrue((self.cache_dir / "comments" / "2.json").exists())
        self.assertTrue((self.cache_dir / "comments_index.json").exists())
        
        # Assert - can load all comments
        loaded = self.cache.load_all_comments()
        self.assertEqual(len(loaded), 2)


if __name__ == "__main__":
    unittest.main()
