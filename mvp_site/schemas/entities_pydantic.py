"""
Pydantic schema models for entity tracking in Milestone 0.4
Uses sequence ID format: {type}_{name}_{sequence}
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from mvp_site.constants import FRIENDLY_COMBATANT_TYPES, NEUTRAL_COMBATANT_TYPES

# Import defensive numeric field converter for robust data handling
from .defensive_numeric_converter import DefensiveNumericConverter


def sanitize_entity_name_for_id(name: str) -> str:
    """Sanitize a name to create a valid entity ID component.

    Converts special characters to underscores to ensure compatibility
    with entity ID validation patterns.

    Args:
        name: Raw entity name (e.g., "Cazador's Spawn")

    Returns:
        Sanitized name suitable for entity ID (e.g., "cazadors_spawn")
    """
    if not name:
        return name

    # Convert to lowercase
    name = name.lower()

    # Replace apostrophes and spaces with underscores
    name = name.replace("'", "").replace(" ", "_").replace("-", "_")

    # Replace any non-ASCII or non-word characters with underscores
    # \w includes letters, digits, and underscore, but also non-ASCII in Python
    # So we use explicit ASCII ranges
    name = re.sub(r"[^a-z0-9_]", "_", name)

    # Remove duplicate underscores
    name = re.sub(r"_+", "_", name)

    # Strip leading/trailing underscores
    return name.strip("_")


class EntityType(Enum):
    """Entity type enumeration"""

    PLAYER_CHARACTER = "pc"
    NPC = "npc"
    CREATURE = "creature"
    LOCATION = "loc"
    ITEM = "item"
    FACTION = "faction"
    OBJECT = "obj"


class CombatDisposition(Enum):
    """Combat disposition for classifying combatant allegiance.

    This enum provides a formal type-safe way to classify whether a combatant
    is friendly (should be preserved) or hostile (can be removed after defeat).

    Usage:
        - FRIENDLY: PC, companions, allies - never removed during combat cleanup
        - HOSTILE: Enemies, monsters - removed when defeated
        - NEUTRAL: Bystanders, non-combatants - typically not involved in combat

    This complements the string-based classification in constants.py by providing
    schema-level type safety for new code paths.
    """

    FRIENDLY = "friendly"  # PC, companions, allies - preserved after combat
    HOSTILE = "hostile"  # Enemies, monsters - removed when defeated
    NEUTRAL = "neutral"  # Bystanders, non-combatants

    @classmethod
    def from_type_string(cls, type_str: str | None) -> "CombatDisposition":
        """Convert a legacy type string to CombatDisposition.

        Args:
            type_str: Legacy type string (e.g., "pc", "enemy", "companion")

        Returns:
            Appropriate CombatDisposition enum value
        """
        if type_str is None:
            return cls.HOSTILE  # Default unknown types to hostile for safety

        normalized = type_str.lower().strip()

        if normalized in FRIENDLY_COMBATANT_TYPES:
            return cls.FRIENDLY

        if normalized in NEUTRAL_COMBATANT_TYPES:
            return cls.NEUTRAL

        return cls.HOSTILE


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
    """D&D-style character stats with defensive conversion"""

    strength: int = Field(ge=1, le=30, default=10)
    dexterity: int = Field(ge=1, le=30, default=10)
    constitution: int = Field(ge=1, le=30, default=10)
    intelligence: int = Field(ge=1, le=30, default=10)
    wisdom: int = Field(ge=1, le=30, default=10)
    charisma: int = Field(ge=1, le=30, default=10)

    @field_validator("strength", mode="before")
    @classmethod
    def convert_strength(cls, v):
        return DefensiveNumericConverter.convert_value("strength", v)

    @field_validator("dexterity", mode="before")
    @classmethod
    def convert_dexterity(cls, v):
        return DefensiveNumericConverter.convert_value("dexterity", v)

    @field_validator("constitution", mode="before")
    @classmethod
    def convert_constitution(cls, v):
        return DefensiveNumericConverter.convert_value("constitution", v)

    @field_validator("intelligence", mode="before")
    @classmethod
    def convert_intelligence(cls, v):
        return DefensiveNumericConverter.convert_value("intelligence", v)

    @field_validator("wisdom", mode="before")
    @classmethod
    def convert_wisdom(cls, v):
        return DefensiveNumericConverter.convert_value("wisdom", v)

    @field_validator("charisma", mode="before")
    @classmethod
    def convert_charisma(cls, v):
        return DefensiveNumericConverter.convert_value("charisma", v)

    def get_modifier(self, ability_name: str) -> int:
        """Calculate D&D 5e ability modifier: (ability - 10) // 2"""
        ability_value = getattr(self, ability_name)
        return (ability_value - 10) // 2


