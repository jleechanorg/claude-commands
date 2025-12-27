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
    def convert_dict_with_fields(cls, data: Any, numeric_fields: set[str]) -> Any:
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

        result: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                result[key] = cls.convert_dict_with_fields(value, numeric_fields)
            elif isinstance(value, list):
                # Process lists (in case they contain dicts)
                converted_list = []
                for item in value:
                    if isinstance(item, dict):
                        converted_list.append(
                            cls.convert_dict_with_fields(item, numeric_fields)
                        )
                    elif key in numeric_fields:
                        converted_list.append(cls.try_convert_to_int(item))
                    else:
                        converted_list.append(item)
                result[key] = converted_list
            # Convert the value if it's in the numeric fields set
            elif key in numeric_fields:
                result[key] = cls.try_convert_to_int(value)
            else:
                result[key] = value

        return result

    @classmethod
    def convert_all_possible_ints(cls, data: Any) -> Any:
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

        result: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                result[key] = cls.convert_all_possible_ints(value)
            elif isinstance(value, list):
                # Process lists
                converted_list = []
                for item in value:
                    if isinstance(item, dict):
                        converted_list.append(cls.convert_all_possible_ints(item))
                    else:
                        converted_list.append(cls.try_convert_to_int(item))
                result[key] = converted_list
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
