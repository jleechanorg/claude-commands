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
    def create(cls, narrative_text: str, structured_response: Optional[NarrativeResponse], 
               model: str = "gemini-2.5-flash") -> 'GeminiResponse':
        """
        Create a GeminiResponse with backwards compatibility.
        
        Maintains the existing create() interface while using the new unified structure.
        """
        # JSON BUG DEBUG: Log what's being passed to GeminiResponse
        logging.debug(f"JSON_BUG_GEMINI_RESPONSE_CREATE_NARRATIVE: {narrative_text[:500]}...")
        logging.debug(f"JSON_BUG_GEMINI_RESPONSE_CREATE_STRUCTURED: {structured_response is not None}")
        
        # Check if narrative_text contains JSON - this should never happen now
        if '"narrative":' in narrative_text or '"god_mode_response":' in narrative_text:
            logging.error(f"JSON_BUG_DETECTED_IN_GEMINI_RESPONSE_CREATE: narrative_text contains JSON!")
            raise ValueError("narrative_text should not contain JSON - this indicates a parsing bug")
        
        return cls(
            narrative_text=narrative_text,
            provider="gemini",
            model=model,
            structured_response=structured_response
        )