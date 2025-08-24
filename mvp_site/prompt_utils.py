"""
Pure utility functions for campaign prompt building and JSON escape sequence conversion.

This module contains helper functions that are shared between world_logic.py and tests.
Extracted to avoid import-unsafe dependencies and code duplication.
"""

import random
from typing import Optional
from debug_hybrid_system import convert_json_escape_sequences
import logging_util

# Random content constants (copied from world_logic.py to avoid circular dependencies)
RANDOM_CHARACTERS = [
    "A brave warrior seeking to prove their worth in battle",
    "A cunning rogue with a mysterious past and hidden agenda", 
    "A wise wizard devoted to uncovering ancient magical secrets",
    "A noble paladin sworn to protect the innocent from evil",
    "A skilled ranger who knows the wilderness like no other",
    "A charismatic bard who weaves magic through music and stories",
    "A devout cleric blessed with divine power to heal and smite",
    "A fierce barbarian driven by primal instincts and tribal honor",
    "A stealthy monk trained in martial arts and inner discipline", 
    "A nature-loving druid who can shapeshift and command beasts",
]

RANDOM_SETTINGS = [
    "The bustling city of Waterdeep, where intrigue and adventure await around every corner",
    "The mystical Feywild, a realm where magic runs wild and reality bends to emotion",
    "The treacherous Underdark, a vast network of caverns filled with dangerous creatures",
    "The frozen lands of Icewind Dale, where survival means everything in the harsh tundra",
    "The desert kingdom of Calimshan, where genies and merchants rule with equal power",
    "The pirate-infested Sword Coast, where gold and glory are won by blade and cunning",
    "The haunted moors of Barovia, trapped in eternal mist and ruled by dark powers",
    "The floating city of Sharn, where magic and technology create vertical neighborhoods",
    "The jungle continent of Chult, where ancient ruins hide deadly secrets and treasures",
    "The war-torn kingdom of Cyre, struggling to rebuild after magical devastation",
]


def _convert_and_format_field(field_value: str, field_name: str) -> str:
    """Convert JSON escape sequences and format field for prompt.
    
    Args:
        field_value: Raw field value that may contain JSON escape sequences
        field_name: Name of the field (Character, Setting, Description)
        
    Returns:
        Formatted field string or empty string if field_value is empty
    """
    if not field_value.strip():
        return ""
    
    converted_value = convert_json_escape_sequences(field_value.strip())
    return f"{field_name}: {converted_value}"


def _build_campaign_prompt(character: str, setting: str, description: str, old_prompt: Optional[str]) -> str:
    """Build campaign prompt from components with JSON escape sequence conversion.
    
    Args:
        character: Character description (may contain JSON escape sequences)
        setting: Setting description (may contain JSON escape sequences) 
        description: Campaign description (may contain JSON escape sequences)
        old_prompt: Existing prompt to use if provided
        
    Returns:
        Formatted campaign prompt with escape sequences converted
    """
    if isinstance(old_prompt, str) and old_prompt.strip():
        return old_prompt.strip()

    prompt_parts = []

    # Convert and add each field using helper function
    character_part = _convert_and_format_field(character, "Character")
    if character_part:
        prompt_parts.append(character_part)
        
    setting_part = _convert_and_format_field(setting, "Setting")
    if setting_part:
        prompt_parts.append(setting_part)
        
    description_part = _convert_and_format_field(description, "Description")
    if description_part:
        prompt_parts.append(description_part)

    if not prompt_parts:
        # Generate random prompts when no input provided
        random_character = random.choice(RANDOM_CHARACTERS)  # nosec B311
        random_setting = random.choice(RANDOM_SETTINGS)  # nosec B311
        prompt_parts = [f"Character: {random_character}", f"Setting: {random_setting}"]
        
        logging_util.info(
            f"Generated random campaign: character='{random_character}', setting='{random_setting}'"
        )

    return " | ".join(prompt_parts)


# Alias for existing callers in world_logic.py
def _build_campaign_prompt_impl(
    character: str,
    setting: str, 
    description: str,
    old_prompt: Optional[str]
) -> str:
    """Backwards compatibility alias for world_logic.py imports."""
    return _build_campaign_prompt(character, setting, description, old_prompt)