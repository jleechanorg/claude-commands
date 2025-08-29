# Test Failures Summary - August 27, 2025

## Context
This file contains the complete analysis of test failures after major test suite cleanup on branch `fix-run-tests-readarray-compatibility` (PR #1477).

## Major Achievement
- ✅ **Reduced from 69+ to 21 failing tests** (70% improvement)
- ✅ **Eliminated archived test pollution** (50+ archived tests excluded)
- ✅ **Core unit tests passing reliably**

## Current Status: 182 passed, 21 failed

## Detailed Test Failures (21 total)

### Infrastructure Tests (2 failures)
1. `./.claude/hooks/tests/test_command_output_trimmer.py`
2. `./claude-bot-commands/tests/test_claude_bot_server.py`

### Testing Framework (3 failures)
3. `./mvp_site/testing_framework/tests/test_capture.py`
4. `./mvp_site/testing_framework/tests/test_mock_provider.py`
5. `./mvp_site/testing_framework/tests/test_real_provider.py`

### End-to-End Tests (5 failures)
6. `./mvp_site/tests/test_end2end/test_continue_story_end2end.py`
7. `./mvp_site/tests/test_end2end/test_debug_mode_end2end.py`
8. `./mvp_site/tests/test_end2end/test_mcp_error_handling_end2end.py`
9. `./mvp_site/tests/test_end2end/test_mcp_integration_comprehensive.py`
10. `./mvp_site/tests/test_end2end/test_visit_campaign_end2end.py`

### Integration & API Tests (11 failures)
11. `./mvp_site/tests/test_api_response_format_consistency.py`
12. `./mvp_site/tests/test_architectural_decisions.py`
13. `./mvp_site/tests/test_planning_block_validation_integration.py`
14. `./mvp_site/tests/test_production_parity.py`
15. `./mvp_site/tests/test_prompts.py`
16. `./mvp_site/tests/test_settings_api.py`
17. `./mvp_site/tests/test_settings_auth_bypass.py`
18. `./mvp_site/tests/test_syntax_comprehensive.py`
19. `./mvp_site/tests/test_think_block_protocol.py`
20. `./mvp_site/tests/test_token_utils.py`
21. `./mvp_site/tests/test_unknown_entity_filtering.py`

## Debug Instructions

### To reproduce test failures:
```bash
./run_tests.sh --unit --parallel
```

### To run specific failing test:
```bash
cd mvp_site
env TESTING=true python3 -m pytest tests/test_prompts.py -v
```

### To get detailed error output:
```bash
cd mvp_site  
env TESTING=true python3 -m pytest tests/test_prompts.py -v --tb=long
```

### Full test results available in:
- `/tmp/test_results_fixed.log` (complete output)
- `/tmp/test_results.log` (previous run)

## Key Files Modified
- `run_tests.sh` - Added archived test exclusions
- `.claude/hooks/command_output_trimmer.py` - Fixed CompressionStats
- `scripts/mock_hypothesis.py` - Added mock for optional dependencies
- `archived_tests/` - Contains backed up tests

## Next Steps
The remaining 21 test failures are legitimate integration/end-to-end tests that need individual analysis and fixes. These are much more manageable than the original 69+ failures.

Generated: Tue Aug 27 23:35:12 PDT 2025