"""
Tests for the capture framework.
"""

import json
import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock

# Import capture modules
from mvp_site.testing_framework.capture import (

import shutil

    CaptureFirestoreClient,
    CaptureGeminiClient,
    CaptureManager,
    cleanup_old_captures,
)
from mvp_site.testing_framework.capture_analysis import (
    CaptureAnalyzer,
    create_mock_baseline,
)


class TestCaptureManager(unittest.TestCase):
    """Test the CaptureManager class."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.capture_manager = CaptureManager(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""


        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test capture manager initialization."""
        self.assertEqual(self.capture_manager.capture_dir, self.temp_dir)
        self.assertEqual(len(self.capture_manager.interactions), 0)
        self.assertTrue(os.path.exists(self.temp_dir))

    def test_capture_interaction_success(self):
        """Test successful interaction capture."""
        with self.capture_manager.capture_interaction(
            "test_service", "test_operation", {"key": "value"}
        ) as interaction:
            # Simulate recording response
            self.capture_manager.record_response(
                interaction["id"], {"result": "success"}
            )

        self.assertEqual(len(self.capture_manager.interactions), 1)
        interaction = self.capture_manager.interactions[0]

        self.assertEqual(interaction["service"], "test_service")
        self.assertEqual(interaction["operation"], "test_operation")
        self.assertEqual(interaction["request"], {"key": "value"})
        self.assertEqual(interaction["response"], {"result": "success"})
        self.assertEqual(interaction["status"], "success")
        self.assertIn("duration_ms", interaction)

    def test_capture_interaction_error(self):
        """Test error handling in interaction capture."""
        with self.assertRaises(ValueError):
            with self.capture_manager.capture_interaction(
                "test_service", "test_operation", {"key": "value"}
            ):
                raise ValueError("Test error")

        self.assertEqual(len(self.capture_manager.interactions), 1)
        interaction = self.capture_manager.interactions[0]

        self.assertEqual(interaction["status"], "error")
        self.assertEqual(interaction["error"], "Test error")
        self.assertEqual(interaction["error_type"], "ValueError")

    def test_save_captures(self):
        """Test saving captures to file."""
        # Add some test interactions
        with self.capture_manager.capture_interaction(
            "service1", "op1", {"data": "test1"}
        ) as interaction:
            self.capture_manager.record_response(interaction["id"], {"result": "ok"})

        with self.capture_manager.capture_interaction(
            "service2", "op2", {"data": "test2"}
        ) as interaction:
            self.capture_manager.record_response(interaction["id"], {"result": "ok"})

        # Save captures
        filepath = self.capture_manager.save_captures()

        # Verify file was created
        self.assertTrue(os.path.exists(filepath))

        # Verify content
        with open(filepath) as f:
            data = json.load(f)

        self.assertEqual(data["total_interactions"], 2)
        self.assertEqual(len(data["interactions"]), 2)
        self.assertIn("session_id", data)
        self.assertIn("timestamp", data)

    def test_sanitize_data(self):
        """Test data sanitization for sensitive fields."""
        test_data = {
            "username": "test_user",
            "password": "secret123",
            "api_key": "abc123",
            "normal_field": "normal_value",
            "nested": {"secret": "hidden", "visible": "shown"},
        }

        sanitized = self.capture_manager._sanitize_data(test_data)

        self.assertEqual(sanitized["username"], "test_user")
        self.assertEqual(sanitized["password"], "[REDACTED]")
        self.assertEqual(sanitized["api_key"], "[REDACTED]")
        self.assertEqual(sanitized["normal_field"], "normal_value")
        self.assertEqual(sanitized["nested"]["secret"], "[REDACTED]")
        self.assertEqual(sanitized["nested"]["visible"], "shown")

    def test_get_summary(self):
        """Test getting summary statistics."""
        # Add various interactions
        with self.capture_manager.capture_interaction(
            "firestore", "get", {}
        ) as interaction:
            self.capture_manager.record_response(interaction["id"], {"docs": []})

        with self.capture_manager.capture_interaction(
            "firestore", "set", {}
        ) as interaction:
            self.capture_manager.record_response(interaction["id"], {"ok": True})

        with self.capture_manager.capture_interaction(
            "gemini", "generate", {}
        ) as interaction:
            self.capture_manager.record_response(
                interaction["id"], {"text": "response"}
            )

        # Test error case
        with self.assertRaises(Exception):
            with self.capture_manager.capture_interaction("test", "error", {}):
                raise Exception("Test error")

        summary = self.capture_manager.get_summary()

        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["services"]["firestore"]["count"], 2)
        self.assertEqual(summary["services"]["gemini"]["count"], 1)
        self.assertEqual(summary["errors"], 1)
        self.assertEqual(summary["success_rate"], 0.75)


