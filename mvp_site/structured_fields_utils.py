"""Utility helpers for extracting structured Gemini response fields."""

from __future__ import annotations

from typing import Any, Dict, TypeVar

from mvp_site import constants

T = TypeVar("T")


def _get_structured_attr(
    structured_response: Any,
    field_name: str,
    default: T,
    *,
    treat_falsy_as_default: bool = False,
) -> T:
    """Return a structured response attribute or a typed default.

    Gemini can omit fields entirely or explicitly set them to ``None``. We coerce
    ``None`` back to the supplied ``default`` so callers always receive the
    expected type (``str``/``list``/``dict``). ``getattr`` handles the case where
    the attribute does not exist; we only need to guard the ``None`` sentinel.
    """

    value = getattr(structured_response, field_name, default)
    if value is None or (treat_falsy_as_default and not value):
        return default
    return value


def extract_structured_fields(gemini_response_obj: Any) -> Dict[str, Any]:
    """Extract structured fields from a GeminiResponse-like object."""

    structured_fields: Dict[str, Any] = {}

    sr = getattr(gemini_response_obj, "structured_response", None)
    if sr:
        structured_fields = {
            constants.FIELD_SESSION_HEADER: _get_structured_attr(
                sr, constants.FIELD_SESSION_HEADER, ""
            ),
            constants.FIELD_PLANNING_BLOCK: _get_structured_attr(
                sr, constants.FIELD_PLANNING_BLOCK, ""
            ),
            constants.FIELD_DICE_ROLLS: _get_structured_attr(
                sr, constants.FIELD_DICE_ROLLS, []
            ),
            # FIELD_RESOURCES is consumed downstream by Firestore writes which
            # expect a mapping. Returning ``{}`` keeps backwards compatibility
            # with earlier schemas that defaulted to a dict-like payload.
            constants.FIELD_RESOURCES: _get_structured_attr(
                sr, constants.FIELD_RESOURCES, {}, treat_falsy_as_default=True
            ),
            constants.FIELD_DEBUG_INFO: _get_structured_attr(
                sr, constants.FIELD_DEBUG_INFO, {}
            ),
            constants.FIELD_GOD_MODE_RESPONSE: _get_structured_attr(
                sr, constants.FIELD_GOD_MODE_RESPONSE, ""
            ),
        }

    return structured_fields
