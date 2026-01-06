"""
Fake Firestore implementation for testing.
Returns real data structures instead of Mock objects to avoid JSON serialization issues.

IMPORTANT: This implementation makes deep copies of data to simulate real Firestore behavior.
Real Firestore stores data on the server, so in-memory modifications to the original dict
do NOT affect the stored data. This fake must behave the same way.
"""

import copy
import datetime
import json
import operator


class FakeFirestoreDocument:
    """Fake Firestore document that behaves like the real thing."""

    def __init__(self, doc_id=None, data=None, parent_path=""):
        self.id = doc_id or "test-doc-id"
        self._data = data or {}
        self._parent_path = parent_path
        self._collections = {}

    def set(self, data):
        """Simulate setting document data.

        Makes a deep copy to simulate real Firestore behavior where stored data
        is independent of the original dict. This is critical for catching bugs
        where code modifies a dict after persisting it.
        """
        self._data = copy.deepcopy(data)

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


class FakeQuery:
    """Fake Firestore query object."""

    def __init__(self, docs, order_by=None, limit=None, filters=None, start_after=None):
        self._docs = list(docs)
        self._order_by = order_by or []
        self._limit = limit
        self._filters = filters or []
        self._start_after = start_after

    def order_by(self, field, direction=None):
        new_order = list(self._order_by) + [(field, direction)]
        return FakeQuery(
            self._docs,
            order_by=new_order,
            limit=self._limit,
            filters=self._filters,
            start_after=self._start_after,
        )

    def limit(self, count):
        return FakeQuery(
            self._docs,
            order_by=self._order_by,
            limit=count,
            filters=self._filters,
            start_after=self._start_after,
        )

    def where(self, field, op, value):
        filters = self._filters + [(field, op, value)]
        return FakeQuery(
            self._docs,
            order_by=self._order_by,
            limit=self._limit,
            filters=filters,
            start_after=self._start_after,
        )

    def start_after(self, *values):
        return FakeQuery(
            self._docs,
            order_by=self._order_by,
            limit=self._limit,
            filters=self._filters,
            start_after=values,
        )

    def _get_value(self, doc, field):
        data = doc.to_dict()
        if field in data:
            return data[field]
        field_name = str(field)
        if field_name == "__name__" or field_name.endswith("DOCUMENT_ID"):
            return getattr(doc, "id", None)
        return None

    def stream(self):
        """Stream query results."""
        results = list(self._docs)

        # Apply filters
        for field, op, value in self._filters:
            # Handle datetime comparisons properly
            # If value is string and looks like ISO, convert to datetime for comparison if doc value is datetime
            
            # Simple helper for comparisons
            def compare(doc_val, target_val, op_func):
                if doc_val is None: return False
                
                # Type conversion if needed
                d_v = doc_val
                t_v = target_val
                
                if hasattr(d_v, 'timestamp') and isinstance(t_v, str):
                    try:
                        t_v = datetime.datetime.fromisoformat(t_v.replace("Z", "+00:00"))
                    except:
                        pass
                
                try:
                    return op_func(d_v, t_v)
                except:
                    return False

            ops = {
                "<": operator.lt,
                "<=": operator.le,
                ">": operator.gt,
                ">=": operator.ge,
                "==": operator.eq,
                "!=": operator.ne
            }
            
            op_func = ops.get(op)
            if op_func:
                results = [d for d in results if compare(self._get_value(d, field), value, op_func)]

        # Apply sort
        if self._order_by:
            # Assume all directions are the same for simplicity
            direction = self._order_by[0][1]
            reverse = False
            if direction is not None:
                dir_str = str(direction).upper()
                reverse = dir_str.endswith("DESCENDING")

            def get_key(d):
                key_parts = []
                for field, _ in self._order_by:
                    val = self._get_value(d, field)
                    if val is None:
                        val = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
                    key_parts.append(val)
                return tuple(key_parts)

            try:
                results.sort(key=get_key, reverse=reverse)
            except Exception:
                pass  # Best effort

        # Apply start_after cursor
        if self._start_after and self._order_by:
            cursor = []
            for v in self._start_after:
                if hasattr(v, "id"):
                    cursor.append(getattr(v, "id"))
                else:
                    cursor.append(v)

            def cmp(a, b):
                if isinstance(a, datetime.datetime) and isinstance(b, datetime.datetime):
                    return (a > b) - (a < b)
                return (str(a) > str(b)) - (str(a) < str(b))

            def is_after(key_vals, cursor_vals, reverse_flag):
                for a, b in zip(key_vals, cursor_vals):
                    comparison = cmp(a, b)
                    if comparison == 0:
                        continue
                    return comparison < 0 if reverse_flag else comparison > 0
                return False

            filtered = []
            for doc in results:
                key = []
                for field, _ in self._order_by:
                    key_val = self._get_value(doc, field)
                    if hasattr(key_val, "id"):
                        key_val = key_val.id
                    key.append(key_val)
                if is_after(key, cursor, reverse):
                    filtered.append(doc)
            results = filtered

        # Apply limit
        if self._limit is not None:
            results = results[: self._limit]

        return results


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
        return FakeQuery(self._docs.values(), order_by=[(field, direction)])

    def limit(self, count):
        """Mock limit for queries."""
        return FakeQuery(self._docs.values(), limit=count)

    def where(self, field, op, value):
        """Mock where for queries."""
        return FakeQuery(self._docs.values(), filters=[(field, op, value)])


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
