"""
TurnNumber value object - represents a turn number within a scene.
"""
from typing import Any


class TurnNumber:
    """
    Value object representing a turn number within a scene.
    
    Turns are numbered starting from 1 within each scene, representing
    individual player actions and AI responses.
    """
    
    def __init__(self, value: int):
        """
        Create a new TurnNumber.
        
        Args:
            value: The turn number (must be positive)
            
        Raises:
            ValueError: If the value is not a positive integer
        """
        if not isinstance(value, int):
            raise ValueError("TurnNumber must be an integer")
        
        if value < 1:
            raise ValueError("TurnNumber must be positive (>= 1)")
        
        self._value = value
    
    @classmethod
    def first(cls) -> 'TurnNumber':
        """Create the first turn number."""
        return cls(1)
    
    def next(self) -> 'TurnNumber':
        """Get the next turn number."""
        return TurnNumber(self._value + 1)
    
    def previous(self) -> 'TurnNumber':
        """
        Get the previous turn number.
        
        Raises:
            ValueError: If already at turn 1
        """
        if self._value <= 1:
            raise ValueError("Cannot go before turn 1")
        return TurnNumber(self._value - 1)
    
    @property
    def value(self) -> int:
        """Get the integer value of the turn number."""
        return self._value
    
    def __str__(self) -> str:
        """String representation."""
        return str(self._value)
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"TurnNumber({self._value})"
    
    def __eq__(self, other: Any) -> bool:
        """Check equality with another TurnNumber."""
        if not isinstance(other, TurnNumber):
            return False
        return self._value == other._value
    
    def __lt__(self, other: 'TurnNumber') -> bool:
        """Check if this turn comes before another."""
        if not isinstance(other, TurnNumber):
            return NotImplemented
        return self._value < other._value
    
    def __le__(self, other: 'TurnNumber') -> bool:
        """Check if this turn comes before or equals another."""
        if not isinstance(other, TurnNumber):
            return NotImplemented
        return self._value <= other._value
    
    def __gt__(self, other: 'TurnNumber') -> bool:
        """Check if this turn comes after another."""
        if not isinstance(other, TurnNumber):
            return NotImplemented
        return self._value > other._value
    
    def __ge__(self, other: 'TurnNumber') -> bool:
        """Check if this turn comes after or equals another."""
        if not isinstance(other, TurnNumber):
            return NotImplemented
        return self._value >= other._value
    
    def __hash__(self) -> int:
        """Make TurnNumber hashable for use in sets and dicts."""
        return hash(self._value)