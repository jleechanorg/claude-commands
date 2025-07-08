"""
Campaign entity - the core aggregate root for campaign management.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum

from ..value_objects import CampaignId, SceneNumber, TurnNumber
from ..events import CampaignCreated, SceneStarted, TurnPlayed, CampaignCompleted


class CampaignStatus(Enum):
    """Represents the current status of a campaign."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class AttributeSystem(Enum):
    """Supported attribute systems for campaigns."""
    DND = "D&D"
    DESTINY = "Destiny"
    CUSTOM = "Custom"


class Campaign:
    """
    The Campaign aggregate root.
    
    This is the main entity for managing campaign state, enforcing business rules,
    and raising domain events. It represents a single tabletop RPG campaign.
    """
    
    def __init__(
        self,
        campaign_id: CampaignId,
        title: str,
        player_id: str,
        genre: str,
        tone: str,
        attribute_system: AttributeSystem = AttributeSystem.DND,
        debug_mode: bool = True,
        created_at: Optional[datetime] = None
    ):
        """
        Initialize a new Campaign.
        
        Args:
            campaign_id: Unique identifier for the campaign
            title: Campaign title
            player_id: ID of the player who owns this campaign
            genre: Campaign genre (e.g., "Fantasy", "Sci-Fi")
            tone: Campaign tone (e.g., "Serious", "Comedic")
            attribute_system: The game system to use
            debug_mode: Whether debug mode is enabled
            created_at: When the campaign was created (defaults to now)
        """
        # Identity
        self._id = campaign_id
        self._player_id = player_id
        
        # Campaign metadata
        self._title = title
        self._genre = genre
        self._tone = tone
        self._attribute_system = attribute_system
        self._debug_mode = debug_mode
        
        # State tracking
        self._status = CampaignStatus.ACTIVE
        self._current_scene = SceneNumber.first()
        self._current_turn = TurnNumber.first()
        
        # Timestamps
        self._created_at = created_at or datetime.now(timezone.utc)
        self._last_played_at = self._created_at
        
        # Domain events
        self._events: List[Any] = []
        self._raise_event(CampaignCreated(
            campaign_id=campaign_id,
            title=title,
            player_id=player_id,
            genre=genre,
            tone=tone,
            attribute_system=attribute_system.value,
            created_at=self._created_at,
            occurred_at=self._created_at
        ))
    
    # Identity and metadata properties
    
    @property
    def id(self) -> CampaignId:
        """Get the campaign ID."""
        return self._id
    
    @property
    def player_id(self) -> str:
        """Get the player ID who owns this campaign."""
        return self._player_id
    
    @property
    def title(self) -> str:
        """Get the campaign title."""
        return self._title
    
    @property
    def genre(self) -> str:
        """Get the campaign genre."""
        return self._genre
    
    @property
    def tone(self) -> str:
        """Get the campaign tone."""
        return self._tone
    
    @property
    def attribute_system(self) -> AttributeSystem:
        """Get the attribute system."""
        return self._attribute_system
    
    @property
    def debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self._debug_mode
    
    # State properties
    
    @property
    def status(self) -> CampaignStatus:
        """Get the current campaign status."""
        return self._status
    
    @property
    def current_scene(self) -> SceneNumber:
        """Get the current scene number."""
        return self._current_scene
    
    @property
    def current_turn(self) -> TurnNumber:
        """Get the current turn number within the scene."""
        return self._current_turn
    
    @property
    def created_at(self) -> datetime:
        """Get when the campaign was created."""
        return self._created_at
    
    @property
    def last_played_at(self) -> datetime:
        """Get when the campaign was last played."""
        return self._last_played_at
    
    # Business operations
    
    def play_turn(self, player_input: str, ai_response: str) -> None:
        """
        Record that a turn has been played.
        
        Args:
            player_input: The player's input for this turn
            ai_response: The AI's narrative response
            
        Raises:
            ValueError: If the campaign is not active
        """
        if self._status != CampaignStatus.ACTIVE:
            raise ValueError(f"Cannot play turn in {self._status.value} campaign")
        
        # Raise the turn played event
        now = datetime.now(timezone.utc)
        self._raise_event(TurnPlayed(
            campaign_id=self._id,
            scene_number=self._current_scene,
            turn_number=self._current_turn,
            player_input=player_input,
            ai_response=ai_response,
            played_at=now,
            occurred_at=now
        ))
        
        # Update state
        self._current_turn = self._current_turn.next()
        self._last_played_at = now
    
    def start_new_scene(self, scene_description: str) -> None:
        """
        Start a new scene in the campaign.
        
        Args:
            scene_description: Description of the new scene
            
        Raises:
            ValueError: If the campaign is not active
        """
        if self._status != CampaignStatus.ACTIVE:
            raise ValueError(f"Cannot start new scene in {self._status.value} campaign")
        
        # Move to next scene
        self._current_scene = self._current_scene.next()
        self._current_turn = TurnNumber.first()
        
        # Raise the scene started event
        now = datetime.now(timezone.utc)
        self._raise_event(SceneStarted(
            campaign_id=self._id,
            scene_number=self._current_scene,
            scene_description=scene_description,
            started_at=now,
            occurred_at=now
        ))
        
        self._last_played_at = now
    
    def pause(self) -> None:
        """
        Pause the campaign.
        
        Raises:
            ValueError: If the campaign is not active
        """
        if self._status != CampaignStatus.ACTIVE:
            raise ValueError(f"Cannot pause {self._status.value} campaign")
        
        self._status = CampaignStatus.PAUSED
        self._last_played_at = datetime.now(timezone.utc)
    
    def resume(self) -> None:
        """
        Resume a paused campaign.
        
        Raises:
            ValueError: If the campaign is not paused
        """
        if self._status != CampaignStatus.PAUSED:
            raise ValueError(f"Cannot resume {self._status.value} campaign")
        
        self._status = CampaignStatus.ACTIVE
        self._last_played_at = datetime.now(timezone.utc)
    
    def complete(self, final_narrative: str) -> None:
        """
        Mark the campaign as completed.
        
        Args:
            final_narrative: The final narrative to end the campaign
            
        Raises:
            ValueError: If the campaign is not active
        """
        if self._status != CampaignStatus.ACTIVE:
            raise ValueError(f"Cannot complete {self._status.value} campaign")
        
        self._status = CampaignStatus.COMPLETED
        now = datetime.now(timezone.utc)
        self._last_played_at = now
        
        self._raise_event(CampaignCompleted(
            campaign_id=self._id,
            final_scene=self._current_scene,
            final_turn=self._current_turn,
            final_narrative=final_narrative,
            completed_at=now,
            occurred_at=now
        ))
    
    def abandon(self) -> None:
        """
        Abandon the campaign.
        
        Raises:
            ValueError: If the campaign is already completed
        """
        if self._status == CampaignStatus.COMPLETED:
            raise ValueError("Cannot abandon completed campaign")
        
        self._status = CampaignStatus.ABANDONED
        self._last_played_at = datetime.now(timezone.utc)
    
    def toggle_debug_mode(self) -> None:
        """Toggle debug mode on/off."""
        self._debug_mode = not self._debug_mode
    
    # Event handling
    
    def _raise_event(self, event: Any) -> None:
        """
        Raise a domain event.
        
        Args:
            event: The domain event to raise
        """
        self._events.append(event)
    
    def collect_events(self) -> List[Any]:
        """
        Collect and clear all raised events.
        
        Returns:
            List of domain events that were raised
        """
        events = self._events.copy()
        self._events.clear()
        return events
    
    # Factory method
    
    @classmethod
    def create_new(
        cls,
        title: str,
        player_id: str,
        genre: str,
        tone: str,
        attribute_system: str = "D&D",
        debug_mode: bool = True
    ) -> 'Campaign':
        """
        Factory method to create a new campaign.
        
        Args:
            title: Campaign title
            player_id: ID of the player creating the campaign
            genre: Campaign genre
            tone: Campaign tone
            attribute_system: Name of the attribute system to use
            debug_mode: Whether to enable debug mode
            
        Returns:
            A new Campaign instance
        """
        # Generate a new ID
        campaign_id = CampaignId.generate()
        
        # Convert string to enum
        try:
            system_enum = AttributeSystem(attribute_system)
        except ValueError:
            system_enum = AttributeSystem.CUSTOM
        
        return cls(
            campaign_id=campaign_id,
            title=title,
            player_id=player_id,
            genre=genre,
            tone=tone,
            attribute_system=system_enum,
            debug_mode=debug_mode
        )