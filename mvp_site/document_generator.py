"""
Document Generation System

This module handles the generation of campaign documents in multiple formats (PDF, DOCX, TXT).
It processes story logs from campaigns and converts them into formatted, exportable documents
suitable for sharing or archiving.

Key Features:
- Multi-format export (PDF, DOCX, TXT)
- Story context processing and formatting
- Custom font support for better typography
- Actor labeling system (Story, God, Main Character)
- Consistent formatting across all export formats

Architecture:
- Format-specific generation functions
- Shared story text processing
- Configurable styling constants
- Safe file handling with cleanup

Usage:
    # Generate PDF document
    generate_pdf(story_text, output_path, campaign_title)

    # Generate DOCX document
    generate_docx(story_text, output_path, campaign_title)

    # Generate TXT document
    generate_txt(story_text, output_path, campaign_title)

    # Process story log for export
    story_text = get_story_text_from_context(story_log)

Dependencies:
- fpdf: PDF generation library
- python-docx: DOCX document creation
- DejaVu Sans font: Custom font for better Unicode support
"""

import html
import os

from docx import Document
from fpdf import FPDF, XPos, YPos

from mvp_site import constants, logging_util


# --- Enhanced Story Formatting Functions ---
# These functions provide rich formatting with scene numbers, session headers,
# resources, dice rolls, and choice detection (shared with CLI download script)

MAX_PLANNING_BLOCKS = 10  # Number of recent AI planning blocks to search for choices


def _normalize_text(text: str) -> str:
    """Normalize text for comparison by handling HTML entities and whitespace."""
    # Decode HTML entities (&#x27; -> ', &amp; -> &, etc.)
    normalized = html.unescape(text)
    # Normalize whitespace
    normalized = " ".join(normalized.split())
    return normalized


def get_choice_type(
    user_text: str, recent_planning_blocks: list[dict | None]
) -> tuple[str, str | None]:
    """
    Determine if user action was a planning choice or freeform.

    Args:
        user_text: The user's action text
        recent_planning_blocks: List of recent AI response planning_blocks (most recent first)

    Returns:
        Tuple of (choice_type, choice_key) where choice_type is 'freeform' or 'choice'
    """
    if not recent_planning_blocks:
        return ("freeform", None)

    # Normalize user text for comparison
    user_normalized = _normalize_text(user_text)

    # Extract title from user text (before " - " if present)
    user_title = user_normalized.split(" - ")[0].strip() if " - " in user_normalized else None

    # Check each recent planning block (most recent first)
    for planning_block in recent_planning_blocks:
        if not planning_block:
            continue

        # Guard against non-dict planning_block (e.g., legacy string values)
        if not isinstance(planning_block, dict):
            continue

        choices = planning_block.get("choices", {})
        if not choices:
            continue

        # Check if user text matches any choice in this planning block
        for key, choice in choices.items():
            if isinstance(choice, dict):
                choice_text = choice.get("text", "")
                if not choice_text:
                    continue

                choice_normalized = _normalize_text(choice_text)

                # Method 1: Direct startswith match
                if user_normalized.startswith(choice_normalized):
                    return ("choice", key)

                # Method 2: Choice text starts with user's title (for short choice texts)
                if user_title and choice_normalized.startswith(user_title):
                    return ("choice", key)

                # Method 3: User's title matches choice text exactly
                if user_title and user_title.lower() == choice_normalized.lower():
                    return ("choice", key)

                # Method 4: Extract title from choice text and compare
                choice_title = choice_normalized.split(" - ")[0].strip() if " - " in choice_normalized else choice_normalized
                if user_title and user_title.lower() == choice_title.lower():
                    return ("choice", key)

    return ("freeform", None)


def format_story_entry(
    entry: dict,
    include_scene: bool = True,
    recent_planning_blocks: list[dict | None] | None = None,
) -> str:
    """
    Format a single story entry with scene numbers, session headers, resources, and dice rolls.

    Args:
        entry: Story entry dictionary from Firestore
        include_scene: Whether to include scene number header
        recent_planning_blocks: List of recent AI response planning_blocks (for user entries)

    Returns:
        Formatted string for the entry
    """
    actor = entry.get("actor", "unknown")
    text = entry.get("text", "")
    mode = entry.get("mode")
    scene_num = entry.get("user_scene_number")
    session_header = entry.get("session_header", "")
    resources = entry.get("resources", "")
    dice_rolls = entry.get("dice_rolls", [])

    parts = []

    # Add scene header for AI responses
    if actor == "gemini" and scene_num and include_scene:
        parts.append("=" * 60)
        parts.append(f"SCENE {scene_num}")
        parts.append("=" * 60)

    # Add session header if present (contains timestamp, location, status)
    if session_header:
        # Clean up the session header (remove [SESSION_HEADER] prefix if present)
        clean_header = session_header.replace("[SESSION_HEADER]", "").strip()
        if clean_header:
            parts.append(f"[{clean_header}]")

    # Add resources if present
    if resources:
        parts.append(f"Resources: {resources}")

    # Add dice rolls if present
    if dice_rolls:
        parts.append("Dice Rolls:")
        for roll in dice_rolls:
            parts.append(f"  - {roll}")

    # Add blank line after metadata if we have any
    if session_header or resources or dice_rolls:
        parts.append("")

    # Add actor label with choice type for player actions
    if actor == "gemini":
        label = "Game Master"
    elif mode == "god":
        label = "God Mode"
    else:
        # Determine if this was a planning choice or freeform
        choice_type, choice_key = get_choice_type(text, recent_planning_blocks or [])
        if choice_type == "choice" and choice_key:
            label = f"Player (choice: {choice_key})"
        else:
            label = "Player (freeform)"

    parts.append(f"{label}:")
    parts.append(text)

    return "\n".join(parts)


