"""
Defines the GameState class, which represents the complete state of a campaign.
"""
import datetime
from enum import Enum
from typing import Optional
import logging

class MigrationStatus(Enum):
    """Enum for the migration status of the game state."""
    NOT_CHECKED = "NOT_CHECKED"
    MIGRATION_PENDING = "MIGRATION_PENDING"
    MIGRATED = "MIGRATED"
    NO_LEGACY_DATA = "NO_LEGACY_DATA"

class GameState:
    """
    A class to hold and manage game state data, behaving like a flexible dictionary.
    """
    def __init__(self, **kwargs):
        """Initializes the GameState object with arbitrary data."""
        # Set default values for core attributes if they are not provided
        self.game_state_version = kwargs.get("game_state_version", 1)
        self.player_character_data = kwargs.get("player_character_data", {})
        self.world_data = kwargs.get("world_data", {})
        self.npc_data = kwargs.get("npc_data", {})
        self.custom_campaign_state = kwargs.get("custom_campaign_state", {})
        self.last_state_update_timestamp = kwargs.get("last_state_update_timestamp", datetime.datetime.now(datetime.timezone.utc))
        
        migration_status_value = kwargs.get("migration_status", MigrationStatus.NOT_CHECKED.value)
        try:
            self.migration_status = MigrationStatus(migration_status_value)
        except ValueError:
            self.migration_status = MigrationStatus.NOT_CHECKED

        # Dynamically set any other attributes from kwargs
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        """Serializes the GameState object to a dictionary for Firestore."""
        # Copy all attributes from the instance's __dict__
        data = self.__dict__.copy()
        
        # Convert Enum members to their string values for serialization
        if 'migration_status' in data and isinstance(data['migration_status'], MigrationStatus):
            data['migration_status'] = data['migration_status'].value
            
        return data

    @classmethod
    def from_dict(cls, source: dict):
        """Creates a GameState object from a dictionary (e.g., from Firestore)."""
        if not source:
            return None
        
        # The constructor now directly accepts the dictionary.
        return cls(**source)

    def validate_checkpoint_consistency(self, narrative_text: str) -> list:
        """
        Validates that critical checkpoint data in the state matches references in the narrative.
        Returns a list of discrepancies found.
        
        Args:
            narrative_text: The latest narrative content from the AI
            
        Returns:
            List of discrepancy descriptions, empty if no issues found
        """
        discrepancies = []
        
        # Check player character HP consistency
        if 'player_character_data' in self.__dict__:
            pc_data = self.player_character_data
            hp_current = pc_data.get('hp_current')
            hp_max = pc_data.get('hp_max')
            
            if hp_current is not None and hp_max is not None:
                hp_percentage = (hp_current / hp_max) * 100
                
                # Check for narrative/state HP mismatches
                if hp_percentage < 25:  # Critically wounded
                    if not any(word in narrative_text.lower() for word in ['wounded', 'injured', 'hurt', 'bleeding', 'pain']):
                        discrepancies.append(f"State shows character critically wounded ({hp_current}/{hp_max} HP) but narrative doesn't reflect injury")
                elif hp_percentage > 90:  # Healthy
                    if any(word in narrative_text.lower() for word in ['wounded', 'injured', 'bleeding', 'dying']):
                        discrepancies.append(f"Narrative describes character as injured but state shows healthy ({hp_current}/{hp_max} HP)")
        
        # Check location consistency
        current_location = self.world_data.get('current_location')
        if current_location:
            # Simple check - if location is mentioned in state but narrative talks about being elsewhere
            location_words = current_location.lower().split()
            if len(location_words) > 0 and not any(word in narrative_text.lower() for word in location_words):
                # Only flag if narrative explicitly mentions being in a different place
                if any(phrase in narrative_text.lower() for phrase in ['you are in', 'you find yourself in', 'you arrive at']):
                    discrepancies.append(f"State location '{current_location}' may not match narrative location references")
        
        # Check active missions consistency
        active_missions = self.custom_campaign_state.get('active_missions', [])
        if active_missions:
            for mission in active_missions:
                if isinstance(mission, dict):
                    mission_name = mission.get('name') or mission.get('title') or str(mission)
                else:
                    mission_name = str(mission)
                
                # If mission is marked as completed in narrative but still active in state
                if 'complet' in narrative_text.lower() and mission_name.lower() in narrative_text.lower():
                    discrepancies.append(f"Mission '{mission_name}' may be completed in narrative but still active in state")
        
        return discrepancies

def get_initial_game_state():
    """
    Returns a blank, initial game state dictionary.
    The Gemini service is responsible for populating this.
    """
    return GameState().to_dict()
