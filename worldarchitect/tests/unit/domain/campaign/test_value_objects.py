"""
Unit tests for campaign value objects.
"""
import pytest
from worldarchitect.domain.campaign.value_objects import CampaignId, SceneNumber, TurnNumber


class TestCampaignId:
    """Tests for CampaignId value object."""
    
    def test_create_valid_campaign_id(self):
        """Test creating a valid campaign ID."""
        campaign_id = CampaignId("abc-123-def")
        assert campaign_id.value == "abc-123-def"
        assert str(campaign_id) == "abc-123-def"
    
    def test_campaign_id_strips_whitespace(self):
        """Test that campaign ID strips surrounding whitespace."""
        campaign_id = CampaignId("  abc-123  ")
        assert campaign_id.value == "abc-123"
    
    def test_campaign_id_rejects_empty_string(self):
        """Test that empty strings are rejected."""
        with pytest.raises(ValueError, match="non-empty string"):
            CampaignId("")
    
    def test_campaign_id_rejects_whitespace_only(self):
        """Test that whitespace-only strings are rejected."""
        with pytest.raises(ValueError, match="whitespace only"):
            CampaignId("   ")
    
    def test_campaign_id_rejects_none(self):
        """Test that None is rejected."""
        with pytest.raises(ValueError, match="non-empty string"):
            CampaignId(None)
    
    def test_campaign_id_equality(self):
        """Test campaign ID equality comparison."""
        id1 = CampaignId("abc-123")
        id2 = CampaignId("abc-123")
        id3 = CampaignId("def-456")
        
        assert id1 == id2
        assert id1 != id3
        assert id1 != "abc-123"  # Should not equal string
    
    def test_campaign_id_hashable(self):
        """Test that campaign IDs can be used in sets and dicts."""
        id1 = CampaignId("abc-123")
        id2 = CampaignId("abc-123")
        id3 = CampaignId("def-456")
        
        # Should work in sets
        id_set = {id1, id2, id3}
        assert len(id_set) == 2  # id1 and id2 are equal
        
        # Should work as dict keys
        id_dict = {id1: "value1", id3: "value2"}
        assert id_dict[id2] == "value1"  # id2 equals id1
    
    def test_campaign_id_generate(self):
        """Test generating new campaign IDs."""
        id1 = CampaignId.generate()
        id2 = CampaignId.generate()
        
        assert id1 != id2  # Should be unique
        assert len(id1.value) > 0  # Should have content
        assert isinstance(id1.value, str)


class TestSceneNumber:
    """Tests for SceneNumber value object."""
    
    def test_create_valid_scene_number(self):
        """Test creating a valid scene number."""
        scene = SceneNumber(5)
        assert scene.value == 5
        assert str(scene) == "5"
    
    def test_scene_number_minimum(self):
        """Test that scene numbers must be at least 1."""
        SceneNumber(1)  # Should work
        
        with pytest.raises(ValueError, match="positive"):
            SceneNumber(0)
        
        with pytest.raises(ValueError, match="positive"):
            SceneNumber(-1)
    
    def test_scene_number_must_be_integer(self):
        """Test that scene numbers must be integers."""
        with pytest.raises(ValueError, match="integer"):
            SceneNumber(1.5)
        
        with pytest.raises(ValueError, match="integer"):
            SceneNumber("1")
    
    def test_scene_number_first(self):
        """Test creating the first scene number."""
        scene = SceneNumber.first()
        assert scene.value == 1
    
    def test_scene_number_next(self):
        """Test getting the next scene number."""
        scene1 = SceneNumber(5)
        scene2 = scene1.next()
        assert scene2.value == 6
    
    def test_scene_number_previous(self):
        """Test getting the previous scene number."""
        scene1 = SceneNumber(5)
        scene2 = scene1.previous()
        assert scene2.value == 4
    
    def test_scene_number_previous_at_minimum(self):
        """Test that we can't go before scene 1."""
        scene = SceneNumber(1)
        with pytest.raises(ValueError, match="before scene 1"):
            scene.previous()
    
    def test_scene_number_comparisons(self):
        """Test scene number comparisons."""
        scene1 = SceneNumber(3)
        scene2 = SceneNumber(5)
        scene3 = SceneNumber(5)
        
        assert scene1 < scene2
        assert scene1 <= scene2
        assert scene2 > scene1
        assert scene2 >= scene1
        assert scene2 == scene3
        assert scene2 <= scene3
        assert scene2 >= scene3
    
    def test_scene_number_hashable(self):
        """Test that scene numbers can be used in sets and dicts."""
        scene1 = SceneNumber(3)
        scene2 = SceneNumber(3)
        scene3 = SceneNumber(5)
        
        scene_set = {scene1, scene2, scene3}
        assert len(scene_set) == 2


class TestTurnNumber:
    """Tests for TurnNumber value object."""
    
    def test_create_valid_turn_number(self):
        """Test creating a valid turn number."""
        turn = TurnNumber(3)
        assert turn.value == 3
        assert str(turn) == "3"
    
    def test_turn_number_minimum(self):
        """Test that turn numbers must be at least 1."""
        TurnNumber(1)  # Should work
        
        with pytest.raises(ValueError, match="positive"):
            TurnNumber(0)
        
        with pytest.raises(ValueError, match="positive"):
            TurnNumber(-1)
    
    def test_turn_number_must_be_integer(self):
        """Test that turn numbers must be integers."""
        with pytest.raises(ValueError, match="integer"):
            TurnNumber(1.5)
        
        with pytest.raises(ValueError, match="integer"):
            TurnNumber("1")
    
    def test_turn_number_first(self):
        """Test creating the first turn number."""
        turn = TurnNumber.first()
        assert turn.value == 1
    
    def test_turn_number_next(self):
        """Test getting the next turn number."""
        turn1 = TurnNumber(3)
        turn2 = turn1.next()
        assert turn2.value == 4
    
    def test_turn_number_previous(self):
        """Test getting the previous turn number."""
        turn1 = TurnNumber(3)
        turn2 = turn1.previous()
        assert turn2.value == 2
    
    def test_turn_number_previous_at_minimum(self):
        """Test that we can't go before turn 1."""
        turn = TurnNumber(1)
        with pytest.raises(ValueError, match="before turn 1"):
            turn.previous()
    
    def test_turn_number_comparisons(self):
        """Test turn number comparisons."""
        turn1 = TurnNumber(2)
        turn2 = TurnNumber(4)
        turn3 = TurnNumber(4)
        
        assert turn1 < turn2
        assert turn1 <= turn2
        assert turn2 > turn1
        assert turn2 >= turn1
        assert turn2 == turn3
        assert turn2 <= turn3
        assert turn2 >= turn3
    
    def test_turn_number_hashable(self):
        """Test that turn numbers can be used in sets and dicts."""
        turn1 = TurnNumber(2)
        turn2 = TurnNumber(2)
        turn3 = TurnNumber(4)
        
        turn_set = {turn1, turn2, turn3}
        assert len(turn_set) == 2