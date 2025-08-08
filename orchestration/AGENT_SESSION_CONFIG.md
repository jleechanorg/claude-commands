# Agent Session Configuration

## Overview

This document describes the configuration for long-running orchestration agent sessions.

## Key Changes

### 1. Always Use `--dangerously-skip-permissions`

**Rationale**: Orchestration agents need to perform autonomous operations including:
- File creation and editing
- Git operations (branch creation, commits, pushes)
- GitHub operations (PR creation, comments)
- Browser automation for testing
- Package installation and builds

**Implementation**: All orchestration agents now automatically use `--dangerously-skip-permissions` flag to prevent interruption by approval prompts.

### 2. 1-Hour Session Duration

**Rationale**: Orchestration agents may run for extended periods, especially for:
- Complex browser testing workflows
- Multi-step PR creation and validation
- Long-running builds and test suites
- Image capture and upload processes

**Implementation**: New `tmux-agent.conf` configuration keeps sessions alive for 1 hour after completion.

## Configuration Files

### `orchestration/tmux-agent.conf`
- Tmux configuration optimized for agent sessions
- Keeps sessions alive after process completion
- Enables proper monitoring and debugging
- 1-hour keepalive timer for extended workflows

### `orchestration/task_dispatcher.py`
- Already uses `--dangerously-skip-permissions` for all agents
- Updated to use agent-specific tmux configuration
- Extended session duration to 3600 seconds (1 hour)
- Enhanced logging for session management

### `orchestration/agent_health_monitor.py`
- Updated to use agent-specific tmux configuration
- Maintains consistency with task dispatcher approach

## Usage

All orchestration agents started through the framework now automatically:
1. Run with full permissions (no approval prompts)
2. Remain accessible for 1 hour after completion
3. Provide enhanced session monitoring capabilities

## Security Considerations

**⚠️ CRITICAL SECURITY WARNING:**
- The `--dangerously-skip-permissions` flag **MUST NEVER** be used for user-supplied prompts or production traffic
- This configuration is **ONLY** for controlled development environments with trusted input
- **NEVER expose this configuration to external users or untrusted input**

**Development Environment Safety:**
- The flag is intentionally used for orchestration in controlled development settings
- Agents operate in isolated worktree environments when possible
- All operations are logged and traceable through tmux session history
- Sessions auto-terminate after 1 hour to prevent resource accumulation
- Sandbox isolation layer provides additional containment for agent operations

## Monitoring

Monitor agent sessions with:
```bash
tmux list-sessions | grep agent
tmux attach -t [session-name]
tmux capture-pane -t [session-name] -p
```
