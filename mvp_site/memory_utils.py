"""Memory management utilities for core memories.

This module centralizes all memory-related logic:
- Token budget selection (prevents context overflow)
- Deduplication (removes near-duplicate memories)
- Memory constants and thresholds

Usage:
    from mvp_site.memory_utils import (
        select_memories_by_budget,
        is_duplicate_memory,
        AUTO_MEMORY_PREFIX,
    )
"""

from __future__ import annotations

from difflib import SequenceMatcher

from mvp_site import logging_util
from mvp_site.token_utils import CHARS_PER_TOKEN

# Prefix for auto-generated core memories
AUTO_MEMORY_PREFIX = "[auto]"

# Maximum length for auto-generated core memories.
# 500 chars allows ~100 words which is enough for a meaningful summary.
AUTO_MEMORY_MAX_LENGTH = 500

# Similarity threshold for deduplication (0.0-1.0).
# Memories with similarity >= this threshold are considered duplicates.
# 0.85 catches near-duplicates while allowing meaningfully different memories.
MEMORY_SIMILARITY_THRESHOLD = 0.85

# Maximum tokens to allocate for core memories in prompt.
# Prevents memory explosion from consuming entire context window.
# 40K tokens allows substantial memory while leaving room for story history,
# system prompts, and response in a 200K context window.
MAX_CORE_MEMORY_TOKENS = 40000

# Minimum recent memories to always include regardless of token budget.
# Ensures continuity even when memories are large.
MIN_RECENT_MEMORIES = 10

# Number of recent memories to check for duplicates.
# Duplicates are most likely in recent context; checking all is O(n²) expensive.
DEDUPE_WINDOW_SIZE = 20


def is_similar_memory(
    new_entry: str, existing: str, threshold: float | None = None
) -> bool:
    """Check if two memories are similar enough to be considered duplicates.

    Args:
        new_entry: The new memory to check
        existing: An existing memory to compare against
        threshold: Similarity threshold (0.0-1.0). Defaults to MEMORY_SIMILARITY_THRESHOLD.

    Returns:
        True if memories are similar enough to be duplicates
    """
    if threshold is None:
        threshold = MEMORY_SIMILARITY_THRESHOLD

    # Quick exact match check
    if new_entry == existing:
        return True

    # Fuzzy similarity check
    ratio = SequenceMatcher(None, new_entry.lower(), existing.lower()).ratio()
    return ratio >= threshold


def is_duplicate_memory(
    new_entry: str,
    existing_memories: list[str],
    threshold: float | None = None,
    window_size: int | None = None,
) -> bool:
    """Check if a memory already exists in recent memories (exact or near-duplicate).

    Only checks the most recent `window_size` memories for performance.
    Duplicates are most likely to occur in recent context anyway.

    Args:
        new_entry: The new memory to check
        existing_memories: List of existing memories (oldest first)
        threshold: Similarity threshold. Defaults to MEMORY_SIMILARITY_THRESHOLD.
        window_size: Number of recent memories to check. Defaults to DEDUPE_WINDOW_SIZE.

    Returns:
        True if memory is a duplicate of a recent memory
    """
    if window_size is None:
        window_size = DEDUPE_WINDOW_SIZE

    # Only check recent memories for duplicates
    # Handle window_size=0 explicitly to avoid -0 slicing (returns entire list)
    if window_size <= 0 or not existing_memories:
        recent_memories = []
    else:
        recent_memories = existing_memories[-window_size:]

    return any(
        is_similar_memory(new_entry, existing, threshold)
        for existing in recent_memories
    )


def select_memories_by_budget(
    memories: list[str],
    max_tokens: int | None = None,
    min_recent: int | None = None,
) -> list[str]:
    """Select memories that fit within a token budget.

    Strategy:
    1. Always include the most recent `min_recent` memories for continuity
    2. Add older memories from newest to oldest until budget exhausted

    Args:
        memories: Full list of memories (oldest first)
        max_tokens: Maximum token budget. Defaults to MAX_CORE_MEMORY_TOKENS.
        min_recent: Minimum recent memories to include. Defaults to MIN_RECENT_MEMORIES.

    Returns:
        Selected memories (preserves original order, oldest first)
    """
    if max_tokens is None:
        max_tokens = MAX_CORE_MEMORY_TOKENS
    if min_recent is None:
        min_recent = MIN_RECENT_MEMORIES
    elif min_recent < 0:
        min_recent = 0

    if not memories:
        return []

    # If under budget, return all (use ceiling to avoid undercounting)
    def to_tokens(chars: int) -> int:
        return (chars + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN

    total_tokens = to_tokens(sum(len(mem) for mem in memories))
    logging_util.info(
        f"[MEMORY_BUDGET] Input: {len(memories)} memories, "
        f"{total_tokens:,} tokens (budget: {max_tokens:,})"
    )

    if total_tokens <= max_tokens:
        logging_util.info(
            f"[MEMORY_BUDGET] Under budget - returning all {len(memories)} memories"
        )
        return memories

    # Split into guaranteed recent and optional older
    if min_recent > 0:
        recent = memories[-min_recent:] if len(memories) > min_recent else memories
        older = memories[:-min_recent] if len(memories) > min_recent else []
    else:
        recent = []
        older = memories

    # Start with recent memories
    selected_older: list[str] = []
    used_chars = sum(len(mem) for mem in recent)

    # Add older memories from newest to oldest until budget exhausted
    for memory in reversed(older):
        prospective_chars = used_chars + len(memory)
        if to_tokens(prospective_chars) <= max_tokens:
            selected_older.insert(0, memory)  # Maintain order
            used_chars = prospective_chars

    result = selected_older + recent
    excluded_count = len(memories) - len(result)
    final_tokens = to_tokens(used_chars)
    logging_util.info(
        f"[MEMORY_BUDGET] TRUNCATED: {len(result)} selected, "
        f"{excluded_count} excluded, {final_tokens:,} tokens used"
    )
    return result


def format_memories_for_prompt(memories: list[str]) -> str:
    """Format memories as a bullet list for LLM prompt.

    Args:
        memories: List of memory strings

    Returns:
        Formatted string with header and bullet points, or empty string if no memories

    Note:
        Uses escaped \\n for consistency with other prompt sections in llm_service.py.
        The LLM interprets these as newlines in the prompt context.
    """
    if not memories:
        return ""

    memories_list = "\\n".join([f"- {item}" for item in memories])
    return f"CORE MEMORY LOG (SUMMARY OF KEY EVENTS):\\n{memories_list}\\n\\n"
