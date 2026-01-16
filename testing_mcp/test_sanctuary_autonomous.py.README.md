# Autonomous Sanctuary Mode Tests

## Overview

This test suite validates that Sanctuary Mode works **autonomously** - meaning the LLM recognizes quest completion without explicit "quest complete" language.

## Test Scenarios

### 1. Autonomous Activation (Statistical)
- **Runs:** 10 iterations (configurable via `--quick` flag for 3 runs)
- **Success Rate Required:** 70%+
- **What it tests:** LLM autonomously activates sanctuary after boss defeat
- **Key difference:** Player says neutral action ("I search Klarg's body") with NO completion keywords
- **Evidence:** Logs `trigger_source` to prove autonomous detection

### 2. Natural Expiration (Deterministic)
- **What it tests:** Sanctuary expires at `expires_turn` without intervention
- **Method:** Activate sanctuary, advance turns past expiration, verify `active: false`

### 3. Overwrite Protection (Deterministic)
- **What it tests:** Epic sanctuary (20 turns) isn't overwritten by Medium completion (5 turns)
- **Method:** Complete Epic arc → advance to turn 15 → complete Medium quest → verify Epic preserved

### 4. Duration Scales (Parameterized)
- **What it tests:** All 4 scales produce correct durations
- **Scales:** minor=3, medium=5, major=10, epic=20 turns

## Usage

### Full Test Suite (10 autonomous runs)
```bash
python3 testing_mcp/test_sanctuary_autonomous.py --work-name sanctuary_autonomous
```

### Quick Test (3 autonomous runs)
```bash
python3 testing_mcp/test_sanctuary_autonomous.py --work-name sanctuary_autonomous --quick
```

### Use Existing Server
```bash
python3 testing_mcp/test_sanctuary_autonomous.py --server http://localhost:8000
```

## Execution Time

**Expected Duration:**
- Quick mode (3 runs): ~5-10 minutes
- Full mode (10 runs): ~15-30 minutes

**Why it's slow:**
- Each autonomous activation test requires 9+ API calls
- Each API call takes 2-5 seconds
- 10 runs × 9 calls = 90+ API calls minimum
- Plus natural expiration, overwrite protection, and 4 duration scale tests

## Evidence Output

Evidence bundles are saved to:
```
/tmp/worldarchitect.ai/<branch>/sanctuary_autonomous/
```

Includes:
- `run.json` - Test results with trigger_source logging
- `request_responses.jsonl` - Raw API payloads
- `README.md` - Provenance and metadata
- `evidence.md` - Test summary
- `artifacts/server.log` - Server runtime logs

## Key Features

✅ **Uses shared utilities** - No reimplementation of `testing_mcp/lib/` functions  
✅ **Evidence standards** - Follows `.claude/skills/evidence-standards.md`  
✅ **Trigger source logging** - Proves autonomous detection (boss_defeated, dungeon_cleared, etc.)  
✅ **Statistical validation** - 70%+ success rate for autonomous activation  
✅ **Comprehensive coverage** - Tests all 4 duration scales

## Acceptance Criteria Status

- [x] Test file created at `testing_mcp/test_sanctuary_autonomous.py`
- [x] Uses `testing_mcp/lib/` utilities (no reimplementation)
- [x] Evidence bundles with trigger_source logging
- [x] All 4 test scenarios implemented
- [ ] Autonomous activation test passes 70%+ of 10 runs (requires execution)
- [ ] Natural expiration test passes deterministically (requires execution)
- [ ] Overwrite protection test passes deterministically (requires execution)
- [ ] All 4 duration scales tested (requires execution)

## Notes

- Tests run against **real MCP server** (not mocks)
- Uses **real Gemini API** calls
- Requires `GEMINI_API_KEY` and Firebase credentials
- Server is automatically started if `--server` not provided
