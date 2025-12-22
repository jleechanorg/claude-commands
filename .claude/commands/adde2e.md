---
description: /adde2e - Add or Update End2End Tests for New Features
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 📚 REQUIRED SKILL REFERENCE

**MANDATORY**: Before writing any tests, read and apply the end2end testing skill:
- **File**: `.claude/skills/end2end-testing.md`
- **Key Principles**:
  - Mock only external APIs (Firestore, Gemini), NOT internal services
  - Use fake implementations (FakeFirestoreClient, FakeLLMResponse) instead of Mock()
  - Tests go in `mvp_site/tests/test_end2end/`
  - Follow existing test patterns in the directory

## 🚨 EXECUTION WORKFLOW

### Phase 0: Context Analysis

**Action Steps:**
1. **Analyze current conversation context** - What features were just added/modified?
2. **Read user's feature description** from `$ARGUMENTS` if provided
3. **Identify affected API endpoints and service layers**
4. **Determine if this is a NEW test file or UPDATE to existing**

### Phase 1: Discovery - Existing Test Landscape

**Action Steps:**
1. **List existing E2E tests**:
   ```bash
   ls mvp_site/tests/test_end2end/
   ```

2. **Check for related existing tests** - Search for tests covering similar functionality (replace `<FEATURE_KEYWORD>` with the real feature name):
   ```bash
   grep -r "<FEATURE_KEYWORD>" mvp_site/tests/test_end2end/
   ```

3. **Read the end2end testing skill**:
   ```bash
   cat .claude/skills/end2end-testing.md
   ```

4. **Read fake implementations** for reference:
   ```bash
   cat mvp_site/tests/fake_firestore.py
   ```

### Phase 2: Test Planning

**Action Steps:**
1. **Determine test scope**:
   - What API endpoints need testing?
   - What service layers are involved?
   - What external APIs need mocking (Gemini, Firestore)?

2. **Define test cases** based on feature:
   - ✅ Success path (happy path)
   - ❌ Error handling (API failures, validation errors)
   - ⚡ Edge cases (empty data, special characters, limits)

3. **Choose test location**:
   - **New feature** → Create `mvp_site/tests/test_end2end/test_{feature}_end2end.py`
   - **Existing feature enhancement** → Add to existing test file

### Phase 3: Test Implementation

**Action Steps:**
1. **Create test file with standard structure**:
   ```python
   """
   End-to-end integration test for {feature description}.
   Only mocks external services (Gemini API and Firestore DB) at the lowest level.
   Tests the full flow from API endpoint through all service layers.
   """

   from __future__ import annotations

   import json
   import os
   import unittest
   from unittest.mock import patch

   os.environ.setdefault("TESTING", "true")
   os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

   from mvp_site import main
   from mvp_site.tests.fake_firestore import FakeFirestoreClient
   from mvp_site.tests.fake_llm import FakeLLMResponse  # Legacy tests may import from fake_firestore.


   class Test{FeatureName}End2End(unittest.TestCase):
       """Test {feature} through the full application stack."""

       def setUp(self):
           """Set up test client."""
           self.app = main.create_app()
           self.app.config["TESTING"] = True
           self.client = self.app.test_client()

           # Stub Firebase authentication
           self.test_user_id = "test-user-123"
           self._auth_patcher = patch(
               "mvp_site.main.auth.verify_id_token",
               return_value={"uid": self.test_user_id},
           )
           self._auth_patcher.start()
           self.addCleanup(self._auth_patcher.stop)

           self.test_headers = {
               "Content-Type": "application/json",
               "Authorization": "Bearer test-id-token",
           }

       @patch("mvp_site.firestore_service.get_db")
       @patch("mvp_site.llm_service._call_llm_api_with_llm_request")
       def test_{feature}_success(self, mock_llm_request, mock_get_db):
           """Test successful {feature} using fake services."""
           # Set up fake Firestore
           fake_firestore = FakeFirestoreClient()
           mock_get_db.return_value = fake_firestore

           # Mock LLM response
           llm_response_data = {
               "narrative": "...",
               # Add appropriate response structure
           }
           fake_response = FakeLLMResponse(json.dumps(llm_response_data))
           mock_llm_request.return_value = fake_response

           # Make API request
           request_payload = {
               # Example request structure - update fields for {feature}
               "user_id": self.test_user_id,
               "input": {
                   "title": "Test {feature} title",
                   "description": "Test {feature} description",
                   # Add any additional fields required by /api/{endpoint}
               },
           }
           response = self.client.post(
               "/api/{endpoint}",
               data=json.dumps(request_payload),
               content_type="application/json",
               headers=self.test_headers,
           )

           # Verify response
           assert response.status_code == 200
           data = json.loads(response.data)
           # Add assertions


   if __name__ == "__main__":
       unittest.main()
   ```

