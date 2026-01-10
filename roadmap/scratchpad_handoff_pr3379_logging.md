# Project Goal
Implement unified/structured logging improvements for `.claude/commands/savetmp.py` `_resolve_repo_info()` per HANDOFF-PR3379-LOGGING.

## Branch Info
- Branch: handoff-pr3379-logging
- Task ID: HANDOFF-PR3379-LOGGING
- Created: 2026-01-09

## Current State
- ✅ COMPLETED (100%): stderr print replaced with unified logging
- ✅ COMPLETED (100%): diff attempt debug logs + both-fail warning added
- ✅ COMPLETED (100%): tests updated to verify logging calls instead of stderr
- ✅ COMPLETED (100%): fixed splitlines usage and SHA shortening
- ✅ COMPLETED (100%): fixed misleading warning logic

## Implementation Plan

### Phase 1: Add Unified Logging Import ✅ (COMPLETED)
- Checked `logging_util` import.
- Added fallback for .claude/commands/ context.

### Phase 2: Replace Stderr Print with Logging ✅ (COMPLETED)
- Replaced `print(..., file=sys.stderr)` with `logging_util.warning` in `_resolve_repo_info`, `_read_optional_file`, `_copy_artifact`, and `main`.

### Phase 3: Add Logging for Git Diff Failures ✅ (COMPLETED)
- Added debug logging for 3-dot and 2-dot diff attempts.
- Added warning when both strategies fail.
- Used `splitlines()` for safer output parsing.
- Shortened SHA in debug logs to reduce noise.

### Phase 4: Verification ✅ (COMPLETED)
- Updated unit tests in `.claude/commands/tests/test_savetmp.py`.
- Verified tests pass.

## Next Steps
- Merge PR #3390.

## Key Context
- **Original PR:** #3379 - Fix Git Provenance Bug in savetmp.py
- **CLAUDE.md Unified Logging:** Lines 246-269 (note: unified logging is mandatory for files in `mvp_site/` only; for `.claude/commands/savetmp.py`, using the standard `logging` module is acceptable, and `logging_util` may be used if it is importable)
- **File:** `.claude/commands/savetmp.py` lines 89-170
