import os
from fpdf import FPDF, XPos, YPos
from docx import Document
import constants

# --- CONSTANTS ---
# File Paths and Configuration
ASSETS_DIR = 'assets'
FONT_FILENAME = 'DejaVuSans.ttf'
DEFAULT_FONT_FAMILY = 'Helvetica'
CUSTOM_FONT_NAME = 'DejaVu'
ENCODING = 'latin-1'
ENCODING_REPLACE_STR = 'replace'

# PDF Styling
TITLE_STYLE = 'U'
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


def get_story_text_from_context(story_context):
    """Extracts and formats story text from the context array."""
    story_parts = []
    for entry in story_context:
        actor = entry.get(constants.KEY_ACTOR, UNKNOWN_ACTOR)
        text = entry.get(constants.KEY_TEXT, '')
        mode = entry.get(constants.KEY_MODE)

        if actor == constants.ACTOR_GEMINI:
            label = LABEL_GEMINI
        else: # user
            label = LABEL_GOD if mode == constants.MODE_GOD else LABEL_USER
        
        story_parts.append(f"{label}:\\n{text}")
    
    return "\\n\\n".join(story_parts)


def generate_pdf(story_text, campaign_title):
    """Generates a PDF file from story text and returns its path."""
    pdf = FPDF()
    pdf.add_page()
    
    font_family = DEFAULT_FONT_FAMILY
    try:
        # Assumes 'assets/DejaVuSans.ttf' exists.
        font_path = os.path.join(ASSETS_DIR, FONT_FILENAME)
        pdf.add_font(CUSTOM_FONT_NAME, '', font_path)
        font_family = CUSTOM_FONT_NAME
    except RuntimeError:
        print("WARNING: DejaVuSans.ttf not found. Falling back to core font.")

    # --- CORRECTED TITLE HANDLING ---
    # Set the font family, then style, then size
    pdf.set_font(font_family, style=TITLE_STYLE, size=TITLE_FONT_SIZE) # 'U' for underline instead of 'B' for bold
    encoded_title = campaign_title.encode(ENCODING, ENCODING_REPLACE_STR).decode(ENCODING)
    pdf.cell(0, TITLE_LINE_HEIGHT, text=encoded_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=TITLE_ALIGNMENT)
    pdf.ln(TITLE_SPACING)

    # --- CORRECTED BODY HANDLING ---
    # Set the font for the body (regular style)
    pdf.set_font(font_family, style='', size=BODY_FONT_SIZE)
    for paragraph in story_text.split('\\n\\n'):
        encoded_paragraph = paragraph.encode(ENCODING, ENCODING_REPLACE_STR).decode(ENCODING)
        pdf.multi_cell(0, BODY_LINE_HEIGHT, text=encoded_paragraph, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(PARAGRAPH_SPACING)

    file_path = f"{campaign_title.replace(' ', '_')}.pdf"
    pdf.output(file_path)
    return file_path


def generate_docx(story_text, campaign_title):
    """Generates a DOCX file from story text and returns its path."""
    document = Document()
    document.add_heading(campaign_title, level=DOCX_HEADING_LEVEL)
    for paragraph in story_text.split('\\n\\n'):
        document.add_paragraph(paragraph)
    file_path = f"{campaign_title.replace(' ', '_')}.docx"
    document.save(file_path)
    return file_path

def generate_txt(story_text, campaign_title):
    """Generates a TXT file from story text and returns its path."""
    file_path = f"{campaign_title.replace(' ', '_')}.txt"
    with open(file_path, 'w', encoding='utf-8') as f:
        # Replace the literal '\\n' with actual newlines for the text file
        f.write(story_text.replace('\\\\n', '\\n'))
    return file_path
