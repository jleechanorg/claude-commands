"""
Campaign-related queries.
"""
from dataclasses import dataclass
from typing import Optional

from .base import Query
from ...domain.campaign import CampaignId


@dataclass(frozen=True)
class GetCampaignQuery(Query):
    """Query to get a specific campaign."""
    campaign_id: CampaignId
    player_id: str  # For authorization


@dataclass(frozen=True)
class ListCampaignsQuery(Query):
    """Query to list campaigns for a player."""
    player_id: str
    include_completed: bool = True
    include_abandoned: bool = False
    limit: Optional[int] = None
    offset: Optional[int] = None


@dataclass(frozen=True)
class GetActiveCampaignsQuery(Query):
    """Query to get only active campaigns for a player."""
    player_id: str
    limit: Optional[int] = None


@dataclass(frozen=True)
class GetCampaignHistoryQuery(Query):
    """Query to get the history of a campaign."""
    campaign_id: CampaignId
    player_id: str  # For authorization
    scene_number: Optional[int] = None  # If specified, get only this scene
    limit: Optional[int] = None  # Max number of turns to return


@dataclass(frozen=True)
class GetCampaignStatsQuery(Query):
    """Query to get statistics about a campaign."""
    campaign_id: CampaignId
    player_id: str  # For authorization


@dataclass(frozen=True)
class SearchCampaignsQuery(Query):
    """Query to search campaigns by various criteria."""
    player_id: str
    search_term: Optional[str] = None
    genre: Optional[str] = None
    status: Optional[str] = None
    created_after: Optional[str] = None  # ISO date string
    created_before: Optional[str] = None  # ISO date string
    limit: Optional[int] = None
    offset: Optional[int] = None