# Agent Limit Enforcement Fix Plan

## Problem
The orchestration system has a `MAX_CONCURRENT_AGENTS = 5` limit defined in `task_dispatcher.py`, but it's not being enforced. We were able to create 11 agents when the limit should have stopped us at 5.

## Root Cause
1. `TaskDispatcher` checks `self.active_agents` which is a local set that starts empty with each invocation
2. The system doesn't persist active agent count between runs
3. Each orchestration command creates a new `TaskDispatcher` instance with empty `active_agents`

## Current Architecture Issues
- `task_dispatcher.py` has the limit logic but it's not persistent
- `orchestrate_unified.py` uses `TaskDispatcher` but doesn't respect the limit
- No central tracking of running agents across invocations

## Solution Options

### Option 1: Remove task_dispatcher.py and implement limit in orchestrate_unified.py
- Check actual tmux sessions before creating new agents
- Count existing `task-agent-*` sessions
- Enforce limit based on actual running agents

### Option 2: Fix task_dispatcher.py to track agents properly
- Use Redis or file-based tracking for persistent agent count
- Check actual tmux sessions on startup
- Maintain accurate active_agents set

### Option 3: Implement system-wide agent manager
- Central service that tracks all agents
- All orchestration commands check with manager
- Proper lifecycle management

## Recommendation
Go with Option 1 - Remove `task_dispatcher.py` and implement proper limit checking in `orchestrate_unified.py` by counting actual tmux sessions. This is simpler and more reliable than trying to maintain state.

## Files to Change
1. Remove `orchestration/task_dispatcher.py`
2. Update `orchestration/orchestrate_unified.py` to:
   - Count existing tmux sessions before creating agents
   - Enforce MAX_CONCURRENT_AGENTS limit
   - Move any needed logic from task_dispatcher.py
3. Update tests that depend on task_dispatcher.py
4. Update documentation

## Implementation Steps
1. Analyze what parts of task_dispatcher.py are actually needed
2. Move essential logic to orchestrate_unified.py
3. Implement proper agent counting via tmux sessions
4. Remove task_dispatcher.py
5. Update all imports and tests
6. Test the limit enforcement
