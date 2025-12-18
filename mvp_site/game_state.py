"""
Defines the GameState class, which represents the complete state of a campaign.

Includes:
- D&D 5E mechanics calculation functions for deterministic game logic (dice rolls)
- XP/Level validation using D&D 5e XP thresholds
- Time monotonicity checks to prevent time regression
- Helper functions for XP→Level calculations

The LLM should focus on narrative while code handles all mathematical operations.
"""

import datetime
import json
import random
import re
from dataclasses import dataclass
from typing import Any, Optional

from mvp_site import constants, logging_util

# =============================================================================
# D&D 5e XP THRESHOLDS
# =============================================================================
# Cumulative XP required to reach each level (1-20)
# Source: D&D 5e Player's Handbook / SRD
# =============================================================================

XP_THRESHOLDS = [
    0,        # Level 1
    300,      # Level 2
    900,      # Level 3
    2700,     # Level 4
    6500,     # Level 5
    14000,    # Level 6
    23000,    # Level 7
    34000,    # Level 8
    48000,    # Level 9
    64000,    # Level 10
    85000,    # Level 11
    100000,   # Level 12
    120000,   # Level 13
    140000,   # Level 14
    165000,   # Level 15
    195000,   # Level 16
    225000,   # Level 17
    265000,   # Level 18
    305000,   # Level 19
    355000,   # Level 20
]

XP_BY_CR = {
    0: 10, 0.125: 25, 0.25: 50, 0.5: 100,
    1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800,
    6: 2300, 7: 2900, 8: 3900, 9: 5000, 10: 5900,
    11: 7200, 12: 8400, 13: 10000, 14: 11500, 15: 13000,
    16: 15000, 17: 18000, 18: 20000, 19: 22000, 20: 25000,
    21: 33000, 22: 41000, 23: 50000, 24: 62000, 25: 75000,
    26: 90000, 27: 105000, 28: 120000, 29: 135000, 30: 155000
}

PROFICIENCY_BY_LEVEL = {
    1: 2, 2: 2, 3: 2, 4: 2,
    5: 3, 6: 3, 7: 3, 8: 3,
    9: 4, 10: 4, 11: 4, 12: 4,
    13: 5, 14: 5, 15: 5, 16: 5,
    17: 6, 18: 6, 19: 6, 20: 6
}


def _coerce_int(value: Any, default: int | None = 0) -> int | None:
    """
    Safely coerce value to int.

    Handles string numbers from JSON/LLM responses and floats.

    Args:
        value: The value to coerce (int, str, float, or other)
        default: Default value if coercion fails (can be None)

    Returns:
        Integer value or default
    """
    if value is None:
        return default
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    if isinstance(value, float):
        return int(value)
    return default


def level_from_xp(xp: int) -> int:
    """
    Calculate character level from cumulative XP using D&D 5e thresholds.

    Args:
        xp: Current cumulative experience points (clamped to 0 if negative).
            Accepts int, str, or float - coerced to int.

    Returns:
        Character level (1-20)

    Examples:
        >>> level_from_xp(0)
        1
        >>> level_from_xp(300)
        2
        >>> level_from_xp(5000)
        4
        >>> level_from_xp(500000)
        20
        >>> level_from_xp("5000")  # String input from JSON
        4
    """
    # Coerce to int for type safety (handles strings from JSON/LLM)
    xp = _coerce_int(xp, 0)
    # Clamp negative XP to 0
    xp = max(0, xp)

    # Find the highest level threshold that XP meets or exceeds
    level = 1
    for i, threshold in enumerate(XP_THRESHOLDS):
        if xp >= threshold:
            level = i + 1
        else:
            break

    return level


def xp_needed_for_level(level: int) -> int:
    """
    Get the cumulative XP required to reach a specific level.

    Args:
        level: Target level (clamped to 1-20 range).
               Accepts int, str, or float - coerced to int.

    Returns:
        Cumulative XP required for that level

    Examples:
        >>> xp_needed_for_level(1)
        0
        >>> xp_needed_for_level(5)
        6500
        >>> xp_needed_for_level(20)
        355000
        >>> xp_needed_for_level("5")  # String input from JSON
        6500
    """
    # Coerce to int for type safety
    level = _coerce_int(level, 1)
    # Clamp level to valid range
    level = max(1, min(20, level))
    return XP_THRESHOLDS[level - 1]


def xp_to_next_level(current_xp: int, current_level: int = None) -> int:
    """
    Calculate XP remaining to reach the next level.

    Args:
        current_xp: Current cumulative XP.
                    Accepts int, str, or float - coerced to int.
        current_level: Optional current level to optimize calculation.

    Returns:
        XP needed to reach next level (0 if at max level 20)

    Examples:
        >>> xp_to_next_level(0)
        300
        >>> xp_to_next_level(150)
        150
        >>> xp_to_next_level(355000)
        0
        >>> xp_to_next_level("150")  # String input from JSON
        150
    """
    # Coerce to int for type safety
    current_xp = _coerce_int(current_xp, 0)
    current_xp = max(0, current_xp)
    
    if current_level is None:
        current_level = level_from_xp(current_xp)
    else:
        current_level = _coerce_int(current_level, level_from_xp(current_xp))
        current_level = max(1, min(20, current_level))

    # At max level, no more XP needed
    if current_level >= 20:
        return 0

    next_threshold = XP_THRESHOLDS[current_level]  # Index is level since we need level+1
    return next_threshold - current_xp


