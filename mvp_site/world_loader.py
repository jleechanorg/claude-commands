"""
World content loader for WorldArchitect.AI
Loads world files and creates combined instruction content for AI system.
"""

import os

from mvp_site import logging_util
from mvp_site.file_cache import read_file_cached

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
        return read_file_cached(BANNED_NAMES_PATH).strip()

    except FileNotFoundError:
        logging_util.warning(f"Banned names file not found at {BANNED_NAMES_PATH}")
        return ""
    except Exception as e:
        logging_util.warning(f"Could not load banned names file: {e}")
        return ""


def load_world_content_for_system_instruction():
    """
    Load world file and create system instruction.

    Returns:
        str: Combined world content formatted for system instruction
    """
    try:
        # Load world content using cached file reader
        logging_util.info(f"Looking for world content at: {WORLD_ASSIAH_PATH}")
        world_content = read_file_cached(WORLD_ASSIAH_PATH).strip()

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
            "---",
        ]

        # Only add banned names section if content was loaded
        if banned_names_content:
            combined_parts.extend(
                [
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
                    "---",
                ]
            )

        # Add world consistency rules
        combined_parts.extend(
            [
                "",
                "## WORLD CONSISTENCY RULES",
                "1. **Character Consistency**: Maintain established character personalities and relationships",
                "2. **Timeline Integrity**: Respect established historical events and chronology",
                "3. **Power Scaling**: Follow established power hierarchies and combat abilities",
                "4. **Cultural Accuracy**: Maintain consistency in world cultures and societies",
                "5. **Geographic Consistency**: Respect established locations and their descriptions",
            ]
        )

        # Only add rule 6 if banned names were loaded
        if banned_names_content:
            combined_parts.append(
                "6. **Name Restrictions**: NEVER use any name from the CRITICAL NAMING RESTRICTIONS section"
            )

        combined_parts.extend(
            [
                "",
                "Use this world content to enhance campaign narratives while maintaining consistency with established lore.",
            ]
        )

        return "\n".join(combined_parts)

    except FileNotFoundError as e:
        logging_util.error(f"CRITICAL: World file not found: {e}")
        raise
    except Exception as e:
        logging_util.error(f"CRITICAL: Error loading world content: {e}")
        raise
