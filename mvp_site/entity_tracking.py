"""
Entity tracking system for narrative generation
Using simple schemas from Milestone 0.4
NOTE: Pydantic validation not yet implemented - see roadmap/test_pydantic_vs_simple_plan.md
"""
from typing import List, Dict, Any
from schemas.entities_simple import (
    create_from_game_state as schemas_create_from_game_state,
    SceneManifest,
    EntityStatus,
    Visibility
)

# Re-export the classes and enums from schemas
__all__ = ['SceneManifest', 'EntityStatus', 'Visibility', 'create_from_game_state']

def create_from_game_state(game_state: Dict[str, Any], session_number: int, turn_number: int) -> SceneManifest:
    """
    Create a SceneManifest from game state using the schemas implementation.
    This is a wrapper to maintain backward compatibility with existing code.
    """
    return schemas_create_from_game_state(game_state, session_number, turn_number)