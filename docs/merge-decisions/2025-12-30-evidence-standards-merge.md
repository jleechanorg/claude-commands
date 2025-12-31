# Merge Decision: Evidence Standards Conflict Resolution

**Date:** 2025-12-30
**Branch:** `claude/fix-alexiel-campaign-x6tpx`
**Merge From:** `origin/main` (commit `b8eba0c8e`)
**Merge Into:** PR #2561 (Campaign Integrity fixes)

## Context

While working on campaign balance test improvements, `origin/main` was updated with evidence standards enhancements. This required a merge with conflict resolution.

## Conflicts Resolved

### 1. `.claude/commands/generatetest.md`

**Location:** Evidence Standards Checklist section (lines 277-290)

**Ours (kept):**
- Log checksums requirement: any `*.log` evidence file has matching `.sha256`
- LLM/API claims: `request_responses.jsonl` + `.sha256` present when behavior is asserted
- Post-setup validation: confirm `GOD_MODE_UPDATE_STATE` did not auto-correct state

**Main (added):**
- Raw capture: use `DEFAULT_EVIDENCE_ENV` from `server_utils.py`
- JSONL file: create `request_responses.jsonl` with full request/response pairs
- Server logs: copy to `artifacts/server.log` with checksum
- Evidence mode: document capture approach with `evidence_mode` field

**Resolution:** Combined both - all items are complementary and strengthen evidence standards.

### 2. `.claude/skills/evidence-standards.md`

**Location:** Checksum requirements section (lines 115-131)

**Ours (kept):**
- Log checksum requirement with explicit file examples (`local_mcp_*.log`, server logs, browser logs)

**Main (added):**
- Expanded file list (PASS_*.json, FAIL_*.json, request_responses.jsonl)
- Python helper function `_write_checksum_for_file()`

**Resolution:** Combined both - kept our explicit log requirement and added main's expanded list and helper function.

## Rationale

Both branches were improving evidence standards independently:
- Our branch focused on campaign balance testing with log checksums
- Main branch added general evidence capture improvements

The changes are additive - combining them creates a more comprehensive evidence standard.

## Verification

```bash
# Verify no remaining conflict markers
git grep -l '<<<<<<<' || echo "No conflicts remaining"

# Verify merge commit
git log -1 --oneline
```

## Impact

- Evidence standards now require checksums for all file types
- `generatetest.md` has comprehensive checklist covering both approaches
- No functionality was lost from either branch