class TestCaptureFirestoreClient(unittest.TestCase):
    """Test the Firestore capture wrapper."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.capture_manager = CaptureManager(self.temp_dir)
        self.mock_client = MagicMock()
        self.capture_client = CaptureFirestoreClient(
            self.mock_client, self.capture_manager
        )

    def tearDown(self):
        """Clean up test environment."""


        shutil.rmtree(self.temp_dir)

    def test_collection_add(self):
        """Test collection add with capture."""
        # Mock Firestore response
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "test_doc_id"
        mock_doc_ref.path = "test_collection/test_doc_id"
        self.mock_client.collection.return_value.add.return_value = (None, mock_doc_ref)

        # Perform operation
        collection = self.capture_client.collection("test_collection")
        result = collection.add({"test": "data"})

        # Verify capture
        self.assertEqual(len(self.capture_manager.interactions), 1)
        interaction = self.capture_manager.interactions[0]

        self.assertEqual(interaction["service"], "firestore")
        self.assertEqual(interaction["operation"], "collection.add")
        self.assertEqual(interaction["request"]["collection"], "test_collection")
        self.assertEqual(interaction["request"]["data"], {"test": "data"})
        self.assertEqual(interaction["response"]["document_id"], "test_doc_id")

    def test_document_get(self):
        """Test document get with capture."""
        # Mock Firestore response
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.id = "test_doc"
        mock_doc.to_dict.return_value = {"field": "value"}
        self.mock_client.document.return_value.get.return_value = mock_doc

        # Perform operation
        doc = self.capture_client.document("test_collection/test_doc")
        result = doc.get()

        # Verify capture
        self.assertEqual(len(self.capture_manager.interactions), 1)
        interaction = self.capture_manager.interactions[0]

        self.assertEqual(interaction["service"], "firestore")
        self.assertEqual(interaction["operation"], "document.get")
        self.assertEqual(interaction["response"]["exists"], True)
        self.assertEqual(interaction["response"]["data"], {"field": "value"})


class TestCaptureGeminiClient(unittest.TestCase):
    """Test the Gemini capture wrapper."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.capture_manager = CaptureManager(self.temp_dir)
        self.mock_client = MagicMock()
        self.capture_client = CaptureGeminiClient(
            self.mock_client, self.capture_manager
        )

    def tearDown(self):
        """Clean up test environment."""


        shutil.rmtree(self.temp_dir)

    def test_generate_content(self):
        """Test content generation with capture."""
        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = "Generated response text"
        mock_response.finish_reason = "STOP"
        self.mock_client.generate_content.return_value = mock_response

        # Perform operation
        response = self.capture_client.generate_content("Test prompt")

        # Verify capture
        self.assertEqual(len(self.capture_manager.interactions), 1)
        interaction = self.capture_manager.interactions[0]

        self.assertEqual(interaction["service"], "gemini")
        self.assertEqual(interaction["operation"], "generate_content")
        self.assertEqual(interaction["request"]["prompt"], "Test prompt")
        self.assertEqual(interaction["response"]["text"], "Generated response text")
        self.assertEqual(interaction["response"]["finish_reason"], "STOP")


