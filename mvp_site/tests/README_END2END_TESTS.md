# End-to-End Integration Tests

## Overview

These tests validate the complete flow through all application layers while only mocking external API boundaries (Firestore and Gemini API).

## Testing Philosophy

**Key Principle**: Mock only external APIs, not internal service calls.

- ✅ Mock: `firebase_admin.firestore.client()`, `google.genai.Client()`
- ❌ Don't Mock: `firestore_service.py`, `llm_service.py`, `main.py` functions

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

### Fake Implementations
**fake_firestore.py** - Reusable fake implementations
- `FakeFirestoreClient` - Mimics Firestore client behavior
- `FakeFirestoreDocument` - Returns real dictionaries
- `FakeFirestoreCollection` - Handles nested collections
- `FakeLLMResponse` - Simple response with text attribute

### End-to-End Tests (test_end2end/)
| Test File | Purpose |
|-----------|---------|
| `run_end2end_tests.py` | Test runner for all E2E tests |
| `test_continue_story_end2end.py` | Story continuation with LLM responses |
| `test_create_campaign_end2end.py` | Full campaign creation flow |
| `test_debug_mode_end2end.py` | Debug mode UI and logging |
| `test_embedded_json_narrative_end2end.py` | JSON data embedded in narratives |
| `test_entity_tracking_budget_end2end.py` | Entity tracking with token budgets |
| `test_god_mode_end2end.py` | DM/God mode features |
| `test_llm_provider_end2end.py` | LLM provider switching |
| `test_mcp_error_handling_end2end.py` | MCP error handling scenarios |
| `test_mcp_integration_comprehensive.py` | Full MCP server integration |
| `test_mcp_protocol_end2end.py` | MCP JSON-RPC protocol compliance |
| `test_npc_death_state_end2end.py` | NPC death state persistence |
| `test_timeline_log_budget_end2end.py` | Timeline logging with budgets |
| `test_visit_campaign_end2end.py` | Loading existing campaigns |

## Running the Tests

```bash
# Run all E2E tests (from project root)
TESTING=true python3 mvp_site/tests/test_end2end/run_end2end_tests.py

# Run a specific E2E test
TESTING=true python3 -m pytest mvp_site/tests/test_end2end/test_create_campaign_end2end.py -v

# Use slash commands
/teste                    # Mock mode - fast
/tester                   # Real mode - full integration
/testerc                  # Real mode with capture
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
