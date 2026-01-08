"""
Defines the GameState class, which represents the complete state of a campaign.

Includes:
- D&D 5E mechanics integration for deterministic game logic (dice rolls in mvp_site.dice)
- XP/Level validation using D&D 5e XP thresholds
- Time monotonicity checks to prevent time regression
- Helper functions for XP→Level calculations

The LLM should focus on narrative while code handles all mathematical operations.
"""

from __future__ import annotations

import datetime
import json
from typing import Any, Literal, overload

from mvp_site import constants, dice as dice_module, logging_util
from mvp_site.dice import DiceRollResult, execute_dice_tool

# =============================================================================
# D&D 5e XP THRESHOLDS
# =============================================================================
# Cumulative XP required to reach each level (1-20)
# Source: D&D 5e Player's Handbook / SRD
# =============================================================================

XP_THRESHOLDS = [
    0,  # Level 1
    300,  # Level 2
    900,  # Level 3
    2700,  # Level 4
    6500,  # Level 5
    14000,  # Level 6
    23000,  # Level 7
    34000,  # Level 8
    48000,  # Level 9
    64000,  # Level 10
    85000,  # Level 11
    100000,  # Level 12
    120000,  # Level 13
    140000,  # Level 14
    165000,  # Level 15
    195000,  # Level 16
    225000,  # Level 17
    265000,  # Level 18
    305000,  # Level 19
    355000,  # Level 20
]