class HealthStatus(BaseModel):
    """Health and condition tracking with defensive conversion"""

    hp: int = Field(ge=0)
    hp_max: int = Field(ge=1)
    temp_hp: int = Field(ge=0, default=0)
    conditions: list[str] = Field(default_factory=list)
    death_saves: dict[str, int] = Field(
        default_factory=lambda: {"successes": 0, "failures": 0}
    )

    @field_validator("hp", mode="before")
    @classmethod
    def convert_hp(cls, v):
        return DefensiveNumericConverter.convert_value("hp", v)

    @field_validator("hp_max", mode="before")
    @classmethod
    def convert_hp_max(cls, v):
        return DefensiveNumericConverter.convert_value("hp_max", v)

    @field_validator("temp_hp", mode="before")
    @classmethod
    def convert_temp_hp(cls, v):
        return DefensiveNumericConverter.convert_value("temp_hp", v)

    @model_validator(mode="after")
    def validate_hp_not_exceed_max(self) -> "HealthStatus":
        """Clamp HP to hp_max if it exceeds after defensive conversion.

        When defensive conversion reduces hp_max (e.g., "unknown" → 1), we clamp
        hp to the new hp_max rather than raising an error, since the user didn't
        explicitly provide conflicting valid integers.
        """
        if self.hp_max > 0 and self.hp > self.hp_max:
            self.hp = self.hp_max
        return self


class Location(BaseModel):
    """Location entity model"""

    entity_id: str = Field(pattern=r"^loc_[\w]+_\d{3}$")
    entity_type: EntityType = Field(default=EntityType.LOCATION)
    display_name: str
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    connected_locations: list[str] = Field(default_factory=list)
    entities_present: list[str] = Field(default_factory=list)
    environmental_effects: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)


