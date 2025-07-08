"""
Campaign-related commands.
"""
from dataclasses import dataclass
from typing import Optional

from .base import Command
from ...domain.campaign import CampaignId


@dataclass(frozen=True)
class CreateCampaignCommand(Command):
    """Command to create a new campaign."""
    title: str
    player_id: str
    genre: str
    tone: str
    attribute_system: str = "D&D"
    debug_mode: bool = True
    character_name: Optional[str] = None
    character_background: Optional[str] = None
    custom_instructions: Optional[str] = None


@dataclass(frozen=True)
class PlayTurnCommand(Command):
    """Command to play a turn in a campaign."""
    campaign_id: CampaignId
    player_input: str
    god_mode: bool = False


@dataclass(frozen=True)
class StartNewSceneCommand(Command):
    """Command to start a new scene in a campaign."""
    campaign_id: CampaignId
    scene_description: str


@dataclass(frozen=True)
class SaveGameCommand(Command):
    """Command to save the current game state."""
    campaign_id: CampaignId


@dataclass(frozen=True)
class LoadGameCommand(Command):
    """Command to load a saved game."""
    campaign_id: CampaignId
    player_id: str


@dataclass(frozen=True)
class PauseCampaignCommand(Command):
    """Command to pause a campaign."""
    campaign_id: CampaignId


@dataclass(frozen=True)
class ResumeCampaignCommand(Command):
    """Command to resume a paused campaign."""
    campaign_id: CampaignId


@dataclass(frozen=True)
class CompleteCampaignCommand(Command):
    """Command to complete a campaign."""
    campaign_id: CampaignId
    final_narrative: str


@dataclass(frozen=True)
class AbandonCampaignCommand(Command):
    """Command to abandon a campaign."""
    campaign_id: CampaignId
    reason: Optional[str] = None


@dataclass(frozen=True)
class ToggleDebugModeCommand(Command):
    """Command to toggle debug mode for a campaign."""
    campaign_id: CampaignId


@dataclass(frozen=True)
class DeleteCampaignCommand(Command):
    """Command to delete a campaign."""
    campaign_id: CampaignId
    player_id: str  # For authorization