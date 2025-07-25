"""
Utility functions for entity handling and validation.
"""

from typing import List


def filter_unknown_entities(entities: List[str]) -> List[str]:
    """
    Filter out 'Unknown' entities from a list.

    'Unknown' is used as a default location name when location is not found
    in world_data and should not be treated as a real entity for validation.

    Args:
        entities: List of entity names to filter

    Returns:
        List of entities with 'Unknown' entries removed
    """
    return [e for e in entities if e.lower() != 'unknown']


def is_unknown_entity(entity: str) -> bool:
    """
    Check if an entity is the 'Unknown' placeholder.

    Args:
        entity: Entity name to check

    Returns:
        True if entity is 'Unknown' (case-insensitive), False otherwise
    """
    return entity.lower() == 'unknown'
