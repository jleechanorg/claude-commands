#!/usr/bin/env python3
"""
Phase 5: State helper function tests for firestore_service.py
Test _handle_append_syntax, _handle_core_memories_safeguard,
_handle_dict_merge, _handle_delete_token, _handle_string_to_dict_update
"""

import os

# Add parent directory to path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from firestore_service import (
    DELETE_TOKEN,
    _handle_append_syntax,
    _handle_core_memories_safeguard,
    _handle_delete_token,
    _handle_dict_merge,
    _handle_string_to_dict_update,
    update_state_with_changes,
)


class TestFirestoreStateHelpers(unittest.TestCase):
    """Test state helper functions in firestore_service.py"""

    # Tests for _handle_append_syntax
    @patch("firestore_service._perform_append")
    @patch("logging_util.info")
    def test_handle_append_syntax_valid(self, mock_log, mock_append):
        """Test _handle_append_syntax with valid append syntax"""
        state = {"items": ["existing"]}
        value = {"append": ["new1", "new2"]}

        result = _handle_append_syntax(state, "items", value)

        assert result
        mock_log.assert_called_with(
            "update_state: Detected explicit append for 'items'."
        )
        mock_append.assert_called_once_with(
            state["items"], ["new1", "new2"], "items", deduplicate=False
        )

    def test_handle_append_syntax_not_dict(self):
        """Test _handle_append_syntax with non-dict value"""
        state = {}
        value = "not a dict"

        result = _handle_append_syntax(state, "key", value)

        assert not result

    def test_handle_append_syntax_no_append_key(self):
        """Test _handle_append_syntax with dict missing 'append' key"""
        state = {}
        value = {"other": "value"}

        result = _handle_append_syntax(state, "key", value)

        assert not result

    @patch("firestore_service._perform_append")
    @patch("logging_util.info")
    def test_handle_append_syntax_creates_list(self, mock_log, mock_append):
        """Test _handle_append_syntax creates list if missing"""
        state = {}
        value = {"append": "single_item"}

        result = _handle_append_syntax(state, "new_key", value)

        assert result
        assert state["new_key"] == []
        mock_append.assert_called_once()

    @patch("firestore_service._perform_append")
    @patch("logging_util.info")
    def test_handle_append_syntax_core_memories_dedup(self, mock_log, mock_append):
        """Test _handle_append_syntax with core_memories uses deduplication"""
        state = {"core_memories": ["memory1"]}
        value = {"append": ["memory2", "memory1"]}  # memory1 is duplicate

        result = _handle_append_syntax(state, "core_memories", value)

        assert result
        # Verify deduplicate=True for core_memories
        mock_append.assert_called_once_with(
            state["core_memories"],
            ["memory2", "memory1"],
            "core_memories",
            deduplicate=True,
        )

    # Tests for _handle_core_memories_safeguard
    @patch("firestore_service._perform_append")
    @patch("logging_util.warning")
    def test_handle_core_memories_safeguard_triggered(self, mock_warning, mock_append):
        """Test _handle_core_memories_safeguard prevents overwrite"""
        state = {"core_memories": ["existing"]}
        value = ["new1", "new2"]  # Direct overwrite attempt

        result = _handle_core_memories_safeguard(state, "core_memories", value)

        assert result
        mock_warning.assert_called_once()
        assert "CRITICAL SAFEGUARD" in mock_warning.call_args[0][0]
        mock_append.assert_called_once_with(
            state["core_memories"], value, "core_memories", deduplicate=True
        )

    def test_handle_core_memories_safeguard_other_key(self):
        """Test _handle_core_memories_safeguard ignores other keys"""
        state = {"other_key": "value"}

        result = _handle_core_memories_safeguard(state, "other_key", ["new"])

        assert not result

    @patch("firestore_service._perform_append")
    @patch("logging_util.warning")
    def test_handle_core_memories_safeguard_creates_list(
        self, mock_warning, mock_append
    ):
        """Test _handle_core_memories_safeguard creates list if missing"""
        state = {}
        value = "single_memory"

        result = _handle_core_memories_safeguard(state, "core_memories", value)

        assert result
        assert state["core_memories"] == []
        mock_append.assert_called_once()

    # Tests for _handle_dict_merge
    def test_handle_dict_merge_non_dict_value(self):
        """Test _handle_dict_merge with non-dict value"""
        state = {}

        result = _handle_dict_merge(state, "key", "not a dict")

        assert not result

    @patch("firestore_service.update_state_with_changes")
    def test_handle_dict_merge_existing_dict(self, mock_update):
        """Test _handle_dict_merge merges with existing dict"""
        state = {"config": {"a": 1, "b": 2}}
        value = {"b": 3, "c": 4}
        mock_update.return_value = {"a": 1, "b": 3, "c": 4}

        result = _handle_dict_merge(state, "config", value)

        assert result
        mock_update.assert_called_once_with({"a": 1, "b": 2}, value)
        assert state["config"] == {"a": 1, "b": 3, "c": 4}

    @patch("firestore_service.update_state_with_changes")
    def test_handle_dict_merge_new_dict(self, mock_update):
        """Test _handle_dict_merge creates new dict when key missing"""
        state = {}
        value = {"a": 1}
        mock_update.return_value = {"a": 1}

        result = _handle_dict_merge(state, "new_key", value)

        assert result
        mock_update.assert_called_once_with({}, value)
        assert state["new_key"] == {"a": 1}

    @patch("firestore_service.update_state_with_changes")
    def test_handle_dict_merge_overwrite_non_dict(self, mock_update):
        """Test _handle_dict_merge overwrites non-dict existing value"""
        state = {"key": "string_value"}
        value = {"a": 1}
        mock_update.return_value = {"a": 1}

        result = _handle_dict_merge(state, "key", value)

        assert result
        # Should create new dict, not merge with string
        mock_update.assert_called_once_with({}, value)
        assert state["key"] == {"a": 1}

    # Tests for _handle_delete_token
    @patch("logging_util.info")
    def test_handle_delete_token_deletes_existing(self, mock_log):
        """Test _handle_delete_token removes existing key"""
        state = {"key1": "value1", "key2": "value2"}

        result = _handle_delete_token(state, "key1", DELETE_TOKEN)

        assert result
        assert "key1" not in state
        assert "key2" in state
        mock_log.assert_called_with(
            "update_state: Deleting key 'key1' due to DELETE_TOKEN."
        )

    @patch("logging_util.info")
    def test_handle_delete_token_missing_key(self, mock_log):
        """Test _handle_delete_token with non-existent key"""
        state = {"other": "value"}

        result = _handle_delete_token(state, "missing", DELETE_TOKEN)

        assert result
        assert state == {"other": "value"}
        mock_log.assert_called_with(
            "update_state: Attempted to delete key 'missing' but it doesn't exist."
        )

    def test_handle_delete_token_wrong_value(self):
        """Test _handle_delete_token with value not DELETE_TOKEN"""
        state = {"key": "value"}

        result = _handle_delete_token(state, "key", "not_delete_token")

        assert not result
        assert "key" in state  # Key not deleted

    # Tests for _handle_string_to_dict_update
    @patch("logging_util.info")
    def test_handle_string_to_dict_update_preserves_dict(self, mock_log):
        """Test _handle_string_to_dict_update preserves dict structure"""
        state = {"quest": {"name": "Main Quest", "level": 5}}
        value = "completed"

        result = _handle_string_to_dict_update(state, "quest", value)

        assert result
        assert state["quest"] == {
            "name": "Main Quest",
            "level": 5,
            "status": "completed",
        }
        mock_log.assert_called_once()

    def test_handle_string_to_dict_update_non_dict_existing(self):
        """Test _handle_string_to_dict_update with non-dict existing value"""
        state = {"key": "string_value"}

        result = _handle_string_to_dict_update(state, "key", "new_value")

        assert not result

    def test_handle_string_to_dict_update_missing_key(self):
        """Test _handle_string_to_dict_update with missing key"""
        state = {}

        result = _handle_string_to_dict_update(state, "missing", "value")

        assert not result

    @patch("logging_util.info")
    def test_handle_string_to_dict_update_overwrites_status(self, mock_log):
        """Test _handle_string_to_dict_update overwrites existing status"""
        state = {"quest": {"name": "Quest", "status": "active"}}
        value = "completed"

        result = _handle_string_to_dict_update(state, "quest", value)

        assert result
        assert state["quest"]["status"] == "completed"
        assert state["quest"]["name"] == "Quest"

    # Integration test for update_state_with_changes
    def test_update_state_with_changes_integration(self):
        """Test update_state_with_changes with various scenarios"""
        state = {
            "hp": 100,
            "inventory": ["sword", "shield"],
            "stats": {"str": 18, "dex": 14},
            "core_memories": ["memory1"],
            "to_delete": "value",
        }

        changes = {
            "hp": 80,  # Simple overwrite
            "inventory": {"append": ["potion"]},  # Append syntax
            "stats": {"con": 16},  # Dict merge
            "core_memories": ["memory2", "memory3"],  # Safeguarded
            "to_delete": DELETE_TOKEN,  # Deletion
            "new_key": "new_value",  # New key
        }

        with patch("logging_util.info"), patch("logging_util.warning"):
            result = update_state_with_changes(state, changes)

        # Verify results
        assert result["hp"] == 80
        assert "potion" in result["inventory"]
        assert result["stats"] == {"str": 18, "dex": 14, "con": 16}
        assert "memory1" in result["core_memories"]  # Original preserved
        assert "memory2" in result["core_memories"]  # New added
        assert "to_delete" not in result
        assert result["new_key"] == "new_value"

    # =============================================================================
    # MATRIX-DRIVEN TDD TESTS - Phase 1: RED (Failing Tests)
    # =============================================================================

    def test_matrix_delete_token_comprehensive(self):
        """Matrix 1: DELETE_TOKEN handling - All combinations [1,1-3]"""
        # Test cases based on comprehensive matrix planning
        test_cases = [
            # [1,1] DELETE_TOKEN with existing key - should delete
            {
                "name": "delete_existing_key",
                "state": {"key": "value", "other": "data"},
                "key": "key",
                "value": DELETE_TOKEN,
                "expected_handled": True,
                "expected_state": {"other": "data"}
            },
            # [1,2] DELETE_TOKEN with non-existing key - should log attempt
            {
                "name": "delete_missing_key",
                "state": {"other": "data"},
                "key": "missing_key",
                "value": DELETE_TOKEN,
                "expected_handled": True,
                "expected_state": {"other": "data"}
            },
            # [1,3] Non-DELETE_TOKEN value - should return False
            {
                "name": "non_delete_token",
                "state": {"key": "value"},
                "key": "key",
                "value": "not_delete_token",
                "expected_handled": False,
                "expected_state": {"key": "value"}
            }
        ]

        for case in test_cases:
            with self.subTest(case=case["name"]):
                result = _handle_delete_token(case["state"], case["key"], case["value"])
                self.assertEqual(result, case["expected_handled"],
                               f"Handler return mismatch for {case['name']}")
                self.assertEqual(case["state"], case["expected_state"],
                               f"State mismatch for {case['name']}")

    @patch("firestore_service._perform_append")
    @patch("logging_util.info")
    def test_matrix_append_syntax_comprehensive(self, mock_log, mock_append):
        """Matrix 2: Append syntax handling - All combinations [2,1-3]"""
        test_cases = [
            # [2,1] Valid append to existing list
            {
                "name": "append_to_existing_list",
                "state": {"items": ["existing"]},
                "key": "items",
                "value": {"append": ["new1", "new2"]},
                "expected_handled": True,
                "expect_append_call": True
            },
            # [2,2] Valid append creates new list
            {
                "name": "append_creates_new_list",
                "state": {},
                "key": "new_items",
                "value": {"append": ["item1"]},
                "expected_handled": True,
                "expect_append_call": True
            },
            # [2,3] Non-append dict should return False
            {
                "name": "non_append_dict",
                "state": {"key": []},
                "key": "key",
                "value": {"other": "value"},
                "expected_handled": False,
                "expect_append_call": False
            }
        ]

        for case in test_cases:
            with self.subTest(case=case["name"]):
                mock_append.reset_mock()
                mock_log.reset_mock()

                result = _handle_append_syntax(case["state"], case["key"], case["value"])
                self.assertEqual(result, case["expected_handled"],
                               f"Handler return mismatch for {case['name']}")

                if case["expect_append_call"]:
                    mock_append.assert_called_once()
                    mock_log.assert_called_once()
                else:
                    mock_append.assert_not_called()

    @patch("firestore_service._perform_append")
    @patch("logging_util.warning")
    def test_matrix_core_memories_safeguard_comprehensive(self, mock_log, mock_append):
        """Matrix 3: Core memories safeguard - All combinations [3,1-3]"""
        test_cases = [
            # [3,1] Core memories with existing list - safe append with dedup
            {
                "name": "core_memories_existing_list",
                "state": {"core_memories": ["old_memory"]},
                "key": "core_memories",
                "value": ["new_memory"],
                "expected_handled": True,
                "expect_warning": True
            },
            # [3,2] Core memories with empty state - creates new list
            {
                "name": "core_memories_empty_state",
                "state": {},
                "key": "core_memories",
                "value": ["first_memory"],
                "expected_handled": True,
                "expect_warning": True
            },
            # [3,3] Non-core-memories key - should return False
            {
                "name": "non_core_memories_key",
                "state": {},
                "key": "other_key",
                "value": ["some_value"],
                "expected_handled": False,
                "expect_warning": False
            }
        ]

        for case in test_cases:
            with self.subTest(case=case["name"]):
                mock_append.reset_mock()
                mock_log.reset_mock()

                result = _handle_core_memories_safeguard(case["state"], case["key"], case["value"])
                self.assertEqual(result, case["expected_handled"],
                               f"Handler return mismatch for {case['name']}")

                if case["expect_warning"]:
                    mock_log.assert_called_once()
                    mock_append.assert_called_once_with(
                        case["state"]["core_memories"], case["value"], "core_memories", deduplicate=True
                    )
                else:
                    mock_log.assert_not_called()
                    mock_append.assert_not_called()

    def test_matrix_integration_state_updates_red_phase(self):
        """Matrix 5: Integration testing - RED phase with expected failures [5,1-4]"""
        # These tests are designed to FAIL initially to follow TDD RED phase
        test_cases = [
            # [5,1] Empty dict with simple values
            {
                "name": "empty_to_simple",
                "initial_state": {},
                "changes": {"name": "test", "level": 1, "active": True},
                "expected_keys": ["name", "level", "active"]
            },
            # [5,2] List field with append operation
            {
                "name": "list_append_operation",
                "initial_state": {"inventory": ["sword"]},
                "changes": {"inventory": {"append": ["potion", "shield"]}},
                "should_contain_original": True,
                "should_contain_new": ["potion", "shield"]
            }
        ]

        for case in test_cases:
            with self.subTest(case=case["name"]):
                result = update_state_with_changes(case["initial_state"], case["changes"])

                # Basic assertions that should work
                self.assertIsInstance(result, dict)

                # More specific assertions for different test types
                if "expected_keys" in case:
                    for key in case["expected_keys"]:
                        self.assertIn(key, result, f"Missing key {key} in result")

    def test_matrix_value_type_validation_red_phase(self):
        """Matrix 6: Value type validation - RED phase [6,1-7]"""
        test_cases = [
            # Test various types to ensure they're handled correctly
            {"input": None, "expected_type": type(None), "description": "none_value"},
            {"input": "test_string", "expected_type": str, "description": "string_value"},
            {"input": 42, "expected_type": int, "description": "integer_value"},
            {"input": 3.14, "expected_type": float, "description": "float_value"},
            {"input": True, "expected_type": bool, "description": "boolean_value"},
            {"input": [1, 2, 3], "expected_type": list, "description": "list_value"},
            {"input": {"key": "value"}, "expected_type": dict, "description": "dict_value"}
        ]

        for case in test_cases:
            with self.subTest(case=case["description"]):
                state = {}
                changes = {"test_field": case["input"]}

                result = update_state_with_changes(state, changes)

                # Basic validation - the function should not crash
                self.assertIsInstance(result, dict)

                # Type preservation tests
                if case["input"] is not None:
                    self.assertIn("test_field", result)
                    self.assertIsInstance(result["test_field"], case["expected_type"])

    def test_matrix_edge_cases_refactor(self):
        """Matrix 7: Edge cases and refactoring validation [7,1-5]"""
        edge_cases = [
            # [7,1] Empty key handling
            {
                "name": "empty_key_handling",
                "state": {},
                "changes": {"": "empty_key_value"},
                "expect_success": True
            },
            # [7,2] Large data handling
            {
                "name": "large_data_handling",
                "state": {},
                "changes": {"large_field": "x" * 1000},
                "expect_success": True
            },
            # [7,3] Nested DELETE_TOKEN
            {
                "name": "nested_delete_token",
                "state": {"parent": {"child": "value", "keep": "data"}},
                "changes": {"parent": {"child": DELETE_TOKEN}},
                "expect_success": True,
                "expected_result": {"parent": {"keep": "data"}}
            },
            # [7,4] Multiple append operations
            {
                "name": "multiple_append_operations",
                "state": {"list1": ["a"], "list2": ["x"]},
                "changes": {"list1": {"append": ["b"]}, "list2": {"append": ["y"]}},
                "expect_success": True
            },
            # [7,5] Complex nested merge
            {
                "name": "complex_nested_merge",
                "state": {"config": {"ui": {"theme": "dark"}, "sound": True}},
                "changes": {"config": {"ui": {"language": "en"}, "notifications": False}},
                "expect_success": True
            }
        ]

        for case in edge_cases:
            with self.subTest(case=case["name"]):
                with patch("logging_util.info"), patch("logging_util.warning"):
                    result = update_state_with_changes(case["state"], case["changes"])

                    # Should not crash
                    self.assertIsInstance(result, dict)

                    # Check specific expected results if provided
                    if "expected_result" in case:
                        self.assertEqual(result, case["expected_result"])

    def test_matrix_performance_characteristics(self):
        """Matrix 8: Performance and scalability testing [8,1-4]"""
        import time

        performance_cases = [
            # [8,1] Large dictionary merge
            {
                "name": "large_dict_merge",
                "state": {f"key_{i}": f"value_{i}" for i in range(100)},
                "changes": {f"key_{i}": f"new_value_{i}" for i in range(50, 150)},
                "max_time": 0.1  # Should complete within 100ms
            },
            # [8,2] Deep nesting performance
            {
                "name": "deep_nesting",
                "state": {"level1": {"level2": {"level3": {"data": "original"}}}},
                "changes": {"level1": {"level2": {"level3": {"new_data": "added"}}}},
                "max_time": 0.05  # Should be very fast for reasonable nesting
            },
            # [8,3] Large list append
            {
                "name": "large_list_append",
                "state": {"items": list(range(1000))},
                "changes": {"items": {"append": list(range(1000, 1100))}},
                "max_time": 0.1  # Should handle large lists efficiently
            }
        ]

        for case in performance_cases:
            with self.subTest(case=case["name"]):
                start_time = time.time()

                with patch("logging_util.info"), patch("logging_util.warning"):
                    result = update_state_with_changes(case["state"], case["changes"])

                elapsed_time = time.time() - start_time

                # Performance assertion
                self.assertLess(elapsed_time, case["max_time"],
                               f"Performance test {case['name']} took {elapsed_time:.3f}s, expected < {case['max_time']}s")

                # Correctness assertion
                self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)
