#!/usr/bin/env python3
"""
Orchestration System Constants

Shared constants used across the orchestration system to ensure consistency.
"""

# Universal agent timeout (single source of truth for orchestration/monitoring)
# SYSTEM CONTRACT: Orchestration layer pinned to 600s per CLAUDE.md and AGENTS.md
AGENT_TIMEOUT_SECONDS = 600  # 10 minutes

# Independent timeouts for different concerns:
# - AGENT_SESSION_TIMEOUT: Overall session lifetime (longer for debugging)
# - RUNTIME_CLI_TIMEOUT: Per-CLI attempt timeout (may differ from session)
AGENT_SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes - session lifetime for long-running debug
RUNTIME_CLI_TIMEOUT_SECONDS = 900  # 15 minutes - per attempt timeout

# Agent monitoring thresholds
IDLE_MINUTES_THRESHOLD = 30  # Minutes of no activity before considering agent idle
CLEANUP_CHECK_INTERVAL_MINUTES = 15  # How often to check for cleanup opportunities

# Production safety limits - only counts actively working agents (not idle)
DEFAULT_MAX_CONCURRENT_AGENTS = 5

# Agent name generation
TIMESTAMP_MODULO = 100000000  # 8 digits from microseconds for unique name generation
MAX_AGENT_NAME_LENGTH = 128  # Align with backend agent-name constraints