class Character(BaseModel):
    """Comprehensive character model with narrative consistency and D&D 5e support"""

    entity_id: str = Field(pattern=r"^(pc|npc)_[\w]+_\d{3}$")
    entity_type: EntityType
    display_name: str
    aliases: list[str] = Field(default_factory=list)

    # CRITICAL: Narrative consistency fields (from entities_simple.py)
    gender: str | None = Field(
        None, description="Gender for narrative consistency (required for NPCs)"
    )
    age: int | None = Field(
        None, ge=0, le=50000, description="Age in years for narrative consistency"
    )

    # D&D fundamentals (from game_state_instruction.md)
    mbti: str | None = Field(
        None, description="MBTI personality type for consistent roleplay"
    )
    alignment: str | None = Field(None, description="D&D alignment (Lawful Good, etc.)")
    class_name: str | None = Field(
        None, description="Character class (Fighter, Wizard, etc.)"
    )
    background: str | None = Field(
        None, description="Character background (Soldier, Noble, etc.)"
    )

    # Core attributes
    level: int = Field(ge=1, le=20, default=1)

    @field_validator("level", mode="before")
    @classmethod
    def convert_level(cls, v):
        return DefensiveNumericConverter.convert_value("level", v)

    stats: Stats = Field(default_factory=Stats)
    health: HealthStatus

    # Status and visibility
    status: list[EntityStatus] = Field(default_factory=lambda: [EntityStatus.CONSCIOUS])
    visibility: Visibility = Field(default=Visibility.VISIBLE)

    # Location
    current_location: str = Field(pattern=r"^loc_[\w]+_\d{3}$")

    # Equipment and inventory
    equipped_items: list[str] = Field(default_factory=list)
    inventory: list[str] = Field(default_factory=list)

    # Resources
    resources: dict[str, Any] = Field(default_factory=dict)

    # Knowledge and memories
    knowledge: list[str] = Field(default_factory=list)
    core_memories: list[str] = Field(default_factory=list)
    recent_decisions: list[str] = Field(default_factory=list)

    # Relationships
    relationships: dict[str, str] = Field(default_factory=dict)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v, info):
        """Validate gender field for narrative consistency (permissive for LLM creativity)"""
        # Check if this is an NPC
        entity_type = info.data.get("entity_type")
        entity_id = info.data.get("entity_id", "")

        # Determine entity type from entity_id if not set
        if entity_type is None:
            if entity_id.startswith("npc_"):
                entity_type = EntityType.NPC
            elif entity_id.startswith("pc_"):
                entity_type = EntityType.PLAYER_CHARACTER

        # For NPCs, gender is mandatory to prevent narrative inconsistency
        if entity_type == EntityType.NPC:
            if v is None or v == "":
                raise ValueError(
                    "Gender is required for NPCs to ensure narrative consistency. "
                    "Can be any descriptive value (e.g., 'male', 'female', 'fluid', 'mixed', etc.)"
                )

            # Accept any non-empty string for creative flexibility
            if not isinstance(v, str):
                raise ValueError(f"Gender must be a string_type, got: {type(v)}")

            return v.lower().strip()

        # For PCs, gender is optional but must be a string if provided
        if v is not None and v != "":
            if not isinstance(v, str):
                raise ValueError(f"Gender must be a string_type, got: {type(v)}")
            return v.lower().strip()

        return v

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        """Validate age field for narrative consistency"""
        if v is not None:
            if not isinstance(v, int) or v < 0:
                raise ValueError(f"Age must be a non-negative integer, got: {v}")
            if v > 50000:  # Fantasy setting allows very old beings
                raise ValueError(f"Age {v} seems unreasonably high (max: 50000)")
        return v

    @field_validator("mbti")
    @classmethod
    def validate_mbti(cls, v):
        """Validate personality field (accepts MBTI or creative descriptions)"""
        if v is not None:
            if not isinstance(v, str):
                raise ValueError(f"Personality/MBTI must be a string, got: {type(v)}")

            # Accept any personality description for creative flexibility
            # Could be traditional MBTI (INFJ) or creative ("mysterious and brooding")
            return v.strip()
        return v

    @field_validator("alignment")
    @classmethod
    def validate_alignment(cls, v):
        """Validate alignment field (accepts D&D or creative alignments)"""
        if v is not None:
            if not isinstance(v, str):
                raise ValueError(f"Alignment must be a string, got: {type(v)}")

            # Accept any alignment description for creative flexibility
            # Could be traditional D&D ("Lawful Good") or creative ("Chaotic Awesome")
            return v.strip()
        return v

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v, info):
        if "entity_id" in info.data:
            if info.data["entity_id"].startswith("pc_"):
                return EntityType.PLAYER_CHARACTER
            if info.data["entity_id"].startswith("npc_"):
                return EntityType.NPC
        return v

    @model_validator(mode="after")
    def validate_npc_gender_required(self):
        """Ensure NPCs have gender field for narrative consistency"""
        if self.entity_type == EntityType.NPC and (
            self.gender is None or self.gender == ""
        ):
            raise ValueError(
                "Gender is required for NPCs to ensure narrative consistency. "
                "Valid options: ['male', 'female', 'non-binary', 'other']"
            )
        return self

    model_config = ConfigDict(use_enum_values=True)


class PlayerCharacter(Character):
    """Player character specific model"""

    entity_type: EntityType = Field(default=EntityType.PLAYER_CHARACTER)
    player_name: str | None = None
    experience: dict[str, int] = Field(
        default_factory=lambda: {"current": 0, "to_next_level": 300}
    )
    inspiration: bool = Field(default=False)
    hero_points: int = Field(ge=0, default=0)


