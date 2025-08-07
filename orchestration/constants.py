#!/usr/bin/env python3
"""
Orchestration System Constants

Shared constants used across the orchestration system to ensure consistency.
"""

# Agent session timeout (1 hour in seconds)
AGENT_SESSION_TIMEOUT_SECONDS = 3600  # 1 hour (was 24 hours)

# Agent monitoring thresholds
IDLE_MINUTES_THRESHOLD = 30  # Minutes of no activity before considering agent idle
CLEANUP_CHECK_INTERVAL_MINUTES = 15  # How often to check for cleanup opportunities

# Production safety limits - only counts actively working agents (not idle)
DEFAULT_MAX_CONCURRENT_AGENTS = 5

# Agent name generation
TIMESTAMP_MODULO = 100000000  # 8 digits from microseconds for unique name generation
