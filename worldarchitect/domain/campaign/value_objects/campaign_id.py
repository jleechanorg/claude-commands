"""
CampaignId value object - represents a unique identifier for a campaign.
"""
from typing import Any
import uuid


class CampaignId:
    """
    Value object representing a unique campaign identifier.
    
    This ensures that campaign IDs are always valid and provides
    type safety throughout the domain layer.
    """
    
    def __init__(self, value: str):
        """
        Create a new CampaignId.
        
        Args:
            value: The string representation of the campaign ID
            
        Raises:
            ValueError: If the value is empty or invalid
        """
        if not value or not isinstance(value, str):
            raise ValueError("CampaignId must be a non-empty string")
        
        self._value = value.strip()
        
        if not self._value:
            raise ValueError("CampaignId cannot be whitespace only")
    
    @classmethod
    def generate(cls) -> 'CampaignId':
        """Generate a new unique CampaignId."""
        return cls(str(uuid.uuid4()))
    
    @property
    def value(self) -> str:
        """Get the string value of the campaign ID."""
        return self._value
    
    def __str__(self) -> str:
        """String representation."""
        return self._value
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"CampaignId('{self._value}')"
    
    def __eq__(self, other: Any) -> bool:
        """Check equality with another CampaignId."""
        if not isinstance(other, CampaignId):
            return False
        return self._value == other._value
    
    def __hash__(self) -> int:
        """Make CampaignId hashable for use in sets and dicts."""
        return hash(self._value)