class GameState:
    """
    A class to hold and manage game state data, behaving like a flexible dictionary.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initializes the GameState object with arbitrary data."""
        # Set default values for core attributes if they are not provided
        self.game_state_version = kwargs.get("game_state_version", 1)
        self.player_character_data = kwargs.get("player_character_data", {})
        self.world_data = kwargs.get("world_data", {})
        self.npc_data = kwargs.get("npc_data", {})
        self.custom_campaign_state = kwargs.get("custom_campaign_state", {})

        # Ensure attribute_system is set (defaults to Destiny system)
        if "attribute_system" not in self.custom_campaign_state:
            self.custom_campaign_state["attribute_system"] = (
                constants.DEFAULT_ATTRIBUTE_SYSTEM
            )

        self.combat_state = kwargs.get("combat_state", {"in_combat": False})
        self.last_state_update_timestamp = kwargs.get(
            "last_state_update_timestamp", datetime.datetime.now(datetime.UTC)
        )

        # Initialize time pressure structures
        self.time_sensitive_events = kwargs.get("time_sensitive_events", {})
        self.npc_agendas = kwargs.get("npc_agendas", {})
        self.world_resources = kwargs.get("world_resources", {})
        self.time_pressure_warnings = kwargs.get("time_pressure_warnings", {})

        # Debug mode flag
        self.debug_mode = kwargs.get("debug_mode", constants.DEFAULT_DEBUG_MODE)

        # Dynamically set any other attributes from kwargs
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)

        # Apply time consolidation migration
        self._consolidate_time_tracking()

    def to_dict(self) -> dict:
        """Serializes the GameState object to a dictionary for Firestore."""
        # Copy all attributes from the instance's __dict__
        data = self.__dict__.copy()

        # Remove any internal cache attributes that shouldn't be serialized
        # These are typically prefixed with underscore and added at runtime
        keys_to_remove = [
            key for key in data if key.startswith("_") and key != "__dict__"
        ]
        for key in keys_to_remove:
            del data[key]

        return data

    @classmethod
    def from_dict(cls, source: dict[str, Any] | None) -> Optional["GameState"]:
        """Creates a GameState object from a dictionary (e.g., from Firestore)."""
        if not source:
            return None

        # The constructor now directly accepts the dictionary.
        return cls(**source)

    def validate_checkpoint_consistency(self, narrative_text: str) -> list[str]:
        """
        Validates that critical checkpoint data in the state matches references in the narrative.
        Returns a list of discrepancies found.
        """
        discrepancies = []
        narrative_lower = narrative_text.lower()

        # Check player character HP consistency
        if "player_character_data" in self.__dict__:
            pc_data = self.player_character_data
            hp_current = pc_data.get("hp_current")
            hp_max = pc_data.get("hp_max")

            if hp_current is not None and hp_max is not None and hp_max > 0:
                # Check for unconscious/death vs HP mismatch
                if (
                    "unconscious" in narrative_lower
                    or "lies unconscious" in narrative_lower
                ):
                    if hp_current > 0:
                        discrepancies.append(
                            f"Narrative mentions unconsciousness but HP is {hp_current}/{hp_max}"
                        )

                if any(
                    phrase in narrative_lower
                    for phrase in ["completely drained", "drained of life"]
                ):
                    if hp_current > 5:  # Should be very low if "drained of life"
                        discrepancies.append(
                            f"Narrative describes being drained of life but HP is {hp_current}/{hp_max}"
                        )

                hp_percentage = (hp_current / hp_max) * 100

                # Check for narrative/state HP mismatches
                if hp_percentage < 25:  # Critically wounded
                    if not any(
                        word in narrative_lower
                        for word in [
                            "wounded",
                            "injured",
                            "hurt",
                            "bleeding",
                            "pain",
                            "unconscious",
                        ]
                    ):
                        discrepancies.append(
                            f"State shows character critically wounded ({hp_current}/{hp_max} HP) but narrative doesn't reflect injury"
                        )
                elif hp_percentage > 90:  # Healthy
                    if any(
                        word in narrative_lower
                        for word in [
                            "wounded",
                            "injured",
                            "bleeding",
                            "dying",
                            "unconscious",
                        ]
                    ):
                        discrepancies.append(
                            f"Narrative describes character as injured but state shows healthy ({hp_current}/{hp_max} HP)"
                        )
            elif hp_current is not None and hp_max == 0:
                # Skip validation only during character creation when HP is not yet initialized
                campaign_state = self.world_data.get("campaign_state", "")
                character_creation = self.custom_campaign_state.get(
                    "character_creation", {}
                )
                is_character_creation = (
                    campaign_state == "character_creation"
                    or character_creation.get("in_progress", False)
                )
                if not is_character_creation:
                    discrepancies.append(
                        f"Character has invalid HP state: {hp_current}/{hp_max} (hp_max should not be 0 outside character creation)"
                    )

        # Check location consistency
        current_location = self.world_data.get(
            "current_location_name"
        ) or self.world_data.get("current_location")
        if current_location:
            # Handle dict location objects by extracting name
            if isinstance(current_location, dict):
                current_location = current_location.get("name", "")

            # Ensure we have a string before calling lower()
            if isinstance(current_location, str):
                location_lower = current_location.lower()
            else:
                location_lower = str(current_location).lower()

            # If narrative mentions being in a specific place that doesn't match state
            if "forest" in narrative_lower and "tavern" in location_lower:
                discrepancies.append(
                    f"State location '{current_location}' conflicts with narrative mentioning forest"
                )
            elif "tavern" in narrative_lower and "forest" in location_lower:
                discrepancies.append(
                    f"State location '{current_location}' conflicts with narrative mentioning tavern"
                )

        # Check active missions consistency
        active_missions = self.custom_campaign_state.get("active_missions", [])
        if active_missions:
            for mission in active_missions:
                if isinstance(mission, dict):
                    mission_name = (
                        mission.get("name") or mission.get("title") or str(mission)
                    )
                else:
                    mission_name = str(mission)

                mission_lower = mission_name.lower()

                # Check for specific mission completion phrases
                if "dragon" in mission_lower and any(
                    phrase in narrative_lower
                    for phrase in ["dragon finally defeated", "dragon defeated"]
                ):
                    discrepancies.append(
                        f"Mission '{mission_name}' appears completed in narrative but still active in state"
                    )

                if "treasure" in mission_lower and any(
                    phrase in narrative_lower
                    for phrase in ["treasure secured", "treasure found"]
                ):
                    discrepancies.append(
                        f"Mission '{mission_name}' appears completed in narrative but still active in state"
                    )

        return discrepancies

    # Combat Management Methods

    def start_combat(self, combatants_data: list[dict[str, Any]]) -> None:
        """
        Initialize combat state with given combatants.

        Args:
            combatants_data: List of dicts with keys: name, initiative, type, hp_current, hp_max
        """
        logging_util.info(
            f"COMBAT STARTED - Participants: {[c['name'] for c in combatants_data]}"
        )

        # Sort by initiative (highest first)
        sorted_combatants = sorted(
            combatants_data, key=lambda x: x["initiative"], reverse=True
        )

        self.combat_state = {
            "in_combat": True,
            "current_round": 1,
            "current_turn_index": 0,
            "initiative_order": [
                {
                    "name": c["name"],
                    "initiative": c["initiative"],
                    "type": c.get("type", "unknown"),
                }
                for c in sorted_combatants
            ],
            "combatants": {
                c["name"]: {
                    "hp_current": c.get("hp_current", 1),
                    "hp_max": c.get("hp_max", 1),
                    "status": c.get("status", []),
                }
                for c in sorted_combatants
            },
            "combat_log": [],
        }

        initiative_list = [f"{c['name']}({c['initiative']})" for c in sorted_combatants]
        logging_util.info(f"COMBAT INITIALIZED - Initiative order: {initiative_list}")

    def end_combat(self) -> None:
        """End combat and reset combat state."""
        if self.combat_state.get("in_combat", False):
            final_round = self.combat_state.get("current_round", 0)
            participants = list(self.combat_state.get("combatants", {}).keys())

            # Clean up defeated enemies before ending combat
            defeated_enemies = self.cleanup_defeated_enemies()
            if defeated_enemies:
                logging_util.info(
                    f"COMBAT CLEANUP: Defeated enemies removed during combat end: {defeated_enemies}"
                )

            logging_util.info(
                f"COMBAT ENDED - Duration: {final_round} rounds, Participants: {participants}"
            )

        # Reset combat state
        self.combat_state = {
            "in_combat": False,
            "current_round": 0,
            "current_turn_index": 0,
            "initiative_order": [],
            "combatants": {},
            "combat_log": [],
        }

    def _is_named_npc(self, npc: dict[str, Any]) -> bool:
        """Return True if the NPC should be preserved (named/important)."""
        role_raw = npc.get("role")
        role_normalized = (
            role_raw.lower().strip() if isinstance(role_raw, str) else role_raw
        )

        generic_roles = {None, "", "enemy", "minion", "generic", "unknown"}
        has_named_role = role_normalized not in generic_roles
        has_story = npc.get("backstory") or npc.get("background")
        return bool(has_named_role or has_story or npc.get("is_important"))

    def cleanup_defeated_enemies(self) -> list[str]:
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

        # Handle both dict and list formats for combatants
        # AI sometimes generates combatants as a list instead of dict
        if isinstance(combatants, list):
            # Convert list format to dict format for processing
            combatants_dict = {}
            for combatant in combatants:
                if isinstance(combatant, dict) and "name" in combatant:
                    name = combatant["name"]
                    combatants_dict[name] = combatant
            combatants = combatants_dict
            # Update the combat_state with the normalized dict format
            self.combat_state["combatants"] = combatants_dict

        # Find defeated enemies (HP <= 0)
        for name, combat_data in combatants.items():
            hp_current = _coerce_int(combat_data.get("hp_current", 0), 0)
            if hp_current <= 0:
                # Check if this is an enemy (not PC, companion, or ally)
                enemy_type_raw: Any = None
                for init_entry in self.combat_state.get("initiative_order", []):
                    if init_entry["name"] == name:
                        enemy_type_raw = init_entry.get("type")
                        break

                if enemy_type_raw is None:
                    # Fallback to combatant metadata when initiative entry is missing
                    enemy_type_raw = combat_data.get("type") or combat_data.get("role")

                if enemy_type_raw is None and name in self.npc_data:
                    # Final fallback to npc_data for classification
                    npc_record = self.npc_data[name]
                    enemy_type_raw = npc_record.get("role") or npc_record.get("type")

                enemy_type = (
                    enemy_type_raw.lower().strip()
                    if isinstance(enemy_type_raw, str)
                    else enemy_type_raw
                )

                friendly_types = {"pc", "companion", "ally", "support", "friendly", "party", "player"}
                if enemy_type is None or enemy_type == "unknown":
                    # Attempt to infer friendliness from player or NPC metadata before defaulting to enemy cleanup
                    player_name = (
                        self.player_character_data.get("name")
                        if isinstance(self.player_character_data, dict)
                        else None
                    )
                    if player_name and name == player_name:
                        logging_util.info(
                            f"COMBAT CLEANUP: Skipping {name} removal because combatant matches player character with missing/unknown type"
                        )
                        continue

                    npc_record = (
                        self.npc_data.get(name)
                        if isinstance(self.npc_data, dict)
                        else None
                    )
                    npc_role_raw = npc_record.get("role") if isinstance(npc_record, dict) else None
                    npc_type_raw = npc_record.get("type") if isinstance(npc_record, dict) else None
                    npc_role = (
                        npc_role_raw.lower().strip()
                        if isinstance(npc_role_raw, str)
                        else npc_role_raw
                    )
                    npc_type = (
                        npc_type_raw.lower().strip()
                        if isinstance(npc_type_raw, str)
                        else npc_type_raw
                    )

                    if npc_role in friendly_types or npc_type in friendly_types:
                        logging_util.info(
                            f"COMBAT CLEANUP: Skipping {name} removal because npc_data marks combatant as friendly "
                            f"(role/type: {npc_role or npc_type}) despite missing initiative type"
                        )
                        continue

                    # Default to treating missing/unknown types as generic enemies to avoid leaving defeated foes targetable
                    logging_util.warning(
                        f"COMBAT CLEANUP: Defaulting {name} to generic enemy because type is missing/unknown "
                        f"(initiative entry absent or incomplete)"
                    )
                    enemy_type = "enemy"

                if enemy_type in friendly_types:
                    logging_util.info(
                        f"COMBAT CLEANUP: Skipping {name} because combatant is friendly ({enemy_type})"
                    )
                    continue

                defeated_enemies.append(name)
                logging_util.info(
                    f"COMBAT CLEANUP: Marking {name} ({enemy_type}) as defeated"
                )

        # Remove defeated enemies from combat tracking
        for enemy_name in defeated_enemies:
            # Remove from combat_state combatants
            if enemy_name in self.combat_state.get("combatants", {}):
                del self.combat_state["combatants"][enemy_name]
                logging_util.info(
                    f"COMBAT CLEANUP: Removed {enemy_name} from combat_state.combatants"
                )

            # Remove from initiative order
            self.combat_state["initiative_order"] = [
                entry
                for entry in self.combat_state.get("initiative_order", [])
                if entry["name"] != enemy_name
            ]

            # Handle NPC data - mark named NPCs as dead, delete generic enemies
            if enemy_name in self.npc_data:
                npc = self.npc_data[enemy_name]
                # Check if this is a named/important NPC (has role, backstory, or is explicitly important)
                # Named NPCs should be preserved with dead status for narrative continuity
                if self._is_named_npc(npc):
                    # Mark as dead instead of deleting - preserve for narrative continuity
                    if "status" not in npc:
                        npc["status"] = []
                    elif not isinstance(npc["status"], list):
                        status_value = npc["status"]
                        npc["status"] = [] if status_value is None else [status_value]
                    if "dead" not in npc["status"]:
                        npc["status"].append("dead")
                    npc["hp_current"] = 0
                    logging_util.info(f"COMBAT CLEANUP: Marked {enemy_name} as dead in npc_data (named NPC preserved)")
                else:
                    # Generic enemies can be deleted
                    del self.npc_data[enemy_name]
                    logging_util.info(f"COMBAT CLEANUP: Removed {enemy_name} from npc_data (generic enemy)")

        return defeated_enemies

    def _consolidate_time_tracking(self) -> None:
        """
        Consolidate time tracking from separate fields into a single object.
        Migrates old time_of_day field into world_time object if needed.
        """
        if not hasattr(self, "world_data") or not self.world_data:
            return

        world_data = self.world_data

        # Check if we have the old separate time_of_day field
        if "time_of_day" in world_data:
            # Migrate time_of_day into world_time object
            old_time_of_day = world_data["time_of_day"]

            # Ensure world_time exists and is a dict
            if "world_time" not in world_data:
                # Create world_time with reasonable defaults based on time_of_day
                hour = self._estimate_hour_from_time_of_day(old_time_of_day)
                world_data["world_time"] = {
                    "hour": hour,
                    "minute": 0,
                    "second": 0,
                    "microsecond": 0,
                    "time_of_day": old_time_of_day,
                }
            elif not isinstance(world_data["world_time"], dict):
                world_data["world_time"] = {
                    "hour": 12,
                    "minute": 0,
                    "second": 0,
                    "microsecond": 0,
                }
                world_data["world_time"]["time_of_day"] = old_time_of_day
            else:
                # world_time exists and is dict, just add time_of_day
                world_data["world_time"]["time_of_day"] = old_time_of_day

            # Remove the old field
            del world_data["time_of_day"]
            logging_util.info(
                f"Migrated time_of_day '{old_time_of_day}' into world_time object"
            )

        # Only process world_time if it already exists
        if "world_time" in world_data and isinstance(world_data["world_time"], dict):
            # Ensure microsecond field exists (default to 0 for existing campaigns)
            if "microsecond" not in world_data["world_time"]:
                world_data["world_time"]["microsecond"] = 0
                logging_util.info(
                    "Added microsecond field to world_time (default: 0)"
                )

            # Calculate time_of_day from hour if not present
            if "time_of_day" not in world_data["world_time"]:
                try:
                    hour = int(world_data["world_time"].get("hour", 12))
                except (ValueError, TypeError):
                    hour = 12  # Default to midday if conversion fails
                world_data["world_time"]["time_of_day"] = self._calculate_time_of_day(
                    hour
                )
                logging_util.info(
                    f"Calculated time_of_day as '{world_data['world_time']['time_of_day']}' from hour {hour}"
                )

    def _calculate_time_of_day(self, hour: int) -> str:
        """
        Calculate descriptive time of day from hour value.

        Args:
            hour: Hour value (0-23)

        Returns:
            String description of time of day
        """
        if 0 <= hour <= 4:
            return "Deep Night"
        if 5 <= hour <= 6:
            return "Dawn"
        if 7 <= hour <= 11:
            return "Morning"
        if 12 <= hour <= 13:
            return "Midday"
        if 14 <= hour <= 17:
            return "Afternoon"
        if 18 <= hour <= 19:
            return "Evening"
        if 20 <= hour <= 23:
            return "Night"
        return "Unknown"

    def _estimate_hour_from_time_of_day(self, time_of_day: str) -> int:
        """
        Estimate a reasonable hour value from a time of day description.
        Used for migration when we have time_of_day but no hour.

        Args:
            time_of_day: String description like "Morning", "Evening", etc.

        Returns:
            Integer hour value (0-23)
        """
        time_mapping = {
            "deep night": 2,  # Middle of deep night
            "dawn": 6,  # Dawn hour
            "morning": 9,  # Mid-morning
            "midday": 12,  # Noon
            "afternoon": 15,  # Mid-afternoon
            "evening": 18,  # Early evening
            "night": 21,  # Mid-night
        }

        # Normalize and look up
        normalized = time_of_day.lower().strip()
        return time_mapping.get(normalized, 12)  # Default to noon if unknown

    # =========================================================================
    # XP/Level Validation Methods
    # =========================================================================

    def validate_xp_level(self, strict: bool = False) -> dict[str, Any]:
        """
        Validate that the player's level matches their XP using D&D 5e thresholds.

        In default mode (strict=False):
        - Auto-corrects level mismatches and logs warnings
        - Clamps invalid XP/level values to valid ranges

        In strict mode (strict=True):
        - Raises ValueError on XP/level mismatch

        Args:
            strict: If True, raise ValueError on mismatches instead of auto-correcting

        Returns:
            Dict with validation results (flags describe the original input; corrected
            fields describe applied fixes):
            - valid: True if XP/level matched before any corrections or were missing
            - corrected: True if level was auto-corrected
            - expected_level: Computed level from XP
            - provided_level: Original level value
            - clamped_xp: XP after clamping (if negative)
            - clamped_level: Level after clamping (if out of range)

        Raises:
            ValueError: In strict mode, if XP/level mismatch is detected
        """
        result: dict[str, Any] = {"valid": True}

        pc_data = self.player_character_data
        if not isinstance(pc_data, dict) or not pc_data:
            return result  # No structured player data to validate

        # Get XP value - handle different possible structures
        # Supports: experience.current (dict), experience (scalar int/str), xp, xp_current
        xp_raw = None
        experience_val = pc_data.get("experience")
        if isinstance(experience_val, dict):
            # Experience stored as {"current": 2700, ...}
            xp_raw = experience_val.get("current")
        elif experience_val is not None:
            # Experience stored as scalar (int or str like 2700 or "2700")
            xp_raw = experience_val
        elif "xp" in pc_data:
            xp_raw = pc_data.get("xp")
        elif "xp_current" in pc_data:
            xp_raw = pc_data.get("xp_current")

        # Get level value (raw, before coercion)
        provided_level_raw = pc_data.get("level")

        # Coerce XP to int for type safety (handles strings from JSON/LLM)
        if xp_raw is None:
            # If no XP, assume 0 for level 1 character
            xp = 0
            result["assumed_xp"] = 0
        else:
            xp = _coerce_int(xp_raw, 0)

        # Coerce level to int if present (handles strings from JSON/LLM)
        provided_level = None
        if provided_level_raw is not None:
            provided_level = _coerce_int(provided_level_raw, None)

        # Clamp negative XP
        if xp < 0:
            result["clamped_xp"] = 0
            xp = 0
            # Persist clamped XP back to every known XP field to avoid divergence
            if isinstance(experience_val, dict):
                pc_data["experience"]["current"] = 0
            if experience_val is not None and not isinstance(experience_val, dict):
                pc_data["experience"] = 0
            if "xp" in pc_data:
                pc_data["xp"] = 0
            if "xp_current" in pc_data:
                pc_data["xp_current"] = 0
            logging_util.warning("XP validation: Negative XP clamped to 0")

        # Calculate expected level from XP
        expected_level = level_from_xp(xp)
        result["expected_level"] = expected_level

        # Handle missing level - compute from XP and PERSIST to state
        if provided_level is None:
            result["computed_level"] = expected_level
            # Persist computed level to state
            if hasattr(self, "player_character_data") and isinstance(
                self.player_character_data, dict
            ):
                self.player_character_data["level"] = expected_level
            return result

        # Store original level BEFORE clamping (per docstring: "Original level value")
        result["provided_level"] = provided_level

        # Clamp level to valid range (1-20)
        if provided_level < 1:
            result["clamped_level"] = 1
            logging_util.warning(f"XP validation: Level {provided_level} clamped to 1")
            provided_level = 1
            if hasattr(self, "player_character_data") and isinstance(
                self.player_character_data, dict
            ):
                self.player_character_data["level"] = provided_level
        elif provided_level > 20:
            result["clamped_level"] = 20
            logging_util.warning(f"XP validation: Level {provided_level} clamped to 20")
            provided_level = 20
            if hasattr(self, "player_character_data") and isinstance(
                self.player_character_data, dict
            ):
                self.player_character_data["level"] = provided_level

        # Check for mismatch
        if provided_level != expected_level:
            result["valid"] = False
            result["corrected"] = True

            message = (
                f"XP/Level mismatch: XP={xp} should be Level {expected_level}, "
                f"but provided Level {provided_level}"
            )

            if strict:
                raise ValueError(message)

            # Default: warn and auto-correct by persisting expected level
            logging_util.warning(
                f"XP validation: {message} - auto-correcting and persisting"
            )
            if hasattr(self, "player_character_data") and isinstance(
                self.player_character_data, dict
            ):
                self.player_character_data["level"] = expected_level
                result["corrected_level"] = expected_level

        return result

    # =========================================================================
    # Time Monotonicity Validation Methods
    # =========================================================================

    def validate_time_monotonicity(
        self,
        new_time: dict[str, Any],
        strict: bool = False,
        previous_time: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Validate that time progression is monotonic (never goes backwards).

        Args:
            new_time: Dict with time fields (hour, minute, optionally day)
            strict: If True, raise ValueError on backwards time

        Returns:
            Dict with validation results.
        """
        result: dict[str, Any] = {"valid": True}

        # Get reference time: prefer explicitly supplied previous_time (from caller),
        # otherwise fall back to the GameState's current world_data value.
        current_world_time = previous_time or (self.world_data or {}).get("world_time")
        if not current_world_time or not isinstance(current_world_time, dict):
            return result

        if not isinstance(new_time, dict):
            return result

        current_day = None
        if isinstance(current_world_time, dict):
            current_day = current_world_time.get("day")

        old_total = self._time_to_minutes(current_world_time)
        new_total = self._time_to_minutes(new_time, default_day=current_day)

        if new_total < old_total:
            old_str = self._format_time(current_world_time)
            new_str = self._format_time(new_time)
            message = (
                f"Time regression detected: {new_str} is earlier than {old_str}"
            )

            if strict:
                raise ValueError(f"Time cannot go backwards: {message}")

            result["valid"] = True  # Still valid but with warning
            result["warning"] = True
            result["message"] = message
            logging_util.warning(f"Time monotonicity: {message}")

        return result

    def _time_to_minutes(self, time_dict: dict[str, Any], default_day: int | None = None) -> int:
        """Convert a time dict to total minutes for comparison."""
        fallback_day = 0 if default_day is None else _coerce_int(default_day, 0)
        day = _coerce_int(time_dict.get("day", fallback_day), fallback_day)
        hour = _coerce_int(time_dict.get("hour", 0), 0)
        minute = _coerce_int(time_dict.get("minute", 0), 0)

        return (day * 24 * 60) + (hour * 60) + minute

    def _format_time(self, time_dict: dict[str, Any]) -> str:
        """Format a time dict as a human-readable string."""
        day_raw = time_dict.get("day")
        day = _coerce_int(day_raw) if day_raw is not None else None
        hour = _coerce_int(time_dict.get("hour", 0), 0)
        minute = _coerce_int(time_dict.get("minute", 0), 0)

        if day is not None:
            return f"Day {day}, {hour:02d}:{minute:02d}"
        return f"{hour:02d}:{minute:02d}"

    # Combat Management Methods

    def start_combat(self, combatants_data: list[dict[str, Any]]) -> None:
        """Initialize combat state with given combatants."""
        logging_util.info(
            f"COMBAT STARTED - Participants: {[c['name'] for c in combatants_data]}"
        )

        sorted_combatants = sorted(
            combatants_data, key=lambda x: x["initiative"], reverse=True
        )

        self.combat_state = {
            "in_combat": True,
            "current_round": 1,
            "current_turn_index": 0,
            "initiative_order": [
                {
                    "name": c["name"],
                    "initiative": c["initiative"],
                    "type": c.get("type", "unknown"),
                }
                for c in sorted_combatants
            ],
            "combatants": {
                c["name"]: {
                    "hp_current": c.get("hp_current", 1),
                    "hp_max": c.get("hp_max", 1),
                    "status": c.get("status", []),
                }
                for c in sorted_combatants
            },
            "combat_log": [],
        }

        initiative_list = [f"{c['name']}({c['initiative']})" for c in sorted_combatants]
        logging_util.info(f"COMBAT INITIALIZED - Initiative order: {initiative_list}")

    def end_combat(self) -> None:
        """End combat and reset combat state."""
        if self.combat_state.get("in_combat", False):
            final_round = self.combat_state.get("current_round", 0)
            participants = list(self.combat_state.get("combatants", {}).keys())

            defeated_enemies = self.cleanup_defeated_enemies()
            if defeated_enemies:
                logging_util.info(
                    f"COMBAT CLEANUP: Defeated enemies removed during combat end: {defeated_enemies}"
                )

            logging_util.info(
                f"COMBAT ENDED - Duration: {final_round} rounds, Participants: {participants}"
            )

        self.combat_state = {
            "in_combat": False,
            "current_round": 0,
            "current_turn_index": 0,
            "initiative_order": [],
            "combatants": {},
            "combat_log": [],
        }

    def cleanup_defeated_enemies(self) -> list[str]:
        """
        Identifies defeated enemies and synchronizes combat_state with npc_data.

        Rules:
        - Remove defeated enemies from combat_state/initiative_order.
        - If the enemy is a named/important NPC (role/backstory/is_important), keep it
          in npc_data and mark status=['dead'] with hp_current=0.
        - Generic enemies (enemy/minion/etc.) are deleted from npc_data.
        """
        defeated_enemies: list[str] = []

        combatants = self.combat_state.get("combatants", {})
        if not combatants:
            return defeated_enemies

        # Normalize list format to dict if needed
        if isinstance(combatants, list):
            combatants_dict = {}
            for combatant in combatants:
                if isinstance(combatant, dict) and "name" in combatant:
                    combatants_dict[combatant["name"]] = combatant
            combatants = combatants_dict
            self.combat_state["combatants"] = combatants_dict

        friendly_types = {"pc", "companion", "ally", "support", "friendly", "party", "player"}

        for name, combat_data in combatants.items():
            hp_current = _coerce_int(combat_data.get("hp_current", 0), 0)
            if hp_current <= 0:
                enemy_type_raw: Any = None
                for init_entry in self.combat_state.get("initiative_order", []):
                    if init_entry["name"] == name:
                        enemy_type_raw = init_entry.get("type")
                        break

                if enemy_type_raw is None:
                    enemy_type_raw = combat_data.get("type") or combat_data.get("role")
                if enemy_type_raw is None and name in self.npc_data:
                    npc_record = self.npc_data[name]
                    enemy_type_raw = npc_record.get("role") or npc_record.get("type")

                enemy_type = (
                    enemy_type_raw.lower().strip()
                    if isinstance(enemy_type_raw, str)
                    else enemy_type_raw
                )

                if enemy_type in friendly_types:
                    logging_util.info(
                        f"COMBAT CLEANUP: Skipping {name} because combatant is friendly ({enemy_type})"
                    )
                    continue

                if enemy_type is None or enemy_type == "unknown":
                    npc_record = self.npc_data.get(name, {}) if isinstance(self.npc_data, dict) else {}
                    npc_role = npc_record.get("role")
                    npc_type = npc_record.get("type")
                    npc_role_norm = npc_role.lower().strip() if isinstance(npc_role, str) else npc_role
                    npc_type_norm = npc_type.lower().strip() if isinstance(npc_type, str) else npc_type
                    if npc_role_norm in friendly_types or npc_type_norm in friendly_types:
                        logging_util.info(
                            f"COMBAT CLEANUP: Skipping {name} removal because npc_data marks combatant as friendly"
                        )
                        continue
                    logging_util.warning(
                        f"COMBAT CLEANUP: Defaulting {name} to generic enemy because type is missing/unknown"
                    )
                    enemy_type = "enemy"

                defeated_enemies.append(name)
                logging_util.info(f"COMBAT CLEANUP: Marking {name} ({enemy_type}) as defeated")

        for enemy_name in defeated_enemies:
            # Remove from combat tracking
            if enemy_name in self.combat_state.get("combatants", {}):
                del self.combat_state["combatants"][enemy_name]
                logging_util.info(f"COMBAT CLEANUP: Removed {enemy_name} from combat_state.combatants")

            self.combat_state["initiative_order"] = [
                entry for entry in self.combat_state.get("initiative_order", []) if entry["name"] != enemy_name
            ]

            # Sync npc_data
            if enemy_name in self.npc_data:
                npc = self.npc_data[enemy_name]
                if self._is_named_npc(npc):
                    if "status" not in npc or npc["status"] is None:
                        npc["status"] = []
                    if not isinstance(npc["status"], list):
                        npc["status"] = [npc["status"]]
                    if "dead" not in npc["status"]:
                        npc["status"].append("dead")
                    npc["hp_current"] = 0
                    logging_util.info(f"COMBAT CLEANUP: Marked {enemy_name} as dead in npc_data (named NPC preserved)")
                else:
                    del self.npc_data[enemy_name]
                    logging_util.info(f"COMBAT CLEANUP: Removed {enemy_name} from npc_data (generic enemy)")

        return defeated_enemies

    def _consolidate_time_tracking(self) -> None:
        """Consolidate time tracking from separate fields into a single object."""
        if not hasattr(self, "world_data") or not self.world_data:
            return

        world_data = self.world_data

        if "time_of_day" in world_data:
            old_time_of_day = world_data["time_of_day"]

            if "world_time" not in world_data:
                hour = self._estimate_hour_from_time_of_day(old_time_of_day)
                world_data["world_time"] = {
                    "hour": hour,
                    "minute": 0,
                    "second": 0,
                    "microsecond": 0,
                    "time_of_day": old_time_of_day,
                }
            elif not isinstance(world_data["world_time"], dict):
                world_data["world_time"] = {
                    "hour": 12,
                    "minute": 0,
                    "second": 0,
                    "microsecond": 0,
                }
                world_data["world_time"]["time_of_day"] = old_time_of_day
            else:
                world_data["world_time"]["time_of_day"] = old_time_of_day

            del world_data["time_of_day"]
            logging_util.info(
                f"Migrated time_of_day '{old_time_of_day}' into world_time object"
            )

        if "world_time" in world_data and isinstance(world_data["world_time"], dict):
            if "microsecond" not in world_data["world_time"]:
                world_data["world_time"]["microsecond"] = 0
                logging_util.info(
                    "Added microsecond field to world_time (default: 0)"
                )

            if "time_of_day" not in world_data["world_time"]:
                try:
                    hour = int(world_data["world_time"].get("hour", 12))
                except (ValueError, TypeError):
                    hour = 12
                world_data["world_time"]["time_of_day"] = self._calculate_time_of_day(
                    hour
                )
                logging_util.info(
                    f"Calculated time_of_day as '{world_data['world_time']['time_of_day']}' from hour {hour}"
                )

    def _calculate_time_of_day(self, hour: int) -> str:
        """Calculate descriptive time of day from hour value."""
        if 0 <= hour <= 4:
            return "Deep Night"
        if 5 <= hour <= 6:
            return "Dawn"
        if 7 <= hour <= 11:
            return "Morning"
        if 12 <= hour <= 13:
            return "Midday"
        if 14 <= hour <= 17:
            return "Afternoon"
        if 18 <= hour <= 19:
            return "Evening"
        if 20 <= hour <= 23:
            return "Night"
        return "Unknown"

    def _estimate_hour_from_time_of_day(self, time_of_day: str) -> int:
        """Estimate a reasonable hour value from a time of day description."""
        time_mapping = {
            "deep night": 2,
            "dawn": 6,
            "morning": 9,
            "midday": 12,
            "afternoon": 15,
            "evening": 18,
            "night": 21,
        }
        normalized = time_of_day.lower().strip()
        return time_mapping.get(normalized, 12)


# =============================================================================
# DICE ROLL TOOL DEFINITIONS (for tool use / function calling)
# =============================================================================

DICE_ROLL_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "roll_dice",
            "description": "Roll dice for damage, healing, or random effects ONLY. "
            "DO NOT use for skill checks, attacks, or saving throws - use the specific tools instead. "
            "This tool just returns numbers, it does NOT determine success/failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "notation": {
                        "type": "string",
                        "description": "Dice notation (e.g., '2d6+3' for damage, '1d8' for healing)",
                    },
                    "purpose": {
                        "type": "string",
                        "description": "What this roll is for (e.g., 'damage', 'healing', 'random table')",
                    },
                },
                "required": ["notation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "roll_attack",
            "description": "Roll a COMPLETE attack with hit check vs AC and damage if hit. Returns success/failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attack_modifier": {
                        "type": "integer",
                        "description": "Total attack bonus (ability + proficiency combined)",
                    },
                    "ability_modifier": {
                        "type": "integer",
                        "description": "Ability modifier component (STR or DEX)",
                    },
                    "ability_name": {
                        "type": "string",
                        "description": "Ability used for attack: STR or DEX",
                    },
                    "proficiency_bonus": {
                        "type": "integer",
                        "description": "Proficiency bonus component",
                    },
                    "weapon_name": {
                        "type": "string",
                        "description": "Name of the weapon used (e.g., 'Longsword', 'Shortbow')",
                    },
                    "damage_notation": {
                        "type": "string",
                        "description": "Damage dice (e.g., '1d8+3')",
                    },
                    "target_ac": {
                        "type": "integer",
                        "description": "Target's Armor Class",
                    },
                    "advantage": {"type": "boolean", "default": False},
                    "disadvantage": {"type": "boolean", "default": False},
                },
                "required": ["attack_modifier", "damage_notation", "target_ac"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "roll_skill_check",
            "description": "Roll a skill check vs a DC. Covers ALL skills: "
            "Persuasion, Intimidation, Deception (social), Perception, Stealth, Investigation, "
            "Athletics, Acrobatics, Thieves' Tools, etc. "
            "ALWAYS use this for skill checks - it returns success/failure based on DC comparison. "
            "Examples: Persuasion to convince an NPC, Intimidation to threaten, "
            "Stealth to sneak past guards, Thieves' Tools to pick a lock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attribute_modifier": {"type": "integer", "description": "Relevant ability modifier (DEX for Stealth, INT for Investigation, etc.)"},
                    "attribute_name": {"type": "string", "description": "Ability score abbreviation: STR, DEX, CON, INT, WIS, or CHA"},
                    "proficiency_bonus": {"type": "integer", "description": "Character's proficiency bonus (typically 2-6)"},
                    "proficient": {"type": "boolean", "default": False, "description": "True if proficient in this skill"},
                    "expertise": {"type": "boolean", "default": False, "description": "True if character has expertise (double proficiency)"},
                    "dc": {"type": "integer", "description": "Difficulty Class to beat (10=easy, 15=medium, 20=hard, 25=very hard)"},
                    "skill_name": {"type": "string", "description": "Name of the skill (e.g., 'Thieves Tools', 'Stealth', 'Perception')"},
                },
                "required": ["attribute_modifier", "attribute_name", "proficiency_bonus", "dc", "skill_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "roll_saving_throw",
            "description": "Roll a saving throw vs a DC (e.g., DEX save vs fireball, WIS save vs charm). "
            "ALWAYS use this for saving throws - it returns success/failure based on DC comparison. "
            "Example: Thieves' Tools check to pick a lock, Stealth check to sneak past guards.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attribute_modifier": {"type": "integer", "description": "Relevant ability modifier for the save"},
                    "proficiency_bonus": {"type": "integer", "description": "Character's proficiency bonus"},
                    "proficient": {"type": "boolean", "default": False, "description": "True if proficient in this saving throw"},
                    "dc": {"type": "integer", "description": "Difficulty Class to beat"},
                    "save_type": {"type": "string", "description": "Type of save: STR, DEX, CON, INT, WIS, or CHA"},
                },
                "required": ["attribute_modifier", "proficiency_bonus", "dc", "save_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "declare_no_roll_needed",
            "description": "Declare that no dice roll is needed for this action. "
            "Use ONLY for trivial actions that auto-succeed: opening unlocked doors, picking up items, "
            "walking in safe areas, asking for directions, casual greetings. "
            "DO NOT use this for: combat, Persuasion/Intimidation/Deception checks, "
            "convincing resistant NPCs, negotiations, skill checks, saving throws, contested actions, "
            "or anything with meaningful risk/uncertainty. "
            "If an NPC is resisting or needs convincing, use roll_skill_check instead. "
            "You MUST provide a reason explaining why no roll is needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The player action being evaluated (e.g., 'open the unlocked door')",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why no dice roll is needed (e.g., 'Door is unlocked, no check required')",
                    },
                },
                "required": ["action", "reason"],
            },
        },
    },
]


def validate_and_correct_state(
    state_dict: dict[str, Any], previous_world_time: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Validate state dict and apply corrections before persistence.

    Uses GameState's internal validation logic.
    """
    # Create temporary GameState to run validations
    temp_state = GameState.from_dict(state_dict.copy())
    if temp_state is None:
        logging_util.warning(
            "VALIDATION: Could not create GameState from dict, skipping validation"
        )
        return state_dict

    # 1. XP/Level Validation (using Main's logic)
    # This modifies temp_state in-place (auto-corrects)
    xp_result = temp_state.validate_xp_level(strict=False)
    if xp_result.get("corrected") or xp_result.get("computed_level"):
        logging_util.info(f"XP Validation applied corrections: {xp_result}")

    # 2. Time Monotonicity (using Main's logic)
    # Get current time from world_data in state_dict (not temp_state, as we want to check input)
    new_time = (state_dict.get("world_data", {}) or {}).get("world_time")
    if new_time:
        # Note: In strict mode this raises, in default mode it just warns
        temp_state.validate_time_monotonicity(
            new_time, strict=False, previous_time=previous_world_time
        )

    return temp_state.to_dict()


def calculate_modifier(attribute: int) -> int:
    """Calculate ability modifier from attribute score."""
    return (attribute - 10) // 2


def calculate_proficiency_bonus(level: int) -> int:
    """Get proficiency bonus for a given character level."""
    if level < 1: return 2
    if level > 20: return 6
    return PROFICIENCY_BY_LEVEL.get(level, 2)


def calculate_armor_class(dex_modifier: int, armor_bonus: int = 0, shield_bonus: int = 0) -> int:
    """Calculate Armor Class."""
    return 10 + dex_modifier + armor_bonus + shield_bonus


def calculate_passive_perception(wis_modifier: int, proficient: bool, proficiency_bonus: int) -> int:
    """Calculate passive Perception score."""
    base = 10 + wis_modifier
    if proficient:
        base += proficiency_bonus
    return base


def xp_for_cr(cr: float) -> int:
    """Get XP award for defeating a creature of given Challenge Rating."""
    return XP_BY_CR.get(cr, 0)


@dataclass
class DiceRollResult:
    """Result of a dice roll with full context.

    Basic fields (always present):
        notation: Dice notation like "1d20+5"
        individual_rolls: List of each die result
        modifier: Total numeric modifier
        total: Final result

    Context fields (optional, for rich formatting):
        purpose: What the roll is for (e.g., "Perception check")
        modifier_breakdown: Dict of label->value (e.g., {"WIS": 5, "PROF": 3})
        target_dc: The DC/AC to beat
        success: Whether the roll succeeded
    """
    notation: str
    individual_rolls: list[int]
    modifier: int
    total: int
    natural_20: bool = False
    natural_1: bool = False
    # Optional context for rich formatting
    purpose: str = ""
    modifier_breakdown: dict[str, int] | None = None
    target_dc: int | None = None
    success: bool | None = None

    def __str__(self) -> str:
        """Format dice roll as human-readable string with labeled modifiers.

        Full format (with all context):
            "Perception: 1d20 +5 WIS +3 PROF = 15 +5 WIS +3 PROF = 23 vs DC 15 (Success)"

        Basic format (without context):
            "1d20+3 = 15+3 = 18"
            "2d6+2 = [4+3]+2 = 9"
            "1d20 = 20 (NAT 20!)"
        """
        if not self.individual_rolls:
            return f"{self.notation} = {self.total}"

        # Format the dice roll portion (e.g., "15" or "[4+3]")
        if len(self.individual_rolls) == 1:
            rolls_value = str(self.individual_rolls[0])
        else:
            rolls_value = f"[{'+'.join(str(r) for r in self.individual_rolls)}]"
            # Also compute the sum for display
            rolls_sum = sum(self.individual_rolls)
            rolls_value = f"[{'+'.join(str(r) for r in self.individual_rolls)}={rolls_sum}]"

        # Build modifier string with labels if available
        if self.modifier_breakdown:
            # Format: "+5 WIS +3 PROF" (each modifier labeled)
            mod_parts = []
            for label, value in self.modifier_breakdown.items():
                if value >= 0:
                    mod_parts.append(f"+{value} {label}")
                else:
                    mod_parts.append(f"{value} {label}")
            mod_str = " ".join(mod_parts)
            mod_display = f" {mod_str}" if mod_str else ""
        else:
            # Basic format: just the number
            if self.modifier > 0:
                mod_str = f"+{self.modifier}"
                mod_display = mod_str
            elif self.modifier < 0:
                mod_str = str(self.modifier)
                mod_display = mod_str
            else:
                mod_str = ""
                mod_display = ""

        # Build the result string
        parts = []

        # Add purpose prefix if available
        if self.purpose:
            parts.append(f"{self.purpose}:")

        # Add the dice notation with labeled modifiers
        if self.modifier_breakdown:
            # Extract base die notation (e.g., "1d20" from "1d20+5")
            base_notation = self.notation.split('+')[0].split('-')[0]
            parts.append(f"{base_notation}{mod_display}")
        else:
            parts.append(self.notation)

        # Add the calculation: "= 15 +5 WIS +3 PROF = 23"
        if self.modifier_breakdown:
            parts.append(f"= {rolls_value}{mod_display} = {self.total}")
        elif mod_display:
            parts.append(f"= {rolls_value}{mod_display} = {self.total}")
        else:
            parts.append(f"= {rolls_value} = {self.total}")

        # Add DC/target and success/fail
        if self.target_dc is not None:
            parts.append(f"vs DC {self.target_dc}")
            if self.success is not None:
                parts.append(f"({'Success' if self.success else 'Fail'})")
            elif self.natural_20:
                parts.append("(NAT 20!)")
            elif self.natural_1:
                parts.append("(NAT 1!)")
        else:
            # No DC, just show natural 20/1
            if self.natural_20:
                parts[-1] += " (NAT 20!)"
            elif self.natural_1:
                parts[-1] += " (NAT 1!)"

        return " ".join(parts)


def roll_dice(notation: str) -> DiceRollResult:
    """
    Roll dice using standard notation (e.g., "2d6+3", "1d20-1", "4d6").
    """
    # Parse notation: XdY+Z or XdY-Z or XdY
    pattern = r"(\d+)d(\d+)([+-]\d+)?"
    match = re.match(pattern, notation.lower().replace(" ", ""))

    if not match:
        return DiceRollResult(notation, [], 0, 0)

    num_dice = int(match.group(1))
    die_size = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    if num_dice < 1 or die_size < 1:
        return DiceRollResult(notation, [], modifier, modifier)

    # Roll each die
    rolls = [random.randint(1, die_size) for _ in range(num_dice)]
    total = sum(rolls) + modifier

    natural_20 = die_size == 20 and num_dice == 1 and rolls[0] == 20
    natural_1 = die_size == 20 and num_dice == 1 and rolls[0] == 1

    return DiceRollResult(notation, rolls, modifier, total, natural_20, natural_1)


def roll_with_advantage(notation: str) -> tuple[DiceRollResult, DiceRollResult, int]:
    """Roll with advantage (roll twice, take higher)."""
    roll1 = roll_dice(notation)
    roll2 = roll_dice(notation)
    final = max(roll1.total, roll2.total)
    return roll1, roll2, final


def roll_with_disadvantage(notation: str) -> tuple[DiceRollResult, DiceRollResult, int]:
    """Roll with disadvantage (roll twice, take lower)."""
    roll1 = roll_dice(notation)
    roll2 = roll_dice(notation)
    final = min(roll1.total, roll2.total)
    return roll1, roll2, final


def calculate_attack_roll(attack_modifier: int, advantage: bool = False, disadvantage: bool = False) -> dict:
    """Perform a complete attack roll."""
    notation = f"1d20+{attack_modifier}" if attack_modifier >= 0 else f"1d20{attack_modifier}"

    def _safe_natural_roll(roll: DiceRollResult) -> int:
        if roll.individual_rolls:
            return int(roll.individual_rolls[0])
        # roll_dice can return empty rolls for invalid/degenerate notations; derive best-effort.
        return max(0, int(roll.total) - int(roll.modifier))

    if advantage and not disadvantage:
        roll1, roll2, total = roll_with_advantage(notation)
        natural_rolls = [_safe_natural_roll(roll1), _safe_natural_roll(roll2)]
        natural = max(natural_rolls)
        return {
            "rolls": natural_rolls, "modifier": attack_modifier, "total": total,
            "used_roll": "higher", "is_critical": natural == 20,
            "is_fumble": natural_rolls[0] == 1 and natural_rolls[1] == 1, "notation": notation
        }
    if disadvantage and not advantage:
        roll1, roll2, total = roll_with_disadvantage(notation)
        natural_rolls = [_safe_natural_roll(roll1), _safe_natural_roll(roll2)]
        natural = min(natural_rolls)
        return {
            "rolls": natural_rolls, "modifier": attack_modifier, "total": total,
            "used_roll": "lower", "is_critical": natural_rolls[0] == 20 and natural_rolls[1] == 20,
            "is_fumble": natural == 1, "notation": notation
        }
    roll = roll_dice(notation)
    return {
        "rolls": roll.individual_rolls, "modifier": attack_modifier, "total": roll.total,
        "used_roll": "single", "is_critical": roll.natural_20,
        "is_fumble": roll.natural_1, "notation": notation
    }


def calculate_damage(damage_notation: str, is_critical: bool = False) -> DiceRollResult:
    """Calculate damage, doubling dice on critical hit."""
    if is_critical:
        pattern = r"(\d+)d(\d+)([+-]\d+)?"
        match = re.match(pattern, damage_notation.lower().replace(" ", ""))
        if match:
            num_dice = int(match.group(1)) * 2
            die_size = match.group(2)
            modifier = match.group(3) or ""
            crit_notation = f"{num_dice}d{die_size}{modifier}"
            return roll_dice(crit_notation)
    return roll_dice(damage_notation)


def calculate_skill_check(attribute_modifier: int, proficiency_bonus: int, proficient: bool = False, expertise: bool = False) -> DiceRollResult:
    """Perform a skill check."""
    total_modifier = attribute_modifier
    if proficient or expertise:
        total_modifier += proficiency_bonus
    if expertise:
        total_modifier += proficiency_bonus
    notation = f"1d20+{total_modifier}" if total_modifier >= 0 else f"1d20{total_modifier}"
    return roll_dice(notation)


def calculate_saving_throw(attribute_modifier: int, proficiency_bonus: int, proficient: bool = False) -> DiceRollResult:
    """Perform a saving throw."""
    total_modifier = attribute_modifier
    if proficient:
        total_modifier += proficiency_bonus
    notation = f"1d20+{total_modifier}" if total_modifier >= 0 else f"1d20{total_modifier}"
    return roll_dice(notation)


def calculate_resource_depletion(current_amount: float, depletion_rate: float, time_elapsed: float, depletion_unit: str = "per_day") -> float:
    """Calculate resource depletion over time."""
    depleted = depletion_rate * time_elapsed
    remaining = current_amount - depleted
    return max(0, remaining)


def execute_dice_tool(tool_name: str, arguments: dict) -> dict:
    """Execute a dice roll tool call and return the result."""
    def _coerce_int_inner(value: Any, default: int = 0) -> int:
        if isinstance(value, bool): return int(value)
        try: return int(value)
        except (ValueError, TypeError): return default

    def _coerce_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool): return value
        if isinstance(value, str): return value.lower() in ("true", "1", "yes")
        if value is None: return default
        return bool(value)

    if tool_name == "roll_dice":
        notation = arguments.get("dice_notation") or arguments.get("notation", "1d20")
        purpose = arguments.get("purpose", "")
        result = roll_dice(notation)
        return {
            "notation": result.notation, "rolls": result.individual_rolls,
            "modifier": result.modifier, "total": result.total,
            "natural_20": result.natural_20, "natural_1": result.natural_1,
            "purpose": purpose, "formatted": str(result)
        }

    if tool_name == "roll_attack":
        raw_attack_mod = arguments.get("attack_modifier")
        if raw_attack_mod is None and "modifier" in arguments:
            raw_attack_mod = arguments.get("modifier")
        attack_mod = _coerce_int_inner(raw_attack_mod, 0)
        ability_mod = _coerce_int_inner(arguments.get("ability_modifier"), None)
        ability_name = arguments.get("ability_name", "").upper() or None
        prof_bonus = _coerce_int_inner(arguments.get("proficiency_bonus"), None)
        weapon_name = arguments.get("weapon_name", "")
        damage_notation = arguments.get("damage_notation") or arguments.get("damage_dice") or "1d6"
        target_ac = _coerce_int_inner(arguments.get("target_ac"), 10)
        advantage = _coerce_bool(arguments.get("advantage"), False)
        disadvantage = _coerce_bool(arguments.get("disadvantage"), False)

        attack = calculate_attack_roll(attack_mod, advantage, disadvantage)
        rolls = attack["rolls"]  # List of raw d20 rolls (1 for normal, 2 for adv/disadv)
        hit = not attack["is_fumble"] and (attack["total"] >= target_ac or attack["is_critical"])

        # Build labeled modifier breakdown: "Longsword: 1d20 +3 STR +2 PROF = 12 +3 STR +2 PROF = 17 vs AC 15 (Hit!)"
        mod_parts = []
        if ability_mod is not None and ability_name:
            mod_parts.append(f"+{ability_mod} {ability_name}" if ability_mod >= 0 else f"{ability_mod} {ability_name}")
        if prof_bonus is not None and prof_bonus > 0:
            mod_parts.append(f"+{prof_bonus} PROF")
        if not mod_parts:
            # Fallback: use combined modifier if components not provided
            mod_parts.append(f"+{attack_mod}" if attack_mod >= 0 else f"{attack_mod}")
        mod_str = " ".join(mod_parts)

        attack_label = weapon_name or "Attack"
        hit_str = "CRITICAL!" if attack["is_critical"] else ("FUMBLE!" if attack["is_fumble"] else ("Hit!" if hit else "Miss"))

        # Handle advantage/disadvantage display: show both rolls with which was used
        if len(rolls) == 2:
            used = attack.get("used_roll", "higher")
            roll_display = f"({rolls[0]}, {rolls[1]} - {used})"
        elif not rolls:
            roll_display = "0"
        else:
            roll_display = str(rolls[0])
        formatted = f"{attack_label}: 1d20 {mod_str} = {roll_display} {mod_str} = {attack['total']} vs AC {target_ac} ({hit_str})"

        result = {
            "attack_roll": attack, "target_ac": target_ac, "hit": hit,
            "critical": attack["is_critical"], "fumble": attack["is_fumble"],
            "weapon_name": weapon_name, "ability_name": ability_name,
            "formatted": formatted
        }
        if hit:
            damage = calculate_damage(damage_notation, attack["is_critical"])
            result["damage"] = {
                "notation": damage.notation, "rolls": damage.individual_rolls,
                "modifier": damage.modifier, "total": damage.total,
                "critical": attack["is_critical"]
            }
            # Append damage to formatted string
            result["formatted"] += f" | Damage: {damage}"
        else:
            result["damage"] = None
        return result

    if tool_name == "roll_skill_check":
        raw_attr_mod = arguments.get("attribute_modifier")
        if raw_attr_mod is None and "modifier" in arguments:
            raw_attr_mod = arguments.get("modifier")
        attr_mod = _coerce_int_inner(raw_attr_mod, 0)
        attr_name = arguments.get("attribute_name", "").upper() or "MOD"
        prof_bonus = _coerce_int_inner(arguments.get("proficiency_bonus"), 2)
        proficient = _coerce_bool(arguments.get("proficient"), False)
        expertise = _coerce_bool(arguments.get("expertise"), False)
        dc = _coerce_int_inner(arguments.get("dc"), 10)
        skill_name = arguments.get("skill_name") or arguments.get("skill") or ""

        result = calculate_skill_check(attr_mod, prof_bonus, proficient, expertise)
        roll = result.individual_rolls[0] if result.individual_rolls else 0
        success = result.total >= dc

        # Build labeled modifier breakdown: "1d20 +5 INT +3 PROF = 8 +5 INT +3 PROF = 16"
        mod_parts = [f"+{attr_mod} {attr_name}" if attr_mod >= 0 else f"{attr_mod} {attr_name}"]
        effective_prof = prof_bonus * (2 if expertise else 1) if proficient else 0
        if effective_prof > 0:
            prof_label = "EXPERT" if expertise else "PROF"
            mod_parts.append(f"+{effective_prof} {prof_label}")
        mod_str = " ".join(mod_parts)
        formatted = f"{skill_name}: 1d20 {mod_str} = {roll} {mod_str} = {result.total} vs DC {dc} ({'Success' if success else 'Fail'})"

        return {
            "skill": skill_name, "roll": roll,
            "modifier": result.modifier, "total": result.total, "dc": dc, "success": success,
            "natural_20": result.natural_20, "natural_1": result.natural_1,
            "attribute_name": attr_name, "proficiency_applied": effective_prof,
            "formatted": formatted
        }

    if tool_name == "roll_saving_throw":
        raw_attr_mod = arguments.get("attribute_modifier")
        if raw_attr_mod is None and "modifier" in arguments:
            raw_attr_mod = arguments.get("modifier")
        attr_mod = _coerce_int_inner(raw_attr_mod, 0)
        prof_bonus = _coerce_int_inner(arguments.get("proficiency_bonus"), 2)
        proficient = _coerce_bool(arguments.get("proficient"), False)
        dc = _coerce_int_inner(arguments.get("dc"), 10)
        save_type = arguments.get("save_type", "").upper() or "SAVE"

        result = calculate_saving_throw(attr_mod, prof_bonus, proficient)
        roll = result.individual_rolls[0] if result.individual_rolls else 0
        success = result.total >= dc

        # Build labeled modifier breakdown: "DEX save: 1d20 +3 DEX +2 PROF = 8 +3 DEX +2 PROF = 13"
        mod_parts = [f"+{attr_mod} {save_type}" if attr_mod >= 0 else f"{attr_mod} {save_type}"]
        effective_prof = prof_bonus if proficient else 0
        if effective_prof > 0:
            mod_parts.append(f"+{effective_prof} PROF")
        mod_str = " ".join(mod_parts)
        formatted = f"{save_type} save: 1d20 {mod_str} = {roll} {mod_str} = {result.total} vs DC {dc} ({'Success' if success else 'Fail'})"

        return {
            "save_type": save_type, "roll": roll,
            "modifier": result.modifier, "total": result.total, "dc": dc, "success": success,
            "natural_20": result.natural_20, "natural_1": result.natural_1,
            "proficiency_applied": effective_prof,
            "formatted": formatted
        }

    if tool_name == "declare_no_roll_needed":
        action = arguments.get("action", "unspecified action")
        reason = arguments.get("reason", "no reason provided")
        return {
            "no_roll": True,
            "action": action,
            "reason": reason,
            "formatted": f"No roll needed for '{action}': {reason}"
        }

    return {"error": f"Unknown tool: {tool_name}"}


