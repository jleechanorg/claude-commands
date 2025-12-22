"""
LLMRequest Class for Structured JSON Input to Gemini API

This class replaces the flawed json_input_schema approach that converted JSON
back to concatenated strings. Instead, it provides structured JSON that is sent
directly to the Gemini API without string conversion.

Key principles:
1. Flat JSON structure (no nested "context")
2. Preserves structured data types (dict, list)
3. Sends actual JSON to Gemini, not concatenated strings
4. Similar pattern to GeminiResponse class
"""

import json
from dataclasses import dataclass, field
from typing import Any

from mvp_site import logging_util
from mvp_site.serialization import json_default_serializer

# Configuration constants
# Increased payload size limit for Gemini 2.5 Flash to handle larger game states
# Gemini 2.5 Flash supports up to 500MB input, using 10MB for very complex campaigns
MAX_PAYLOAD_SIZE = (
    10 * 1024 * 1024
)  # 10MB limit for API payloads (supports very complex game states)
MAX_STRING_LENGTH = 1000000


class LLMRequestError(Exception):
    """Custom exception for LLMRequest validation and serialization errors."""

    def __init__(self, message: str, status_code: int | None = 422):
        super().__init__(message)
        self.status_code = status_code


class PayloadTooLargeError(LLMRequestError):
    """Raised when JSON payload exceeds size limits."""


class ValidationError(LLMRequestError):
    """Raised when LLMRequest fields fail validation."""


