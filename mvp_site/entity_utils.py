"""
Entity Utils - Backward Compatibility Shim

This module is maintained for backward compatibility.
All functionality has been consolidated into entity_validator.py.

Import from mvp_site.entity_validator for new code.
"""

from mvp_site.entity_validator import filter_unknown_entities, is_unknown_entity

__all__ = ["filter_unknown_entities", "is_unknown_entity"]
