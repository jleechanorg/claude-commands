"""
SceneNumber value object - represents a scene number in a campaign.
"""
from typing import Any


class SceneNumber:
    """
    Value object representing a scene number in a campaign.
    
    Scenes are numbered starting from 1, representing major narrative breaks
    in the campaign story.
    """
    
    def __init__(self, value: int):
        """
        Create a new SceneNumber.
        
        Args:
            value: The scene number (must be positive)
            
        Raises:
            ValueError: If the value is not a positive integer
        """
        if not isinstance(value, int):
            raise ValueError("SceneNumber must be an integer")
        
        if value < 1:
            raise ValueError("SceneNumber must be positive (>= 1)")
        
        self._value = value
    
    @classmethod
    def first(cls) -> 'SceneNumber':
        """Create the first scene number."""
        return cls(1)
    
    def next(self) -> 'SceneNumber':
        """Get the next scene number."""
        return SceneNumber(self._value + 1)
    
    def previous(self) -> 'SceneNumber':
        """
        Get the previous scene number.
        
        Raises:
            ValueError: If already at scene 1
        """
        if self._value <= 1:
            raise ValueError("Cannot go before scene 1")
        return SceneNumber(self._value - 1)
    
    @property
    def value(self) -> int:
        """Get the integer value of the scene number."""
        return self._value
    
    def __str__(self) -> str:
        """String representation."""
        return str(self._value)
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"SceneNumber({self._value})"
    
    def __eq__(self, other: Any) -> bool:
        """Check equality with another SceneNumber."""
        if not isinstance(other, SceneNumber):
            return False
        return self._value == other._value
    
    def __lt__(self, other: 'SceneNumber') -> bool:
        """Check if this scene comes before another."""
        if not isinstance(other, SceneNumber):
            return NotImplemented
        return self._value < other._value
    
    def __le__(self, other: 'SceneNumber') -> bool:
        """Check if this scene comes before or equals another."""
        if not isinstance(other, SceneNumber):
            return NotImplemented
        return self._value <= other._value
    
    def __gt__(self, other: 'SceneNumber') -> bool:
        """Check if this scene comes after another."""
        if not isinstance(other, SceneNumber):
            return NotImplemented
        return self._value > other._value
    
    def __ge__(self, other: 'SceneNumber') -> bool:
        """Check if this scene comes after or equals another."""
        if not isinstance(other, SceneNumber):
            return NotImplemented
        return self._value >= other._value
    
    def __hash__(self) -> int:
        """Make SceneNumber hashable for use in sets and dicts."""
        return hash(self._value)