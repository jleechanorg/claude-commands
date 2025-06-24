"""
Defines the GameState class, which represents the complete state of a campaign.
"""
import datetime
from enum import Enum
from typing import Optional, List
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
        self.combat_state = kwargs.get("combat_state", {"in_combat": False})
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

    # Combat Management Methods
    
    def start_combat(self, combatants_data: List[dict]) -> None:
        """
        Initialize combat state with given combatants.
        
        Args:
            combatants_data: List of dicts with keys: name, initiative, type, hp_current, hp_max
        """
        logging.info(f"COMBAT STARTED - Participants: {[c['name'] for c in combatants_data]}")
        
        # Sort by initiative (highest first)
        sorted_combatants = sorted(combatants_data, key=lambda x: x['initiative'], reverse=True)
        
        self.combat_state = {
            "in_combat": True,
            "current_round": 1,
            "current_turn_index": 0,
            "initiative_order": [
                {
                    "name": c['name'],
                    "initiative": c['initiative'],
                    "type": c.get('type', 'unknown')
                } for c in sorted_combatants
            ],
            "combatants": {
                c['name']: {
                    "hp_current": c.get('hp_current', 1),
                    "hp_max": c.get('hp_max', 1),
                    "status": c.get('status', [])
                } for c in sorted_combatants
            },
            "combat_log": []
        }
        
        initiative_list = [f"{c['name']}({c['initiative']})" for c in sorted_combatants]
        logging.info(f"COMBAT INITIALIZED - Initiative order: {initiative_list}")
    
    def end_combat(self) -> None:
        """End combat and reset combat state."""
        if self.combat_state.get("in_combat", False):
            final_round = self.combat_state.get("current_round", 0)
            participants = list(self.combat_state.get("combatants", {}).keys())
            
            # Clean up defeated enemies before ending combat
            defeated_enemies = self.cleanup_defeated_enemies()
            if defeated_enemies:
                logging.info(f"COMBAT CLEANUP: Defeated enemies removed during combat end: {defeated_enemies}")
            
            logging.info(f"COMBAT ENDED - Duration: {final_round} rounds, Participants: {participants}")
        
        # Reset combat state
        self.combat_state = {
            "in_combat": False,
            "current_round": 0,
            "current_turn_index": 0,
            "initiative_order": [],
            "combatants": {},
            "combat_log": []
        }
    
    def cleanup_defeated_enemies(self) -> List[str]:
        """
        Identifies and removes defeated enemies from both combat_state and npc_data.
        Returns a list of defeated enemy names for logging.
        
        CRITICAL: This function works regardless of in_combat status to handle
        cleanup during combat end transitions.
        """
        defeated_enemies = []
        
        # Check if we have any combatants to clean up
        combatants = self.combat_state.get("combatants", {})
        if not combatants:
            return defeated_enemies
        
        # Find defeated enemies (HP <= 0)
        for name, combat_data in combatants.items():
            if combat_data.get("hp_current", 0) <= 0:
                # Check if this is an enemy (not PC, companion, or ally)
                enemy_type = None
                for init_entry in self.combat_state.get("initiative_order", []):
                    if init_entry["name"] == name:
                        enemy_type = init_entry.get("type", "unknown")
                        break
                
                if enemy_type not in ["pc", "companion", "ally"]:
                    defeated_enemies.append(name)
                    logging.info(f"COMBAT CLEANUP: Marking {name} ({enemy_type}) as defeated")
        
        # Remove defeated enemies from combat tracking
        for enemy_name in defeated_enemies:
            # Remove from combat_state combatants
            if enemy_name in self.combat_state.get("combatants", {}):
                del self.combat_state["combatants"][enemy_name]
                logging.info(f"COMBAT CLEANUP: Removed {enemy_name} from combat_state.combatants")
            
            # Remove from initiative order
            self.combat_state["initiative_order"] = [
                entry for entry in self.combat_state.get("initiative_order", [])
                if entry["name"] != enemy_name
            ]
            
            # Remove from NPC data (defeated enemies shouldn't persist)
            if enemy_name in self.npc_data:
                del self.npc_data[enemy_name]
                logging.info(f"COMBAT CLEANUP: Removed {enemy_name} from npc_data")
        
        return defeated_enemies

def get_initial_game_state():
    """
    Returns a blank, initial game state dictionary.
    The Gemini service is responsible for populating this.
    """
    return GameState().to_dict()
