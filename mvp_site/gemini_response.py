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
    
    @property
    def session_header(self) -> str:
        """Get session header from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'session_header'):
            return self.structured_response.session_header or ""
        return ""
    
    @property
    def planning_block(self) -> str:
        """Get planning block from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'planning_block'):
            return self.structured_response.planning_block or ""
        return ""
    
    @property
    def dice_rolls(self) -> List[str]:
        """Get dice rolls from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'dice_rolls'):
            return self.structured_response.dice_rolls or []
        return []
    
    @property
    def resources(self) -> str:
        """Get resources from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'resources'):
            return self.structured_response.resources or ""
        return ""
    
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
        if self.debug_tags_present and any(self.debug_tags_present.values()):
            return True
        
        return False
    
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
    
    @staticmethod
    def _strip_all_debug_tags(text: str) -> str:
        """Remove all debug tags from text."""
        if not text:
            return text
        
        # Remove [Mode: STORY MODE] prefix
        text = re.sub(r'^\[Mode:\s*[A-Z\s]+\]\s*\n*', '', text)
        
        # Remove embedded JSON objects (malformed responses)
        text = re.sub(r'\{[^}]*"session_header"[^}]*\}[^"]*"[^"]*"', '', text, flags=re.DOTALL)
        
        # Remove [DEBUG_START]...[DEBUG_END] blocks
        text = re.sub(r'\[DEBUG_START\].*?\[DEBUG_END\]', '', text, flags=re.DOTALL)
        
        # Remove [SESSION_HEADER] blocks (if they exist in narrative)
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
    def _detect_debug_tags_static(text: str) -> Dict[str, bool]:
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
        
        # If we have a structured response, use the new method
        if structured_response:
            return cls.create_from_structured_response(structured_response, model, narrative_text)
        
        # Otherwise fall back to legacy mode
        return cls.create_legacy(narrative_text, model)
    
    @classmethod
    def create_from_structured_response(cls, structured_response: NarrativeResponse, 
                                      model: str = "gemini-2.5-flash", 
                                      combined_narrative_text: str = None) -> 'GeminiResponse':
        """
        Create GeminiResponse from structured JSON response.
        
        This is the new preferred way to create responses that properly separates
        narrative from debug content.
        
        Args:
            structured_response: Parsed NarrativeResponse object
            model: Model name used for generation
            combined_narrative_text: The combined narrative text (including god_mode_response if present)
            
        Returns:
            GeminiResponse with clean narrative and structured data
        """
        # Use the combined narrative text if provided (includes god_mode_response)
        # Otherwise extract clean narrative from structured response
        clean_narrative = combined_narrative_text if combined_narrative_text is not None else structured_response.narrative
        
        # Remove any remaining debug tags from narrative using static method
        clean_narrative = cls._strip_all_debug_tags(clean_narrative)
        
        # Detect debug tags from structured response content
        debug_tags = {
            'dm_notes': False,
            'dice_rolls': False,
            'state_changes': False
        }
        
        if structured_response:
            debug_info = structured_response.debug_info or {}
            # Check for non-empty debug content
            debug_tags['dm_notes'] = bool(debug_info.get('dm_notes'))
            debug_tags['dice_rolls'] = bool(debug_info.get('dice_rolls'))
            # Check for state changes
            debug_tags['state_changes'] = bool(structured_response.state_updates)
        
        return cls(
            narrative_text=clean_narrative,
            model=model,
            provider="gemini",
            structured_response=structured_response,
            debug_tags_present=debug_tags,
        )
    
    @classmethod
    def create_legacy(cls, narrative_text: str, model: str = "gemini-2.5-flash",
                     structured_response: Optional[NarrativeResponse] = None) -> 'GeminiResponse':
        """
        Create GeminiResponse from plain text (legacy support).
        
        This handles old-style responses that embed debug content in the narrative.
        
        Args:
            narrative_text: Raw narrative text (may contain debug tags)
            model: Model name used for generation
            structured_response: Optional structured response object
            
        Returns:
            GeminiResponse with debug content stripped from narrative
        """
        clean_narrative = cls._strip_all_debug_tags(narrative_text)
        
        return cls(
            narrative_text=clean_narrative,
            model=model,
            provider="gemini",
            structured_response=structured_response,
            debug_tags_present=cls._detect_debug_tags_static(narrative_text),
        )