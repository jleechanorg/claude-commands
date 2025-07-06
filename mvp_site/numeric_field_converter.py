"""
Numeric field converter for ensuring numeric values are stored as integers in Firestore
"""
from typing import Any, Dict, Set


class NumericFieldConverter:
    """Handles conversion of numeric fields from strings to integers"""
    
    # Define which fields should be stored as integers
    NUMERIC_FIELDS: Set[str] = {
        # HP-related fields
        'hp', 'hp_current', 'hp_max', 'temp_hp',
        
        # Character stats
        'level', 'xp', 'xp_current', 'xp_to_next_level',
        'ac', 'armor_class', 'initiative',
        
        # Ability scores
        'strength', 'dexterity', 'constitution',
        'intelligence', 'wisdom', 'charisma',
        
        # Combat-related
        'damage', 'healing', 'attack_bonus',
        
        # Resources
        'gold', 'hero_points', 'inspiration_points',
        
        # Other numeric fields
        'round_number', 'turn_number', 'session_number',
        'successes', 'failures'  # Death saves
    }
    
    @classmethod
    def convert_value(cls, key: str, value: Any) -> Any:
        """
        Convert a value to integer if the key is a known numeric field.
        
        Args:
            key: The field name
            value: The value to potentially convert
            
        Returns:
            The value converted to int if applicable, otherwise unchanged
        """
        if key in cls.NUMERIC_FIELDS and isinstance(value, str):
            try:
                # Try to convert to integer
                return int(value)
            except (ValueError, TypeError):
                # If conversion fails, return original value
                return value
        return value
    
    @classmethod
    def convert_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively convert all numeric fields in a dictionary.
        
        Args:
            data: Dictionary to process
            
        Returns:
            Dictionary with numeric fields converted to integers
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
                    cls.convert_dict(item) if isinstance(item, dict) else cls.convert_value(key, item)
                    for item in value
                ]
            else:
                # Convert the value if it's a numeric field
                result[key] = cls.convert_value(key, value)
        
        return result
    
    @classmethod
    def is_numeric_field(cls, field_name: str) -> bool:
        """Check if a field name should be stored as a number."""
        return field_name in cls.NUMERIC_FIELDS