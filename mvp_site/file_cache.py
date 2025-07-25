"""
Generalized file caching module using cachetools.

This module provides thread-safe file caching for any file read operation,
replacing custom cache implementations with a battle-tested library.
"""

import os
import threading
import time

import logging_util
from cachetools import TTLCache
from token_utils import format_token_count

# Cache configuration constants
CACHE_MAX_SIZE = 1000  # Maximum number of files to cache
CACHE_TTL_SECONDS = 3600  # Cache TTL in seconds (1 hour)

# Thread-safe file cache with 1-hour TTL
_file_cache = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL_SECONDS)
_cache_lock = threading.Lock()

# Statistics tracking
_cache_stats = {
    'hits': 0,
    'misses': 0,
    'total_chars_cached': 0,
    'start_time': time.time()
}

def read_file_cached(filepath: str, encoding: str = 'utf-8') -> str:
    """
    Read file with automatic caching. Thread-safe with TTL expiration.

    Args:
        filepath: Path to file to read
        encoding: File encoding (default: utf-8)

    Returns:
        File content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
    """
    # Normalize path for consistent cache keys
    normalized_path = os.path.abspath(filepath)

    with _cache_lock:
        # Check cache first
        if normalized_path in _file_cache:
            content = _file_cache[normalized_path]
            _cache_stats['hits'] += 1

            char_count = len(content)
            formatted_count = format_token_count(char_count)
            logging_util.info(f"Cache HIT for {os.path.basename(filepath)}: {formatted_count}")
            return content

        # Cache miss - read from file
        _cache_stats['misses'] += 1

        try:
            with open(normalized_path, 'r', encoding=encoding) as f:
                content = f.read()

            # Cache the content
            _file_cache[normalized_path] = content

            char_count = len(content)
            _cache_stats['total_chars_cached'] += char_count
            formatted_count = format_token_count(char_count)
            logging_util.info(f"Cache MISS for {os.path.basename(filepath)}: loaded and cached {formatted_count}")

            return content

        except Exception as e:
            logging_util.error(f"Failed to read file {filepath}: {e}")
            raise

def clear_file_cache() -> None:
    """Clear all cached files. Useful for testing and development."""
    with _cache_lock:
        _file_cache.clear()
        _cache_stats['hits'] = 0
        _cache_stats['misses'] = 0
        _cache_stats['total_chars_cached'] = 0
        _cache_stats['start_time'] = time.time()

    logging_util.info("Cleared file cache")

def get_cache_stats() -> dict:
    """
    Get cache performance statistics.

    Returns:
        Dictionary with cache performance metrics
    """
    with _cache_lock:
        total_requests = _cache_stats['hits'] + _cache_stats['misses']
        hit_rate = (_cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_hits': _cache_stats['hits'],
            'cache_misses': _cache_stats['misses'],
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 1),
            'total_cached_chars': _cache_stats['total_chars_cached'],
            'total_cached_tokens': _cache_stats['total_chars_cached'] // 4,
            'cached_files': len(_file_cache),
            'uptime_seconds': round(time.time() - _cache_stats['start_time'], 1)
        }

def invalidate_file(filepath: str) -> bool:
    """
    Remove specific file from cache (useful when file is modified).

    Args:
        filepath: Path to file to remove from cache

    Returns:
        True if file was in cache and removed, False otherwise
    """
    normalized_path = os.path.abspath(filepath)

    with _cache_lock:
        if normalized_path in _file_cache:
            del _file_cache[normalized_path]
            logging_util.info(f"Invalidated cache for {os.path.basename(filepath)}")
            return True
        return False
