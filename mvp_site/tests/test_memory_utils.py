"""Tests for memory_utils module."""

from mvp_site.memory_utils import (
    AUTO_MEMORY_MAX_LENGTH,
    AUTO_MEMORY_PREFIX,
    DEDUPE_WINDOW_SIZE,
    MAX_CORE_MEMORY_TOKENS,
    MEMORY_SIMILARITY_THRESHOLD,
    MIN_RECENT_MEMORIES,
    format_memories_for_prompt,
    is_duplicate_memory,
    is_similar_memory,
    select_memories_by_budget,
)


class TestIsSimilarMemory:
    """Tests for is_similar_memory function."""

    def test_exact_match_is_similar(self):
        """Exact matches should be considered similar."""
        assert is_similar_memory("Hello world", "Hello world")

    def test_case_insensitive_match(self):
        """Case differences should still match."""
        assert is_similar_memory("HELLO WORLD", "hello world")

    def test_slightly_different_is_similar(self):
        """Small differences should still match."""
        assert is_similar_memory(
            "The party fought the dragon", "The party fought the dragons"
        )

    def test_completely_different_not_similar(self):
        """Completely different strings should not match."""
        assert not is_similar_memory(
            "The party fought the dragon", "Bob went to the store to buy milk"
        )

    def test_custom_threshold(self):
        """Custom threshold should be respected."""
        # These are ~75% similar
        mem1 = "The party explored the dungeon"
        mem2 = "The party explored the forest"

        # Should not match at default 0.85 threshold
        assert not is_similar_memory(mem1, mem2, threshold=0.85)

        # Should match at lower 0.7 threshold
        assert is_similar_memory(mem1, mem2, threshold=0.7)


class TestIsDuplicateMemory:
    """Tests for is_duplicate_memory function."""

    def test_empty_list_no_duplicate(self):
        """New memory with empty list is not duplicate."""
        assert not is_duplicate_memory("New memory", [])

    def test_exact_duplicate_found(self):
        """Exact duplicate should be found."""
        existing = ["Memory A", "Memory B", "Memory C"]
        assert is_duplicate_memory("Memory B", existing)

    def test_near_duplicate_found(self):
        """Near-duplicate should be found."""
        existing = ["The party fought a dragon and won"]
        assert is_duplicate_memory("The party fought a dragon and won!", existing)

    def test_no_duplicate_when_different(self):
        """Different memory should not be flagged."""
        existing = ["The party fought a dragon"]
        assert not is_duplicate_memory("Bob bought groceries", existing)

    def test_only_checks_recent_window(self):
        """Should only check recent memories within window size."""
        # Create 100 memories, put duplicate at position 0 (outside window of 20)
        existing = ["DUPLICATE memory here"] + [f"Memory {i}" for i in range(99)]

        # With default window (20), should NOT find duplicate at position 0
        assert not is_duplicate_memory("DUPLICATE memory here", existing)

        # With window_size=100, SHOULD find duplicate
        assert is_duplicate_memory("DUPLICATE memory here", existing, window_size=100)


class TestSelectMemoriesByBudget:
    """Tests for select_memories_by_budget function."""

    def test_empty_list_returns_empty(self):
        """Empty input returns empty output."""
        assert select_memories_by_budget([]) == []

    def test_under_budget_returns_all(self):
        """Memories under budget are all returned."""
        memories = ["Short memory 1", "Short memory 2", "Short memory 3"]
        result = select_memories_by_budget(memories, max_tokens=1000)
        assert result == memories

    def test_preserves_order(self):
        """Original order should be preserved."""
        memories = [f"Memory {i}" for i in range(5)]
        result = select_memories_by_budget(memories, max_tokens=1000)
        assert result == memories

    def test_recent_memories_always_included(self):
        """Most recent memories should always be included."""
        # Create 20 memories, budget allows only ~15
        memories = [f"Memory {i}" for i in range(20)]
        result = select_memories_by_budget(memories, max_tokens=50, min_recent=10)

        # Last 10 should always be included
        for i in range(10, 20):
            assert f"Memory {i}" in result

    def test_over_budget_truncates_old(self):
        """When over budget, oldest memories are dropped first."""
        # Each memory is ~10 tokens (40 chars)
        memories = ["A" * 40 for _ in range(100)]

        # Budget for ~20 memories (200 tokens)
        result = select_memories_by_budget(memories, max_tokens=200, min_recent=5)

        # Should have fewer memories than original
        assert len(result) < len(memories)

        # Should include at least min_recent
        assert len(result) >= 5

    def test_large_campaign_scenario(self):
        """Simulate a large campaign with 800+ memories."""
        # Create 800 memories of ~22.5 tokens each (90 chars)
        # Total: 800 * 22.5 = ~18,000 tokens
        memories = [
            f"[auto] This is memory number {i} with some plot details about what happened in the story "
            for i in range(800)
        ]

        # Apply budget of 5000 tokens (~222 memories at 22.5 tokens each)
        result = select_memories_by_budget(memories, max_tokens=5000, min_recent=10)

        # Should significantly reduce memory count
        assert len(result) < 300  # Under budget
        assert len(result) >= 10  # At least min_recent

        # Most recent should be included
        assert memories[-1] in result
        assert memories[-10] in result


class TestFormatMemoriesForPrompt:
    """Tests for format_memories_for_prompt function."""

    def test_empty_list_returns_empty_string(self):
        """Empty list should return empty string."""
        assert format_memories_for_prompt([]) == ""

    def test_formats_with_header_and_bullets(self):
        """Memories should be formatted with header and bullets."""
        memories = ["Memory A", "Memory B"]
        result = format_memories_for_prompt(memories)

        assert "CORE MEMORY LOG" in result
        assert "- Memory A" in result
        assert "- Memory B" in result

    def test_ends_with_escaped_newlines(self):
        """Output should end with escaped newlines for prompt separation."""
        memories = ["Memory A"]
        result = format_memories_for_prompt(memories)
        assert result.endswith("\\n\\n")


class TestConstants:
    """Tests to verify constants have sensible values."""

    def test_auto_memory_max_length(self):
        """AUTO_MEMORY_MAX_LENGTH should be reasonable."""
        assert AUTO_MEMORY_MAX_LENGTH >= 100  # At least 100 chars
        assert AUTO_MEMORY_MAX_LENGTH <= 1000  # Not too long

    def test_similarity_threshold(self):
        """MEMORY_SIMILARITY_THRESHOLD should be reasonable."""
        assert 0.5 <= MEMORY_SIMILARITY_THRESHOLD <= 0.95

    def test_max_memory_tokens(self):
        """MAX_CORE_MEMORY_TOKENS should be reasonable."""
        assert MAX_CORE_MEMORY_TOKENS >= 5000
        assert MAX_CORE_MEMORY_TOKENS <= 100000  # Allow up to 100K for generous budgets

    def test_min_recent_memories(self):
        """MIN_RECENT_MEMORIES should be reasonable."""
        assert MIN_RECENT_MEMORIES >= 5
        assert MIN_RECENT_MEMORIES <= 50

    def test_dedupe_window_size(self):
        """DEDUPE_WINDOW_SIZE should be reasonable."""
        assert DEDUPE_WINDOW_SIZE >= 10
        assert DEDUPE_WINDOW_SIZE <= 100

    def test_auto_memory_prefix(self):
        """AUTO_MEMORY_PREFIX should be defined."""
        assert AUTO_MEMORY_PREFIX == "[auto]"
