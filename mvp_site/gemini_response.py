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