def execute_tool_requests(tool_requests: list[dict]) -> list[dict]:
    '''
    Execute a list of tool requests with strict type validation.

    Args:
        tool_requests: List of dicts, each containing "tool" (str) and "args" (dict).

    Returns:
        List of results with tool execution details.
    '''
    if not isinstance(tool_requests, list):
        logging_util.error(f"tool_requests must be a list, got {type(tool_requests)}")
        return []

    results = []
    for request in tool_requests:
        if not isinstance(request, dict):
            logging_util.error(f"Tool request must be dict, got {type(request)}")
            continue

        tool_name = request.get("tool")
        args = request.get("args", {})

        # Strict Type Validation
        if not isinstance(tool_name, str) or not tool_name:
            logging_util.error(f"Invalid tool name type or empty: {tool_name} ({type(tool_name)})")
            continue

        if not isinstance(args, dict):
            logging_util.error(f"Tool args must be dict, got {type(args)}")
            args = {}

        try:
            # Delegate to the specific dice tool handler
            result = execute_dice_tool(tool_name, args)
        except Exception as e:
            logging_util.error(f"Tool execution error: {tool_name}: {e}")
            result = {"error": str(e)}

        results.append({
            "tool": tool_name,
            "args": args,
            "result": result,
        })

    return results


def format_tool_results_text(tool_results: Any) -> str:
    """Format tool execution results into a stable, human-readable prompt snippet.

    Providers use this to inject server-executed dice results back into Phase 2.
    """
    if not isinstance(tool_results, list):
        return ""

    lines: list[str] = []
    for item in tool_results:
        if not isinstance(item, dict):
            continue
        tool_name = item.get("tool")
        result = item.get("result", {})
        if not isinstance(tool_name, str) or not tool_name:
            continue
        if isinstance(result, dict) and isinstance(result.get("formatted"), str) and result["formatted"]:
            # Keep Phase 2 context tight: formatted strings already embed the exact numbers.
            lines.append(f"- {result['formatted']}")
            continue
        if isinstance(result, dict) and isinstance(result.get("error"), str) and result["error"]:
            lines.append(f"- {tool_name}: ERROR {result['error']}")
            continue
        # Fallback: last-resort JSON (should be rare)
        try:
            result_str = json.dumps(result, sort_keys=True)
        except TypeError:
            result_str = json.dumps({"error": "unserializable tool result"}, sort_keys=True)
        lines.append(f"- {tool_name}: {result_str}")

    return "\n".join(lines)
