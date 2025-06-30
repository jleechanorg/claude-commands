"""
Pydantic schema models for entity tracking in Milestone 0.4
Uses sequence ID format: {type}_{name}_{sequence}
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


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


class Stats(BaseModel):
    """D&D-style character stats"""
    strength: int = Field(ge=1, le=30, default=10)
    dexterity: int = Field(ge=1, le=30, default=10)
    constitution: int = Field(ge=1, le=30, default=10)
    intelligence: int = Field(ge=1, le=30, default=10)
    wisdom: int = Field(ge=1, le=30, default=10)
    charisma: int = Field(ge=1, le=30, default=10)


class HealthStatus(BaseModel):
    """Health and condition tracking"""
    hp: int = Field(ge=0)
    hp_max: int = Field(ge=1)
    temp_hp: int = Field(ge=0, default=0)
    conditions: List[str] = Field(default_factory=list)
    death_saves: Dict[str, int] = Field(default_factory=lambda: {"successes": 0, "failures": 0})
    
    @validator('hp')
    def hp_not_exceed_max(cls, v, values):
        if 'hp_max' in values and v > values['hp_max']:
            raise ValueError(f"HP {v} cannot exceed max HP {values['hp_max']}")
        return v


class Location(BaseModel):
    """Location entity model"""
    entity_id: str = Field(regex=r"^loc_[\w]+_\d{3}$")
    entity_type: EntityType = Field(default=EntityType.LOCATION)
    display_name: str
    aliases: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    connected_locations: List[str] = Field(default_factory=list)
    entities_present: List[str] = Field(default_factory=list)
    environmental_effects: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class Character(BaseModel):
    """Base character model for PCs and NPCs"""
    entity_id: str = Field(regex=r"^(pc|npc)_[\w]+_\d{3}$")
    entity_type: EntityType
    display_name: str
    aliases: List[str] = Field(default_factory=list)
    
    # Core attributes
    level: int = Field(ge=1, le=20, default=1)
    stats: Stats = Field(default_factory=Stats)
    health: HealthStatus
    
    # Status and visibility
    status: List[EntityStatus] = Field(default_factory=lambda: [EntityStatus.CONSCIOUS])
    visibility: Visibility = Field(default=Visibility.VISIBLE)
    
    # Location
    current_location: str = Field(regex=r"^loc_[\w]+_\d{3}$")
    
    # Equipment and inventory
    equipped_items: List[str] = Field(default_factory=list)
    inventory: List[str] = Field(default_factory=list)
    
    # Resources
    resources: Dict[str, Any] = Field(default_factory=dict)
    
    # Knowledge and memories
    knowledge: List[str] = Field(default_factory=list)
    core_memories: List[str] = Field(default_factory=list)
    recent_decisions: List[str] = Field(default_factory=list)
    
    # Relationships
    relationships: Dict[str, str] = Field(default_factory=dict)
    
    @validator('entity_type')
    def validate_entity_type(cls, v, values):
        if 'entity_id' in values:
            if values['entity_id'].startswith('pc_'):
                return EntityType.PLAYER_CHARACTER
            elif values['entity_id'].startswith('npc_'):
                return EntityType.NPC
        return v
    
    class Config:
        use_enum_values = True


class PlayerCharacter(Character):
    """Player character specific model"""
    entity_type: EntityType = Field(default=EntityType.PLAYER_CHARACTER)
    player_name: Optional[str] = None
    experience: Dict[str, int] = Field(
        default_factory=lambda: {"current": 0, "to_next_level": 300}
    )
    inspiration: bool = Field(default=False)
    hero_points: int = Field(ge=0, default=0)


class NPC(Character):
    """NPC specific model"""
    entity_type: EntityType = Field(default=EntityType.NPC)
    faction: Optional[str] = None
    role: Optional[str] = None
    attitude_to_party: Optional[str] = Field(default="neutral")


class CombatState(BaseModel):
    """Combat tracking model"""
    in_combat: bool = Field(default=False)
    round_number: int = Field(ge=0, default=0)
    turn_order: List[str] = Field(default_factory=list)
    active_combatant: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    
    @validator('participants')
    def validate_participants(cls, v, values):
        # All turn_order entities must be in participants
        if 'turn_order' in values:
            for entity in values['turn_order']:
                if entity not in v:
                    raise ValueError(f"Turn order entity {entity} not in participants")
        return v


class SceneManifest(BaseModel):
    """Complete scene state for validation"""
    scene_id: str = Field(regex=r"^scene_[\w]+_\d{3}$")
    timestamp: datetime = Field(default_factory=datetime.now)
    session_number: int = Field(ge=1)
    turn_number: int = Field(ge=1)
    
    # Location
    current_location: Location
    
    # Entities
    player_characters: List[PlayerCharacter] = Field(min_items=1)
    npcs: List[NPC] = Field(default_factory=list)
    
    # Entity tracking helpers
    present_entities: List[str] = Field(default_factory=list)
    mentioned_entities: List[str] = Field(default_factory=list)
    focus_entity: Optional[str] = None
    
    # Combat
    combat_state: Optional[CombatState] = None
    
    # Environmental
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    special_conditions: List[str] = Field(default_factory=list)
    
    @validator('present_entities')
    def validate_present_entities(cls, v, values):
        """Ensure all present entities exist in the scene"""
        all_entity_ids = []
        
        if 'player_characters' in values:
            all_entity_ids.extend([pc.entity_id for pc in values['player_characters']])
        if 'npcs' in values:
            all_entity_ids.extend([npc.entity_id for npc in values['npcs']])
            
        for entity_id in v:
            if entity_id not in all_entity_ids:
                raise ValueError(f"Present entity {entity_id} not found in scene entities")
                
        return v
    
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
        if self.combat_state and self.combat_state.in_combat:
            prompt_parts.extend([
                "",
                "COMBAT STATE:",
                f"Round: {self.combat_state.round_number}",
                f"Turn Order: {', '.join(self.combat_state.turn_order)}",
                f"Active: {self.combat_state.active_combatant or 'None'}"
            ])
        
        # Add special conditions
        if self.special_conditions:
            prompt_parts.extend([
                "",
                f"SPECIAL CONDITIONS: {', '.join(self.special_conditions)}"
            ])
        
        prompt_parts.append("=== END MANIFEST ===")
        
        return "\n".join(prompt_parts)
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Generate JSON schema for structured output"""
        return {
            "type": "object",
            "properties": {
                "narrative": {
                    "type": "string",
                    "description": "The narrative text for this turn"
                },
                "entities_mentioned": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of character names mentioned in the narrative"
                },
                "visibility_notes": {
                    "type": "object",
                    "description": "Notes about hidden/invisible entities"
                }
            },
            "required": ["narrative", "entities_mentioned"]
        }


