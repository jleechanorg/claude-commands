"""
Campaign bounded context - manages campaign lifecycle and state.
"""
from .entities import Campaign, CampaignStatus, AttributeSystem
from .value_objects import CampaignId, SceneNumber, TurnNumber
from .events import (
    CampaignEvent,
    CampaignCreated,
    SceneStarted,
    TurnPlayed,
    CampaignCompleted,
    CampaignPaused,
    CampaignResumed,
    CampaignAbandoned
)
from .repositories import (
    CampaignRepository,
    RepositoryError,
    CampaignNotFoundError,
    CampaignAlreadyExistsError
)

__all__ = [
    # Entities
    'Campaign',
    'CampaignStatus',
    'AttributeSystem',
    
    # Value Objects
    'CampaignId',
    'SceneNumber',
    'TurnNumber',
    
    # Events
    'CampaignEvent',
    'CampaignCreated',
    'SceneStarted',
    'TurnPlayed',
    'CampaignCompleted',
    'CampaignPaused',
    'CampaignResumed',
    'CampaignAbandoned',
    
    # Repository
    'CampaignRepository',
    'RepositoryError',
    'CampaignNotFoundError',
    'CampaignAlreadyExistsError'
]