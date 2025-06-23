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
        narrative_lower = narrative_text.lower()
        
        # Check player character HP consistency
        if 'player_character_data' in self.__dict__:
            pc_data = self.player_character_data
            hp_current = pc_data.get('hp_current')
            hp_max = pc_data.get('hp_max')
            
            if hp_current is not None and hp_max is not None:
                # Check for unconscious/death vs HP mismatch
                if 'unconscious' in narrative_lower or 'lies unconscious' in narrative_lower:
                    if hp_current > 0:
                        discrepancies.append(f"Narrative mentions unconsciousness but HP is {hp_current}/{hp_max}")
                
                if any(phrase in narrative_lower for phrase in ['completely drained', 'drained of life']):
                    if hp_current > 5:  # Should be very low if "drained of life"
                        discrepancies.append(f"Narrative describes being drained of life but HP is {hp_current}/{hp_max}")
                
                hp_percentage = (hp_current / hp_max) * 100
                
                # Check for narrative/state HP mismatches
                if hp_percentage < 25:  # Critically wounded
                    if not any(word in narrative_lower for word in ['wounded', 'injured', 'hurt', 'bleeding', 'pain', 'unconscious']):
                        discrepancies.append(f"State shows character critically wounded ({hp_current}/{hp_max} HP) but narrative doesn't reflect injury")
                elif hp_percentage > 90:  # Healthy
                    if any(word in narrative_lower for word in ['wounded', 'injured', 'bleeding', 'dying', 'unconscious']):
                        discrepancies.append(f"Narrative describes character as injured but state shows healthy ({hp_current}/{hp_max} HP)")
        
        # Check location consistency
        current_location = self.world_data.get('current_location_name') or self.world_data.get('current_location')
        if current_location:
            # Check for explicit location mismatches
            location_lower = current_location.lower()
            
            # If narrative mentions being in a specific place that doesn't match state
            if 'forest' in narrative_lower and 'tavern' in location_lower:
                discrepancies.append(f"State location '{current_location}' conflicts with narrative mentioning forest")
            elif 'tavern' in narrative_lower and 'forest' in location_lower:
                discrepancies.append(f"State location '{current_location}' conflicts with narrative mentioning tavern")
            
            # General location mismatch detection
            if any(phrase in narrative_lower for phrase in ['standing in', 'in the middle of', 'surrounded by']):
                location_words = location_lower.split()
                if len(location_words) > 0 and not any(word in narrative_lower for word in location_words):
                    discrepancies.append(f"State location '{current_location}' may not match narrative location references")
        
        # Check active missions consistency
        active_missions = self.custom_campaign_state.get('active_missions', [])
        if active_missions:
            for mission in active_missions:
                if isinstance(mission, dict):
                    mission_name = mission.get('name') or mission.get('title') or str(mission)
                else:
                    mission_name = str(mission)
                
                mission_lower = mission_name.lower()
                
                # Check for specific mission completion phrases
                if 'dragon' in mission_lower and any(phrase in narrative_lower for phrase in ['dragon finally defeated', 'dragon defeated']):
                    discrepancies.append(f"Mission '{mission_name}' appears completed in narrative but still active in state")
                
                if 'treasure' in mission_lower and any(phrase in narrative_lower for phrase in ['treasure secured', 'treasure found']):
                    discrepancies.append(f"Mission '{mission_name}' appears completed in narrative but still active in state")
                
                # General completion detection
                if any(phrase in narrative_lower for phrase in ['quest was complete', 'quest complete', 'mission complete']):
                    if any(word in mission_lower for word in narrative_lower.split()):
                        discrepancies.append(f"Mission '{mission_name}' may be completed in narrative but still active in state")
        
        return discrepancies

def get_initial_game_state():
    """
    Returns a blank, initial game state dictionary.
    The Gemini service is responsible for populating this.
    """
    return GameState().to_dict()