def create_from_game_state(game_state: Dict[str, Any], 
                          session: int, 
                          turn: int) -> SceneManifest:
    """Create a SceneManifest from legacy game state format"""
    
    # Create location
    location = Location(
        entity_id="loc_default_001",
        display_name=game_state.get("location", "Unknown Location"),
        aliases=[]
    )
    
    # Create player character
    pc_data = game_state.get("player_character_data", {})
    pc_name = pc_data.get("name", "Unknown")
    
    pc = PlayerCharacter(
        entity_id=f"pc_{pc_name.lower().replace(' ', '_')}_001",
        display_name=pc_name,
        health=HealthStatus(
            hp=pc_data.get("hp", 10),
            hp_max=pc_data.get("hp_max", 10)
        ),
        current_location=location.entity_id
    )
    
    # Create NPCs
    npcs = []
    npc_data = game_state.get("npc_data", {})
    for idx, (npc_name, npc_info) in enumerate(npc_data.items()):
        if npc_info.get("present", True):
            npc = NPC(
                entity_id=f"npc_{npc_name.lower().replace(' ', '_')}_{idx+1:03d}",
                display_name=npc_name,
                health=HealthStatus(
                    hp=npc_info.get("hp", 10),
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
    present_entities = [pc.entity_id]
    present_entities.extend([npc.entity_id for npc in npcs])
    
    # Create combat state if needed
    combat_state = None
    if game_state.get("combat_state", {}).get("in_combat"):
        combat_data = game_state["combat_state"]
        combat_state = CombatState(
            in_combat=True,
            participants=combat_data.get("participants", []),
            round_number=combat_data.get("round", 1)
        )
    
    # Create scene manifest
    manifest = SceneManifest(
        scene_id=f"scene_s{session}_t{turn}_001",
        session_number=session,
        turn_number=turn,
        current_location=location,
        player_characters=[pc],
        npcs=npcs,
        present_entities=present_entities,
        combat_state=combat_state
    )
    
    return manifest