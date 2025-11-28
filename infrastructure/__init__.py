"""
Infrastructure helpers for server deployment and configuration

This package contains reusable infrastructure code that can be used
across different deployment scenarios and server configurations.
"""

from infrastructure.worker_config import (
    calculate_default_workers,
    parse_workers,
    parse_threads,
    get_workers,
    get_threads,
)
from infrastructure.mcp_helpers import (
    create_thread_safe_mcp_getter,
)
from infrastructure.executor_config import (
    EXECUTOR_MAX_WORKERS,
    get_blocking_io_executor,
    configure_asyncio_executor,
    shutdown_executor,
    get_executor_stats,
)

__all__ = [
    "calculate_default_workers",
    "parse_workers",
    "parse_threads",
    "get_workers",
    "get_threads",
    "create_thread_safe_mcp_getter",
    # Executor configuration (100-thread pool for blocking I/O)
    "EXECUTOR_MAX_WORKERS",
    "get_blocking_io_executor",
    "configure_asyncio_executor",
    "shutdown_executor",
    "get_executor_stats",
]
