"""
Entity tracking system for narrative generation
Uses Pydantic validation for robust schema enforcement
"""
from typing import Dict, Any

# Import from Pydantic schemas (entities_simple.py was removed)
from schemas.entities_pydantic import (
    create_from_game_state as schemas_create_from_game_state,
    SceneManifest,
    EntityStatus,
    Visibility
)
VALIDATION_TYPE = "Pydantic"

# Re-export the classes and enums from schemas
__all__ = ['SceneManifest', 'EntityStatus', 'Visibility', 'create_from_game_state', 'VALIDATION_TYPE']

def create_from_game_state(game_state: Dict[str, Any], session_number: int, turn_number: int) -> SceneManifest:
    """
    Create a SceneManifest from game state using Pydantic validation.
    """
    return schemas_create_from_game_state(game_state, session_number, turn_number)

def get_validation_info() -> Dict[str, str]:
    """Get information about the current validation approach"""
    return {
        "validation_type": VALIDATION_TYPE,
        "pydantic_available": "true"
    }