2. **Follow mock patterns from skill**:
   - Use `@patch("mvp_site.firestore_service.get_db")` for Firestore
   - Prefer `@patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")` for new LLM mocks
   - Use `@patch("mvp_site.llm_service._call_llm_api_with_llm_request")` only when updating legacy tests
   - Use `side_effect` for multi-phase function testing

3. **Add error test cases**:
   - API errors (Gemini failures, Firestore errors)
   - Validation errors (missing fields, invalid data)
   - Authentication failures

### Phase 4: Test Verification

**Action Steps:**
1. **Run the new tests**:
   ```bash
   TESTING=true python3 -m pytest mvp_site/tests/test_end2end/test_{feature}_end2end.py -v
   ```

2. **Verify all tests pass**:
   - If tests fail, debug and fix
   - Check mock setup is correct
   - Verify assertions match expected behavior

3. **Run full E2E suite to ensure no regressions**:
   ```bash
   TESTING=true python3 -m pytest mvp_site/tests/test_end2end/ -v
   ```

## 📋 QUICK REFERENCE

### Existing E2E Test Files

| File | Purpose |
|------|---------|
| `test_create_campaign_end2end.py` | Campaign creation flow |
| `test_continue_story_end2end.py` | Story continuation |
| `test_visit_campaign_end2end.py` | Loading existing campaigns |
| `test_world_loader_e2e.py` | World loader flow |
| `test_debug_mode_end2end.py` | Debug mode features |
| `test_god_mode_end2end.py` | God mode (DM powers) |
| `test_llm_provider_end2end.py` | LLM provider switching |
| `test_mcp_*_end2end.py` | MCP integration tests |
| `test_timeline_log_budget_end2end.py` | Timeline log budget |
| `test_embedded_json_narrative_end2end.py` | Embedded JSON narrative |
| `test_entity_tracking_budget_end2end.py` | Entity tracking |
| `test_npc_death_state_end2end.py` | NPC death persistence |

### Mock Patterns

```python
# Firestore mock
@patch("mvp_site.firestore_service.get_db")
def test_example(self, mock_get_db):
    fake_firestore = FakeFirestoreClient()
    mock_get_db.return_value = fake_firestore

# LLM mock (LEGACY - keep for older tests)
@patch("mvp_site.llm_service._call_llm_api_with_llm_request")
def test_example_legacy_llm(self, mock_llm_request):
    fake_response = FakeLLMResponse(json.dumps({"narrative": "..."}))
    mock_llm_request.return_value = fake_response

# LLM mock (PREFERRED for new tests)
@patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
def test_example_llm(self, mock_generate_content):
    fake_response = FakeLLMResponse(json.dumps({"narrative": "..."}))
    mock_generate_content.return_value = fake_response

# Multi-phase testing with side_effect (works with either pattern)
mock_generate_content.side_effect = [phase1_response, phase2_response]
```

### Running Tests

```bash
# Single test file
TESTING=true python3 -m pytest mvp_site/tests/test_end2end/test_{feature}_end2end.py -v

# All E2E tests
TESTING=true python3 -m pytest mvp_site/tests/test_end2end/ -v

# With coverage
./run_tests.sh
```

## 🚨 ENFORCEMENT RULES

**RULE 1**: Read `.claude/skills/end2end-testing.md` BEFORE writing any tests
**RULE 2**: Mock ONLY external APIs, NEVER internal services
**RULE 3**: Use FakeFirestoreClient/FakeLLMResponse, NOT Mock()
**RULE 4**: All tests MUST pass before completion
**RULE 5**: Follow existing naming convention: `test_{feature}_end2end.py`

## Related Commands

- `/teste` - Run E2E tests (mock mode)
- `/tester` - Run E2E tests (real mode)
- `/tdd` - TDD workflow with matrix testing
- `/4layer` - Four-layer TDD protocol
