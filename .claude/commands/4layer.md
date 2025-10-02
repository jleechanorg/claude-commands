---
description: /4layer - Four-Layer TDD Testing Protocol
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Workflow

**Action Steps:**
1. **Planning Phase** (`/think`):
   - Identify all affected components
   - Design test scenarios for each layer
   - Plan data flow and expected behaviors
   - Consider edge cases and error scenarios

2. **Execution Phase** (`/e`):
   - Write failing tests for Layer 1
   - Implement minimal code to pass Layer 1
   - Progress through Layers 2-4
   - Refactor as needed

## 📋 REFERENCE DOCUMENTATION

# /4layer - Four-Layer TDD Testing Protocol

## Purpose

Implements comprehensive Test-Driven Development across 4 testing layers to ensure complete coverage from unit to end-to-end testing.

## Usage

```
/4layer [feature_name]
```

## Testing Layers (in order)

### Layer 1: Unit Tests

- Test each affected module in isolation
- Mock all dependencies
- Focus on individual function/method behavior
- Files typically affected:
  - `test_main_[feature].py`
  - `test_gemini_service_[feature].py`
  - `test_firestore_service_[feature].py`
  - `test_frontend_[feature].js`

### Layer 2: Python Integration Tests

- Test complete backend flow
- Mock ONLY external services (Firestore, Gemini API)
- Verify data flow through all Python modules
- File: `test_integration/test_[feature]_integration.py`

### Layer 3: Browser Tests (Mocked Services)

- Full UI testing with Playwright
- Mock Firestore and Gemini API
- Capture screenshots of UI behavior
- Verify frontend-backend integration
- File: `testing_ui/test_[feature]_browser_mock.py`

### Layer 4: Browser Tests (Real Services)

- Complete end-to-end testing
- Use real Firebase and Gemini API
- Capture screenshots of actual behavior
- Validate entire system integration
- File: `testing_ui/test_[feature]_browser_real.py`

## Example Structure

```python

# Layer 1: test_main_structured_fields.py

def test_response_includes_structured_fields():
    """Unit test: main.py returns structured fields in response"""
    # Mock all dependencies
    # Test specific function behavior

# Layer 2: test_structured_fields_integration.py

def test_structured_fields_flow():
    """Integration: Full backend flow with mocked APIs"""
    # Mock only Firestore and Gemini
    # Test complete data flow

# Layer 3: test_structured_fields_browser_mock.py

def test_structured_fields_display():
    """Browser: UI displays fields correctly (mocked)"""
    # Use Playwright with mocked backend
    # Capture screenshots

# Layer 4: test_structured_fields_browser_real.py

def test_structured_fields_e2e():
    """E2E: Complete system with real APIs"""
    # No mocks - real Firebase/Gemini
    # Final validation screenshots
```

## Benefits

- Catches issues at appropriate levels
- Progressive confidence building
- Clear separation of concerns
- Complete coverage from unit to E2E
- TDD compliance at every layer

## Command Integration

When `/4layer` is invoked:
1. Automatically triggers `/think` for planning
2. Uses `/tdd` principles for implementation
3. Executes via `/e` with structured milestones
4. Provides clear progress tracking
