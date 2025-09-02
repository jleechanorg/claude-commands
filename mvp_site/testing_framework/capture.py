"""
Data capture framework for real service interactions.
Records API calls and responses for mock validation and analysis.
"""

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any


class CaptureManager:
    """Manages capture of service interactions for mock validation."""

    def __init__(self, capture_dir: str | None = None):
        """Initialize capture manager with storage directory."""
        self.capture_dir = capture_dir or os.environ.get(
            "TEST_CAPTURE_DIR", "/tmp/test_captures"
        )
        self.interactions = []
        self.capture_session_id = str(int(time.time() * 1000))

        # Ensure capture directory exists
        os.makedirs(self.capture_dir, exist_ok=True)

    @contextmanager
    def capture_interaction(self, service: str, operation: str, request_data: dict):
        """Context manager for capturing service interactions."""
        interaction_id = len(self.interactions)
        start_time = time.time()

        interaction = {
            "id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "operation": operation,
            "request": self._sanitize_data(request_data),
            "start_time": start_time,
        }

        try:
            yield interaction
            # Response will be set by caller
            duration = time.time() - start_time
            interaction["duration_ms"] = duration * 1000
            interaction["status"] = "success"

        except Exception as e:
            duration = time.time() - start_time
            interaction.update(
                {
                    "duration_ms": duration * 1000,
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            raise
        finally:
            # Apply any pending responses that were recorded during execution
            if hasattr(self, '_pending_responses') and interaction["id"] in self._pending_responses:
                interaction["response"] = self._pending_responses[interaction["id"]]
                del self._pending_responses[interaction["id"]]
            
            self.interactions.append(interaction)

    def record_response(self, interaction_id: int, response_data: Any):
        """Record response data for a specific interaction."""
        # Find the interaction by ID in the active context or in the list
        target_interaction = None
        
        # Check if interaction is already in the list
        if interaction_id < len(self.interactions):
            target_interaction = self.interactions[interaction_id]
        else:
            # This might be called during context manager execution
            # where interaction hasn't been added to list yet
            # Store response for later use when interaction is finalized
            if not hasattr(self, '_pending_responses'):
                self._pending_responses = {}
            self._pending_responses[interaction_id] = self._sanitize_data(response_data)
            return
            
        if target_interaction:
            target_interaction["response"] = self._sanitize_data(response_data)

    def save_captures(self, filename: str | None = None) -> str:
        """Save captured interactions to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}_{self.capture_session_id}.json"

        filepath = os.path.join(self.capture_dir, filename)

        capture_data = {
            "session_id": self.capture_session_id,
            "timestamp": datetime.now().isoformat(),
            "total_interactions": len(self.interactions),
            "interactions": self.interactions,
        }

        with open(filepath, "w") as f:
            json.dump(capture_data, f, indent=2, default=str)

        return filepath

    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize data for JSON serialization and privacy."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Redact sensitive fields - match key patterns more specifically
                key_lower = key.lower()
                if any(
                    pattern in key_lower
                    for pattern in ["password", "secret", "token", "api_key", "auth_key", "private_key"]
                ) or key_lower.endswith("_key") or key_lower.startswith("key_"):
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = self._sanitize_data(value)
            return sanitized
        if isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        if hasattr(data, "__dict__"):
            # Handle objects by converting to dict
            return self._sanitize_data(data.__dict__)
        # Handle primitive types
        return data

    def get_summary(self) -> dict:
        """Get summary statistics of captured interactions."""
        if not self.interactions:
            return {"total": 0}

        services = {}
        total_duration = 0
        errors = 0

        for interaction in self.interactions:
            service = interaction["service"]
            if service not in services:
                services[service] = {"count": 0, "operations": {}}

            services[service]["count"] += 1
            operation = interaction["operation"]
            if operation not in services[service]["operations"]:
                services[service]["operations"][operation] = 0
            services[service]["operations"][operation] += 1

            if "duration_ms" in interaction:
                total_duration += interaction["duration_ms"]

            if interaction.get("status") == "error":
                errors += 1

        return {
            "total": len(self.interactions),
            "services": services,
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration / len(self.interactions)
            if self.interactions
            else 0,
            "errors": errors,
            "success_rate": (len(self.interactions) - errors) / len(self.interactions)
            if self.interactions
            else 0,
        }


class CaptureFirestoreClient:
    """Wrapper for Firestore client that captures interactions."""

    def __init__(self, firestore_client, capture_manager: CaptureManager):
        self._client = firestore_client
        self._capture = capture_manager

    def collection(self, collection_path: str):
        """Get collection reference with capture."""
        return CaptureCollectionReference(
            self._client.collection(collection_path), collection_path, self._capture
        )

    def document(self, document_path: str):
        """Get document reference with capture."""
        return CaptureDocumentReference(
            self._client.document(document_path), document_path, self._capture
        )

    def __getattr__(self, name):
        """Delegate other attributes to the real client."""
        return getattr(self._client, name)


class CaptureCollectionReference:
    """Wrapper for Firestore collection reference with capture."""

    def __init__(
        self, collection_ref, collection_path: str, capture_manager: CaptureManager
    ):
        self._ref = collection_ref
        self._path = collection_path
        self._capture = capture_manager

    def add(self, document_data: dict):
        """Add document with capture."""
        with self._capture.capture_interaction(
            "firestore",
            "collection.add",
            {"collection": self._path, "data": document_data},
        ) as interaction:
            result = self._ref.add(document_data)
            self._capture.record_response(
                interaction["id"],
                {"document_id": result[1].id, "document_path": result[1].path},
            )
            return result

    def document(self, document_id: str = None):
        """Get document reference."""
        doc_ref = self._ref.document(document_id)
        return CaptureDocumentReference(
            doc_ref, f"{self._path}/{document_id or 'auto'}", self._capture
        )

    def stream(self):
        """Stream documents with capture."""
        with self._capture.capture_interaction(
            "firestore", "collection.stream", {"collection": self._path}
        ) as interaction:
            docs = list(self._ref.stream())
            self._capture.record_response(
                interaction["id"],
                {
                    "document_count": len(docs),
                    "documents": [
                        {"id": doc.id, "data": doc.to_dict()} for doc in docs
                    ],
                },
            )
            return docs

    def get(self):
        """Get all documents with capture."""
        with self._capture.capture_interaction(
            "firestore", "collection.get", {"collection": self._path}
        ) as interaction:
            docs = list(self._ref.get())
            self._capture.record_response(
                interaction["id"],
                {
                    "document_count": len(docs),
                    "documents": [
                        {"id": doc.id, "data": doc.to_dict()} for doc in docs
                    ],
                },
            )
            return docs

    def __getattr__(self, name):
        """Delegate other attributes to the real reference."""
        return getattr(self._ref, name)


class CaptureDocumentReference:
    """Wrapper for Firestore document reference with capture."""

    def __init__(self, doc_ref, doc_path: str, capture_manager: CaptureManager):
        self._ref = doc_ref
        self._path = doc_path
        self._capture = capture_manager

    def set(self, document_data: dict, merge: bool = False):
        """Set document with capture."""
        with self._capture.capture_interaction(
            "firestore",
            "document.set",
            {"document": self._path, "data": document_data, "merge": merge},
        ) as interaction:
            result = self._ref.set(document_data, merge=merge)
            self._capture.record_response(
                interaction["id"], {"write_result": str(result)}
            )
            return result

    def get(self):
        """Get document with capture."""
        with self._capture.capture_interaction(
            "firestore", "document.get", {"document": self._path}
        ) as interaction:
            doc = self._ref.get()
            self._capture.record_response(
                interaction["id"],
                {
                    "exists": doc.exists,
                    "data": doc.to_dict() if doc.exists else None,
                    "id": doc.id,
                },
            )
            return doc

    def update(self, field_updates: dict):
        """Update document with capture."""
        with self._capture.capture_interaction(
            "firestore",
            "document.update",
            {"document": self._path, "updates": field_updates},
        ) as interaction:
            result = self._ref.update(field_updates)
            self._capture.record_response(
                interaction["id"], {"write_result": str(result)}
            )
            return result

    def delete(self):
        """Delete document with capture."""
        with self._capture.capture_interaction(
            "firestore", "document.delete", {"document": self._path}
        ) as interaction:
            result = self._ref.delete()
            self._capture.record_response(
                interaction["id"], {"write_result": str(result)}
            )
            return result

    def __getattr__(self, name):
        """Delegate other attributes to the real reference."""
        return getattr(self._ref, name)


class CaptureGeminiClient:
    """Wrapper for Gemini client that captures interactions."""

    def __init__(self, gemini_client, capture_manager: CaptureManager):
        self._client = gemini_client
        self._capture = capture_manager

    def generate_content(self, prompt: str, **kwargs):
        """Generate content with capture."""
        with self._capture.capture_interaction(
            "gemini",
            "generate_content",
            {
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "kwargs": kwargs,
            },
        ) as interaction:
            response = self._client.generate_content(prompt, **kwargs)
            self._capture.record_response(
                interaction["id"],
                {
                    "text": response.text[:500] + "..."
                    if len(response.text) > 500
                    else response.text,
                    "finish_reason": getattr(response, "finish_reason", None),
                    "usage_metadata": getattr(response, "usage_metadata", None),
                },
            )
            return response

    def __getattr__(self, name):
        """Delegate other attributes to the real client."""
        return getattr(self._client, name)


def load_capture_data(filepath: str) -> dict:
    """Load captured interaction data from file."""
    with open(filepath) as f:
        return json.load(f)


def cleanup_old_captures(capture_dir: str, days_to_keep: int = 7):
    """Clean up capture files older than specified days."""
    if not os.path.exists(capture_dir):
        return

    cutoff_time = time.time() - (days_to_keep * 24 * 3600)

    for filename in os.listdir(capture_dir):
        filepath = os.path.join(capture_dir, filename)
        if os.path.isfile(filepath) and filename.startswith("capture_"):
            if os.path.getmtime(filepath) < cutoff_time:
                os.remove(filepath)
