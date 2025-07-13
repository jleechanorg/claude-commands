# End-to-End Integration Tests

## Overview

These tests validate the complete flow through all application layers while only mocking external API boundaries (Firestore and Gemini API).

## Testing Philosophy

**Key Principle**: Mock only external APIs, not internal service calls.

- ✅ Mock: `firebase_admin.firestore.client()`, `google.genai.Client()`
- ❌ Don't Mock: `firestore_service.py`, `gemini_service.py`, `main.py` functions

## Implementation Approach

### The Problem with Mock Objects

Using `Mock()` or `MagicMock()` objects can cause JSON serialization errors when the mocked data flows through the application and gets serialized for API responses.

### The Solution: Fake Implementations

We use fake implementations that return real Python data structures:

```python
# BAD: Returns Mock objects
mock_doc = Mock()
mock_doc.to_dict.return_value = {"name": "test"}

# GOOD: Returns real dictionaries
fake_doc = FakeFirestoreDocument()
fake_doc.set({"name": "test"})
```

## Test Files

1. **fake_firestore.py** - Reusable fake implementations
   - `FakeFirestoreClient` - Mimics Firestore client behavior
   - `FakeFirestoreDocument` - Returns real dictionaries
   - `FakeFirestoreCollection` - Handles nested collections
   - `FakeGeminiResponse` - Simple response with text attribute

2. **test_create_campaign_end2end_fixed.py** - Campaign creation tests
3. **test_continue_story_end2end_fixed.py** - Story continuation tests  
4. **test_visit_campaign_end2end_fixed.py** - Campaign retrieval tests
5. **test_create_campaign_end2end_v2.py** - Alternative implementation example

## Running the Tests

```bash
# From project root
TESTING=true python3 mvp_site/tests/test_create_campaign_end2end_fixed.py

# Or use the test runner
./run_tests.sh mvp_site/tests/test_*_fixed.py
```

## Key Implementation Details

### Firestore Structure
The app uses nested collections:
```
users/
  {user_id}/
    campaigns/
      {campaign_id}
```

### Fake Implementation Features
- Auto-generated document IDs
- Support for subcollections
- Real dictionary storage
- Methods: `set()`, `update()`, `get()`, `to_dict()`, `collection()`, `add()`

### Benefits
1. No JSON serialization errors
2. True end-to-end testing through all layers
3. Validates actual data flow
4. Catches integration issues between services