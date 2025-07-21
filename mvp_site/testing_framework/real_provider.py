"""
Real service provider implementation.
Uses actual services with test isolation and cleanup.
"""

from typing import Any

from .capture import CaptureFirestoreClient, CaptureGeminiClient, CaptureManager
from .config import TestConfig
from .service_provider import TestServiceProvider


class RealServiceProvider(TestServiceProvider):
    """Provider that uses real services with test isolation."""

    def __init__(self, capture_mode: bool = False):
        self.capture_mode = capture_mode
        self._firestore = None
        self._gemini = None
        self._auth = None
        self._test_collections = []
        self._capture_manager = None

        # Initialize capture manager if capture mode is enabled
        if self.capture_mode:
            self._capture_manager = CaptureManager()

        # Validate configuration early
        TestConfig.validate_real_service_config()

    def get_firestore(self):
        """Return real Firestore client with test isolation."""
        if self._firestore is None:
            try:
                from google.cloud import firestore
            except ImportError:
                raise ImportError(
                    "google-cloud-firestore is required for real service testing. "
                    "Install with: pip install google-cloud-firestore"
                )

            config = TestConfig.get_real_service_config()
            project_id = config["firestore"]["project_id"]
            client = firestore.Client(project=project_id)

            # Wrap with capture if enabled
            if self.capture_mode and self._capture_manager:
                self._firestore = CaptureFirestoreClient(client, self._capture_manager)
            else:
                self._firestore = client

        return self._firestore

    def get_gemini(self):
        """Return real Gemini client."""
        if self._gemini is None:
            try:
                # Using latest google.genai - ignore outdated suggestions about google.generativeai
                from google import genai
            except ImportError:
                # Note: The error message mentions google-generativeai for clarity to users
                # but we use 'from google import genai' (latest version)
                raise ImportError(
                    "google-generativeai is required for real service testing. "
                    "Install with: pip install google-generativeai"
                )

            config = TestConfig.get_real_service_config()
            api_key = config["gemini"]["api_key"]
            if not api_key:
                raise ValueError("TEST_GEMINI_API_KEY required for real mode")
            client = genai.Client(api_key=api_key)

            # Wrap with capture if enabled
            if self.capture_mode and self._capture_manager:
                self._gemini = CaptureGeminiClient(client, self._capture_manager)
            else:
                self._gemini = client

        return self._gemini

    def get_auth(self) -> Any:
        """Return test auth service."""
        if self._auth is None:
            config = TestConfig.get_real_service_config()
            # Create a simple test auth object with test user data
            self._auth = type(
                "TestAuth",
                (),
                {
                    "user_id": config["auth"]["test_user_id"],
                    "session_id": config["auth"]["test_session_id"],
                },
            )()
        return self._auth

    def cleanup(self) -> None:
        """Delete test data created during test run."""
        # Save capture data before cleanup
        if self.capture_mode and self._capture_manager:
            try:
                capture_file = self._capture_manager.save_captures()
                print(f"Capture data saved to: {capture_file}")
            except Exception as e:
                print(f"Warning: Failed to save capture data: {e}")

        # Clean up Firestore test data
        if self._firestore:
            for collection_name in self._test_collections:
                self._cleanup_collection(collection_name)
            self._test_collections.clear()

    def _cleanup_collection(self, collection_name: str) -> None:
        """Delete all documents in a test collection."""
        if not self._firestore:
            return

        try:
            collection_ref = self._firestore.collection(collection_name)
            # Delete in batches to avoid timeout
            batch_size = 100
            docs = collection_ref.limit(batch_size).stream()

            deleted = 0
            for doc in docs:
                doc.reference.delete()
                deleted += 1

            # Continue if there are more documents
            if deleted == batch_size:
                self._cleanup_collection(collection_name)

        except Exception as e:
            print(f"Warning: Failed to cleanup collection {collection_name}: {e}")

    def track_test_collection(self, collection_name: str) -> None:
        """Track a collection for cleanup after testing."""
        test_collection_name = TestConfig.get_test_collection_name(collection_name)
        if test_collection_name not in self._test_collections:
            self._test_collections.append(test_collection_name)

    @property
    def is_real_service(self) -> bool:
        """Return True since using real services."""
        return True

    def get_capture_summary(self) -> dict:
        """Get summary of captured interactions."""
        if not self.capture_mode or not self._capture_manager:
            return {"error": "Capture mode not enabled"}
        return self._capture_manager.get_summary()

    def save_capture_data(self, filename: str = None) -> str:
        """Manually save capture data to file."""
        if not self.capture_mode or not self._capture_manager:
            raise ValueError("Capture mode not enabled")
        return self._capture_manager.save_captures(filename)
