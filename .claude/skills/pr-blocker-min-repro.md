---
description: "PR blocker minimal repro ladder for fast, evidence-based triage"
type: "workflow"
scope: "github"
---

## Overview

The Four-Layer Minimal Repro Protocol provides a systematic escalation ladder for reproducing PR-blocking issues efficiently. Starting with the fastest unit tests and climbing through end2end, MCP API, and browser tests, this protocol ensures you identify the exact failure layer without wasting time on unnecessarily slow test runs. Use this when you need concrete evidence to triage blocker beads and make informed decisions about PR status.

## Goal
Reproduce PR-blocking beads with the fastest reliable ladder:
1) `unit` -> 2) `end2end` -> 3) `testing_mcp` (real local server) -> 4) `testing_ui` browser.

Use this when a PR has unresolved blocker beads and you need evidence-backed status updates quickly.

## Rules
- Run from repo root.
- Keep provider/user isolation - Ensure test data and state are isolated per test run so parallel executions don't interfere.
- Stop climbing the ladder only when the blocker is conclusively reproduced.
- If lower layers pass but browser fails, classify as `ui` (browser-only).
- Always attach concrete evidence paths and log lines to bead notes.

## Quick Start

### 1) Unit
```bash
./vpython -m pytest \
  $PROJECT_ROOT/tests/test_settings_api.py::TestSettingsAPI::test_update_settings_allows_openrouter_provider \
  $PROJECT_ROOT/tests/test_settings_api.py::TestSettingsAPI::test_update_settings_allows_cerebras_provider -q
```

### 2) End-to-End
```bash
./vpython -m pytest \
  $PROJECT_ROOT/tests/test_end2end/test_faction_settings_end2end.py::TestFactionSettingsEndToEnd::test_pre_spicy_provider_roundtrip \
  $PROJECT_ROOT/tests/test_end2end/test_llm_provider_end2end.py::TestLLMProviderSettingsEndToEnd::test_round_trips_openrouter_and_gemini_preferences -q
```

### 3) MCP / HTTP Local Server
```bash
./vpython testing_mcp/faction/test_faction_settings_real.py
```

### 4) Browser (Final Escalation)
```bash
BYOK_CASES=1,2 \
BYOK_PARALLEL=true \
BYOK_PROVIDERS=gemini,openrouter,cerebras \
BYOK_TEST_PORT=8088 \
./vpython testing_ui/test_llm_settings_browser.py
```

## Evidence Review Checklist
- Confirm each worker reports `TEST PASSED` or explicit failure.
- Grep worker logs for blocker signatures:
```bash
rg -n "status: 400|Failed to create campaign|non-stream|invalid-key validation message|did not update state|Traceback" \
  /tmp/your-project.com/browser/byok-parallel-*/**/worker.log
```
- Verify screenshot + log consistency (no false screenshot claims).
- Record exact evidence directory and critical lines per bead.

## Advanced Patterns

### Escalation Tips
- If a layer passes but the bug seems environmental, skip to browser tests to verify the full stack
- When multiple providers are involved, isolate failures by testing one provider at a time
- Use specific test cases rather than full suites to reduce noise and focus on the blocker

### Parallel Run Isolation
- Each test run should use unique provider/user/test-port combinations
- Verify evidence directories don't collide: `/tmp/your-project.com/[branch]/[test-run-id]/`
- Check worker logs individually to avoid confusion from concurrent execution

### Evidence Gathering Heuristics
- Always capture the first failure signature - subsequent errors may be cascading effects
- Screenshot timestamps should align with log timestamps (±5 seconds)
- If evidence looks suspicious (e.g., "TEST PASSED" but screenshots show errors), re-run with verbose logging
- Preserve full evidence bundles for at least 24 hours after closing blocker beads

## Bead Update Template
Use this pattern in bead notes:
- `Repro ladder results:` unit=`pass|fail`, end2end=`pass|fail`, mcp=`pass|fail`, browser=`pass|fail`.
- `Classification:` backend, mcp, ui, or external-provider.
- `Evidence:` absolute path(s) + key log line(s).
- `Decision:` keep open, close, or downgrade priority.
