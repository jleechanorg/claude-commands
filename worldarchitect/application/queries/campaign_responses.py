"""
Response DTOs for campaign queries.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class CampaignDTO:
    """Data transfer object for campaign data."""
    id: str
    title: str
    player_id: str
    genre: str
    tone: str
    attribute_system: str
    status: str
    current_scene: int
    current_turn: int
    debug_mode: bool
    created_at: datetime
    last_played_at: datetime


@dataclass(frozen=True)
class CampaignListItemDTO:
    """Simplified DTO for campaign lists."""
    id: str
    title: str
    genre: str
    status: str
    current_scene: int
    last_played_at: datetime


@dataclass(frozen=True)
class CampaignHistoryTurnDTO:
    """DTO for a single turn in campaign history."""
    scene_number: int
    turn_number: int
    player_input: str
    ai_response: str
    played_at: datetime


@dataclass(frozen=True)
class CampaignHistoryDTO:
    """DTO for campaign history."""
    campaign_id: str
    campaign_title: str
    turns: List[CampaignHistoryTurnDTO]
    total_turns: int
    scene_count: int


@dataclass(frozen=True)
class CampaignStatsDTO:
    """DTO for campaign statistics."""
    campaign_id: str
    campaign_title: str
    total_scenes: int
    total_turns: int
    average_turns_per_scene: float
    total_play_time: Optional[float]  # In hours
    status: str
    created_at: datetime
    last_played_at: datetime
    completion_percentage: Optional[float]  # For tracking progress


@dataclass(frozen=True)
class CampaignSearchResultDTO:
    """DTO for campaign search results."""
    campaigns: List[CampaignListItemDTO]
    total_count: int
    offset: int
    limit: int
    has_more: bool