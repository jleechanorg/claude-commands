"""
Domain events for the Campaign aggregate.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..value_objects import CampaignId, SceneNumber, TurnNumber


@dataclass(frozen=True)
class CampaignEvent:
    """Base class for all campaign domain events."""
    campaign_id: CampaignId
    occurred_at: datetime


@dataclass(frozen=True)
class CampaignCreated(CampaignEvent):
    """Event raised when a new campaign is created."""
    title: str
    player_id: str
    genre: str
    tone: str
    attribute_system: str
    created_at: datetime
    
    def __post_init__(self):
        # Set occurred_at to created_at if not provided
        if not hasattr(self, 'occurred_at'):
            object.__setattr__(self, 'occurred_at', self.created_at)


@dataclass(frozen=True)
class SceneStarted(CampaignEvent):
    """Event raised when a new scene starts in a campaign."""
    scene_number: SceneNumber
    scene_description: str
    started_at: datetime
    
    def __post_init__(self):
        # Set occurred_at to started_at if not provided
        if not hasattr(self, 'occurred_at'):
            object.__setattr__(self, 'occurred_at', self.started_at)


@dataclass(frozen=True)
class TurnPlayed(CampaignEvent):
    """Event raised when a turn is played in a campaign."""
    scene_number: SceneNumber
    turn_number: TurnNumber
    player_input: str
    ai_response: str
    played_at: datetime
    
    def __post_init__(self):
        # Set occurred_at to played_at if not provided
        if not hasattr(self, 'occurred_at'):
            object.__setattr__(self, 'occurred_at', self.played_at)


@dataclass(frozen=True)
class CampaignCompleted(CampaignEvent):
    """Event raised when a campaign is completed."""
    final_scene: SceneNumber
    final_turn: TurnNumber
    final_narrative: str
    completed_at: datetime
    
    def __post_init__(self):
        # Set occurred_at to completed_at if not provided
        if not hasattr(self, 'occurred_at'):
            object.__setattr__(self, 'occurred_at', self.completed_at)


@dataclass(frozen=True)
class CampaignPaused(CampaignEvent):
    """Event raised when a campaign is paused."""
    paused_at: datetime
    
    def __post_init__(self):
        # Set occurred_at to paused_at if not provided
        if not hasattr(self, 'occurred_at'):
            object.__setattr__(self, 'occurred_at', self.paused_at)


@dataclass(frozen=True)
class CampaignResumed(CampaignEvent):
    """Event raised when a campaign is resumed."""
    resumed_at: datetime
    
    def __post_init__(self):
        # Set occurred_at to resumed_at if not provided
        if not hasattr(self, 'occurred_at'):
            object.__setattr__(self, 'occurred_at', self.resumed_at)


@dataclass(frozen=True)
class CampaignAbandoned(CampaignEvent):
    """Event raised when a campaign is abandoned."""
    abandoned_at: datetime
    reason: Optional[str] = None
    
    def __post_init__(self):
        # Set occurred_at to abandoned_at if not provided
        if not hasattr(self, 'occurred_at'):
            object.__setattr__(self, 'occurred_at', self.abandoned_at)