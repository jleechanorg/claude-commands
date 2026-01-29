# Testing Infrastructure

**Purpose**: Centralized testing utilities, debug protocols, and CI/local parity guidelines.

## Test Utilities (MANDATORY)

**Always use `testing_mcp/lib/` utilities - NEVER reimplement test infrastructure.**

### Available Shared Utilities

| Module | Functions |
|--------|-----------|
| `lib/evidence_utils.py` | `get_evidence_dir()`, `capture_provenance()`, `save_evidence()`, `write_with_checksum()`, `create_evidence_bundle()`, `save_request_responses()` |
| `lib/mcp_client.py` | `MCPClient(base_url, timeout)`, `client.tools_call(tool_name, args)` |
| `lib/campaign_utils.py` | `create_campaign()`, `process_action()`, `get_campaign_state()`, `ensure_game_state_seed()` |
| `lib/server_utils.py` | `start_local_mcp_server()`, `pick_free_port()`, `DEFAULT_EVIDENCE_ENV` |
| `lib/model_utils.py` | `settings_for_model()`, `update_user_settings()` |
| `lib/narrative_validation.py` | `validate_narrative_quality()`, `extract_dice_notation()` |

### Required Pattern
```python
# Import from lib modules
from testing_mcp.lib.evidence_utils import get_evidence_dir, capture_provenance
from testing_mcp.lib.mcp_client import MCPClient
from testing_mcp.lib.campaign_utils import create_campaign, process_action

# NEVER reimplement these functions
```

### Anti-Pattern
Writing custom `capture_provenance()`, `get_evidence_dir()`, `save_evidence()`, or any function that duplicates `testing_mcp/lib/` functionality.

## CI/Local Parity

Mock external dependencies to ensure tests pass in both CI and local environments:

```python
with patch('shutil.which', return_value='/usr/bin/command'):
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # test code here
```

**Rules:**
- Mock `shutil.which()`, `subprocess.run()`, file ops
- Never rely on system state in tests
- Test files (`$PROJECT_ROOT/tests/*`) may use direct logging

## Debug Protocol

### Test Failure Debugging
- Embed debug info in assertions, not print statements
- Debugging order: Environment -> Function -> Logic -> Assertions
- Test most basic assumption first: "Does the function actually work?"

```python
# CORRECT - Debug info in assertion
debug_info = f"function_result={result}, context={context}"
self.assertTrue(result, f"FAIL DEBUG: {debug_info}")

# WRONG - Print statements (lost in CI)
print(f"Debug: {result}")
```

## Testing Protocol

**ZERO TOLERANCE:** Fix ALL test failures in CI

**LOCAL TESTING:** Don't run full test suite locally - rely on GitHub CI
- Run only SPECIFIC tests: `TESTING=true python $PROJECT_ROOT/tests/test_<specific>.py`
- GitHub CI is the authoritative source for test results

## MCP Smoke Tests

```bash
MCP_SERVER_URL="https://..." MCP_TEST_MODE=real node scripts/mcp-smoke-tests.mjs
```
- Hard-fails on any non-200 response
- Results saved to `/tmp/repo/branch/smoke_tests/`

## Related Skills
- `evidence-standards.md` - Evidence capture standards
- `end2end-testing.md` - E2E test patterns
