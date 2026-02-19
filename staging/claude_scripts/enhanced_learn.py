#!/usr/bin/env python3
"""
Simple enhanced /learn command that actually works
"""

import json
import re
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path.home() / ".cache" / "claude-learning"
MEMORY_FILE = MEMORY_DIR / "learning_memory.json"


def enhanced_learn(learning_content):
    """Enhanced learn function with pattern detection and storage"""

    # Ensure memory directory exists
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing memory
    memory = {}
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE) as f:
                memory = json.load(f)
        except:
            memory = {
                "entities": {},
                "relations": [],
                "stats": {"total_corrections": 0},
            }

    if "entities" not in memory:
        memory = {"entities": {}, "relations": [], "stats": {"total_corrections": 0}}

    if "stats" not in memory:
        memory["stats"] = {"total_corrections": 0}

    # Pattern detection
    patterns = [
        (r"don't\s+(.*?),\s*(.*)", "dont_do_instead"),
        (r"use\s+(.*?)\s+instead\s+of\s+(.*?)", "use_instead_of"),
        (r"i\s+prefer\s+(.*)", "preference"),
        (r"when\s+(.*?),\s*(.*)", "context_behavior"),
        (r"always\s+(.*)", "always_rule"),
        (r"never\s+(.*)", "never_rule"),
    ]

    # Context detection
    context_keywords = {
        "urgent": ["quick", "urgent", "asap", "fast"],
        "quality": ["careful", "thorough", "comprehensive"],
        "coding": ["function", "class", "import", "test", "code"],
        "review": ["pr", "review", "check"],
        "workflow": ["command", "process", "commit"],
    }

    detected_contexts = []
    text_lower = learning_content.lower()
    for context, keywords in context_keywords.items():
        if any(kw in text_lower for kw in keywords):
            detected_contexts.append(context)

    if not detected_contexts:
        detected_contexts = ["general"]

    # Find corrections
    corrections_found = []
    for pattern, correction_type in patterns:
        matches = re.findall(pattern, learning_content, re.IGNORECASE)
        for match in matches:
            corrections_found.append(
                {"type": correction_type, "match": match, "text": learning_content}
            )

    # Store corrections
    if corrections_found:
        for i, correction in enumerate(corrections_found):
            # Unique ID with microseconds to avoid collisions
            entity_id = f"correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"

            memory["entities"][entity_id] = {
                "id": entity_id,
                "type": "user_correction",
                "correction_type": correction["type"],
                "pattern": correction["match"],
                "original_text": correction["text"],
                "context": detected_contexts,
                "confidence": 0.8,
                "created": datetime.now().isoformat(),
                "applied_count": 0,
                "success_count": 0,
            }

            memory["stats"]["total_corrections"] += 1
    else:
        # Store as general observation
        entity_id = f"observation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        memory["entities"][entity_id] = {
            "id": entity_id,
            "type": "general_observation",
            "content": learning_content,
            "context": detected_contexts,
            "created": datetime.now().isoformat(),
        }

    # Save memory
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

    # Return results
    total_corrections = memory["stats"]["total_corrections"]
    corrections_count = len(corrections_found)

    if corrections_found:
        return f"✅ Stored {corrections_count} correction(s). Total corrections in memory: {total_corrections}"
    return f"✅ Stored observation. Total corrections in memory: {total_corrections}"


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        content = " ".join(sys.argv[1:])
        result = enhanced_learn(content)
        print(result)
    else:
        print("Usage: python enhanced_learn.py 'learning content'")
