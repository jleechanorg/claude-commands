"""
Defensive numeric field converter that handles 'unknown' and invalid values
"""

from typing import Any

from mvp_site import logging_util


class DefensiveNumericConverter:
    """Handles conversion of numeric fields with fallback defaults for unknown/invalid values.

    When invalid values are encountered, logs warnings and uses safe defaults.
    """

    # Field categories for validation rules
    HP_FIELDS = {"hp", "hp_current", "hp_max", "level"}
    NON_NEGATIVE_FIELDS = {
        "temp_hp",
        "xp",
        "xp_current",
        "gold",
        "successes",
        "failures",
        "damage",
        "healing",
        "initiative",
    }
    ABILITY_SCORE_FIELDS = {
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
    }

    # Define default values for different types of numeric fields
    FIELD_DEFAULTS: dict[str, int] = {
        # HP-related fields (minimum 1 for living entities)
        "hp": 1,
        "hp_current": 1,
        "hp_max": 1,
        "temp_hp": 0,
        # Character stats (D&D standard average)
        "level": 1,
        "xp": 0,
        "xp_current": 0,
        "xp_to_next_level": 300,
        "ac": 10,
        "armor_class": 10,
        "initiative": 0,
        # Ability scores (D&D standard average)
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10,
        # Combat-related
        "damage": 0,
        "healing": 0,
        "attack_bonus": 0,
        # Resources
        "gold": 0,
        "hero_points": 0,
        "inspiration_points": 0,
        # Other numeric fields
        "round_number": 1,
        "turn_number": 1,
        "session_number": 1,
        "successes": 0,
        "failures": 0,
    }

    @classmethod
    def convert_value(cls, key: str, value: Any) -> Any:
        """
        Convert a value to integer with defensive handling of unknown/invalid values.

        Args:
            key: The field name
            value: The value to potentially convert

        Returns:
            The value converted to int with appropriate defaults for unknown/invalid values
        """
        if key not in cls.FIELD_DEFAULTS:
            return value

        # Handle explicit 'unknown' values (case-insensitive)
        if (isinstance(value, str) and value.lower() == "unknown") or value is None:
            logging_util.warning(
                f"Invalid value '{value}' for field '{key}'. Using default: {cls.FIELD_DEFAULTS[key]}"
            )
            return cls.FIELD_DEFAULTS[key]

        # Try to convert to integer
        try:
            converted = int(value)

            # Apply field-specific validation using field sets
            if key in cls.HP_FIELDS:
                # These fields should never be less than 1
                return max(1, converted)
            if key in cls.NON_NEGATIVE_FIELDS:
                # These fields should never be negative
                return max(0, converted)
            if key in cls.ABILITY_SCORE_FIELDS:
                # Ability scores should be 1-30
                return max(1, min(30, converted))
            return converted

        except (ValueError, TypeError):
            # If conversion fails, return the default
            logging_util.warning(
                f"Failed to convert '{value}' to int for field '{key}'. Using default: {cls.FIELD_DEFAULTS[key]}"
            )
            return cls.FIELD_DEFAULTS[key]

    @classmethod
    def convert_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively convert all numeric fields in a dictionary with defensive handling.

        Args:
            data: Dictionary to process

        Returns:
            Dictionary with numeric fields converted to integers with safe defaults
        """
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                result[key] = cls.convert_dict(value)
            elif isinstance(value, list):
                # Process lists (in case they contain dicts or numeric values)
                result[key] = [
                    cls.convert_dict(item)
                    if isinstance(item, dict)
                    else cls.convert_value(key, item)
                    for item in value
                ]
            elif key in cls.FIELD_DEFAULTS:
                result[key] = cls.convert_value(key, value)
            else:
                result[key] = value

        return result
