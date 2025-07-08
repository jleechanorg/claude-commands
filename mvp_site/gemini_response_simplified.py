"""
Simplified GeminiResponse class for clean debug content handling.

This replaces the complex hierarchy of LLMResponse -> GeminiLLMResponse -> GeminiResponse
with a single, clear class that properly separates narrative from debug content.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
import re
from narrative_response_schema import NarrativeResponse


@dataclass
class GeminiResponse:
    """
    Simplified response class that properly handles debug content separation.
    
    Key responsibilities:
    1. Extract clean narrative text (no debug tags)
    2. Preserve structured response data (debug_info, state_updates, etc.)
    3. Provide backward compatibility for existing code
    """
    
    # Core content
    narrative_text: str  # Clean narrative text for display (no debug tags)
    model: str = "gemini-2.5-flash"
    provider: str = "gemini"
    
    # Structured data from JSON response
    structured_response: Optional[NarrativeResponse] = None
    
    # Legacy compatibility
    debug_tags_present: Optional[Dict[str, bool]] = None
    processing_metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.debug_tags_present is None:
            self.debug_tags_present = {}
        if self.processing_metadata is None:
            self.processing_metadata = {}
    
    @classmethod
    def create_from_structured_response(cls, structured_response: NarrativeResponse, 
                                      model: str = "gemini-2.5-flash") -> 'GeminiResponse':
        """
        Create GeminiResponse from structured JSON response.
        
        This is the new preferred way to create responses that properly separates
        narrative from debug content.
        """
        # Extract clean narrative from structured response
        clean_narrative = structured_response.narrative
        
        # Remove any remaining debug tags from narrative
        clean_narrative = cls._strip_debug_tags(clean_narrative)
        
        return cls(
            narrative_text=clean_narrative,
            model=model,
            structured_response=structured_response,
            debug_tags_present=cls._detect_debug_tags(structured_response.narrative),
        )
    
    @classmethod
    def create_legacy(cls, narrative_text: str, model: str = "gemini-2.5-flash") -> 'GeminiResponse':
        """
        Create GeminiResponse from plain text (legacy support).
        
        This handles old-style responses that embed debug content in the narrative.
        """
        clean_narrative = cls._strip_debug_tags(narrative_text)
        
        return cls(
            narrative_text=clean_narrative,
            model=model,
            debug_tags_present=cls._detect_debug_tags(narrative_text),
        )
    
    @staticmethod
    def _strip_debug_tags(text: str) -> str:
        """Remove all debug tags from text."""
        if not text:
            return text
        
        # Remove [Mode: STORY MODE] prefix
        text = re.sub(r'^\[Mode:\s*[A-Z\s]+\]\s*\n*', '', text)
        
        # Remove embedded JSON objects (malformed responses)
        text = re.sub(r'\{[^}]*"session_header"[^}]*\}[^"]*"[^"]*"', '', text, flags=re.DOTALL)
        
        # Remove [DEBUG_START]...[DEBUG_END] blocks
        text = re.sub(r'\[DEBUG_START\].*?\[DEBUG_END\]', '', text, flags=re.DOTALL)
        
        # Remove [SESSION_HEADER] blocks (if they exist in narrative) - be more aggressive
        text = re.sub(r'\[SESSION_HEADER\].*?(?=\n\n[A-Z]|\n\n[A-S]|\n\nT|\n\nU|\n\nV|\n\nW|\n\nX|\n\nY|\n\nZ|\n[A-Z][a-z])', '', text, flags=re.DOTALL)
        
        # Remove --- PLANNING BLOCK --- sections (if they exist in narrative)
        text = re.sub(r'--- PLANNING BLOCK ---.*?$', '', text, flags=re.DOTALL)
        
        # Remove [STATE_UPDATES_PROPOSED] blocks
        text = re.sub(r'\[STATE_UPDATES_PROPOSED\].*?\[END_STATE_UPDATES_PROPOSED\]', '', text, flags=re.DOTALL)
        
        # Remove other debug markers
        text = re.sub(r'\[DEBUG_[A-Z_]+\].*?\[DEBUG_[A-Z_]+\]', '', text, flags=re.DOTALL)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def _detect_debug_tags(text: str) -> Dict[str, bool]:
        """Detect which debug tags are present in text."""
        if not text:
            return {}
        
        return {
            'debug_start_end': '[DEBUG_START]' in text and '[DEBUG_END]' in text,
            'session_header': '[SESSION_HEADER]' in text,
            'planning_block': '--- PLANNING BLOCK ---' in text,
            'state_updates': '[STATE_UPDATES_PROPOSED]' in text,
            'debug_rolls': '[DEBUG_ROLL_START]' in text,
        }
    
    # Property accessors for backward compatibility and new fields
    @property
    def state_updates(self) -> Dict[str, Any]:
        """Get state updates from structured response."""
        if self.structured_response:
            return self.structured_response.state_updates or {}
        return {}
    
    @property
    def entities_mentioned(self) -> List[str]:
        """Get entities mentioned from structured response."""
        if self.structured_response:
            return self.structured_response.entities_mentioned or []
        return []
    
    @property
    def location_confirmed(self) -> str:
        """Get location from structured response."""
        if self.structured_response:
            return self.structured_response.location_confirmed or "Unknown"
        return "Unknown"
    
    @property
    def debug_info(self) -> Dict[str, Any]:
        """Get debug info from structured response."""
        if self.structured_response:
            return self.structured_response.debug_info or {}
        return {}
    
    @property
    def session_header(self) -> str:
        """Get session header from structured response."""
        if self.structured_response:
            return self.structured_response.session_header or ""
        return ""
    
    @property
    def planning_block(self) -> str:
        """Get planning block from structured response."""
        if self.structured_response:
            return self.structured_response.planning_block or ""
        return ""
    
    @property
    def dice_rolls(self) -> List[str]:
        """Get dice rolls from structured response."""
        if self.structured_response:
            return self.structured_response.dice_rolls or []
        return []
    
    @property
    def resources(self) -> str:
        """Get resources from structured response."""
        if self.structured_response:
            return self.structured_response.resources or ""
        return ""
    
    def get_narrative_text(self, debug_mode: bool = False) -> str:
        """
        Get narrative text for display.
        
        Args:
            debug_mode: If True, may include debug content (legacy compatibility)
        
        Returns:
            Clean narrative text
        """
        return self.narrative_text
    
    def has_debug_content(self) -> bool:
        """Check if response has any debug content."""
        return any(self.debug_tags_present.values()) or bool(self.debug_info)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            'narrative_text': self.narrative_text,
            'model': self.model,
            'provider': self.provider,
            'debug_tags_present': self.debug_tags_present,
            'processing_metadata': self.processing_metadata,
        }
        
        if self.structured_response:
            result['structured_response'] = self.structured_response.to_dict()
        
        return result