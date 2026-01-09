"""
Shared type definitions for WorldArchitect.AI

This module contains common type definitions used across the application,
including TypedDicts for Firebase data structures, type aliases, and
protocol definitions for better type safety.
"""

from datetime import datetime
from typing import Any, Literal, Optional, Protocol, TypedDict, Union


# Firebase/Firestore data structures
class CampaignData(TypedDict, total=False):
    """Type definition for campaign data stored in Firestore."""

    name: str
    prompt: str
    narrative: str
    entities: dict[str, Any]
    state_updates: list[dict[str, Any]]
    started: bool
    created_at: datetime
    updated_at: datetime
    user_id: str
    is_legacy: bool
    session_count: int


class StateUpdate(TypedDict, total=False):
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
    attributes: dict[str, Union[str, int, float]]
    equipment: list[str]
    spells: list[str]
    location: Optional[str]


class MissionData(TypedDict):
    """Type definition for mission/quest data."""

    id: str
    title: str
    description: str
    status: Literal["active", "completed", "failed", "inactive"]
    objectives: list[str]
    rewards: Optional[list[str]]


class ApiResponse(TypedDict):
    """Standard API response structure."""

    success: bool
    message: Optional[str]
    data: Optional[dict[str, Any]]
    error: Optional[str]


class LLMRequest(TypedDict):
    """Type definition for Gemini API requests."""

    prompt: str
    max_tokens: Optional[int]
    temperature: Optional[float]
    response_mode: Literal["json", "text"]
    model: Optional[str]


class LLMResponse(TypedDict):
    """Type definition for Gemini API responses."""

    text: str
    usage: dict[str, int]
    model: str
    finish_reason: Optional[str]


# Type aliases
UserId = str
CampaignId = str
EntityId = str
SessionId = str
Timestamp = Union[datetime, float, int]

# JSON-compatible types
JsonValue = Union[str, int, float, bool, None, dict[str, Any], list[Any]]
JsonDict = dict[str, JsonValue]


# Protocol definitions for better interface contracts
class DatabaseService(Protocol):
    """Protocol for database service implementations."""

    def get_campaign(
        self, user_id: UserId, campaign_id: CampaignId
    ) -> Optional[CampaignData]:
        """Retrieve a campaign by ID."""
        ...

    def update_campaign(
        self, user_id: UserId, campaign_id: CampaignId, updates: dict[str, Any]
    ) -> bool:
        """Update a campaign with the provided field changes."""
        ...

    def delete_campaign(self, user_id: UserId, campaign_id: CampaignId) -> bool:
        """Delete a campaign."""
        ...


class AIService(Protocol):
    """Protocol for AI service implementations."""

    def generate_response(self, request: LLMRequest) -> LLMResponse:
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
Nullable = Optional[Any]
