"""
Campaign command handlers.
"""
from typing import Dict, Any

from .base import CommandHandler, NotFoundError, ValidationError
from .campaign_commands import (
    CreateCampaignCommand,
    PlayTurnCommand,
    StartNewSceneCommand,
    PauseCampaignCommand,
    ResumeCampaignCommand,
    CompleteCampaignCommand,
    AbandonCampaignCommand,
    ToggleDebugModeCommand,
    DeleteCampaignCommand
)
from ...domain.campaign import (
    Campaign,
    CampaignId,
    CampaignRepository,
    CampaignNotFoundError
)


class CreateCampaignHandler(CommandHandler[CampaignId]):
    """Handler for creating new campaigns."""
    
    def __init__(self, repository: CampaignRepository):
        """
        Initialize the handler.
        
        Args:
            repository: The campaign repository
        """
        self._repository = repository
    
    async def handle(self, command: CreateCampaignCommand) -> CampaignId:
        """
        Create a new campaign.
        
        Args:
            command: The create campaign command
            
        Returns:
            The ID of the created campaign
            
        Raises:
            ValidationError: If the command data is invalid
        """
        # Validate command
        if not command.title or not command.title.strip():
            raise ValidationError("Campaign title cannot be empty")
        
        if not command.player_id:
            raise ValidationError("Player ID is required")
        
        # Create the campaign
        campaign = Campaign.create_new(
            title=command.title,
            player_id=command.player_id,
            genre=command.genre,
            tone=command.tone,
            attribute_system=command.attribute_system,
            debug_mode=command.debug_mode
        )
        
        # Save to repository
        await self._repository.save(campaign)
        
        # Return the campaign ID
        return campaign.id


class PlayTurnHandler(CommandHandler[Dict[str, Any]]):
    """Handler for playing turns in a campaign."""
    
    def __init__(
        self,
        repository: CampaignRepository,
        narrative_service: Any  # Will be defined later
    ):
        """
        Initialize the handler.
        
        Args:
            repository: The campaign repository
            narrative_service: Service for generating narrative responses
        """
        self._repository = repository
        self._narrative_service = narrative_service
    
    async def handle(self, command: PlayTurnCommand) -> Dict[str, Any]:
        """
        Play a turn in the campaign.
        
        Args:
            command: The play turn command
            
        Returns:
            Dict containing the AI response and updated game state
            
        Raises:
            NotFoundError: If the campaign is not found
        """
        # Load the campaign
        campaign = await self._repository.find_by_id(command.campaign_id)
        if not campaign:
            raise NotFoundError(f"Campaign not found: {command.campaign_id}")
        
        # Generate AI response (placeholder - will integrate with narrative service)
        # For now, return a simple response
        ai_response = f"[AI response to: {command.player_input}]"
        
        # Record the turn in the campaign
        campaign.play_turn(
            player_input=command.player_input,
            ai_response=ai_response
        )
        
        # Save the updated campaign
        await self._repository.save(campaign)
        
        # Return the response
        return {
            "campaign_id": str(campaign.id),
            "scene_number": campaign.current_scene.value,
            "turn_number": campaign.current_turn.value - 1,  # We just incremented it
            "player_input": command.player_input,
            "ai_response": ai_response,
            "god_mode": command.god_mode
        }


class StartNewSceneHandler(CommandHandler[None]):
    """Handler for starting new scenes."""
    
    def __init__(self, repository: CampaignRepository):
        """
        Initialize the handler.
        
        Args:
            repository: The campaign repository
        """
        self._repository = repository
    
    async def handle(self, command: StartNewSceneCommand) -> None:
        """
        Start a new scene in the campaign.
        
        Args:
            command: The start new scene command
            
        Raises:
            NotFoundError: If the campaign is not found
        """
        # Load the campaign
        campaign = await self._repository.find_by_id(command.campaign_id)
        if not campaign:
            raise NotFoundError(f"Campaign not found: {command.campaign_id}")
        
        # Start the new scene
        campaign.start_new_scene(command.scene_description)
        
        # Save the updated campaign
        await self._repository.save(campaign)


class PauseCampaignHandler(CommandHandler[None]):
    """Handler for pausing campaigns."""
    
    def __init__(self, repository: CampaignRepository):
        """
        Initialize the handler.
        
        Args:
            repository: The campaign repository
        """
        self._repository = repository
    
    async def handle(self, command: PauseCampaignCommand) -> None:
        """
        Pause a campaign.
        
        Args:
            command: The pause campaign command
            
        Raises:
            NotFoundError: If the campaign is not found
        """
        # Load the campaign
        campaign = await self._repository.find_by_id(command.campaign_id)
        if not campaign:
            raise NotFoundError(f"Campaign not found: {command.campaign_id}")
        
        # Pause the campaign
        campaign.pause()
        
        # Save the updated campaign
        await self._repository.save(campaign)


