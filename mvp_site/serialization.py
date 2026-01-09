"""Centralized JSON serialization helpers for mvp_site.

This module consolidates the previously duplicated json_default_serializer
functions from: firestore_service.py, llm_request.py, world_logic.py,
llm_service.py, and mock_firestore_service_wrapper.py.

All modules should import from here to ensure consistent serialization behavior.
"""

from typing import Any, Optional

# Lazy import to avoid circular dependency issues
_firestore = None

# Max string length for serialization (prevents huge serializations)
MAX_STRING_LENGTH = 10000


def _get_firestore():
    """Lazy load firestore module to avoid import issues."""
    global _firestore
    if _firestore is None:
        try:
            from google.cloud import firestore  # type: ignore

            _firestore = firestore
        except ImportError:
            _firestore = False  # Mark as unavailable
    return _firestore if _firestore else None


def json_default_serializer(obj: Any) -> Any:
    """
    Unified JSON serializer for objects that aren't serializable by default.

    Handles:
    - datetime/date objects (via isoformat)
    - Firestore sentinels (DELETE_FIELD, SERVER_TIMESTAMP)
    - Sets/frozensets (converted to lists)
    - Bytes (decoded to UTF-8 string)
    - Objects with to_dict() method (like GameState, entities)
    - Objects with __dict__ attribute
    - String fallback with length limiting

    Args:
        obj: Object to serialize

    Returns:
        JSON-serializable representation of the object

    Raises:
        TypeError: If object cannot be serialized
    """
    # Handle datetime objects (most common case)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()

    # Handle Firestore sentinels
    firestore = _get_firestore()
    if firestore is not None:
        if obj is firestore.DELETE_FIELD:
            return None
        if obj is firestore.SERVER_TIMESTAMP:
            return "<SERVER_TIMESTAMP>"

    # Handle Sentinel objects (from testing frameworks like unittest.mock)
    if type(obj).__name__ == "Sentinel":
        return "<SERVER_TIMESTAMP>"

    # Handle sets by converting to lists
    if isinstance(obj, (set, frozenset)):
        return list(obj)

    # Handle bytes by decoding to string
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")

    # Handle objects with to_dict method (like GameState, entities, SceneManifest)
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        try:
            return obj.to_dict()
        except (AttributeError, TypeError):
            pass  # Fall through to next method

    # Handle objects with __dict__ attribute
    if hasattr(obj, "__dict__"):
        try:
            return obj.__dict__
        except (AttributeError, TypeError):
            pass  # Fall through to string representation

    # Fall back to string representation with length limiting
    if hasattr(obj, "__str__"):
        try:
            str_repr = str(obj)
            if len(str_repr) > MAX_STRING_LENGTH:
                return str_repr[:MAX_STRING_LENGTH] + "...[truncated]"
            return str_repr
        except (UnicodeDecodeError, UnicodeEncodeError, TypeError):
            pass

    # Last resort - raise to surface unsupported types
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def json_serial(obj: Any) -> Optional[str]:
    """
    Simple JSON serializer for basic types (backward compatibility alias).

    This is a simpler version primarily for logging purposes.
    For most cases, use json_default_serializer instead.

    Args:
        obj: Object to serialize

    Returns:
        String representation or raises TypeError

    Raises:
        TypeError: If object type is not supported
    """
    if hasattr(obj, "isoformat"):
        return obj.isoformat()

    if type(obj).__name__ == "Sentinel":
        return "<SERVER_TIMESTAMP>"

    # Check Firestore sentinels
    firestore = _get_firestore()
    if firestore is not None:
        if obj is firestore.DELETE_FIELD:
            return None
        if obj is firestore.SERVER_TIMESTAMP:
            return "<SERVER_TIMESTAMP>"

    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# Re-export for backward compatibility
__all__ = ["json_default_serializer", "json_serial", "MAX_STRING_LENGTH"]