class TestCaptureAnalyzer(unittest.TestCase):
    """Test the capture analysis tools."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = CaptureAnalyzer(self.temp_dir)

        # Create test capture file
        self.test_data = {
            "session_id": "test_session",
            "timestamp": "2025-01-01T00:00:00",
            "total_interactions": 3,
            "interactions": [
                {
                    "id": 0,
                    "service": "firestore",
                    "operation": "get",
                    "request": {"collection": "test"},
                    "response": {"docs": []},
                    "status": "success",
                    "duration_ms": 100,
                },
                {
                    "id": 1,
                    "service": "gemini",
                    "operation": "generate",
                    "request": {"prompt": "test"},
                    "response": {"text": "response"},
                    "status": "success",
                    "duration_ms": 200,
                },
                {
                    "id": 2,
                    "service": "firestore",
                    "operation": "set",
                    "request": {"doc": "test"},
                    "response": {},
                    "status": "error",
                    "error": "Test error",
                    "duration_ms": 50,
                },
            ],
        }

        self.test_file = os.path.join(self.temp_dir, "capture_test.json")
        with open(self.test_file, "w") as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        """Clean up test environment."""


        shutil.rmtree(self.temp_dir)

    def test_analyze_interactions(self):
        """Test interaction analysis."""
        analysis = self.analyzer._analyze_interactions(self.test_data["interactions"])

        self.assertEqual(analysis["total_interactions"], 3)
        self.assertEqual(analysis["by_service"]["firestore"]["count"], 2)
        self.assertEqual(analysis["by_service"]["gemini"]["count"], 1)
        self.assertEqual(analysis["by_service"]["firestore"]["errors"], 1)
        self.assertEqual(len(analysis["errors"]), 1)
        self.assertEqual(analysis["performance"]["total_duration"], 350)
        self.assertEqual(analysis["performance"]["avg_duration"], 350 / 3)

    def test_compare_with_mock(self):
        """Test comparison with mock responses."""
        mock_responses = {
            "firestore.get": {"docs": []},
            "gemini.generate": {"text": "different response"},
            # Missing firestore.set mock
        }

        comparison = self.analyzer.compare_with_mock(self.test_file, mock_responses)

        self.assertEqual(
            comparison["total_comparisons"], 2
        )  # Only success interactions
        self.assertEqual(comparison["matches"], 1)  # firestore.get matches
        self.assertEqual(len(comparison["differences"]), 1)  # gemini.generate differs
        self.assertEqual(
            len(comparison["missing_mocks"]), 0
        )  # firestore.set was error, so not compared
        self.assertEqual(comparison["accuracy_score"], 0.5)

    def test_generate_report(self):
        """Test report generation."""
        analysis = self.analyzer._analyze_interactions(self.test_data["interactions"])
        report = self.analyzer.generate_report(analysis)

        self.assertIn("Capture Analysis Report", report)
        self.assertIn("Total Interactions: 3", report)
        self.assertIn("firestore", report)
        self.assertIn("gemini", report)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""


        shutil.rmtree(self.temp_dir)

    def test_cleanup_old_captures(self):
        """Test cleanup of old capture files."""
        # Create test files with different ages
        old_file = os.path.join(self.temp_dir, "capture_old.json")
        new_file = os.path.join(self.temp_dir, "capture_new.json")
        non_capture_file = os.path.join(self.temp_dir, "other.json")

        # Create files
        for filepath in [old_file, new_file, non_capture_file]:
            with open(filepath, "w") as f:
                json.dump({"test": "data"}, f)

        # Make old file actually old
        old_time = time.time() - (10 * 24 * 3600)  # 10 days ago
        os.utime(old_file, (old_time, old_time))

        # Run cleanup (keep files newer than 7 days)
        cleanup_old_captures(self.temp_dir, days_to_keep=7)

        # Verify results
        self.assertFalse(os.path.exists(old_file))  # Should be deleted
        self.assertTrue(os.path.exists(new_file))  # Should remain
        self.assertTrue(
            os.path.exists(non_capture_file)
        )  # Should remain (not a capture file)

    def test_create_mock_baseline(self):
        """Test creating mock baseline from capture data."""
        # Create test capture data
        capture_data = {
            "interactions": [
                {
                    "service": "firestore",
                    "operation": "get",
                    "status": "success",
                    "response": {"docs": []},
                },
                {
                    "service": "gemini",
                    "operation": "generate",
                    "status": "success",
                    "response": {"text": "test"},
                },
                {
                    "service": "firestore",
                    "operation": "set",
                    "status": "error",  # Should be ignored
                },
            ]
        }

        capture_file = os.path.join(self.temp_dir, "test_capture.json")
        with open(capture_file, "w") as f:
            json.dump(capture_data, f)

        output_file = os.path.join(self.temp_dir, "mock_baseline.json")

        # Create baseline
        count = create_mock_baseline(capture_file, output_file)

        # Verify results
        self.assertEqual(count, 2)  # Only success interactions
        self.assertTrue(os.path.exists(output_file))

        with open(output_file) as f:
            baseline = json.load(f)

        self.assertIn("firestore.get", baseline)
        self.assertIn("gemini.generate", baseline)
        self.assertNotIn("firestore.set", baseline)  # Error case excluded
        self.assertEqual(baseline["firestore.get"], {"docs": []})
        self.assertEqual(baseline["gemini.generate"], {"text": "test"})


if __name__ == "__main__":
    unittest.main()
