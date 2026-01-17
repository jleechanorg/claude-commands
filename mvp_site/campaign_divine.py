"""
Campaign Divine/Multiverse Upgrade Detection Logic

Extracted from game_state.py to keep upgrade detection logic separate and maintainable.
"""

from __future__ import annotations

from typing import Any

from mvp_site import constants


def _coerce_int(value: Any, default: int | None = 0) -> int | None:
    """
    Safely coerce value to int.

    Handles string numbers from JSON/LLM responses and floats.

    Args:
        value: The value to coerce (int, str, float, or other)
        default: Default value if coercion fails (can be None)

    Returns:
        Coerced int value, or default if coercion fails
    """
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str)):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default
    return default


def get_campaign_tier(custom_campaign_state: dict[str, Any]) -> str:
    """
    Get the current campaign tier (mortal, divine, or sovereign).

    Args:
        custom_campaign_state: The custom_campaign_state dict from GameState

    Returns:
        Campaign tier constant (mortal, divine, or sovereign)
    """
    return custom_campaign_state.get(
        "campaign_tier", constants.CAMPAIGN_TIER_MORTAL
    )


def is_divine_upgrade_available(
    custom_campaign_state: dict[str, Any],
    player_character_data: dict[str, Any],
) -> bool:
    """
    Check if divine upgrade (mortal → divine) is available.

    Triggers:
    - divine_potential >= 100
    - Level >= 25
    - divine_upgrade_available flag set by narrative milestone

    Args:
        custom_campaign_state: The custom_campaign_state dict from GameState
        player_character_data: The player_character_data dict from GameState

    Returns:
        True if divine upgrade is available, False otherwise
    """
    if get_campaign_tier(custom_campaign_state) != constants.CAMPAIGN_TIER_MORTAL:
        return False

    # Check explicit flag (set by narrative milestone)
    if custom_campaign_state.get("divine_upgrade_available", False):
        return True

    # Check divine potential threshold (coerce to int to handle string values)
    divine_potential_raw = custom_campaign_state.get("divine_potential", 0)
    divine_potential = _coerce_int(divine_potential_raw, 0)
    if divine_potential and divine_potential >= constants.DIVINE_POTENTIAL_THRESHOLD:
        return True

    # Check level threshold (coerce to int to handle string values)
    # Level may be at top-level (normalized) or in experience dict
    # Guard against non-dict player_character_data (Firestore can persist nulls)
    pc_data = player_character_data if isinstance(player_character_data, dict) else {}
    level_raw = pc_data.get("level", None)
    if level_raw is None:
        experience = pc_data.get("experience", {})
        level_raw = experience.get("level", 1) if isinstance(experience, dict) else 1
    level = _coerce_int(level_raw, 1)
    if level and level >= constants.DIVINE_UPGRADE_LEVEL_THRESHOLD:
        return True

    return False


def is_multiverse_upgrade_available(
    custom_campaign_state: dict[str, Any],
) -> bool:
    """
    Check if multiverse upgrade (any tier → sovereign) is available.

    Triggers:
    - universe_control >= 70
    - multiverse_upgrade_available flag set by narrative milestone

    Args:
        custom_campaign_state: The custom_campaign_state dict from GameState

    Returns:
        True if multiverse upgrade is available, False otherwise
    """
    if get_campaign_tier(custom_campaign_state) == constants.CAMPAIGN_TIER_SOVEREIGN:
        return False

    # Check explicit flag (set by narrative milestone)
    if custom_campaign_state.get("multiverse_upgrade_available", False):
        return True

    # Check universe control threshold (coerce to int to handle string values)
    universe_control_raw = custom_campaign_state.get("universe_control", 0)
    universe_control = _coerce_int(universe_control_raw, 0)
    if universe_control and universe_control >= constants.UNIVERSE_CONTROL_THRESHOLD:
        return True

    return False


def is_campaign_upgrade_available(
    custom_campaign_state: dict[str, Any],
    player_character_data: dict[str, Any],
) -> bool:
    """
    Check if any campaign upgrade is currently available.

    Args:
        custom_campaign_state: The custom_campaign_state dict from GameState
        player_character_data: The player_character_data dict from GameState

    Returns:
        True if any upgrade is available, False otherwise
    """
    return is_divine_upgrade_available(
        custom_campaign_state, player_character_data
    ) or is_multiverse_upgrade_available(custom_campaign_state)


def get_pending_upgrade_type(
    custom_campaign_state: dict[str, Any],
    player_character_data: dict[str, Any],
) -> str | None:
    """
    Get the type of upgrade that's currently available.

    Args:
        custom_campaign_state: The custom_campaign_state dict from GameState
        player_character_data: The player_character_data dict from GameState

    Returns:
        "divine" if divine upgrade is available
        "multiverse" if multiverse upgrade is available
        None if no upgrade is available
    """
    # Multiverse takes priority (can upgrade from any tier)
    if is_multiverse_upgrade_available(custom_campaign_state):
        return "multiverse"
    if is_divine_upgrade_available(custom_campaign_state, player_character_data):
        return "divine"
    return None


def get_highest_stat_modifier(player_character_data: dict[str, Any]) -> int:
    """
    Get the highest ability score modifier for GP calculation.

    Used for converting stats to God Power in divine/sovereign tiers.

    Args:
        player_character_data: The player_character_data dict from GameState

    Returns:
        Highest ability modifier (defaults to 0 if none found)
    """
    pc_data = player_character_data if isinstance(player_character_data, dict) else {}
    attributes = pc_data.get("attributes", {})
    if not isinstance(attributes, dict):
        return 0

    highest_modifier: int | None = None
    for attr_name, attr_value in attributes.items():
        modifier: int | None = None
        if isinstance(attr_value, dict):
            # Handle {"score": 18, "modifier": 4} format
            if "modifier" in attr_value:
                modifier = _coerce_int(attr_value.get("modifier"), None)
            elif "score" in attr_value:
                score = _coerce_int(attr_value.get("score"), None)
                if score is not None:
                    modifier = (score - 10) // 2
        else:
            # Handle direct score value (int/str/float) - calculate modifier
            score = _coerce_int(attr_value, None)
            if score is not None:
                modifier = (score - 10) // 2

        if modifier is not None:
            if highest_modifier is None or modifier > highest_modifier:
                highest_modifier = modifier

    # Return 0 if no valid attributes found (fallback)
    return highest_modifier if highest_modifier is not None else 0
