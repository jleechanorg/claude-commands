"""
Test narratives for validation prototype testing.
Each narrative has known entity presence/absence for validation.
"""

test_narratives = [
    # 1. All entities present correctly
    {
        "id": "test_001",
        "narrative": "Gideon stepped forward, his armor gleaming in the torchlight. Beside him, Rowan clutched her healing staff, ready to support the knight. 'We must be cautious,' Gideon warned.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": [],
        "location": "Dungeon Entrance",
    },
    # 2. Missing one entity (Rowan)
    {
        "id": "test_002",
        "narrative": "The knight advanced through the darkness, sword drawn. His footsteps echoed in the empty corridor as he searched for any sign of danger.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": ["Rowan"],
        "location": "Dark Corridor",
    },
    # 3. Missing both entities
    {
        "id": "test_003",
        "narrative": "The chamber stood empty, save for the flickering shadows cast by ancient braziers. Dust motes danced in the stale air.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": ["Gideon", "Rowan"],
        "location": "Empty Chamber",
    },
    # 4. Entity mentioned by title only
    {
        "id": "test_004",
        "narrative": "Ser Vance checked his equipment while the healer prepared her spells. They would need to work together to survive the trials ahead.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": [],
        "location": "Preparation Room",
        "notes": "Gideon referenced as 'Ser Vance', Rowan as 'the healer'",
    },
    # 5. Pronoun references only
    {
        "id": "test_005",
        "narrative": "He raised his shield just as she cast a protective ward. They had fought together many times before, and their teamwork was flawless.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": [],
        "location": "Combat Arena",
        "notes": "Entities referenced only by pronouns",
    },
    # 6. One entity hidden
    {
        "id": "test_006",
        "narrative": "Gideon scanned the room carefully. He could sense Rowan's presence, though she remained hidden in the shadows, ready to strike.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": [],
        "entity_states": {"Rowan": ["hidden"]},
        "location": "Ambush Point",
    },
    # 7. One entity unconscious
    {
        "id": "test_007",
        "narrative": "The knight knelt beside Rowan's unconscious form. She had fallen during the battle, and he needed to protect her until she recovered.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": [],
        "entity_states": {"Rowan": ["unconscious"]},
        "location": "After Battle",
    },
    # 8. Combat scenario with all present
    {
        "id": "test_008",
        "narrative": "Gideon's sword clashed against the orc's axe while Rowan chanted healing prayers. The battle was fierce, but they fought as one.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": [],
        "location": "Orc Lair",
        "combat_active": True,
    },
    # 9. Partial name mentions
    {
        "id": "test_009",
        "narrative": "Gid-- The knight's words were cut short as an arrow flew past. Row-- The healer's scream echoed through the cavern.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": [],
        "location": "Ambush Site",
        "notes": "Names partially mentioned/interrupted",
    },
    # 10. Descriptive references
    {
        "id": "test_010",
        "narrative": "The armored warrior and the young cleric made their way through the mist. Their journey had been long, but they pressed on.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": [],
        "location": "Misty Path",
        "notes": "Entities referenced by descriptions",
    },
    # 11. Group reference missing individual
    {
        "id": "test_011",
        "narrative": "The party continued forward. Their leader guided them through the treacherous path ahead.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": ["Gideon", "Rowan"],
        "location": "Mountain Trail",
        "notes": "Generic 'party' reference without individuals",
    },
    # 12. Wrong entity names
    {
        "id": "test_012",
        "narrative": "Marcus drew his blade while Elena prepared her magic. The two adventurers were ready for whatever lay ahead.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": ["Gideon", "Rowan"],
        "location": "Unknown Dungeon",
        "notes": "Different character names entirely",
    },
    # 13. Past tense narrative with one missing
    {
        "id": "test_013",
        "narrative": "Gideon remembered how they had entered this place together. Now he stood alone, wondering where his companion had gone.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": ["Rowan"],
        "location": "Memory Scene",
    },
    # 14. Dialogue heavy with both present
    {
        "id": "test_014",
        "narrative": "'Watch out!' Gideon shouted. 'I see it,' Rowan replied, already moving her hands in arcane gestures. 'Stay behind me!'",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": [],
        "location": "Trap Corridor",
    },
    # 15. Entity mentioned in thoughts only
    {
        "id": "test_015",
        "narrative": "The knight pondered their situation. *Where is Rowan when I need her?* he thought, gripping his sword tighter.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": ["Rowan"],
        "location": "Solo Scene",
        "notes": "Rowan mentioned in thoughts but not present",
    },
    # 16. Plural references with both
    {
        "id": "test_016",
        "narrative": "The two companions stood back to back. Gideon and Rowan had faced worse odds before, and they would survive this too.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": [],
        "location": "Surrounded",
    },
    # 17. Action-focused missing names
    {
        "id": "test_017",
        "narrative": "A sword struck the stone wall, sending sparks flying. Healing magic filled the air, mending wounds as quickly as they appeared.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": ["Gideon", "Rowan"],
        "location": "Intense Combat",
        "notes": "Actions imply entities but no names",
    },
    # 18. Environmental focus with one entity
    {
        "id": "test_018",
        "narrative": "Rowan examined the ancient runes on the wall. The symbols glowed faintly in response to her touch, revealing hidden meanings.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": ["Gideon"],
        "location": "Rune Chamber",
    },
    # 19. Time skip narrative
    {
        "id": "test_019",
        "narrative": "Hours had passed since they entered. Now, Gideon and Rowan finally reached the inner sanctum, exhausted but determined.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": [],
        "location": "Inner Sanctum",
    },
    # 20. Ambiguous references
    {
        "id": "test_020",
        "narrative": "Someone moved in the darkness. A figure in armor perhaps? The sound of prayers echoed softly, but the source was unclear.",
        "expected_entities": ["Gideon", "Rowan"],
        "missing_entities": ["Gideon", "Rowan"],
        "location": "Dark Chamber",
        "notes": "Ambiguous references that could be the entities",
    },
]


# Helper function to get narrative by ID
def get_narrative(narrative_id):
    """Get a specific test narrative by ID."""
    for narrative in test_narratives:
        if narrative["id"] == narrative_id:
            return narrative
    return None


# Helper function to get narratives by characteristic
def get_narratives_by_type(narrative_type):
    """Get narratives matching a specific type (e.g., 'missing_entities', 'combat_active')."""
    if narrative_type == "all_present":
        return [n for n in test_narratives if not n["missing_entities"]]
    if narrative_type == "some_missing":
        return [n for n in test_narratives if n["missing_entities"]]
    if narrative_type == "combat":
        return [n for n in test_narratives if n.get("combat_active", False)]
    if narrative_type == "hidden_entities":
        return [n for n in test_narratives if "entity_states" in n]
    return test_narratives
