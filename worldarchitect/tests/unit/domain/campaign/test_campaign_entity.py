"""
Unit tests for Campaign entity.
"""
import pytest
from datetime import datetime
from worldarchitect.domain.campaign import (
    Campaign, CampaignStatus, AttributeSystem,
    CampaignId, SceneNumber, TurnNumber,
    CampaignCreated, SceneStarted, TurnPlayed, CampaignCompleted
)


class TestCampaignEntity:
    """Tests for Campaign entity."""
    
    def test_create_new_campaign(self):
        """Test creating a new campaign."""
        campaign = Campaign.create_new(
            title="Epic Adventure",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic",
            attribute_system="D&D",
            debug_mode=True
        )
        
        assert campaign.title == "Epic Adventure"
        assert campaign.player_id == "player-123"
        assert campaign.genre == "Fantasy"
        assert campaign.tone == "Heroic"
        assert campaign.attribute_system == AttributeSystem.DND
        assert campaign.debug_mode is True
        assert campaign.status == CampaignStatus.ACTIVE
        assert campaign.current_scene == SceneNumber.first()
        assert campaign.current_turn == TurnNumber.first()
        
        # Should have raised a creation event
        events = campaign.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], CampaignCreated)
        assert events[0].title == "Epic Adventure"
    
    def test_create_campaign_with_custom_attribute_system(self):
        """Test creating a campaign with a custom attribute system."""
        campaign = Campaign.create_new(
            title="Custom Game",
            player_id="player-123",
            genre="Sci-Fi",
            tone="Dark",
            attribute_system="Unknown System"
        )
        
        assert campaign.attribute_system == AttributeSystem.CUSTOM
    
    def test_play_turn_in_active_campaign(self):
        """Test playing a turn in an active campaign."""
        campaign = Campaign.create_new(
            title="Test Campaign",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic"
        )
        campaign.collect_events()  # Clear creation event
        
        # Play a turn
        campaign.play_turn(
            player_input="I attack the goblin",
            ai_response="You swing your sword at the goblin..."
        )
        
        # Turn should advance
        assert campaign.current_turn.value == 2
        
        # Should have raised a turn played event
        events = campaign.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], TurnPlayed)
        assert events[0].player_input == "I attack the goblin"
        assert events[0].scene_number.value == 1
        assert events[0].turn_number.value == 1
    
    def test_cannot_play_turn_in_paused_campaign(self):
        """Test that turns cannot be played in a paused campaign."""
        campaign = Campaign.create_new(
            title="Test Campaign",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic"
        )
        campaign.pause()
        
        with pytest.raises(ValueError, match="Cannot play turn in paused campaign"):
            campaign.play_turn("input", "response")
    
    def test_start_new_scene(self):
        """Test starting a new scene."""
        campaign = Campaign.create_new(
            title="Test Campaign",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic"
        )
        campaign.collect_events()  # Clear creation event
        
        # Play some turns in scene 1
        campaign.play_turn("turn 1", "response 1")
        campaign.play_turn("turn 2", "response 2")
        
        # Start new scene
        campaign.start_new_scene("The party enters the dark forest...")
        
        # Should be in scene 2, turn 1
        assert campaign.current_scene.value == 2
        assert campaign.current_turn.value == 1
        
        # Should have raised appropriate events
        events = campaign.collect_events()
        assert len(events) == 3  # 2 turns + 1 scene
        assert isinstance(events[2], SceneStarted)
        assert events[2].scene_number.value == 2
        assert events[2].scene_description == "The party enters the dark forest..."
    
    def test_pause_and_resume_campaign(self):
        """Test pausing and resuming a campaign."""
        campaign = Campaign.create_new(
            title="Test Campaign",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic"
        )
        
        # Pause the campaign
        campaign.pause()
        assert campaign.status == CampaignStatus.PAUSED
        
        # Cannot pause an already paused campaign
        with pytest.raises(ValueError, match="Cannot pause paused campaign"):
            campaign.pause()
        
        # Resume the campaign
        campaign.resume()
        assert campaign.status == CampaignStatus.ACTIVE
        
        # Cannot resume an active campaign
        with pytest.raises(ValueError, match="Cannot resume active campaign"):
            campaign.resume()
    
    def test_complete_campaign(self):
        """Test completing a campaign."""
        campaign = Campaign.create_new(
            title="Test Campaign",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic"
        )
        campaign.collect_events()  # Clear creation event
        
        # Play some content
        campaign.play_turn("turn 1", "response 1")
        campaign.start_new_scene("Scene 2")
        campaign.play_turn("turn 2", "response 2")
        
        # Complete the campaign
        final_narrative = "And so the heroes saved the kingdom..."
        campaign.complete(final_narrative)
        
        assert campaign.status == CampaignStatus.COMPLETED
        
        # Should have raised completion event
        events = campaign.collect_events()
        completion_event = events[-1]
        assert isinstance(completion_event, CampaignCompleted)
        assert completion_event.final_scene.value == 2
        assert completion_event.final_turn.value == 2
        assert completion_event.final_narrative == final_narrative
        
        # Cannot complete an already completed campaign
        with pytest.raises(ValueError, match="Cannot complete completed campaign"):
            campaign.complete("Another ending")
    
    def test_abandon_campaign(self):
        """Test abandoning a campaign."""
        campaign = Campaign.create_new(
            title="Test Campaign",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic"
        )
        
        # Can abandon active campaign
        campaign.abandon()
        assert campaign.status == CampaignStatus.ABANDONED
        
        # Can abandon paused campaign
        campaign2 = Campaign.create_new(
            title="Test Campaign 2",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic"
        )
        campaign2.pause()
        campaign2.abandon()
        assert campaign2.status == CampaignStatus.ABANDONED
        
        # Cannot abandon completed campaign
        campaign3 = Campaign.create_new(
            title="Test Campaign 3",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic"
        )
        campaign3.complete("The end")
        
        with pytest.raises(ValueError, match="Cannot abandon completed campaign"):
            campaign3.abandon()
    
    def test_toggle_debug_mode(self):
        """Test toggling debug mode."""
        campaign = Campaign.create_new(
            title="Test Campaign",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic",
            debug_mode=True
        )
        
        assert campaign.debug_mode is True
        
        campaign.toggle_debug_mode()
        assert campaign.debug_mode is False
        
        campaign.toggle_debug_mode()
        assert campaign.debug_mode is True
    
    def test_last_played_at_updates(self):
        """Test that last_played_at timestamp updates with activity."""
        campaign = Campaign.create_new(
            title="Test Campaign",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic"
        )
        
        initial_time = campaign.last_played_at
        
        # Play a turn should update timestamp
        campaign.play_turn("input", "response")
        assert campaign.last_played_at >= initial_time
        
        turn_time = campaign.last_played_at
        
        # Start new scene should update timestamp
        campaign.start_new_scene("New scene")
        assert campaign.last_played_at >= turn_time
    
    def test_events_are_collected_and_cleared(self):
        """Test that events are properly collected and cleared."""
        campaign = Campaign.create_new(
            title="Test Campaign",
            player_id="player-123",
            genre="Fantasy",
            tone="Heroic"
        )
        
        # Should have creation event
        events1 = campaign.collect_events()
        assert len(events1) == 1
        
        # Should be empty after collection
        events2 = campaign.collect_events()
        assert len(events2) == 0
        
        # Play some turns
        campaign.play_turn("turn 1", "response 1")
        campaign.play_turn("turn 2", "response 2")
        
        # Should have 2 events
        events3 = campaign.collect_events()
        assert len(events3) == 2
        
        # Should be empty again
        events4 = campaign.collect_events()
        assert len(events4) == 0