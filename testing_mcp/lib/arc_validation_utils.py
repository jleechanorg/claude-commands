"""
Shared utilities for companion arc validation and companion detection.

This module provides centralized functions for:
- Validating companion arc structures (handling dual structure system)
- Detecting companions from multiple storage locations
- Extracting companion arcs and events from game state
"""

from typing import Any


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
        for name in campaign_companions.keys():
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
