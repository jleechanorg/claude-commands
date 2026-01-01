"""Shared game-related constants for MCP integration tests."""

from __future__ import annotations

# D&D 5e XP thresholds (PHB). Keys are level numbers, values are cumulative XP.
XP_THRESHOLDS: dict[int, int] = {
    1: 0,
    2: 300,
    3: 900,
    4: 2700,
    5: 6500,
    6: 14000,
    7: 23000,
    8: 34000,
    9: 48000,
    10: 64000,
    11: 85000,
    12: 100000,
    13: 120000,
    14: 140000,
    15: 165000,
    16: 195000,
    17: 225000,
    18: 265000,
    19: 305000,
    20: 355000,
}

# Regex patterns to detect XP gains in LLM narratives (supports commas in numbers).
XP_GAIN_PATTERNS: list[str] = [
    r"(\d[\d,]*)\s*XP",
    r"(\d[\d,]*)\s*experience\s*points?",
    r"gain(?:ed|s)?\s*(\d[\d,]*)",
    r"earn(?:ed|s)?\s*(\d[\d,]*)",
    r"award(?:ed|s)?\s*(\d[\d,]*)",
]
