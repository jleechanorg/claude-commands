"""
Entity Preloader - Backward Compatibility Shim

This module is maintained for backward compatibility.
All functionality has been consolidated into entity_instructions.py.

Import from mvp_site.entity_instructions for new code.
"""

from mvp_site.entity_instructions import (
    EntityPreloader,
    LocationEntityEnforcer,
    entity_preloader,
    location_enforcer,
)
from mvp_site.entity_tracking import SceneManifest, create_from_game_state

__all__ = [
    "EntityPreloader",
    "LocationEntityEnforcer",
    "entity_preloader",
    "location_enforcer",
    "SceneManifest",
    "create_from_game_state",
]
