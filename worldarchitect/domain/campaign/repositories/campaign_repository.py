"""
Repository interface for Campaign aggregate.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.campaign import Campaign
from ..value_objects import CampaignId


class CampaignRepository(ABC):
    """
    Abstract repository interface for Campaign persistence.
    
    This interface defines the contract that infrastructure implementations
    must follow. The domain layer depends only on this interface, not on
    concrete implementations.
    """
    
    @abstractmethod
    async def save(self, campaign: Campaign) -> None:
        """
        Save a campaign to the repository.
        
        Args:
            campaign: The campaign to save
            
        Raises:
            RepositoryError: If the save operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, campaign_id: CampaignId) -> Optional[Campaign]:
        """
        Find a campaign by its ID.
        
        Args:
            campaign_id: The ID of the campaign to find
            
        Returns:
            The campaign if found, None otherwise
            
        Raises:
            RepositoryError: If the query fails
        """
        pass
    
    @abstractmethod
    async def find_by_player_id(self, player_id: str) -> List[Campaign]:
        """
        Find all campaigns for a specific player.
        
        Args:
            player_id: The ID of the player
            
        Returns:
            List of campaigns for the player (may be empty)
            
        Raises:
            RepositoryError: If the query fails
        """
        pass
    
    @abstractmethod
    async def find_active_by_player_id(self, player_id: str) -> List[Campaign]:
        """
        Find all active campaigns for a specific player.
        
        Args:
            player_id: The ID of the player
            
        Returns:
            List of active campaigns for the player (may be empty)
            
        Raises:
            RepositoryError: If the query fails
        """
        pass
    
    @abstractmethod
    async def delete(self, campaign_id: CampaignId) -> bool:
        """
        Delete a campaign from the repository.
        
        Args:
            campaign_id: The ID of the campaign to delete
            
        Returns:
            True if the campaign was deleted, False if not found
            
        Raises:
            RepositoryError: If the delete operation fails
        """
        pass
    
    @abstractmethod
    async def exists(self, campaign_id: CampaignId) -> bool:
        """
        Check if a campaign exists in the repository.
        
        Args:
            campaign_id: The ID of the campaign to check
            
        Returns:
            True if the campaign exists, False otherwise
            
        Raises:
            RepositoryError: If the query fails
        """
        pass


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class CampaignNotFoundError(RepositoryError):
    """Raised when a campaign is not found in the repository."""
    
    def __init__(self, campaign_id: CampaignId):
        super().__init__(f"Campaign not found: {campaign_id}")
        self.campaign_id = campaign_id


class CampaignAlreadyExistsError(RepositoryError):
    """Raised when trying to create a campaign that already exists."""
    
    def __init__(self, campaign_id: CampaignId):
        super().__init__(f"Campaign already exists: {campaign_id}")
        self.campaign_id = campaign_id