class NPC(Character):
    """NPC specific model"""

    entity_type: EntityType = Field(default=EntityType.NPC)
    faction: str | None = None
    role: str | None = None
    attitude_to_party: str | None = Field(default="neutral")


class CombatState(BaseModel):
    """Combat tracking model"""

    in_combat: bool = Field(default=False)
    round_number: int = Field(ge=0, default=0)
    turn_order: list[str] = Field(default_factory=list)
    active_combatant: str | None = None
    participants: list[str] = Field(default_factory=list)

    @field_validator("participants")
    @classmethod
    def validate_participants(cls, v, info):
        # All turn_order entities must be in participants
        if "turn_order" in info.data:
            for entity in info.data["turn_order"]:
                if entity not in v:
                    raise ValueError(f"Turn order entity {entity} not in participants")
        return v


class SceneManifest(BaseModel):
    """Complete scene state for validation"""

    scene_id: str = Field(pattern=r"^scene_[\w]+_\d{3}$")
    timestamp: datetime = Field(default_factory=datetime.now)
    session_number: int = Field(ge=1)
    turn_number: int = Field(ge=1)

    # Location
    current_location: Location

    # Entities
    player_characters: list[PlayerCharacter] = Field(min_length=1)
    npcs: list[NPC] = Field(default_factory=list)

    # Entity tracking helpers
    present_entities: list[str] = Field(default_factory=list)
    mentioned_entities: list[str] = Field(default_factory=list)
    focus_entity: str | None = None

    # Combat
    combat_state: CombatState | None = None

    # Environmental
    time_of_day: str | None = None
    weather: str | None = None
    special_conditions: list[str] = Field(default_factory=list)

    @field_validator("present_entities")
    @classmethod
    def validate_present_entities(cls, v, info):
        """Ensure all present entities exist in the scene"""
        all_entity_ids = []

        if "player_characters" in info.data:
            all_entity_ids.extend(
                [pc.entity_id for pc in info.data["player_characters"]]
            )
        if "npcs" in info.data:
            all_entity_ids.extend([npc.entity_id for npc in info.data["npcs"]])

        for entity_id in v:
            if entity_id not in all_entity_ids:
                raise ValueError(
                    f"Present entity {entity_id} not found in scene entities"
                )

        return v

    def get_expected_entities(self) -> list[str]:
        """Get list of entities that should be mentioned in narrative"""
        expected = []

        # Add all visible, conscious entities
        for pc in self.player_characters:
            pc_visible = pc.visibility in (Visibility.VISIBLE, "visible")
            pc_conscious = (
                EntityStatus.CONSCIOUS in pc.status or "conscious" in pc.status
            )
            if pc_visible and pc_conscious and pc.entity_id in self.present_entities:
                expected.append(pc.display_name)

        for npc in self.npcs:
            npc_visible = npc.visibility in (Visibility.VISIBLE, "visible")
            npc_conscious = (
                EntityStatus.CONSCIOUS in npc.status or "conscious" in npc.status
            )
            if npc_visible and npc_conscious and npc.entity_id in self.present_entities:
                expected.append(npc.display_name)

        return expected

    def to_prompt_format(self) -> str:
        """Convert to structured format for prompt injection"""
        prompt_parts = [
            "=== SCENE MANIFEST ===",
            f"Location: {self.current_location.display_name}",
            f"Session: {self.session_number}, Turn: {self.turn_number}",
            "",
        ]

        # Add present characters
        prompt_parts.append("PRESENT CHARACTERS:")
        for pc in self.player_characters:
            if pc.entity_id in self.present_entities:
                status_str = ", ".join(
                    [s.value if hasattr(s, "value") else str(s) for s in pc.status]
                )
                prompt_parts.append(
                    f"- {pc.display_name} (PC): HP {pc.health.hp}/{pc.health.hp_max}, "
                    f"Status: {status_str}, Visibility: {pc.visibility.value if hasattr(pc.visibility, 'value') else str(pc.visibility)}"
                )

        for npc in self.npcs:
            if npc.entity_id in self.present_entities:
                status_str = ", ".join(
                    [s.value if hasattr(s, "value") else str(s) for s in npc.status]
                )
                prompt_parts.append(
                    f"- {npc.display_name} (NPC): HP {npc.health.hp}/{npc.health.hp_max}, "
                    f"Status: {status_str}, Visibility: {npc.visibility.value if hasattr(npc.visibility, 'value') else str(npc.visibility)}"
                )

        # Add combat info if relevant
        if self.combat_state and self.combat_state.in_combat:
            prompt_parts.extend(
                [
                    "",
                    "COMBAT STATE:",
                    f"Round: {self.combat_state.round_number}",
                    f"Turn Order: {', '.join(self.combat_state.turn_order)}",
                    f"Active: {self.combat_state.active_combatant or 'None'}",
                ]
            )

        # Add special conditions
        if self.special_conditions:
            prompt_parts.extend(
                ["", f"SPECIAL CONDITIONS: {', '.join(self.special_conditions)}"]
            )

        prompt_parts.append("=== END MANIFEST ===")

        return "\n".join(prompt_parts)


