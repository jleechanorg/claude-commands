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

import logging
import os

import constants
from docx import Document
from fpdf import FPDF, XPos, YPos


def get_story_text_from_context(story_log):
    """
    Convert story log entries to formatted text for document export.
    This function replicates the logic from main.py export_campaign.
    """
    story_parts = []
    for entry in story_log:
        actor = entry.get(constants.KEY_ACTOR, UNKNOWN_ACTOR)
        text = entry.get(constants.KEY_TEXT, '')
        mode = entry.get(constants.KEY_MODE)
        if actor == constants.ACTOR_GEMINI:
            label = LABEL_GEMINI
        else:
            label = LABEL_GOD if mode == constants.MODE_GOD else LABEL_USER
        story_parts.append(f"{label}:\n{text}")
    return "\n\n".join(story_parts)

# --- CONSTANTS ---
# File Paths and Configuration
ASSETS_DIR = 'assets'
FONT_FILENAME = 'DejaVuSans.ttf'
DEFAULT_FONT_FAMILY = 'Helvetica'
CUSTOM_FONT_NAME = 'DejaVu'
ENCODING = 'latin-1'
ENCODING_REPLACE_STR = 'replace'

# PDF Styling
PDF_TITLE_STYLE = 'U'
TITLE_FONT_SIZE = 16
TITLE_LINE_HEIGHT = 10
TITLE_ALIGNMENT = 'C'
BODY_FONT_SIZE = 12
BODY_LINE_HEIGHT = 5
PARAGRAPH_SPACING = 3
TITLE_SPACING = 5

# Document Content Labels
LABEL_GEMINI = 'Story'
LABEL_GOD = 'God'
LABEL_USER = 'Main Character'
UNKNOWN_ACTOR = 'Unknown'

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
            os.path.join(os.path.dirname(__file__), ASSETS_DIR, FONT_FILENAME),  # Relative to this file
        ]

        font_path = None
        for path in possible_paths:
            if os.path.exists(path):
                font_path = path
                break

        if font_path:
            # The 'uni=True' parameter is crucial for UTF-8 support with FPDF.
            pdf.add_font(CUSTOM_FONT_NAME, '', font_path)
            font_family = CUSTOM_FONT_NAME
            logging.info("DejaVuSans.ttf found and loaded.")
        else:
            raise RuntimeError("Font file not found in any expected location")
    except (RuntimeError, FileNotFoundError):
        logging.warning("DejaVuSans.ttf not found. Falling back to core font. Non-ASCII characters may not render correctly.")
        # If the custom font fails, we stick with the default Helvetica.
        pass

    pdf.set_font(font_family, style='', size=BODY_FONT_SIZE)

    # Split the text into paragraphs and write them to the PDF.
    # The \\n is now a literal backslash followed by 'n', so we split on that.
    for paragraph in story_text.split('\\n\\n'):
        # No more manual encoding/decoding is needed.
        pdf.multi_cell(0, BODY_LINE_HEIGHT, text=paragraph, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(PARAGRAPH_SPACING)

    pdf.output(output_filepath)


def generate_docx(story_text, output_filepath, campaign_title=""):
    """Generates a DOCX file and saves it to the specified path."""
    document = Document()
    document.core_properties.title = campaign_title # Set metadata title
    for paragraph in story_text.split('\\n\\n'):
        document.add_paragraph(paragraph)
    document.save(output_filepath)

def generate_txt(story_text, output_filepath, campaign_title=""):
    """Generates a TXT file and saves it to the specified path."""
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(story_text.replace('\\\\n', '\\n'))
