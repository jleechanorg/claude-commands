"""
LLM Response classes for provider-agnostic response handling.

This module provides a unified interface for handling responses from different
LLM providers (Gemini, OpenAI, Claude, etc.) while maintaining backwards
compatibility with existing GeminiResponse usage.
"""

from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
from narrative_response_schema import NarrativeResponse


@dataclass
class LLMResponse(ABC):
    """
    Abstract base class for all LLM responses.
    
    Provides a unified interface for handling responses from any LLM provider
    while allowing provider-specific implementations.
    """
    
    # Core response content (required for all providers)
    narrative_text: str  # Clean narrative text for display
    provider: str        # LLM provider name (e.g., "gemini", "openai", "claude")
    model: str          # Specific model used (e.g., "gemini-2.5-flash")
    
    # Structured data (optional, depends on provider capabilities)
    structured_response: Optional[NarrativeResponse] = None
    
    # Debug and monitoring
    debug_tags_present: Dict[str, bool] = None
    processing_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if self.debug_tags_present is None:
            self.debug_tags_present = {}
        if self.processing_metadata is None:
            self.processing_metadata = {}
    
    @abstractmethod
    def get_state_updates(self) -> Dict[str, Any]:
        """Get state updates from the response."""
        pass
    
    @abstractmethod
    def get_entities_mentioned(self) -> List[str]:
        """Get entities mentioned in the response."""
        pass
    
    @abstractmethod
    def get_location_confirmed(self) -> str:
        """Get confirmed location from the response."""
        pass
    
    @abstractmethod
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information from the response."""
        pass
    
    @property
    def has_debug_content(self) -> bool:
        """Check if any debug content was generated."""
        return any(self.debug_tags_present.values()) if self.debug_tags_present else False
    
    @property
    def is_valid(self) -> bool:
        """Check if the response is valid and usable."""
        return bool(self.narrative_text and self.narrative_text.strip())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for API serialization."""
        return {
            'narrative_text': self.narrative_text,
            'provider': self.provider,
            'model': self.model,
            'state_updates': self.get_state_updates(),
            'entities_mentioned': self.get_entities_mentioned(),
            'location_confirmed': self.get_location_confirmed(),
            'debug_info': self.get_debug_info(),
            'has_debug_content': self.has_debug_content,
            'is_valid': self.is_valid
        }


@dataclass 
class GeminiLLMResponse(LLMResponse):
    """
    Gemini-specific implementation of LLMResponse.
    
    Maintains compatibility with existing GeminiResponse while implementing
    the unified LLMResponse interface.
    """
    
    def __post_init__(self):
        """Initialize Gemini-specific defaults."""
        super().__post_init__()
        if not self.provider:
            self.provider = "gemini"
        
        # Auto-detect debug tags if not provided
        if not self.debug_tags_present:
            self.debug_tags_present = self._detect_debug_tags()
    
    def _detect_debug_tags(self) -> Dict[str, bool]:
        """Detect debug content in structured response."""
        debug_tags = {
            'dm_notes': False,
            'dice_rolls': False, 
            'state_changes': False
        }
        
        if self.structured_response and hasattr(self.structured_response, 'debug_info'):
            debug_info = self.structured_response.debug_info or {}
            
            # Check for non-empty debug content
            debug_tags['dm_notes'] = bool(debug_info.get('dm_notes'))
            debug_tags['dice_rolls'] = bool(debug_info.get('dice_rolls'))
            # Check for state changes in the structured response
            debug_tags['state_changes'] = bool(self.structured_response.state_updates)
        
        return debug_tags
    
    @classmethod
    def create(cls, narrative_text: str, structured_response: Optional[NarrativeResponse], 
               model: str = "gemini-2.5-flash") -> 'GeminiLLMResponse':
        """
        Create a GeminiLLMResponse with automatic debug tag detection.
        
        Maintains compatibility with existing GeminiResponse.create() usage.
        """
        return cls(
            narrative_text=narrative_text,
            provider="gemini",
            model=model,
            structured_response=structured_response
        )
    
    def get_state_updates(self) -> Dict[str, Any]:
        """Get state updates from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'state_updates'):
            return self.structured_response.state_updates or {}
        
        # JSON mode is required - log error if no structured response
        if not self.structured_response:
            logging.error("ERROR: No structured response available for state updates. JSON mode is required.")
        return {}
    
    def get_entities_mentioned(self) -> List[str]:
        """Get entities mentioned from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'entities_mentioned'):
            return self.structured_response.entities_mentioned or []
        return []
    
    def get_location_confirmed(self) -> str:
        """Get confirmed location from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'location_confirmed'):
            return self.structured_response.location_confirmed or 'Unknown'
        return 'Unknown'
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug info from structured response."""
        if self.structured_response and hasattr(self.structured_response, 'debug_info'):
            return self.structured_response.debug_info or {}
        return {}


# Factory function for creating provider-specific responses
def create_llm_response(provider: str, narrative_text: str, 
                       model: str, structured_response: Optional[NarrativeResponse] = None,
                       **kwargs) -> LLMResponse:
    """
    Factory function to create appropriate LLMResponse subclass based on provider.
    
    Args:
        provider: LLM provider name ("gemini", "openai", "claude", etc.)
        narrative_text: Clean narrative text for display
        model: Specific model used
        structured_response: Parsed structured response (if available)
        **kwargs: Additional provider-specific arguments
        
    Returns:
        Appropriate LLMResponse subclass instance
        
    Raises:
        ValueError: If provider is not supported
    """
    provider = provider.lower()
    
    if provider == "gemini":
        return GeminiLLMResponse(
            narrative_text=narrative_text,
            provider=provider,
            model=model,
            structured_response=structured_response,
            **kwargs
        )
    else:
        # Future providers can be added here
        # elif provider == "openai":
        #     return OpenAILLMResponse(...)
        # elif provider == "claude":
        #     return ClaudeLLMResponse(...)
        raise ValueError(f"Unsupported LLM provider: {provider}")


# Backwards compatibility alias
# This allows existing code using GeminiResponse to continue working
class GeminiResponse(GeminiLLMResponse):
    """
    Backwards compatibility alias for GeminiLLMResponse.
    
    This allows existing code that imports and uses GeminiResponse
    to continue working without changes while providing the new
    unified interface.
    """
    pass