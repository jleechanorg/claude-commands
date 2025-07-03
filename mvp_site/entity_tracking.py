"""
Entity tracking system for narrative generation
Supports both Simple and Pydantic validation approaches for comparison testing
"""
import os
from typing import List, Dict, Any

# Configuration for choosing validation approach
USE_PYDANTIC = os.getenv('USE_PYDANTIC', 'false').lower() == 'true'

if USE_PYDANTIC:
    try:
        from schemas.entities_pydantic import (
            create_from_game_state as schemas_create_from_game_state,
            SceneManifest,
            EntityStatus,
            Visibility
        )
        VALIDATION_TYPE = "Pydantic"
    except ImportError:
        print("Warning: Pydantic not available, falling back to Simple validation")
        from schemas.entities_simple import (
            create_from_game_state as schemas_create_from_game_state,
            SceneManifest,
            EntityStatus,
            Visibility
        )
        VALIDATION_TYPE = "Simple (Pydantic unavailable)"
else:
    from schemas.entities_simple import (
        create_from_game_state as schemas_create_from_game_state,
        SceneManifest,
        EntityStatus,
        Visibility
    )
    VALIDATION_TYPE = "Simple"

# Re-export the classes and enums from schemas
__all__ = ['SceneManifest', 'EntityStatus', 'Visibility', 'create_from_game_state', 'VALIDATION_TYPE']

def create_from_game_state(game_state: Dict[str, Any], session_number: int, turn_number: int) -> SceneManifest:
    """
    Create a SceneManifest from game state using the configured validation approach.
    
    Set USE_PYDANTIC=true environment variable to use Pydantic validation.
    Default is Simple validation for performance.
    """
    return schemas_create_from_game_state(game_state, session_number, turn_number)

def get_validation_info() -> Dict[str, str]:
    """Get information about the current validation approach"""
    return {
        "validation_type": VALIDATION_TYPE,
        "use_pydantic": str(USE_PYDANTIC),
        "pydantic_available": "true" if USE_PYDANTIC else "depends_on_import"
    }