"""
Worker Configuration Library for Gunicorn

Provides testable, reusable functions for calculating and parsing Gunicorn worker
configuration with environment-aware defaults and error handling.

This library separates configuration logic from gunicorn.conf.py, making it:
- Testable with unit tests
- Reusable across different deployment configurations
- Easy to reason about and maintain
"""
import multiprocessing
import os
from typing import Optional


def calculate_default_workers() -> int:
    """
    Calculate default number of workers using standard formula.

    Returns:
        (2 * CPU cores) + 1
    """
    return (2 * multiprocessing.cpu_count()) + 1


def parse_workers(workers_env: Optional[str], default_workers: int) -> int:
    """
    Parse GUNICORN_WORKERS environment variable with error handling.

    Args:
        workers_env: Raw environment variable value
        default_workers: Default value to use on parse error or None

    Returns:
        Parsed integer value or default
    """
    if workers_env is None:
        return default_workers

    try:
        return int(workers_env)
    except ValueError:
        print(f"WARNING: Invalid GUNICORN_WORKERS value '{workers_env}', using default {default_workers}")
        return default_workers


def parse_threads(threads_env: Optional[str], default_threads: int = 4) -> int:
    """
    Parse GUNICORN_THREADS environment variable with error handling.

    Args:
        threads_env: Raw environment variable value
        default_threads: Default value to use on parse error or None (default: 4)

    Returns:
        Parsed integer value or default
    """
    if threads_env is None:
        return default_threads

    try:
        return int(threads_env)
    except ValueError:
        print(f"WARNING: Invalid GUNICORN_THREADS value '{threads_env}', using default {default_threads}")
        return default_threads


def get_workers() -> int:
    """
    Get number of workers with environment-aware defaults.

    Environment handling:
    - GUNICORN_WORKERS set: Use that value (with validation)
    - ENVIRONMENT="preview": Use 1 worker (memory constrained)
    - RENDER=true (Render.com free tier): Use 1 worker (512MB memory limit)
    - Otherwise: Use (2*CPU)+1 workers

    Returns:
        Number of workers to use
    """
    workers_env = os.getenv("GUNICORN_WORKERS")
    default_workers_calc = calculate_default_workers()

    # If GUNICORN_WORKERS is set, use it (with validation)
    if workers_env is not None:
        return parse_workers(workers_env, default_workers_calc)

    # For preview environment, use 1 worker to fit in 512MB memory
    if os.getenv("ENVIRONMENT") == "preview":
        return 1

    # For Render.com free tier, use 1 worker to fit in 512MB memory limit
    # Render sets RENDER=true in their environment
    if os.getenv("RENDER") == "true":
        return 1

    # Otherwise use standard formula
    return default_workers_calc


def get_threads() -> int:
    """
    Get number of threads per worker.

    Returns:
        Number of threads (default: 4, or GUNICORN_THREADS if set)
    """
    threads_env = os.getenv("GUNICORN_THREADS")
    return parse_threads(threads_env, default_threads=4)
