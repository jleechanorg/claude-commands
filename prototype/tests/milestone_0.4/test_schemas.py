#!/usr/bin/env python3
"""
Test the Pydantic schemas for entity tracking
"""

from schemas.entities_simple import (
    NPC,
    HealthStatus,
    Location,
    PlayerCharacter,
    SceneManifest,
    Visibility,
    create_from_game_state,
)


def test_basic_schemas():
    """Test basic schema creation"""
    print("Testing basic schema creation...")

    # Create a location
    throne_room = Location(
        entity_id="loc_throne_room_001",
        display_name="The Throne Room",
        aliases=["throne room", "royal chamber"],
        connected_locations=["loc_corridor_001", "loc_balcony_001"],
    )
    print(f"✓ Created location: {throne_room.display_name}")

    # Create a player character
    sariel = PlayerCharacter(
        entity_id="pc_sariel_001",
        display_name="Sariel Arcanus",
        aliases=["Sariel", "Princess Sariel"],
        level=5,
        health=HealthStatus(hp=8, hp_max=8),
        current_location=throne_room.entity_id,
        equipped_items=["item_staff_001", "item_robes_001"],
        knowledge=["knowledge_titus_betrayal_001"],
        core_memories=["memory_valerius_death_001"],
    )
    print(f"✓ Created PC: {sariel.display_name} (Level {sariel.level})")

    # Create NPCs
    cassian = NPC(
        entity_id="npc_cassian_001",
        display_name="Prince Cassian",
        aliases=["Cassian", "Brother"],
        level=6,
        health=HealthStatus(hp=45, hp_max=50),
        current_location=throne_room.entity_id,
        faction="faction_arcanus_001",
        role="Twin Prince",
    )
    print(f"✓ Created NPC: {cassian.display_name}")

    # Create scene manifest
    scene = SceneManifest(
        scene_id="scene_test_001",
        session_number=1,
        turn_number=1,
        current_location=throne_room,
        player_characters=[sariel],
        npcs=[cassian],
        present_entities=[sariel.entity_id, cassian.entity_id],
    )
    print(
        f"✓ Created scene manifest with {len(scene.player_characters)} PC(s) and {len(scene.npcs)} NPC(s)"
    )

    return scene


def test_game_state_conversion():
    """Test converting legacy game state to schemas"""
    print("\nTesting game state conversion...")

    # Legacy game state format
    game_state = {
        "location": "Throne Room",
        "player_character_data": {"name": "Sariel", "hp": 8, "hp_max": 8},
        "npc_data": {
            "Cassian": {"present": True, "hp": 45, "hp_max": 50, "conscious": True},
            "Guard": {"present": True, "hp": 20, "hp_max": 25, "hidden": True},
            "Valerius": {"present": False},
        },
        "combat_state": {
            "in_combat": True,
            "participants": ["Sariel", "Cassian", "Guard"],
            "round": 3,
        },
    }

    # Convert to scene manifest
    manifest = create_from_game_state(game_state, session=1, turn=42)
    print("✓ Converted game state to manifest")
    print(f"  - Location: {manifest.current_location.display_name}")
    print(f"  - PCs: {[pc.display_name for pc in manifest.player_characters]}")
    print(f"  - NPCs: {[npc.display_name for npc in manifest.npcs]}")
    print(
        f"  - Combat: {manifest.combat_state.get('in_combat', False) if manifest.combat_state else False}"
    )

    # Check visibility
    hidden_npcs = [
        npc for npc in manifest.npcs if npc.visibility == Visibility.INVISIBLE
    ]
    print(f"  - Hidden NPCs: {[npc.display_name for npc in hidden_npcs]}")

    return manifest


def test_prompt_generation():
    """Test prompt format generation"""
    print("\nTesting prompt generation...")

    scene = test_basic_schemas()

    # Generate prompt format
    prompt = scene.to_prompt_format()
    print("Generated prompt format:")
    print("-" * 60)
    print(prompt)
    print("-" * 60)

    return prompt


def test_validation():
    """Test schema validation"""
    print("\nTesting schema validation...")

    # Test HP validation
    try:
        HealthStatus(hp=20, hp_max=10)
    except ValueError as e:
        print(f"✓ HP validation works: {e}")

    # Test entity ID validation
    try:
        PlayerCharacter(
            entity_id="invalid_id",
            display_name="Invalid",
            health=HealthStatus(hp=10, hp_max=10),
            current_location="loc_test_001",
        )
    except ValueError as e:
        print(f"✓ Entity ID validation works: {e}")

    # Test level validation
    try:
        PlayerCharacter(
            entity_id="pc_test_001",
            display_name="Test",
            level=25,  # Max is 20
            health=HealthStatus(hp=10, hp_max=10),
            current_location="loc_test_001",
        )
    except ValueError as e:
        print(f"✓ Level validation works: {e}")


def test_expected_entities():
    """Test expected entity extraction"""
    print("\nTesting expected entity extraction...")

    manifest = test_game_state_conversion()
    expected = manifest.get_expected_entities()

    print(f"Expected entities in narrative: {expected}")

    # Should include visible, conscious entities
    # Should exclude hidden Guard
    assert "Sariel" in expected
    assert "Cassian" in expected
    assert "Guard" not in expected  # Hidden
    print("✓ Expected entity filtering works correctly")


def main():
    """Run all tests"""
    print("Pydantic Schema Tests")
    print("=" * 60)

    # Run tests
    test_basic_schemas()
    test_game_state_conversion()
    test_prompt_generation()
    test_validation()
    test_expected_entities()

    print("\n" + "=" * 60)
    print("All tests completed successfully!")


if __name__ == "__main__":
    main()