@dataclass
class LLMRequest:
    """
    Structured request object for Gemini API calls.

    Provides a clean, typed interface for building JSON requests that are sent
    directly to Gemini API without string concatenation.
    """

    # Core identification fields
    user_action: str
    game_mode: str
    user_id: str

    # Game data (structured, not strings)
    game_state: dict[str, Any] = field(default_factory=dict)
    story_history: list[dict[str, Any]] = field(default_factory=list)
    entity_tracking: dict[str, Any] = field(default_factory=dict)

    # Context fields
    checkpoint_block: str = ""
    core_memories: list[str] = field(default_factory=list)
    selected_prompts: list[str] = field(default_factory=list)
    sequence_ids: list[str] = field(default_factory=list)

    # Story generation specific fields
    character_prompt: str | None = None
    generate_companions: bool = False
    use_default_world: bool = False
    world_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate LLMRequest fields after initialization."""
        self._validate_required_fields()
        self._validate_field_types()
        self._validate_string_lengths()

    def _validate_required_fields(self):
        """Validate that required fields are not empty or None."""
        if not self.user_id or not self.user_id.strip():
            raise ValidationError("user_id cannot be empty or whitespace")

        if not self.game_mode or not self.game_mode.strip():
            raise ValidationError("game_mode cannot be empty or whitespace")

        if not self.user_action and self.user_action is not None:  # noqa: SIM102
            # Allow empty string for initial story, but not for continuation
            if not self.character_prompt:
                raise ValidationError(
                    "user_action cannot be empty for story continuation"
                )

    def _validate_field_types(self):  # noqa: PLR0912
        """Validate that fields have correct data types."""
        if not isinstance(self.game_state, dict):
            raise ValidationError(
                f"game_state must be dict, got {type(self.game_state)}"
            )

        if not isinstance(self.story_history, list):
            raise ValidationError(
                f"story_history must be list, got {type(self.story_history)}"
            )

        if not isinstance(self.entity_tracking, dict):
            raise ValidationError(
                f"entity_tracking must be dict, got {type(self.entity_tracking)}"
            )

        if not isinstance(self.core_memories, list):
            raise ValidationError(
                f"core_memories must be list, got {type(self.core_memories)}"
            )

        if not isinstance(self.selected_prompts, list):
            raise ValidationError(
                f"selected_prompts must be list, got {type(self.selected_prompts)}"
            )

        if not isinstance(self.sequence_ids, list):
            raise ValidationError(
                f"sequence_ids must be list, got {type(self.sequence_ids)}"
            )

        if not isinstance(self.world_data, dict):
            raise ValidationError(
                f"world_data must be dict, got {type(self.world_data)}"
            )

        # Validate list contents
        for i, memory in enumerate(self.core_memories):
            if not isinstance(memory, str):
                raise ValidationError(
                    f"core_memories[{i}] must be string, got {type(memory)}"
                )

        for i, prompt in enumerate(self.selected_prompts):
            if not isinstance(prompt, str):
                raise ValidationError(
                    f"selected_prompts[{i}] must be string, got {type(prompt)}"
                )

        for i, seq_id in enumerate(self.sequence_ids):
            if not isinstance(seq_id, str):
                raise ValidationError(
                    f"sequence_ids[{i}] must be string, got {type(seq_id)}"
                )

    def _validate_string_lengths(self):
        """Validate that string fields are within reasonable limits."""
        if len(self.user_action) > MAX_STRING_LENGTH:
            raise ValidationError(
                f"User action is too long ({len(self.user_action)} characters). "
                f"Maximum allowed is {MAX_STRING_LENGTH} characters. "
                f"Please reduce the length of your action."
            )

        if len(self.checkpoint_block) > MAX_STRING_LENGTH:
            raise ValidationError(
                f"Checkpoint block is too long ({len(self.checkpoint_block)} characters). "
                f"Maximum allowed is {MAX_STRING_LENGTH} characters. "
                f"Please reduce the checkpoint data size."
            )

        if self.character_prompt and len(self.character_prompt) > MAX_STRING_LENGTH:
            raise ValidationError(
                f"Campaign prompt is too long ({len(self.character_prompt)} characters). "
                f"Maximum allowed is {MAX_STRING_LENGTH} characters. "
                f"Please reduce the length of your character, setting, or description fields."
            )

    def to_json(self) -> dict[str, Any]:
        """
        Convert to flat JSON structure for direct Gemini API consumption.

        Returns a flat dictionary with all fields at the top level.
        No nested "context" wrapper - just the raw structured data.

        Raises:
            PayloadTooLargeError: If JSON payload exceeds size limits
            LLMRequestError: If JSON serialization fails
        """
        try:
            json_data = {
                "user_action": self.user_action,
                "game_mode": self.game_mode,
                "user_id": self.user_id,
                "game_state": self.game_state,
                "story_history": self.story_history,
                "entity_tracking": self.entity_tracking,
                "checkpoint_block": self.checkpoint_block,
                "core_memories": self.core_memories,
                "selected_prompts": self.selected_prompts,
                "sequence_ids": self.sequence_ids,
                "use_default_world": self.use_default_world,
            }

            # Add story generation specific fields if present
            if self.character_prompt:
                json_data["character_prompt"] = self.character_prompt
                json_data["generate_companions"] = self.generate_companions
                json_data["world_data"] = self.world_data

            # Validate payload size
            self._validate_payload_size(json_data)

            return json_data

        except (TypeError, ValueError) as e:
            logging_util.error(f"JSON serialization failed for LLMRequest: {e}")
            raise LLMRequestError(f"Failed to serialize LLMRequest to JSON: {e}") from e

    def _validate_payload_size(self, json_data: dict[str, Any]):
        """Validate that JSON payload is within size limits."""
        try:
            # Test serialization and measure size
            json_str = json.dumps(json_data, default=json_default_serializer)
            payload_size = len(json_str.encode("utf-8"))

            if payload_size > MAX_PAYLOAD_SIZE:
                raise PayloadTooLargeError(
                    f"JSON payload too large: {payload_size} bytes exceeds limit of {MAX_PAYLOAD_SIZE} bytes"
                )

            logging_util.debug(f"LLMRequest payload size: {payload_size} bytes")

        except (TypeError, ValueError) as e:
            logging_util.error(f"Failed to validate payload size: {e}")
            raise LLMRequestError(f"Payload size validation failed: {e}") from e

    @classmethod
    def build_story_continuation(
        cls,
        user_action: str,
        user_id: str,
        game_mode: str,
        game_state: dict[str, Any],
        story_history: list[dict[str, Any]],
        checkpoint_block: str = "",
        core_memories: list[str] | None = None,
        sequence_ids: list[str] | None = None,
        entity_tracking: dict[str, Any] | None = None,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
    ) -> "LLMRequest":
        """
        Build a LLMRequest for story continuation.

        Args:
            user_action: The user's input/action
            user_id: User identifier
            game_mode: Game interaction mode (e.g., 'character', 'story')
            game_state: Current game state as structured dict
            story_history: Previous story entries as structured list
            checkpoint_block: Checkpoint summary text
            core_memories: Important story memories
            sequence_ids: Story sequence identifiers
            entity_tracking: Entity tracking data
            selected_prompts: Selected prompt types
            use_default_world: Whether to use default world content

        Returns:
            LLMRequest configured for story continuation
        """
        # Validate input parameters before creating instance
        if not user_action and not entity_tracking:
            raise ValidationError("user_action cannot be empty for story continuation")

        if not isinstance(game_state, dict):
            raise ValidationError(f"game_state must be dict, got {type(game_state)}")

        if not isinstance(story_history, list):
            raise ValidationError(
                f"story_history must be list, got {type(story_history)}"
            )

        return cls(
            user_action=user_action,
            user_id=user_id,
            game_mode=game_mode,
            game_state=game_state,
            story_history=story_history,
            checkpoint_block=checkpoint_block,
            core_memories=core_memories or [],
            sequence_ids=sequence_ids or [],
            entity_tracking=entity_tracking or {},
            selected_prompts=selected_prompts or [],
            use_default_world=use_default_world,
        )

    @classmethod
    def build_initial_story(
        cls,
        character_prompt: str,
        user_id: str,
        selected_prompts: list[str],
        generate_companions: bool = False,
        use_default_world: bool = False,
        world_data: dict[str, Any] | None = None,
    ) -> "LLMRequest":
        """
        Build a LLMRequest for initial story generation.

        Args:
            character_prompt: The character/story prompt from user
            user_id: User identifier
            selected_prompts: List of selected prompt types
            generate_companions: Whether to generate companion characters
            use_default_world: Whether to use default world content
            world_data: Custom world data if applicable

        Returns:
            LLMRequest configured for initial story generation
        """
        # Validate input parameters before creating instance
        if not character_prompt or not character_prompt.strip():
            raise ValidationError("character_prompt cannot be empty for initial story")

        if not isinstance(selected_prompts, list):
            raise ValidationError(
                f"selected_prompts must be list, got {type(selected_prompts)}"
            )

        return cls(
            user_action="",  # No user action for initial story
            user_id=user_id,
            game_mode="character",  # Default for initial stories
            character_prompt=character_prompt,
            selected_prompts=selected_prompts,
            generate_companions=generate_companions,
            use_default_world=use_default_world,
            world_data=world_data or {},
        )
