"""
Defines the GameState class, which represents the complete state of a campaign.
"""
import datetime

class GameState:
    """A structured class to hold and manage all game state data."""
    
    def __init__(self, 
                 player_character_data: dict, 
                 world_data: dict, 
                 npc_data: dict, 
                 custom_campaign_state: dict,
                 game_state_version: int = 1,
                 last_state_update_timestamp=None):
        self.game_state_version = game_state_version
        self.player_character_data = player_character_data
        self.world_data = world_data
        self.npc_data = npc_data
        self.custom_campaign_state = custom_campaign_state
        self.last_state_update_timestamp = last_state_update_timestamp or datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> dict:
        """Serializes the GameState object to a dictionary for Firestore."""
        return {
            "game_state_version": self.game_state_version,
            "player_character_data": self.player_character_data,
            "world_data": self.world_data,
            "npc_data": self.npc_data,
            "custom_campaign_state": self.custom_campaign_state,
            "last_state_update_timestamp": self.last_state_update_timestamp
        }

    @classmethod
    def from_dict(cls, source: dict):
        """Creates a GameState object from a dictionary (e.g., from Firestore)."""
        if not source:
            return None
            
        return cls(
            player_character_data=source.get("player_character_data", {}),
            world_data=source.get("world_data", {}),
            npc_data=source.get("npc_data", {}),
            custom_campaign_state=source.get("custom_campaign_state", {}),
            game_state_version=source.get("game_state_version", 1),
            last_state_update_timestamp=source.get("last_state_update_timestamp")
        ) 
