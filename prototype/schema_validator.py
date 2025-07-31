"""
JSON schema validation utilities for validation results.
Ensures all validation results conform to the standard format.
"""

import json
import os
from typing import Any

import jsonschema

# Try to import jsonschema if available
try:
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("Warning: jsonschema package not available. Schema validation disabled.")


class SchemaValidator:
    """Validates validation results against the standard schema."""

    def __init__(self):
        # Load schema
        schema_path = os.path.join(os.path.dirname(__file__), "validation_schema.json")
        with open(schema_path) as f:
            self.schema = json.load(f)

    def validate(self, result: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate a result against the schema.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if JSONSCHEMA_AVAILABLE:
            try:
                jsonschema.validate(instance=result, schema=self.schema)
                return True, []
            except jsonschema.exceptions.ValidationError as e:
                return False, [str(e)]
        else:
            # Fallback manual validation
            errors = self._manual_validate(result)
            return len(errors) == 0, errors

    def _manual_validate(self, result: dict[str, Any]) -> list[str]:
        """Manual validation when jsonschema is not available."""
        errors = []

        # Check required fields
        required_fields = [
            "all_entities_present",
            "entities_found",
            "entities_missing",
            "confidence",
        ]
        for field in required_fields:
            if field not in result:
                errors.append(f"Missing required field: {field}")

        # Check field types
        if "all_entities_present" in result and not isinstance(
            result["all_entities_present"], bool
        ):
            errors.append("all_entities_present must be boolean")

        if "entities_found" in result and not isinstance(
            result["entities_found"], list
        ):
            errors.append("entities_found must be a list")

        if "entities_missing" in result and not isinstance(
            result["entities_missing"], list
        ):
            errors.append("entities_missing must be a list")

        if "confidence" in result:
            conf = result["confidence"]
            if not isinstance(conf, int | float) or conf < 0 or conf > 1:
                errors.append("confidence must be a number between 0 and 1")

        return errors

    def create_valid_result(
        self,
        all_present: bool,
        found: list[str],
        missing: list[str],
        confidence: float,
        **kwargs,
    ) -> dict[str, Any]:
        """Helper to create a schema-compliant result."""
        result = {
            "all_entities_present": all_present,
            "entities_found": found,
            "entities_missing": missing,
            "confidence": confidence,
        }

        # Add optional fields
        for key in [
            "entity_references",
            "entity_states",
            "errors",
            "warnings",
            "metadata",
            "validation_details",
        ]:
            if key in kwargs:
                result[key] = kwargs[key]

        return result


# Singleton instance
_schema_validator = None


def get_schema_validator() -> SchemaValidator:
    """Get singleton schema validator instance."""
    global _schema_validator
    if _schema_validator is None:
        _schema_validator = SchemaValidator()
    return _schema_validator