def get_story_text_from_context_enhanced(
    story_log: list[dict],
    include_scenes: bool = True,
) -> str:
    """
    Convert story log entries to formatted text with enhanced formatting.

    This is the enhanced version that includes:
    - Scene numbers and headers
    - Session headers (timestamps, location, status)
    - Resources
    - Dice rolls
    - Choice detection (freeform vs predefined choice)

    Args:
        story_log: List of story entry dictionaries from Firestore
        include_scenes: Whether to include scene numbers and headers

    Returns:
        Formatted story text ready for export
    """
    story_parts = []
    # Track last N planning blocks to search for choice matches
    recent_planning_blocks: list[dict | None] = []

    for entry in story_log:
        # Skip malformed entries
        if not isinstance(entry, dict):
            continue

        # Pass recent planning blocks for user entries to determine choice type
        formatted = format_story_entry(
            entry, include_scene=include_scenes, recent_planning_blocks=recent_planning_blocks
        )
        story_parts.append(formatted)

        # Track planning blocks from AI responses (keep last N)
        if entry.get("actor") == "gemini":
            planning_block = entry.get("planning_block")
            if planning_block:
                # Insert at beginning (most recent first)
                recent_planning_blocks.insert(0, planning_block)
                # Keep only last N
                if len(recent_planning_blocks) > MAX_PLANNING_BLOCKS:
                    recent_planning_blocks.pop()

    return "\n\n".join(story_parts)


def get_story_text_from_context(story_log):
    """
    Convert story log entries to formatted text for document export.
    This function replicates the logic from main.py export_campaign.
    """
    story_parts = []
    for entry in story_log:
        actor = entry.get(constants.KEY_ACTOR, UNKNOWN_ACTOR)
        text = entry.get(constants.KEY_TEXT, "")
        mode = entry.get(constants.KEY_MODE)
        if actor == constants.ACTOR_GEMINI:
            label = LABEL_GEMINI
        else:
            label = LABEL_GOD if mode == constants.MODE_GOD else LABEL_USER
        story_parts.append(f"{label}:\n{text}")
    return "\n\n".join(story_parts)


# --- CONSTANTS ---
# File Paths and Configuration
ASSETS_DIR = "assets"
FONT_FILENAME = "DejaVuSans.ttf"
DEFAULT_FONT_FAMILY = "Helvetica"
CUSTOM_FONT_NAME = "DejaVu"
ENCODING = "latin-1"
ENCODING_REPLACE_STR = "replace"

# PDF Styling
PDF_TITLE_STYLE = "U"
TITLE_FONT_SIZE = 16
TITLE_LINE_HEIGHT = 10
TITLE_ALIGNMENT = "C"
BODY_FONT_SIZE = 12
BODY_LINE_HEIGHT = 5
PARAGRAPH_SPACING = 3
TITLE_SPACING = 5

# Document Content Labels
LABEL_GEMINI = "Story"
LABEL_GOD = "God"
LABEL_USER = "Main Character"
UNKNOWN_ACTOR = "Unknown"

# Document Generation
DOCX_HEADING_LEVEL = 1
# --- END CONSTANTS ---


def generate_pdf(story_text, output_filepath, campaign_title=""):
    """Generates a PDF file and saves it to the specified path."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_title(campaign_title)

    font_family = DEFAULT_FONT_FAMILY
    try:
        # Try multiple possible locations for the font file
        possible_paths = [
            os.path.join(ASSETS_DIR, FONT_FILENAME),  # Current working directory
            os.path.join(
                os.path.dirname(__file__), ASSETS_DIR, FONT_FILENAME
            ),  # Relative to this file
        ]

        font_path = None
        for path in possible_paths:
            if os.path.exists(path):
                font_path = path
                break

        if font_path:
            # The 'uni=True' parameter is crucial for UTF-8 support with FPDF.
            pdf.add_font(CUSTOM_FONT_NAME, "", font_path)
            font_family = CUSTOM_FONT_NAME
            logging_util.info("DejaVuSans.ttf found and loaded.")
        else:
            raise RuntimeError("Font file not found in any expected location")
    except (RuntimeError, FileNotFoundError):
        logging_util.warning(
            "DejaVuSans.ttf not found. Falling back to core font. Non-ASCII characters may not render correctly."
        )
        # If the custom font fails, we stick with the default Helvetica.

    pdf.set_font(font_family, style="", size=BODY_FONT_SIZE)

    # Split the text into paragraphs and write them to the PDF.
    # The \\n is now a literal backslash followed by 'n', so we split on that.
    for paragraph in story_text.split("\\n\\n"):
        # No more manual encoding/decoding is needed.
        pdf.multi_cell(
            0, BODY_LINE_HEIGHT, text=paragraph, new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )
        pdf.ln(PARAGRAPH_SPACING)

    pdf.output(output_filepath)


def generate_docx(story_text, output_filepath, campaign_title=""):
    """Generates a DOCX file and saves it to the specified path."""
    document = Document()
    document.core_properties.title = campaign_title  # Set metadata title
    for paragraph in story_text.split("\\n\\n"):
        document.add_paragraph(paragraph)
    document.save(output_filepath)


def generate_txt(story_text, output_filepath, campaign_title=""):
    """Generates a TXT file and saves it to the specified path."""
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(story_text.replace("\\\\n", "\\n"))
