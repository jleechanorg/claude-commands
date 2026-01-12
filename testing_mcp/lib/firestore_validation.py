"""Firestore validation utilities for MCP tests.

This module provides utilities to validate that data persisted to Firestore
matches what was returned by the API, particularly for audit trail fields
like action_resolution.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add mvp_site to path for Firestore access
if Path(__file__).parent.parent.parent not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mvp_site.clock_skew_credentials import apply_clock_skew_patch
from mvp_site.firestore_service import get_db


def validate_action_resolution_in_firestore(
    user_id: str,
    campaign_id: str,
    *,
    limit: int = 5,
    require_audit_flags: bool = True,
) -> dict[str, Any]:
    """Validate that action_resolution is present in Firestore story entries.
    
    This function checks the latest Gemini story entries in Firestore to ensure
    that action_resolution audit trail data was properly persisted.
    
    Args:
        user_id: User ID for the campaign
        campaign_id: Campaign ID to check
        limit: Number of recent entries to check (default: 5)
        require_audit_flags: Whether to require audit_flags field (default: True)
        
    Returns:
        Dict with validation results:
        {
            "passed": bool,
            "errors": list[str],
            "warnings": list[str],
            "entries_checked": int,
            "entries_with_action_resolution": int,
            "entries_details": list[dict],  # Per-entry validation details
        }
    """
    errors: list[str] = []
    warnings: list[str] = []
    entries_details: list[dict[str, Any]] = []
    
    # Initialize Firestore connection
    # Set up environment for Firestore access
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        cred_path = os.path.expanduser("~/serviceAccountKey.json")
        if os.path.exists(cred_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
        else:
            errors.append(
                "Cannot access Firestore: GOOGLE_APPLICATION_CREDENTIALS not set "
                "and ~/serviceAccountKey.json not found"
            )
            return {
                "passed": False,
                "errors": errors,
                "warnings": warnings,
                "entries_checked": 0,
                "entries_with_action_resolution": 0,
                "entries_details": entries_details,
            }
    
    if not os.environ.get("WORLDAI_DEV_MODE"):
        os.environ["WORLDAI_DEV_MODE"] = "true"
    
    # Apply clock skew patch before importing Firebase
    apply_clock_skew_patch()
    
    try:
        db = get_db()
    except Exception as e:
        errors.append(f"Failed to connect to Firestore: {e}")
        return {
            "passed": False,
            "errors": errors,
            "warnings": warnings,
            "entries_checked": 0,
            "entries_with_action_resolution": 0,
            "entries_details": entries_details,
        }
    
    # Query story entries
    try:
        story_ref = (
            db.collection("users")
            .document(user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("story")
        )
        
        # Get latest Gemini entries (actor == 'gemini')
        # Add small delay for Firestore eventual consistency (writes may take a moment)
        import time
        time.sleep(0.5)  # Small delay to allow Firestore write to propagate
        
        entries = story_ref.where("actor", "==", "gemini").limit(limit).stream()
        
        entries_checked = 0
        entries_with_ar = 0
        
        for entry in entries:
            entries_checked += 1
            entry_data = entry.to_dict()
            entry_id = entry.id
            timestamp = entry_data.get("timestamp")
            
            # Check for action_resolution at top level
            has_action_resolution = "action_resolution" in entry_data
            action_resolution = entry_data.get("action_resolution")
            
            # Also check in unified_response if present
            unified_response = entry_data.get("unified_response", {})
            if not has_action_resolution and isinstance(unified_response, dict):
                has_action_resolution = "action_resolution" in unified_response
                if has_action_resolution:
                    action_resolution = unified_response.get("action_resolution")
            
            entry_detail = {
                "entry_id": entry_id,
                "timestamp": str(timestamp) if timestamp else None,
                "has_action_resolution": has_action_resolution,
                "action_resolution": action_resolution,
                "errors": [],
                "warnings": [],
            }
            
            if has_action_resolution and action_resolution:
                entries_with_ar += 1
                
                # Validate action_resolution structure
                if not isinstance(action_resolution, dict):
                    entry_detail["errors"].append(
                        f"action_resolution is not a dict (got {type(action_resolution).__name__})"
                    )
                else:
                    # Check for required fields
                    if require_audit_flags:
                        if "audit_flags" not in action_resolution:
                            entry_detail["errors"].append(
                                "action_resolution missing required field: audit_flags"
                            )
                        elif not isinstance(action_resolution.get("audit_flags"), list):
                            entry_detail["errors"].append(
                                "action_resolution.audit_flags must be a list"
                            )
                    
                    # Check for reinterpreted field (should be present for outcome declarations)
                    if "reinterpreted" not in action_resolution:
                        entry_detail["warnings"].append(
                            "action_resolution missing field: reinterpreted (recommended for audit trail)"
                        )
                    
                    # Log what fields are present
                    ar_keys = list(action_resolution.keys())
                    entry_detail["action_resolution_keys"] = ar_keys
            else:
                entry_detail["errors"].append(
                    "Missing action_resolution field in Firestore story entry. "
                    "Audit trail data was not persisted."
                )
            
            entries_details.append(entry_detail)
        
        # Aggregate errors and warnings
        for detail in entries_details:
            errors.extend(detail["errors"])
            warnings.extend(detail["warnings"])
        
        # Determine if validation passed
        passed = len(errors) == 0
        
        # Add summary warnings
        if entries_checked == 0:
            warnings.append("No Gemini story entries found in Firestore")
        elif entries_with_ar == 0:
            errors.append(
                f"None of {entries_checked} Gemini entries contain action_resolution. "
                "Audit trail data is not being persisted to Firestore."
            )
        elif entries_with_ar < entries_checked:
            warnings.append(
                f"Only {entries_with_ar}/{entries_checked} entries contain action_resolution. "
                "Some entries may be missing audit trail data."
            )
        
        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "entries_checked": entries_checked,
            "entries_with_action_resolution": entries_with_ar,
            "entries_details": entries_details,
        }
        
    except Exception as e:
        errors.append(f"Failed to query Firestore story entries: {e}")
        return {
            "passed": False,
            "errors": errors,
            "warnings": warnings,
            "entries_checked": 0,
            "entries_with_action_resolution": 0,
            "entries_details": entries_details,
        }


def validate_story_entry_fields(
    user_id: str,
    campaign_id: str,
    expected_fields: list[str],
    *,
    limit: int = 5,
    actor: str = "gemini",
) -> dict[str, Any]:
    """Validate that specific fields are present in Firestore story entries.
    
    Args:
        user_id: User ID for the campaign
        campaign_id: Campaign ID to check
        expected_fields: List of field names that should be present
        limit: Number of recent entries to check (default: 5)
        actor: Actor type to filter by (default: "gemini")
        
    Returns:
        Dict with validation results:
        {
            "passed": bool,
            "errors": list[str],
            "warnings": list[str],
            "entries_checked": int,
            "field_presence": dict[str, int],  # Count of entries with each field
        }
    """
    errors: list[str] = []
    warnings: list[str] = []
    field_presence: dict[str, int] = {field: 0 for field in expected_fields}
    
    # Initialize Firestore connection
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        cred_path = os.path.expanduser("~/serviceAccountKey.json")
        if os.path.exists(cred_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
        else:
            errors.append(
                "Cannot access Firestore: GOOGLE_APPLICATION_CREDENTIALS not set "
                "and ~/serviceAccountKey.json not found"
            )
            return {
                "passed": False,
                "errors": errors,
                "warnings": warnings,
                "entries_checked": 0,
                "field_presence": field_presence,
            }
    
    if not os.environ.get("WORLDAI_DEV_MODE"):
        os.environ["WORLDAI_DEV_MODE"] = "true"
    
    apply_clock_skew_patch()
    
    try:
        db = get_db()
    except Exception as e:
        errors.append(f"Failed to connect to Firestore: {e}")
        return {
            "passed": False,
            "errors": errors,
            "warnings": warnings,
            "entries_checked": 0,
            "field_presence": field_presence,
        }
    
    try:
        story_ref = (
            db.collection("users")
            .document(user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("story")
        )
        
        entries = story_ref.where("actor", "==", actor).limit(limit).stream()
        
        entries_checked = 0
        for entry in entries:
            entries_checked += 1
            entry_data = entry.to_dict()
            
            # Check each expected field
            for field in expected_fields:
                if field in entry_data:
                    field_presence[field] += 1
                # Also check in unified_response
                elif isinstance(entry_data.get("unified_response"), dict):
                    if field in entry_data.get("unified_response", {}):
                        field_presence[field] += 1
        
        # Check if all fields are present in at least one entry
        missing_fields = [
            field for field in expected_fields if field_presence[field] == 0
        ]
        
        if missing_fields:
            errors.append(
                f"Missing fields in Firestore: {', '.join(missing_fields)}. "
                f"Checked {entries_checked} entries."
            )
        
        if entries_checked == 0:
            warnings.append(f"No {actor} story entries found in Firestore")
        
        passed = len(errors) == 0
        
        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "entries_checked": entries_checked,
            "field_presence": field_presence,
        }
        
    except Exception as e:
        errors.append(f"Failed to query Firestore story entries: {e}")
        return {
            "passed": False,
            "errors": errors,
            "warnings": warnings,
            "entries_checked": 0,
            "field_presence": field_presence,
        }
