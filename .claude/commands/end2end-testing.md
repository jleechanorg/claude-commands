---
description: /end2end-testing - Show end-to-end testing principles and patterns
type: documentation
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**

1. Display the core E2E philosophy (Mock only external APIs, NOT internal service functions).
2. Display the mandatory E2E coverage checklist.
3. Review the complete rules/guide at `.claude/skills/end2end-testing.md`.

## 📋 REFERENCE DOCUMENTATION

# /end2end-testing - End-to-End (E2E) Testing Guide

**Purpose**: Quickly lookup E2E testing principles, fake implementations, and test patterns.

See the full authoritative skill at: `.claude/skills/end2end-testing.md`

## E2E Philosophy
- **Key Principle**: Mock only **external APIs**, NOT internal service functions.
- **Why Fake Instead of Mock?**: Using `Mock()` or `MagicMock()` causes JSON serialization errors when mocked data flows through the application. Use fake implementations (`fake_firestore.py`, `fake_llm.py`) that return real Python data structures.

## Quick Directory & Code Map
- **Primary E2E Directory**: `$PROJECT_ROOT/tests/test_end2end/`
- **Shared Base Class**: `$PROJECT_ROOT/tests/test_end2end/__init__.py` -> `End2EndBaseTestCase`
- **Fake Firestore**: `$PROJECT_ROOT/tests/fake_firestore.py` -> `FakeFirestoreClient`
- **Fake LLM (shallow/legacy)**: `$PROJECT_ROOT/tests/fake_llm.py` -> `FakeLLMResponse`
- **Fake LLM (SDK-faithful)**: `$PROJECT_ROOT/tests/fake_llm_realistic.py` -> `RealisticFakeLLMResponse`, `make_realistic_fake()`
  - Use for tests that read `usage_metadata.prompt_token_count`, `finish_reason`, or iterate `candidates[0].content.parts` (code_execution path)
  - `make_realistic_fake(with_dice=True)` adds stub `executable_code` / `code_execution_result` parts
  - Fixture `FIXTURE_STORY_RESPONSE_TEXT` sourced from a real prod Gemini 3 Flash response

## Mandatory E2E Coverage Rules
When a PR creates or updates multiple non-test files under `$PROJECT_ROOT/**`, it must add or update at least one end-to-end test unless the PR explicitly justifies why the changed code is unreachable through an end-to-end application path.

The E2E test must:
1. Exercise every newly introduced or modified production code path in the PR.
2. Drive the application through the real in-process route/service flow instead of calling each helper directly.
3. Assert the observable response, persisted state, emitted structured fields, or other user/server-visible effect from each changed path.
4. Fail if any changed path is skipped, bypassed, or only imported.
5. Remain deterministic with fake external APIs for Layer 2; add MCP/Browser `/es` evidence separately when real services or UI behavior must be proven.
