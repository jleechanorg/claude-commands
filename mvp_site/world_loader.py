"""
World content loader for WorldArchitect.AI
Loads world files and creates combined instruction content for AI system.
"""

import os
import logging

# World file paths - only used in this module
# The world directory is now permanently located within mvp_site/world/
WORLD_DIR = os.path.join(os.path.dirname(__file__), "world")
    
WORLD_ASSIAH_PATH = os.path.join(WORLD_DIR, "world_assiah_compressed.md")
BANNED_NAMES_PATH = os.path.join(WORLD_DIR, "banned_names.md")

def load_banned_names():
    """
    Load the banned names from the dedicated banned_names.md file
    
    Returns:
        str: Banned names content or empty string if not found.
    """
    try:
        # Load from dedicated banned_names.md file
        with open(BANNED_NAMES_PATH, 'r', encoding='utf-8') as f:
            banned_content = f.read().strip()
            
        char_count = len(banned_content)
        token_count = char_count // 4  # Rough estimate
        logging.info(f"Loaded banned names from {BANNED_NAMES_PATH}: {char_count} characters (~{token_count} tokens)")
        return banned_content
            
    except FileNotFoundError:
        logging.warning(f"Banned names file not found at {BANNED_NAMES_PATH}")
        return ""
    except Exception as e:
        logging.warning(f"Could not load banned names file: {e}")
        return ""


def load_world_content_for_system_instruction():
    """
    Load world file and create system instruction.
    
    Returns:
        str: Combined world content formatted for system instruction
    """
    try:
        # Use the absolute path that is already constructed
        world_path = WORLD_ASSIAH_PATH
            
        logging.info(f"Looking for world content at: {world_path}")
        
        # Load world content
        with open(world_path, 'r', encoding='utf-8') as f:
            world_content = f.read().strip()
        char_count = len(world_content)
        token_count = char_count // 4  # Rough estimate
        logging.info(f"Loaded world content: {char_count} characters (~{token_count} tokens)")
        
        # Load banned names list
        banned_names_content = load_banned_names()
        
        # Build the base content
        combined_parts = [
            "# WORLD CONTENT FOR CAMPAIGN CONSISTENCY",
            "",
            "## WORLD CANON - INTEGRATED CAMPAIGN GUIDE",
            "The following content contains all world information in a single authoritative source:",
            "",
            world_content,
            "",
            "---"
        ]
        
        # Only add banned names section if content was loaded
        if banned_names_content:
            combined_parts.extend([
                "",
                "## CRITICAL NAMING RESTRICTIONS (from banned_names.md)",
                "**IMPORTANT**: The following content is from banned_names.md. These names are BANNED and must NEVER be used for any character, location, or entity:",
                "",
                banned_names_content,
                "",
                "**Enforcement**: If you are about to use any name from the CRITICAL NAMING RESTRICTIONS, you MUST choose a different name. This applies to:",
                "- New NPCs being introduced",
                "- Player character suggestions",
                "- Location names",
                "- Organization names",
                "- Any other named entity",
                "",
                "---"
            ])
        
        # Add world consistency rules
        combined_parts.extend([
            "",
            "## WORLD CONSISTENCY RULES",
            "1. **Character Consistency**: Maintain established character personalities and relationships",
            "2. **Timeline Integrity**: Respect established historical events and chronology",
            "3. **Power Scaling**: Follow established power hierarchies and combat abilities",
            "4. **Cultural Accuracy**: Maintain consistency in world cultures and societies",
            "5. **Geographic Consistency**: Respect established locations and their descriptions"
        ])
        
        # Only add rule 6 if banned names were loaded
        if banned_names_content:
            combined_parts.append("6. **Name Restrictions**: NEVER use any name from the CRITICAL NAMING RESTRICTIONS section")
        
        combined_parts.extend([
            "",
            "Use this world content to enhance campaign narratives while maintaining consistency with established lore."
        ])
        
        combined_content = "\n".join(combined_parts)
        
        return combined_content
        
    except FileNotFoundError as e:
        logging.error(f"CRITICAL: World file not found: {e}")
        raise
    except Exception as e:
        logging.error(f"CRITICAL: Error loading world content: {e}")
        raise