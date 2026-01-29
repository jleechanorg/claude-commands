#!/usr/bin/env python3
"""
Orchestration System Constants

Shared constants used across the orchestration system to ensure consistency.
"""

# Agent session timeout (1 hour in seconds)
AGENT_SESSION_TIMEOUT_SECONDS = 3600  # 1 hour (was 24 hours)

# Runtime CLI execution timeout (per attempt)
# All CLIs (claude, codex, gemini, cursor) use OAuth authentication and complex tasks may timeout
# Preflight validation allows timeouts to pass, so runtime must have timeouts to prevent hangs
# and allow prompt fallback to next CLI in chain
RUNTIME_CLI_TIMEOUT_SECONDS = 1800  # 30 minutes per CLI attempt (all CLIs use OAuth and may need time for complex tasks)

# Agent monitoring thresholds
IDLE_MINUTES_THRESHOLD = 30  # Minutes of no activity before considering agent idle
CLEANUP_CHECK_INTERVAL_MINUTES = 15  # How often to check for cleanup opportunities

# Production safety limits - only counts actively working agents (not idle)
DEFAULT_MAX_CONCURRENT_AGENTS = 5

# Agent name generation
TIMESTAMP_MODULO = 100000000  # 8 digits from microseconds for unique name generation
