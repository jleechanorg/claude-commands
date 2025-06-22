"""
Defines the GameState class, which represents the complete state of a campaign.
"""
import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field
from typing import Any, Dict, List

class MigrationStatus(Enum):
    NOT_CHECKED = "NOT_CHECKED"
    MIGRATED = "MIGRATED"
    NO_LEGACY_DATA = "NO_LEGACY_DATA"

@dataclass
class GameState:
    """Represents the entire state of a game campaign."""
    player_character_data: Dict[str, Any] = field(default_factory=dict)
    world_data: Dict[str, Any] = field(default_factory=dict)
    npc_data: Dict[str, Any] = field(default_factory=dict)
    custom_campaign_state: Dict[str, Any] = field(default_factory=dict)
    
    # Versioning and migration
    game_state_version: int = 1
    migration_status: str = "NOT_CHECKED"
    last_state_update_timestamp: Any = None # Can be datetime or Firestore Sentinel

    @classmethod
    def from_dict(cls, source: Dict[str, Any]):
        """Creates a GameState instance from a dictionary."""
        # A simple factory method to load from a dict.
        # You could add more complex logic here for version migration, etc.
        return cls(**source)

    def to_dict(self):
        """Converts the GameState instance to a dictionary."""
        # The dataclasses.asdict helper can be useful, but a simple dict comprehension
        # is often sufficient and more explicit.
        return {
            "player_character_data": self.player_character_data,
            "world_data": self.world_data,
            "npc_data": self.npc_data,
            "custom_campaign_state": self.custom_campaign_state,
            "game_state_version": self.game_state_version,
            "migration_status": self.migration_status,
            "last_state_update_timestamp": self.last_state_update_timestamp
        }

def get_initial_game_state():
    """
    Returns a blank, initial game state dictionary.
    The Gemini service is responsible for populating this.
    """
    return GameState().to_dict()
