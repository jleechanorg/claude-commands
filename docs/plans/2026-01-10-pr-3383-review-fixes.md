# PR #3383 Review Fixes - Actionable Items

**Date**: 2026-01-10  
**PR**: https://github.com/jleechanorg/worldarchitect.ai/pull/3383  
**Reviewer**: CodeRabbit

## Summary of Issues Found

CodeRabbit identified **8 actionable issues** that need to be addressed before merge. Some issues have been partially addressed in follow-up commits, but verification is needed.

## Critical Issues to Fix

### 1. ✅ Evidence Paths Point to Machine-Local Temp Directories

**Location**: 
- `.beads/issues.jsonl` (multiple entries)
- `roadmap/roadmap.md` (line 20)
- `roadmap/scratchpad_handoff_llm_guardrails_validation.md` (lines 49, 64-79, 325-328)

**Problem**: Evidence paths like `/tmp/worldarchitect.ai/claude/test-and-fix-system-prompt-RiZyM/...` are machine-local and prevent others from reproducing.

**Status**: ⚠️ **PARTIALLY ADDRESSED** - Some comments indicate fixes were made, but verification needed.

**Fix Required**:
- Add `how_to_regenerate` or `repro_instructions` field with exact commands
- OR upload artifacts to durable location (S3, CI artifacts) and add `evidence_url` field
- Include: exact test command, repo commit hash, environment variables, dataset/model versions

**Example Fix**:
```json
{
  "evidence_path": "/tmp/worldarchitect.ai/claude/test-and-fix-system-prompt-RiZyM/llm_guardrails_exploits/iteration_001/",
  "how_to_regenerate": "Run: python testing_mcp/test_llm_guardrails_exploits.py --start-local --real-services --evidence. Requires commit abc123def456, branch claude/test-and-fix-system-prompt-RiZyM, WORLDAI_DEV_MODE=true"
}
```

**Verification**: Check that all evidence references in `.beads/issues.jsonl` include regeneration instructions.

### 2. ✅ Roadmap "Last Updated" Date

**Location**: `roadmap/roadmap.md` (line 131)

**Status**: ✅ **ALREADY FIXED** - Shows "2026-01-09" (correct)

**No action needed** - This was already updated.

### 3. ✅ Scratchpad File Structure

**Location**: `roadmap/scratchpad_handoff_llm_guardrails_validation.md`

**Status**: ✅ **ADDRESSED** - CodeRabbit confirmed all required sections are present:
- ✅ Project Goal
- ✅ Implementation Plan (present as "Phases" or similar)
- ✅ Current State
- ✅ Next Steps
- ✅ Key Context (may be embedded in other sections)
- ✅ Branch Info

**Verification**: Confirm all required sections match repo convention exactly.

### 4. ⚠️ Machine-Specific Paths in Handoff Docs

**Location**: `roadmap/scratchpad_handoff_llm_guardrails_validation.md` (lines 94-107, 128-149, 160-193, 225-229)

**Problem**: Uses `/Users/jleechan/...` and `pkill -f` which is risky and not portable.

**Fix Required**: Use repo-relative paths and safer process management:
```bash
# Instead of:
cd /Users/jleechan/projects/worktree_worker3/testing_mcp
pkill -f "mcp_api.*58729"

# Use:
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT/testing_mcp"
PORT="${PORT:-58729}"
python -m mvp_site.mcp_api --http-only --host 127.0.0.1 --port "$PORT" &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT
```

### 5. ⚠️ Missing Test File Reference

**Location**: `docs/plans/2026-01-06-guardrails-validator-fixes.md` (lines 28-31, 71, 112)

**Problem**: References `testing_mcp/test_guardrails_validator_unit.py` which doesn't exist.

**Fix Required**: Either:
- Add task to create the test file, OR
- Update references to point to existing test file (`test_llm_guardrails_exploits.py`)

**Action**: Verify if this test file should exist or if references should be updated.

## Nitpick Comments (Lower Priority)

### 6. Date Fields Missing in Planning Docs

**Location**: `docs/plans/2026-01-06-guardrails-validator-fixes.md` (lines 1-11)

**Fix**: Add date and cross-references:
```markdown
# Guardrails Validator Fixes Implementation Plan

**Date:** 2026-01-06
**Status:** ⬜ NOT STARTED
**Related docs:**
  - [Iteration 001 Findings Analysis](../2026-01-09-guardrails-iteration-001-findings.md)
  - [Guardrails Validation Scratchpad](../../roadmap/scratchpad_handoff_llm_guardrails_validation.md)
```

### 7. File References Should Be Markdown Links

**Location**: `docs/plans/2026-01-09-guardrails-iteration-001-findings.md` (lines 133-141)

**Fix**: Convert plain text paths to markdown links:
```markdown
- Evidence bundle: [iteration_001/evidence.md](path/to/file)
- Summary: [evidence.md](path/to/file)
```

### 8. ✅ Avoid Phrase Matching as Primary Fix

**Location**: `.beads/issues.jsonl` (line 128 - `worktree_worker3-ul3` entry)

**Problem**: Description recommends "model-specific detection phrases" which is rule-based NLP (discouraged).

**Status**: ✅ **ADDRESSED** - CodeRabbit confirmed the narrative was updated to clarify phrase matching is a fallback.

