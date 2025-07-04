"""
Simple entity schema models for Milestone 0.4 (without Pydantic)
Uses sequence ID format: {type}_{name}_{sequence}
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import re


class EntityType(Enum):
    """Entity type enumeration"""
    PLAYER_CHARACTER = "pc"
    NPC = "npc"
    CREATURE = "creature"
    LOCATION = "loc"
    ITEM = "item"
    FACTION = "faction"
    OBJECT = "obj"


class EntityStatus(Enum):
    """Common entity statuses"""
    CONSCIOUS = "conscious"
    UNCONSCIOUS = "unconscious"
    DEAD = "dead"
    HIDDEN = "hidden"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    STUNNED = "stunned"


class Visibility(Enum):
    """Entity visibility states"""
    VISIBLE = "visible"
    HIDDEN = "hidden"
    INVISIBLE = "invisible"
    OBSCURED = "obscured"
    DARKNESS = "darkness"


class SimpleValidator:
    """Simple validation helper"""
    @staticmethod
    def validate_entity_id(entity_id: str, entity_type: str) -> bool:
        pattern = rf"^{entity_type}_[\w-]+_\d{{3}}$"
        return bool(re.match(pattern, entity_id))
    
    @staticmethod
    def validate_range(value: int, min_val: int, max_val: int, name: str) -> int:
        if value < min_val or value > max_val:
            raise ValueError(f"{name} must be between {min_val} and {max_val}, got {value}")
        return value


class Stats:
    """D&D-style character stats"""
    def __init__(self, strength=10, dexterity=10, constitution=10, 
                 intelligence=10, wisdom=10, charisma=10):
        self.strength = SimpleValidator.validate_range(strength, 1, 30, "Strength")
        self.dexterity = SimpleValidator.validate_range(dexterity, 1, 30, "Dexterity")
        self.constitution = SimpleValidator.validate_range(constitution, 1, 30, "Constitution")
        self.intelligence = SimpleValidator.validate_range(intelligence, 1, 30, "Intelligence")
        self.wisdom = SimpleValidator.validate_range(wisdom, 1, 30, "Wisdom")
        self.charisma = SimpleValidator.validate_range(charisma, 1, 30, "Charisma")


class HealthStatus:
    """Health and condition tracking"""
    def __init__(self, hp: int, hp_max: int, temp_hp: int = 0, 
                 conditions: List[str] = None):
        if hp > hp_max:
            raise ValueError(f"HP {hp} cannot exceed max HP {hp_max}")
        if hp < 0:
            raise ValueError(f"HP cannot be negative")
        if hp_max < 1:
            raise ValueError(f"Max HP must be at least 1")
            
        self.hp = hp
        self.hp_max = hp_max
        self.temp_hp = max(0, temp_hp)
        self.conditions = conditions or []
        self.death_saves = {"successes": 0, "failures": 0}


class Location:
    """Location entity model"""
    def __init__(self, entity_id: str, display_name: str, aliases: List[str] = None,
                 description: str = None, connected_locations: List[str] = None,
                 entities_present: List[str] = None, environmental_effects: List[str] = None):
        
        if not SimpleValidator.validate_entity_id(entity_id, "loc"):
            raise ValueError(f"Invalid location ID format: {entity_id}")
            
        self.entity_id = entity_id
        self.entity_type = EntityType.LOCATION
        self.display_name = display_name
        self.aliases = aliases or []
        self.description = description
        self.connected_locations = connected_locations or []
        self.entities_present = entities_present or []
        self.environmental_effects = environmental_effects or []


class Character:
    """Base character model for PCs and NPCs"""
    def __init__(self, entity_id: str, entity_type: EntityType, display_name: str,
                 health: HealthStatus, current_location: str, level: int = 1,
                 aliases: List[str] = None, stats: Stats = None, 
                 status: List[EntityStatus] = None, visibility: Visibility = Visibility.VISIBLE,
                 equipped_items: List[str] = None, inventory: List[str] = None,
                 resources: Dict[str, Any] = None, knowledge: List[str] = None,
                 core_memories: List[str] = None, recent_decisions: List[str] = None,
                 relationships: Dict[str, str] = None):
        
        # Validate entity ID
        type_prefix = entity_type.value
        if not SimpleValidator.validate_entity_id(entity_id, type_prefix):
            raise ValueError(f"Invalid {type_prefix} ID format: {entity_id}")
        
        # Validate location ID
        if not SimpleValidator.validate_entity_id(current_location, "loc"):
            raise ValueError(f"Invalid location ID format: {current_location}")
            
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.display_name = display_name
        self.aliases = aliases or []
        self.level = SimpleValidator.validate_range(level, 1, 20, "Level")
        self.stats = stats or Stats()
        self.health = health
        self.status = status or [EntityStatus.CONSCIOUS]
        self.visibility = visibility
        self.current_location = current_location
        self.equipped_items = equipped_items or []
        self.inventory = inventory or []
        self.resources = resources or {}
        self.knowledge = knowledge or []
        self.core_memories = core_memories or []
        self.recent_decisions = recent_decisions or []
        self.relationships = relationships or {}


class PlayerCharacter(Character):
    """Player character specific model"""
    def __init__(self, player_name: str = None, experience: Dict[str, int] = None,
                 inspiration: bool = False, hero_points: int = 0, **kwargs):
        super().__init__(entity_type=EntityType.PLAYER_CHARACTER, **kwargs)
        self.player_name = player_name
        self.experience = experience or {"current": 0, "to_next_level": 300}
        self.inspiration = inspiration
        self.hero_points = max(0, hero_points)


class NPC(Character):
    """NPC specific model"""
    def __init__(self, faction: str = None, role: str = None, 
                 attitude_to_party: str = "neutral", **kwargs):
        super().__init__(entity_type=EntityType.NPC, **kwargs)
        self.faction = faction
        self.role = role
        self.attitude_to_party = attitude_to_party


class SceneManifest:
    """Complete scene state for validation"""
    def __init__(self, scene_id: str, session_number: int, turn_number: int,
                 current_location: Location, player_characters: List[PlayerCharacter],
                 npcs: List[NPC] = None, present_entities: List[str] = None,
                 mentioned_entities: List[str] = None, focus_entity: str = None,
                 combat_state: Dict[str, Any] = None, time_of_day: str = None,
                 weather: str = None, special_conditions: List[str] = None):
        
        if not re.match(r"^scene_[\w]+_\d{3}$", scene_id):
            raise ValueError(f"Invalid scene ID format: {scene_id}")
            
        self.scene_id = scene_id
        self.timestamp = datetime.now()
        self.session_number = max(1, session_number)
        self.turn_number = max(1, turn_number)
        self.current_location = current_location
        self.player_characters = player_characters
        self.npcs = npcs or []
        self.present_entities = present_entities or []
        self.mentioned_entities = mentioned_entities or []
        self.focus_entity = focus_entity
        self.combat_state = combat_state
        self.time_of_day = time_of_day
        self.weather = weather
        self.special_conditions = special_conditions or []
        
    def get_expected_entities(self) -> List[str]:
        """Get list of entities that should be mentioned in narrative"""
        expected = []
        
        # Add all visible, conscious entities
        for pc in self.player_characters:
            if (pc.visibility == Visibility.VISIBLE and 
                EntityStatus.CONSCIOUS in pc.status and
                pc.entity_id in self.present_entities):
                expected.append(pc.display_name)
        
        for npc in self.npcs:
            if (npc.visibility == Visibility.VISIBLE and 
                EntityStatus.CONSCIOUS in npc.status and
                npc.entity_id in self.present_entities):
                expected.append(npc.display_name)
        
        return expected
    
    def to_prompt_format(self) -> str:
        """Convert to structured format for prompt injection"""
        prompt_parts = [
            f"=== SCENE MANIFEST ===",
            f"Location: {self.current_location.display_name}",
            f"Session: {self.session_number}, Turn: {self.turn_number}",
            ""
        ]
        
        # Add present characters
        prompt_parts.append("PRESENT CHARACTERS:")
        for pc in self.player_characters:
            if pc.entity_id in self.present_entities:
                status_str = ", ".join([s.value for s in pc.status])
                prompt_parts.append(
                    f"- {pc.display_name} (PC): HP {pc.health.hp}/{pc.health.hp_max}, "
                    f"Status: {status_str}, Visibility: {pc.visibility.value}"
                )
        
        for npc in self.npcs:
            if npc.entity_id in self.present_entities:
                status_str = ", ".join([s.value for s in npc.status])
                prompt_parts.append(
                    f"- {npc.display_name} (NPC): HP {npc.health.hp}/{npc.health.hp_max}, "
                    f"Status: {status_str}, Visibility: {npc.visibility.value}"
                )
        
        # Add combat info if relevant
        if self.combat_state and self.combat_state.get("in_combat"):
            prompt_parts.extend([
                "",
                "COMBAT STATE:",
                f"Round: {self.combat_state.get('round_number', 1)}",
                f"Participants: {', '.join(self.combat_state.get('participants', []))}",
            ])
        
        # Add special conditions
        if self.special_conditions:
            prompt_parts.extend([
                "",
                f"SPECIAL CONDITIONS: {', '.join(self.special_conditions)}"
            ])
        
        prompt_parts.append("=== END MANIFEST ===")
        
        return "\n".join(prompt_parts)


def create_from_game_state(game_state: Dict[str, Any], 
                          session: int, 
                          turn: int) -> SceneManifest:
    """Create a SceneManifest from legacy game state format"""
    
    # Create location - check both possible field names
    location_name = game_state.get("world_data", {}).get("current_location", 
                    game_state.get("world_data", {}).get("current_location_name",
                    game_state.get("location", "Unknown Location")))
    
    location = Location(
        entity_id="loc_default_001",
        display_name=location_name
    )
    
    # Create player character - only if we have actual character data
    player_characters = []
    pc_data = game_state.get("player_character_data", {})
    
    # Only create a player character if we have a name
    if pc_data and pc_data.get("name"):
        pc_name = pc_data.get("name")
        
        # Use string_id if present, otherwise generate one
        pc_entity_id = pc_data.get("string_id", f"pc_{pc_name.lower().replace(' ', '_')}_001")
        
        pc = PlayerCharacter(
            entity_id=pc_entity_id,
            display_name=pc_name,
            health=HealthStatus(
                hp=pc_data.get("hp_current", pc_data.get("hp", 10)),
                hp_max=pc_data.get("hp_max", 10)
            ),
            current_location=location.entity_id
        )
        player_characters.append(pc)
    
    # Create NPCs
    npcs = []
    npc_data = game_state.get("npc_data", {})
    for idx, (npc_name, npc_info) in enumerate(npc_data.items()):
        if npc_info.get("present", True):
            # Use string_id if present, otherwise generate one
            npc_entity_id = npc_info.get("string_id", f"npc_{npc_name.lower().replace(' ', '_')}_{idx+1:03d}")
            
            npc = NPC(
                entity_id=npc_entity_id,
                display_name=npc_info.get("name", npc_name),
                health=HealthStatus(
                    hp=npc_info.get("hp_current", npc_info.get("hp", 10)),
                    hp_max=npc_info.get("hp_max", 10)
                ),
                current_location=location.entity_id,
                status=[EntityStatus.CONSCIOUS] if npc_info.get("conscious", True) 
                       else [EntityStatus.UNCONSCIOUS],
                visibility=Visibility.INVISIBLE if npc_info.get("hidden", False)
                          else Visibility.VISIBLE
            )
            npcs.append(npc)
    
    # Determine present entities
    present_entities = []
    present_entities.extend([pc.entity_id for pc in player_characters])
    present_entities.extend([npc.entity_id for npc in npcs])
    
    # Create scene manifest
    manifest = SceneManifest(
        scene_id=f"scene_s{session}_t{turn}_001",
        session_number=session,
        turn_number=turn,
        current_location=location,
        player_characters=player_characters,
        npcs=npcs,
        present_entities=present_entities,
        combat_state=game_state.get("combat_state")
    )
    
    return manifest