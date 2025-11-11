import json
import random
import sqlite3
from typing import Any
from unittest.mock import Mock

import requests
from firebase_admin import auth, firestore, storage


class SmartMockGenerator:
    def __init__(self):
        self.mocks = {}

    def generate_firebase_auth_mock(self) -> Mock:
        mock_auth = Mock(spec=auth)
        mock_auth.create_user.return_value = Mock(
            uid="test_uid_123",
            email="test@example.com",
            display_name="Test User"
        )
        mock_auth.get_user.return_value = Mock(
            uid="test_uid_123",
            email="test@example.com",
            display_name="Test User"
        )
        mock_auth.delete_user.return_value = None
        mock_auth.update_user.return_value = Mock(
            uid="test_uid_123",
            email="updated@example.com",
            display_name="Updated User"
        )
        return mock_auth

    def generate_firebase_firestore_mock(self) -> Mock:
        mock_firestore = Mock(spec=firestore)
        mock_client = Mock()
        mock_collection = Mock()
        mock_document = Mock()

        # Mock document reference
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = Mock(
            exists=True,
            to_dict=lambda: {"id": "doc1", "name": "Test Document", "value": 42}
        )
        mock_doc_ref.set.return_value = Mock(update_time="2023-01-01T00:00:00Z")
        mock_doc_ref.update.return_value = Mock(update_time="2023-01-01T00:00:00Z")
        mock_doc_ref.delete.return_value = None

        # Mock collection reference
        mock_collection.document.return_value = mock_doc_ref
        mock_collection.get.return_value = [
            Mock(to_dict=lambda: {"id": "doc1", "name": "Document 1"}),
            Mock(to_dict=lambda: {"id": "doc2", "name": "Document 2"})
        ]

        # Mock client
        mock_client.collection.return_value = mock_collection
        mock_firestore.client.return_value = mock_client

        return mock_firestore

    def generate_firebase_storage_mock(self) -> Mock:
        mock_storage = Mock(spec=storage)
        mock_bucket = Mock()
        mock_blob = Mock()

        mock_blob.upload_from_string.return_value = None
        mock_blob.download_as_text.return_value = "test content"
        mock_blob.delete.return_value = None
        mock_blob.generate_signed_url.return_value = "https://example.com/signed-url"

        mock_bucket.blob.return_value = mock_blob
        mock_storage.bucket.return_value = mock_bucket

        return mock_storage

    def generate_api_mock(self, endpoints: dict[str, Any] | None = None) -> Mock:
        mock_api = Mock(spec=requests)
        mock_response = Mock()

        if endpoints:
            for method, url in endpoints.items():
                if method == "GET":
                    mock_api.get.return_value = mock_response
                elif method == "POST":
                    mock_api.post.return_value = mock_response
                elif method == "PUT":
                    mock_api.put.return_value = mock_response
                elif method == "DELETE":
                    mock_api.delete.return_value = mock_response
        else:
            # Default responses
            mock_response.json.return_value = {"status": "success", "data": []}
            mock_response.status_code = 200
            mock_response.text = json.dumps({"status": "success", "data": []})

            mock_api.get.return_value = mock_response
            mock_api.post.return_value = mock_response
            mock_api.put.return_value = mock_response
            mock_api.delete.return_value = mock_response

        return mock_api

    def generate_database_mock(self, schema: dict[str, list[str]] | None = None) -> Mock:
        mock_db = Mock(spec=sqlite3)
        mock_connection = Mock()
        mock_cursor = Mock()

        mock_cursor.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = None

        if schema:
            for table, columns in schema.items():
                # Generate sample data for the table
                sample_data = []
                for _ in range(random.randint(1, 5)):
                    row = {}
                    for col in columns:
                        if "id" in col.lower():
                            row[col] = random.randint(1, 1000)
                        elif "name" in col.lower():
                            row[col] = f"Test {col} {random.randint(1, 100)}"
                        elif "email" in col.lower():
                            row[col] = f"test{random.randint(1, 1000)}@example.com"
                        elif "date" in col.lower():
                            row[col] = "2023-01-01"
                        else:
                            row[col] = random.choice([1, "test", True, None])
                    sample_data.append(row)

                # Mock select queries for this table
                mock_cursor.fetchall.return_value = sample_data
                mock_cursor.fetchone.return_value = sample_data[0] if sample_data else None

        mock_connection.cursor.return_value = mock_cursor
        mock_db.connect.return_value = mock_connection

        return mock_db

    def generate_all_mocks(self,
                          firebase: bool = True,
                          api_endpoints: dict[str, Any] | None = None,
                          db_schema: dict[str, list[str]] | None = None) -> dict[str, Mock]:
        mocks = {}

        if firebase:
            mocks['firebase_auth'] = self.generate_firebase_auth_mock()
            mocks['firebase_firestore'] = self.generate_firebase_firestore_mock()
            mocks['firebase_storage'] = self.generate_firebase_storage_mock()

        if api_endpoints is not None:
            mocks['api'] = self.generate_api_mock(api_endpoints)
        else:
            mocks['api'] = self.generate_api_mock()

        if db_schema is not None:
            mocks['database'] = self.generate_database_mock(db_schema)
        else:
            mocks['database'] = self.generate_database_mock()

        self.mocks = mocks
        return mocks

    def get_mock(self, service_name: str) -> Mock | None:
        return self.mocks.get(service_name)
