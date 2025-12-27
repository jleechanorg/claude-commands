"""
Entity Tracking System

This module provides entity tracking capabilities for narrative generation, ensuring that
characters, NPCs, and other entities are properly tracked and validated during story generation.
The system uses Pydantic validation for robust schema enforcement and data integrity.

Key Features:
- Scene manifest creation from game state
- Entity status tracking (active, inactive, mentioned)
- Visibility management (visible, hidden, off-screen)
- Pydantic-based validation for data integrity
- Integration with AI narrative generation

Architecture:
- Wrapper around Pydantic schemas for entity validation
- Game state integration for entity discovery
- Scene-based entity tracking with turn/session context
- Enumerated status and visibility states

Usage:
    # Create scene manifest from game state
    manifest = create_from_game_state(game_state, session_number, turn_number)

    # Get validation information
    info = get_validation_info()

    # Access entity data
    entities = manifest.get_expected_entities()

Note: This module acts as a bridge between the core application and the Pydantic-based
entity schemas, providing a stable API while delegating validation to the schemas module.
"""

from typing import Any

# Import from Pydantic schemas (entities_simple.py was removed)
from mvp_site.schemas.entities_pydantic import (
    EntityStatus,
    SceneManifest,
    Visibility,
    create_from_game_state as schemas_create_from_game_state,
)

VALIDATION_TYPE = "Pydantic"

# Re-export the classes and enums from schemas
__all__ = [
    "SceneManifest",
    "EntityStatus",
    "Visibility",
    "create_from_game_state",
    "VALIDATION_TYPE",
]


def create_from_game_state(
    game_state: dict[str, Any], session_number: int, turn_number: int
) -> SceneManifest:
    """
    Create a SceneManifest from game state using Pydantic validation.
    """
    return schemas_create_from_game_state(game_state, session_number, turn_number)


def get_validation_info() -> dict[str, str]:
    """Get information about the current validation approach"""
    return {"validation_type": VALIDATION_TYPE, "pydantic_available": "true"}
