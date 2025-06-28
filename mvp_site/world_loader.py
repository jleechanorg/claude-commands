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

def load_world_content_for_system_instruction():
    """
    Load world files and create a combined system instruction.
    The book takes precedence over the world file for any conflicts.
    
    Returns:
        str: Combined world content formatted for system instruction
    """
    try:
        # If WORLD_DIR is relative (not starting with ../), join with current dir
        if WORLD_DIR.startswith(".."):
            book_path = os.path.join(os.path.dirname(__file__), CELESTIAL_WARS_BOOK_PATH)
            world_path = os.path.join(os.path.dirname(__file__), WORLD_ASSIAH_PATH)
        else:
            # WORLD_DIR is "world" - files are in same directory
            book_path = CELESTIAL_WARS_BOOK_PATH
            world_path = WORLD_ASSIAH_PATH
            
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
        
        # Combine with clear precedence hierarchy
        combined_content = f"""
# WORLD CONTENT FOR CAMPAIGN CONSISTENCY

## PRIMARY CANON - CELESTIAL WARS ALEXIEL BOOK (HIGHEST AUTHORITY)
The following content takes absolute precedence over all other world information:

{book_content}

---

## SECONDARY CANON - WORLD OF ASSIAH DOCUMENTATION
The following content supplements the book but is overruled by it in case of conflicts:

{world_content}

---

## WORLD CONSISTENCY RULES
1. **Canon Hierarchy**: Book content ALWAYS overrides world content
2. **Character Consistency**: Maintain established character personalities and relationships
3. **Timeline Integrity**: Respect established historical events and chronology
4. **Power Scaling**: Follow established power hierarchies and combat abilities
5. **Cultural Accuracy**: Maintain consistency in world cultures and societies
6. **Geographic Consistency**: Respect established locations and their descriptions

Use this world content to enhance campaign narratives while maintaining consistency with established lore.
        """.strip()
        
        return combined_content
        
    except FileNotFoundError as e:
        logging.error(f"CRITICAL: World file not found: {e}")
        raise
    except Exception as e:
        logging.error(f"CRITICAL: Error loading world content: {e}")
        raise