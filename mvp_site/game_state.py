"""
Defines the GameState class, which represents the complete state of a campaign.

Also provides D&D 5E mechanics calculation functions for deterministic game logic.
The LLM should focus on narrative while code handles all mathematical operations.
"""

import datetime
import random
import re
from dataclasses import dataclass
from typing import Any, Optional

from mvp_site import constants, logging_util


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
                enemy_type = None
                for init_entry in self.combat_state.get("initiative_order", []):
                    if init_entry["name"] == name:
                        enemy_type = init_entry.get("type", "unknown")
                        break

                if enemy_type not in ["pc", "companion", "ally"]:
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

            # Remove from NPC data (defeated enemies shouldn't persist)
            if enemy_name in self.npc_data:
                del self.npc_data[enemy_name]
                logging_util.info(f"COMBAT CLEANUP: Removed {enemy_name} from npc_data")

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


# =============================================================================
# D&D 5E MECHANICS CALCULATIONS
# =============================================================================
# These functions replace LLM-based calculations with deterministic code.
# The LLM should focus on narrative; code handles math.
# =============================================================================


def generate_pre_rolled_dice(
    num_d20: int = 100,
    num_d12: int = 20,
    num_d10: int = 20,
    num_d8: int = 30,
    num_d6: int = 40,
    num_d4: int = 20,
    num_d100: int = 10,
) -> dict[str, list[int]]:
    """
    Generate pre-rolled dice for single-inference LLM architecture.

    Instead of using tool calls (two-stage inference), we pre-roll dice
    and include them in the LLM request. The LLM uses these values in order,
    ensuring true randomness with only one API call.

    Args:
        num_d20: Number of d20 rolls (default 100 - enough for most combat)
        num_d12: Number of d12 rolls (default 20)
        num_d10: Number of d10 rolls (default 20)
        num_d8: Number of d8 rolls (default 30 - common damage die)
        num_d6: Number of d6 rolls (default 40 - very common)
        num_d4: Number of d4 rolls (default 20)
        num_d100: Number of d100 rolls (default 10 - percentile)

    Returns:
        Dict with die type keys and lists of pre-rolled values:
        {
            "d20": [14, 7, 19, 3, ...],
            "d12": [8, 11, 2, ...],
            "d10": [5, 9, 1, ...],
            "d8": [6, 3, 8, ...],
            "d6": [4, 2, 6, ...],
            "d4": [3, 1, 4, ...],
            "d100": [42, 87, 13, ...]
        }
    """
    # S311: Standard random is intentional - dice rolls need randomness, not cryptography
    return {
        "d20": [random.randint(1, 20) for _ in range(num_d20)],  # noqa: S311
        "d12": [random.randint(1, 12) for _ in range(num_d12)],  # noqa: S311
        "d10": [random.randint(1, 10) for _ in range(num_d10)],  # noqa: S311
        "d8": [random.randint(1, 8) for _ in range(num_d8)],  # noqa: S311
        "d6": [random.randint(1, 6) for _ in range(num_d6)],  # noqa: S311
        "d4": [random.randint(1, 4) for _ in range(num_d4)],  # noqa: S311
        "d100": [random.randint(1, 100) for _ in range(num_d100)],  # noqa: S311
    }




@dataclass
class DiceRollResult:
    """Result of a dice roll with full transparency."""

    notation: str  # Original notation, e.g., "2d6+3"
    individual_rolls: list[int]  # Each die result
    modifier: int  # The +/- modifier
    total: int  # Final sum
    natural_20: bool = False  # For d20 rolls
    natural_1: bool = False  # For d20 rolls

    def __str__(self) -> str:
        rolls_str = ", ".join(str(r) for r in self.individual_rolls)
        if self.modifier == 0:
            return f"{self.notation} = [{rolls_str}] = {self.total}"
        if self.modifier > 0:
            return f"{self.notation} = [{rolls_str}]+{self.modifier} = {self.total}"
        return f"{self.notation} = [{rolls_str}]{self.modifier} = {self.total}"


# XP by Challenge Rating lookup table (D&D 5E SRD)
XP_BY_CR: dict[float, int] = {
    0: 10,
    0.125: 25,  # CR 1/8
    0.25: 50,  # CR 1/4
    0.5: 100,  # CR 1/2
    1: 200,
    2: 450,
    3: 700,
    4: 1100,
    5: 1800,
    6: 2300,
    7: 2900,
    8: 3900,
    9: 5000,
    10: 5900,
    11: 7200,
    12: 8400,
    13: 10000,
    14: 11500,
    15: 13000,
    16: 15000,
    17: 18000,
    18: 20000,
    19: 22000,
    20: 25000,
    21: 33000,
    22: 41000,
    23: 50000,
    24: 62000,
    25: 75000,
    26: 90000,
    27: 105000,
    28: 120000,
    29: 135000,
    30: 155000,
}

# XP thresholds for each level (total XP needed to reach that level)
XP_THRESHOLDS: dict[int, int] = {
    1: 0,
    2: 300,
    3: 900,
    4: 2700,
    5: 6500,
    6: 14000,
    7: 23000,
    8: 34000,
    9: 48000,
    10: 64000,
    11: 85000,
    12: 100000,
    13: 120000,
    14: 140000,
    15: 165000,
    16: 195000,
    17: 225000,
    18: 265000,
    19: 305000,
    20: 355000,
}

# Proficiency bonus by level
PROFICIENCY_BY_LEVEL: dict[int, int] = {
    1: 2,
    2: 2,
    3: 2,
    4: 2,
    5: 3,
    6: 3,
    7: 3,
    8: 3,
    9: 4,
    10: 4,
    11: 4,
    12: 4,
    13: 5,
    14: 5,
    15: 5,
    16: 5,
    17: 6,
    18: 6,
    19: 6,
    20: 6,
}


