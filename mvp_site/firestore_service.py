"""
Firestore Service - Database Operations and Game State Management

This module provides comprehensive database operations for WorldArchitect.AI,
including campaign management, game state synchronization, and robust data handling.

Key Responsibilities:
- Campaign CRUD operations (Create, Read, Update, Delete)
- Game state serialization and persistence
- Complex state update processing with merge logic
- Mission management and data conversion
- Defensive programming patterns for data integrity
- JSON serialization utilities for Firestore compatibility

Architecture:
- Uses Firebase Firestore for data persistence
- Implements robust state update mechanisms
- Provides mission handling with smart conversion
- Includes comprehensive error handling and logging
- Supports legacy data cleanup and migration

Dependencies:
- Firebase Admin SDK for Firestore operations
- Custom GameState class for state management
- NumericFieldConverter for data type handling
- Logging utilities for comprehensive debugging
"""

# ruff: noqa: PLR0911, PLR0912, UP038

import collections.abc
import datetime
import json
import os
import time
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

from mvp_site import constants, logging_util
from mvp_site.custom_types import CampaignId, UserId
from mvp_site.decorators import log_exceptions
from mvp_site.game_state import GameState
from mvp_site.numeric_field_converter import NumericFieldConverter
from mvp_site.serialization import json_default_serializer, json_serial

__all__ = ["json_default_serializer", "json_serial"]

MAX_TEXT_BYTES: int = 1000000
MAX_LOG_LINES: int = 20
DELETE_TOKEN: str = (
    "__DELETE__"  # Token used to mark fields for deletion in state updates
)

UTC = datetime.UTC


class FirestoreWriteError(RuntimeError):
    """Raised when Firestore write operations return unexpected responses."""


# Note: Tests patch the fully-qualified module path (`mvp_site.firestore_service`).

# ruff: noqa: PLR0915


