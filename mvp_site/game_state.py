"""
Defines the GameState class, which represents the complete state of a campaign.

Includes:
- XP/Level validation using D&D 5e XP thresholds
- Time monotonicity checks to prevent time regression
- Helper functions for XP→Level calculations
"""

import datetime
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


def xp_to_next_level(current_xp: int) -> int:
    """
    Calculate XP remaining to reach the next level.

    Args:
        current_xp: Current cumulative XP.
                    Accepts int, str, or float - coerced to int.

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
    current_level = level_from_xp(current_xp)

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

        # Convert Enum members to their string values for serialization

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

        Args:
            narrative_text: The latest narrative content from the AI

        Returns:
            List of discrepancy descriptions, empty if no issues found
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

            # General location mismatch detection
            if any(
                phrase in narrative_lower
                for phrase in ["standing in", "in the middle of", "surrounded by"]
            ):
                location_words = location_lower.split()
                if len(location_words) > 0 and not any(
                    word in narrative_lower for word in location_words
                ):
                    discrepancies.append(
                        f"State location '{current_location}' may not match narrative location references"
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

                # General completion detection
                if any(
                    phrase in narrative_lower
                    for phrase in [
                        "quest was complete",
                        "quest complete",
                        "mission complete",
                    ]
                ):
                    if any(word in mission_lower for word in narrative_lower.split()):
                        discrepancies.append(
                            f"Mission '{mission_name}' may be completed in narrative but still active in state"
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
        role = npc.get("role")
        has_named_role = role not in [None, "", "enemy", "minion", "generic"]
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
            if combat_data.get("hp_current", 0) <= 0:
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
                    logging_util.warning(
                        f"COMBAT CLEANUP: Skipping {name} removal because type is missing/unknown "
                        f"(initiative entry absent or incomplete)"
                    )
                    continue

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
            # Use experience_val (already fetched) to avoid re-fetching and handle None properly
            if isinstance(experience_val, dict):
                pc_data["experience"]["current"] = 0
            # Only write scalar if experience_val is not None (mirrors read logic)
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
            # Persist computed level to state (fixes missing level persistence bug)
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
        self, new_time: dict[str, Any], strict: bool = False
    ) -> dict[str, Any]:
        """
        Validate that time progression is monotonic (never goes backwards).

        In default mode (strict=False):
        - Warns on time regression but allows the update
        - Returns warning flag and message

        In strict mode (strict=True):
        - Raises ValueError on time regression

        Args:
            new_time: Dict with time fields (hour, minute, optionally day)
            strict: If True, raise ValueError on backwards time

        Returns:
            Dict with validation results (valid reflects whether the update is
            allowed in the current mode):
            - valid: True if time is forward or same, or if regression is allowed
              with a warning in non-strict mode
            - warning: True if time went backwards (in non-strict mode)
            - message: Description of the issue

        Raises:
            ValueError: In strict mode, if time goes backwards
        """
        result: dict[str, Any] = {"valid": True}

        # Get current time from world_data
        # Use `or {}` to handle both missing and explicitly-null world_data
        current_world_time = (self.world_data or {}).get("world_time")
        if not current_world_time or not isinstance(current_world_time, dict):
            # No previous time to compare against
            return result

        # Validate new_time is a dict before processing
        if not isinstance(new_time, dict):
            # new_time must be a dict to compare
            return result

        # Convert times to comparable values
        current_day = None
        if isinstance(current_world_time, dict):
            current_day = current_world_time.get("day")

        old_total = self._time_to_minutes(current_world_time)
        new_total = self._time_to_minutes(new_time, default_day=current_day)

        # Check for regression
        if new_total < old_total:
            old_str = self._format_time(current_world_time)
            new_str = self._format_time(new_time)
            message = (
                f"Time regression detected: {new_str} is earlier than {old_str}"
            )

            if strict:
                raise ValueError(f"Time cannot go backwards: {message}")

            # Default: warn but allow
            result["valid"] = True  # Still valid but with warning
            result["warning"] = True
            result["message"] = message
            logging_util.warning(f"Time monotonicity: {message}")

        return result

    def _time_to_minutes(self, time_dict: dict[str, Any], default_day: int | None = None) -> int:
        """
        Convert a time dict to total minutes for comparison.

        Accounts for day if present (each day = 24*60 minutes).
        Values are coerced to int for type safety (handles strings from JSON/LLM).
        """
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
