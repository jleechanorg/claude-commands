"""
Fake Firestore implementation for testing.
Returns real data structures instead of Mock objects to avoid JSON serialization issues.
"""

import datetime


class FakeFirestoreDocument:
    """Fake Firestore document that behaves like the real thing."""

    def __init__(self, doc_id=None, data=None, parent_path=""):
        self.id = doc_id or "test-doc-id"
        self._data = data or {}
        self._parent_path = parent_path
        self._collections = {}

    def set(self, data):
        """Simulate setting document data."""
        self._data = data

    def update(self, data):
        """Simulate updating document data with nested field support."""
        for key, value in data.items():
            if "." in key:
                # Handle nested field updates like 'settings.gemini_model'
                parts = key.split(".")
                current = self._data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                # Handle regular field updates
                self._data[key] = value

    def get(self):
        """Simulate getting the document."""
        return self

    def exists(self):
        """Document exists after being set."""
        return bool(self._data)

    def to_dict(self):
        """Return the document data."""
        return self._data

    def collection(self, name):
        """Get a subcollection."""
        path = (
            f"{self._parent_path}/{self.id}/{name}"
            if self._parent_path
            else f"{self.id}/{name}"
        )
        if name not in self._collections:
            self._collections[name] = FakeFirestoreCollection(name, parent_path=path)
        return self._collections[name]


class FakeFirestoreCollection:
    """Fake Firestore collection that behaves like the real thing."""

    def __init__(self, name, parent_path=""):
        self.name = name
        self._parent_path = parent_path
        self._docs = {}
        self._doc_counter = 0

    def document(self, doc_id=None):
        """Get or create a document reference."""
        if doc_id is None:
            # Generate a new ID
            self._doc_counter += 1
            doc_id = f"generated-id-{self._doc_counter}"

        if doc_id not in self._docs:
            path = (
                f"{self._parent_path}/{self.name}" if self._parent_path else self.name
            )
            self._docs[doc_id] = FakeFirestoreDocument(doc_id, parent_path=path)

        return self._docs[doc_id]

    def stream(self):
        """Stream all documents."""
        return list(self._docs.values())

    def add(self, data):
        """Add a new document with auto-generated ID."""
        doc = self.document()  # This creates a doc with auto-generated ID
        doc.set(data)
        # Return tuple like real Firestore: (timestamp, doc_ref)
        fake_timestamp = datetime.datetime.now(datetime.UTC)
        return (fake_timestamp, doc)

    def order_by(self, field, direction=None):
        """Mock order_by for queries."""
        # Return self to allow chaining
        return self


class FakeFirestoreClient:
    """Fake Firestore client that behaves like the real thing."""

    def __init__(self):
        self._collections = {}

    def collection(self, path):
        """Get a collection."""
        if path not in self._collections:
            self._collections[path] = FakeFirestoreCollection(path, parent_path="")
        return self._collections[path]

    def document(self, path):
        """Get a document by path."""
        parts = path.split("/")
        if len(parts) == 2:
            collection_name, doc_id = parts
            return self.collection(collection_name).document(doc_id)
        if len(parts) == 4:
            # Nested collection like campaigns/id/story
            parent_collection, parent_id, sub_collection, doc_id = parts
            parent_doc = self.collection(parent_collection).document(parent_id)
            return parent_doc.collection(sub_collection).document(doc_id)
        # More complex paths - just return a fake document
        doc_id = parts[-1] if parts else "unknown"
        return FakeFirestoreDocument(doc_id)


class FakeLLMResponse:
    """Fake LLM response that behaves like the real thing."""

    def __init__(self, text):
        self.text = text
        self.narrative_text = text
        # Parse JSON if it looks like JSON for state updates
        import json

        try:
            data = json.loads(text)
            # Create a mock structured response for get_state_updates()
            self._state_updates = data.get("state_changes", {})
            self._entities_mentioned = data.get("entities_mentioned", [])
            self._location_confirmed = data.get("location_confirmed")
        except (json.JSONDecodeError, TypeError):
            self._state_updates = {}
            self._entities_mentioned = []
            self._location_confirmed = None

    def get_state_updates(self):
        """Return state updates from the fake response."""
        return self._state_updates

    @property
    def structured_response(self):
        """Mock structured response object."""

        class MockStructuredResponse:
            def __init__(self, state_updates, entities_mentioned, location_confirmed):
                self.state_updates = state_updates
                self.entities_mentioned = entities_mentioned
                self.location_confirmed = location_confirmed

        return MockStructuredResponse(
            self._state_updates, self._entities_mentioned, self._location_confirmed
        )


class FakeTokenCount:
    """Fake token count response."""

    def __init__(self, count=1000):
        self.total_tokens = count
