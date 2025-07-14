"""
Simplified mock service provider implementation.
Avoids dependency issues while providing the same interface.
"""

from typing import Any, Dict, List
from .service_provider import TestServiceProvider


class SimpleMockDocument:
    """Mock Firestore document."""
    
    def __init__(self, data=None):
        self._data = data or {}
        self.exists = data is not None
    
    def set(self, data):
        self._data = data
        self.exists = True
    
    def get(self):
        return self
    
    def to_dict(self):
        return self._data
    
    @property
    def reference(self):
        return self


class SimpleMockCollection:
    """Mock Firestore collection."""
    
    def __init__(self, name):
        self.name = name
        self._documents = {}
    
    def document(self, doc_id):
        if doc_id not in self._documents:
            self._documents[doc_id] = SimpleMockDocument()
        return self._documents[doc_id]
    
    def stream(self):
        return list(self._documents.values())


class SimpleMockFirestore:
    """Simplified mock Firestore for testing the framework."""
    
    def __init__(self):
        self.data = {}
        self.operation_count = 0
        self._collections = {}
    
    def reset(self):
        self.data.clear()
        self.operation_count = 0
        self._collections.clear()
    
    def collection(self, collection_name):
        if collection_name not in self._collections:
            self._collections[collection_name] = SimpleMockCollection(collection_name)
        return self._collections[collection_name]
    
    def get_campaigns_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        self.operation_count += 1
        return []


class SimpleMockGemini:
    """Simplified mock Gemini for testing the framework."""
    
    def __init__(self):
        self.call_count = 0
    
    def generate_content(self, prompt_parts, model: str = None):
        self.call_count += 1
        return type('Response', (), {'text': 'Mock response'})()
    
    def reset(self):
        self.call_count = 0


class SimpleMockAuth:
    """Simplified mock auth service."""
    
    def __init__(self):
        self.call_count = 0
    
    def verify_id_token(self, token):
        self.call_count += 1
        return {'uid': 'test-user-123'}
    
    def reset(self):
        self.call_count = 0


class SimpleMockServiceProvider(TestServiceProvider):
    """Simplified provider that uses basic mocks without complex dependencies."""
    
    def __init__(self):
        self._firestore = SimpleMockFirestore()
        self._gemini = SimpleMockGemini()
        self._auth = SimpleMockAuth()
    
    def get_firestore(self) -> SimpleMockFirestore:
        """Return simplified mock Firestore client."""
        return self._firestore
    
    def get_gemini(self) -> SimpleMockGemini:
        """Return simplified mock Gemini client."""
        return self._gemini
    
    def get_auth(self) -> SimpleMockAuth:
        """Return mock auth service."""
        return self._auth
    
    def cleanup(self) -> None:
        """Clean up mock services (reset to initial state)."""
        self._firestore.reset()
        self._gemini.reset()
        self._auth.reset()
    
    @property
    def is_real_service(self) -> bool:
        """Return False since using mock services."""
        return False