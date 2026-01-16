"""
Shared utilities for companion arc validation and companion detection.

This module provides centralized functions for:
- Validating companion arc structures (handling dual structure system)
- Detecting companions from multiple storage locations
- Extracting companion arcs and events from game state
- Narrative validation (companion mentions, arc themes, dialogue)
"""

import re


def extract_companion_arcs(game_state: dict) -> dict:
    """Extract companion_arcs from game_state."""
    custom_state = game_state.get("custom_campaign_state", {})
    return custom_state.get("companion_arcs", {})


def extract_companion_arc_event(action_data: dict) -> dict | None:
    """Extract companion_arc_event from action response."""
    game_state = action_data.get("game_state", {})
    custom_state = game_state.get("custom_campaign_state", {})
    return custom_state.get("companion_arc_event")


def extract_next_companion_arc_turn(game_state: dict) -> int | None:
    """Extract next_companion_arc_turn from game_state."""
    custom_state = game_state.get("custom_campaign_state", {})
    return custom_state.get("next_companion_arc_turn")


def validate_arc_structure(arc: dict, arc_name: str) -> tuple[bool, list[str]]:
    """Validate companion arc structure.

    Handles two arc structure types:
    1. Arc definition (arc_<id>): Contains metadata like companion_id, objectives, title
    2. Arc state (npc_<id> or companion_name): Contains progression like phase, progress, history

    Only validates arc states (those with phase/progress), not definitions.

    Args:
        arc: Arc data dictionary
        arc_name: Name/key of the arc in companion_arcs

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Skip validation for arc definitions (keys starting with "arc_" that don't have phase/progress)
    if arc_name.startswith("arc_") and "phase" not in arc and "progress" not in arc:
        # This is an arc definition/metadata structure, not an active arc state
        # Return True (valid) but don't require arc_type/phase/progress
        return True, []

    # For arc states, require phase and progress (arc_type is optional but preferred)
    required_fields = ["phase", "progress"]
    for field in required_fields:
        if field not in arc:
            errors.append(f"Missing required field: {field}")

    # arc_type is preferred but not strictly required (can be inferred)
    if "arc_type" not in arc:
        # Warning but not error - arc_type can be missing if not set by LLM
        pass

    if "phase" in arc:
        valid_phases = ["discovery", "development", "crisis", "resolution"]
        if arc["phase"] not in valid_phases:
            errors.append(f"Invalid phase: {arc['phase']} (must be one of {valid_phases})")

    if "progress" in arc:
        progress = arc["progress"]
        if not isinstance(progress, (int, float)) or progress < 0 or progress > 100:
            errors.append(f"Invalid progress: {progress} (must be 0-100)")

    return len(errors) == 0, errors


def detect_companions(game_state: dict, initial_arcs: dict | None = None) -> list[str]:
    """Detect companions from multiple storage locations.

    Checks:
    1. npc_data (with relationship == "companion")
    2. custom_campaign_state.companions
    3. active_entities (type == "companion")
    4. Extract from arc structures (companion_id field, npc_<name> pattern)

    Args:
        game_state: Full game state dictionary
        initial_arcs: Optional initial companion_arcs dict for fallback extraction

    Returns:
        List of companion names/IDs found
    """
    companions = []

    # Check npc_data
    npc_data = game_state.get("npc_data", {})
    for name, npc in npc_data.items():
        if isinstance(npc, dict) and npc.get("relationship") == "companion":
            if name not in companions:
                companions.append(name)

    # Check custom_campaign_state.companions
    custom_state = game_state.get("custom_campaign_state", {})
    campaign_companions = custom_state.get("companions", {})
    if isinstance(campaign_companions, dict):
        for name in campaign_companions:
            if name not in companions:
                companions.append(name)

    # Check active_entities for companion references
    active_entities = game_state.get("active_entities", {})
    if isinstance(active_entities, dict):
        for entity_id, entity_data in active_entities.items():
            if isinstance(entity_data, dict):
                entity_type = entity_data.get("type", "")
                if entity_type == "companion" and entity_id not in companions:
                    companions.append(entity_id)

    # Extract companion names from arc structures (fallback)
    if not companions and initial_arcs:
        for arc_name, arc_data in initial_arcs.items():
            if isinstance(arc_data, dict):
                # Check companion_id field
                companion_id = arc_data.get("companion_id", "")
                if companion_id and companion_id not in companions:
                    companions.append(companion_id)
                # Check if arc_name itself is a companion name (npc_<name> pattern)
                if arc_name.startswith("npc_") and arc_name not in companions:
                    # Extract companion name (remove npc_ prefix)
                    comp_name = arc_name.replace("npc_", "").replace("_", " ")
                    if comp_name and comp_name not in companions:
                        companions.append(comp_name)

    return companions


def filter_arc_states(companion_arcs: dict) -> dict:
    """Filter companion_arcs to only include arc states (not definitions).

    Arc definitions (arc_<id>) are metadata structures without phase/progress.
    Arc states (npc_<id> or companion names) have phase/progress fields.

    Args:
        companion_arcs: Full companion_arcs dictionary

    Returns:
        Dictionary containing only arc states (filtered definitions)
    """
    arc_states = {}
    for arc_name, arc_data in companion_arcs.items():
        if not isinstance(arc_data, dict):
            continue
        # Skip arc definitions (arc_<id> without phase/progress)
        if arc_name.startswith("arc_") and "phase" not in arc_data and "progress" not in arc_data:
            continue
        # Include arc states (have phase/progress)
        arc_states[arc_name] = arc_data
    return arc_states


# Narrative validation functions

def extract_narrative(action_response: dict) -> str:
    """Extract narrative text from action response."""
    return action_response.get("narrative", "") or action_response.get("response", "")


def find_companions_in_narrative(
    narrative: str, expected_companions: list[str] | None = None
) -> list[str]:
    """Find companion names mentioned in narrative.

    Args:
        narrative: The narrative text to search
        expected_companions: List of companion names to search for (optional)

    Returns:
        List of companion names found in the narrative
    """
    companions_found = []

    # Common companion name patterns (fallback if expected_companions not provided)
    common_names = ["Lyra", "Marcus", "Elara", "Thorin", "Aria", "Kael", "Sariel", "Luna", "Zara"]

    # Use expected companions if provided, otherwise use common names
    names_to_check = expected_companions if expected_companions else common_names

    for name in names_to_check:
        # Check for full name or first name only
        name_parts = name.split()
        first_name = name_parts[0] if name_parts else name
        if name.lower() in narrative.lower() or first_name.lower() in narrative.lower():
            companions_found.append(name)

    # Look for dialogue quotes that might indicate companion speech
    # Pattern: "text" said Name or Name says "text"
    dialogue_pattern = r'["""]([^"""]+)["""]\s*(?:said|says|whispered|asked|exclaimed)\s+([A-Z][a-z]+)'
    matches = re.findall(dialogue_pattern, narrative, re.IGNORECASE)
    for match in matches:
        if match[1] not in companions_found:
            companions_found.append(match[1])

    return companions_found


def find_arc_themes_in_narrative(narrative: str, arc_type: str) -> bool:
    """Check if narrative contains themes related to the arc type.

    Args:
        narrative: The narrative text to search
        arc_type: The type of arc (e.g., "lost_family", "personal_redemption")

    Returns:
        True if at least 2 theme keywords are found
    """
    arc_themes = {
        "lost_family": ["sister", "brother", "family", "missing", "search", "find", "relative"],
        "personal_redemption": ["mistake", "wrong", "atonement", "forgive", "redemption", "past"],
        "rival_nemesis": ["rival", "enemy", "hunt", "hunted", "nemesis", "conflict"],
        "forbidden_love": ["love", "romance", "secret", "forbidden", "heart", "feelings"],
        "dark_secret": ["secret", "hidden", "dangerous", "reveal", "truth", "conceal"],
        "homeland_crisis": ["home", "village", "town", "crisis", "danger", "threat", "save"],
        "mentor_legacy": ["mentor", "teacher", "legacy", "unfinished", "continue", "honor"],
        "prophetic_destiny": ["prophecy", "destiny", "fate", "marked", "chosen", "vision"],
    }

    themes = arc_themes.get(arc_type, [])
    narrative_lower = narrative.lower()

    # Check if at least 2 themes appear in narrative
    matches = sum(1 for theme in themes if theme in narrative_lower)
    return matches >= 2


def validate_companion_dialogue_in_narrative(narrative: str, arc_event: dict) -> bool:
    """Validate that companion dialogue from arc_event appears in narrative.

    Args:
        narrative: The narrative text to search
        arc_event: The companion arc event containing dialogue

    Returns:
        True if at least 30% of dialogue words appear in narrative
    """
    if not arc_event:
        return False

    companion_dialogue = arc_event.get("companion_dialogue", "")

    if not companion_dialogue:
        return False

    # Check if dialogue appears in narrative (allowing for minor variations)
    dialogue_words = set(companion_dialogue.lower().split())
    narrative_words = set(narrative.lower().split())

    # If at least 30% of dialogue words appear in narrative, consider it present
    if len(dialogue_words) > 0:
        overlap = len(dialogue_words.intersection(narrative_words))
        overlap_ratio = overlap / len(dialogue_words)
        return overlap_ratio >= 0.3

    return False


def validate_arc_event_structure(event: dict) -> tuple[bool, list[str]]:
    """Validate companion_arc_event structure.

    Args:
        event: The companion arc event dictionary

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    required_fields = ["companion", "arc_type", "phase", "event_type", "description", "companion_dialogue"]
    for field in required_fields:
        if field not in event:
            errors.append(f"Missing required field: {field}")

    if "phase" in event:
        valid_phases = ["discovery", "development", "crisis", "resolution"]
        if event["phase"] not in valid_phases:
            errors.append(f"Invalid phase: {event['phase']}")

    # Validate event_type against allowed values
    if "event_type" in event:
        valid_event_types = [
            "hook_introduced",
            "stakes_raised",
            "complication",
            "revelation",
            "confrontation",
            "arc_complete",
        ]
        if event["event_type"] not in valid_event_types:
            errors.append(
                f"Invalid event_type: {event['event_type']}. "
                f"Must be one of: {', '.join(valid_event_types)}"
            )

    # Validate companion_dialogue is present and non-empty (REQUIRED per instruction)
    if "companion_dialogue" in event:
        companion_dialogue = event["companion_dialogue"]
        if not companion_dialogue or not isinstance(companion_dialogue, str) or not companion_dialogue.strip():
            errors.append("companion_dialogue is REQUIRED and must be a non-empty string")

    # Strict mode: require callback_planted for non-resolution phases
    if event.get("phase") != "resolution" and "callback_planted" not in event:
        errors.append("Missing callback_planted (MUST plant at least one callback)")

    return len(errors) == 0, errors
