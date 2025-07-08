"""
Gemini Response objects for clean architecture between AI service and main application.

DEPRECATED: This module is kept for backwards compatibility. 
New code should use llm_response.py for the unified LLMResponse interface.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
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
        
        # Log for debugging
        logging.debug(f"GeminiResponse.create parsed narrative: {narrative_text[:200]}...")
        logging.debug(f"GeminiResponse.create has structured response: {structured_response is not None}")
        
        
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