XP_BY_CR = {
    0: 10,
    0.125: 25,
    0.25: 50,
    0.5: 100,
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

PROFICIENCY_BY_LEVEL = {
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


def coerce_int(value: Any, default: int | None = 0) -> int | None:
    """Public wrapper around :func:`_coerce_int` for safe int coercion."""

    return _coerce_int(value, default)


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

    next_threshold = XP_THRESHOLDS[
        current_level
    ]  # Index is level since we need level+1
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
        # Item registry: maps item_id (string) → item definition (dict)
        # Example item: helm_telepathy → name "Helm of Telepathy", type "head", stats "30ft telepathy"
        self.item_registry = kwargs.get("item_registry", {})
        self.custom_campaign_state = kwargs.get("custom_campaign_state", {})
        if not isinstance(self.custom_campaign_state, dict):
            self.custom_campaign_state = {}

        # Ensure arc_milestones is initialized for tracking narrative arc completion
        # Handle both missing key AND null value from Firestore
        if "arc_milestones" not in self.custom_campaign_state or not isinstance(
            self.custom_campaign_state.get("arc_milestones"), dict
        ):
            self.custom_campaign_state["arc_milestones"] = {}

        # Ensure active_constraints exists for tracking secrecy/deception rules
        # (player OOC constraints such as "don't reveal X to Y") and remains
        # list-typed for prompt rules that append entries.
        if "active_constraints" not in self.custom_campaign_state or not isinstance(
            self.custom_campaign_state.get("active_constraints"), list
        ):
            self.custom_campaign_state["active_constraints"] = []

        # Ensure attribute_system is set (defaults to Destiny system)
        if "attribute_system" not in self.custom_campaign_state:
            self.custom_campaign_state["attribute_system"] = (
                constants.DEFAULT_ATTRIBUTE_SYSTEM
            )

        # Campaign tier progression (mortal → divine → sovereign)
        if "campaign_tier" not in self.custom_campaign_state:
            self.custom_campaign_state["campaign_tier"] = (
                constants.CAMPAIGN_TIER_MORTAL
            )

        # Divine/multiverse progression tracking
        if "divine_potential" not in self.custom_campaign_state:
            self.custom_campaign_state["divine_potential"] = 0
        if "universe_control" not in self.custom_campaign_state:
            self.custom_campaign_state["universe_control"] = 0
        if "divine_upgrade_available" not in self.custom_campaign_state:
            self.custom_campaign_state["divine_upgrade_available"] = False
        if "multiverse_upgrade_available" not in self.custom_campaign_state:
            self.custom_campaign_state["multiverse_upgrade_available"] = False

        self.combat_state = kwargs.get("combat_state", {"in_combat": False})
        # Normalize combat_state to handle LLM-generated malformed data
        self._normalize_combat_state()
        self.last_state_update_timestamp = kwargs.get(
            "last_state_update_timestamp", datetime.datetime.now(datetime.UTC)
        )

        # Player turn counter (1-indexed, excludes GOD mode commands)
        # Used for living world cadence (fires every 3 player turns)
        self.player_turn = kwargs.get("player_turn", 0)

        # Initialize time pressure structures
        self.time_sensitive_events = kwargs.get("time_sensitive_events", {})
        self.npc_agendas = kwargs.get("npc_agendas", {})
        self.world_resources = kwargs.get("world_resources", {})
        self.time_pressure_warnings = kwargs.get("time_pressure_warnings", {})

        # Debug mode flag
        self.debug_mode = kwargs.get("debug_mode", constants.DEFAULT_DEBUG_MODE)

        # LLM-requested instruction hints for next turn
        # Extracted from debug_info.meta.needs_detailed_instructions and used to load
        # detailed prompt sections (e.g., relationships, reputation) on subsequent turns
        self.pending_instruction_hints: list[str] = kwargs.get(
            "pending_instruction_hints", []
        )

        # Dynamically set any other attributes from kwargs
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)

        # Apply time consolidation migration
        self._consolidate_time_tracking()

    def _normalize_combat_state(self) -> None:  # noqa: PLR0912
        """
        Normalize combat_state to handle LLM-generated malformed data.

        Fixes common issues:
        1. initiative_order entries that are strings instead of dicts
        2. combatants that are strings instead of dicts
        3. Coerces HP values to integers

        Only normalizes fields that already exist - does not add new fields.
        """
        if not isinstance(self.combat_state, dict):
            self.combat_state = {"in_combat": False}
            return

        # Normalize initiative_order entries (only if field exists)
        if "initiative_order" in self.combat_state:
            init_order = self.combat_state["initiative_order"]
            if isinstance(init_order, list):
                normalized_order = []
                for entry in init_order:
                    if isinstance(entry, str):
                        # Convert string to dict with name
                        normalized_order.append(
                            {
                                "name": entry,
                                "initiative": 0,
                                "type": "unknown",
                            }
                        )
                    elif isinstance(entry, dict):
                        # Ensure required fields exist
                        normalized_order.append(
                            {
                                "name": entry.get("name", "Unknown"),
                                "initiative": _coerce_int(
                                    entry.get("initiative", 0), 0
                                ),
                                "type": entry.get("type", "unknown"),
                            }
                        )
                    # Skip non-string, non-dict entries
                self.combat_state["initiative_order"] = normalized_order

        # Normalize combatants entries (only if field exists)
        if "combatants" in self.combat_state:
            combatants = self.combat_state["combatants"]
            if isinstance(combatants, list):
                # Convert list to dict format
                combatants_dict = {}
                for c in combatants:
                    if isinstance(c, str):
                        combatants_dict[c] = {
                            "hp_current": 1,
                            "hp_max": 1,
                            "status": [],
                        }
                    elif isinstance(c, dict) and "name" in c:
                        name = c["name"]
                        combatants_dict[name] = {
                            "hp_current": _coerce_int(c.get("hp_current", 1), 1),
                            "hp_max": _coerce_int(c.get("hp_max", 1), 1),
                            "status": c.get("status", []),
                        }
                self.combat_state["combatants"] = combatants_dict
            elif isinstance(combatants, dict):
                # Ensure all combatant values are dicts with coerced ints
                normalized_combatants = {}
                for name, data in combatants.items():
                    if isinstance(data, str):
                        # String value - convert to minimal dict
                        normalized_combatants[name] = {
                            "hp_current": 1,
                            "hp_max": 1,
                            "status": [],
                        }
                    elif isinstance(data, dict):
                        normalized_combatants[name] = {
                            "hp_current": _coerce_int(data.get("hp_current", 1), 1),
                            "hp_max": _coerce_int(data.get("hp_max", 1), 1),
                            "status": data.get("status", []),
                            # Preserve type/role if present
                            **({"type": data["type"]} if "type" in data else {}),
                            **({"role": data["role"]} if "role" in data else {}),
                        }
                    else:
                        # Unknown type - skip
                        continue
                self.combat_state["combatants"] = normalized_combatants

        # Ensure consistency: Remove initiative entries that don't have a corresponding combatant
        # This prevents "orphaned" turns and invalid states where init exists but combatants don't
        if (
            "initiative_order" in self.combat_state
            and "combatants" in self.combat_state
        ):
            init_order = self.combat_state.get("initiative_order")
            combatants = self.combat_state.get("combatants")
            # Guard: Only proceed if types are correct
            if isinstance(init_order, list) and isinstance(combatants, dict):
                combatants_keys = set(combatants.keys())
                self.combat_state["initiative_order"] = [
                    entry
                    for entry in init_order
                    if isinstance(entry, dict) and entry.get("name") in combatants_keys
                ]
        # CRITICAL: Validate schema consistency between initiative_order and combatants
        self._validate_combat_state_consistency()

    def _validate_combat_state_consistency(self) -> None:
        """
        Validate that initiative_order and combatants are consistent.

        Logs warnings for:
        1. initiative_order names that don't exist in combatants (orphaned entries)
        2. combatants keys that don't appear in initiative_order (missing from turn order)
        3. Empty combatants with populated initiative_order (invalid state)
        """
        if not isinstance(self.combat_state, dict):
            return

        init_order = self.combat_state.get("initiative_order", [])
        combatants = self.combat_state.get("combatants", {})

        if not isinstance(init_order, list) or not isinstance(combatants, dict):
            return

        # Get names from initiative_order
        init_names = {
            entry.get("name") for entry in init_order if isinstance(entry, dict)
        }

        # Get keys from combatants
        combatant_keys = set(combatants.keys())

        # Check for orphaned initiative entries (name not in combatants)
        orphaned_init = init_names - combatant_keys
        if orphaned_init:
            logging_util.warning(
                f"⚠️ COMBAT_STATE_MISMATCH: initiative_order has names not in combatants: {orphaned_init}. "
                "Cleanup may fail for these entries."
            )

        # Check for combatants missing from initiative_order
        missing_from_init = combatant_keys - init_names
        if missing_from_init:
            logging_util.warning(
                f"⚠️ COMBAT_STATE_MISMATCH: combatants has keys not in initiative_order: {missing_from_init}. "
                "These combatants won't have a turn."
            )

        # Check for empty combatants with populated initiative_order (INVALID STATE)
        if init_order and not combatants:
            logging_util.error(
                f"🔴 INVALID_COMBAT_STATE: initiative_order has {len(init_order)} entries but combatants is empty. "
                "Combat cleanup will fail. This violates the combat schema."
            )

        # Check for missing combat_summary when combat has ended
        in_combat = self.combat_state.get("in_combat", False)
        combat_phase = self.combat_state.get("combat_phase", "")
        combat_summary = self.combat_state.get("combat_summary")

        if not in_combat and combat_phase == "ended":
            if not combat_summary:
                logging_util.warning(
                    "⚠️ MISSING_COMBAT_SUMMARY: Combat ended (in_combat=false, combat_phase=ended) "
                    "but no combat_summary provided. XP and loot may not be awarded."
                )
            elif isinstance(combat_summary, dict):
                # Validate combat_summary has required fields
                required_fields = ["xp_awarded", "enemies_defeated"]
                missing = [f for f in required_fields if f not in combat_summary]
                if missing:
                    logging_util.warning(
                        f"⚠️ INCOMPLETE_COMBAT_SUMMARY: Missing fields: {missing}. "
                        "XP awards may be incorrect."
                    )
                # Validate xp_awarded is a number
                xp = combat_summary.get("xp_awarded")
                if xp is not None and not isinstance(xp, (int, float)):
                    logging_util.warning(
                        f"⚠️ INVALID_XP_AWARDED: xp_awarded is {type(xp).__name__}, expected int. "
                        f"Value: {xp}"
                    )

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
    def from_dict(cls, source: dict[str, Any] | None) -> "GameState" | None:
        """Creates a GameState object from a dictionary (e.g., from Firestore)."""
        if not source:
            return None

        # The constructor now directly accepts the dictionary.
        return cls(**source)

    def get_combat_state(self) -> dict:
        """
        Get combat_state as a normalized dict.

        This is the standardized way to access combat_state throughout the codebase.
        Always returns a dict (never None), with sensible defaults.

        Returns:
            dict: Combat state with at minimum {"in_combat": False}
        """
        if not hasattr(self, "combat_state"):
            return {"in_combat": False}
        if not isinstance(self.combat_state, dict):
            return {"in_combat": False}
        return self.combat_state

    def is_in_combat(self) -> bool:
        """
        Check if combat is currently active.

        This is the standardized way to check combat status.

        Returns:
            bool: True if in_combat is explicitly True, False otherwise
        """
        combat_state = self.get_combat_state()
        return combat_state.get("in_combat", False) is True

    def get_encounter_state(self) -> dict:
        """
        Get encounter_state as a normalized dict.

        This is the standardized way to access encounter_state throughout the codebase.
        Used for non-combat encounters (heists, social victories, stealth, puzzles).
        Always returns a dict (never None), with sensible defaults.

        Returns:
            dict: Encounter state with at minimum {"encounter_active": False}

        Schema:
            {
                "encounter_active": bool,
                "encounter_id": str,
                "encounter_type": "heist" | "social" | "stealth" | "puzzle" | "quest",
                "difficulty": "easy" | "medium" | "hard" | "deadly",
                "participants": [...],
                "encounter_completed": bool,
                "encounter_summary": {...},
                "rewards_processed": bool
            }
        """
        if not hasattr(self, "encounter_state"):
            return {"encounter_active": False}
        if not isinstance(self.encounter_state, dict):
            return {"encounter_active": False}
        return self.encounter_state

    def get_rewards_pending(self) -> dict | None:
        """
        Get rewards_pending from game state.

        This is the standardized way to access pending rewards throughout the codebase.
        Used by RewardsAgent to detect when rewards need to be processed.

        Returns:
            dict: Rewards pending data, or None if no rewards pending

        Schema:
            {
                "source": "combat" | "encounter" | "quest" | "milestone",
                "source_id": str,  # combat_session_id or encounter_id
                "xp": int,
                "gold": int,
                "items": [...],
                "level_up_available": bool,
                "processed": bool
            }
        """
        if not hasattr(self, "rewards_pending"):
            return None
        if not isinstance(self.rewards_pending, dict):
            return None
        # Return None if rewards is empty dict
        if not self.rewards_pending:
            return None
        return self.rewards_pending

    def has_pending_rewards(self) -> bool:
        """
        Check if there are any pending rewards from any source.

        Checks:
        1. Explicit rewards_pending field
        2. Combat ended with summary but not processed
        3. Encounter completed with encounter_summary but not processed

        Returns:
            bool: True if rewards are pending and need processing
        """
        # Check explicit rewards_pending
        rewards = self.get_rewards_pending()
        if rewards and not rewards.get("processed", False):
            return True

        # Check combat ended with summary
        combat_state = self.get_combat_state()
        # Use centralized constant for combat finished phases
        if (
            combat_state.get("combat_phase") in constants.COMBAT_FINISHED_PHASES
            and combat_state.get("combat_summary")
            and not combat_state.get("rewards_processed", False)
        ):
            return True

        # Check encounter completed with summary
        encounter_state = self.get_encounter_state()
        encounter_completed = encounter_state.get("encounter_completed", False)
        encounter_summary = encounter_state.get("encounter_summary")
        encounter_processed = encounter_state.get("rewards_processed", False)

        if encounter_completed:
            if not isinstance(encounter_summary, dict):
                logging_util.debug(
                    "🏆 REWARDS_CHECK: Encounter completed but encounter_summary missing/invalid"
                )
            elif encounter_summary.get("xp_awarded") is None:
                logging_util.debug(
                    "🏆 REWARDS_CHECK: Encounter completed but encounter_summary missing xp_awarded"
                )
            elif not encounter_processed:
                return True

        return False

    # =========================================================================
    # Arc Milestone Tracking Methods
    # =========================================================================
    # These methods provide structured tracking for narrative arcs to prevent
    # the LLM from losing track of completed events during context compression.
    # =========================================================================

    def mark_arc_completed(
        self, arc_name: str, phase: str | None = None, metadata: dict | None = None
    ) -> None:
        """
        Mark a narrative arc as completed with timestamp.

        Once an arc is marked completed, it cannot be reverted to in_progress.
        This prevents timeline confusion where the LLM forgets major events.
        Calling this again for the same arc overwrites the previous completion
        record (including completed_at) to allow phase/metadata updates.

        Args:
            arc_name: Unique identifier for the arc (e.g., "wedding_tour")
            phase: Optional phase name when completion occurred
            metadata: Optional additional data to store with the milestone
        """
        milestones = self.custom_campaign_state.get("arc_milestones", {})

        milestone_data = {
            "status": "completed",
            "completed_at": datetime.datetime.now(datetime.UTC).isoformat(),
        }

        if phase is not None:
            milestone_data["phase"] = phase

        if metadata is not None:
            milestone_data["metadata"] = metadata

        milestones[arc_name] = milestone_data
        self.custom_campaign_state["arc_milestones"] = milestones

    def update_arc_progress(self, arc_name: str, phase: str, progress: int = 0) -> None:
        """
        Update the progress of an in-progress arc.

        If the arc is already completed, this method does nothing to prevent
        timeline regression.

        Args:
            arc_name: Unique identifier for the arc
            phase: Current phase of the arc
            progress: Progress percentage (0-100)
        """
        milestones = self.custom_campaign_state.get("arc_milestones", {})
        arc_data = milestones.get(arc_name)

        # Prevent regression of completed arcs
        if isinstance(arc_data, dict) and arc_data.get("status") == "completed":
            logging_util.warning(
                "Attempted to update progress for completed arc '%s' "
                "(phase=%s, progress=%s). Update ignored to prevent timeline regression.",
                arc_name,
                phase,
                progress,
            )
            return  # Arc already completed, don't regress

        progress_value = _coerce_int(progress, 0)
        if progress_value < 0 or progress_value > 100:
            logging_util.warning(
                "Arc progress out of range for '%s': %s. Clamping to 0-100.",
                arc_name,
                progress_value,
            )
            progress_value = max(0, min(100, progress_value))

        milestones[arc_name] = {
            "status": "in_progress",
            "phase": phase,
            "progress": progress_value,
            "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        }
        self.custom_campaign_state["arc_milestones"] = milestones

    def is_arc_completed(self, arc_name: str) -> bool:
        """
        Check if a narrative arc has been marked as completed.

        Args:
            arc_name: Unique identifier for the arc

        Returns:
            True if the arc is completed, False otherwise
        """
        milestones = self.custom_campaign_state.get("arc_milestones", {})
        arc_data = milestones.get(arc_name)
        if not isinstance(arc_data, dict):
            return False
        return arc_data.get("status") == "completed"

    def get_arc_phase(self, arc_name: str) -> str | None:
        """
        Get the current phase of a narrative arc.

        Args:
            arc_name: Unique identifier for the arc

        Returns:
            The phase name if set, None otherwise
        """
        milestones = self.custom_campaign_state.get("arc_milestones", {})
        arc_data = milestones.get(arc_name)
        if not isinstance(arc_data, dict):
            return None
        return arc_data.get("phase")

    def get_completed_arcs_summary(self) -> str:
        """
        Generate a summary of completed arcs for inclusion in LLM context.

        This provides deterministic state information to prevent the LLM from
        forgetting that major narrative arcs have concluded.

        Returns:
            Formatted string summarizing completed arcs, empty if none
        """
        milestones = self.custom_campaign_state.get("arc_milestones", {})

        completed = [
            (name, data)
            for name, data in milestones.items()
            if isinstance(data, dict) and data.get("status") == "completed"
        ]

        if not completed:
            return ""

        lines = ["[COMPLETED ARCS - DO NOT REVISIT AS IN-PROGRESS]"]
        for arc_name, data in completed:
            phase = data.get("phase", "final")
            completed_at = data.get("completed_at", "unknown")
            lines.append(
                f"- {arc_name}: COMPLETED (phase: {phase}, at: {completed_at})"
            )

        return "\n".join(lines)

    def validate_checkpoint_consistency(self, narrative_text: str) -> list[str]:  # noqa: PLR0912,PLR0915,SIM102
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

            # Defensive: persisted game state may contain numeric strings
            hp_current = _coerce_int(hp_current, None)
            hp_max = _coerce_int(hp_max, None)

            if hp_current is not None and hp_max is not None and hp_max > 0:
                # Check for unconscious/death vs HP mismatch
                if (
                    "unconscious" in narrative_lower
                    or "lies unconscious" in narrative_lower
                ) and hp_current > 0:
                    discrepancies.append(
                        f"Narrative mentions unconsciousness but HP is {hp_current}/{hp_max}"
                    )

                if (
                    any(
                        phrase in narrative_lower
                        for phrase in ["completely drained", "drained of life"]
                    )
                    and hp_current > 5
                ):  # Should be very low if "drained of life"
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
                elif hp_percentage > 90 and any(
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
        """Return True if the NPC should be preserved (named/important).

        Uses centralized constants from mvp_site.constants for maintainability.
        """
        role_raw = npc.get("role")
        # Use centralized helper for role classification
        has_named_role = not constants.is_generic_enemy_role(role_raw)
        has_story = npc.get("backstory") or npc.get("background")
        return bool(has_named_role or has_story or npc.get("is_important"))

    def cleanup_defeated_enemies(self) -> list[str]:  # noqa: PLR0912,PLR0915
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
            hp_current = _coerce_int(combat_data.get("hp_current", 0), 0) or 0
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

                # Use centralized constants for friendly type detection
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
                    npc_role_raw = (
                        npc_record.get("role") if isinstance(npc_record, dict) else None
                    )
                    npc_type_raw = (
                        npc_record.get("type") if isinstance(npc_record, dict) else None
                    )
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

                    if constants.is_friendly_combatant(
                        npc_role
                    ) or constants.is_friendly_combatant(npc_type):
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

                if constants.is_friendly_combatant(enemy_type):
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
                    logging_util.info(
                        f"COMBAT CLEANUP: Marked {enemy_name} as dead in npc_data (named NPC preserved)"
                    )
                else:
                    # Generic enemies can be deleted
                    del self.npc_data[enemy_name]
                    logging_util.info(
                        f"COMBAT CLEANUP: Removed {enemy_name} from npc_data (generic enemy)"
                    )

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
                logging_util.info("Added microsecond field to world_time (default: 0)")

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

    def _calculate_time_of_day(self, hour: int) -> str:  # noqa: PLR0911
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

    def validate_xp_level(self, strict: bool = False) -> dict[str, Any]:  # noqa: PLR0912,PLR0915
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

        # Clamp level minimum to 1 (no max - epic levels 21+ allowed)
        if provided_level < 1:
            result["clamped_level"] = 1
            logging_util.warning(f"XP validation: Level {provided_level} clamped to 1")
            provided_level = 1
            if hasattr(self, "player_character_data") and isinstance(
                self.player_character_data, dict
            ):
                self.player_character_data["level"] = provided_level
        elif provided_level > 20:
            # Epic levels (21+) are allowed for epic/mythic campaigns
            # Log as info, not warning - this is intentional for epic play
            result["epic_level"] = True
            logging_util.info(
                f"Epic level detected: Level {provided_level} (beyond standard D&D 5e cap)"
            )

        # Check for mismatch (skip XP validation for epic levels 21+)
        # Epic levels are set by the LLM for epic/mythic campaigns and don't follow XP table
        if provided_level > 20:
            # Epic level - valid by definition, no XP-based validation needed
            result["valid"] = True
            result["epic_level"] = True
            return result

        if provided_level != expected_level:
            result["valid"] = False

            message = (
                f"XP/Level mismatch: XP={xp} should be Level {expected_level}, "
                f"but provided Level {provided_level}"
            )

            if strict:
                raise ValueError(message)

            # For the current structured schema (experience={"current": ...}), level-ups are
            # handled by the rewards_pending flow rather than server-side mutation.
            #
            # For legacy/compat schemas (scalar experience/xp fields), auto-correct to keep
            # state consistent and tests deterministic.
            if expected_level > provided_level:
                if isinstance(experience_val, dict):
                    logging_util.info(
                        f"XP validation: {message} - level-up detected, letting LLM handle via rewards_pending"
                    )
                    result["level_up_pending"] = True
                else:
                    # Do NOT set "corrected" flag when no actual correction happens
                    # Only set level_up_pending to indicate LLM should handle the level-up
                    result["level_up_pending"] = True  # Ensure test detects level up
                    logging_util.warning(
                        f"XP validation: {message} - flagging level up mismatch (legacy XP schema, LLM will handle)"
                    )
                    # Do NOT auto-correct level upwards - let the user/LLM process the level up
                    # if hasattr(self, "player_character_data") and isinstance(
                    #     self.player_character_data, dict
                    # ):
                    #     self.player_character_data["level"] = expected_level
                    #     result["corrected_level"] = expected_level
            else:
                # Level regression/mismatch: stored level is HIGHER than XP indicates
                # This is a data integrity issue - auto-correct it
                result["corrected"] = True
                logging_util.warning(
                    f"XP validation: {message} - auto-correcting level regression"
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
            message = f"Time regression detected: {new_str} is earlier than {old_str}"

            if strict:
                raise ValueError(f"Time cannot go backwards: {message}")

            result["valid"] = True  # Still valid but with warning
            result["warning"] = True
            result["message"] = message
            logging_util.warning(f"Time monotonicity: {message}")

        return result

    def _time_to_minutes(
        self, time_dict: dict[str, Any], default_day: int | None = None
    ) -> int:
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

    # =========================================================================
    # Character Identity Methods
    # =========================================================================

    def get_character_identity_block(self) -> str:
        """
        Generate a character identity block for system prompts.

        This ensures the LLM always has access to immutable character facts
        like name, gender, pronouns, and key relationships.

        Returns:
            Formatted string block for system prompts
        """
        pc = self.player_character_data
        if not pc or not isinstance(pc, dict):
            return ""

        lines = ["## Character Identity (IMMUTABLE)"]

        # Name
        name = pc.get("name")
        if name:
            lines.append(f"- **Name**: {name}")

        # Gender and pronouns - handle None values properly
        # Note: .get("gender", "") returns None if key exists with None value
        gender_raw = pc.get("gender")
        gender = str(gender_raw).lower() if gender_raw else ""
        if gender:
            if gender in ("female", "woman", "f"):
                lines.append("- **Gender**: Female (she/her)")
                lines.append(
                    "- **NEVER** refer to this character as 'he', 'him', "
                    "or use male-gendered familial terms for them"
                )
            elif gender in ("male", "man", "m"):
                lines.append("- **Gender**: Male (he/him)")
                lines.append(
                    "- **NEVER** refer to this character as 'she', 'her', "
                    "or use female-gendered familial terms for them"
                )
            else:
                lines.append(f"- **Gender**: {gender}")

        # Race
        race = pc.get("race")
        if race:
            lines.append(f"- **Race**: {race}")

        # Class
        char_class = pc.get("class") or pc.get("character_class")
        if char_class:
            lines.append(f"- **Class**: {char_class}")

        # Key relationships (from backstory or explicit field)
        relationships = pc.get("relationships", {})
        if isinstance(relationships, dict) and relationships:
            lines.append("- **Key Relationships**:")
            for rel_name, rel_type in relationships.items():
                lines.append(f"  - {rel_name}: {rel_type}")

        # Parentage (important for characters like Alexiel)
        parentage = pc.get("parentage") or pc.get("parents")
        if parentage:
            if isinstance(parentage, dict):
                for parent_type, parent_name in parentage.items():
                    lines.append(f"- **{parent_type.title()}**: {parent_name}")
            elif isinstance(parentage, str):
                lines.append(f"- **Parentage**: {parentage}")

        # Active Effects (buffs, conditions, persistent effects)
        # These MUST be applied to all relevant rolls and checks
        active_effects = pc.get("active_effects", [])
        if active_effects and isinstance(active_effects, list):
            lines.append("")
            lines.append("### Active Effects (ALWAYS APPLY)")
            lines.append(
                "The following buffs/effects are ALWAYS active and MUST be applied "
                "to all relevant rolls, checks, saves, and combat calculations:"
            )
            for effect in active_effects:
                if isinstance(effect, str) and effect.strip():
                    lines.append(f"  - {effect}")
                elif isinstance(effect, dict):
                    effect_name = (
                        effect.get("name") or effect.get("effect") or str(effect)
                    )
                    lines.append(f"  - {effect_name}")

        if len(lines) == 1:
            return ""  # Only header, no actual data

        return "\n".join(lines)

    # =========================================================================
    # God Mode Directive Management
    # =========================================================================

    def add_god_mode_directive(self, directive: str) -> None:
        """
        Add a God Mode directive to the campaign rules.

        These directives persist across sessions and are injected into prompts.

        Args:
            directive: The rule to add (e.g., "always award XP after combat")
        """
        if "god_mode_directives" not in self.custom_campaign_state:
            self.custom_campaign_state["god_mode_directives"] = []

        directives = self.custom_campaign_state["god_mode_directives"]

        # Check for duplicates
        existing_texts = [
            d.get("rule") if isinstance(d, dict) else d for d in directives
        ]
        if directive not in existing_texts:
            directives.append(
                {
                    "rule": directive,
                    "added": datetime.datetime.now(datetime.UTC).isoformat(),
                }
            )
            logging_util.info(f"GOD MODE DIRECTIVE ADDED: {directive}")

    def get_god_mode_directives(self) -> list[str]:
        """
        Get all active God Mode directives as a list of strings.

        Returns:
            List of directive rule strings
        """
        directives = self.custom_campaign_state.get("god_mode_directives", [])
        result = []
        for d in directives:
            if isinstance(d, dict):
                result.append(d.get("rule", str(d)))
            else:
                result.append(str(d))
        return result

    def get_god_mode_directives_block(self) -> str:
        """
        Generate a formatted block of God Mode directives for system prompts.

        Returns:
            Formatted string block for system prompts
        """
        directives = self.get_god_mode_directives()
        if not directives:
            return ""

        lines = ["## Active God Mode Directives"]
        lines.append("The following rules were set by the player and MUST be followed:")
        for i, directive in enumerate(directives, 1):
            lines.append(f"{i}. {directive}")

        return "\n".join(lines)

    # =========================================================================
    # Campaign Upgrade Detection (Divine/Multiverse Tiers)
    # =========================================================================

    def get_campaign_tier(self) -> str:
        """Get the current campaign tier (mortal, divine, or sovereign)."""
        return self.custom_campaign_state.get(
            "campaign_tier", constants.CAMPAIGN_TIER_MORTAL
        )

    def is_divine_upgrade_available(self) -> bool:
        """
        Check if divine upgrade (mortal → divine) is available.

        Triggers:
        - divine_potential >= 100
        - Level >= 25
        - divine_upgrade_available flag set by narrative milestone
        """
        if self.get_campaign_tier() != constants.CAMPAIGN_TIER_MORTAL:
            return False

        # Check explicit flag (set by narrative milestone)
        if self.custom_campaign_state.get("divine_upgrade_available", False):
            return True

        # Check divine potential threshold
        divine_potential = self.custom_campaign_state.get("divine_potential", 0)
        if divine_potential >= constants.DIVINE_POTENTIAL_THRESHOLD:
            return True

        # Check level threshold
        # Level may be at top-level (normalized) or in experience dict
        level = self.player_character_data.get("level", None)
        if level is None:
            experience = self.player_character_data.get("experience", {})
            level = experience.get("level", 1) if isinstance(experience, dict) else 1
        if level >= constants.DIVINE_UPGRADE_LEVEL_THRESHOLD:
            return True

        return False

    def is_multiverse_upgrade_available(self) -> bool:
        """
        Check if multiverse upgrade (any tier → sovereign) is available.

        Triggers:
        - universe_control >= 70
        - multiverse_upgrade_available flag set by narrative milestone
        """
        if self.get_campaign_tier() == constants.CAMPAIGN_TIER_SOVEREIGN:
            return False

        # Check explicit flag (set by narrative milestone)
        if self.custom_campaign_state.get("multiverse_upgrade_available", False):
            return True

        # Check universe control threshold
        universe_control = self.custom_campaign_state.get("universe_control", 0)
        if universe_control >= constants.UNIVERSE_CONTROL_THRESHOLD:
            return True

        return False

    def is_campaign_upgrade_available(self) -> bool:
        """Check if any campaign upgrade is currently available."""
        return self.is_divine_upgrade_available() or self.is_multiverse_upgrade_available()

    def get_pending_upgrade_type(self) -> str | None:
        """
        Get the type of upgrade that's currently available.

        Returns:
            "divine" if divine upgrade is available
            "multiverse" if multiverse upgrade is available
            None if no upgrade is available
        """
        # Multiverse takes priority (can upgrade from any tier)
        if self.is_multiverse_upgrade_available():
            return "multiverse"
        if self.is_divine_upgrade_available():
            return "divine"
        return None

    def get_highest_stat_modifier(self) -> int:
        """
        Get the highest ability score modifier for GP calculation.

        Used for converting stats to God Power in divine/sovereign tiers.
        """
        attributes = self.player_character_data.get("attributes", {})
        if not isinstance(attributes, dict):
            return 0

        highest_modifier = 0
        for attr_name, attr_value in attributes.items():
            if isinstance(attr_value, dict):
                # Handle {"score": 18, "modifier": 4} format
                modifier = attr_value.get("modifier", 0)
            elif isinstance(attr_value, int):
                # Handle direct score value - calculate modifier
                modifier = (attr_value - 10) // 2
            else:
                continue

            if isinstance(modifier, int) and modifier > highest_modifier:
                highest_modifier = modifier

        return highest_modifier

    # =========================================================================
    # Post-Combat Reward Detection
    # =========================================================================

    def detect_post_combat_issues(
        self,
        previous_combat_state: dict[str, Any] | None,
        state_changes: dict[str, Any],
    ) -> list[str]:
        """
        Detect issues after combat ends, such as missing XP awards.

        Args:
            previous_combat_state: Combat state before the update
            state_changes: The state changes being applied

        Returns:
            List of warning messages
        """
        warnings: list[str] = []

        # Normalize inputs - handle None and non-dict types
        if not previous_combat_state or not isinstance(previous_combat_state, dict):
            return warnings
        if not isinstance(state_changes, dict):
            state_changes = {}

        was_in_combat = previous_combat_state.get("in_combat", False)
        is_now_in_combat = self.combat_state.get("in_combat", False)

        # Check if combat just ended
        if was_in_combat and not is_now_in_combat:
            # Check if XP was awarded in the state changes
            # Use `or {}` to handle explicit null values in state_changes
            pc_changes = state_changes.get("player_character_data") or {}
            if not isinstance(pc_changes, dict):
                pc_changes = {}
            xp_awarded = False

            # Check various XP fields
            if "xp" in pc_changes or "xp_current" in pc_changes:
                xp_awarded = True
            elif "experience" in pc_changes:
                exp_changes = pc_changes["experience"]
                if (
                    isinstance(exp_changes, dict)
                    and "current" in exp_changes
                    or isinstance(exp_changes, (int, float, str))
                ):
                    xp_awarded = True

            if not xp_awarded:
                # Count only defeated enemies (hp <= 0, excluding player/allies)
                combatants = previous_combat_state.get("combatants") or {}
                if not isinstance(combatants, dict):
                    combatants = {}
                defeated_count = sum(
                    1
                    for combatant in combatants.values()
                    if isinstance(combatant, dict)
                    and _coerce_int(combatant.get("hp_current", 1), 1) <= 0
                    and not combatant.get("is_player", False)
                    and not combatant.get("is_ally", False)
                )
                if defeated_count == 0:
                    # Fallback to combat_summary if combatants were already cleaned up
                    combat_summary = previous_combat_state.get("combat_summary")
                    if isinstance(combat_summary, dict):
                        enemies_defeated = combat_summary.get("enemies_defeated", 0)
                        enemies_defeated_int = _coerce_int(enemies_defeated, 0)
                        defeated_count = max(defeated_count, enemies_defeated_int)
                if defeated_count > 0:
                    warnings.append(
                        f"Combat ended but no XP was awarded. "
                        f"Consider awarding XP for {defeated_count} defeated enemy/enemies."
                    )

        return warnings


@overload
def validate_and_correct_state(
    state_dict: dict[str, Any],
    previous_world_time: dict[str, Any] | None = None,
    return_corrections: Literal[False] = False,
) -> dict[str, Any]: ...


@overload
def validate_and_correct_state(
    state_dict: dict[str, Any],
    previous_world_time: dict[str, Any] | None = None,
    return_corrections: Literal[True] = ...,
) -> tuple[dict[str, Any], list[str]]: ...


def validate_and_correct_state(
    state_dict: dict[str, Any],
    previous_world_time: dict[str, Any] | None = None,
    return_corrections: bool = False,
) -> dict[str, Any] | tuple[dict[str, Any], list[str]]:
    """
    Validate state dict and apply corrections before persistence.

    Uses GameState's internal validation logic.

    Args:
        state_dict: The state dictionary to validate
        previous_world_time: Previous world time for monotonicity check
        return_corrections: If True, returns tuple of (state, corrections_list)

    Returns:
        If return_corrections=False: corrected state dict
        If return_corrections=True: tuple of (corrected state dict, list of correction messages)
    """
    corrections: list[str] = []

    # Create temporary GameState to run validations
    temp_state = GameState.from_dict(state_dict.copy())
    if temp_state is None:
        logging_util.warning(
            "VALIDATION: Could not create GameState from dict, skipping validation"
        )
        if return_corrections:
            return state_dict, corrections
        return state_dict

    # 1. XP/Level Validation (using Main's logic)
    # This modifies temp_state in-place (auto-corrects)
    xp_result = temp_state.validate_xp_level(strict=False)
    if xp_result.get("corrected"):
        provided = xp_result.get("provided_level")
        expected = xp_result.get("expected_level")
        corrections.append(
            f"Level auto-corrected from {provided} to {expected} based on XP"
        )
        logging_util.info(f"XP Validation applied corrections: {xp_result}")
    elif xp_result.get("computed_level"):
        corrections.append(
            f"Level computed as {xp_result.get('computed_level')} from XP"
        )
        logging_util.info(f"XP Validation applied corrections: {xp_result}")
    if xp_result.get("clamped_xp") is not None:
        corrections.append("Negative XP clamped to 0")
    if xp_result.get("clamped_level") is not None:
        corrections.append(
            f"Level clamped to minimum 1: {xp_result.get('clamped_level')}"
        )
    if xp_result.get("epic_level"):
        corrections.append(
            f"Epic level {xp_result.get('provided_level')} accepted (beyond standard D&D 5e)"
        )

    # 2. Time Monotonicity (using Main's logic)
    # Get current time from world_data in state_dict (not temp_state, as we want to check input)
    new_time = (state_dict.get("world_data", {}) or {}).get("world_time")
    if new_time:
        # Note: In strict mode this raises, in default mode it just warns
        time_result = temp_state.validate_time_monotonicity(
            new_time, strict=False, previous_time=previous_world_time
        )
        if time_result.get("warning"):
            corrections.append(
                f"Time warning: {time_result.get('message', 'time regression detected')}"
            )

    result_state = temp_state.to_dict()

    if return_corrections:
        return result_state, corrections
    return result_state


def roll_dice(notation: str) -> DiceRollResult:
    """Backward-compatible wrapper around dice.roll_dice."""
    return dice_module.roll_dice(notation)


def roll_with_advantage(notation: str) -> tuple[DiceRollResult, DiceRollResult, int]:
    """Backward-compatible wrapper around dice.roll_with_advantage."""
    return dice_module.roll_with_advantage(notation)


def roll_with_disadvantage(notation: str) -> tuple[DiceRollResult, DiceRollResult, int]:
    """Backward-compatible wrapper around dice.roll_with_disadvantage."""
    return dice_module.roll_with_disadvantage(notation)


def calculate_attack_roll(
    attack_modifier: int, advantage: bool = False, disadvantage: bool = False
) -> dict:
    """Backward-compatible wrapper that keeps monkeypatching stable in tests."""
    notation = (
        f"1d20+{attack_modifier}" if attack_modifier >= 0 else f"1d20{attack_modifier}"
    )

    def _safe_natural_roll(roll: DiceRollResult) -> int:
        if roll.individual_rolls:
            return int(roll.individual_rolls[0])
        return max(0, int(roll.total) - int(roll.modifier))

    if advantage and not disadvantage:
        roll1, roll2, total = roll_with_advantage(notation)
        natural_rolls = [_safe_natural_roll(roll1), _safe_natural_roll(roll2)]
        natural = max(natural_rolls)
        return {
            "rolls": natural_rolls,
            "modifier": attack_modifier,
            "total": total,
            "used_roll": "higher",
            "is_critical": natural == 20,
            "is_fumble": natural_rolls[0] == 1 and natural_rolls[1] == 1,
            "notation": notation,
        }
    if disadvantage and not advantage:
        roll1, roll2, total = roll_with_disadvantage(notation)
        natural_rolls = [_safe_natural_roll(roll1), _safe_natural_roll(roll2)]
        natural = min(natural_rolls)
        return {
            "rolls": natural_rolls,
            "modifier": attack_modifier,
            "total": total,
            "used_roll": "lower",
            "is_critical": natural_rolls[0] == 20 and natural_rolls[1] == 20,
            "is_fumble": natural == 1,
            "notation": notation,
        }
    roll = roll_dice(notation)
    return {
        "rolls": roll.individual_rolls,
        "modifier": attack_modifier,
        "total": roll.total,
        "used_roll": "single",
        "is_critical": roll.natural_20,
        "is_fumble": roll.natural_1,
        "notation": notation,
    }


def calculate_damage(damage_notation: str, is_critical: bool = False) -> DiceRollResult:
    """Backward-compatible wrapper around dice.calculate_damage."""
    return dice_module.calculate_damage(damage_notation, is_critical)


def calculate_skill_check(
    attribute_modifier: int,
    proficiency_bonus: int,
    proficient: bool = False,
    expertise: bool = False,
) -> DiceRollResult:
    """Backward-compatible wrapper around dice.calculate_skill_check."""
    return dice_module.calculate_skill_check(
        attribute_modifier, proficiency_bonus, proficient, expertise
    )


def calculate_saving_throw(
    attribute_modifier: int, proficiency_bonus: int, proficient: bool = False
) -> DiceRollResult:
    """Backward-compatible wrapper around dice.calculate_saving_throw."""
    return dice_module.calculate_saving_throw(
        attribute_modifier, proficiency_bonus, proficient
    )


def calculate_modifier(attribute: int) -> int:
    """Calculate ability modifier from attribute score."""
    return (attribute - 10) // 2


def calculate_proficiency_bonus(level: int) -> int:
    """Get proficiency bonus for a given character level."""
    if level < 1:
        return 2
    if level > 20:
        return 6
    return PROFICIENCY_BY_LEVEL.get(level, 2)


def calculate_armor_class(
    dex_modifier: int, armor_bonus: int = 0, shield_bonus: int = 0
) -> int:
    """Calculate Armor Class."""
    return 10 + dex_modifier + armor_bonus + shield_bonus


def calculate_passive_perception(
    wis_modifier: int, proficient: bool, proficiency_bonus: int
) -> int:
    """Calculate passive Perception score."""
    base = 10 + wis_modifier
    if proficient:
        base += proficiency_bonus
    return base


def xp_for_cr(cr: float) -> int:
    """Get XP award for defeating a creature of given Challenge Rating."""
    return XP_BY_CR.get(cr, 0)


def calculate_resource_depletion(
    current_amount: float,
    depletion_rate: float,
    time_elapsed: float,
    _depletion_unit: str = "per_day",
) -> float:
    """Calculate resource depletion over time."""
    depleted = depletion_rate * time_elapsed
    remaining = current_amount - depleted
    return max(0.0, remaining)


def execute_tool_requests(tool_requests: list[dict]) -> list[dict]:
    """
    Execute a list of tool requests with strict type validation.

    Args:
        tool_requests: List of dicts, each containing "tool" (str) and "args" (dict).

    Returns:
        List of results with tool execution details.
    """
    if not isinstance(tool_requests, list):
        logging_util.error(f"tool_requests must be a list, got {type(tool_requests)}")
        return []

    results = []
    for request in tool_requests:
        if not isinstance(request, dict):
            logging_util.error(f"Tool request must be dict, got {type(request)}")
            results.append(
                {
                    "tool": "unknown",
                    "args": {},
                    "result": {"error": f"Invalid request type: {type(request)}"},
                }
            )
            continue

        tool_name = request.get("tool")
        args = request.get("args", {})

        # Strict Type Validation
        if not isinstance(tool_name, str) or not tool_name:
            logging_util.error(
                f"Invalid tool name type or empty: {tool_name} ({type(tool_name)})"
            )
            results.append(
                {
                    "tool": str(tool_name),
                    "args": args if isinstance(args, dict) else {},
                    "result": {"error": "Invalid tool name"},
                }
            )
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

        results.append(
            {
                "tool": tool_name,
                "args": args,
                "result": result,
            }
        )

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
        if (
            isinstance(result, dict)
            and isinstance(result.get("formatted"), str)
            and result["formatted"]
        ):
            # Keep Phase 2 context tight: formatted strings already embed the exact numbers.
            lines.append(f"- {result['formatted']}")
            continue
        if (
            isinstance(result, dict)
            and isinstance(result.get("error"), str)
            and result["error"]
        ):
            lines.append(f"- {tool_name}: ERROR {result['error']}")
            continue
        # Fallback: last-resort JSON (should be rare)
        try:
            result_str = json.dumps(result, sort_keys=True)
        except TypeError:
            result_str = json.dumps(
                {"error": "unserializable tool result"}, sort_keys=True
            )
        lines.append(f"- {tool_name}: {result_str}")

    return "\n".join(lines)
