#!/usr/bin/env python3
"""
Orchestration System Constants

Shared constants used across the orchestration system to ensure consistency.
"""

import os
import warnings

# Universal agent timeout (single source of truth for orchestration/monitoring)
# SYSTEM CONTRACT: Orchestration layer pinned to 600s per CLAUDE.md and AGENTS.md
AGENT_TIMEOUT_SECONDS = 600  # 10 minutes

# Independent timeouts for different concerns:
# - AGENT_SESSION_TIMEOUT: Overall session lifetime (longer for debugging)
# - RUNTIME_CLI_TIMEOUT: Per-CLI attempt timeout (may differ from session)
AGENT_SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes - session lifetime for long-running debug
RUNTIME_CLI_TIMEOUT_SECONDS = 900  # 15 minutes - per attempt timeout

# Hard ceiling for child CLI processes spawned by generated orchestration wrappers.
# `ulimit -v` expects kibibytes. Override via env when a host needs a different cap.
# Default: 4 GiB (4 * 1024 * 1024 KB)
_DEFAULT_VMEM_CAP_KB = 4 * 1024 * 1024
_ORCHESTRATION_VMEM_CAP_ENV = os.environ.get("ORCHESTRATION_CHILD_PROCESS_VMEM_CAP_KB")
if _ORCHESTRATION_VMEM_CAP_ENV is not None:
    try:
        _parsed = int(_ORCHESTRATION_VMEM_CAP_ENV)
        if _parsed <= 0:
            raise ValueError(f"must be positive, got {_parsed}")
        ORCHESTRATION_CHILD_PROCESS_VMEM_CAP_KB = _parsed
    except ValueError:
        warnings.warn(
            f"Invalid ORCHESTRATION_CHILD_PROCESS_VMEM_CAP_KB value: "
            f"'{_ORCHESTRATION_VMEM_CAP_ENV}'. Using default: {_DEFAULT_VMEM_CAP_KB} KB"
        )
        ORCHESTRATION_CHILD_PROCESS_VMEM_CAP_KB = _DEFAULT_VMEM_CAP_KB
else:
    ORCHESTRATION_CHILD_PROCESS_VMEM_CAP_KB = _DEFAULT_VMEM_CAP_KB

# Agent monitoring thresholds
IDLE_MINUTES_THRESHOLD = 30  # Minutes of no activity before considering agent idle
CLEANUP_CHECK_INTERVAL_MINUTES = 15  # How often to check for cleanup opportunities

# Production safety limits - only counts actively working agents (not idle)
DEFAULT_MAX_CONCURRENT_AGENTS = 5

# Agent name generation
TIMESTAMP_MODULO = 100000000  # 8 digits from microseconds for unique name generation
MAX_AGENT_NAME_LENGTH = 128  # Align with backend agent-name constraints
