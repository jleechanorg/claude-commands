#!/usr/bin/env python3
"""
Debug script to demonstrate the STATE_UPDATES_PROPOSED issue and fix.

This script shows:
1. The old behavior (parsing STATE_UPDATES_PROPOSED from markdown)
2. The new behavior (using structured JSON response)
3. How the fix handles both cases
"""

import json
import re
from dataclasses import dataclass
from typing import Any


# Simulate the old parse_llm_response_for_state_changes function
def parse_llm_response_for_state_changes(llm_text_response: str) -> dict:
    """Old function that parses STATE_UPDATES_PROPOSED blocks from markdown."""
    matches = re.findall(
        r"\[STATE_UPDATES_PROPOSED\](.*?)\[END_STATE_UPDATES_PROPOSED\]",
        llm_text_response,
        re.DOTALL,
    )

    if not matches:
        print("⚠️ No STATE_UPDATES_PROPOSED block found in response!")
        return {}

    for json_string in reversed(matches):
        json_string = json_string.strip()
        if not json_string:
            continue

        try:
            proposed_changes = json.loads(json_string)
            if isinstance(proposed_changes, dict):
                print("✓ Found STATE_UPDATES_PROPOSED block with state updates")
                return proposed_changes
        except json.JSONDecodeError:
            print(
                f"✗ Found STATE_UPDATES_PROPOSED but invalid JSON: {json_string[:50]}..."
            )

    return {}


# Simulate structured response classes
@dataclass
class MockStructuredResponse:
    state_updates: dict[str, Any]
    narrative: str
    debug_info: dict[str, Any]


@dataclass
class MockGeminiResponse:
    narrative_text: str
    structured_response: MockStructuredResponse | None

    @property
    def state_updates(self) -> dict[str, Any]:
        """Get state updates from structured response."""
        if self.structured_response:
            return self.structured_response.state_updates
        return {}


def demonstrate_issue():
    """Demonstrate the issue with STATE_UPDATES_PROPOSED parsing."""

    print("=== Demonstrating STATE_UPDATES_PROPOSED Issue ===\n")

    # Case 1: Old markdown format (what the parser expects)
    print("1. Old Format (Markdown with STATE_UPDATES_PROPOSED):")
    old_format_response = """[Mode: STORY MODE]
[SESSION_HEADER]
Location: Dungeon
HP: 15/28

You strike the goblin!

[STATE_UPDATES_PROPOSED]
{
    "player_character_data": {
        "hp_current": 15
    },
    "npc_data": {
        "Goblin": {
            "hp_current": 0
        }
    }
}
[END_STATE_UPDATES_PROPOSED]

--- PLANNING BLOCK ---
What next?"""

    state_updates = parse_llm_response_for_state_changes(old_format_response)
    print(f"   State updates found: {json.dumps(state_updates, indent=2)}\n")

    # Case 2: New JSON format (no STATE_UPDATES_PROPOSED blocks)
    print("2. New Format (JSON mode, no STATE_UPDATES_PROPOSED):")
    new_format_response = """[Mode: STORY MODE]
[SESSION_HEADER]
Location: Dungeon
HP: 15/28

You strike the goblin!

--- PLANNING BLOCK ---
What next?"""

    state_updates = parse_llm_response_for_state_changes(new_format_response)
    print(f"   State updates found: {state_updates}")
    print(
        "   ❌ This is the bug! State updates are in structured response, not markdown!\n"
    )

    # Case 3: Show the fix
    print("3. The Fix (using structured response):")

    # Create a mock structured response with state updates
    structured = MockStructuredResponse(
        state_updates={
            "player_character_data": {"hp_current": 15},
            "npc_data": {"Goblin": {"hp_current": 0, "status": "defeated"}},
        },
        narrative=new_format_response,
        debug_info={"dm_notes": ["Goblin defeated"]},
    )

    gemini_response = MockGeminiResponse(
        narrative_text=new_format_response, structured_response=structured
    )

    # Old way (broken)
    print("   Old way (parse markdown):")
    old_way = parse_llm_response_for_state_changes(gemini_response.narrative_text)
    print(f"   Result: {old_way}")

    # New way (fixed)
    print("\n   New way (use structured response):")
    new_way = gemini_response.state_updates
    print(f"   Result: {json.dumps(new_way, indent=2)}")
    print("   ✅ State updates successfully extracted!\n")

    # Show the fixed code logic
    print("4. Fixed Code Logic:")
    print("""
    # Old code (line 874 in main.py):
    proposed_changes = gemini_service.parse_llm_response_for_state_changes(gemini_response_obj.narrative_text)

    # Fixed code:
    if gemini_response_obj.structured_response:
        proposed_changes = gemini_response_obj.state_updates
    else:
        # Fallback to old markdown parsing if no structured response
        proposed_changes = gemini_service.parse_llm_response_for_state_changes(gemini_response_obj.narrative_text)
    """)


if __name__ == "__main__":
    demonstrate_issue()
