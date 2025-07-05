"""
Gemini Response objects for clean architecture between AI service and main application.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
from narrative_response_schema import NarrativeResponse


@dataclass
class GeminiResponse:
    """
    Clean response object from Gemini service to main application.
    
    Separates concerns between narrative text and structured data.
    """
    
    # Core response content
    narrative_text: str  # Clean narrative text for display (no debug tags)
    structured_response: Optional[NarrativeResponse]  # Parsed JSON structure
    
    # Debug monitoring data
    debug_tags_present: Dict[str, bool]  # Which debug content types were generated
    
    # Raw data (for compatibility/debugging)
    raw_response: str  # Original AI response before processing
    
    @classmethod
    def create(cls, narrative_text: str, structured_response: Optional[NarrativeResponse], 
               raw_response: str) -> 'GeminiResponse':
        """
        Create a GeminiResponse with automatic debug tag detection.
        
        Args:
            narrative_text: Clean narrative text for display
            structured_response: Parsed NarrativeResponse object
            raw_response: Original AI response before processing
            
        Returns:
            GeminiResponse object
        """
        # Detect debug content in structured response, not raw text
        debug_tags_present = {
            'dm_notes': False,
            'dice_rolls': False, 
            'state_changes': False
        }
        
        if structured_response and hasattr(structured_response, 'debug_info'):
            debug_info = structured_response.debug_info or {}
            
            # Check for non-empty debug content
            debug_tags_present['dm_notes'] = bool(debug_info.get('dm_notes'))
            debug_tags_present['dice_rolls'] = bool(debug_info.get('dice_rolls'))
            debug_tags_present['state_changes'] = '[DEBUG_STATE_START]' in raw_response
        
        return cls(
            narrative_text=narrative_text,
            structured_response=structured_response,
            debug_tags_present=debug_tags_present,
            raw_response=raw_response
        )
    
    @property
    def has_debug_content(self) -> bool:
        """Check if any debug content was generated."""
        return any(self.debug_tags_present.values())
    
    @property
    def state_updates(self) -> Dict[str, Any]:
        """Get state updates from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'state_updates'):
            return self.structured_response.state_updates or {}
        
        # JSON mode is the ONLY mode - log error if no structured response
        if not self.structured_response:
            logging.error("ERROR: No structured response available for state updates. JSON mode is required.")
        return {}
    
    @property
    def entities_mentioned(self) -> List[str]:
        """Get entities mentioned from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'entities_mentioned'):
            return self.structured_response.entities_mentioned or []
        return []
    
    @property
    def location_confirmed(self) -> str:
        """Get confirmed location from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'location_confirmed'):
            return self.structured_response.location_confirmed or 'Unknown'
        return 'Unknown'
    
    @property
    def debug_info(self) -> Dict[str, Any]:
        """Get debug info from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'debug_info'):
            return self.structured_response.debug_info or {}
        return {}