def calculate_modifier(attribute: int) -> int:
    """
    Calculate ability modifier from attribute score.
    Formula: (attribute - 10) // 2 (rounded down)

    Args:
        attribute: Ability score (typically 1-30)

    Returns:
        Modifier value (can be negative)
    """
    return (attribute - 10) // 2


def calculate_proficiency_bonus(level: int) -> int:
    """
    Get proficiency bonus for a given character level.

    Args:
        level: Character level (1-20)

    Returns:
        Proficiency bonus (+2 to +6)
    """
    if level < 1:
        return 2
    if level > 20:
        return 6
    return PROFICIENCY_BY_LEVEL.get(level, 2)


def calculate_armor_class(
    dex_modifier: int, armor_bonus: int = 0, shield_bonus: int = 0
) -> int:
    """
    Calculate Armor Class.
    Base AC = 10 + DEX modifier + armor bonus + shield bonus

    Args:
        dex_modifier: Dexterity modifier
        armor_bonus: Bonus from armor (may cap DEX)
        shield_bonus: Bonus from shield (typically +2)

    Returns:
        Armor Class value
    """
    return 10 + dex_modifier + armor_bonus + shield_bonus


def calculate_passive_perception(
    wis_modifier: int, proficient: bool, proficiency_bonus: int
) -> int:
    """
    Calculate passive Perception score.
    Formula: 10 + WIS modifier + (proficiency if proficient)

    Args:
        wis_modifier: Wisdom modifier
        proficient: Whether proficient in Perception
        proficiency_bonus: Character's proficiency bonus

    Returns:
        Passive Perception value
    """
    base = 10 + wis_modifier
    if proficient:
        base += proficiency_bonus
    return base


def xp_for_cr(cr: float) -> int:
    """
    Get XP award for defeating a creature of given Challenge Rating.

    Args:
        cr: Challenge Rating (0, 0.125, 0.25, 0.5, 1-30)

    Returns:
        XP value
    """
    return XP_BY_CR.get(cr, 0)


def level_from_xp(total_xp: int) -> int:
    """
    Determine character level from total XP.

    Args:
        total_xp: Total accumulated XP

    Returns:
        Character level (1-20)
    """
    level = 1
    for lvl, threshold in sorted(XP_THRESHOLDS.items()):
        if total_xp >= threshold:
            level = lvl
        else:
            break
    return min(level, 20)


def xp_needed_for_level(level: int) -> int:
    """
    Get total XP needed to reach a specific level.

    Args:
        level: Target level (1-20)

    Returns:
        Total XP threshold for that level
    """
    if level < 1:
        return 0
    if level > 20:
        return XP_THRESHOLDS[20]
    return XP_THRESHOLDS.get(level, 0)


def xp_to_next_level(current_xp: int, current_level: int) -> int:
    """
    Calculate XP remaining until next level.

    Args:
        current_xp: Current total XP
        current_level: Current level

    Returns:
        XP needed for next level (0 if at max level)
    """
    if current_level >= 20:
        return 0
    next_level_threshold = xp_needed_for_level(current_level + 1)
    return max(0, next_level_threshold - current_xp)


def roll_dice(notation: str) -> DiceRollResult:
    """
    Roll dice using standard notation (e.g., "2d6+3", "1d20-1", "4d6").

    This provides TRUE randomness via Python's random module,
    replacing LLM-simulated dice rolls for fairness.

    Args:
        notation: Dice notation string (e.g., "1d20+5", "2d6", "1d8-2")

    Returns:
        DiceRollResult with full transparency
    """
    # Parse notation: XdY+Z or XdY-Z or XdY
    pattern = r"(\d+)d(\d+)([+-]\d+)?"
    match = re.match(pattern, notation.lower().replace(" ", ""))

    if not match:
        # Invalid notation, return 0
        return DiceRollResult(
            notation=notation,
            individual_rolls=[],
            modifier=0,
            total=0,
        )

    num_dice = int(match.group(1))
    die_size = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    # Validate die_size to prevent crashes on invalid notations like "1d0"
    if die_size < 1:
        return DiceRollResult(
            notation=notation,
            individual_rolls=[],
            modifier=modifier,
            total=modifier,
        )

    # Roll each die
    rolls = [random.randint(1, die_size) for _ in range(num_dice)]

    # Calculate total
    total = sum(rolls) + modifier

    # Check for natural 20/1 on d20 rolls
    natural_20 = die_size == 20 and num_dice == 1 and rolls[0] == 20
    natural_1 = die_size == 20 and num_dice == 1 and rolls[0] == 1

    return DiceRollResult(
        notation=notation,
        individual_rolls=rolls,
        modifier=modifier,
        total=total,
        natural_20=natural_20,
        natural_1=natural_1,
    )


def calculate_resource_depletion(
    current_amount: float,
    depletion_rate: float,
    time_elapsed: float,
    depletion_unit: str = "per_day",
) -> float:
    """
    Calculate resource depletion over time.

    Args:
        current_amount: Current resource amount
        depletion_rate: Rate of depletion
        time_elapsed: Time elapsed (in the unit specified)
        depletion_unit: Unit of depletion rate (per_day, per_hour, etc.)

    Returns:
        Remaining resource amount (minimum 0)
    """
    # Convert time_elapsed to match depletion_unit if needed
    # For simplicity, assume time_elapsed is in the same unit as depletion_rate
    depleted = depletion_rate * time_elapsed
    remaining = current_amount - depleted
    return max(0, remaining)
