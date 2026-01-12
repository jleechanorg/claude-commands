# Pagination Evidence Collection Utilities

**Date**: 2026-01-11  
**Purpose**: One-off test utilities created for pagination evidence collection

## Files

- `populate_db_via_api.py` - Creates test campaigns via API for pagination testing
- `manual_test_pagination.py` - Playwright script for manual browser testing
- `reproduce_pagination_bug.py` - Script to reproduce pagination bug scenario
- `start_server_bg.sh` - Wrapper to start server in background

## Usage

These utilities were used to:
1. Populate test data (63 campaigns for `jleechan@gmail.com`)
2. Manually verify pagination UI behavior
3. Reproduce and test bug scenarios

## Status

Evidence collection complete. These utilities are archived for reference but are not part of the test suite.

## Related Evidence

See `/tmp/pagination_evidence_20260111/` for complete evidence bundle.
