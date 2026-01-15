# Red-Green Test Summary: Narrative Lag Fix

## Test Overview
This document summarizes the red-green test execution for the narrative lag fix (PR #3467).

## Changes Made

### 1. Code Fixes Applied
- **Structured Prompt Fix**: Prioritizes `USER_ACTION` at the top of prompts to prevent narrative lag
- **Logging Bug Fix**: Safe `user_action` access to prevent `AttributeError` when `user_action` is `None`/empty

### 2. Test Improvements
- **Always Save Evidence**: Test now always saves evidence to `/tmp/worldarchitect.ai/<branch>/narrative_lag_repro/` (per evidence-standards.md)
- **Use Venv Python**: Test uses `venv/bin/python3` for server startup (has all dependencies including numpy)
- **Evidence Bundle**: Uses `create_evidence_bundle()` with iteration support and server log inclusion

## Red State (Without Fix)
**Expected Behavior**: Narrative lag should occur - GM prioritizes story history over current user action.

**Code State**: Structured prompt fix removed - `user_action` buried in middle of JSON blob.

**Test Command**:
```bash
cd testing_mcp
python3 test_narrative_lag_repro.py --start-local
```

**Expected Result**: Test should FAIL with narrative lag detected (GM continues ritual instead of responding to STOP command).

## Green State (With Fix)
**Expected Behavior**: GM correctly responds to current user action, prioritizing it over story history.

**Code State**: Structured prompt fix active - `USER_ACTION` placed at top of structured prompt.

**Test Command**:
```bash
cd testing_mcp  
python3 test_narrative_lag_repro.py --start-local
```

**Expected Result**: Test should PASS - GM responds to attack/interrupt correctly.

## Evidence Location
All test runs save evidence to:
```
/tmp/worldarchitect.ai/fix/narrative-lag-prompt-priority/narrative_lag_repro/
├── iteration_001/
│   ├── README.md
│   ├── methodology.md
│   ├── evidence.md
│   ├── metadata.json
│   ├── request_responses.jsonl
│   └── artifacts/
│       └── server.log
├── iteration_002/
└── latest -> iteration_002
```

## Test Scenario
1. Creates campaign with 40+ filler actions (exploits "lost-in-the-middle" effect)
2. Action A: Starts complex ritual (creates unresolved intent)
3. Action B: "Stop ritual, attack goblin" (tests if GM responds to current action)
4. Validates GM responds to Action B (attack/goblin/sword) instead of continuing ritual

## Commits
- `d07918308`: Fix: Safe user_action access in logging to prevent AttributeError
- `95b178859`: test: Update narrative lag test to always save evidence and use venv python

## PR
https://github.com/jleechanorg/worldarchitect.ai/pull/3467
