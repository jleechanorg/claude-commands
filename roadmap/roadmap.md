# WorldArchitect.AI Development Roadmap

## Active Development Tasks

### 🎯 HANDOFF-LLM_GUARDRAILS_VALIDATION (Priority: HIGH) 🟡
**Status**: 🟡 IN PROGRESS - 84.4% pass rate (5 Qwen failures remaining)
**Handoff Document**: `roadmap/scratchpad_handoff_llm_guardrails_validation.md`
**Branch**: `claude/test-and-fix-system-prompt-RiZyM`
**PR Reference**: #2902 https://github.com/jleechanorg/worldarchitect.ai/pull/2902

**Objective**: Prevent LLM exploit attempts (item spawning, god-mode actions, stat manipulation, narrative hijacking, anachronistic items) in WorldArchitect.AI D&D game.

**Current Result**: 27/32 pass (84.4%) - **Gemini: 16/16 (100%)**, **Qwen: 11/16 (68.8%)**

**Implementation**: Added "The Tabletop DM Test" universal guardrail principle to system prompt + fixed validation logic (context window 160→400 chars, added implicit rejection phrases).

**Remaining Work**: Fix 5 Qwen failures (2 stat manipulation, 3 anachronistic items)

**Evidence**: Run `python testing_mcp/test_llm_guardrails_exploits.py --evidence` (see `roadmap/scratchpad_handoff_llm_guardrails_validation.md` for setup).

### 🚨 HANDOFF-DELETE-TESTING-MODE (Priority: HIGH) 🟢
**Status**: READY FOR HANDOFF
**Handoff Document**: `roadmap/scratchpad_handoff_delete_testing_mode.md`
**Branch**: `delete-testing-mode`
**PR Reference**: #1536

**Objective**: Remove dual-mode authentication system that causes configuration confusion, debugging complexity, and maintenance burden.

**Problem**: Testing mode creates two parallel authentication paths (frontend test bypass + backend header bypass) leading to configuration mismatches and poor debugging practices.

**Implementation**: 4-phase approach (14-20 hours) - Backend Firebase Admin SDK, Frontend testing removal, Test infrastructure updates, Environment configuration.

**Success Criteria**: Single authentication path using real Firebase in all environments, elimination of configuration confusion.

### 🔍 Debug External Memory Backup System (Priority: HIGH)
**Status**: Ready for Implementation
**Classification**: Small & LLM Autonomous
**Branch**: `debug-memory-backup-system`

**Objective**: Investigate and fix failing health checks in external memory backup system (`/Users/jleechan/projects/worldarchitect-memory-backups/`) that shows 4/5 checks failing every 30 minutes.

**Issues Identified**:
- ⚠️ Cannot connect to remote repository (WARNING level)
- ⚠️ Failed to fetch latest from remote (WARNING level)
- ⚠️ No historical snapshots found (WARNING level)
- Note: Critical infrastructure issues (missing repo, uninitialized git, missing directories) already resolved

**Requirements**: Debug remaining connection and data sync issues in external memory backup system. Focus on remote repository connectivity and historical snapshot population. System runs health checks every 30 minutes via cron. This is separate from the successfully implemented ~/.claude conversation backup system.

**Success Criteria**: Reduce failing health checks from current 4/5 to 1/5 or better, focusing on remote connectivity and snapshot availability.

### 🚨 HANDOFF-COPILOT-SKIP-FIX (Priority: CRITICAL)
**Status**: Ready for Implementation
**Handoff Document**: `roadmap/scratchpad_handoff_copilot_skip_fix.md`
**Branch**: `handoff-copilot-skip-fix`
**PR Reference**: #1301, #1302

**Critical Bug**: Copilot incorrectly reports "zero comments" when 30+ inline review comments exist, causing complete skipping of comment processing workflow.

**Root Cause**: Skip detection logic only checks general PR comments (`gh pr view --json comments`) and reviews (`gh pr view --json reviews`) but completely ignores inline review comments (`gh api repos/owner/repo/pulls/PR/comments`).

**Impact**: Major workflow failures where copilot claims "no work needed" despite significant review feedback requiring responses.

**Evidence**:
- PR #1294: Copilot skipped processing despite 30 review comments
- Root cause: Only checks general comments, misses inline review comments
- Impact: Critical code review feedback ignored

**Implementation**:
- Fix comment detection to check all three sources
- Remove optimization that skips steps
- Add mandatory gates with visual feedback
- Timeline: 50 minutes

### 🔧 CommentReply Threading Enhancement (Priority: HIGH)
**Status**: Ready for Implementation
**Handoff Document**: `roadmap/handoff_commentreply_threading_v2.md`
**Branch**: `handoff-commentreply-threading-v2`

**Objective**: Fix critical implementation gap where `/commentreply` claims fixes but doesn't edit files

**Key Issues**:
- Current system only prints messages, no actual file modifications
- Missing threaded reply format enforcement
- No verification mechanisms for claimed fixes
- All PR comment responses are essentially fake implementations

**Implementation Strategy**:
- LLM-native enhancement of existing `.claude/commands/commentreply.md`
- Mandatory file editing protocol with verification
- Enhanced threaded reply format requirements
- Real-time validation of comment responses

**Success Criteria**:
- Every comment response includes actual file changes
- All responses use proper GitHub threading format
- Each fix includes commit hash verification
- Original issues are actually resolved

---

## Completed Tasks

### ✅ JSON Input Architecture Migration
**Status**: Completed (PR #1114)
**Branch**: `json_input`

Major architectural change from string-based to structured JSON requests for Gemini API integration.

---

## Backlog

### Testing Infrastructure
- End-to-end test coverage expansion
- Mock service architecture improvements
- Performance testing framework

### User Experience
- Campaign creation workflow optimization
- Story continuation enhancements
- Memory system improvements

### Architecture
- MCP integration enhancements
- Service layer optimizations
- Database performance improvements

---

*Last Updated: 2026-01-09*