class ResumeCampaignHandler(CommandHandler[None]):
    """Handler for resuming campaigns."""
    
    def __init__(self, repository: CampaignRepository):
        """
        Initialize the handler.
        
        Args:
            repository: The campaign repository
        """
        self._repository = repository
    
    async def handle(self, command: ResumeCampaignCommand) -> None:
        """
        Resume a paused campaign.
        
        Args:
            command: The resume campaign command
            
        Raises:
            NotFoundError: If the campaign is not found
        """
        # Load the campaign
        campaign = await self._repository.find_by_id(command.campaign_id)
        if not campaign:
            raise NotFoundError(f"Campaign not found: {command.campaign_id}")
        
        # Resume the campaign
        campaign.resume()
        
        # Save the updated campaign
        await self._repository.save(campaign)


class CompleteCampaignHandler(CommandHandler[None]):
    """Handler for completing campaigns."""
    
    def __init__(self, repository: CampaignRepository):
        """
        Initialize the handler.
        
        Args:
            repository: The campaign repository
        """
        self._repository = repository
    
    async def handle(self, command: CompleteCampaignCommand) -> None:
        """
        Complete a campaign.
        
        Args:
            command: The complete campaign command
            
        Raises:
            NotFoundError: If the campaign is not found
        """
        # Load the campaign
        campaign = await self._repository.find_by_id(command.campaign_id)
        if not campaign:
            raise NotFoundError(f"Campaign not found: {command.campaign_id}")
        
        # Complete the campaign
        campaign.complete(command.final_narrative)
        
        # Save the updated campaign
        await self._repository.save(campaign)


class AbandonCampaignHandler(CommandHandler[None]):
    """Handler for abandoning campaigns."""
    
    def __init__(self, repository: CampaignRepository):
        """
        Initialize the handler.
        
        Args:
            repository: The campaign repository
        """
        self._repository = repository
    
    async def handle(self, command: AbandonCampaignCommand) -> None:
        """
        Abandon a campaign.
        
        Args:
            command: The abandon campaign command
            
        Raises:
            NotFoundError: If the campaign is not found
        """
        # Load the campaign
        campaign = await self._repository.find_by_id(command.campaign_id)
        if not campaign:
            raise NotFoundError(f"Campaign not found: {command.campaign_id}")
        
        # Abandon the campaign
        campaign.abandon()
        
        # Save the updated campaign
        await self._repository.save(campaign)


class ToggleDebugModeHandler(CommandHandler[bool]):
    """Handler for toggling debug mode."""
    
    def __init__(self, repository: CampaignRepository):
        """
        Initialize the handler.
        
        Args:
            repository: The campaign repository
        """
        self._repository = repository
    
    async def handle(self, command: ToggleDebugModeCommand) -> bool:
        """
        Toggle debug mode for a campaign.
        
        Args:
            command: The toggle debug mode command
            
        Returns:
            The new debug mode state
            
        Raises:
            NotFoundError: If the campaign is not found
        """
        # Load the campaign
        campaign = await self._repository.find_by_id(command.campaign_id)
        if not campaign:
            raise NotFoundError(f"Campaign not found: {command.campaign_id}")
        
        # Toggle debug mode
        campaign.toggle_debug_mode()
        
        # Save the updated campaign
        await self._repository.save(campaign)
        
        # Return the new state
        return campaign.debug_mode


class DeleteCampaignHandler(CommandHandler[None]):
    """Handler for deleting campaigns."""
    
    def __init__(self, repository: CampaignRepository):
        """
        Initialize the handler.
        
        Args:
            repository: The campaign repository
        """
        self._repository = repository
    
    async def handle(self, command: DeleteCampaignCommand) -> None:
        """
        Delete a campaign.
        
        Args:
            command: The delete campaign command
            
        Raises:
            NotFoundError: If the campaign is not found
            ValidationError: If the player doesn't own the campaign
        """
        # Load the campaign to verify ownership
        campaign = await self._repository.find_by_id(command.campaign_id)
        if not campaign:
            raise NotFoundError(f"Campaign not found: {command.campaign_id}")
        
        # Verify ownership
        if campaign.player_id != command.player_id:
            raise ValidationError("You can only delete your own campaigns")
        
        # Delete from repository
        deleted = await self._repository.delete(command.campaign_id)
        if not deleted:
            raise NotFoundError(f"Campaign not found: {command.campaign_id}")