"""
Centralized Executor Configuration for WorldArchitect.AI

This module provides a shared ThreadPoolExecutor with 100 workers for handling
blocking I/O operations (Gemini API, Firestore, etc.) across both the Flask
web server and MCP server.

Key Features:
- 100 concurrent threads for blocking I/O (configurable via EXECUTOR_MAX_WORKERS)
- Singleton pattern ensures one executor per process
- Thread-safe initialization
- Automatic integration with asyncio.to_thread() via set_default_executor()

Usage:
    from infrastructure.executor_config import (
        get_blocking_io_executor,
        configure_asyncio_executor,
        EXECUTOR_MAX_WORKERS,
    )

    # Option 1: Get executor directly for loop.run_in_executor()
    executor = get_blocking_io_executor()
    result = await loop.run_in_executor(executor, blocking_func)

    # Option 2: Configure asyncio to use our executor by default
    # This makes asyncio.to_thread() use our 100-thread pool automatically
    configure_asyncio_executor(loop)
    result = await asyncio.to_thread(blocking_func)  # Uses our executor!
"""

import asyncio
import concurrent.futures
import os
import threading
from typing import Optional

# Configuration - can be overridden via environment variable
EXECUTOR_MAX_WORKERS: int = int(os.getenv("EXECUTOR_MAX_WORKERS", "100"))

# Thread name prefix for debugging/monitoring
EXECUTOR_THREAD_PREFIX: str = "blocking_io"

# Singleton executor and lock
_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
_executor_lock = threading.Lock()


def get_blocking_io_executor() -> concurrent.futures.ThreadPoolExecutor:
    """
    Get or create the shared blocking I/O executor.

    Returns a singleton ThreadPoolExecutor with EXECUTOR_MAX_WORKERS threads.
    Thread-safe using double-checked locking pattern.

    Returns:
        ThreadPoolExecutor configured for blocking I/O operations
    """
    global _executor

    if _executor is None:
        with _executor_lock:
            if _executor is None:
                _executor = concurrent.futures.ThreadPoolExecutor(
                    max_workers=EXECUTOR_MAX_WORKERS,
                    thread_name_prefix=EXECUTOR_THREAD_PREFIX,
                )
    return _executor


def configure_asyncio_executor(loop=None) -> None:
    """
    Configure asyncio to use our shared executor by default.

    After calling this, asyncio.to_thread() will automatically use our
    100-thread executor instead of the default limited one.

    Args:
        loop: Event loop to configure. If None, uses current running loop
              or creates a new one if no loop is running.

    Note:
        This should be called once during application startup, after
        creating the event loop but before any asyncio.to_thread() calls.
    """
    executor = get_blocking_io_executor()

    if loop is None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError(
                "configure_asyncio_executor() must be called from a running "
                "event loop or with an explicit loop argument"
            )

    loop.set_default_executor(executor)


def shutdown_executor(wait: bool = True) -> None:
    """
    Shutdown the shared executor gracefully.

    Args:
        wait: If True, wait for all pending tasks to complete
    """
    global _executor

    with _executor_lock:
        if _executor is not None:
            _executor.shutdown(wait=wait)
            _executor = None


def get_executor_stats() -> dict:
    """
    Get current executor statistics for monitoring.

    Returns:
        Dictionary with executor configuration and state
    """
    return {
        "max_workers": EXECUTOR_MAX_WORKERS,
        "thread_prefix": EXECUTOR_THREAD_PREFIX,
        "executor_initialized": _executor is not None,
    }