**Verification**: Confirm the description in `.beads/issues.jsonl` for `worktree_worker3-ul3` reflects structured output preference.

**Fix** (if still needed): Reframe toward prompt/schema-first approach:
```diff
- **Root Cause:** Qwen uses different rejection language than Gemini. Need model-specific detection phrases.
+ **Root Cause (hypothesis):** Qwen follows guardrails less reliably / expresses rejection differently.
+ **Approach:** Prefer prompt/schema changes that force explicit rejection signal; use phrase matching only as fallback.
```

### 9. ⚠️ Double-Escaped JSON in Issues File

**Location**: `.beads/issues.jsonl`

**Problem**: New issue entry uses double-escaped characters (`\\n` and `\\"`) instead of proper JSON escapes (`\n` and `\"`). This causes malformed description display.

**Fix Required**: Ensure all JSON strings use single-escaped sequences:
- `\\n` → `\n`
- `\\"` → `\"`

**Verification**: Check all entries in `.beads/issues.jsonl` for proper JSON escaping.

### 10. ⚠️ Missing Schema Fields in Issues File

**Location**: `.beads/issues.jsonl`

**Problem**: New issue entry may be missing required schema fields (`content_hash`, `source_repo`) that are present in existing entries.

**Status**: ⚠️ **NEEDS VERIFICATION** - The file shows entries with these fields, but review comment suggests some may be missing.

**Fix Required**: Ensure all entries include:
- `content_hash`: SHA256 hash of content for deduplication
- `source_repo`: Repository identifier (typically `"."` for local)

**Verification**: Verify all entries in `.beads/issues.jsonl` have consistent schema.

### 11. ⚠️ Narrow Outcome Detection to Avoid False Rejections

**Location**: `mvp_site/prompts/narrative_system_instruction.md` (line 193)

**Problem**: Current guardrails may reject legitimate inputs that reference established outcomes or background facts (e.g., "I loot the goblin I killed earlier" or "the chandelier falls as I duck").

**Fix Required**: Narrow detection patterns to avoid false positives:
- Distinguish between player declaring NEW outcomes vs referencing EXISTING outcomes
- Allow past-tense verbs when they reference established narrative facts
- Focus on outcome declarations that attempt to bypass game mechanics

**Priority**: P2 (Medium) - May cause user frustration but not critical for functionality.

## Priority Order

1. **🚨 CRITICAL**: Fix evidence paths (issue #1) - blocks reproducibility
2. **⚠️ HIGH**: Fix JSON escaping in issues file (issue #9) - data integrity
3. **⚠️ HIGH**: Verify schema fields in issues file (issue #10) - data consistency
4. **⚠️ HIGH**: Fix machine-specific paths (issue #4) - portability issue
5. **📝 MEDIUM**: Fix missing test file reference (issue #5) - broken reference
6. **📝 MEDIUM**: Narrow outcome detection (issue #11) - avoid false rejections
7. **📝 LOW**: Add dates and links (issues #6, #7) - documentation polish
8. **✅ VERIFIED**: Scratchpad structure (issue #3) - already addressed
9. **✅ VERIFIED**: Phrase matching approach (issue #8) - already addressed

## Implementation Plan

### Phase 1: Critical Fixes (Before Merge)

1. **Verify and fix `.beads/issues.jsonl`**:
   - Check all entries for proper JSON escaping (no double-escaped sequences)
   - Verify all entries have `content_hash` and `source_repo` fields
   - Add `how_to_regenerate` field to entries with evidence paths

2. **Update `roadmap/roadmap.md`**:
   - Verify evidence path includes regeneration instructions
   - Ensure reproducible commands are documented

3. **Update `roadmap/scratchpad_handoff_llm_guardrails_validation.md`**:
   - Replace machine-specific paths (`/Users/jleechan/...`) with repo-relative paths
   - Replace `pkill -f` commands with safer process management
   - Verify all required scratchpad sections are present

### Phase 2: Documentation Fixes

4. **Update `docs/plans/2026-01-06-guardrails-validator-fixes.md`**:
   - Add date and cross-references header
   - Fix test file reference (`test_guardrails_validator_unit.py` - either create or update reference)

5. **Update `docs/plans/2026-01-09-guardrails-iteration-001-findings.md`**:
   - Convert file references to markdown links

### Phase 3: Prompt Refinement (Post-Merge Consideration)

6. **Review `mvp_site/prompts/narrative_system_instruction.md`**:
   - Narrow outcome detection patterns to avoid false rejections
   - Distinguish between new outcome declarations vs references to established facts
   - Test with edge cases (e.g., "I loot the goblin I killed earlier")

## Verification Checklist

- [ ] All `.beads/issues.jsonl` entries have proper JSON escaping
- [ ] All `.beads/issues.jsonl` entries have `content_hash` and `source_repo` fields
- [ ] All evidence paths include `how_to_regenerate` instructions
- [ ] No machine-specific paths (`/Users/jleechan/...`) in handoff docs
- [ ] Scratchpad has all required sections (verified by CodeRabbit)
- [ ] Test file references are valid or clearly marked as TODO
- [ ] Planning docs have dates and cross-references
- [ ] File references use markdown links
