"""
Numeric field converter utilities for converting string values to integers.
Used primarily for data layer operations (e.g., Firestore) where simple conversion
is needed without smart defaults. For robust entity conversion with fallbacks,
use DefensiveNumericConverter instead.
"""

from typing import Any


class NumericFieldConverter:
    """Simple utilities for converting string values to integers"""

    @classmethod
    def try_convert_to_int(cls, value: Any) -> Any:
        """
        Try to convert a value to integer, return original if conversion fails.

        Args:
            value: The value to potentially convert

        Returns:
            The value converted to int if possible, otherwise unchanged
        """
        if isinstance(value, str):
            try:
                return int(value)
            except (ValueError, TypeError):
                return value
        return value

    @classmethod
    def convert_dict_with_fields(
        cls, data: dict[str, Any], numeric_fields: set[str]
    ) -> dict[str, Any]:
        """
        Recursively convert specified numeric fields in a dictionary.

        Args:
            data: Dictionary to process
            numeric_fields: Set of field names that should be converted to integers

        Returns:
            Dictionary with specified numeric fields converted to integers
        """
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                result[key] = cls.convert_dict_with_fields(value, numeric_fields)
            elif isinstance(value, list):
                # Process lists (in case they contain dicts)
                result[key] = [
                    cls.convert_dict_with_fields(item, numeric_fields)
                    if isinstance(item, dict)
                    else cls.try_convert_to_int(item)
                    if key in numeric_fields
                    else item
                    for item in value
                ]
            # Convert the value if it's in the numeric fields set
            elif key in numeric_fields:
                result[key] = cls.try_convert_to_int(value)
            else:
                result[key] = value

        return result

    @classmethod
    def convert_all_possible_ints(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Try to convert all string values that look like integers.
        This is useful for general-purpose conversion where you don't know field names.

        Args:
            data: Dictionary to process

        Returns:
            Dictionary with all convertible string integers converted
        """
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                result[key] = cls.convert_all_possible_ints(value)
            elif isinstance(value, list):
                # Process lists
                result[key] = [
                    cls.convert_all_possible_ints(item)
                    if isinstance(item, dict)
                    else cls.try_convert_to_int(item)
                    for item in value
                ]
            else:
                # Try to convert any value
                result[key] = cls.try_convert_to_int(value)

        return result

    # Legacy methods for backward compatibility - delegate to new methods
    @classmethod
    def convert_value(cls, key: str, value: Any) -> Any:
        """Legacy method - just tries to convert the value regardless of key"""
        return cls.try_convert_to_int(value)

    @classmethod
    def convert_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Legacy method - tries to convert all possible integers"""
        return cls.convert_all_possible_ints(data)
