#!/usr/bin/env python3
"""
Enhanced /learn command with Memory MCP integration
Fallback to local JSON storage if Memory MCP has permission issues
"""

import json
import re
from datetime import datetime
from pathlib import Path

# Memory storage path
MEMORY_DIR = Path.home() / ".cache" / "claude-learning"
MEMORY_FILE = MEMORY_DIR / "learning_memory.json"


def ensure_memory_dir():
    """Create memory directory if it doesn't exist"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def load_memory():
    """Load existing memory or create empty structure"""
    ensure_memory_dir()
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    return {
        "entities": {},
        "relations": [],
        "corrections": [],
        "metadata": {"created": datetime.now().isoformat(), "version": "1.0"},
    }


def save_memory(memory_data):
    """Save memory to local file"""
    ensure_memory_dir()
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory_data, f, indent=2)


def detect_correction_patterns(text):
    """Detect correction patterns in user text"""
    patterns = [
        (r"don't\s+(.*?),\s*(.*)", "dont_do_instead"),
        (r"use\s+(.*?)\s+instead\s+of\s+(.*?)", "use_instead_of"),
        (r"i\s+prefer\s+(.*)", "preference"),
        (r"when\s+(.*?),\s*(.*)", "context_behavior"),
        (r"always\s+(.*)", "always_rule"),
        (r"never\s+(.*)", "never_rule"),
        (r"actually,?\s+(.*)", "correction"),
        (r"(?:wrong|incorrect|mistake).*?should\s+be\s+(.*)", "mistake_fix"),
    ]

    corrections = []
    text_lower = text.lower()

    for pattern, correction_type in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            corrections.append(
                {
                    "type": correction_type,
                    "match": match if isinstance(match, tuple) else (match,),
                    "original_text": text,
                    "confidence": 0.8,
                }
            )

    return corrections


def detect_context(text):
    """Detect context indicators in the text"""
    context_indicators = {
        "urgent": ["quick", "urgent", "asap", "immediately", "fast", "rush"],
        "quality": ["careful", "thorough", "comprehensive", "detailed"],
        "coding": ["function", "class", "variable", "import", "test", "code"],
        "review": ["pr", "review", "check", "verify", "approve"],
        "workflow": ["command", "process", "step", "procedure"],
        "testing": ["test", "testing", "spec", "coverage"],
        "documentation": ["docs", "readme", "documentation", "comment"],
    }

    detected_contexts = []
    text_lower = text.lower()

    for context, keywords in context_indicators.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_contexts.append(context)

    return detected_contexts if detected_contexts else ["general"]


def store_correction_local(correction, context):
    """Store correction in local memory file"""
    memory = load_memory()

    entity_id = f"correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    entity = {
        "id": entity_id,
        "type": "user_correction",
        "correction_type": correction["type"],
        "pattern": correction["match"],
        "original_text": correction["original_text"],
        "context": context,
        "confidence": correction["confidence"],
        "created": datetime.now().isoformat(),
        "applied_count": 0,
        "success_count": 0,
    }

    memory["entities"][entity_id] = entity
    memory["corrections"].append(entity_id)

    # Add relation to user
    memory["relations"].append(
        {
            "from": "jleechan2015",
            "to": entity_id,
            "type": "corrected_with",
            "created": datetime.now().isoformat(),
        }
    )

    save_memory(memory)
    return entity_id


def store_observation_local(content, context):
    """Store general observation in local memory"""
    memory = load_memory()

    entity_id = f"observation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    entity = {
        "id": entity_id,
        "type": "general_observation",
        "content": content,
        "context": context,
        "created": datetime.now().isoformat(),
    }

    memory["entities"][entity_id] = entity
    save_memory(memory)
    return entity_id


def query_relevant_patterns(current_context, _action_type=None):
    """Query memory for relevant patterns"""
    memory = load_memory()
    relevant_patterns = []

    for entity_id, entity in memory["entities"].items():
        if entity["type"] == "user_correction":
            # Check context overlap
            entity_contexts = entity.get("context", [])
            if any(ctx in current_context for ctx in entity_contexts):
                if entity["confidence"] > 0.6:  # High confidence threshold
                    relevant_patterns.append(entity)

    return relevant_patterns


def update_pattern_confidence(entity_id, adjustment):
    """Update pattern confidence based on success/failure"""
    memory = load_memory()

    if entity_id in memory["entities"]:
        entity = memory["entities"][entity_id]
        entity["confidence"] = max(0.0, min(1.0, entity["confidence"] + adjustment))
        entity["last_updated"] = datetime.now().isoformat()

        if adjustment > 0:
            entity["success_count"] = entity.get("success_count", 0) + 1

        entity["applied_count"] = entity.get("applied_count", 0) + 1

        save_memory(memory)


def enhanced_learn(learning_content):
    """Main enhanced learn function"""

    # Detect context
    context = detect_context(learning_content)

    # Detect correction patterns
    corrections = detect_correction_patterns(learning_content)

    results = []

    if corrections:
        # Store each correction
        for correction in corrections:
            entity_id = store_correction_local(correction, context)
            results.append(
                f"✅ Stored correction: {correction['type']} (ID: {entity_id})"
            )
    else:
        # Store as general observation
        entity_id = store_observation_local(learning_content, context)
        results.append(f"✅ Stored observation (ID: {entity_id})")

    # Show memory stats
    memory = load_memory()
    total_corrections = len(
        [e for e in memory["entities"].values() if e["type"] == "user_correction"]
    )

    results.append(f"📊 Total corrections in memory: {total_corrections}")

    return "\n".join(results)


def apply_memory_patterns(current_context):
    """Apply relevant patterns from memory"""
    patterns = query_relevant_patterns(current_context)

    if not patterns:
        return "📝 No relevant patterns found in memory"

    guidance = ["📝 Applying learned patterns:"]
    for pattern in patterns:
        rule_text = f"Type: {pattern['correction_type']}, Confidence: {pattern['confidence']:.1f}"
        guidance.append(f"• {rule_text}")

    return "\n".join(guidance)


def get_memory_stats():
    """Get memory statistics"""
    memory = load_memory()

    stats = {
        "total_entities": len(memory["entities"]),
        "corrections": len(
            [e for e in memory["entities"].values() if e["type"] == "user_correction"]
        ),
        "observations": len(
            [
                e
                for e in memory["entities"].values()
                if e["type"] == "general_observation"
            ]
        ),
        "relations": len(memory["relations"]),
    }

    return stats


if __name__ == "__main__":
    # Test the system
    test_inputs = [
        "Don't use global imports, use module-level imports instead",
        "I prefer structured commit messages with prefixes",
        "When urgent, focus on surgical fixes not comprehensive refactoring",
        "Always run tests before marking tasks complete",
    ]

    print("Testing Enhanced Learn System:")
    print("=" * 50)

    for test_input in test_inputs:
        print(f"\nInput: {test_input}")
        result = enhanced_learn(test_input)
        print(f"Result: {result}")

    print(f"\nMemory Stats: {get_memory_stats()}")

    print(f"\nMemory file location: {MEMORY_FILE}")
