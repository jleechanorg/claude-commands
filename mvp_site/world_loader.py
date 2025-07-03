"""
World content loader for WorldArchitect.AI
Loads world files and creates combined instruction content for AI system.
"""

import os
import logging

# World file paths - only used in this module
# In deployment, world files are copied to same directory as the app
if os.path.exists(os.path.join(os.path.dirname(__file__), "world")):
    WORLD_DIR = "world"
else:
    WORLD_DIR = "../world"
    
CELESTIAL_WARS_BOOK_PATH = os.path.join(WORLD_DIR, "celestial_wars_alexiel_book.md")
WORLD_ASSIAH_PATH = os.path.join(WORLD_DIR, "world_assiah.md")
# BANNED_NAMES_PATH = os.path.join(WORLD_DIR, "banned_names.md")  # Removed - banned names are in world_assiah.md

def load_banned_names():
    """
    Extract the banned names section from world_assiah.md
    
    Returns:
        str: Banned names content or empty string if not found.
             The banned names are embedded in world_assiah.md, not a separate file.
    """
    try:
        # The banned names are in world_assiah.md, not a separate file
        world_path = os.path.join(os.path.dirname(__file__), WORLD_ASSIAH_PATH)
        
        with open(world_path, 'r', encoding='utf-8') as f:
            world_content = f.read()
            
        # Extract the banned names section
        import re
        banned_match = re.search(r'### Banned Names\s*\n(.*?)(?=\n---|\n##|\Z)', world_content, re.DOTALL)
        
        if banned_match:
            banned_names_content = banned_match.group(1).strip()
            logging.info(f"Extracted banned names from world_assiah.md: {banned_names_content}")
            return f"### Banned Names\n{banned_names_content}"
        else:
            logging.info("No banned names section found in world_assiah.md")
            return ""
            
    except Exception as e:
        logging.warning(f"Could not extract banned names from world file: {e}")
        return ""


def load_world_content_for_system_instruction():
    """
    Load world files and create a combined system instruction.
    The book takes precedence over the world file for any conflicts.
    
    Returns:
        str: Combined world content formatted for system instruction
    """
    try:
        # Construct paths consistently with banned_names logic
        if os.path.isabs(CELESTIAL_WARS_BOOK_PATH):
            book_path = CELESTIAL_WARS_BOOK_PATH
            world_path = WORLD_ASSIAH_PATH
        else:
            book_path = os.path.join(os.path.dirname(__file__), CELESTIAL_WARS_BOOK_PATH)
            world_path = os.path.join(os.path.dirname(__file__), WORLD_ASSIAH_PATH)
            
        logging.info(f"Looking for book at: {book_path}")
        logging.info(f"Looking for world at: {world_path}")
        
        # Load book content (higher precedence)
        with open(book_path, 'r', encoding='utf-8') as f:
            book_content = f.read().strip()
        logging.info(f"Loaded Celestial Wars book: {len(book_content)} characters")
        
        # Load world content (lower precedence)
        with open(world_path, 'r', encoding='utf-8') as f:
            world_content = f.read().strip()
        logging.info(f"Loaded Assiah world: {len(world_content)} characters")
        
        # Load banned names list
        banned_names_content = load_banned_names()
        
        # Build the base content
        combined_parts = [
            "# WORLD CONTENT FOR CAMPAIGN CONSISTENCY",
            "",
            "## PRIMARY CANON - CELESTIAL WARS ALEXIEL BOOK (HIGHEST AUTHORITY)",
            "The following content takes absolute precedence over all other world information:",
            "",
            book_content,
            "",
            "---",
            "",
            "## SECONDARY CANON - WORLD OF ASSIAH DOCUMENTATION",
            "The following content supplements the book but is overruled by it in case of conflicts:",
            "",
            world_content,
            "",
            "---"
        ]
        
        # Only add banned names section if content was loaded
        if banned_names_content:
            combined_parts.extend([
                "",
                "## CRITICAL NAMING RESTRICTIONS",
                "**IMPORTANT**: The following names are BANNED and must NEVER be used for any character, location, or entity:",
                "",
                banned_names_content,
                "",
                "**Enforcement**: If you are about to use any name from the banned list, you MUST choose a different name. This applies to:",
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
            "1. **Canon Hierarchy**: Book content ALWAYS overrides world content",
            "2. **Character Consistency**: Maintain established character personalities and relationships",
            "3. **Timeline Integrity**: Respect established historical events and chronology",
            "4. **Power Scaling**: Follow established power hierarchies and combat abilities",
            "5. **Cultural Accuracy**: Maintain consistency in world cultures and societies",
            "6. **Geographic Consistency**: Respect established locations and their descriptions"
        ])
        
        # Only add rule 7 if banned names were loaded
        if banned_names_content:
            combined_parts.append("7. **Name Restrictions**: NEVER use any name from the banned names list")
        
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