"""
Campaign repository interfaces.
"""
from .campaign_repository import (
    CampaignRepository,
    RepositoryError,
    CampaignNotFoundError,
    CampaignAlreadyExistsError
)

__all__ = [
    'CampaignRepository',
    'RepositoryError',
    'CampaignNotFoundError',
    'CampaignAlreadyExistsError'
]