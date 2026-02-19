#!/usr/bin/env python3
"""
Query learned patterns from memory
"""

import json
from pathlib import Path

MEMORY_FILE = Path.home() / ".cache" / "claude-learning" / "learning_memory.json"


def query_patterns(context_keywords=None, correction_type=None):
    """Query relevant patterns from memory"""

    if not MEMORY_FILE.exists():
        return "No memory file found. Use /learn to start building memory."

    try:
        with open(MEMORY_FILE) as f:
            memory = json.load(f)
    except:
        return "Error reading memory file."

    entities = memory.get("entities", {})
    corrections = [e for e in entities.values() if e.get("type") == "user_correction"]

    if not corrections:
        return "No corrections found in memory."

    # Filter by context if provided
    if context_keywords:
        context_keywords = [kw.lower() for kw in context_keywords]
        filtered = []
        for correction in corrections:
            correction_contexts = [ctx.lower() for ctx in correction.get("context", [])]
            if any(kw in correction_contexts for kw in context_keywords):
                filtered.append(correction)
        corrections = filtered

    # Filter by type if provided
    if correction_type:
        corrections = [
            c for c in corrections if c.get("correction_type") == correction_type
        ]

    if not corrections:
        return f"No matching patterns found for context: {context_keywords}, type: {correction_type}"

    # Sort by confidence
    corrections.sort(key=lambda x: x.get("confidence", 0), reverse=True)

    # Format results
    results = [f"📝 Found {len(corrections)} relevant pattern(s):"]

    for i, correction in enumerate(corrections[:5], 1):  # Show top 5
        pattern_text = correction.get("pattern")
        if isinstance(pattern_text, list):
            pattern_text = " → ".join(pattern_text)

        confidence = correction.get("confidence", 0)
        contexts = ", ".join(correction.get("context", []))
        correction_type = correction.get("correction_type", "unknown")

        results.append(f"{i}. {pattern_text}")
        results.append(
            f"   Type: {correction_type}, Confidence: {confidence:.1f}, Context: {contexts}"
        )

    return "\n".join(results)


def get_memory_summary():
    """Get summary of what's in memory"""

    if not MEMORY_FILE.exists():
        return "No memory file found."

    try:
        with open(MEMORY_FILE) as f:
            memory = json.load(f)
    except:
        return "Error reading memory file."

    entities = memory.get("entities", {})
    memory.get("stats", {})

    corrections = [e for e in entities.values() if e.get("type") == "user_correction"]
    observations = [
        e for e in entities.values() if e.get("type") == "general_observation"
    ]

    # Count by type
    correction_types = {}
    contexts = {}

    for correction in corrections:
        ctype = correction.get("correction_type", "unknown")
        correction_types[ctype] = correction_types.get(ctype, 0) + 1

        for ctx in correction.get("context", []):
            contexts[ctx] = contexts.get(ctx, 0) + 1

    results = [
        "📊 Memory Summary:",
        f"Total corrections: {len(corrections)}",
        f"Total observations: {len(observations)}",
        "",
        "Correction types:",
    ]

    for ctype, count in sorted(correction_types.items()):
        results.append(f"  {ctype}: {count}")

    results.append("\nContexts:")
    for ctx, count in sorted(contexts.items()):
        results.append(f"  {ctx}: {count}")

    return "\n".join(results)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "summary":
            print(get_memory_summary())
        else:
            # Query by context keywords
            keywords = sys.argv[1:]
            result = query_patterns(context_keywords=keywords)
            print(result)
    else:
        print("Usage:")
        print("  python query_patterns.py summary")
        print("  python query_patterns.py coding urgent")
        print("  python query_patterns.py workflow")
