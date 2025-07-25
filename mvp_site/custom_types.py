"""
Shared type definitions for WorldArchitect.AI

This module contains common type definitions used across the application,
including TypedDicts for Firebase data structures, type aliases, and
protocol definitions for better type safety.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Protocol, TypedDict, Union


# Firebase/Firestore data structures
class CampaignData(TypedDict, total=False):
    """Type definition for campaign data stored in Firestore."""
    name: str
    prompt: str
    narrative: str
    entities: Dict[str, Any]
    state_updates: List[Dict[str, Any]]
    started: bool
    created_at: datetime
    updated_at: datetime
    user_id: str
    is_legacy: bool
    session_count: int


class StateUpdate(TypedDict):
    """Type definition for state update objects."""
    type: str
    key: str
    value: Union[str, int, float, bool, None]
    description: Optional[str]
    category: Optional[str]


class EntityData(TypedDict, total=False):
    """Type definition for entity data in campaigns."""
    name: str
    type: str
    description: str
    level: Optional[int]
    hp: Optional[int]
    max_hp: Optional[int]
    attributes: Dict[str, Union[str, int, float]]
    equipment: List[str]
    spells: List[str]
    location: Optional[str]


class MissionData(TypedDict):
    """Type definition for mission/quest data."""
    id: str
    title: str
    description: str
    status: Literal["active", "completed", "failed", "inactive"]
    objectives: List[str]
    rewards: Optional[List[str]]


class ApiResponse(TypedDict):
    """Standard API response structure."""
    success: bool
    message: Optional[str]
    data: Optional[Dict[str, Any]]
    error: Optional[str]


class GeminiRequest(TypedDict):
    """Type definition for Gemini API requests."""
    prompt: str
    max_tokens: Optional[int]
    temperature: Optional[float]
    response_mode: Literal["json", "text"]
    model: Optional[str]


class GeminiResponse(TypedDict):
    """Type definition for Gemini API responses."""
    text: str
    usage: Dict[str, int]
    model: str
    finish_reason: Optional[str]


# Type aliases
UserId = str
CampaignId = str
EntityId = str
SessionId = str
Timestamp = Union[datetime, float, int]

# JSON-compatible types
JsonValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JsonDict = Dict[str, JsonValue]


# Protocol definitions for better interface contracts
class DatabaseService(Protocol):
    """Protocol for database service implementations."""

    def get_campaign(self, user_id: UserId, campaign_id: CampaignId) -> Optional[CampaignData]:
        """Retrieve a campaign by ID."""
        ...

    def update_campaign(self, user_id: UserId, campaign_id: CampaignId, data: CampaignData) -> bool:
        """Update a campaign."""
        ...

    def delete_campaign(self, user_id: UserId, campaign_id: CampaignId) -> bool:
        """Delete a campaign."""
        ...


class AIService(Protocol):
    """Protocol for AI service implementations."""

    def generate_response(self, request: GeminiRequest) -> GeminiResponse:
        """Generate an AI response."""
        ...

    def validate_response(self, response: str) -> bool:
        """Validate an AI response."""
        ...


# Constants for type checking
VALID_ENTITY_TYPES = Literal["character", "npc", "creature", "location", "item"]
VALID_CAMPAIGN_STATES = Literal["active", "paused", "completed", "archived"]
VALID_LOG_LEVELS = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Helper type for nullable fields
Nullable = Union[Any, None]