def create_from_game_state(
    game_state: dict[str, Any], session_number: int, turn_number: int
) -> SceneManifest:
    """Create a SceneManifest from legacy game state format"""

    # Create location
    location = Location(
        entity_id="loc_default_001",
        display_name=game_state.get("location", "Unknown Location"),
        aliases=[],
    )

    # Create player character
    pc_data = game_state.get("player_character_data", {})
    pc_name = pc_data.get("name", "Unknown")

    # Use existing string_id if present, otherwise generate one
    if "string_id" in pc_data:
        pc_entity_id = pc_data["string_id"]
    else:
        pc_entity_id = f"pc_{sanitize_entity_name_for_id(pc_name)}_001"

    pc = PlayerCharacter(
        entity_id=pc_entity_id,
        display_name=pc_name,
        health=HealthStatus(
            hp=pc_data.get("hp_current", pc_data.get("hp", 10)),
            hp_max=pc_data.get("hp_max", 10),
        ),
        current_location=location.entity_id,
    )

    # Create NPCs
    # Pattern for valid NPC entity IDs (must start with npc_ or pc_)
    npc_entity_id_pattern = re.compile(r"^(pc|npc)_[\w]+_\d{3}$")

    npcs = []
    npc_data = game_state.get("npc_data", {})
    for idx, (npc_key, npc_info) in enumerate(npc_data.items()):
        if npc_info.get("present", True):
            # Use existing string_id if present AND valid, otherwise generate one
            stored_id = npc_info.get("string_id")
            if stored_id and npc_entity_id_pattern.match(stored_id):
                npc_entity_id = stored_id
            else:
                # Generate valid ID - handles missing or invalid string_id
                npc_entity_id = (
                    f"npc_{sanitize_entity_name_for_id(npc_key)}_{idx + 1:03d}"
                )

            # Use "name" field if present, otherwise fall back to the key
            npc_display_name = npc_info.get("name", npc_key)

            npc = NPC(
                entity_id=npc_entity_id,
                display_name=npc_display_name,
                health=HealthStatus(
                    hp=npc_info.get("hp_current", npc_info.get("hp", 10)),
                    hp_max=npc_info.get("hp_max", 10),
                ),
                current_location=location.entity_id,
                status=[EntityStatus.CONSCIOUS]
                if npc_info.get("conscious", True)
                else [EntityStatus.UNCONSCIOUS],
                visibility=Visibility.INVISIBLE
                if npc_info.get("hidden", False)
                else Visibility.VISIBLE,
                gender=npc_info.get(
                    "gender", "other"
                ),  # Required for NPCs, default to "other" if not specified
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
            round_number=combat_data.get("round", 1),
        )

    # Create scene manifest
    return SceneManifest(
        scene_id=f"scene_s{session_number}_t{turn_number}_001",
        session_number=session_number,
        turn_number=turn_number,
        current_location=location,
        player_characters=[pc],
        npcs=npcs,
        present_entities=present_entities,
        combat_state=combat_state,
    )