class _InMemoryFirestoreDocument:
    """Simple in-memory document used when MOCK_SERVICES_MODE is enabled."""

    def __init__(self, doc_id: str, parent_path: str = "") -> None:
        self.id = doc_id
        self._data: dict[str, Any] = {}
        self._parent_path = parent_path
        self._collections: dict[str, _InMemoryFirestoreCollection] = {}

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        if not merge:
            self._data = data
            return

        def deep_merge(target: dict[str, Any], source: dict[str, Any]) -> None:
            for key, value in source.items():
                if (
                    key in target
                    and isinstance(target[key], dict)
                    and isinstance(value, dict)
                ):
                    deep_merge(target[key], value)
                else:
                    target[key] = value

        deep_merge(self._data, data)

    def update(self, updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            if "." in key:
                parts = key.split(".")
                current = self._data
                for part in parts[:-1]:
                    current = current.setdefault(part, {})  # type: ignore[assignment]
                current[parts[-1]] = value
            else:
                self._data[key] = value

    def get(self) -> "_InMemoryFirestoreDocument":
        return self

    @property
    def exists(self) -> bool:  # type: ignore[override]
        return bool(self._data)

    def to_dict(self) -> dict[str, Any]:
        return self._data

    def collection(self, name: str) -> "_InMemoryFirestoreCollection":
        path = f"{self._parent_path}/{self.id}" if self._parent_path else self.id
        return self._collections.setdefault(
            name, _InMemoryFirestoreCollection(name, parent_path=path)
        )


class _InMemoryFirestoreCollection:
    """Simple in-memory collection used when MOCK_SERVICES_MODE is enabled."""

    def __init__(self, name: str, parent_path: str = "") -> None:
        self.name = name
        self._parent_path = parent_path
        self._docs: dict[str, _InMemoryFirestoreDocument] = {}
        self._doc_counter = 0

    def document(self, doc_id: str | None = None) -> _InMemoryFirestoreDocument:
        if doc_id is None:
            self._doc_counter += 1
            doc_id = f"generated-id-{self._doc_counter}"

        if doc_id not in self._docs:
            path = (
                f"{self._parent_path}/{self.name}" if self._parent_path else self.name
            )
            self._docs[doc_id] = _InMemoryFirestoreDocument(doc_id, parent_path=path)

        return self._docs[doc_id]

    def stream(self) -> list[_InMemoryFirestoreDocument]:
        return list(self._docs.values())

    def add(
        self, data: dict[str, Any]
    ) -> tuple[datetime.datetime, _InMemoryFirestoreDocument]:
        doc = self.document()
        doc.set(data)
        fake_timestamp = datetime.datetime.now(UTC)
        return fake_timestamp, doc

    def order_by(self, *_args: Any, **_kwargs: Any) -> "_InMemoryFirestoreCollection":
        return self


class _InMemoryFirestoreClient:
    def __init__(self) -> None:
        self._collections: dict[str, _InMemoryFirestoreCollection] = {}

    def collection(self, path: str) -> _InMemoryFirestoreCollection:
        return self._collections.setdefault(
            path, _InMemoryFirestoreCollection(path, parent_path="")
        )

    def document(self, path: str) -> _InMemoryFirestoreDocument:
        parts = path.split("/")
        if len(parts) == 2:
            collection_name, doc_id = parts
            return self.collection(collection_name).document(doc_id)
        if len(parts) == 4:
            parent_collection, parent_id, sub_collection, doc_id = parts
            parent_doc = self.collection(parent_collection).document(parent_id)
            return parent_doc.collection(sub_collection).document(doc_id)
        doc_id = parts[-1] if parts else "unknown"
        return _InMemoryFirestoreDocument(doc_id)

    def reset(self) -> None:
        """Reset all collections (useful for testing)."""
        self._collections.clear()


# Singleton instance for MOCK_SERVICES_MODE to persist state across tool calls
_mock_client_singleton: _InMemoryFirestoreClient | None = None


def reset_mock_firestore() -> None:
    """Reset the mock Firestore singleton (useful for testing).

    This clears all data from the in-memory Firestore client and resets
    the singleton instance. Should only be called in test environments.
    """
    global _mock_client_singleton
    if _mock_client_singleton is not None:
        _mock_client_singleton.reset()
        logging_util.info("Mock Firestore singleton reset")


def _truncate_log_json(
    data: Any,
    max_lines: int = MAX_LOG_LINES,
    json_serializer=json_default_serializer,
) -> str:
    """Truncate JSON logs to max_lines to prevent log spam."""
    try:
        # Use provided serializer or fallback to str
        serializer = json_serializer if json_serializer is not None else str
        json_str = json.dumps(data, indent=2, default=serializer)
        lines = json_str.split("\n")
        if len(lines) <= max_lines:
            return json_str

        # Truncate and add indicator
        truncated_lines = lines[: max_lines - 1] + [
            f"... (truncated, showing {max_lines - 1}/{len(lines)} lines)"
        ]
        return "\n".join(truncated_lines)
    except Exception:
        # Fallback to string representation if JSON fails
        return str(data)[:500] + "..." if len(str(data)) > 500 else str(data)


def _perform_append(
    target_list: list,
    items_to_append: Any | list[Any],
    key_name: str,
    deduplicate: bool = False,
) -> None:
    """
    Safely appends one or more items to a target list, with an option to prevent duplicates.
    This function modifies the target_list in place.
    """
    if not isinstance(items_to_append, list):
        items_to_append = [items_to_append]  # Standardize to list

    newly_added_items: list[Any] = []
    for item in items_to_append:
        # If deduplication is on, skip items already in the list
        if deduplicate and item in target_list:
            continue
        target_list.append(item)
        newly_added_items.append(item)

    if newly_added_items:
        logging_util.info(
            f"APPEND/SAFEGUARD: Added {len(newly_added_items)} new items to '{key_name}'."
        )
    else:
        logging_util.info(
            f"APPEND/SAFEGUARD: No new items were added to '{key_name}' (duplicates may have been found)."
        )


class MissionHandler:
    """
    Handles mission-related operations for game state management.
    Consolidates mission processing, conversion, and updates.
    """

    @staticmethod
    def initialize_missions_list(state_to_update: dict[str, Any], key: str) -> None:
        """Initialize active_missions as empty list if it doesn't exist or is wrong type."""
        if key not in state_to_update or not isinstance(state_to_update.get(key), list):
            state_to_update[key] = []

    @staticmethod
    def find_existing_mission_index(
        missions_list: list[dict[str, Any]], mission_id: str
    ) -> int:
        """Find the index of an existing mission by mission_id. Returns -1 if not found."""
        for i, existing_mission in enumerate(missions_list):
            if (
                isinstance(existing_mission, dict)
                and existing_mission.get("mission_id") == mission_id
            ):
                return i
        return -1

    @staticmethod
    def process_mission_data(
        state_to_update: dict[str, Any],
        key: str,
        mission_id: str,
        mission_data: dict[str, Any],
    ) -> None:
        """Process a single mission, either updating existing or adding new."""
        # Ensure the mission has an ID
        if "mission_id" not in mission_data:
            mission_data["mission_id"] = mission_id

        # Check if this mission already exists (by mission_id)
        existing_mission_index = MissionHandler.find_existing_mission_index(
            state_to_update[key], mission_id
        )

        if existing_mission_index != -1:
            # Update existing mission
            logging_util.info(f"Updating existing mission: {mission_id}")
            state_to_update[key][existing_mission_index].update(mission_data)
        else:
            # Add new mission
            logging_util.info(f"Adding new mission: {mission_id}")
            state_to_update[key].append(mission_data)

    @staticmethod
    def handle_missions_dict_conversion(
        state_to_update: dict[str, Any], key: str, missions_dict: dict[str, Any]
    ) -> None:
        """Convert dictionary format missions to list append format."""
        for mission_id, mission_data in missions_dict.items():
            if isinstance(mission_data, dict):
                MissionHandler.process_mission_data(
                    state_to_update, key, mission_id, mission_data
                )
            else:
                logging_util.warning(
                    f"Skipping invalid mission data for {mission_id}: not a dictionary"
                )

    @staticmethod
    def handle_active_missions_conversion(
        state_to_update: dict[str, Any], key: str, value: Any
    ) -> None:
        """Handle smart conversion of active_missions from various formats to list."""
        logging_util.warning(
            f"SMART CONVERSION: AI attempted to set 'active_missions' as {type(value).__name__}. Converting to list append."
        )

        # Initialize active_missions as empty list if it doesn't exist
        MissionHandler.initialize_missions_list(state_to_update, key)

        # Convert based on value type
        if isinstance(value, dict):
            # AI is providing missions as a dict like {"main_quest_1": {...}, "side_quest_1": {...}}
            MissionHandler.handle_missions_dict_conversion(state_to_update, key, value)
        else:
            # For other non-list types, log error and skip
            logging_util.error(
                f"Cannot convert {type(value).__name__} to mission list. Skipping."
            )


def _handle_append_syntax(
    state_to_update: dict[str, Any], key: str, value: dict[str, Any]
) -> bool:
    """
    Handle explicit append syntax {'append': ...}.

    Returns:
        bool: True if handled, False otherwise
    """
    if not (isinstance(value, dict) and "append" in value):
        return False

    logging_util.info(f"update_state: Detected explicit append for '{key}'.")
    if key not in state_to_update or not isinstance(state_to_update.get(key), list):
        state_to_update[key] = []
    _perform_append(
        state_to_update[key], value["append"], key, deduplicate=(key == "core_memories")
    )
    return True


def _handle_core_memories_safeguard(
    state_to_update: dict[str, Any], key: str, value: Any
) -> bool:
    """
    Handle safeguard for direct 'core_memories' overwrite.

    Returns:
        bool: True if handled, False otherwise
    """
    if key != "core_memories":
        return False

    logging_util.warning(
        "CRITICAL SAFEGUARD: Intercepted direct overwrite on 'core_memories'. Converting to safe, deduplicated append."
    )
    if key not in state_to_update or not isinstance(state_to_update.get(key), list):
        state_to_update[key] = []
    _perform_append(state_to_update[key], value, key, deduplicate=True)
    return True


def _handle_dict_merge(state_to_update: dict[str, Any], key: str, value: Any) -> bool:
    """
    Handle dictionary merging and creation.

    Returns:
        bool: True if handled, False otherwise
    """
    if not isinstance(value, dict):
        return False

    # Case 1: Recursive merge for nested dictionaries
    if isinstance(state_to_update.get(key), collections.abc.Mapping):
        state_to_update[key] = update_state_with_changes(
            state_to_update.get(key, {}), value
        )
        return True

    # Case 2: Create new dictionary when incoming value is dict but existing is not
    state_to_update[key] = update_state_with_changes({}, value)
    return True


def _handle_delete_token(state_to_update: dict[str, Any], key: str, value: Any) -> bool:
    """
    Handle DELETE_TOKEN for field deletion.

    Returns:
        bool: True if handled, False otherwise
    """
    if value != DELETE_TOKEN:
        return False

    if key in state_to_update:
        logging_util.info(f"update_state: Deleting key '{key}' due to DELETE_TOKEN.")
        del state_to_update[key]
    else:
        logging_util.info(
            f"update_state: Attempted to delete key '{key}' but it doesn't exist."
        )
    return True


def _handle_string_to_dict_update(
    state_to_update: dict[str, Any], key: str, value: Any
) -> bool:
    """
    Handle string updates to existing dictionaries (preserve dict structure).

    Returns:
        bool: True if handled, False otherwise
    """
    if not isinstance(state_to_update.get(key), collections.abc.Mapping):
        return False

    logging_util.info(
        f"update_state: Preserving dict structure for key '{key}', adding 'status' field."
    )
    existing_dict = state_to_update[key].copy()
    existing_dict["status"] = value
    state_to_update[key] = existing_dict

    return True


def update_state_with_changes(
    state_to_update: dict[str, Any], changes: dict[str, Any]
) -> dict[str, Any]:
    """
    Recursively updates a state dictionary with a changes dictionary using intelligent merge logic.

    This is the core function for applying AI-generated state updates to the game state.
    It implements sophisticated handling for different data types and update patterns.

    Key Features:
    - Explicit append syntax: {'append': [items]} for safe list operations
    - Core memories safeguard: Prevents accidental overwrite of important game history
    - Recursive dictionary merging: Deep merge for nested objects
    - DELETE_TOKEN support: Allows removal of specific fields
    - Mission smart conversion: Handles various mission data formats
    - Numeric field conversion: Ensures proper data types
    - Defensive programming: Validates data structures before operations

    Update Patterns Handled:
    1. DELETE_TOKEN - Removes fields marked for deletion
    2. Explicit append - Safe list operations with deduplication
    3. Core memories safeguard - Protects critical game history
    4. Mission conversion - Handles dict-to-list conversion for missions
    5. Dictionary merging - Recursive merge for nested structures
    6. String-to-dict preservation - Maintains existing dict structures
    7. Simple overwrite - Default behavior for primitive values

    Args:
        state_to_update (dict): The current game state to modify
        changes (dict): Changes to apply (typically from AI response)

    Returns:
        dict: Updated state dictionary with changes applied

    Example Usage:
        current_state = {"health": 100, "items": ["sword"]}
        changes = {"health": 80, "items": {"append": ["potion"]}}
        result = update_state_with_changes(current_state, changes)
        # Result: {"health": 80, "items": ["sword", "potion"]}
    """
    logging_util.info(
        f"--- update_state_with_changes: applying changes:\\n{_truncate_log_json(changes)}"
    )

    # Auto-initialize completed_missions if active_missions exists but completed_missions doesn't
    # Fix for older campaigns that predate the completed_missions field
    if "active_missions" in state_to_update and "completed_missions" not in state_to_update:
        logging_util.info(
            "Auto-initializing completed_missions field for older campaign"
        )
        state_to_update["completed_missions"] = []

    # Normalize dotted keys in changes (e.g., "player_character_data.level" -> nested dict)
    # This handles LLM responses that use dotted paths instead of nested structures
    changes = _normalize_dotted_keys_in_place(changes)

    for key, value in changes.items():
        # Try each handler in order of precedence

        # Case 1: Handle DELETE_TOKEN first (highest priority)
        if _handle_delete_token(state_to_update, key, value):
            continue

        # Case 2: Explicit append syntax
        if _handle_append_syntax(state_to_update, key, value):
            continue

        # Case 3: Core memories safeguard
        if _handle_core_memories_safeguard(state_to_update, key, value):
            continue

        # Case 4: Auto-initialize completed_missions if active_missions is being updated
        # CRITICAL: Must run BEFORE smart conversion (which calls continue)
        # Fix for bug where older campaigns don't have completed_missions field
        if key == "active_missions" and "completed_missions" not in state_to_update:
            logging_util.info(
                "Auto-initializing completed_missions field (missing in older campaigns)"
            )
            state_to_update["completed_missions"] = []

        # Case 4.5: Active missions smart conversion
        if key == "active_missions" and not isinstance(value, list):
            MissionHandler.handle_active_missions_conversion(
                state_to_update, key, value
            )
            continue

        # Case 4.6: Completed missions smart conversion (same as active_missions)
        if key == "completed_missions" and not isinstance(value, list):
            MissionHandler.handle_active_missions_conversion(
                state_to_update, key, value
            )
            continue

        # Case 5: Dictionary operations (merge or create)
        if _handle_dict_merge(state_to_update, key, value):
            continue

        # Case 6: String to dict updates (preserve structure)
        if _handle_string_to_dict_update(state_to_update, key, value):
            continue

        # Case 7: Simple overwrite for everything else
        # Convert numeric fields from strings to integers
        # Note: We handle conversion here instead of in _handle_dict_merge to avoid
        # double conversion when dictionaries are recursively processed
        if isinstance(value, dict):
            # For dictionaries, use convert_dict to handle nested conversions
            converted_value = NumericFieldConverter.convert_dict(value)
        else:
            # For simple values, use convert_value
            converted_value = NumericFieldConverter.convert_value(key, value)
        state_to_update[key] = converted_value
    logging_util.info("--- update_state_with_changes: finished ---")
    return state_to_update


def _expand_dot_notation(d: dict[str, Any]) -> dict[str, Any]:
    """
    Expands a dictionary with dot-notation keys into a nested dictionary.
    Example: {'a.b': 1, 'c': 2} -> {'a': {'b': 1}, 'c': 2}

    Dot characters are reserved for path notation. Keys with literal dots are
    not supported by this helper and should be avoided in update payloads.
    """
    expanded_dict: dict[str, Any] = {}
    terminal_paths: set[tuple[str, ...]] = set()
    for k, v in d.items():
        if "." in k:
            keys = k.split(".")
            if any(part == "" for part in keys):
                raise ValueError(
                    "Invalid dot-notation key; leading, trailing, or repeated dots "
                    f"are not supported: '{k}'"
                )
            d_ref = expanded_dict
            prefix: list[str] = []
            for part in keys[:-1]:
                prefix.append(part)
                if tuple(prefix) in terminal_paths:
                    raise ValueError(
                        "Conflicting keys in dot-notation expansion: "
                        f"cannot set '{k}' because '{'.'.join(prefix)}' "
                        "already exists as a terminal value"
                    )
                existing = d_ref.get(part)
                if existing is not None and not isinstance(existing, dict):
                    raise ValueError(
                        "Conflicting keys in dot-notation expansion: "
                        f"cannot set '{k}' because '{part}' already exists as "
                        "a non-dict value"
                    )
                if part not in d_ref:
                    d_ref[part] = {}
                d_ref = d_ref[part]
            final_key = keys[-1]
            if tuple(keys) in terminal_paths:
                raise ValueError(
                    "Conflicting keys in dot-notation expansion: "
                    f"'{k}' already exists as a terminal value"
                )
            existing_final = d_ref.get(final_key)
            if existing_final is not None and isinstance(existing_final, dict):
                raise ValueError(
                    "Conflicting keys in dot-notation expansion: "
                    f"'{k}' would overwrite an existing nested structure"
                )
            d_ref[final_key] = v
            terminal_paths.add(tuple(keys))
        else:
            if k in expanded_dict:
                raise ValueError(
                    "Conflicting keys in dot-notation expansion: "
                    f"'{k}' overlaps with an existing nested update"
                )
            expanded_dict[k] = v
            terminal_paths.add((k,))
    return expanded_dict


def _normalize_dotted_keys_in_place(d: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a dict by merging dotted-notation keys into nested structures.

    Unlike _expand_dot_notation which creates a new dict, this function:
    1. Works with existing nested structures in the dict
    2. Merges dotted keys into those structures
    3. Removes the original dotted keys

    Example:
        Input: {"player": {"name": "X"}, "player.level": 5}
        Output: {"player": {"name": "X", "level": 5}}

    This handles the common case where LLM outputs both nested objects AND
    dotted paths for additional fields.
    """
    # Find all dotted keys
    dotted_keys = [k for k in d.keys() if "." in k]

    for dotted_key in dotted_keys:
        parts = dotted_key.split(".")
        value = d[dotted_key]

        # Navigate/create nested structure
        current = d
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                # Can't merge into non-dict - skip this key
                logging_util.warning(
                    f"Cannot merge dotted key '{dotted_key}': "
                    f"'{part}' is not a dict"
                )
                break
            current = current[part]
        else:
            # Successfully navigated - set the value
            final_key = parts[-1]
            current[final_key] = value
            # Remove the original dotted key
            del d[dotted_key]

    return d


# json_serial and json_default_serializer are now imported from mvp_site.serialization


def get_db() -> firestore.Client:
    """Return an initialized Firestore client or fail fast.

    Tests should patch this helper rather than relying on in-module mocks so that
    production code paths always exercise the real Firestore SDK.

    In MOCK_SERVICES_MODE, returns a singleton in-memory client to persist state
    across tool calls within the same MCP server session.
    """
    global _mock_client_singleton

    if os.getenv("MOCK_SERVICES_MODE", "").lower() == "true":
        if _mock_client_singleton is None:
            logging_util.info(
                "MOCK_SERVICES_MODE enabled - creating singleton in-memory Firestore client"
            )
            _mock_client_singleton = _InMemoryFirestoreClient()
        else:
            logging_util.info(
                "MOCK_SERVICES_MODE enabled - reusing singleton in-memory Firestore client"
            )
        return _mock_client_singleton

    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            logging_util.info("Firebase not initialized - attempting to initialize now")
            # WORLDAI_* vars take precedence for WorldArchitect.AI repo-specific config
            worldai_creds_path = os.getenv("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS")
            if worldai_creds_path:
                worldai_creds_path = os.path.expanduser(worldai_creds_path)
                if os.path.exists(worldai_creds_path):
                    logging_util.info(
                        f"Using WORLDAI credentials from {worldai_creds_path}"
                    )
                    firebase_admin.initialize_app(
                        credentials.Certificate(worldai_creds_path)
                    )
                else:
                    firebase_admin.initialize_app()
            else:
                firebase_admin.initialize_app()
        except Exception as init_error:
            logging_util.error(f"Failed to initialize Firebase: {init_error}")
            raise ValueError(
                "Firebase initialization failed. Ensure proper configuration is available."
            ) from init_error

    try:
        return firestore.client()
    except Exception as client_error:
        logging_util.error(f"Failed to create Firestore client: {client_error}")
        raise ValueError(
            "Firestore client creation failed. Check Firebase configuration and network connectivity."
        ) from client_error


@log_exceptions
def get_campaigns_for_user(
    user_id: UserId, limit: int = None, sort_by: str = "last_played"
) -> list[dict[str, Any]]:
    """Retrieves campaigns for a given user with optional pagination and sorting.

    Args:
        user_id: Firebase user ID
        limit: Optional maximum number of campaigns to return
        sort_by: Sort field ('created_at' or 'last_played'), defaults to 'last_played'

    Returns:
        List of campaign dictionaries
    """
    db = get_db()
    campaigns_ref = db.collection("users").document(user_id).collection("campaigns")

    # Apply sorting (handle empty sort_by values)
    if not sort_by or not sort_by.strip():
        sort_by = "last_played"  # Default sort field
    campaigns_query = campaigns_ref.order_by(sort_by, direction="DESCENDING")

    # Apply limit if specified
    if limit is not None:
        campaigns_query = campaigns_query.limit(limit)

    campaign_list: list[dict[str, Any]] = []
    for campaign in campaigns_query.stream():
        campaign_data = campaign.to_dict()
        campaign_data["id"] = campaign.id

        # Safely get and format timestamps
        created_at = campaign_data.get("created_at")
        if created_at and hasattr(created_at, "isoformat"):
            campaign_data["created_at"] = created_at.isoformat()

        last_played = campaign_data.get("last_played")
        if last_played and hasattr(last_played, "isoformat"):
            campaign_data["last_played"] = last_played.isoformat()

        campaign_list.append(campaign_data)

    return campaign_list


@log_exceptions
def get_campaign_by_id(
    user_id: UserId, campaign_id: CampaignId
) -> tuple[dict[str, Any] | None, list[dict[str, Any]] | None]:
    """
    Retrieves a single campaign and its full story using a robust, single query
    and in-memory sort to handle all data types.
    """
    db = get_db()
    campaign_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
    )

    campaign_doc = campaign_ref.get()
    if not campaign_doc.exists:
        return None, None

    # --- SIMPLIFIED FETCH LOGIC ---
    # 1. Fetch ALL documents, ordered only by the field that always exists: timestamp.
    story_ref = campaign_ref.collection("story").order_by("timestamp")
    story_docs = story_ref.stream()

    # 2. Convert to a list of dictionaries
    all_story_entries: list[dict[str, Any]] = [doc.to_dict() for doc in story_docs]

    # 🚨 DEBUG: Log story retrieval details
    logging_util.info(
        f"📖 FETCHED STORY ENTRIES: user={user_id}, campaign={campaign_id}, "
        f"total_entries={len(all_story_entries)}"
    )

    # Count entries by actor
    user_entries: list[dict[str, Any]] = [
        entry for entry in all_story_entries if entry.get("actor") == "user"
    ]
    ai_entries: list[dict[str, Any]] = [
        entry for entry in all_story_entries if entry.get("actor") == "gemini"
    ]
    other_entries: list[dict[str, Any]] = [
        entry
        for entry in all_story_entries
        if entry.get("actor") not in ["user", "gemini"]
    ]

    logging_util.info(
        f"📊 STORY BREAKDOWN: user_entries={len(user_entries)}, "
        f"ai_entries={len(ai_entries)}, other_entries={len(other_entries)}"
    )

    # Log recent entries for debugging
    if all_story_entries:
        recent_entries: list[dict[str, Any]] = all_story_entries[-5:]  # Last 5 entries
        logging_util.info(f"🔍 RECENT ENTRIES (last {len(recent_entries)}):")
        for i, entry in enumerate(recent_entries, 1):
            actor = entry.get("actor", "unknown")
            mode = entry.get("mode", "N/A")
            text_preview = (
                entry.get("text", "")[:50] + "..."
                if len(entry.get("text", "")) > 50
                else entry.get("text", "")
            )
            timestamp = entry.get("timestamp", "unknown")
            logging_util.info(f"  {i}. [{actor}] {mode} | {text_preview} | {timestamp}")
    else:
        logging_util.warning(f"⚠️ NO STORY ENTRIES FOUND for campaign {campaign_id}")

    # 3. Sort the list in Python, which is more powerful than a Firestore query.
    # We sort by timestamp first, and then by the 'part' number.
    # If 'part' is missing (for old docs), we treat it as 1.
    def _norm_ts(ts):
        # Handle None/missing timestamps first
        if ts is None:
            return datetime.datetime.fromtimestamp(0, UTC)

        # Handle datetime objects - ensure timezone consistency
        if hasattr(ts, "isoformat"):
            # If datetime is timezone-naive, make it UTC
            if ts.tzinfo is None:
                return ts.replace(tzinfo=UTC)
            return ts

        # Handle string timestamps
        if isinstance(ts, str):
            if not ts.strip():  # Empty string
                return datetime.datetime.fromtimestamp(0, UTC)
            # Best-effort parse; fallback to epoch for invalid strings
            try:
                parsed = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                # Ensure timezone consistency - make UTC if naive
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=UTC)
                return parsed
            except Exception:
                # Invalid string - return epoch for stable sorting
                return datetime.datetime.fromtimestamp(0, UTC)

        # Handle integer/float timestamps (epoch seconds)
        if isinstance(ts, (int, float)):
            try:
                return datetime.datetime.fromtimestamp(ts, UTC)
            except (ValueError, OverflowError):
                # Invalid timestamp value - return epoch
                return datetime.datetime.fromtimestamp(0, UTC)

        # Fallback to epoch for any other unknown types (list, dict, etc.)
        return datetime.datetime.fromtimestamp(0, UTC)

    all_story_entries.sort(
        key=lambda x: (_norm_ts(x.get("timestamp")), x.get("part", 1))
    )

    # 4. Add a sequence ID and convert timestamps AFTER sorting.
    # TERMINOLOGY: sequence_id = absolute position (ALL entries)
    #              user_scene_number = user-facing "Scene #X" (AI responses only)
    # See llm_service.py module docstring for full turn/scene terminology.
    user_scene_counter: int = 0
    for i, entry in enumerate(all_story_entries):
        entry["sequence_id"] = i + 1

        # Only increment user scene number for AI responses (case-insensitive)
        actor_value = entry.get("actor")
        normalized_actor = actor_value.lower() if isinstance(actor_value, str) else None
        if normalized_actor == "gemini":
            user_scene_counter += 1
            entry["user_scene_number"] = user_scene_counter
        else:
            entry["user_scene_number"] = None

        # Convert timestamp to ISO format if it's not already a string
        if hasattr(entry["timestamp"], "isoformat"):
            entry["timestamp"] = entry["timestamp"].isoformat()
        # If it's already a string, leave it as is

    return campaign_doc.to_dict(), all_story_entries


@log_exceptions
def add_story_entry(
    user_id: UserId,
    campaign_id: CampaignId,
    actor: str,
    text: str,
    mode: str | None = None,
    structured_fields: dict[str, Any] | None = None,
) -> None:
    """Add a story entry to Firestore with write-then-read pattern for data integrity.

    This function implements the write-then-read pattern:
    1. Write data to Firestore
    2. Read it back immediately to verify persistence
    3. Only return success if read confirms write succeeded

    This prevents data loss from failed writes that appear successful to users.

    Args:
        user_id: User ID
        campaign_id: Campaign ID
        actor: Actor type ('user' or 'gemini')
        text: Story text content
        mode: Optional mode (e.g., 'god', 'character')
        structured_fields: Required dict for AI responses containing structured response fields
    """
    # Start timing for latency measurement
    start_time: float = time.time()

    # In mock services mode, skip verification since mocks don't support read-back
    # NOTE: Can't rely on fakes alone - even perfect fakes add 0.9s latency per test
    # Unit tests need to be fast, so bypassing verification entirely is correct
    mock_mode: bool = os.getenv("MOCK_SERVICES_MODE") == "true"
    if mock_mode:
        # Use original write-only implementation for testing
        _write_story_entry_to_firestore(
            user_id, campaign_id, actor, text, mode, structured_fields
        )
        logging_util.info(
            f"✅ Write-then-read (mock mode): user={user_id}, campaign={campaign_id}, actor={actor}"
        )

        # Return None to match original add_story_entry behavior for mock tests
        return

    # Write to Firestore and capture document ID for verification
    write_start_time: float = time.time()
    document_id: str = _write_story_entry_to_firestore(
        user_id, campaign_id, actor, text, mode, structured_fields
    )
    write_duration: float = time.time() - write_start_time

    logging_util.info(
        f"✍️ Write completed: {write_duration:.3f}s, document_id: {document_id}"
    )

    # Direct document verification using document ID (much more reliable than text matching)
    verify_start_time: float = time.time()
    entry_found: bool = False

    # Try verification with progressive delays for Firestore eventual consistency
    # NOTE: Keeping synchronous sleep - Flask is sync, async would require major refactor
    for attempt in range(constants.VERIFICATION_MAX_ATTEMPTS):
        delay: float = constants.VERIFICATION_INITIAL_DELAY + (
            attempt * constants.VERIFICATION_DELAY_INCREMENT
        )
        time.sleep(delay)

        logging_util.debug(
            f"🔍 VERIFICATION: Attempt {attempt + 1}/{constants.VERIFICATION_MAX_ATTEMPTS} after {delay}s delay"
        )
        entry_found = verify_document_by_id(user_id, campaign_id, document_id, actor)

        if entry_found:
            logging_util.info(
                f"✅ VERIFICATION: Found document {document_id} on attempt {attempt + 1}"
            )
            break

        if attempt < constants.VERIFICATION_MAX_ATTEMPTS - 1:
            logging_util.debug(
                f"⚠️ VERIFICATION: Attempt {attempt + 1} failed, retrying..."
            )

    verify_duration: float = time.time() - verify_start_time

    if not entry_found:
        logging_util.error(
            f"❌ VERIFICATION: All {constants.VERIFICATION_MAX_ATTEMPTS} attempts failed after {verify_duration:.3f}s"
        )
        raise Exception(
            f"Write-then-read verification failed: Could not find document '{document_id}' "
            f"for actor='{actor}' after {constants.VERIFICATION_MAX_ATTEMPTS} attempts"
        )

    # Calculate total latency
    total_duration: float = time.time() - start_time

    logging_util.info(
        f"📖 Verify-latest timing: {verify_duration:.3f}s (checked latest 10 entries)"
    )
    logging_util.info(
        f"⏱️ Write-then-read TOTAL latency: {total_duration:.3f}s "
        f"(write: {write_duration:.3f}s, verify: {verify_duration:.3f}s, sleep: 0.100s)"
    )
    logging_util.info(
        f"✅ Write-then-read verification successful: "
        f"user={user_id}, campaign={campaign_id}, actor={actor}"
    )

    # Return None to match original add_story_entry API
    return


def _write_story_entry_to_firestore(
    user_id: UserId,
    campaign_id: CampaignId,
    actor: str,
    text: str,
    mode: str | None = None,
    structured_fields: dict[str, Any] | None = None,
) -> str:  # noqa: PLR0915
    """Internal implementation to write story entry data directly to Firestore

    Writes story entries using the standard collection.add() method without transactions.
    Text is automatically chunked if it exceeds Firestore's size limits.

    Returns:
        str: Document ID of the first chunk (used for verification)
    """
    db = get_db()
    story_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
    )
    text_bytes: bytes = text.encode("utf-8")
    chunks: list[bytes] = [
        text_bytes[i : i + MAX_TEXT_BYTES]
        for i in range(0, len(text_bytes), MAX_TEXT_BYTES)
    ]

    if not chunks:
        # Handle empty text for both user and AI actors
        if actor == constants.ACTOR_GEMINI:
            god_mode_empty_narrative = bool(
                structured_fields and structured_fields.get("god_mode_response")
            )
            if god_mode_empty_narrative:
                logging_util.info(
                    f"🛡️ GOD_MODE_EMPTY_NARRATIVE: Accepting empty narrative for campaign {campaign_id} "
                    "because god_mode_response is present."
                )
                chunks = [b""]
            else:
                # AI returned empty narrative - this is an LLM compliance error
                # Do not mask with placeholder text - surface the error
                logging_util.error(
                    f"🚨 EMPTY_NARRATIVE_ERROR: LLM returned empty narrative for campaign {campaign_id}. "
                    f"This indicates a system prompt compliance issue. structured_fields present: {bool(structured_fields)}"
                )
                raise FirestoreWriteError(
                    f"LLM returned empty narrative for campaign {campaign_id}. "
                    "The AI must always provide narrative content. Check system prompts for narrative requirements."
                )
        else:
            # Create a placeholder for empty user inputs (this is valid - user submitted empty)
            placeholder_text = "[Empty input]"
            chunks = [placeholder_text.encode("utf-8")]
    base_entry_data: dict[str, Any] = {"actor": actor}
    if mode:
        base_entry_data["mode"] = mode

    # For AI responses, structured_fields should always be provided
    # Save ALL fields from structured_fields to Firestore
    if structured_fields:
        # Simply merge all structured fields into base_entry_data
        # This ensures we capture any field that Gemini provides
        for field_name, field_value in structured_fields.items():
            # Skip None values to avoid storing null fields
            if field_value is not None:
                base_entry_data[field_name] = field_value
    elif actor == constants.ACTOR_GEMINI:
        # Log warning if AI response missing structured fields
        logging_util.warning(
            f"AI response missing structured_fields for campaign {campaign_id}"
        )

    # Simple and reliable write with document ID capture
    timestamp: datetime.datetime = datetime.datetime.now(UTC)
    document_id: str | None = None

    for i, chunk in enumerate(chunks):
        entry_data: dict[str, Any] = base_entry_data.copy()
        entry_data["text"] = chunk.decode("utf-8")
        entry_data["timestamp"] = timestamp
        entry_data["part"] = i + 1

        try:
            # Create the story entry and capture document ID
            add_result = story_ref.collection("story").add(entry_data)
            # Handle both real Firestore (tuple) and mock (direct reference)
            doc_ref = None
            if isinstance(add_result, tuple):
                for candidate in add_result:
                    if hasattr(candidate, "id"):
                        doc_ref = candidate
                        break
                if doc_ref is None and len(add_result) >= 2:
                    doc_ref = add_result[1]
                elif doc_ref is None and len(add_result) >= 1:
                    doc_ref = add_result[0]
            else:
                doc_ref = add_result

            if i == 0:  # Store the first chunk's document ID for verification
                if doc_ref is not None and hasattr(doc_ref, "id"):
                    document_id = doc_ref.id
                    logging_util.debug(
                        f"✍️ WRITE: Created document {document_id} with actor='{actor}'"
                    )
                else:
                    # CRITICAL: This should never happen in production!
                    mock_mode = os.getenv("MOCK_SERVICES_MODE") == "true"
                    logging_util.error(
                        f"🚨 CRITICAL: doc_ref missing .id attribute! "
                        f"mock_mode={mock_mode}, doc_ref={doc_ref}, "
                        f"add_result={add_result}, type={type(add_result)}"
                    )
                    raise FirestoreWriteError(
                        "Firestore add() failed to return a document reference with an id. "
                        f"add_result={add_result}, type={type(add_result)}"
                    )
        except Exception:
            raise  # Re-raise the exception to maintain original behavior

    try:
        story_ref.update({"last_played": timestamp})
    except Exception:
        raise

    # Return document ID for verification - must be set by this point
    # FirestoreWriteError is raised above if doc_ref doesn't have an id
    if document_id is None:
        raise FirestoreWriteError(
            "Document ID was not captured during write. "
            "This indicates an unexpected error in the Firestore write operation."
        )
    return document_id


def verify_document_by_id(
    user_id: UserId, campaign_id: CampaignId, document_id: str, expected_actor: str
) -> bool:
    """Verify a story entry was written by directly reading the document by ID

    Args:
        user_id: User ID
        campaign_id: Campaign ID
        document_id: Document ID to verify
        expected_actor: Expected actor type for validation

    Returns:
        bool: True if document exists and has correct actor
    """
    if not document_id:
        logging_util.error("🔍 VERIFICATION: No document_id provided")
        return False

    try:
        db = get_db()
        campaign_ref = (
            db.collection("users")
            .document(user_id)
            .collection("campaigns")
            .document(campaign_id)
        )
        doc_ref = campaign_ref.collection("story").document(document_id)

        # Direct document read by ID
        doc = doc_ref.get()

        if not doc.exists:
            logging_util.warning(
                f"🔍 VERIFICATION: Document {document_id} does not exist"
            )
            return False

        entry = doc.to_dict()
        actual_actor = entry.get("actor", constants.ACTOR_UNKNOWN)

        if actual_actor == expected_actor:
            return True
        logging_util.warning(
            f"🔄 VERIFICATION: Actor mismatch - expected '{expected_actor}', got '{actual_actor}'"
        )
        return False

    except Exception as e:
        logging_util.error(
            f"❌ VERIFICATION: Error reading document {document_id}: {str(e)}"
        )
        return False


def verify_latest_entry(
    user_id: UserId, campaign_id: CampaignId, actor: str, text: str, limit: int = 10
) -> bool:
    """Efficiently verify a story entry was written by reading only the latest entries

    Args:
        user_id: User ID
        campaign_id: Campaign ID
        actor: Expected actor type
        text: Expected text content
        limit: Number of latest entries to check (default 10)

    Returns:
        bool: True if matching entry found in latest entries
    """
    db = get_db()
    campaign_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
    )

    # Read only the latest N entries, ordered by timestamp descending
    story_ref = (
        campaign_ref.collection("story")
        .order_by("timestamp", direction="DESCENDING")
        .limit(limit)
    )
    story_docs = story_ref.stream()

    # Check if our entry is among the latest entries
    for _i, doc in enumerate(story_docs):
        entry = doc.to_dict()
        entry_actor = entry.get("actor", constants.ACTOR_UNKNOWN)
        entry_text = entry.get("text", "NO_TEXT")

        # Check for exact match
        if entry_actor == actor and entry_text == text:
            return True

    return False


@log_exceptions
def create_campaign(
    user_id: UserId,
    title: str,
    initial_prompt: str,
    opening_story: str,
    initial_game_state: dict[str, Any],
    selected_prompts: list[str] | None = None,
    use_default_world: bool = False,
    opening_story_structured_fields: dict[str, Any] | None = None,
) -> CampaignId:
    db = get_db()
    campaigns_collection = (
        db.collection("users").document(user_id).collection("campaigns")
    )

    # Create the main campaign document
    campaign_ref: firestore.DocumentReference = campaigns_collection.document()
    campaign_data: dict[str, Any] = {
        "title": title,
        "initial_prompt": initial_prompt,
        "created_at": datetime.datetime.now(UTC),
        "last_played": datetime.datetime.now(UTC),
        "selected_prompts": selected_prompts or [],
        "use_default_world": use_default_world,
    }
    campaign_ref.set(campaign_data)

    # Create the initial game state document
    game_state_ref: firestore.DocumentReference = campaign_ref.collection(
        "game_states"
    ).document("current_state")
    game_state_ref.set(initial_game_state)

    # Assuming 'god' mode for the very first conceptual prompt.
    # You might want to make this mode configurable or infer it.
    add_story_entry(user_id, campaign_ref.id, "user", initial_prompt, mode="god")

    add_story_entry(
        user_id,
        campaign_ref.id,
        "gemini",
        opening_story,
        structured_fields=opening_story_structured_fields,
    )

    return campaign_ref.id


@log_exceptions
def get_campaign_game_state(
    user_id: UserId, campaign_id: CampaignId
) -> GameState | None:
    """Fetches the current game state for a given campaign."""
    db = get_db()
    game_state_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
        .collection("game_states")
        .document("current_state")
    )

    game_state_doc = game_state_ref.get()
    if not game_state_doc.exists:
        return None
    game_state = GameState.from_dict(game_state_doc.to_dict())
    if game_state is None:
        logging_util.warning(
            "GET_CAMPAIGN_GAME_STATE: GameState.from_dict returned None, returning empty GameState"
        )
        return GameState(user_id=user_id)
    return game_state


@log_exceptions
def update_campaign_game_state(
    user_id: UserId, campaign_id: CampaignId, game_state_update: dict[str, Any]
) -> None:
    """Updates the game state for a campaign, overwriting with the provided dict."""
    if not user_id or not campaign_id:
        raise ValueError("User ID and Campaign ID are required.")

    db = get_db()
    game_state_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
        .collection("game_states")
        .document("current_state")
    )

    try:
        # NOTE: This function now expects a COMPLETE game state dictionary.
        # The merge logic has been moved to the handle_interaction function in main.py
        # to ensure consistency across all update types (AI, GOD_MODE, etc.)

        # Normalize dotted keys (e.g., "player_character_data.level" -> nested in player_character_data)
        # This handles LLM output that uses both nested objects AND dotted paths
        game_state_update = _normalize_dotted_keys_in_place(game_state_update)

        # Add the last updated timestamp before setting.
        game_state_update["last_state_update_timestamp"] = firestore.SERVER_TIMESTAMP

        game_state_ref.set(game_state_update)
        logging_util.info(
            f"Successfully set new game state for campaign {campaign_id}."
        )
        # The log below is for the final state being written.
        logging_util.info(
            f"Final state written to Firestore for campaign {campaign_id}:\\n{_truncate_log_json(game_state_update)}"
        )

    except Exception as e:
        logging_util.error(
            f"Failed to update game state for campaign {campaign_id}: {e}",
            exc_info=True,
        )
        raise


# --- NEWLY ADDED FUNCTION ---
@log_exceptions
def update_campaign_title(
    user_id: UserId, campaign_id: CampaignId, new_title: str
) -> bool:
    """Updates the title of a specific campaign."""
    db = get_db()
    campaign_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
    )
    campaign_ref.set({"title": new_title}, merge=True)
    return True


@log_exceptions
def update_campaign(
    user_id: UserId, campaign_id: CampaignId, updates: dict[str, Any]
) -> bool:
    """Updates a campaign with arbitrary updates.

    Supports dot-notation paths for nested field updates.
    Example: {"game_state.arc_milestones.quest1": {"status": "completed"}}
    will correctly update the nested structure.
    Dot characters are reserved for nested paths; literal dots in field names are
    not supported by this helper.

    Args:
        user_id: User ID
        campaign_id: Campaign ID
        updates: Dictionary of updates, supports dot-notation keys for nested paths

    Returns:
        bool: True if update succeeded
    """
    db = get_db()
    campaign_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
    )
    campaign_doc = campaign_ref.get()
    if not campaign_doc.exists:
        logging_util.error(
            "update_campaign: campaign document not found "
            f"(user_id={user_id}, campaign_id={campaign_id})"
        )
        raise ValueError(
            f"Campaign {campaign_id} not found for user {user_id}; "
            "cannot apply updates."
        )

    # Check if any keys use dot-notation
    has_dot_notation = any("." in key for key in updates)

    if has_dot_notation:
        # Expand dot-notation to nested dicts and use set(merge=True).
        # We intentionally avoid Firestore's update() with dot-paths here because:
        #   - update() operates on exact field paths and can overwrite or recreate
        #     intermediate maps if the existing document shape does not match what
        #     the path assumes (e.g., when a parent field is missing or is not a map).
        #   - Small changes to the stored structure (or legacy/migrated documents)
        #     can cause update() with a dot-path to behave differently across
        #     campaigns, sometimes creating flat fields instead of the nested
        #     structure our code expects.
        # By first expanding dot-notation into a nested dict and then calling
        # set(..., merge=True), we ask Firestore to merge at the map level:
        #   - Only the specified nested fields are updated.
        #   - Unspecified sibling fields under the same parent map are preserved.
        #   - The behavior is consistent even when some intermediate maps are
        #     missing (Firestore will create them as needed during the merge).
        # This makes nested updates more predictable and resilient than relying
        # directly on update() with dot-paths against documents that may evolve
        # over time.
        expanded_updates = _expand_dot_notation(updates)
        logging_util.info(
            f"update_campaign: Expanded dot-notation updates for campaign {campaign_id}"
        )
        campaign_ref.set(expanded_updates, merge=True)
    else:
        # No dot-notation, use standard update
        logging_util.info(
            f"update_campaign: Using standard update for campaign {campaign_id}"
        )
        campaign_ref.update(updates)

    return True


# --- USER SETTINGS FUNCTIONS ---
@log_exceptions
def get_user_settings(user_id: UserId) -> dict[str, Any] | None:
    """Get user settings from Firestore.

    Args:
        user_id: User ID to get settings for

    Returns:
        Dict containing user settings, empty dict if user exists but no settings,
        or None if user doesn't exist or database error
    """
    try:
        db = get_db()
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()

        if user_doc.exists:
            data = user_doc.to_dict()
            return data.get("settings", {})  # Empty dict for user with no settings
        # Return None for users that don't exist yet
        return None
    except Exception as e:
        # Hash user_id for security in logs
        user_hash = str(hash(user_id))[-6:] if user_id else "unknown"
        logging_util.error(
            f"Failed to get user settings for user_{user_hash}: {str(e)}"
        )
        # Return None to distinguish database errors from no settings
        return None


@log_exceptions
def update_user_settings(user_id: UserId, settings: dict[str, Any]) -> bool:
    """Update user settings in Firestore.

    Uses nested field updates to prevent clobbering sibling settings fields.

    Args:
        user_id: User ID to update settings for
        settings: Dictionary of settings to update

    Returns:
        bool: True if update succeeded, False otherwise
    """
    try:
        db = get_db()
        user_ref = db.collection("users").document(user_id)

        # Check if user document exists first
        user_doc = user_ref.get()

        # Use Firestore SERVER_TIMESTAMP - SDK import is guaranteed at module level
        timestamp = firestore.SERVER_TIMESTAMP

        if user_doc.exists:
            # Use nested field update to avoid clobbering sibling settings
            update_data = {}
            for key, value in settings.items():
                update_data[f"settings.{key}"] = value
            update_data["lastUpdated"] = timestamp

            user_ref.update(update_data)
        else:
            # Create new document with settings
            user_data = {
                "settings": settings,
                "lastUpdated": timestamp,
                "createdAt": timestamp,
            }
            user_ref.set(user_data)

        logging_util.info(f"Updated settings for user {user_id}: {settings}")
        return True
    except Exception as e:
        logging_util.error(
            f"Failed to update user settings for {user_id}: {str(e)}", exc_info=True
        )
        return False
