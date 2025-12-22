"""Memory MCP Integration Module

Automatically enhances LLM responses with relevant memory context.
"""

import re
import time
from datetime import UTC, datetime
from typing import Any

from mvp_site import logging_util, memory_mcp_real

# Common English stop words to exclude from search terms
STOP_WORDS = {
    "the",
    "is",
    "at",
    "which",
    "on",
    "and",
    "a",
    "an",
    "as",
    "are",
    "was",
    "were",
    "been",
    "be",
}


class MemoryIntegration:
    """Core memory integration for automatic context enhancement"""

    def __init__(self):
        self.hot_cache = {}  # TTL: 5 min
        self.warm_cache = {}  # TTL: 30 min
        self.entity_cache = {}  # TTL: 1 hour
        self.cache_timestamps = {}
        self.metrics = MemoryMetrics()

    def extract_query_terms(self, user_input: str) -> list[str]:
        """
        Extracts key terms from the user input for use in memory searches.

        This method identifies and extracts various types of terms from the input string:
        - Entity names: Capitalized words or phrases (e.g., "John Doe").
        - Technical terms: Words not in a predefined list of stop words.
        - PR references: Strings matching the pattern "PR #<number>".

        Args:
            user_input (str): The raw input string provided by the user.

        Returns:
            List[str]: A list of up to 5 unique terms extracted from the input,
            including entities, technical terms, and PR references.
        """
        # Remove common words
        stop_words = STOP_WORDS

        # Extract potential entity names (capitalized words)
        entity_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
        entities = re.findall(entity_pattern, user_input)

        # Extract technical terms
        words = user_input.lower().split()
        technical_terms = [w for w in words if w not in stop_words and len(w) > 2]

        # Extract PR numbers
        pr_pattern = r"PR\s*#?\d+"
        pr_refs = re.findall(pr_pattern, user_input, re.IGNORECASE)

        # Combine and deduplicate
        all_terms = list(set(entities + technical_terms + pr_refs))
        return all_terms[:5]  # Limit to top 5 terms

    def calculate_relevance_score(
        self, entity: dict[str, Any], query_context: str
    ) -> float:
        """
        Calculate the relevance score of an entity to a given query context.

        The scoring algorithm considers the following factors:
        - Name match: If the entity's name matches or contains terms from the query context,
          it contributes 0.4 to the score.
        - Type match: If the entity's type contains specific keywords (e.g., 'pattern', 'learning', 'issue'),
          it contributes 0.2 to the score.
        - Observation relevance: Matches between query terms and the entity's observations contribute
          0.05 per match, up to a maximum of 0.3.

        The final score is capped at 1.0.

        Args:
            entity (Dict[str, Any]): The entity to evaluate. Expected keys include 'name', 'entityType',
                and 'observations' (a list of strings).
            query_context (str): The query context to compare against the entity.

        Returns:
            float: A relevance score between 0.0 and 1.0, where higher scores indicate greater relevance.
        """
        score = 0.0
        query_lower = query_context.lower()

        # Name match (highest weight)
        entity_name = entity.get("name", "").lower().replace("_", " ")
        if entity_name in query_lower or any(
            term in entity_name for term in query_lower.split()
        ):
            score += 0.4

        # Type match
        entity_type = entity.get("entityType", "")
        if any(term in entity_type for term in ["pattern", "learning", "issue"]):
            score += 0.2

        # Observation relevance
        observations = entity.get("observations") or []
        if not isinstance(observations, list):
            observations = [observations]
        obs_text = " ".join(map(str, observations)).lower()
        matches = sum(1 for term in query_lower.split() if term in obs_text)
        score += min(0.3, matches * 0.05)

        # Recency bonus based on entity timestamps
        try:
            # Check if entity has timestamp information
            entity_timestamp = entity.get("timestamp") or entity.get("last_seen")
            if entity_timestamp:
                try:
                    # Parse timestamp (handle multiple formats)
                    if isinstance(entity_timestamp, str):
                        # Try ISO format first
                        timestamp = datetime.fromisoformat(
                            entity_timestamp.replace("Z", "+00:00")
                        )
                    else:
                        timestamp = entity_timestamp

                    # Ensure timezone-aware (assume UTC if naive)
                    if getattr(timestamp, "tzinfo", None) is None:
                        timestamp = timestamp.replace(tzinfo=UTC)

                    # Calculate recency bonus (entities seen within last 24 hours get bonus)
                    now = datetime.now(UTC)
                    time_diff = (now - timestamp).total_seconds()
                    hours_ago = time_diff / 3600

                    if hours_ago < 24:
                        recency_bonus = 0.1 * (1 - hours_ago / 24)  # Up to 0.1 bonus
                        score += recency_bonus
                except Exception as e:
                    # Skip recency bonus if timestamp parsing fails
                    logging_util.debug(f"Failed to parse timestamp for recency bonus: {e}")
        except Exception as e:
            # Skip recency calculation if no timestamp data available
            logging_util.debug(f"No timestamp data available for recency calculation: {e}")

        return min(1.0, score)

    def _call_memory_mcp_search(self, query: str) -> list[dict[str, Any]]:
        """Wrapper for Memory MCP search calls - REAL implementation"""
        try:
            # Import the real Memory MCP module

            # Call the real MCP search function
            results = memory_mcp_real.search_nodes(query)
            logging_util.debug(
                f"Memory MCP search for '{query}' returned {len(results)} results"
            )
            # Type cast to satisfy mypy
            return list(results) if results else []

        except ImportError:
            # No fallback - MCP tools are not accessible from Python
            logging_util.debug("Memory MCP cannot be accessed from Python runtime")
            return []
        except Exception as e:
            logging_util.error(f"Memory MCP search error: {e}")
            return []

    def search_relevant_memory(self, terms: list[str]) -> list[dict[str, Any]]:
        """
        Search and retrieve relevant memories.

        This method searches for memories relevant to the provided terms. It first checks the
        `hot_cache` for cached results. If no valid cache entry is found, it performs a search
        (implementation details omitted for brevity).

        Caching Behavior:
        - Results are cached in `hot_cache` with a time-to-live (TTL) of 5 minutes.
        - Cache keys are generated by concatenating the sorted search terms with colons.

        Error Handling:
        - If an exception occurs during the search, it is logged, and an empty list is returned.
        - The method also records metrics about the query's success or failure.

        Args:
            terms (List[str]): A list of search terms extracted from user input.

        Returns:
            List[Dict[str, Any]]: A list of memory entities relevant to the search terms.
        """
        start_time = time.time()

        # Check hot cache first
        cache_key = f"search:{':'.join(sorted(terms))}"
        if (
            cache_key in self.hot_cache
            and time.time() - self.cache_timestamps[cache_key] < 300
        ):  # 5 min TTL
            self.metrics.record_query(True, time.time() - start_time)
            cached_result: list[dict[str, Any]] = self.hot_cache[cache_key]
            return cached_result

        try:
            # Use real Memory MCP functions - integrate directly with Claude Code MCP
            # This requires the memory server to be running and accessible

            # Search for each term using real MCP
            all_results = []
            for term in terms[:3]:  # Limit searches to prevent timeout
                try:
                    # Call Memory MCP search (this will work when running in Claude Code)
                    # For now, we'll create a wrapper that can be easily replaced
                    results = self._call_memory_mcp_search(term)
                    if results:
                        all_results.extend(results)
                except Exception as e:
                    logging_util.debug(f"MCP search failed for term '{term}': {e}")
                    continue

            # Deduplicate by entity name
            unique_entities = {}
            for entity in all_results:
                name = entity.get("name", "")
                if name and name not in unique_entities:
                    unique_entities[name] = entity

            # Score and filter
            scored = []
            query_text = " ".join(terms)
            for entity in unique_entities.values():
                score = self.calculate_relevance_score(entity, query_text)
                if score >= 0.4:
                    scored.append((score, entity))

            # Sort by score and take top 5
            relevant = [e for _, e in sorted(scored, key=lambda x: x[0], reverse=True)][
                :5
            ]

            # Cache result
            self.hot_cache[cache_key] = relevant
            self.cache_timestamps[cache_key] = time.time()

            self.metrics.record_query(False, time.time() - start_time)
            return relevant

        except Exception as e:
            logging_util.error(f"Memory search failed: {e}")
            self.metrics.record_query(False, time.time() - start_time)
            return []

    def enhance_context(
        self, original_context: str, memories: list[dict[str, Any]]
    ) -> str:
        """Inject memory context into prompt"""
        if not memories:
            return original_context

        memory_section = "\n## Relevant Memory Context\n"
        for memory in memories:
            name = memory.get("name", "Unknown")
            entity_type = memory.get("entityType", "unknown")
            observations = memory.get("observations", [])

            memory_section += f"\n### {name} ({entity_type})\n"
            for obs in observations[:3]:  # Limit observations
                memory_section += f"- {obs}\n"

        # Inject before the main content
        return memory_section + "\n" + original_context

    def get_enhanced_response_context(self, user_input: str) -> str:
        """Main entry point for memory enhancement"""
        # Extract terms
        terms = self.extract_query_terms(user_input)
        if not terms:
            return ""

        # Search memories
        memories = self.search_relevant_memory(terms)
        if not memories:
            return ""

        # Create context section
        return self.enhance_context("", memories)


class MemoryMetrics:
    """Track memory system performance"""

    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.query_times = []

    def record_query(self, cached: bool, latency: float):
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        self.query_times.append(latency)

    @property
    def cache_hit_rate(self):
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0

    @property
    def avg_latency(self):
        return sum(self.query_times) / len(self.query_times) if self.query_times else 0


# Global instance
memory_integration = MemoryIntegration()


def enhance_slash_command(command: str, args: str) -> str:
    """Enhance slash command with memory context"""
    # Commands that benefit from memory
    memory_commands = {"/learn", "/debug", "/think", "/analyze", "/fix"}

    if command not in memory_commands:
        return ""

    return memory_integration.get_enhanced_response_context(args)
