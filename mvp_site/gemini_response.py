"""
Gemini Response objects for clean architecture between AI service and main application.

DEPRECATED: This module is kept for backwards compatibility. 
New code should use llm_response.py for the unified LLMResponse interface.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
import re
from narrative_response_schema import NarrativeResponse

# Import the new unified response classes
from llm_response import GeminiLLMResponse as _GeminiLLMResponse


class GeminiResponse(_GeminiLLMResponse):
    """
    DEPRECATED: Backwards compatibility class for existing GeminiResponse usage.
    
    This class inherits from GeminiLLMResponse to maintain API compatibility
    while providing the new unified interface.
    """
    
    def __init__(self, narrative_text: str, 
                 structured_response: Optional[NarrativeResponse] = None,
                 debug_tags_present: Optional[Dict[str, bool]] = None,
                 processing_metadata: Optional[Dict[str, Any]] = None,
                 provider: str = "gemini",
                 model: str = "gemini-2.5-flash"):
        """
        Backwards compatible constructor for GeminiResponse.
        
        Maintains the old interface while using the new unified structure.
        """
        # Store the raw narrative text separately
        self._raw_narrative_text = narrative_text
        
        super().__init__(
            narrative_text=narrative_text,
            provider=provider,
            model=model,
            structured_response=structured_response,
            debug_tags_present=debug_tags_present,
            processing_metadata=processing_metadata
        )
    
    # Maintain backwards compatibility for property access
    @property 
    def state_updates(self) -> Dict[str, Any]:
        """Backwards compatibility property for state_updates."""
        return self.get_state_updates()
    
    @property
    def entities_mentioned(self) -> List[str]:
        """Backwards compatibility property for entities_mentioned."""
        return self.get_entities_mentioned()
    
    @property 
    def location_confirmed(self) -> str:
        """Backwards compatibility property for location_confirmed."""
        return self.get_location_confirmed()
    
    @property
    def debug_info(self) -> Dict[str, Any]:
        """Backwards compatibility property for debug_info."""
        return self.get_debug_info()
    
    def get_narrative_text(self, debug_mode: bool = False) -> str:
        """
        Get the narrative text with debug content handled based on debug mode.
        
        Args:
            debug_mode: If True, include debug content. If False, strip debug content.
            
        Returns:
            Narrative text with debug content handled appropriately
        """
        if not hasattr(self, '_raw_narrative_text'):
            # If we don't have raw text stored, return the narrative text as is
            return self.narrative_text
            
        if debug_mode:
            # In debug mode, strip only STATE_UPDATES_PROPOSED blocks (never shown to users)
            return self._strip_state_updates_only(self._raw_narrative_text)
        else:
            # Strip all debug content when debug mode is off
            return self._strip_debug_content(self._raw_narrative_text)
    
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
        processed_text = re.sub(r'\[DEBUG_START\][\s\S]*?\[DEBUG_END\]', '', text)
        processed_text = re.sub(r'\[DEBUG_STATE_START\][\s\S]*?\[DEBUG_STATE_END\]', '', processed_text)
        processed_text = re.sub(r'\[DEBUG_ROLL_START\][\s\S]*?\[DEBUG_ROLL_END\]', '', processed_text)
        # Also strip STATE_UPDATES_PROPOSED blocks which are internal state management
        processed_text = re.sub(r'\[STATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]', '', processed_text)
        # Handle malformed STATE_UPDATES_PROPOSED blocks (missing opening characters)
        processed_text = re.sub(r'S?TATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]', '', processed_text)
        
        return processed_text
    
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
        processed_text = re.sub(r'\[STATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]', '', text)
        # Also handle malformed blocks where the opening characters might be missing
        processed_text = re.sub(r'S?TATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]', '', processed_text)
        return processed_text
    
    @classmethod
    def create(cls, raw_response_text: str, model: str = "gemini-2.5-flash") -> 'GeminiResponse':
        """
        Create a GeminiResponse from raw Gemini API response.
        
        Handles all JSON parsing internally.
        
        Args:
            raw_response_text: Raw text response from Gemini API
            model: Model name used for generation
            
        Returns:
            GeminiResponse with parsed narrative and structured data
        """
        # Import here to avoid circular dependency
        from narrative_response_schema import parse_structured_response
        
        # Parse the raw response to extract narrative and structured data
        narrative_text, structured_response = parse_structured_response(raw_response_text)
        
        
        return cls(
            narrative_text=narrative_text,
            provider="gemini",
            model=model,
            structured_response=structured_response
        )
    
    @classmethod
    def create_legacy(cls, narrative_text: str, structured_response: Optional[NarrativeResponse], 
               model: str = "gemini-2.5-flash") -> 'GeminiResponse':
        """
        Legacy create method for backwards compatibility.
        
        DEPRECATED: Use create() with raw response text instead.
        """
        logging.warning("Using deprecated create_legacy method. Switch to create() with raw response.")
        
        return cls(
            narrative_text=narrative_text,
            provider="gemini",
            model=model,
            structured_response=structured_response
        )