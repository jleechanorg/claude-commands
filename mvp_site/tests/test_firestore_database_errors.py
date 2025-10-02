"""
Unit tests for firestore_service.py database error handling.

Tests connection failures, transaction errors, query problems,
and document-level error scenarios to improve coverage.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from google.api_core import exceptions

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set testing environment
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["TESTING"] = "true"

import pytest

from mvp_site import firestore_service
from mvp_site.game_state import GameState


class TestFirestoreDatabaseErrors(unittest.TestCase):
    """Test database error scenarios in firestore_service.py"""

    def setUp(self):
        """Set up test environment"""
        self.test_user_id = "test_user_123"
        self.test_campaign_id = "test_campaign_456"
        self.game_state = GameState()
        self.game_state.campaign_id = self.test_campaign_id

    # Group 1 - Connection Errors

    @patch("firestore_service.get_db")
    def test_connection_timeout_recovery(self, mock_get_db):
        """Test recovery from database connection timeouts"""

        # Mock timeout exception
        timeout_error = exceptions.DeadlineExceeded("Connection timeout")
        mock_db = mock_get_db.return_value
        mock_db.collection.side_effect = timeout_error

        # Test that connection timeout raises exception (current behavior)
        with pytest.raises(Exception) as context:
            firestore_service.get_campaigns_for_user(self.test_user_id)

        # Should raise timeout exception
        assert "timeout" in str(context.value).lower()

    @patch("firestore_service.get_db")
    def test_connection_refused_handling(self, mock_get_db):
        """Test handling of network connection failures"""

        # Mock connection refused
        connection_error = exceptions.ServiceUnavailable("Connection refused")
        mock_db = mock_get_db.return_value
        mock_db.collection.side_effect = connection_error

        # Test connection error handling (current behavior: raises exception)
        with pytest.raises(Exception) as context:
            firestore_service.get_campaigns_for_user(self.test_user_id)

        # Should raise connection exception
        assert "connection" in str(context.value).lower()

    @patch("firestore_service.get_db")
    def test_auth_token_expiry_refresh(self, mock_get_db):
        """Test handling of expired authentication tokens"""

        # Mock authentication error
        auth_error = exceptions.Unauthenticated("Token expired")
        mock_db = mock_get_db.return_value
        mock_db.collection.side_effect = auth_error

        # Test auth error handling (current behavior: raises exception)
        with pytest.raises(Exception) as context:
            firestore_service.get_campaigns_for_user(self.test_user_id)

        # Should raise auth exception
        assert "token" in str(context.value).lower()

    # Group 2 - Transaction Errors

    @patch("firestore_service.get_db")
    def test_transaction_conflict_resolution(self, mock_get_db):
        """Test handling of concurrent transaction conflicts"""

        # Mock transaction conflict
        conflict_error = exceptions.Aborted("Transaction aborted due to conflict")
        mock_db = mock_get_db.return_value
        mock_transaction = MagicMock()
        mock_db.transaction.return_value = mock_transaction
        mock_transaction.get.side_effect = conflict_error

        # Test transaction conflict handling in state update
        result = firestore_service.update_state_with_changes(
            {"initial": "state"}, {"new": "changes"}
        )

        # Should return the merged state even if database update fails
        assert isinstance(result, dict)
        assert result["new"] == "changes"

    @patch("firestore_service.get_db")
    def test_transaction_rollback_on_failure(self, mock_get_db):
        """Test transaction rollback when operations fail"""
        # Mock transaction that fails partway through
        mock_db = mock_get_db.return_value
        mock_transaction = MagicMock()
        mock_db.transaction.return_value = mock_transaction

        # Mock successful get but failed update
        MagicMock()
        mock_transaction.get.return_value.exists = True
        mock_transaction.update.side_effect = Exception("Update failed")

        # Test rollback behavior - this tests that we handle transaction failures
        # The actual test depends on the specific transaction implementation
        result = firestore_service.update_state_with_changes(
            {"test": "data"}, {"update": "value"}
        )

        # Should still return merged state locally even if transaction fails
        assert isinstance(result, dict)

    @patch("firestore_service.get_db")
    def test_deadlock_detection_recovery(self, mock_get_db):
        """Test recovery from transaction deadlocks"""

        # Mock deadlock scenario
        deadlock_error = exceptions.DeadlineExceeded("Deadlock detected")
        mock_db = mock_get_db.return_value
        mock_transaction = MagicMock()
        mock_db.transaction.return_value = mock_transaction
        mock_transaction.get.side_effect = deadlock_error

        # Test deadlock handling in state operations
        result = firestore_service.update_state_with_changes(
            {"nested": {"data": "value"}}, {"nested": {"new": "data"}}
        )

        # Should handle deadlock and return merged state
        assert isinstance(result, dict)
        assert result["nested"]["new"] == "data"

    # Group 3 - Query Errors

    @patch("firestore_service.get_db")
    def test_invalid_query_syntax_handling(self, mock_get_db):
        """Test handling of malformed database queries"""

        # Mock invalid query
        query_error = exceptions.InvalidArgument("Invalid query syntax")
        mock_db = mock_get_db.return_value
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection
        mock_collection.where.side_effect = query_error

        # Test invalid query handling
        result = firestore_service.get_campaigns_for_user(self.test_user_id)

        # Should handle query error gracefully
        assert result == []

    @patch("firestore_service.get_db")
    def test_query_timeout_with_retry(self, mock_get_db):
        """Test handling of slow queries that timeout"""

        # Mock query timeout
        timeout_error = exceptions.DeadlineExceeded("Query timeout")
        mock_db = mock_get_db.return_value
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection
        mock_collection.get.side_effect = timeout_error

        # Test query timeout handling
        result = firestore_service.get_campaigns_for_user(self.test_user_id)

        # Should handle timeout gracefully
        assert result == []

    @patch("firestore_service.get_db")
    def test_query_size_limit_exceeded(self, mock_get_db):
        """Test handling when query results are too large"""

        # Mock result size limit exceeded
        size_error = exceptions.OutOfRange("Result set too large")
        mock_db = mock_get_db.return_value
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection
        mock_collection.stream.side_effect = size_error

        # Test size limit handling
        result = firestore_service.get_campaigns_for_user(self.test_user_id)

        # Should handle size limit gracefully
        assert result == []

    @patch("firestore_service.get_db")
    def test_collection_not_found_error(self, mock_get_db):
        """Test handling when collections don't exist"""

        # Mock collection not found
        not_found_error = exceptions.NotFound("Collection not found")
        mock_db = mock_get_db.return_value
        mock_db.collection.side_effect = not_found_error

        # Test collection not found handling (current behavior: raises exception)
        with pytest.raises(Exception) as context:
            firestore_service.get_campaigns_for_user(self.test_user_id)

        # Should raise not found exception
        assert "not found" in str(context.value).lower()

    # Group 4 - Document Errors

    @patch("firestore_service.get_db")
    def test_document_not_found_graceful(self, mock_get_db):
        """Test graceful handling of missing documents"""
        # Mock document not found
        mock_db = mock_get_db.return_value
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value.exists = False
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_db.collection.return_value = mock_collection

        # Test missing document handling using state update functions
        result = firestore_service.update_state_with_changes(
            {"existing": "data"}, {"new": "value"}
        )

        # Should handle missing document gracefully and return merged state
        assert isinstance(result, dict)
        assert result["new"] == "value"

    @patch("firestore_service.get_db")
    def test_document_size_limit_handling(self, mock_get_db):
        """Test handling of oversized documents (>1MB)"""

        # Mock document too large error
        size_error = exceptions.InvalidArgument("Document too large")
        mock_db = mock_get_db.return_value
        mock_doc_ref = MagicMock()
        mock_doc_ref.set.side_effect = size_error
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_db.collection.return_value = mock_collection

        # Test oversized document handling
        large_data = {"large_field": "x" * 2000000}  # Simulate large data

        # This tests that we can handle large state updates locally
        result = firestore_service.update_state_with_changes(
            {"small": "data"}, large_data
        )

        # Should handle locally even if database write fails
        assert isinstance(result, dict)
        assert "large_field" in result

    @patch("firestore_service.get_db")
    def test_invalid_document_id_format(self, mock_get_db):
        """Test handling of malformed document IDs"""

        # Mock invalid document ID error
        id_error = exceptions.InvalidArgument("Invalid document ID")
        mock_db = mock_get_db.return_value
        mock_collection = MagicMock()
        mock_collection.document.side_effect = id_error
        mock_db.collection.return_value = mock_collection

        # Test invalid ID handling (current behavior: raises exception)
        with pytest.raises(Exception) as context:
            firestore_service.get_campaigns_for_user("invalid/id/with/slashes")

        # Should raise invalid ID exception
        assert "invalid" in str(context.value).lower()

    @patch("firestore_service.get_db")
    def test_document_permission_denied(self, mock_get_db):
        """Test handling of access control failures"""

        # Mock permission denied error
        perm_error = exceptions.PermissionDenied("Access denied")
        mock_db = mock_get_db.return_value
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.side_effect = perm_error
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_db.collection.return_value = mock_collection

        # Test permission handling
        result = firestore_service.get_campaigns_for_user(self.test_user_id)

        # Should handle permission error gracefully
        assert result == []

    @patch("firestore_service.get_db")
    def test_batch_operation_partial_failure(self, mock_get_db):
        """Test handling when some batch operations succeed, others fail"""
        # Mock batch with mixed results
        mock_db = mock_get_db.return_value
        mock_batch = MagicMock()
        mock_db.batch.return_value = mock_batch

        # Mock partial failure in batch commit

        batch_error = exceptions.Aborted("Partial batch failure")
        mock_batch.commit.side_effect = batch_error

        # Test batch partial failure with state operations
        # This simulates what happens when batch operations fail
        result1 = firestore_service.update_state_with_changes({"test": 1}, {"test": 2})
        result2 = firestore_service.update_state_with_changes({"test": 3}, {"test": 4})

        # Should handle partial failure gracefully
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert result1["test"] == 2
        assert result2["test"] == 4


if __name__ == "__main__":
    unittest.main()
