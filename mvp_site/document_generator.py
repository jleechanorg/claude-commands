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
    pdf.set_title(campaign_title) # Set metadata title
    
    font_family = DEFAULT_FONT_FAMILY
    try:
        # Assumes 'assets/DejaVuSans.ttf' exists.
        font_path = os.path.join(ASSETS_DIR, FONT_FILENAME)
        pdf.add_font(CUSTOM_FONT_NAME, '', font_path)
        font_family = CUSTOM_FONT_NAME
    except RuntimeError:
        print("WARNING: DejaVuSans.ttf not found. Falling back to core font.")

    # --- CORRECTED BODY HANDLING ---
    # Set the font for the body (regular style)
    pdf.set_font(font_family, style='', size=BODY_FONT_SIZE)
    for paragraph in story_text.split('\\n\\n'):
        encoded_paragraph = paragraph.encode(ENCODING, ENCODING_REPLACE_STR).decode(ENCODING)
        pdf.multi_cell(0, BODY_LINE_HEIGHT, text=encoded_paragraph, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
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
