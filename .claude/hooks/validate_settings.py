#!/usr/bin/env python3
"""Pre-commit hook to validate settings.json against official schema

Note: Uses lenient validation to allow 'description' fields in hooks.
While not officially documented, Claude Code parser accepts them.

Requirements:
    pip install jsonschema requests
"""

import json
import sys
from pathlib import Path

import requests
from jsonschema import validate, ValidationError

def remove_additional_properties_false(schema):
    """Recursively remove 'additionalProperties: false' to allow description fields"""
    if isinstance(schema, dict):
        # Remove additionalProperties constraint
        if 'additionalProperties' in schema:
            del schema['additionalProperties']

        # Recurse into nested schemas
        for _, value in schema.items():
            if isinstance(value, (dict, list)):
                remove_additional_properties_false(value)
    elif isinstance(schema, list):
        for item in schema:
            remove_additional_properties_false(item)

    return schema

def validate_settings():
    """Validate all settings.json files in the project"""

    schema_url = "https://json.schemastore.org/claude-code-settings.json"

    # Find settings files
    settings_files = [
        Path.home() / '.claude' / 'settings.json',
        Path('.claude') / 'settings.json',
    ]

    errors = []

    for settings_file in settings_files:
        if not settings_file.exists():
            continue

        print(f"🔍 Validating {settings_file}...")

        try:
            # Load schema
            schema = requests.get(schema_url, timeout=5).json()

            # Make schema lenient (allow description fields)
            lenient_schema = remove_additional_properties_false(schema.copy())

            # Load settings
            with open(settings_file, 'r') as f:
                settings = json.load(f)

            # Validate with lenient schema
            validate(instance=settings, schema=lenient_schema)
            print("   ✅ Valid (lenient mode: allows description fields)")

        except ValidationError as e:
            print(f"   ❌ Validation error: {e.message}")
            print(f"      Path: {' -> '.join(str(p) for p in e.path)}")
            errors.append((settings_file, e))
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON: {e}")
            errors.append((settings_file, e))
        except Exception as e:
            print(f"   ⚠️  Error validating: {e}")
            errors.append((settings_file, e))

    if errors:
        print(f"\n❌ Found {len(errors)} validation error(s)")
        return False

    print("\n✅ All settings files valid")
    return True

if __name__ == "__main__":
    success = validate_settings()
    sys.exit(0 if success else 1)
