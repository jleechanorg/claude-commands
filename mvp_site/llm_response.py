"""
Gemini Response objects for clean architecture between AI service and main application.
"""

import json
import re
from typing import Any

from mvp_site import logging_util
from mvp_site.action_resolution_utils import (
    get_action_resolution,
    get_outcome_resolution,
)
from mvp_site.narrative_response_schema import (
    NarrativeResponse,
    parse_structured_response,
)


class LLMResponse:
    """
    Gemini Response wrapper for clean architecture between AI service and main application.

    Provides structured response handling with backward compatibility.
    """

    def __init__(
        self,
        narrative_text: str,
        structured_response: NarrativeResponse | None = None,
        debug_tags_present: dict[str, bool] | None = None,
        processing_metadata: dict[str, Any] | None = None,
        provider: str = "gemini",
        model: str = "gemini-3-pro-preview",
        agent_mode: str | None = None,
        raw_response_text: str | None = None,
    ):
        """
        Initialize LLMResponse.

        Args:
            narrative_text: The clean narrative text from the response
            structured_response: Optional parsed NarrativeResponse object
            debug_tags_present: Dictionary indicating which debug tags were found
            processing_metadata: Additional metadata about response processing
            provider: LLM provider name (default: "gemini")
            model: Model identifier
            agent_mode: The mode of the agent that generated this response
                        (e.g., "god", "think", "character"). Single source of truth
                        for mode detection - set by agent selection in llm_service.
            raw_response_text: The full raw response text from the LLM (for debugging)
        """
        self.narrative_text = narrative_text
        self.structured_response = structured_response
        self.debug_tags_present = debug_tags_present or {}
        self.processing_metadata = processing_metadata or {}
        self.provider = provider
        self.model = model
        self.agent_mode = agent_mode
        self._raw_narrative_text = narrative_text
        self.raw_response_text = raw_response_text

        # Detect old tags if not already done
        if debug_tags_present is None:
            self._detect_old_tags()

    # Maintain backwards compatibility for property access
    @property
    def state_updates(self) -> dict[str, Any]:
        """Backwards compatibility property for state_updates."""
        return self.get_state_updates()

    @property
    def entities_mentioned(self) -> list[str]:
        """Backwards compatibility property for entities_mentioned."""
        return self.get_entities_mentioned()

    @property
    def location_confirmed(self) -> str:
        """Backwards compatibility property for location_confirmed."""
        return self.get_location_confirmed()

    @property
    def debug_info(self) -> dict[str, Any]:
        """Backwards compatibility property for debug_info."""
        return self.get_debug_info()

    @property
    def session_header(self) -> str:
        """Get session header from structured response."""
        if self.structured_response and hasattr(
            self.structured_response, "session_header"
        ):
            return self.structured_response.session_header or ""
        return ""

    @property
    def planning_block(self) -> str:
        """Get planning block from structured response."""
        if self.structured_response and hasattr(
            self.structured_response, "planning_block"
        ):
            return self.structured_response.planning_block or ""
        return ""

    @property
    def dice_rolls(self) -> list[str]:
        """Get dice rolls from structured response."""
        if self.structured_response and hasattr(self.structured_response, "dice_rolls"):
            return self.structured_response.dice_rolls or []
        return []

    @property
    def resources(self) -> str:
        """Get resources from structured response."""
        if self.structured_response and hasattr(self.structured_response, "resources"):
            return self.structured_response.resources or ""
        return ""

    @property
    def action_resolution(self) -> dict[str, Any]:
        """Get action resolution from structured response (backward compat with outcome_resolution)."""
        return get_action_resolution(self.structured_response)

    @property
    def outcome_resolution(self) -> dict[str, Any]:
        """Backwards compatibility property for outcome_resolution."""
        return get_outcome_resolution(self.structured_response)

    def _detect_old_tags(self) -> dict[str, list[str]]:
        """
        Detect deprecated tag patterns in the response and log warnings.

        This helps identify when the LLM is still using old patterns that should
        be replaced with proper JSON fields.

        Returns:
            Dictionary mapping tag types to lists of found instances
        """
        old_tags_found = {
            "state_updates_proposed": [],
            "debug_blocks": [],
            "other_deprecated": [],
        }

        patterns = {
            "state_updates_proposed": [
                r"\[STATE_UPDATES_PROPOSED\]",
                r"\[END_STATE_UPDATES_PROPOSED\]",
                r"\[S?TATE_UPDATES_PROPOSED\]",  # Malformed variants
            ],
            "debug_blocks": [
                r"\[DEBUG_START\]",
                r"\[DEBUG_END\]",
                r"\[DEBUG_STATE_START\]",
                r"\[DEBUG_STATE_END\]",
                r"\[DEBUG_ROLL_START\]",
                r"\[DEBUG_ROLL_END\]",
            ],
            "other_deprecated": [r"\[ENTITY_TRACKING_ENABLED\]", r"\[PRE_JSON_MODE\]"],
        }

        # Check narrative text
        if self.narrative_text:
            for tag_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.findall(pattern, self.narrative_text)
                    if matches:
                        old_tags_found[tag_type].extend(matches)
                        logging_util.warning(
                            f"Deprecated tag found in narrative: {pattern} "
                            f"(found {len(matches)} times). These should not appear in narrative field."
                        )

        # Check structured response if available
        if self.structured_response:
            # Convert to string to search (this is a bit hacky but effective)
            try:
                # Handle different response types
                if hasattr(self.structured_response, "dict"):
                    response_dict = self.structured_response.dict()
                elif hasattr(self.structured_response, "__dict__"):
                    response_dict = self.structured_response.__dict__
                else:
                    response_dict = str(self.structured_response)

                response_str = json.dumps(response_dict)
                for tag_type, pattern_list in patterns.items():
                    for pattern in pattern_list:
                        matches = re.findall(pattern, response_str)
                        if matches:
                            old_tags_found[tag_type].extend(matches)
                            logging_util.warning(
                                f"Deprecated tag found in structured response: {pattern} "
                                f"(found {len(matches)} times). Use proper JSON fields instead."
                            )
            except Exception as e:
                logging_util.debug(
                    f"Could not check structured response for old tags: {e}"
                )

        # Log summary if any old tags found
        total_found = sum(len(tags) for tags in old_tags_found.values())
        if total_found > 0:
            logging_util.error(
                f"DEPRECATED TAGS DETECTED: Found {total_found} deprecated tags in response. "
                "Update prompts to use proper JSON format. Details: "
                f"{ {k: len(v) for k, v in old_tags_found.items() if v} }"
            )

            # Store in processing metadata for tracking
            if self.processing_metadata is None:
                self.processing_metadata = {}
            self.processing_metadata["deprecated_tags_found"] = old_tags_found

        return old_tags_found

    def get_narrative_text(self, debug_mode: bool = False) -> str:
        """
        Get the narrative text with debug content handled based on debug mode.

        For new structured responses, the narrative is already clean.
        For legacy responses, this method provides backward compatibility.

        Args:
            debug_mode: If True, include debug content. If False, strip debug content.

        Returns:
            Clean narrative text (debug content is now in separate fields)
        """
        # With the new architecture, narrative_text is always clean
        # Debug content is in separate fields (session_header, planning_block, etc.)
        return self.narrative_text

    @property
    def has_debug_content(self) -> bool:
        """Check if response has any debug content."""
        # Check debug tags if present - this is what the tests check
        return bool(self.debug_tags_present and any(self.debug_tags_present.values()))

    def get_state_updates(self) -> dict[str, Any]:
        """Get state updates from structured response."""
        if self.structured_response and hasattr(
            self.structured_response, "state_updates"
        ):
            return self.structured_response.state_updates or {}

        # JSON mode is required - log error if no structured response
        if not self.structured_response:
            logging_util.error(
                "ERROR: No structured response available for state updates. JSON mode is required."
            )
        return {}

    def get_entities_mentioned(self) -> list[str]:
        """Get entities mentioned from structured response."""
        if self.structured_response and hasattr(
            self.structured_response, "entities_mentioned"
        ):
            return self.structured_response.entities_mentioned or []
        return []

    def get_location_confirmed(self) -> str:
        """Get confirmed location from structured response."""
        if self.structured_response and hasattr(
            self.structured_response, "location_confirmed"
        ):
            return self.structured_response.location_confirmed or "Unknown"
        return "Unknown"

    def get_debug_info(self) -> dict[str, Any]:
        """Get debug info from structured response."""
        info = {}
        if self.structured_response and hasattr(self.structured_response, "debug_info"):
            # Create a copy to avoid mutating the original debug_info dict
            original_debug_info = self.structured_response.debug_info or {}
            info = dict(original_debug_info)

        # Inject raw response text if available (critical for test harness validation)
        if self.raw_response_text:
            info["raw_response_text"] = self.raw_response_text

        return info

    @staticmethod
    def _strip_debug_content(text: str) -> str:
        """
        Strip debug content from AI response text while preserving the rest.
        Removes content between debug tags: [DEBUG_START/END], [DEBUG_ROLL_START/END], [DEBUG_STATE_START/END]
        Also removes [STATE_UPDATES_PROPOSED] blocks which are internal state management.

        Args:
            text: The full AI response with debug content

        Returns:
            The response with debug content removed
        """
        if not text:
            return text

        # Use regex for proper pattern matching - same patterns as frontend
        processed_text = re.sub(r"\[DEBUG_START\][\s\S]*?\[DEBUG_END\]", "", text)
        processed_text = re.sub(
            r"\[DEBUG_STATE_START\][\s\S]*?\[DEBUG_STATE_END\]", "", processed_text
        )
        processed_text = re.sub(
            r"\[DEBUG_ROLL_START\][\s\S]*?\[DEBUG_ROLL_END\]", "", processed_text
        )
        # Also strip STATE_UPDATES_PROPOSED blocks which are internal state management
        processed_text = re.sub(
            r"\[STATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]",
            "",
            processed_text,
        )
        # Handle malformed STATE_UPDATES_PROPOSED blocks (missing opening characters)
        return re.sub(
            r"\[S?TATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]",
            "",
            processed_text,
        )

    @staticmethod
    def _strip_state_updates_only(text: str) -> str:
        """
        Strip only STATE_UPDATES_PROPOSED blocks from text, preserving all other debug content.
        This ensures that internal state management blocks are never shown to users, even in debug mode.

        Args:
            text: The full AI response text

        Returns:
            The response with STATE_UPDATES_PROPOSED blocks removed
        """
        if not text:
            return text

        # Remove only STATE_UPDATES_PROPOSED blocks - these should never be shown to users
        processed_text = re.sub(
            r"\[STATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]",
            "",
            text,
        )
        # Also handle malformed blocks where the opening characters might be missing
        return re.sub(
            r"\[S?TATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]",
            "",
            processed_text,
        )

    @staticmethod
    def _strip_all_debug_tags(text: str) -> str:
        """Remove all debug tags from text."""
        if not text:
            return text

        # Remove [Mode: STORY MODE] prefix
        text = re.sub(r"^\[Mode:\s*[A-Z\s]+\]\s*\n*", "", text)

        # Remove embedded JSON objects (malformed responses)
        text = re.sub(
            r"""\{[^}]*"session_header"[^}]*\}[^"']"[^"']*\"""", "", text, flags=re.DOTALL
        )

        # Remove [DEBUG_START]...[DEBUG_END] blocks
        text = re.sub(r"\[DEBUG_START\].*?\[DEBUG_END\]", "", text, flags=re.DOTALL)

        # Remove [SESSION_HEADER] blocks (if they exist in narrative)
        text = re.sub(
            r"\[SESSION_HEADER\].*?(?=\n\n[A-Z]|\n\n[A-S]|\n\nT|\n\nU|\n\nV|\n\nW|\n\nX|\n\nY|\n\nZ|\n[A-Z][a-z])",
            "",
            text,
            flags=re.DOTALL,
        )

        # Remove [STATE_UPDATES_PROPOSED] blocks
        text = re.sub(
            r"\[STATE_UPDATES_PROPOSED\].*?\[END_STATE_UPDATES_PROPOSED\]",
            "",
            text,
            flags=re.DOTALL,
        )

        # Remove other debug markers
        text = re.sub(
            r"\[DEBUG_[A-Z_]+\].*?\[DEBUG_[A-Z_]+\]", "", text, flags=re.DOTALL
        )

        # Clean up extra whitespace
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
        return text.strip()

    @staticmethod
    def _detect_debug_tags_static(text: str) -> dict[str, bool]:
        """Detect which debug tags are present in text."""
        if not text:
            return {}

        return {
            "debug_start_end": "[DEBUG_START]" in text and "[DEBUG_END]" in text,
            "session_header": "[SESSION_HEADER]" in text,
            "state_updates": "[STATE_UPDATES_PROPOSED]" in text,
            "debug_rolls": "[DEBUG_ROLL_START]" in text,
        }

    @classmethod
    def create(
        cls,
        raw_response_text: str,
        model: str = "gemini-3-pro-preview",
        provider: str = "gemini",
        processing_metadata: dict[str, Any] | None = None,
        agent_mode: str | None = None,
    ) -> "LLMResponse":
        """
        Create a LLMResponse from raw Gemini API response.

        Handles all JSON parsing internally.

        Args:
            raw_response_text: Raw text response from Gemini API
            model: Model name used for generation

        Returns:
            LLMResponse with parsed narrative and structured data
        """
        # Parse the raw response to extract narrative and structured data
        narrative_text, structured_response = parse_structured_response(
            raw_response_text
        )

        # If we have a structured response, use the new method
        if structured_response:
            return cls.create_from_structured_response(
                structured_response,
                model,
                narrative_text,
                provider=provider,
                processing_metadata=processing_metadata,
                agent_mode=agent_mode,
                raw_response_text=raw_response_text,
            )

        # Otherwise fall back to legacy mode
        return cls.create_legacy(
            narrative_text,
            model,
            provider=provider,
            processing_metadata=processing_metadata,
            agent_mode=agent_mode,
            raw_response_text=raw_response_text,
        )

    @classmethod
    def create_from_structured_response(
        cls,
        structured_response: NarrativeResponse,
        model: str = "gemini-3-pro-preview",
        combined_narrative_text: str | None = None,
        *,
        provider: str = "gemini",
        processing_metadata: dict[str, Any] | None = None,
        agent_mode: str | None = None,
        raw_response_text: str | None = None,
    ) -> "LLMResponse":
        """
        Create LLMResponse from structured JSON response.

        This is the new preferred way to create responses that properly separates
        narrative from debug content.

        Args:
            structured_response: Parsed NarrativeResponse object
            model: Model name used for generation
            combined_narrative_text: The combined narrative text (including god_mode_response if present)
            agent_mode: The mode of the agent that generated this response (e.g., "god", "think")
            raw_response_text: The full raw response text from the LLM

        Returns:
            LLMResponse with clean narrative and structured data
        """
        # Use the combined narrative text if provided (includes god_mode_response)
        # Otherwise extract clean narrative from structured response
        clean_narrative = (
            combined_narrative_text
            if combined_narrative_text is not None
            else structured_response.narrative
        )

        # Remove any remaining debug tags from narrative using static method
        clean_narrative = cls._strip_all_debug_tags(clean_narrative)

        # Detect debug tags from structured response content
        debug_tags = {"dm_notes": False, "dice_rolls": False}

        if structured_response:
            debug_info = structured_response.debug_info or {}
            # Check for non-empty debug content
            debug_tags["dm_notes"] = bool(debug_info.get("dm_notes"))
            debug_tags["dice_rolls"] = bool(debug_info.get("dice_rolls"))
            # state_changes debug tag removed - only state_updates used now

        return cls(
            narrative_text=clean_narrative,
            model=model,
            provider=provider,
            structured_response=structured_response,
            debug_tags_present=debug_tags,
            processing_metadata=processing_metadata,
            agent_mode=agent_mode,
            raw_response_text=raw_response_text,
        )

    @classmethod
    def create_legacy(
        cls,
        narrative_text: str,
        model: str = "gemini-3-pro-preview",
        structured_response: NarrativeResponse | None = None,
        *,
        provider: str = "gemini",
        processing_metadata: dict[str, Any] | None = None,
        agent_mode: str | None = None,
        raw_response_text: str | None = None,
    ) -> "LLMResponse":
        """
        Create LLMResponse from plain text (legacy support).

        This handles old-style responses that embed debug content in the narrative.

        Args:
            narrative_text: Raw narrative text (may contain debug tags)
            model: Model name used for generation
            structured_response: Optional structured response object
            agent_mode: The mode of the agent that generated this response (e.g., "god", "think")
            raw_response_text: The full raw response text from the LLM

        Returns:
            LLMResponse with debug content stripped from narrative
        """
        clean_narrative = cls._strip_all_debug_tags(narrative_text)

        return cls(
            narrative_text=clean_narrative,
            model=model,
            provider=provider,
            structured_response=structured_response,
            debug_tags_present=cls._detect_debug_tags_static(narrative_text),
            processing_metadata=processing_metadata,
            agent_mode=agent_mode,
            raw_response_text=raw_response_text,
        )
