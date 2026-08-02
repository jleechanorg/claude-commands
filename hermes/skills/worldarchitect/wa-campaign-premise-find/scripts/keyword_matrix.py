#!/usr/bin/env python3
"""Keyword expansion matrix for WA premise search. Verbatim from SKILL.md Phase 3."""
import re

KEYWORD_MATRIX = {
    "demon_lord":    re.compile(
        r"demon[- ]?lord|demon[- ]?king|demonlord|overlord|dark lord",
        re.IGNORECASE,
    ),
    "reincarnation": re.compile(
        r"reincarnat|reborn|past[- ]?life|previous[- ]?life|isekai",
        re.IGNORECASE,
    ),
    "isekai": re.compile(
        r"isekai|anime[- ]?style[- ]?reborn|reborn in a new world",
        re.IGNORECASE,
    ),
    "overpowered": re.compile(
        r"\bOP\b|over.?powered|god.?tier|level\s*[2-9]\d+|broken build|godlike|level\s*cap|special (class|abilities)|extra attack|prodigy|gestalt",
        re.IGNORECASE,
    ),
    "resurrected": re.compile(
        r"resurrect|return(ed)? from (the )?dead|back from the dead|raised (from the dead|back)|undead|lich|revived",
        re.IGNORECASE,
    ),
    "female_pc": re.compile(
        r"(make me|i am|let's make me|i play|play as|reborn as|reincarnat\w+ as).{0,30}(female|woman|girl|lady|witch|sorceress|goddess|succubus|demoness|queen|empress|princess|heiress|noblewoman)",
        re.IGNORECASE,
    ),
    "daughter_past": re.compile(
        r"daughter.*(past|previous).*life|child.*(past|previous).*life|your daughter survives|my child.*past|my daughter.*previous life|child.*life was in danger|daughter from a past life",
        re.IGNORECASE,
    ),
}


def build_search_regex(tropes):
    """Build a single grep alternation regex from a list of trope names."""
    parts = [KEYWORD_MATRIX[t].pattern for t in tropes if t in KEYWORD_MATRIX]
    return "|".join(parts) if parts else ""


def classify_god_mode(god_mode_text):
    """Return dict of trope_name -> bool for a single God Mode prompt block."""
    return {name: bool(pat.search(god_mode_text)) for name, pat in KEYWORD_MATRIX.items()}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: keyword_matrix.py <tropes...>")
        print("tropes:", list(KEYWORD_MATRIX.keys()))
        sys.exit(1)
    print(build_search_regex(sys.argv[1:]))
